from __future__ import annotations

"""OpenAI provider adapter used by the shared LLM service layer."""

import time

from llm.client import get_model_name, get_openai_client
from llm.types import ModelResponse


def invoke_openai(messages: list[dict[str, str]]) -> ModelResponse:
    """Execute a chat completion call and normalize output/metrics."""
    client = get_openai_client()
    model = get_model_name()
    if client is None:
        return ModelResponse(
            provider="openai",
            model=model,
            text=None,
            error="OPENAI_API_KEY is missing. Add it to your .env file.",
        )

    started = time.perf_counter()
    try:
        result = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        answer = (result.choices[0].message.content or "").strip()
        usage = getattr(result, "usage", None)
        metrics = {
            "latency_ms": elapsed_ms,
            "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
            "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
            "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
            "response_chars": len(answer),
        }
        return ModelResponse(provider="openai", model=model, text=answer or None, metrics=metrics)
    except Exception as exc:
        return ModelResponse(provider="openai", model=model, text=None, error=str(exc))
