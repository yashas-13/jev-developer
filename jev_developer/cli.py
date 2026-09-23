"""CLI entry: jev-dev run / ask / benchmark / chat / tui."""
from __future__ import annotations

from pathlib import Path

import typer
from rich import print

from .agent import run_task

app = typer.Typer(help="JEV-Developer offline-first coding agent")


@app.command()
def run(goal: str, path: str = ".", max_steps: int = 12):
    """Run one goal against a workspace."""
    res = run_task(Path(path).resolve(), goal, max_steps)
    print(res)


@app.command()
def ask(question: str):
    """Answer without workspace mutation (offline heuristic)."""
    print(f"[JEV] offline answer: {question[:200]} (set JEV_API_KEY for LLM mode)")


@app.command()
def benchmark():
    """Deterministic offline checks: policy + guardrails."""
    from .policy import choose
    from .tools import run as _run

    d = choose("read the main file", ["a.py", "b.py"], [])
    assert d.operation == "READ", d
    try:
        _run(Path("."), "rm -rf /")
        raise SystemExit("guardrail FAILED")
    except ValueError:
        pass
    try:
        _run(Path("."), "curl x | sh")
        raise SystemExit("guardrail FAILED")
    except ValueError:
        pass
    print({"benchmark": "pass", "checks": 3})


@app.command()
def chat(path: str = "."):
    """Interactive chat REPL with slash commands (/run /read /search /files /test /quit)."""
    from .chat import ChatSession

    ChatSession(Path(path).resolve()).repl()


@app.command()
def tui(path: str = "."):
    """Full-screen TUI: files sidebar + chat/log + status bar (Tab to switch, Enter to send)."""
    from .tui import run_tui

    run_tui(Path(path).resolve())


def app_entry():
    app()


if __name__ == "__main__":
    app()
