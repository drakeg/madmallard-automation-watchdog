"""Standard-library automation watchdog: heartbeat tracking, output checks and alerts."""
import base64
import binascii
import csv
import hmac
import html
import io
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
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
NOTIFICATION_CHANNEL = os.getenv("NOTIFICATION_CHANNEL", "webhook").lower()
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "")
SMTP_TO = os.getenv("SMTP_TO", "")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "5"))
PORT = int(os.getenv("PORT", "8765"))
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "90"))
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
    validate_delivery_config()
    if not 1 <= RETENTION_DAYS <= 3650:
        raise ValueError("RETENTION_DAYS must be between 1 and 3650")
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
        db.execute("""CREATE TABLE IF NOT EXISTS notification_queue
            (id INTEGER PRIMARY KEY, job TEXT NOT NULL, reason TEXT NOT NULL,
             created REAL NOT NULL, attempt INTEGER NOT NULL DEFAULT 0,
             next_attempt REAL NOT NULL, delivered REAL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS job_settings (
            job TEXT PRIMARY KEY, interval_seconds INTEGER NOT NULL,
            grace_seconds INTEGER NOT NULL, updated REAL NOT NULL)""")
        for job in jobs:
            db.execute("INSERT OR IGNORE INTO alerts(job,active) VALUES (?,0)", (job,))
        for ident, interval, grace in db.execute(
            "SELECT job,interval_seconds,grace_seconds FROM job_settings"
        ):
            if ident in jobs:
                jobs[ident]["interval_seconds"] = interval
                jobs[ident]["grace_seconds"] = grace

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

def delivery_enabled():
    return bool(WEBHOOK_URL) if NOTIFICATION_CHANNEL == "webhook" else NOTIFICATION_CHANNEL == "smtp"


def validate_delivery_config():
    if NOTIFICATION_CHANNEL not in ("webhook", "smtp"):
        raise ValueError("NOTIFICATION_CHANNEL must be webhook or smtp")
    if NOTIFICATION_CHANNEL == "smtp":
        if not all((SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_TO)):
            raise ValueError("SMTP requires host, user, password, sender and recipient")
        if not 1 <= SMTP_PORT <= 65535:
            raise ValueError("SMTP_PORT out of range")
        if any("\r" in x or "\n" in x for x in (SMTP_HOST, SMTP_USER, SMTP_FROM, SMTP_TO)):
            raise ValueError("SMTP fields must not contain newlines")


def notify_smtp(job, reason):
    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = SMTP_TO
    msg["Subject"] = "Watchdog notification: " + job
    msg.set_content("Job: " + job + "\nReason: " + reason + "\n")
    try:
        # Implicit TLS with default certificate verification; no cleartext fallback.
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT,
                              context=ssl.create_default_context(), timeout=5) as smtp:
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
        return True
    except (OSError, smtplib.SMTPException, ssl.SSLError) as exc:
        print("SMTP notification delivery failed:", type(exc).__name__, flush=True)
        return False


def notify(job, reason):
    if NOTIFICATION_CHANNEL == "smtp":
        return notify_smtp(job, reason)
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

def queue_notification(db, ident, reason):
    if delivery_enabled():
        now = time.time()
        db.execute(
            "INSERT INTO notification_queue(job, reason, created, next_attempt) VALUES (?,?,?,?)",
            (ident, reason, now, now)
        )

def dispatch_notifications():
    """Deliver persisted notifications, backing off from transient failures.

    A failed webhook remains queued across restarts. SQLite serializes queue
    updates so only one monitor thread should dispatch per installation.
    """
    if not delivery_enabled():
        return
    with lock, connection() as db:
        pending = db.execute(
            """SELECT id,job,reason,attempt FROM notification_queue
               WHERE delivered IS NULL AND next_attempt <= ?
               ORDER BY id LIMIT 20""", (time.time(),)
        ).fetchall()
    for message_id, ident, reason, attempt in pending:
        success = notify(ident, reason)
        with lock, connection() as db:
            if success:
                db.execute(
                    "UPDATE notification_queue SET delivered=? WHERE id=? AND delivered IS NULL",
                    (time.time(), message_id)
                )
            else:
                delay = min(300, 5 * (2 ** min(attempt, 6)))
                db.execute(
                    "UPDATE notification_queue SET attempt=attempt+1,next_attempt=? WHERE id=? AND delivered IS NULL",
                    (time.time() + delay, message_id)
                )

def prune_history(now=None):
    """Prune only old event history and delivered notification records.

    Never delete pending notifications, even if they are older than retention.
    """
    cutoff = (time.time() if now is None else now) - RETENTION_DAYS * 86400
    with lock, connection() as db:
        events_deleted = db.execute(
            "DELETE FROM events WHERE timestamp < ?", (cutoff,)
        ).rowcount
        delivered_deleted = db.execute(
            "DELETE FROM notification_queue WHERE delivered IS NOT NULL AND delivered < ?",
            (cutoff,)
        ).rowcount
    return events_deleted, delivered_deleted


