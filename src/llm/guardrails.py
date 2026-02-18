from __future__ import annotations

"""Input/output safety checks for chatbot requests and model responses."""

import os
import re


ACTION_PATTERNS = (
    re.compile(r"^\s*(please\s+)?(send|schedule|delete|remove|cancel)\b"),
    re.compile(r"\b(send|schedule|delete|remove|cancel)\b.*\b(now|right now|for me|immediately)\b"),
    re.compile(r"\b(send|schedule|delete|remove|cancel)\s+(this|that|it|email)\b"),
    re.compile(r"\b(create|set)\s+reminder\b"),
)

INFO_QUERY_PREFIXES = (
    "what",
    "which",
    "who",
    "when",
    "where",
    "why",
    "how",
    "list",
    "show",
    "tell me",
    "did i",
    "have i",
)

UNSAFE_ACTION_CLAIMS = (
    "i sent",
    "i have sent",
    "scheduled it",
    "i scheduled",
    "has been scheduled",
    "was scheduled",
    "has been sent",
    "was sent",
    "deleted it",
    "has been deleted",
    "was deleted",
    "removed it",
    "has been removed",
    "was removed",
    "done for you",
)

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
URL_RE = re.compile(r"https?://\S+")


def sanitize_user_prompt(prompt: str, max_chars: int = 1200) -> str:
    """Normalize whitespace and cap prompt size before model calls."""
    cleaned = " ".join(prompt.split())
    return cleaned[:max_chars]


def is_action_request(prompt: str) -> bool:
    """Detect execution-style requests that the chatbot must not perform."""
    lowered = prompt.lower().strip()

    # Do not block informational/history questions like:
    # "What subjects did I recently send to Charles?"
    if any(lowered.startswith(prefix) for prefix in INFO_QUERY_PREFIXES):
        return False

    return any(pattern.search(lowered) for pattern in ACTION_PATTERNS)


def contains_unsafe_action_claim(response: str) -> bool:
    """Flag responses that incorrectly claim actions were executed."""
    lowered = response.lower()
    return any(claim in lowered for claim in UNSAFE_ACTION_CLAIMS)


def redact_sensitive_output(text: str) -> str:
    """Mask emails/URLs in model output when redaction is enabled."""
    redact_enabled = os.getenv("LLM_REDACT_PII", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if not redact_enabled:
        return text

    masked = EMAIL_RE.sub("[redacted-email]", text)
    return URL_RE.sub("[redacted-url]", masked)


def action_guardrail_message() -> str:
    """Return a safe fallback when action execution is requested or claimed."""
    return (
        "I can draft and improve emails here, but I cannot execute actions directly. "
        "Please review and confirm actions on the Send Emails, Schedules, or Reminders pages."
    )
