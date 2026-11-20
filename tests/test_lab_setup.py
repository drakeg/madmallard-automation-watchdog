import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class LabSetupTests(unittest.TestCase):
    def test_credentials_are_private_and_preserved_on_rerun(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'scripts').mkdir()
            script = root / 'scripts/init-healthchecks.py'
            shutil.copyfile(Path(__file__).resolve().parents[1] / 'scripts/init-healthchecks.py', script)
            command = [sys.executable, str(script), '--url', 'http://192.168.0.155:18080']
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            env = root / '.env.healthchecks'
            content = env.read_text()
            self.assertEqual(env.stat().st_mode & 0o777, 0o600)
            self.assertIn('REGISTRATION_OPEN=False', content)
            self.assertNotIn('DJANGO_SUPERUSER_PASSWORD', first.stdout)
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(content, env.read_text())
            bad = subprocess.run(command[:-1] + ['http://user:secret@host/'], capture_output=True)
            self.assertNotEqual(bad.returncode, 0)
