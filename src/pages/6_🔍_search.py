from __future__ import annotations

"""Search page for discovering sent email history."""

import re
from datetime import datetime, timedelta

import streamlit as st

from features.search import SearchFilters, apply_filters
from utils.db import DatabaseManager

db = DatabaseManager()


def _render_result_card(result) -> None:
    """Render one normalized search result row as a card."""
    with st.container(border=True):
        st.markdown(f"**{result.subject}**")
        recipients_text = ", ".join(result.recipients) if result.recipients else "N/A"
        sent_text = result.sent_date.strftime("%Y-%m-%d %H:%M") if result.sent_date else "Unknown"
        st.caption(f"Recipients: {recipients_text}")
        st.caption(f"Sent: {sent_text} | Email ID: {result.email_id}")
        st.write(result.body_excerpt or "_(No body content)_")


def main() -> None:
    """Render search form and results for sent-email history."""
    st.title("🔍 Search")
    st.caption("Find sent emails by keyword with optional recipient, subject, and date filters.")
    st.divider()

    with st.container(border=True):
        st.subheader("Search Criteria")
        query = st.text_input(
            "Keyword",
            placeholder="Try: follow-up, interview, proposal, or an email address...",
            help="Search runs across recipients, subject, and body.",
        ).strip()

        col1, col2 = st.columns(2)
        with col1:
            recipient_contains = st.text_input(
                "Recipient contains (optional)",
                placeholder="e.g., mhdfalaki@gmail.com",
            ).strip()
            use_date_from = st.checkbox("Use Date from", value=False)
            default_from = datetime.now().date() - timedelta(days=90)
            date_from_value = st.date_input("Date from (optional)", value=default_from, disabled=not use_date_from)
        with col2:
            subject_contains = st.text_input(
                "Subject contains (optional)",
                placeholder="e.g., interview",
            ).strip()
            use_date_to = st.checkbox("Use Date to", value=False)
            date_to_value = st.date_input("Date to (optional)", value=datetime.now().date(), disabled=not use_date_to)

    date_from = date_from_value if use_date_from else None
    date_to = date_to_value if use_date_to else None

    if not query:
        st.info("Enter a keyword to start searching sent email history.", icon="ℹ️")
        return

    if date_from and date_to and date_from > date_to:
        st.error("Date range is invalid. `Date from` cannot be later than `Date to`.")
        return

    raw_matches = db.search_sent_emails(re.escape(query))
    filters = SearchFilters(
        recipient_contains=recipient_contains,
        subject_contains=subject_contains,
        date_from=date_from,
        date_to=date_to,
    )
    results = apply_filters(raw_matches, filters)

    st.divider()
    st.subheader("Results")
    st.caption(f"Keyword matches: {len(raw_matches)} | After filters: {len(results)}")

    if not results:
        st.warning("No results found for this query/filter combination.")
        return

    for result in results:
        _render_result_card(result)


if __name__ == "__main__":
    main()
