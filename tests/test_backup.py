import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

spec = importlib.util.spec_from_file_location("backup_tool", Path(__file__).resolve().parents[1] / "scripts/backup.py")
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)

class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / "live.sqlite3"
        with sqlite3.connect(self.source) as db:
            for table in backup.REQUIRED_TABLES:
                db.execute(f'CREATE TABLE "{table}" (id INTEGER PRIMARY KEY, details TEXT)')
            db.execute('INSERT INTO events(details) VALUES (?)', ("synthetic",))

    def test_consistent_backup_and_restore_to_separate_file(self):
        path = Path(self.tmp.name) / "backups" / "snapshot.sqlite3"
        result = backup.backup(self.source, path)
        self.assertEqual(result["tables"]["events"], 1)
        self.assertEqual(result, backup.verify(path))
        restored = Path(self.tmp.name) / "isolated-restore.sqlite3"
        restored.write_bytes(path.read_bytes())
        self.assertEqual(backup.verify(restored)["tables"]["events"], 1)
        with sqlite3.connect(self.source) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events").fetchone()[0], 1)

    def test_refuses_overwrite_and_source_overwrite(self):
        target = Path(self.tmp.name) / "backup.sqlite3"
        backup.backup(self.source, target)
        with self.assertRaisesRegex(ValueError, "overwrite"):
            backup.backup(self.source, target)
        with self.assertRaisesRegex(ValueError, "source"):
            backup.backup(self.source, self.source)

    def test_corrupt_and_missing_table_rejected(self):
        corrupt = Path(self.tmp.name) / "bad.sqlite3"
        corrupt.write_text("not a database")
        with self.assertRaises(sqlite3.DatabaseError):
            backup.verify(corrupt)
        with sqlite3.connect(self.source) as db:
            db.execute("DROP TABLE alerts")
        with self.assertRaisesRegex(ValueError, "Missing required tables"):
            backup.verify(self.source)

if __name__ == "__main__":
    unittest.main()
