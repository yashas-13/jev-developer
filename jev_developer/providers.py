"""Provider: OpenAI-compatible chat for decisions, offline fallback otherwise."""
from __future__ import annotations

import os

import httpx


def complete(messages: list[dict], model: str | None = None) -> str:
    base = os.environ.get("JEV_BASE_URL", "https://openrouter.ai/api/v1")
    key = os.environ.get("JEV_API_KEY") or os.environ.get("TEXT_MODEL_API_KEY")
    model = model or os.environ.get("JEV_MODEL", "openai/gpt-4o-mini")
    if not key:
        raise RuntimeError("no API key")
    r = httpx.post(
        f"{base.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "messages": messages, "temperature": 0},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
