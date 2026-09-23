"""Agent loop: observe files -> typed decision -> guarded tool -> verify.

Loop contract:
- Each step: ``choose(goal, files, history)`` returns one typed Decision whose
  target is observed (never invented). The loop executes it via the matching
  guarded tool and records ``history`` so the same target is not retried.
- Tool errors never crash the loop: they are appended to ``log`` as
  ``error: …`` and the target is marked visited. Three consecutive errors
  return ``status="blocked"`` (guard against infinite failure loops).
- ``EDIT`` is human-gated: the loop stops with ``status="needs-human-edit"``
  and the file name instead of writing autonomously.
- ``DONE``/budget: ``"done"`` when the policy is satisfied, ``"budget"`` when
  ``max_steps`` is exhausted. ``DONE`` is a claim, not proof — callers must
  re-run tests (see ``docs/ARCHITECTURE.md``).
"""
from __future__ import annotations

from pathlib import Path

from .policy import choose
from .tools import edit, read, run, search

SKIP_DIRS = (".git", ".venv", "__pycache__", "node_modules", ".pytest_cache", ".ruff_cache")
CODE_SUFFIXES = (".py", ".js", ".ts", ".md", ".toml", ".json", ".txt")


def collect_files(root: Path, limit: int = 50) -> list[str]:
    """List up to *limit* code/text files under *root*, sorted, skipping caches."""
    out = []
    for f in sorted(root.rglob("*")):
        if len(out) >= limit:
            break
        if f.is_file() and not any(x in f.parts for x in SKIP_DIRS):
            if f.suffix in CODE_SUFFIXES:
                out.append(str(f.relative_to(root)))
    return out


def run_task(root: Path, goal: str, max_steps: int = 12) -> dict:
    """Run one goal; returns ``{"status", "log"[, "file"]}`` (never raises)."""
    history: list[str] = []
    log: list[str] = []
    files = collect_files(root)
    errors = 0
    for _ in range(max_steps):
        d = choose(goal, files, history)
        log.append(f"{d.operation} {d.target} ({d.reason})")
        if d.operation == "DONE":
            return {"status": "done", "log": log}
        if d.operation == "BLOCKED":
            return {"status": "blocked", "log": log}
        try:
            if d.operation == "READ":
                read(root, d.target)
                history.append(d.target)
            elif d.operation == "SEARCH":
                search(root, d.target if d.target else goal[:40])
                history.append(f"search:{d.target[:20]}")
            elif d.operation == "EDIT":
                return {"status": "needs-human-edit", "log": log, "file": d.target}
            elif d.operation == "RUN":
                run(root, d.target)
                history.append(d.target)
            else:
                log.append(f"error: unsupported operation {d.operation}")
                history.append(d.target)
            errors = 0
        except Exception as e:  # never crash loop
            errors += 1
            log.append(f"error: {e}")
            history.append(d.target)
            if errors >= 3:
                log.append("blocked: 3 consecutive tool errors")
                return {"status": "blocked", "log": log}
    return {"status": "budget", "log": log}
