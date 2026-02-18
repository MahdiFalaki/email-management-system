from __future__ import annotations

"""Local retrieval pipeline for app records used as chatbot context."""

import re
from dataclasses import dataclass

from utils.db import DatabaseManager


TOKEN_RE = re.compile(r"[a-z0-9_@.\-]+")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
URL_RE = re.compile(r"https?://\S+")


@dataclass(frozen=True)
class RAGChunk:
    """Normalized retrieval unit built from one app record fragment."""

    chunk_id: str
    text: str
    source_type: str
    source_id: str
    sensitivity: str = "medium"


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def _mask_sensitive_text(text: str) -> str:
    masked = EMAIL_RE.sub("[redacted-email]", text)
    return URL_RE.sub("[redacted-url]", masked)


def _clip(text: str, max_chars: int = 280) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return f"{compact[: max_chars - 3]}..."


def build_rag_chunks(db: DatabaseManager) -> list[RAGChunk]:
    """Build retrievable chunks from profiles, templates, sent emails, and user profile."""
    chunks: list[RAGChunk] = []

    profiles = db.get_all_profiles()
    templates = db.get_all_templates()
    sent_emails = db.get_all_sent_emails()
    user_profile = db.get_user_profile()

    for idx, profile in enumerate(profiles, start=1):
        profile_text = (
            f"Profile: {profile.get('name', 'N/A')} | "
            f"Email: {_mask_sensitive_text(profile.get('email', 'N/A'))} | "
            f"Title: {profile.get('title', 'N/A')} | "
            f"Profession: {profile.get('profession', 'N/A')}"
        )
        chunks.append(
            RAGChunk(
                chunk_id=f"profile-{idx}",
                text=profile_text,
                source_type="profile",
                source_id=str(idx),
                sensitivity="high",
            )
        )

    for idx, template in enumerate(templates, start=1):
        template_text = (
            f"Template: {template.get('name', 'N/A')} | "
            f"Body: {_clip(template.get('body', ''))}"
        )
        chunks.append(
            RAGChunk(
                chunk_id=f"template-{idx}",
                text=template_text,
                source_type="template",
                source_id=str(idx),
                sensitivity="low",
            )
        )

    recent_emails = sent_emails[-20:]
    for idx, email in enumerate(recent_emails, start=1):
        recipients = ", ".join(email.get("recipients", []))
        sent_email_text = (
            f"Sent email | Subject: {email.get('subject', 'N/A')} | "
            f"Recipients: {_mask_sensitive_text(recipients)} | "
            f"Date: {email.get('sent_date', 'N/A')} | "
            f"Body excerpt: {_clip(email.get('body', ''))}"
        )
        chunks.append(
            RAGChunk(
                chunk_id=f"sent-email-{idx}",
                text=sent_email_text,
                source_type="sent_email",
                source_id=str(idx),
                sensitivity="high",
            )
        )

    if user_profile:
        profile_text = (
            f"User profile | Name: {user_profile.get('name', 'N/A')} | "
            f"Title: {user_profile.get('title', 'N/A')} | "
            f"Profession: {user_profile.get('profession', 'N/A')} | "
            f"Signature: {_clip(user_profile.get('signature', ''))}"
        )
        chunks.append(
            RAGChunk(
                chunk_id="user-profile-1",
                text=profile_text,
                source_type="user_profile",
                source_id="1",
                sensitivity="medium",
            )
        )

    return chunks


def retrieve_relevant_chunks(query: str, chunks: list[RAGChunk], top_k: int = 6) -> list[RAGChunk]:
    """Rank chunks by token overlap with the query and return top-k results."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return chunks[:top_k]

    scored: list[tuple[float, RAGChunk]] = []
    for chunk in chunks:
        chunk_tokens = _tokenize(chunk.text)
        if not chunk_tokens:
            continue

        overlap = query_tokens.intersection(chunk_tokens)
        if not overlap:
            continue

        score = len(overlap) / (len(chunk_tokens) ** 0.5)
        scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:top_k]]


def format_retrieved_context(chunks: list[RAGChunk]) -> str:
    """Format selected chunks into a compact context block for system messages."""
    if not chunks:
        return "No relevant records were retrieved from app data."

    lines = []
    for chunk in chunks:
        lines.append(
            f"- [{chunk.source_type}#{chunk.source_id} | sensitivity={chunk.sensitivity}] {chunk.text}"
        )
    return "\n".join(lines)
