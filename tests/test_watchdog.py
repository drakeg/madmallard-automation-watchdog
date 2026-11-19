import importlib.util
import os
from pathlib import Path
import tempfile
import time
import unittest

spec = importlib.util.spec_from_file_location("watchdog", Path(__file__).parents[1] / "watchdog.py")
watchdog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watchdog)

class OutputTests(unittest.TestCase):
    def test_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            watchdog.OUTPUT_ROOT = Path(tmp).resolve()
            self.assertEqual(watchdog.validate_output({"output_check":{"path":"missing.csv","type":"csv"}})[0], False)

    def test_csv_nonempty_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            watchdog.OUTPUT_ROOT = Path(tmp).resolve()
            p = Path(tmp) / "data.csv"
            p.write_text("sku,quantity\n123,5\n")
            self.assertTrue(watchdog.validate_output({"output_check":{"path":"data.csv","type":"csv","max_age_seconds":60}})[0])
            p.write_text("sku,quantity\n")
            self.assertFalse(watchdog.validate_output({"output_check":{"path":"data.csv","type":"csv"}})[0])

    def test_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            watchdog.OUTPUT_ROOT = Path(tmp).resolve()
            self.assertFalse(watchdog.validate_output({"output_check":{"path":"../../etc/passwd"}})[0])

    def test_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            watchdog.OUTPUT_ROOT = Path(tmp).resolve()
            p = Path(tmp) / "report.txt"
            p.write_text("ok")
            os.utime(p, (time.time()-3600,time.time()-3600))
            self.assertFalse(watchdog.validate_output({"output_check":{"path":"report.txt","max_age_seconds":30}})[0])

if __name__ == "__main__":
    unittest.main()
