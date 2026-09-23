"""Guarded tools: read/search/edit/run with deny-lists and budgets.

Security model (explainable in one paragraph):
- Every path is resolved against the workspace *root*; anything escaping the
  root (``..``) or pointing at a secret fragment (``.env``, ``.ssh``,
  ``.config/gh``, ``hosts.yml``, ``id_ed25519``, ``.npmrc``) raises
  ``ValueError`` before any I/O.
- ``run`` never passes user text to a shell blindly: destructive patterns
  (``rm -rf /``, ``mkfs``, fork bombs, ``shutdown``/``reboot``, ``nc``,
  ``curl … | sh``) are denied first, then the command must start with an
  allow-listed read-only/test prefix (``pytest``, ``ruff``,
  ``python -m pytest``, ``node --check``, ``git status``/``git diff``).
- ``edit`` only applies when ``old`` matches the file exactly once, so a
  decision can never silently rewrite the wrong region.
- ``search`` compiles the pattern with ``re`` (invalid regex raises
  ``re.error``) and skips ``.git/.venv/__pycache__/node_modules``.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

DENY_PATHS = (".env", ".ssh", ".config/gh", "hosts.yml", "id_ed25519", ".npmrc")
DENY_CMD = re.compile(r"(rm\s+-rf\s+/( |$)|mkfs|:?\(\)\s*\{|:;\s*\}|shutdown|reboot|nc\s|ncat|curl\s+.*\|\s*(sh|bash))")
ALLOW_RUN_PREFIX = ("pytest", "ruff", "python -m pytest", "python -m ruff", "node --check", "git status", "git diff")
SKIP_DIRS = (".git", ".venv", "__pycache__", "node_modules", ".pytest_cache", ".ruff_cache")


def _guard_path(root: Path, p: str) -> Path:
    """Resolve *p* inside *root* or raise ``ValueError`` (escape or secret)."""
    if not p or p.strip() in ("", ".", "/"):
        raise ValueError("empty path")
    target = (root / p).resolve()
    root_resolved = root.resolve()
    if target != root_resolved and root_resolved not in target.parents:
        raise ValueError("path escapes workspace")
    lowered = str(target).lower()
    if any(d in lowered for d in DENY_PATHS):
        raise ValueError("blocked secret path")
    return target


def read(root: Path, p: str, limit: int = 200) -> str:
    """Read at most *limit* lines of *p*; raises ``ValueError``/``FileNotFoundError``."""
    t = _guard_path(root, p)
    if t.is_dir():
        raise ValueError("path is a directory")
    return "\n".join(t.read_text(errors="replace").splitlines()[:limit])


def search(root: Path, pattern: str, limit: int = 30) -> list[str]:
    """Regex-search workspace files; returns relative paths (max *limit*)."""
    out: list[str] = []
    rx = re.compile(pattern)  # raises re.error on invalid pattern — intentional
    for f in root.rglob("*"):
        if len(out) >= limit:
            break
        if f.is_file() and not any(x in f.parts for x in SKIP_DIRS):
            try:
                text = f.read_text(errors="replace")
            except OSError:
                continue
            if rx.search(text):
                out.append(str(f.relative_to(root)))
    return out


def edit(root: Path, p: str, old: str, new: str) -> str:
    """Replace *old* with *new* in *p*; *old* must occur exactly once.

    Raises:
        ValueError: on empty ``old``, zero matches, or ambiguous (>1) matches.
    """
    if not old:
        raise ValueError("old_text must not be empty")
    t = _guard_path(root, p)
    text = t.read_text(errors="replace")
    count = text.count(old)
    if count == 0:
        raise ValueError("old_text not found")
    if count > 1:
        raise ValueError("old_text must match exactly once")
    t.write_text(text.replace(old, new))
    return f"edited {p}"


def run(root: Path, cmd: str, timeout: int = 120) -> str:
    """Run an allow-listed command; deny destructive patterns first.

    Returns the last 4000 chars of combined stdout+stderr. Raises
    ``ValueError`` for blocked/non-allow-listed commands and propagates
    ``subprocess.TimeoutExpired`` on timeout.
    """
    cmd = cmd.strip()
    if not cmd:
        raise ValueError("empty command")
    if DENY_CMD.search(cmd):
        raise ValueError("blocked command")
    if not cmd.startswith(ALLOW_RUN_PREFIX):
        raise ValueError(f"command not allow-listed: {cmd!r}")
    r = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True, timeout=timeout)
    return (r.stdout + r.stderr)[-4000:]
