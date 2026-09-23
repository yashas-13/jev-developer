"""Config: layered defaults -> .jev/config.yaml -> env (JEV_*) -> CLI flags.

Precedence (highest wins): CLI flag > JEV_* env > .jev/config.yaml > defaults.
``load(root, overrides)`` returns a validated dict; unknown keys raise.
``init_config(root)`` writes a commented starter file (never overwrites).
"""
from __future__ import annotations

import os
from pathlib import Path

DEFAULTS = {
    "max_steps": 12,
    "model": "openai/gpt-4o-mini",
    "base_url": "https://openrouter.ai/api/v1",
    "log_level": "INFO",
    "allow_run": ["pytest", "ruff", "python -m pytest", "node --check", "git status", "git diff"],
    "trace": True,
}

ENV_MAP = {
    "JEV_MAX_STEPS": ("max_steps", int),
    "JEV_MODEL": ("model", str),
    "JEV_BASE_URL": ("base_url", str),
    "JEV_LOG_LEVEL": ("log_level", str),
}

STARTER = """# JEV-Developer config. Env JEV_* overrides these values.
max_steps: 12
model: openai/gpt-4o-mini
base_url: https://openrouter.ai/api/v1
log_level: INFO
trace: true
"""


def init_config(root: Path) -> Path:
    """Write .jev/config.yaml starter if missing; return its path."""
    path = root / ".jev" / "config.yaml"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(STARTER)
    return path


def load(root: Path, overrides: dict | None = None) -> dict:
    """Load and validate config. Raises ValueError on unknown keys/bad types."""
    cfg = dict(DEFAULTS)
    path = root / ".jev" / "config.yaml"
    if path.exists():
        try:
            import yaml  # type: ignore

            data = yaml.safe_load(path.read_text()) or {}
        except ImportError:
            data = {}
        except Exception as e:
            raise ValueError(f"bad config {path}: {e}")
        for k, v in data.items():
            if k not in DEFAULTS:
                raise ValueError(f"unknown config key: {k}")
            cfg[k] = v
    for env, (key, cast) in ENV_MAP.items():
        if os.environ.get(env):
            try:
                cfg[key] = cast(os.environ[env])
            except ValueError:
                raise ValueError(f"bad {env}={os.environ[env]!r}")
    for k, v in (overrides or {}).items():
        if k not in DEFAULTS:
            raise ValueError(f"unknown config key: {k}")
        if v is not None:
            cfg[k] = v
    if not isinstance(cfg["max_steps"], int) or not 1 <= cfg["max_steps"] <= 100:
        raise ValueError("max_steps must be 1..100")
    return cfg
