"""Schedules page for viewing, rescheduling, and canceling scheduled emails."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from utils.db import DatabaseManager


db = DatabaseManager()


def _parse_iso_datetime(value: str | None) -> datetime | None:
    """Parse an ISO datetime string safely.

    Args:
        value: Datetime string in ISO format.

    Returns:
        Parsed ``datetime`` when valid; otherwise ``None``.
    """
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _get_schedule_context(schedule_doc_id: int, email_id: int) -> tuple[dict, datetime | None]:
    """Load linked email details and schedule datetime for one schedule record.

    Args:
        schedule_doc_id: TinyDB document ID for the schedule record.
        email_id: Linked sent-email document ID.

    Returns:
        Tuple of:
        - linked sent-email record (empty dict when unavailable),
        - parsed schedule datetime (``None`` when unavailable/invalid).
    """
    schedule = db.get_schedule(schedule_doc_id) or {}
    email = db.get_sent_email(email_id) or {}
    schedule_dt = _parse_iso_datetime(schedule.get("schedule_date"))
    return email, schedule_dt


def _render_schedule_actions(schedule_doc_id: int, schedule_dt: datetime | None) -> None:
    """Render reschedule and cancel actions for a single schedule row.

    Args:
        schedule_doc_id: TinyDB document ID for the schedule record.
        schedule_dt: Existing scheduled datetime (or ``None``).
    """
    default_dt = schedule_dt or datetime.now()

    date_col, time_col = st.columns(2)
    with date_col:
        new_date = st.date_input(
            "New date",
            value=default_dt.date(),
            min_value=datetime.now().date(),
            key=f"schedule_date_{schedule_doc_id}",
            label_visibility="collapsed",
        )
    with time_col:
        new_time = st.time_input(
            "New time",
            value=default_dt.time().replace(second=0, microsecond=0),
            key=f"schedule_time_{schedule_doc_id}",
            label_visibility="collapsed",
        )

    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if st.button("💾 Reschedule", key=f"reschedule_{schedule_doc_id}", use_container_width=True):
            new_datetime = datetime.combine(new_date, new_time)
            if new_datetime < datetime.now():
                st.error("Scheduled time must be in the future.")
            else:
                db.update_schedule(schedule_doc_id, new_datetime)
                st.success(f"Schedule updated to {new_datetime.strftime('%Y-%m-%d %H:%M')}")
                st.rerun()

    with action_col2:
        if st.button("🗑️ Cancel", key=f"cancel_{schedule_doc_id}", use_container_width=True):
            db.delete_schedule(schedule_doc_id)
            st.success("Schedule canceled.")
            st.rerun()


def _render_schedule_card(schedule: dict) -> None:
    """Render one schedule card with linked email details and actions.

    Args:
        schedule: TinyDB schedule document.
    """
    schedule_doc_id = schedule.doc_id
    email_id = schedule.get("email_id")
    email, schedule_dt = _get_schedule_context(schedule_doc_id, email_id)

    with st.container(border=True):
        top_col1, top_col2 = st.columns([3, 1])
        with top_col1:
            subject = email.get("subject", "(Missing linked email)")
            recipients = ", ".join(email.get("recipients", [])) or "N/A"
            st.markdown(f"**{subject}**")
            st.caption(f"Recipients: {recipients}")
            if schedule_dt:
                st.caption(f"Scheduled for: {schedule_dt.strftime('%Y-%m-%d %H:%M')}")
            else:
                st.caption("Scheduled for: invalid/missing datetime")
        with top_col2:
            st.caption(f"Schedule ID: {schedule_doc_id}")
            st.caption("Status: pending")

        _render_schedule_actions(schedule_doc_id, schedule_dt)


def main() -> None:
    """Render schedules page with upcoming items and management actions."""
    st.title("📅 Schedules")
    st.caption("View, reschedule, or cancel pending scheduled emails.")
    st.divider()

    schedules = db.get_all_schedules()

    if not schedules:
        st.info("No scheduled emails yet. Add one from the Send Email page.", icon="ℹ️")
        return

    st.subheader("Pending Schedules")
    for schedule in schedules:
        _render_schedule_card(schedule)


if __name__ == "__main__":
    main()
