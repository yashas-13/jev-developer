"""Typed errors: every failure has a code, message, and hint.

Codes: E_PATH, E_SECRET, E_CMD, E_EDIT, E_CONFIG, E_PROVIDER, E_TIMEOUT, E_BUDGET.
``JevError`` carries ``code``; tools/agent raise it instead of bare ValueError
(ValueError is still accepted by old callers since JevError subclasses it).
"""
from __future__ import annotations


class JevError(ValueError):
    def __init__(self, code: str, message: str, hint: str = ""):
        super().__init__(message)
        self.code = code
        self.hint = hint

    def __str__(self) -> str:
        base = f"[{self.code}] {super().__str__()}"
        return f"{base} Hint: {self.hint}" if self.hint else base
