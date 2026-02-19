from __future__ import annotations

"""Schedules module logic used by the Streamlit schedules page.

This module intentionally keeps business logic and formatting out of the UI file so
it can be tested without running Streamlit.
"""

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Callable

from utils.db import DatabaseManager


@dataclass(frozen=True)
class ScheduleRow:
    """View model for one schedule record rendered in the schedules page."""

    schedule_id: int
    email_id: int | None
    subject: str
    recipients: list[str]
    schedule_datetime: datetime | None
    status: str
    has_linked_email: bool


def parse_iso_datetime(raw_value: str | None) -> datetime | None:
    """Parse an ISO datetime string, returning None for invalid or empty inputs."""
    if not raw_value:
        return None
    try:
        return datetime.fromisoformat(raw_value)
    except (TypeError, ValueError):
        return None


def schedule_status(raw_status: str | None) -> str:
    """Normalize schedule status to a safe default."""
    if not raw_status:
        return "pending"
    normalized = raw_status.strip().lower()
    return normalized if normalized else "pending"


def build_schedule_rows(db: DatabaseManager) -> list[ScheduleRow]:
    """Build schedule rows joined with linked sent-email metadata.

    Rows are sorted by schedule datetime ascending; invalid/missing datetimes appear last.
    """
    rows: list[ScheduleRow] = []
    for schedule in db.get_all_schedules():
        email_id = schedule.get("email_id")
        linked_email = db.get_sent_email(email_id) if isinstance(email_id, int) else None

        recipients = []
        subject = "Missing linked email"
        if linked_email:
            recipients = list(linked_email.get("recipients", []))
            subject = linked_email.get("subject", "(No subject)")

        rows.append(
            ScheduleRow(
                schedule_id=schedule.doc_id,
                email_id=email_id if isinstance(email_id, int) else None,
                subject=subject,
                recipients=recipients,
                schedule_datetime=parse_iso_datetime(schedule.get("schedule_date")),
                status=schedule_status(schedule.get("status")),
                has_linked_email=linked_email is not None,
            )
        )

    rows.sort(
        key=lambda row: (
            row.schedule_datetime is None,
            row.schedule_datetime or datetime.max,
        )
    )
    return rows


def combine_schedule_datetime(schedule_date: date, schedule_time: time) -> datetime:
    """Build a datetime from UI date/time values."""
    return datetime.combine(schedule_date, schedule_time)


def validate_future_schedule(
    candidate: datetime,
    now_provider: Callable[[], datetime] = datetime.now,
) -> tuple[bool, str]:
    """Validate that schedule target is in the future."""
    if candidate <= now_provider():
        return False, "Scheduled time must be in the future."
    return True, ""

