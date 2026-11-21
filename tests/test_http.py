"""Exercise admin API over loopback with temporary test storage."""
import base64
import importlib.util
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import unittest

spec = importlib.util.spec_from_file_location('watchdog_http', Path(__file__).resolve().parents[1] / 'watchdog.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

class AdminApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = TemporaryDirectory()
        w.DATA = Path(cls.tmp.name)
        w.jobs = {'feed':{'id':'feed','name':'Test feed','interval_seconds':30,'grace_seconds':5}}
        w.ADMIN_TOKEN = 'x' * 40
        w.WEBHOOK_URL = ''
        with w.connection() as db:
            db.execute('CREATE TABLE events (id INTEGER PRIMARY KEY, job TEXT, kind TEXT, timestamp REAL, details TEXT)')
            db.execute('CREATE TABLE alerts (job TEXT PRIMARY KEY, active INTEGER, reason TEXT, since REAL, last_notified REAL)')
            db.execute('INSERT INTO alerts(job,active) VALUES (?,0)', ('feed',))
            db.execute('CREATE TABLE notification_queue (id INTEGER PRIMARY KEY,job TEXT,reason TEXT,created REAL,attempt INTEGER DEFAULT 0,next_attempt REAL,delivered REAL)')
            db.execute('CREATE TABLE job_settings (job TEXT PRIMARY KEY,interval_seconds INTEGER,grace_seconds INTEGER,updated REAL)')
        cls.server = ThreadingHTTPServer(('127.0.0.1',0), w.Handler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_port)
        cls.auth = 'Basic ' + base64.b64encode(('admin:'+w.ADMIN_TOKEN).encode()).decode()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.tmp.cleanup()

    def request(self, path, method='GET', payload=None, authorized=True, extra=None):
        headers = {'Authorization':self.auth} if authorized else {}
        headers.update(extra or {})
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(self.base+path, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=3) as result:
                return result.status, result.read().decode()
        except HTTPError as error:
            return error.code, error.read().decode()

    def test_admin_api_protection_and_schedule(self):
        path='/api/admin/jobs/feed'
        payload={'interval_seconds':120, 'grace_seconds':10}
        self.assertEqual(self.request('/api/admin/jobs',authorized=False)[0],401)
        self.assertEqual(self.request(path,method='PUT',payload=payload,authorized=False)[0],403)
        self.assertEqual(self.request(path,method='PUT',payload=payload)[0],403)
        correct={'Content-Type':'application/json','X-Watchdog-Action':'update-schedule'}
        bad={**correct,'Origin':'https://evil.example'}
        self.assertEqual(self.request(path,'PUT',payload,extra=bad)[0],403)
        self.assertEqual(self.request(path,'PUT',payload,extra=correct)[0],200)
        status, body=self.request('/api/admin/jobs')
        self.assertEqual(status,200)
        self.assertEqual(json.loads(body)['jobs'][0]['interval_seconds'],120)
        status, page=self.request('/')
        self.assertEqual(status,200)
        self.assertIn('id="settings"',page)
        self.assertEqual(self.request('/assets/admin.js')[0],200)
        self.assertEqual(self.request('/api/jobs/feed/delivery')[0],200)
        self.assertEqual(self.request('/api/jobs/feed/delivery',authorized=False)[0],401)
        self.assertIn('data-history-job="feed"',page)
        self.assertIn('id="delivery-panel"',page)
        self.assertIn('id="delivery-rows"',page)
        script_status, script = self.request('/assets/admin.js')
        self.assertEqual(script_status,200)
        self.assertIn("data-history-job",script)
        self.assertIn("cell.textContent =",script)
        self.assertNotIn("innerHTML",script)

    def test_invalid_configuration_fails_closed(self):
        headers={'Content-Type':'application/json','X-Watchdog-Action':'update-schedule'}
        self.assertEqual(self.request('/api/admin/jobs/feed','PUT',{'interval_seconds':0,'grace_seconds':0},extra=headers)[0],400)
        self.assertEqual(self.request('/api/admin/jobs/missing','PUT',{'interval_seconds':50,'grace_seconds':0},extra=headers)[0],404)
        self.assertEqual(self.request('/api/jobs/missing/delivery')[0],404)

if __name__=='__main__':
    unittest.main()
