"""CLI entry: jev-dev run / ask / benchmark / chat / tui / init / doctor / version."""
from __future__ import annotations

from pathlib import Path

import typer
from rich import print

from .agent import run_task

app = typer.Typer(help="JEV-Developer offline-first coding agent", no_args_is_help=True)


@app.command()
def run(goal: str = typer.Argument(..., help="Natural-language goal"),
        path: str = typer.Option(".", help="Workspace root"),
        max_steps: int | None = typer.Option(None, help="Override config max_steps (1-100)")):
    """Run one goal against a workspace."""
    from .config import load
    from .logging_util import get_logger, write_trace

    root = Path(path).resolve()
    cfg = load(root, {"max_steps": max_steps} if max_steps else {})
    log = get_logger()
    log.info("run goal=%r root=%s max_steps=%d", goal[:120], root, cfg["max_steps"])
    res = run_task(root, goal, cfg["max_steps"])
    if cfg["trace"]:
        write_trace(root, {"event": "run", "goal": goal[:200], **res})
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


@app.command()
def init(path: str = "."):
    """Write starter .jev/config.yaml (never overwrites)."""
    from .config import init_config

    p = init_config(Path(path).resolve())
    print(f"config: {p}")


@app.command()
def doctor(path: str = "."):
    """Check env: python, pytest, config, keys, trace dir. Exit 0 if healthy."""
    import shutil
    import sys

    from .config import load

    root = Path(path).resolve()
    checks = {
        "python": sys.version.split()[0],
        "pytest": shutil.which("pytest") is not None or "bundled",
        "node": shutil.which("node") is not None,
        "JEV_API_KEY": "set" if __import__("os").environ.get("JEV_API_KEY") else "missing (offline ok)",
    }
    try:
        cfg = load(root)
        checks["config"] = f"ok max_steps={cfg['max_steps']}"
    except Exception as e:
        checks["config"] = f"ERROR {e}"
    print(checks)


@app.command()
def version():
    """Print version."""
    from . import __version__

    print(f"jev-developer {__version__}")


def app_entry():
    app()


if __name__ == "__main__":
    app()