def job_delivery_history(ident, limit=30):
    if ident not in jobs:
        raise KeyError(ident)
    with lock, connection() as db:
        records = db.execute(
            """SELECT reason,created,attempt,next_attempt,delivered
               FROM notification_queue WHERE job=? ORDER BY id DESC LIMIT ?""",
            (ident, limit)
        ).fetchall()
        state = db.execute(
            "SELECT active,reason,since FROM alerts WHERE job=?", (ident,)
        ).fetchone()
    return {
        "job": ident,
        "alert": {
            "active": bool(state[0]),
            "reason": state[1],
            "since": stamp(state[2]) if state[2] is not None else None,
            "age_seconds": max(0, int(time.time() - state[2])) if state[0] and state[2] else 0
        },
        "delivery": [
            {"reason": reason, "created": stamp(created), "attempts": attempt,
             "next_attempt": stamp(next_time) if delivered is None else None,
             "delivered": stamp(delivered) if delivered is not None else None}
            for reason, created, attempt, next_time, delivered in records
        ]
    }


def update_job_schedule(ident, interval, grace):
    if ident not in jobs:
        raise KeyError(ident)
    # Reject booleans, floats and string coercion to avoid confusing settings.
    if type(interval) is not int or type(grace) is not int:
        raise ValueError("Schedule values must be integers")
    if not (5 <= interval <= 31536000 and 0 <= grace <= 2592000):
        raise ValueError("Interval or grace out of range")
    with lock, connection() as db:
        db.execute(
            """INSERT INTO job_settings(job,interval_seconds,grace_seconds,updated)
               VALUES (?,?,?,?)
               ON CONFLICT(job) DO UPDATE SET
                 interval_seconds=excluded.interval_seconds,
                 grace_seconds=excluded.grace_seconds,
                 updated=excluded.updated""",
            (ident, interval, grace, time.time())
        )
        jobs[ident]["interval_seconds"] = interval
        jobs[ident]["grace_seconds"] = grace
    return {"id": ident, "interval_seconds": interval, "grace_seconds": grace}


def public_job_config():
    with lock:
        return [
            {"id": ident, "name": config.get("name", ident),
             "interval_seconds": int(config["interval_seconds"]),
             "grace_seconds": int(config["grace_seconds"])}
            for ident, config in jobs.items()
        ]


def delivery_summary():
    with lock, connection() as db:
        queued, failed, delivered = db.execute(
            """SELECT
                 COALESCE(SUM(delivered IS NULL),0),
                 COALESCE(SUM(delivered IS NULL AND attempt > 0),0),
                 COALESCE(SUM(delivered IS NOT NULL),0)
               FROM notification_queue"""
        ).fetchone()
    return {"pending": queued, "retrying": failed, "delivered": delivered}


def change_alert(db, ident, reason):
    row = db.execute("SELECT active,reason FROM alerts WHERE job=?", (ident,)).fetchone()
    if reason:
        if not row[0] or row[1] != reason:
            db.execute("UPDATE alerts SET active=1,reason=?,since=?,last_notified=? WHERE job=?",
                       (reason, time.time(), time.time(), ident))
            event(db, ident, "alert", reason)
            queue_notification(db, ident, reason)
            return reason
    elif row[0]:
        db.execute("UPDATE alerts SET active=0,reason=NULL,since=NULL WHERE job=?", (ident,))
        event(db, ident, "recovered", "Successful output-validated completion")
        queue_notification(db, ident, "RECOVERED: Successful output-validated completion")
        return "RECOVERED: Successful output-validated completion"
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
    return (good, detail) if kind == "success" else (True, kind)

def check_missed():
    with lock:
        with connection() as db:
            for ident, job in jobs.items():
                row = db.execute("SELECT MAX(timestamp) FROM events WHERE job=? AND kind='success'", (ident,)).fetchone()
                baseline = row[0] if row[0] is not None else boot_time
                overdue = time.time() > baseline + int(job["interval_seconds"]) + int(job["grace_seconds"])
                if overdue:
                    current = db.execute(
                        "SELECT active,reason FROM alerts WHERE job=?", (ident,)
                    ).fetchone()
                    # Preserve an actionable explicit/output failure until
                    # validated completion, rather than replacing it with missed.
                    if not current[0]:
                        change_alert(db, ident, "Expected completion missed")
    # Notifications are enqueued transactionally by change_alert.

