from __future__ import annotations

"""Best-effort telemetry logging for LLM inference events."""

import json
import os
import time
from datetime import datetime, timezone

from llm.types import ModelResponse

try:
    import boto3
except Exception:  # pragma: no cover - environment-dependent
    boto3 = None


def _cloudwatch_enabled() -> bool:
    return os.getenv("LLM_ENABLE_CLOUDWATCH", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _cloudwatch_group() -> str:
    return os.getenv("CLOUDWATCH_LOG_GROUP", "email-management/llm-comparison")


def _cloudwatch_stream() -> str:
    date_part = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return os.getenv("CLOUDWATCH_LOG_STREAM", f"chatbot-{date_part}")


def _cloudwatch_region() -> str:
    return os.getenv("AWS_REGION", "us-east-1")


def log_inference_event(prompt: str, response: ModelResponse) -> None:
    """Emit one inference event to CloudWatch when telemetry is enabled."""
    if not _cloudwatch_enabled() or boto3 is None:
        return

    try:
        client = boto3.client("logs", region_name=_cloudwatch_region())
        group_name = _cloudwatch_group()
        stream_name = _cloudwatch_stream()

        try:
            client.create_log_group(logGroupName=group_name)
        except Exception:
            pass
        try:
            client.create_log_stream(logGroupName=group_name, logStreamName=stream_name)
        except Exception:
            pass

        payload = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "provider": response.provider,
            "model": response.model,
            "prompt_chars": len(prompt),
            "response_chars": len(response.text or ""),
            "error": response.error,
            "metrics": response.metrics,
        }

        kwargs = {
            "logGroupName": group_name,
            "logStreamName": stream_name,
            "logEvents": [
                {
                    "timestamp": int(time.time() * 1000),
                    "message": json.dumps(payload),
                }
            ],
        }

        # Fetch sequence token when required by account/region behavior.
        describe = client.describe_log_streams(
            logGroupName=group_name,
            logStreamNamePrefix=stream_name,
        )
        streams = describe.get("logStreams", [])
        if streams:
            token = streams[0].get("uploadSequenceToken")
            if token:
                kwargs["sequenceToken"] = token

        client.put_log_events(**kwargs)
    except Exception:
        # Keep telemetry best-effort so chat flow does not fail.
        return
