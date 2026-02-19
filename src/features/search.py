from __future__ import annotations

"""Search feature logic for sent-email discovery."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class SearchFilters:
    """User-selected filters applied on top of keyword search results."""

    recipient_contains: str
    subject_contains: str
    date_from: date | None
    date_to: date | None


@dataclass(frozen=True)
class SearchResult:
    """Normalized result model used by the search page renderer."""

    email_id: int
    subject: str
    recipients: list[str]
    sent_date: datetime | None
    body_excerpt: str


def parse_sent_date(raw_value: str | None) -> datetime | None:
    """Parse stored sent date safely from ISO format."""
    if not raw_value:
        return None
    try:
        return datetime.fromisoformat(raw_value)
    except (TypeError, ValueError):
        return None


def build_excerpt(text: str | None, max_chars: int = 220) -> str:
    """Build a compact single-line excerpt for list views."""
    if not text:
        return ""
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return f"{compact[: max_chars - 3]}..."


def _contains_case_insensitive(haystack: str, needle: str) -> bool:
    return needle.strip().lower() in haystack.lower()


def apply_filters(records: list[dict], filters: SearchFilters) -> list[SearchResult]:
    """Apply recipient/subject/date filters and return normalized sorted results."""
    filtered: list[SearchResult] = []

    for record in records:
        sent_date = parse_sent_date(record.get("sent_date"))
        recipients = [str(item) for item in record.get("recipients", [])]
        subject = str(record.get("subject", "(No subject)"))
        body = str(record.get("body", ""))

        if filters.recipient_contains:
            recipients_text = ", ".join(recipients)
            if not _contains_case_insensitive(recipients_text, filters.recipient_contains):
                continue

        if filters.subject_contains and not _contains_case_insensitive(subject, filters.subject_contains):
            continue

        if filters.date_from and (sent_date is None or sent_date.date() < filters.date_from):
            continue

        if filters.date_to and (sent_date is None or sent_date.date() > filters.date_to):
            continue

        filtered.append(
            SearchResult(
                email_id=record.doc_id,
                subject=subject,
                recipients=recipients,
                sent_date=sent_date,
                body_excerpt=build_excerpt(body),
            )
        )

    # Latest sent first; unknown dates appear last.
    filtered.sort(key=lambda result: result.sent_date or datetime.min, reverse=True)
    return filtered

