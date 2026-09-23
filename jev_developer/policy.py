"""Typed tool-call policy: choose instead of generating arbitrary code.

Operations: READ, SEARCH, EDIT, RUN, DONE, BLOCKED.
Targets are observed files/commands only. Model never emits raw shell.

Decision order (deterministic, offline):
1. READ a file named in the goal (exact basename match, not yet visited).
2. READ the first unvisited file (observe before acting).
3. SEARCH when the goal asks to find/grep/locate and history has no search yet.
4. RUN ``pytest -q`` when the goal asks to test/verify and all files visited.
5. EDIT the first file when the goal asks to fix/add/implement and all files visited.
6. DONE otherwise. BLOCKED is reserved for the agent loop when tools fail
   repeatedly (see ``agent.run_task``); the pure policy never invents it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

OPS = ("READ", "SEARCH", "EDIT", "RUN", "DONE", "BLOCKED")

RUN_KEYWORDS = ("test", "run", "pytest", "check", "verify", "validate")
EDIT_KEYWORDS = ("fix", "add", "edit", "implement", "refactor", "update", "create")
SEARCH_KEYWORDS = ("find", "search", "grep", "locate", "where", "which file")


@dataclass
class Decision:
    operation: str
    target: str
    reason: str

    def __post_init__(self) -> None:
        if self.operation not in OPS:
            raise ValueError(f"unknown operation {self.operation!r}")


def _names(text: str) -> str:
    """Normalise text for filename matching: lowercase, alnum only."""
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def choose(goal: str, files: list[str], history: list[str]) -> Decision:
    """Pick the next typed operation for *goal* given observed *files*.

    Args:
        goal: Natural-language task, e.g. ``"fix bug in server.py"``.
        files: Observed workspace files (relative paths) — the only
            valid READ/EDIT targets.
        history: Already-visited targets (file paths or ``search:``/cmd markers).

    Returns:
        A :class:`Decision` whose target is always observed, never invented.
    """
    g = goal.lower()
    norm_goal = _names(goal)
    # 1. Prefer reading files mentioned in goal first.
    for f in files:
        base = f.lower().split("/")[-1]
        name = _names(base.split(".")[0])
        if name and name in norm_goal and f not in history:
            return Decision("READ", f, f"goal mentions {base}")
    # 2. Observe before acting.
    unread = [f for f in files if f not in history]
    if unread:
        return Decision("READ", unread[0], "observe before acting")
    # 3. Search when asked to locate something (once per goal).
    if any(k in g for k in SEARCH_KEYWORDS) and not any(h.startswith("search:") for h in history):
        return Decision("SEARCH", goal[:80], "goal asks to locate code")
    # 4. Verify after edits.
    if any(k in g for k in RUN_KEYWORDS):
        return Decision("RUN", "pytest -q", "verify after edits")
    # 5. Smallest edit.
    if any(k in g for k in EDIT_KEYWORDS) and files:
        return Decision("EDIT", files[0], "apply smallest edit")
    # 6. Nothing left to do.
    return Decision("DONE", "-", "no further observed action")
