"""Agent loop: observe files -> typed decision -> guarded tool -> verify."""
from __future__ import annotations

from pathlib import Path

from .policy import choose
from .tools import edit, read, run, search


def collect_files(root: Path, limit: int = 50) -> list[str]:
    out = []
    for f in sorted(root.rglob("*")):
        if len(out) >= limit:
            break
        if f.is_file() and not any(x in f.parts for x in (".git", ".venv", "__pycache__", "node_modules", ".pytest_cache")):
            if f.suffix in (".py", ".js", ".ts", ".md", ".toml", ".json", ".txt"):
                out.append(str(f.relative_to(root)))
    return out


def run_task(root: Path, goal: str, max_steps: int = 12) -> dict:
    history: list[str] = []
    log: list[str] = []
    files = collect_files(root)
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
                search(root, goal[:40])
                history.append(f"search:{goal[:20]}")
            elif d.operation == "EDIT":
                return {"status": "needs-human-edit", "log": log, "file": d.target}
            elif d.operation == "RUN":
                run(root, d.target)
                history.append(d.target)
        except Exception as e:  # never crash loop
            log.append(f"error: {e}")
            history.append(d.target)
    return {"status": "budget", "log": log}
