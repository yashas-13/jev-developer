"""Structured logging for the agent: console + JSONL trace files.

Every run_task call emits one JSON line per step to
``<workspace>/.jev/logs/<utc-timestamp>.jsonl`` (best-effort, never raises).
Log levels follow ``JEV_LOG_LEVEL`` (DEBUG/INFO/WARNING/ERROR, default INFO).
Secrets in values are redacted (``JEV_API_KEY``, ``TEXT_MODEL_API_KEY``,
``ghp_``/``gho_`` tokens).
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

_SECRET_RE = re.compile(r"(gh[op]_[A-Za-z0-9_]+|sk-[A-Za-z0-9\-_]+|JEV_API_KEY\s*=\s*\S+)", re.IGNORECASE)

_configured = False


def get_logger(name: str = "jev") -> logging.Logger:
    """Return the shared agent logger (idempotent configuration)."""
    global _configured
    logger = logging.getLogger(name)
    if not _configured:
        level = getattr(logging, os.environ.get("JEV_LOG_LEVEL", "INFO").upper(), logging.INFO)
        logger.setLevel(level)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
            logger.addHandler(handler)
        _configured = True
    return logger


def redact(text: str) -> str:
    """Replace likely secrets with *** (safe for logs/traces)."""
    return _SECRET_RE.sub("***", text)


def write_trace(root: Path, event: dict) -> None:
    """Append one JSON event to today's trace file. Never raises."""
    try:
        import json

        logdir = root / ".jev" / "logs"
        logdir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        line = json.dumps({**event, "ts": datetime.now(timezone.utc).isoformat()})
        with open(logdir / f"{stamp}.jsonl", "a") as fh:
            fh.write(redact(line) + "\n")
    except Exception:
        pass
