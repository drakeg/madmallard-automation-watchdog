"""SMTP transport tests use mocks and never send real email."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import smtplib
import unittest
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location("smtp_watchdog", Path(__file__).resolve().parents[1] / "watchdog.py")
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

class SMTPTests(unittest.TestCase):
    def smtp_config(self):
        return (
            patch.object(w, "NOTIFICATION_CHANNEL", "smtp"),
            patch.object(w, "SMTP_HOST", "smtp.example.invalid"),
            patch.object(w, "SMTP_PORT", 465),
            patch.object(w, "SMTP_USER", "service@example.invalid"),
            patch.object(w, "SMTP_PASSWORD", "synthetic-only-test-password"),
            patch.object(w, "SMTP_FROM", "watchdog@example.invalid"),
            patch.object(w, "SMTP_TO", "operator@example.invalid"),
        )

    def test_smtp_tls_auth_and_redacted_delivery(self):
        from contextlib import ExitStack
        with ExitStack() as stack:
            for ctx in self.smtp_config():
                stack.enter_context(ctx)
            connection = stack.enter_context(patch.object(w.smtplib, "SMTP_SSL"))
            client = connection.return_value.__enter__.return_value
            self.assertTrue(w.delivery_enabled())
            w.validate_delivery_config()
            self.assertTrue(w.notify("inventory-feed", "Expected completion missed"))
            connection.assert_called_once()
            self.assertEqual(connection.call_args.args[:2], ("smtp.example.invalid", 465))
            self.assertIsNotNone(connection.call_args.kwargs.get("context"))
            client.login.assert_called_once_with("service@example.invalid", "synthetic-only-test-password")
            sent = client.send_message.call_args.args[0]
            self.assertEqual(sent["To"], "operator@example.invalid")
            self.assertIn("Expected completion missed", sent.get_content())
            self.assertNotIn("synthetic-only-test-password", sent.as_string())

    def test_failed_delivery_retries_without_secrets(self):
        from contextlib import ExitStack
        with ExitStack() as stack:
            for ctx in self.smtp_config():
                stack.enter_context(ctx)
            connection = stack.enter_context(patch.object(w.smtplib, "SMTP_SSL"))
            client = connection.return_value.__enter__.return_value
            client.login.side_effect = smtplib.SMTPAuthenticationError(535, b"denied")
            self.assertFalse(w.notify("inventory-feed", "Job signaled failure"))

    def test_missing_credentials_and_invalid_transport_rejected(self):
        with patch.object(w, "NOTIFICATION_CHANNEL", "smtp"), patch.object(w, "SMTP_HOST", ""):
            with self.assertRaisesRegex(ValueError, "SMTP requires"):
                w.validate_delivery_config()
        with patch.object(w, "NOTIFICATION_CHANNEL", "sms"):
            with self.assertRaisesRegex(ValueError, "NOTIFICATION_CHANNEL"):
                w.validate_delivery_config()

    def test_enqueue_under_smtp_without_webhook(self):
        from contextlib import ExitStack
        with TemporaryDirectory() as tmp, ExitStack() as stack:
            stack.enter_context(patch.object(w, "DATA", Path(tmp)))
            stack.enter_context(patch.object(w, "NOTIFICATION_CHANNEL", "smtp"))
            stack.enter_context(patch.object(w, "WEBHOOK_URL", ""))
            with w.connection() as db:
                db.execute("""CREATE TABLE notification_queue
                    (id INTEGER PRIMARY KEY,job TEXT,reason TEXT,created REAL,attempt INTEGER DEFAULT 0,next_attempt REAL,delivered REAL)""")
                w.queue_notification(db, "inventory-feed", "failure")
            with w.connection() as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM notification_queue").fetchone()[0], 1)

if __name__ == "__main__":
    unittest.main()
