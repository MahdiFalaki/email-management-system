from __future__ import annotations

"""Shared response types for provider-agnostic LLM service flows."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelResponse:
    """Standard model call result with output text, error, and metrics."""

    provider: str
    model: str
    text: str | None
    error: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
