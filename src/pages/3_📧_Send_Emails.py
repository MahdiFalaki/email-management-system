from datetime import datetime, time, timedelta

import streamlit as st

from utils.db import DatabaseManager
from utils.helpers import send_email

db = DatabaseManager()


def main():
    st.title("📧 Send Email")
    st.caption("Compose, schedule, and set reminders with a live preview.")
    st.divider()

    # Preserve schedule inputs across reruns so users can change date/time without snapping back.
    if "schedule_date" not in st.session_state:
        st.session_state["schedule_date"] = datetime.now().date()
    if "schedule_time" not in st.session_state:
        st.session_state["schedule_time"] = time(hour=datetime.now().hour, minute=datetime.now().minute)

    profiles = db.get_all_profiles()
    templates = db.get_all_templates()
    profiles_by_id = {profile.doc_id: profile for profile in profiles}
    templates_by_id = {template.doc_id: template for template in templates}

    st.info(
        "Select recipients, pick a template, optionally add your signature, then choose Send Now, "
        "Schedule, or Add Reminder.",
        icon="ℹ️",
    )

    with st.container(border=True):
        st.subheader("Recipients & Template")
        col_left, col_right = st.columns([1.4, 1])

        with col_left:
            selected_profile_ids = st.multiselect(
                "Select Recipients",
                options=list(profiles_by_id.keys()),
                format_func=lambda profile_id: (
                    f"{profiles_by_id[profile_id]['name']} ({profiles_by_id[profile_id]['email']})"
                ),
                placeholder="Choose one or more contacts...",
                help="You can select multiple recipients.",
            )
            st.caption(f"Selected: {len(selected_profile_ids)} | Total profiles: {len(profiles)}")

        with col_right:
            selected_template_id = st.selectbox(
                "Select Template",
                options=list(templates_by_id.keys()),
                format_func=lambda template_id: templates_by_id[template_id]["name"],
                index=0 if templates else None,
                placeholder="Pick a template...",
                help="Use a saved template to fill the email body.",
            )
            add_signature = st.toggle("Add Signature", help="Append your saved signature to the email.")

    template_body = templates_by_id.get(selected_template_id, {}).get("body", "")
    if st.session_state.get("raw_email_template_id") != selected_template_id:
        st.session_state["raw_email"] = template_body
        st.session_state["raw_email_template_id"] = selected_template_id

    user_profile = db.get_user_profile()
    signature = user_profile.get("signature", "") if user_profile else ""

    st.divider()
    st.subheader("Content & Preview")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Raw Email Body**")
        st.text_area(
            "Edit the raw body if needed",
            height=320,
            key="raw_email",
            label_visibility="collapsed",
        )

    with col2:
        st.markdown("**Live Preview**")
        preview_body = st.session_state.get("raw_email", "")
        if add_signature:
            preview_body += f"\n\n{signature}"
        st.text_area(
            "Rendered preview",
            value=preview_body,
            height=320,
            key="preview_email",
            label_visibility="collapsed",
            disabled=True,
        )

    st.divider()
    st.subheader("Actions")
    can_send = bool(selected_profile_ids and selected_template_id is not None)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🚀 Send Now", use_container_width=True, disabled=not can_send):
            if can_send:
                errors = []
                for profile_id in selected_profile_ids:
                    profile = profiles_by_id[profile_id]
                    recipient_email = profile["email"]
                    subject = f"Email to {profile['name']}"
                    success = send_email(to=[recipient_email], subject=subject, contents=preview_body)
                    if success:
                        db.add_sent_email([recipient_email], subject, preview_body, datetime.now())
                    else:
                        errors.append(recipient_email)
                if errors:
                    st.error(f"Failed to send to: {', '.join(errors)}")
                else:
                    st.success("Emails sent successfully")
            else:
                st.error("Please select at least one recipient and a template")

    with col2:
        schedule_date = st.date_input(
            "Schedule Date",
            key="schedule_date",
            min_value=datetime.now().date(),
            help="Pick the date to send.",
        )
        schedule_time = st.time_input(
            "Schedule Time",
            key="schedule_time",
            value=st.session_state["schedule_time"],
            step=timedelta(minutes=5),
            help="Pick the time to send.",
        )
        if st.button("🗓️ Schedule", use_container_width=True, disabled=not can_send):
            if can_send:
                schedule_datetime = datetime.combine(schedule_date, schedule_time)
                for profile_id in selected_profile_ids:
                    profile = profiles_by_id[profile_id]
                    recipient_email = profile["email"]
                    subject = f"Email to {profile['name']}"
                    email_id = db.add_sent_email([recipient_email], subject, preview_body, schedule_datetime)
                    db.add_schedule(email_id, schedule_datetime)
                st.success(f"Emails scheduled for {schedule_datetime}")
            else:
                st.error("Please select at least one recipient and a template")

    with col3:
        reminder_days = st.number_input(
            "Reminder (days from now)",
            min_value=1,
            value=3,
            step=1,
            help="Create a reminder after this many days.",
        )
        if st.button("⏰ Add Reminder", use_container_width=True, disabled=not can_send):
            if can_send:
                reminder_date = datetime.now() + timedelta(days=reminder_days)
                for profile_id in selected_profile_ids:
                    profile = profiles_by_id[profile_id]
                    recipient_email = profile["email"]
                    subject = f"Email to {profile['name']}"
                    email_id = db.add_sent_email([recipient_email], subject, preview_body, datetime.now())
                    db.add_reminder(email_id, reminder_date)
                st.success(f"Reminders set for {reminder_date}")
            else:
                st.error("Please select at least one recipient and a template")


if __name__ == "__main__":
    main()
