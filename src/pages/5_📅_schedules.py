from __future__ import annotations

"""Schedules page: view, reschedule, and cancel scheduled emails."""

from datetime import date, datetime, time

import streamlit as st

from pages.schedules_module import (
    build_schedule_rows,
    combine_schedule_datetime,
    validate_future_schedule,
)
from utils.db import DatabaseManager

db = DatabaseManager()


def _status_badge(status: str) -> str:
    """Return a human-friendly status label."""
    icon_by_status = {
        "pending": "🟡",
        "sent": "🟢",
        "failed": "🔴",
        "cancelled": "⚪",
    }
    icon = icon_by_status.get(status, "🔵")
    return f"{icon} {status}"


def _default_date_and_time(target: datetime | None) -> tuple[date, time]:
    """Resolve initial date/time values for schedule edit inputs."""
    if target is None:
        now = datetime.now()
        return now.date(), now.time().replace(second=0, microsecond=0)
    return target.date(), target.time().replace(second=0, microsecond=0)


def _safe_date_input_value(default_date: date, min_date: date) -> date:
    """Keep Streamlit date input defaults inside configured bounds."""
    return default_date if default_date >= min_date else min_date


def main() -> None:
    """Render schedules list and actions for reschedule/cancel."""
    st.title("📅 Schedules")
    st.caption("View, reschedule, and cancel queued emails.")
    st.divider()

    rows = build_schedule_rows(db)
    if not rows:
        st.info("No scheduled emails yet. Create one from the Send Email page.", icon="ℹ️")
        return

    st.subheader("Scheduled Emails")
    for row in rows:
        with st.container(border=True):
            col1, col2 = st.columns([2.2, 1.2])

            with col1:
                st.markdown(f"**{row.subject}**")
                recipients_text = ", ".join(row.recipients) if row.recipients else "N/A"
                st.caption(f"Recipients: {recipients_text}")
                scheduled_text = (
                    row.schedule_datetime.strftime("%Y-%m-%d %H:%M")
                    if row.schedule_datetime
                    else "Unknown"
                )
                st.caption(f"Scheduled For: {scheduled_text}")
                st.caption(f"Schedule ID: {row.schedule_id}")
                st.caption(f"Status: {_status_badge(row.status)}")
                if not row.has_linked_email:
                    st.warning("Linked sent-email record is missing for this schedule.")

            with col2:
                today = datetime.now().date()
                default_date, default_time = _default_date_and_time(row.schedule_datetime)
                schedule_date = st.date_input(
                    "Date",
                    value=_safe_date_input_value(default_date, today),
                    key=f"schedule_date_{row.schedule_id}",
                    min_value=today,
                )
                schedule_time = st.time_input(
                    "Time",
                    value=default_time,
                    key=f"schedule_time_{row.schedule_id}",
                )

                if st.button("💾 Reschedule", key=f"reschedule_{row.schedule_id}", use_container_width=True):
                    new_target = combine_schedule_datetime(schedule_date, schedule_time)
                    is_valid, error_message = validate_future_schedule(new_target)
                    if not is_valid:
                        st.error(error_message)
                    else:
                        db.update_schedule(row.schedule_id, new_target)
                        st.success("Schedule updated successfully.")
                        st.rerun()

                if st.button("🗑️ Cancel", key=f"cancel_{row.schedule_id}", use_container_width=True):
                    db.delete_schedule(row.schedule_id)
                    st.success("Schedule cancelled.")
                    st.rerun()


if __name__ == "__main__":
    main()
