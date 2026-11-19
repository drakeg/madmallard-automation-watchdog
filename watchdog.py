"""Standard-library automation watchdog: heartbeat tracking, output checks and alerts."""
import base64
import binascii
import csv
import hmac
import html
import json
import os
from pathlib import Path
import sqlite3
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request
from urllib.parse import urlsplit

DATA = Path(os.getenv("WATCHDOG_DATA", "/data"))
CONFIG = Path(os.getenv("WATCHDOG_CONFIG", "/app/jobs.json"))
OUTPUT_ROOT = Path(os.getenv("WATCHDOG_OUTPUT_ROOT", "/outputs")).resolve()
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "5"))
PORT = int(os.getenv("PORT", "8765"))
lock = threading.RLock()
jobs = {}
boot_time = time.time()

def stamp(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds")

def connection():
    db = sqlite3.connect(DATA / "watchdog.sqlite3", timeout=10)
    db.execute("PRAGMA journal_mode=WAL")
    return db

def init():
    if not ADMIN_TOKEN or len(ADMIN_TOKEN) < 20:
        raise ValueError("ADMIN_TOKEN must be at least 20 characters")
    DATA.mkdir(parents=True, exist_ok=True)
    spec = json.loads(CONFIG.read_text())
    if not 1 <= len(spec["jobs"]) <= 5:
        raise ValueError("Provide between one and five jobs")
    for job in spec["jobs"]:
        ident = job["id"]
        if not ident.isascii() or not ident.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Invalid job id")
        secret = os.getenv(job["token_env"], "")
        if len(secret) < 20:
            raise ValueError("Missing or short token for " + ident)
        if int(job["interval_seconds"]) < 5 or int(job["grace_seconds"]) < 0:
            raise ValueError("Invalid schedule")
        if ident in jobs:
            raise ValueError("Duplicate job id")
        jobs[ident] = {**job, "_token": secret}
    with connection() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS events
            (id INTEGER PRIMARY KEY, job TEXT NOT NULL, kind TEXT NOT NULL,
             timestamp REAL NOT NULL, details TEXT NOT NULL DEFAULT '')""")
        db.execute("""CREATE TABLE IF NOT EXISTS alerts
            (job TEXT PRIMARY KEY, active INTEGER NOT NULL, reason TEXT,
             since REAL, last_notified REAL)""")
        for job in jobs:
            db.execute("INSERT OR IGNORE INTO alerts(job,active) VALUES (?,0)", (job,))

def event(db, job, kind, details=""):
    db.execute("INSERT INTO events(job,kind,timestamp,details) VALUES (?,?,?,?)",
               (job, kind, time.time(), details[:500]))

def validate_output(job):
    check = job.get("output_check")
    if not check:
        return True, "No output check configured"
    relative = Path(check["path"])
    target = (OUTPUT_ROOT / relative).resolve()
    if not target.is_relative_to(OUTPUT_ROOT):
        return False, "Output escapes configured root"
    if not target.is_file():
        return False, "Expected output missing"
    max_age = int(check.get("max_age_seconds", 86400))
    if time.time() - target.stat().st_mtime > max_age:
        return False, "Output is stale"
    if check.get("type") == "csv":
        try:
            with target.open(newline="", encoding="utf-8") as fh:
                rows = csv.reader(fh)
                next(rows, None)  # header
                if not next(rows, None):
                    return False, "CSV has no records"
        except (OSError, UnicodeError, csv.Error):
            return False, "CSV cannot be read"
    elif target.stat().st_size == 0:
        return False, "Output is empty"
    return True, "Output validated"

def notify(job, reason):
    if not WEBHOOK_URL:
        return False
    # Do not allow unencrypted or non-HTTPS destinations outside loopback tests.
    parsed = urlsplit(WEBHOOK_URL)
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost")):
        print("Notification URL must use HTTPS (loopback HTTP allowed for tests)", flush=True)
        return False
    # Only send nonsensitive identifiers/reason, never filenames or records.
    payload = json.dumps({"text": "Watchdog: " + job + " - " + reason,
                          "job": job, "reason": reason}).encode()
    try:
        req = request.Request(WEBHOOK_URL, data=payload,
                              headers={"Content-Type": "application/json"}, method="POST")
        with request.urlopen(req, timeout=5) as response:
            response.read()
            return True
    except Exception as exc:
        print("Notification delivery failed:", type(exc).__name__, flush=True)
        return False

def change_alert(db, ident, reason):
    row = db.execute("SELECT active,reason FROM alerts WHERE job=?", (ident,)).fetchone()
    if reason:
        if not row[0] or row[1] != reason:
            db.execute("UPDATE alerts SET active=1,reason=?,since=?,last_notified=? WHERE job=?",
                       (reason, time.time(), time.time(), ident))
            event(db, ident, "alert", reason)
            return reason
    elif row[0]:
        db.execute("UPDATE alerts SET active=0,reason=NULL,since=NULL WHERE job=?", (ident,))
        event(db, ident, "recovered", "Successful output-validated completion")
    return None

def record(ident, kind):
    with lock:
        with connection() as db:
            if kind == "success":
                good, detail = validate_output(jobs[ident])
                event(db, ident, "success" if good else "failure", detail)
                alert = change_alert(db, ident, None if good else detail)
            else:
                event(db, ident, kind)
                alert = change_alert(db, ident, "Job signaled failure") if kind == "failure" else None
    if alert:
        notify(ident, alert)
    return (good, detail) if kind == "success" else (True, kind)

def check_missed():
    alerts = []
    with lock:
        with connection() as db:
            for ident, job in jobs.items():
                row = db.execute("SELECT MAX(timestamp) FROM events WHERE job=? AND kind='success'", (ident,)).fetchone()
                baseline = row[0] if row[0] is not None else boot_time
                overdue = time.time() > baseline + int(job["interval_seconds"]) + int(job["grace_seconds"])
                if overdue:
                    alert = change_alert(db, ident, "Expected completion missed")
                    if alert:
                        alerts.append((ident, alert))
    for ident, alert in alerts:
        notify(ident, alert)

def monitor():
    while True:
        try:
            check_missed()
        except Exception as exc:
            print("Monitor error:", repr(exc), flush=True)
        time.sleep(POLL_SECONDS)

class Handler(BaseHTTPRequestHandler):
    def send(self, code, payload, content_type="application/json"):
        body = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parts = self.path.strip("/").split("/")
        if len(parts) != 3 or parts[0] != "api" or parts[1] not in jobs or parts[2] not in ("start", "success", "failure"):
            return self.send(404, {"error": "Not found"})
        ident, kind = parts[1], parts[2]
        token = self.headers.get("Authorization", "").removeprefix("Bearer ")
        if not hmac.compare_digest(token, jobs[ident]["_token"]):
            return self.send(401, {"error": "Unauthorized"})
        good, detail = record(ident, kind)
        return self.send(200 if good else 422, {"ok": good, "message": detail})

    def _admin_authorized(self):
        supplied = self.headers.get("Authorization", "")
        if supplied.startswith("Bearer "):
            return hmac.compare_digest(supplied[7:], ADMIN_TOKEN)
        if supplied.startswith("Basic "):
            try:
                decoded = base64.b64decode(supplied[6:], validate=True).decode("utf-8")
                username, password = decoded.split(":", 1)
                return hmac.compare_digest(username, "admin") and hmac.compare_digest(password, ADMIN_TOKEN)
            except (ValueError, UnicodeDecodeError, binascii.Error):
                return False
        return False

    def do_GET(self):
        if not self._admin_authorized():
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="Watchdog admin"')
            self.end_headers()
            return
        if self.path not in ("/", "/api/status"):
            return self.send(404, {"error": "Not found"})
        with lock, connection() as db:
            snapshot = []
            for ident, job in jobs.items():
                state = db.execute("SELECT active,reason FROM alerts WHERE job=?", (ident,)).fetchone()
                latest = db.execute("SELECT kind,timestamp,details FROM events WHERE job=? ORDER BY id DESC LIMIT 1", (ident,)).fetchone()
                snapshot.append({"id": ident, "name": job.get("name", ident),
                                 "state": "ALERT" if state[0] else "OK",
                                 "reason": state[1] if state[0] else None,
                                 "last_event": {"kind": latest[0], "at": stamp(latest[1])} if latest else None})
        if self.path == "/api/status":
            return self.send(200, {"jobs": snapshot})
        rows = "".join("<tr><td>" + html.escape(s["name"]) + "</td><td>" + s["state"] + "</td><td>" +
                       html.escape(s["reason"] or "") + "</td><td>" +
                       html.escape(str(s["last_event"] or "Not run")) + "</td></tr>" for s in snapshot)
        page = ('<!doctype html><html><head><meta name="viewport" content="width=device-width">'
                '<title>Mad Mallard Watchdog</title><style>body{font:16px system-ui;margin:3rem;background:#101827;color:#eee}'
                'table{border-collapse:collapse;width:100%}td,th{padding:1rem;border-bottom:1px solid #536075;text-align:left}'
                'h1{color:#86daca}</style></head><body><h1>Mad Mallard Automation Watchdog</h1>'
                '<p>Up to five scheduled jobs · completion and output validation</p>'
                '<table><tr><th>Job</th><th>State</th><th>Reason</th><th>Last event (UTC)</th></tr>'
                + rows + '</table><p>Admin API: /api/status (Bearer token)</p></body></html>')
        return self.send(200, page, "text/html")

if __name__ == "__main__":
    init()
    threading.Thread(target=monitor, daemon=True).start()
    print("Watching", len(jobs), "jobs on port", PORT, flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
