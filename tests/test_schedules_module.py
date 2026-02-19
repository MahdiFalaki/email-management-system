from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pages.schedules_module import (  # noqa: E402
    build_schedule_rows,
    parse_iso_datetime,
    schedule_status,
    validate_future_schedule,
)
from utils.db import DatabaseManager  # noqa: E402


class ScheduleModuleTests(unittest.TestCase):
    """Unit tests for schedules module behavior."""

    def test_parse_iso_datetime_handles_invalid_input(self) -> None:
        self.assertIsNone(parse_iso_datetime(None))
        self.assertIsNone(parse_iso_datetime(""))
        self.assertIsNone(parse_iso_datetime("not-a-date"))

    def test_schedule_status_defaults_to_pending(self) -> None:
        self.assertEqual(schedule_status(None), "pending")
        self.assertEqual(schedule_status(""), "pending")
        self.assertEqual(schedule_status(" Pending "), "pending")

    def test_validate_future_schedule_rejects_past_time(self) -> None:
        now = datetime(2026, 2, 19, 12, 0, 0)
        past = now - timedelta(minutes=1)
        ok, message = validate_future_schedule(past, now_provider=lambda: now)
        self.assertFalse(ok)
        self.assertIn("future", message.lower())

    def test_build_schedule_rows_joins_email_and_sorts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "db.json"
            db = DatabaseManager(db_path=str(db_path))
            try:
                email_id_1 = db.add_sent_email(
                    recipients=["a@example.com"],
                    subject="Subject B",
                    body="Body",
                    sent_date=datetime(2026, 2, 20, 10, 0, 0),
                )
                email_id_2 = db.add_sent_email(
                    recipients=["b@example.com"],
                    subject="Subject A",
                    body="Body",
                    sent_date=datetime(2026, 2, 20, 9, 0, 0),
                )

                db.add_schedule(email_id_1, datetime(2026, 2, 21, 10, 0, 0))
                db.add_schedule(email_id_2, datetime(2026, 2, 21, 9, 0, 0))

                rows = build_schedule_rows(db)
                self.assertEqual(len(rows), 2)
                self.assertEqual(rows[0].subject, "Subject A")
                self.assertEqual(rows[1].subject, "Subject B")
                self.assertEqual(rows[0].status, "pending")
            finally:
                db.db.close()

    def test_build_schedule_rows_handles_missing_linked_email(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "db.json"
            db = DatabaseManager(db_path=str(db_path))
            try:
                # Link to a non-existing sent_email id on purpose.
                db.schedules.insert(
                    {
                        "email_id": 9999,
                        "schedule_date": datetime(2026, 2, 21, 10, 0, 0).isoformat(),
                    }
                )

                rows = build_schedule_rows(db)
                self.assertEqual(len(rows), 1)
                self.assertFalse(rows[0].has_linked_email)
                self.assertEqual(rows[0].subject, "Missing linked email")
            finally:
                db.db.close()


if __name__ == "__main__":
    unittest.main()
