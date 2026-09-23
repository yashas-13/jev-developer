"""Provider: OpenAI-compatible chat with retries, timeouts, typed errors.

Offline default: raises JevError E_PROVIDER when no key. With key: POSTs
chat/completions with exponential backoff (3 tries, 1s/2s/4s) and 60s
timeout. Never logs the key.
"""
from __future__ import annotations

import os
import time

import httpx

from .errors import JevError


def complete(messages: list[dict], model: str | None = None, tries: int = 3) -> str:
    base = os.environ.get("JEV_BASE_URL", "https://openrouter.ai/api/v1")
    key = os.environ.get("JEV_API_KEY") or os.environ.get("TEXT_MODEL_API_KEY")
    model = model or os.environ.get("JEV_MODEL", "openai/gpt-4o-mini")
    if not key:
        raise JevError("E_PROVIDER", "no API key", "set JEV_API_KEY for LLM mode; offline heuristic otherwise")
    last: Exception | None = None
    for attempt in range(tries):
        try:
            r = httpx.post(
                f"{base.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "messages": messages, "temperature": 0},
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError) as e:
            last = e
            time.sleep(2**attempt)
    raise JevError("E_PROVIDER", f"LLM call failed after {tries} tries: {last}", "check JEV_BASE_URL/JEV_MODEL/network")


