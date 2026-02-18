from __future__ import annotations

"""AWS Bedrock Titan provider adapter used by the shared LLM service layer."""

import os
import time

from llm.types import ModelResponse

try:
    import boto3
except Exception:  # pragma: no cover - environment-dependent
    boto3 = None


def _get_bedrock_model_id() -> str:
    return os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")


def _get_bedrock_region() -> str:
    return os.getenv("AWS_REGION", "us-east-1")


def _build_converse_payload(messages: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    system_blocks: list[dict] = []
    conversation: list[dict] = []
    for message in messages:
        role = message.get("role", "user")
        content = (message.get("content") or "").strip()
        if not content:
            continue
        if role == "system":
            system_blocks.append({"text": content})
        elif role in {"user", "assistant"}:
            conversation.append({"role": role, "content": [{"text": content}]})

    # Bedrock Converse requires the first conversation message to be from the user.
    while conversation and conversation[0].get("role") != "user":
        conversation.pop(0)

    return system_blocks, conversation


def invoke_bedrock_titan(messages: list[dict[str, str]]) -> ModelResponse:
    """Execute a Bedrock Converse call and normalize output/metrics."""
    model_id = _get_bedrock_model_id()
    if boto3 is None:
        return ModelResponse(
            provider="bedrock",
            model=model_id,
            text=None,
            error="boto3 is not installed. Add boto3 to requirements.txt and install dependencies.",
        )

    started = time.perf_counter()
    try:
        client = boto3.client("bedrock-runtime", region_name=_get_bedrock_region())
        system, conversation = _build_converse_payload(messages)
        if not conversation:
            conversation = [{"role": "user", "content": [{"text": "Hello"}]}]
        result = client.converse(
            modelId=model_id,
            messages=conversation,
            system=system,
            inferenceConfig={"temperature": 0.3, "maxTokens": 500},
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        output_text = ""
        output = result.get("output", {})
        message = output.get("message", {})
        for block in message.get("content", []):
            if "text" in block:
                output_text += block.get("text", "")
        output_text = output_text.strip()

        usage = result.get("usage", {})
        prompt_tokens = usage.get("inputTokens")
        completion_tokens = usage.get("outputTokens")
        total_tokens = usage.get("totalTokens")
        if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
            total_tokens = prompt_tokens + completion_tokens

        metrics = {
            "latency_ms": elapsed_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "response_chars": len(output_text),
        }
        return ModelResponse(provider="bedrock", model=model_id, text=output_text or None, metrics=metrics)
    except Exception as exc:
        return ModelResponse(provider="bedrock", model=model_id, text=None, error=str(exc))
