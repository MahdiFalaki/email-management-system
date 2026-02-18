from __future__ import annotations

"""Orchestration layer for prompt building, provider calls, guardrails, and fallback."""

from llm.guardrails import (
    action_guardrail_message,
    contains_unsafe_action_claim,
    redact_sensitive_output,
    sanitize_user_prompt,
)
from llm.providers.bedrock_provider import invoke_bedrock_titan
from llm.providers.openai_provider import invoke_openai
from llm.prompts import SYSTEM_PROMPT, build_context_header
from llm.rag import build_rag_chunks, format_retrieved_context, retrieve_relevant_chunks
from llm.telemetry import log_inference_event
from llm.types import ModelResponse
from utils.db import DatabaseManager


def build_messages(prompt: str, chat_history: list[dict[str, str]], db: DatabaseManager) -> list[dict[str, str]]:
    """Compose model messages with system guidance, RAG context, and recent chat turns."""
    safe_prompt = sanitize_user_prompt(prompt)
    chunks = build_rag_chunks(db)
    retrieved_chunks = retrieve_relevant_chunks(safe_prompt, chunks, top_k=6)
    retrieved_context = format_retrieved_context(retrieved_chunks)

    built_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": build_context_header()},
        {"role": "system", "content": f"Retrieved context:\n{retrieved_context}"},
    ]
    for msg in chat_history[-8:]:
        if msg["role"] in ("user", "assistant"):
            built_messages.append({"role": msg["role"], "content": msg["content"]})
    # Avoid duplicating the current prompt when caller already appended it to chat history.
    last_message = built_messages[-1] if built_messages else None
    if not (
        last_message
        and last_message.get("role") == "user"
        and (last_message.get("content") or "").strip() == safe_prompt
    ):
        built_messages.append({"role": "user", "content": safe_prompt})
    return built_messages


def _apply_output_guardrails(response: ModelResponse) -> ModelResponse:
    """Enforce post-generation safety checks and optional sensitive-data redaction."""
    if response.text and contains_unsafe_action_claim(response.text):
        response.text = action_guardrail_message()
        response.metrics["guardrail_replaced"] = True
        return response
    if response.text:
        response.text = redact_sensitive_output(response.text)
    return response


def run_provider(
    provider: str,
    prompt: str,
    chat_history: list[dict[str, str]],
    db: DatabaseManager,
) -> ModelResponse:
    """Run one provider end-to-end with shared context, guardrails, and telemetry."""
    messages = build_messages(prompt, chat_history, db)

    if provider == "openai":
        result = invoke_openai(messages)
    elif provider == "bedrock":
        result = invoke_bedrock_titan(messages)
    else:
        return ModelResponse(
            provider=provider,
            model="unknown",
            text=None,
            error=f"Unsupported provider: {provider}",
        )

    result.metrics.setdefault("prompt_chars", len(prompt))
    result = _apply_output_guardrails(result)
    log_inference_event(prompt, result)
    return result


def test_provider_connection(provider: str) -> tuple[bool, str]:
    """Send a minimal ping to verify provider credentials/configuration."""
    ping_messages = [{"role": "user", "content": "Reply with: OK"}]
    if provider == "openai":
        result = invoke_openai(ping_messages)
    elif provider == "bedrock":
        result = invoke_bedrock_titan(ping_messages)
    else:
        return False, f"Unsupported provider: {provider}"

    if result.error:
        return False, f"{provider} connection failed for model '{result.model}': {result.error}"
    return True, f"{provider} connected successfully using model '{result.model}'."


def generate_fallback_response(prompt: str, db: DatabaseManager) -> str:
    """Return deterministic help text when LLM output is unavailable."""
    lowered = prompt.lower()
    profiles = db.get_all_profiles()
    templates = db.get_all_templates()

    if any(word in lowered for word in ["hello", "hi", "hey", "greetings"]):
        return "Hello! How can I help you with your emails today?"
    if any(word in lowered for word in ["template", "templates"]):
        if not templates:
            return "You do not have any templates yet. Add one on the Email Templates page."
        names = ", ".join(t["name"] for t in templates[:8])
        return f"You currently have {len(templates)} template(s): {names}."
    if any(word in lowered for word in ["recipient", "recipients", "contact", "contacts"]):
        if not profiles:
            return "You do not have any recipients yet. Add contacts on the Profiles page."
        names = ", ".join(p["name"] for p in profiles[:8])
        return f"You currently have {len(profiles)} contact(s): {names}."
    if any(word in lowered for word in ["send", "schedule", "reminder"]):
        return "Use the Send Emails page to send now, schedule messages, or create reminders."
    return (
        "I can help with drafting emails, templates, and recipients. "
        "If you want AI answers, set OPENAI_API_KEY (and optional OPENAI_MODEL) in your .env file."
    )
