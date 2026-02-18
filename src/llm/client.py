from __future__ import annotations

"""OpenAI client and model configuration helpers."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_openai_client() -> OpenAI | None:
    """Return a configured OpenAI client, or None when API key is missing."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def get_model_name() -> str:
    """Resolve OpenAI model name from env with a safe default."""
    return os.getenv("OPENAI_MODEL", "gpt-4.1-nano")
