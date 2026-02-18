from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB


class DatabaseManager:
    """Lightweight wrapper around TinyDB collections used in the app."""

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            db_path = str(Path(__file__).resolve().parents[2] / "email_manager.json")
        self.db = TinyDB(db_path)
        self.profiles = self.db.table("profiles")
        self.templates = self.db.table("templates")
        self.sent_emails = self.db.table("sent_emails")
        self.reminders = self.db.table("reminders")
        self.schedules = self.db.table("schedules")
        self.user_profile = self.db.table("user_profile")

    # Profiles -----------------------------------------------------------------
    def add_profile(self, name: str, email: str, title: str, profession: str) -> int:
        return self.profiles.insert(
            {"name": name, "email": email, "title": title, "profession": profession}
        )

    def get_profile(self, profile_id: int) -> dict[str, Any] | None:
        return self.profiles.get(doc_id=profile_id)

    def update_profile(self, profile_id: int, name: str, email: str, title: str, profession: str) -> None:
        self.profiles.update(
            {"name": name, "email": email, "title": title, "profession": profession},
            doc_ids=[profile_id],
        )

    def delete_profile(self, profile_id: int) -> None:
        self.profiles.remove(doc_ids=[profile_id])

    def get_all_profiles(self) -> list[dict[str, Any]]:
        return self.profiles.all()

    # Templates ----------------------------------------------------------------
    def add_template(self, name: str, body: str) -> int:
        return self.templates.insert({"name": name, "body": body})

    def get_template(self, template_id: int) -> dict[str, Any] | None:
        return self.templates.get(doc_id=template_id)

    def update_template(self, template_id: int, name: str, body: str) -> None:
        self.templates.update({"name": name, "body": body}, doc_ids=[template_id])

    def delete_template(self, template_id: int) -> None:
        self.templates.remove(doc_ids=[template_id])

    def get_all_templates(self) -> list[dict[str, Any]]:
        return self.templates.all()

    # Sent emails --------------------------------------------------------------
    def add_sent_email(self, recipients: list[str], subject: str, body: str, sent_date) -> int:
        return self.sent_emails.insert(
            {
                "recipients": recipients,
                "subject": subject,
                "body": body,
                "sent_date": sent_date.isoformat(),
            }
        )

    def get_sent_email(self, email_id: int) -> dict[str, Any] | None:
        return self.sent_emails.get(doc_id=email_id)

    def get_all_sent_emails(self) -> list[dict[str, Any]]:
        return self.sent_emails.all()

    # Reminders ----------------------------------------------------------------
    def add_reminder(self, email_id: int, reminder_date) -> int:
        return self.reminders.insert(
            {"email_id": email_id, "reminder_date": reminder_date.isoformat()}
        )

    def get_reminder(self, reminder_id: int) -> dict[str, Any] | None:
        return self.reminders.get(doc_id=reminder_id)

    def update_reminder(self, reminder_id: int, reminder_date) -> None:
        self.reminders.update({"reminder_date": reminder_date.isoformat()}, doc_ids=[reminder_id])

    def delete_reminder(self, reminder_id: int) -> None:
        self.reminders.remove(doc_ids=[reminder_id])

    def get_all_reminders(self) -> list[dict[str, Any]]:
        return self.reminders.all()

    # Schedules ----------------------------------------------------------------
    def add_schedule(self, email_id: int, schedule_date) -> int:
        return self.schedules.insert(
            {"email_id": email_id, "schedule_date": schedule_date.isoformat()}
        )

    def get_schedule(self, schedule_id: int) -> dict[str, Any] | None:
        return self.schedules.get(doc_id=schedule_id)

    def update_schedule(self, schedule_id: int, schedule_date) -> None:
        self.schedules.update({"schedule_date": schedule_date.isoformat()}, doc_ids=[schedule_id])

    def delete_schedule(self, schedule_id: int) -> None:
        self.schedules.remove(doc_ids=[schedule_id])

    def get_all_schedules(self) -> list[dict[str, Any]]:
        return self.schedules.all()

    # User profile -------------------------------------------------------------
    def set_user_profile(
        self, name: str, title: str, degree: str, university: str, profession: str, social_media: dict[str, str], signature: str
    ) -> int:
        self.user_profile.truncate()  # Remove existing profile
        return self.user_profile.insert(
            {
                "name": name,
                "title": title,
                "degree": degree,
                "university": university,
                "profession": profession,
                "social_media": social_media,
                "signature": signature,
            }
        )

    def get_user_profile(self) -> dict[str, Any] | None:
        profiles = self.user_profile.all()
        return profiles[0] if profiles else None

    def update_user_profile(
        self, name: str, title: str, degree: str, university: str, profession: str, social_media: dict[str, str], signature: str
    ) -> None:
        profiles = self.user_profile.all()
        if profiles:
            self.user_profile.update(
                {
                    "name": name,
                    "title": title,
                    "degree": degree,
                    "university": university,
                    "profession": profession,
                    "social_media": social_media,
                    "signature": signature,
                },
                doc_ids=[profiles[0].doc_id],
            )
        else:
            self.set_user_profile(
                name, title, degree, university, profession, social_media, signature
            )

    def delete_user_profile(self) -> None:
        self.user_profile.truncate()

    # Search -------------------------------------------------------------------
    def search_sent_emails(self, query: str) -> list[dict[str, Any]]:
        Email = Query()
        return self.sent_emails.search(
            (Email.recipients.search(query))
            | (Email.subject.search(query))
            | (Email.body.search(query))
        )
