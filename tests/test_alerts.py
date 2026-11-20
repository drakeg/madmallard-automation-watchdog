"""Synthetic-only integration tests: no outgoing network or customer data."""
import base64
import importlib.util
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('watchdog_alerts', Path(__file__).parents[1] / 'watchdog.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

class AlertTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        w.DATA = Path(self.tmp.name)
        w.OUTPUT_ROOT = Path(self.tmp.name).resolve()
        w.jobs = {'feed': {'id':'feed', 'name':'Feed', 'interval_seconds':5, 'grace_seconds':0,
                           'output_check':{'path':'feed.csv','type':'csv','max_age_seconds':60}}}
        w.ADMIN_TOKEN = 'a' * 32
        w.WEBHOOK_URL = ''
        w.boot_time = time.time() - 10
        with w.connection() as db:
            db.execute('CREATE TABLE events (id INTEGER PRIMARY KEY, job TEXT,kind TEXT,timestamp REAL,details TEXT)')
            db.execute('CREATE TABLE alerts (job TEXT PRIMARY KEY, active INTEGER, reason TEXT,since REAL,last_notified REAL)')
            db.execute('INSERT INTO alerts(job,active) VALUES (?,0)', ('feed',))
            db.execute('CREATE TABLE notification_queue (id INTEGER PRIMARY KEY,job TEXT,reason TEXT,created REAL,attempt INTEGER DEFAULT 0,next_attempt REAL,delivered REAL)')

    def status(self):
        with w.connection() as db:
            return db.execute('SELECT active,reason FROM alerts WHERE job=?', ('feed',)).fetchone()

    def test_missed_failure_recovery_and_db_persistence(self):
        w.check_missed()
        self.assertEqual(self.status(), (1, 'Expected completion missed'))
        w.record('feed','failure')
        self.assertEqual(self.status(), (1, 'Job signaled failure'))
        Path(self.tmp.name, 'feed.csv').write_text('id,value\n1,ready\n')
        self.assertEqual(w.record('feed','success'), (True,'Output validated'))
        self.assertEqual(self.status(), (0, None))
        with w.connection() as db:
            events = [row[0] for row in db.execute('SELECT kind FROM events ORDER BY id')]
        self.assertIn('recovered', events)
        self.assertIn('success', events)
        # Opening a new DB connection simulates the persistence boundary.
        self.assertEqual(self.status(), (0, None))

    def test_bad_output_does_not_recover(self):
        w.record('feed','failure')
        self.assertFalse(w.record('feed','success')[0])
        self.assertEqual(self.status()[0], 1)

    def test_browser_basic_auth_and_bearer(self):
        handler = object.__new__(w.Handler)
        credentials = base64.b64encode(('admin:'+w.ADMIN_TOKEN).encode()).decode()
        for supplied, expected in [(f'Basic {credentials}',True), ('Bearer '+w.ADMIN_TOKEN,True),
                                   ('Basic invalid',False),('Bearer wrong',False),('',False)]:
            handler.headers = {'Authorization': supplied}
            self.assertEqual(handler._admin_authorized(), expected)

    def test_notification_delivery_with_loopback_http(self):
        received = []
        class Sink(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers['Content-Length'])
                received.append(self.rfile.read(length).decode())
                self.send_response(204)
                self.end_headers()
            def log_message(self, *args): pass
        server = HTTPServer(('127.0.0.1', 0), Sink)
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        with patch.object(w, 'WEBHOOK_URL', f'http://127.0.0.1:{server.server_port}/alert'):
            self.assertTrue(w.notify('feed', 'Expected completion missed'))
        self.assertEqual(len(received), 1)
        self.assertIn('Expected completion missed', received[0])

    def test_retry_queue_survives_reopen_and_delivers(self):
        with patch.object(w, 'WEBHOOK_URL', 'https://alerts.example.invalid/hook'):
            w.record('feed', 'failure')
            with w.connection() as db:
                item = db.execute('SELECT id,attempt,delivered FROM notification_queue').fetchone()
            self.assertEqual(item[1:], (0, None))
            with patch.object(w, 'notify', side_effect=[False, True]) as deliver:
                w.dispatch_notifications()
                with w.connection() as db:
                    attempt, next_time = db.execute(
                        'SELECT attempt,next_attempt FROM notification_queue WHERE id=?',
                        (item[0],)
                    ).fetchone()
                    self.assertEqual(attempt, 1)
                    db.execute('UPDATE notification_queue SET next_attempt=0 WHERE id=?', (item[0],))
                w.dispatch_notifications()
                self.assertEqual(deliver.call_count, 2)
            with w.connection() as db:
                self.assertIsNotNone(db.execute(
                    'SELECT delivered FROM notification_queue WHERE id=?', (item[0],)
                ).fetchone()[0])

    def test_missed_does_not_hide_explicit_failure(self):
        w.record('feed', 'failure')
        w.check_missed()
        self.assertEqual(self.status(), (1, 'Job signaled failure'))

    def test_recovery_is_queued(self):
        Path(self.tmp.name, 'feed.csv').write_text('id,value\n1,ready\n')
        with patch.object(w, 'WEBHOOK_URL', 'https://alerts.example.invalid/hook'):
            w.record('feed', 'failure')
            w.record('feed', 'success')
            with w.connection() as db:
                messages = [x[0] for x in db.execute(
                    'SELECT reason FROM notification_queue ORDER BY id')]
            self.assertEqual(len(messages), 2)
            self.assertTrue(messages[1].startswith('RECOVERED:'))

    def test_reject_non_tls_external_webhook(self):
        with patch.object(w, 'WEBHOOK_URL', 'http://example.com/hook'):
            self.assertFalse(w.notify('feed', 'failure'))

if __name__ == '__main__':
    unittest.main()
