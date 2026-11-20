"""Synthetic delivery smoke: isolated DB, loopback receiver, no customer traffic.

Run from repository root, or feed into `docker compose exec -T watchdog python -`.
Retry due time is advanced in the temporary database rather than sleeping.
"""
import importlib.util
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from pathlib import Path
import sys
import tempfile
import threading

sys.path.insert(0, str(Path.cwd()))
import watchdog as w


def main():
    received = []
    class Sink(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(503 if len(received) == 1 else 204)
            self.end_headers()
        def log_message(self, *args):
            pass
    server = HTTPServer(('127.0.0.1', 0), Sink)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            w.DATA = root
            w.OUTPUT_ROOT = root
            w.CONFIG = root / 'jobs.json'
            w.CONFIG.write_text(json.dumps({'jobs': [{'id': 'smoke', 'interval_seconds': 60,
                'grace_seconds': 0, 'token_env': 'SMOKE_ONLY_TOKEN',
                'output_check': {'path': 'output.txt', 'type': 'file'}}]}))
            os.environ['SMOKE_ONLY_TOKEN'] = 'synthetic-test-only-not-a-secret-token'
            w.ADMIN_TOKEN = 'synthetic-test-only-admin-token'
            w.WEBHOOK_URL = f'http://127.0.0.1:{server.server_port}/'
            w.jobs = {}
            w.init()
            w.record('smoke', 'failure')
            assert w.notification_status()[0]['state'] == 'pending'
            # Reload module state while retaining the DB to exercise restart persistence.
            spec = importlib.util.spec_from_file_location('restarted_watchdog', Path(w.__file__))
            restarted = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(restarted)
            restarted.DATA, restarted.WEBHOOK_URL = root, w.WEBHOOK_URL
            assert restarted.notification_status()[0]['attempts'] == 1
            with restarted.connection() as db:
                db.execute('UPDATE notifications SET next_attempt=0')
            restarted.deliver_pending()
            assert restarted.notification_status()[0]['state'] == 'sent'
            (root / 'output.txt').write_text('synthetic complete')
            assert w.record('smoke', 'success')[0], 'Synthetic output validation failed'
            assert len(received) == 3
            assert 'Recovered' in received[-1]['reason']
            assert all(row['state'] == 'sent' for row in w.notification_status())
            print('PASS: real HTTP 503 -> persistent retry -> HTTP 204 -> recovery delivery')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
