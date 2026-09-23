"""Guarded tools: read/search/edit/run with deny-lists and budgets."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

DENY_PATHS = (".env", ".ssh", ".config/gh", "hosts.yml", "id_ed25519", ".npmrc")
DENY_CMD = re.compile(r"(rm\s+-rf\s+/( |$)|mkfs|:?\(\)\s*\{|:;\s*\}|shutdown|reboot|nc\s|ncat|curl\s+.*\|\s*(sh|bash))")
ALLOW_RUN_PREFIX = ("pytest", "ruff", "python -m pytest", "python -m ruff", "node --check", "git status", "git diff")


def _guard_path(root: Path, p: str) -> Path:
    target = (root / p).resolve()
    if target != root and root not in target.parents:
        raise ValueError("path escapes workspace")
    if any(d in str(target) for d in DENY_PATHS):
        raise ValueError("blocked secret path")
    return target


def read(root: Path, p: str, limit: int = 200) -> str:
    t = _guard_path(root, p)
    return "\n".join(t.read_text(errors="replace").splitlines()[:limit])


def search(root: Path, pattern: str, limit: int = 30) -> list[str]:
    out: list[str] = []
    rx = re.compile(pattern)
    for f in root.rglob("*"):
        if len(out) >= limit:
            break
        if f.is_file() and not any(x in f.parts for x in (".git", ".venv", "__pycache__", "node_modules")):
            try:
                text = f.read_text(errors="replace")
            except OSError:
                continue
            if rx.search(text):
                out.append(str(f.relative_to(root)))
    return out


def edit(root: Path, p: str, old: str, new: str) -> str:
    t = _guard_path(root, p)
    text = t.read_text(errors="replace")
    if text.count(old) != 1:
        raise ValueError("old_text must match exactly once")
    t.write_text(text.replace(old, new))
    return f"edited {p}"


def run(root: Path, cmd: str, timeout: int = 120) -> str:
    if DENY_CMD.search(cmd):
        raise ValueError("blocked command")
    if not cmd.startswith(ALLOW_RUN_PREFIX):
        raise ValueError(f"command not allow-listed: {cmd!r}")
    r = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True, timeout=timeout)
    return (r.stdout + r.stderr)[-4000:]