def monitor():
    next_cleanup = 0
    while True:
        try:
            check_missed()
            dispatch_notifications()
            if time.time() >= next_cleanup:
                prune_history()
                next_cleanup = time.time() + 86400
        except Exception as exc:
            print("Monitor error:", repr(exc), flush=True)
        time.sleep(POLL_SECONDS)

def export_event_csv(limit=5000):
    """Export redacted job-state evidence, never the underlying business output."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(("job", "event", "timestamp_utc", "details"))
    with lock, connection() as db:
        rows = db.execute(
            "SELECT job,kind,timestamp,details FROM events ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    for ident, kind, when, details in reversed(rows):
        writer.writerow((ident, kind, stamp(when), details))
    return out.getvalue()


ADMIN_JS = """document.querySelectorAll('#settings button[data-job]').forEach(button => {
  button.addEventListener('click', async () => {
    const row = button.closest('tr');
    const interval = Number(row.querySelector('[data-field=interval_seconds]').value);
    const grace = Number(row.querySelector('[data-field=grace_seconds]').value);
    const status = document.getElementById('result');
    if (!Number.isSafeInteger(interval) || !Number.isSafeInteger(grace)) {
      status.textContent = 'Enter whole seconds'; return;
    }
    button.disabled = true;
    try {
      const response = await fetch('/api/admin/jobs/' + encodeURIComponent(button.dataset.job), {
        method: 'PUT',
        headers: {'Content-Type': 'application/json', 'X-Watchdog-Action': 'update-schedule'},
        body: JSON.stringify({interval_seconds: interval, grace_seconds: grace})
      });
      const result = await response.json();
      status.textContent = response.ok ? ('Saved schedule for ' + result.id) : (result.error || 'Save failed');
    } catch {
      status.textContent = 'Connection failed';
    } finally {
      button.disabled = false;
    }
  });
});
const deliveryRoot = document.getElementById('delivery-panel');
if (deliveryRoot) {
  document.querySelectorAll('[data-history-job]').forEach(button => {
    button.addEventListener('click', async () => {
      const job = button.dataset.historyJob;
      const panel = document.getElementById('delivery-panel');
      const heading = document.getElementById('delivery-heading');
      const message = document.getElementById('delivery-message');
      const table = document.getElementById('delivery-table');
      const body = document.getElementById('delivery-rows');
      panel.hidden = false;
      heading.textContent = 'Notification history: ' + button.dataset.historyName;
      message.textContent = 'Loading delivery history…';
      table.hidden = true;
      body.replaceChildren();
      button.disabled = true;
      try {
        const response = await fetch('/api/jobs/' + encodeURIComponent(job) + '/delivery');
        if (!response.ok) throw new Error('Unable to load delivery history (HTTP ' + response.status + ')');
        const data = await response.json();
        const current = data.alert || {};
        message.textContent = current.active
          ? 'Alert active for ' + current.age_seconds + ' seconds: ' + (current.reason || 'Unknown reason')
          : 'No active alert';
        if (!data.delivery.length) {
          message.textContent += '. No notification delivery records for this job.';
          return;
        }
        for (const item of data.delivery) {
          const row = document.createElement('tr');
          const status = item.delivered ? 'Delivered: ' + item.delivered
                        : (item.attempts ? 'Retrying' : 'Pending');
          for (const value of [item.created, item.reason, status, String(item.attempts),
                               item.next_attempt || '—']) {
            const cell = document.createElement('td');
            cell.textContent = String(value || '—');
            row.appendChild(cell);
          }
          body.appendChild(row);
        }
        table.hidden = false;
      } catch (error) {
        message.textContent = error.message || 'Unable to load history';
      } finally {
        button.disabled = false;
      }
    });
  });
}"""


class Handler(BaseHTTPRequestHandler):
    def send(self, code, payload, content_type="application/json"):
        body = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; script-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_PUT(self):
        parts = self.path.strip("/").split("/")
        if len(parts) != 4 or parts[:3] != ["api", "admin", "jobs"] or parts[3] not in jobs:
            return self.send(404, {"error": "Not found"})
        if not self._admin_authorized() or self.headers.get("X-Watchdog-Action") != "update-schedule":
            return self.send(403, {"error": "Admin authentication and intent header required"})
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            return self.send(415, {"error": "JSON required"})
        # Browsers must not allow cross-site scripts to send this custom header.
        # Reject cross-origin requests explicitly as defense in depth.
        origin = self.headers.get("Origin")
        if origin:
            from urllib.parse import urlsplit as split
            parsed = split(origin)
            host = self.headers.get("Host", "")
            if parsed.netloc != host or parsed.scheme not in ("http", "https"):
                return self.send(403, {"error": "Cross-origin change forbidden"})
        try:
            count = int(self.headers.get("Content-Length", "0"))
            if not 1 <= count <= 2048:
                return self.send(413, {"error": "Invalid request length"})
            data = json.loads(self.rfile.read(count))
            if not isinstance(data, dict) or set(data) != {"interval_seconds", "grace_seconds"}:
                raise ValueError("Unexpected configuration")
            updated = update_job_schedule(parts[3], data["interval_seconds"], data["grace_seconds"])
        except (ValueError, TypeError, UnicodeError, json.JSONDecodeError):
            return self.send(400, {"error": "Invalid schedule: interval 5–31536000, grace 0–2592000 seconds"})
        return self.send(200, updated)

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
        if self.path == "/assets/admin.js":
            return self.send(200, ADMIN_JS, "application/javascript")
        if self.path.startswith("/api/jobs/") and self.path.endswith("/delivery"):
            parts = self.path.strip("/").split("/")
            if len(parts) == 4 and parts[2] in jobs:
                return self.send(200, job_delivery_history(parts[2]))
        if self.path not in ("/", "/api/status", "/api/report.csv", "/api/admin/jobs"):
            return self.send(404, {"error": "Not found"})
        if self.path == "/api/admin/jobs":
            return self.send(200, {"jobs": public_job_config()})
        if self.path == "/api/report.csv":
            return self.send(200, export_event_csv(), "text/csv")
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
            return self.send(200, {"jobs": snapshot, "delivery": delivery_summary()})
        delivery = delivery_summary()
        config_rows = "".join(
            '<tr><td>' + html.escape(c["name"]) + '</td><td><input type="number" min="5" max="31536000" value="' +
            str(c["interval_seconds"]) + '" data-field="interval_seconds"></td><td><input type="number" min="0" max="2592000" value="' +
            str(c["grace_seconds"]) + '" data-field="grace_seconds"></td><td><button type="button" data-job="' +
            html.escape(c["id"], quote=True) + '">Save</button></td></tr>'
            for c in public_job_config()
        )
        rows = "".join(
            '<tr><td>' + html.escape(item["name"]) + '</td><td>' + item["state"] + '</td><td>' +
            html.escape(item["reason"] or "") + '</td><td>' +
            html.escape(str(item["last_event"] or "Not run")) + '</td><td><button type="button" '
            'data-history-job="' + html.escape(item["id"], quote=True) +
            '" data-history-name="' + html.escape(item["name"], quote=True) +
            '" aria-controls="delivery-panel">History</button></td></tr>'
            for item in snapshot
        )
        page = ('<!doctype html><html><head><meta name="viewport" content="width=device-width">'
                '<title>Mad Mallard Watchdog</title><style>body{font:16px system-ui;margin:3rem;background:#101827;color:#eee}'
                'table{border-collapse:collapse;width:100%}td,th{padding:1rem;border-bottom:1px solid #536075;text-align:left}'
                'table{display:block;overflow-x:auto}button{cursor:pointer}button:focus-visible{outline:3px solid #86daca}'
                'a{color:#86daca}[hidden]{display:none!important}h1{color:#86daca}</style></head><body><h1>Mad Mallard Automation Watchdog</h1>'
                '<p>Up to five scheduled jobs · completion and output validation</p>'
                '<p>Notification delivery: ' + str(delivery["pending"]) +
                ' pending, ' + str(delivery["retrying"]) + ' retrying, ' +
                str(delivery["delivered"]) + ' delivered</p>'
                '<table><tr><th>Job</th><th>State</th><th>Reason</th><th>Last event (UTC)</th><th>Notifications</th></tr>'
                + rows + '</table>'
                '<section id="delivery-panel" hidden aria-labelledby="delivery-heading"><h2 id="delivery-heading">Notification history</h2>'
                '<p id="delivery-message" role="status" aria-live="polite"></p>'
                '<table id="delivery-table" hidden><thead><tr><th>Created (UTC)</th><th>Reason</th>'
                '<th>Delivery</th><th>Attempts</th><th>Next attempt (UTC)</th></tr></thead>'
                '<tbody id="delivery-rows"></tbody></table></section>'
                '<h2>Job schedules</h2><p>Edit completion interval and grace in seconds; changes persist across restarts.</p>'
                '<table id="settings"><thead><tr><th>Job</th><th>Interval (s)</th><th>Grace (s)</th><th>Save</th></tr></thead><tbody>'
                + config_rows + '</tbody></table><p id="result" role="status" aria-live="polite"></p>'
                '<p><a href="/api/report.csv">Export event evidence (CSV)</a></p>'
                '<p>Use the History button to inspect up to 30 recent notifications per job.</p>'
                '<script src="/assets/admin.js" defer></script></body></html>')
        return self.send(200, page, "text/html")

if __name__ == "__main__":
    init()
    threading.Thread(target=monitor, daemon=True).start()
    print("Watching", len(jobs), "jobs on port", PORT, flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
