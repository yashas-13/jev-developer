"""Typed tool-call policy: choose instead of generating arbitrary code.

Operations: READ, SEARCH, EDIT, RUN, DONE, BLOCKED.
Targets are observed files/commands only. Model never emits raw shell.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

OPS = ("READ", "SEARCH", "EDIT", "RUN", "DONE", "BLOCKED")


@dataclass
class Decision:
    operation: str
    target: str
    reason: str


def choose(goal: str, files: list[str], history: list[str]) -> Decision:
    g = goal.lower()
    # Prefer reading files mentioned in goal first.
    for f in files:
        base = f.lower().split("/")[-1]
        name = re.sub(r"\W+", "", base.split(".")[0])
        if name and name in re.sub(r"\W+", "", g) and f not in history:
            return Decision("READ", f, f"goal mentions {base}")
    unread = [f for f in files if f not in history]
    if unread:
        return Decision("READ", unread[0], "observe before acting")
    if any(k in g for k in ("test", "run", "pytest", "check")):
        return Decision("RUN", "pytest -q", "verify after edits")
    if any(k in g for k in ("fix", "add", "edit", "implement", "refactor")) and files:
        return Decision("EDIT", files[0], "apply smallest edit")
    return Decision("DONE", "-", "no further observed action")
