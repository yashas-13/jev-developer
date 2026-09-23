"""Interactive chat session: multi-turn REPL with history, slash commands, step streaming."""
from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .agent import collect_files, run_task
from .policy import choose
from .tools import read, run, search

HELP = """Commands:
  /run <goal>     run agent loop on workspace
  /read <file>    read a file
  /search <pat>   regex search workspace
  /files          list observed files
  /test           run pytest -q
  /clear          clear history
  /help           this help
  /quit           exit
Anything else = chat (offline heuristic; set JEV_API_KEY for LLM mode)."""

BANNER = "[bold cyan]JEV-Developer[/] [dim]interactive chat · type /help[/]"


class ChatSession:
    def __init__(self, root: Path, console: Console | None = None):
        self.root = root
        self.console = console or Console()
        self.history: list[dict] = []

    def files(self) -> list[str]:
        return collect_files(self.root)

    def answer(self, text: str) -> str:
        """Offline heuristic answer grounded in workspace file list."""
        files = self.files()
        d = choose(text, files, [h.get("target", "") for h in self.history if isinstance(h, dict)])
        return (
            f"Plan: {d.operation} {d.target} ({d.reason}). "
            f"Workspace has {len(files)} files. Use /run to execute, /read to inspect."
        )

    def handle(self, line: str) -> str | None:
        """Returns output text, or 'quit' sentinel."""
        line = line.strip()
        if not line:
            return ""
        if line in ("/quit", "/exit", "quit", "exit"):
            return "quit"
        if line in ("/help", "help"):
            return HELP
        if line == "/clear":
            self.history.clear()
            return "history cleared"
        if line == "/files":
            fs = self.files()
            return "\n".join(fs[:50]) or "(no files)"
        if line.startswith("/read "):
            p = line[6:].strip()
            try:
                return read(self.root, p)[:4000]
            except Exception as e:
                return f"error: {e}"
        if line.startswith("/search "):
            pat = line[8:].strip()
            try:
                hits = search(self.root, pat)
                return "\n".join(hits) or "(no matches)"
            except Exception as e:
                return f"error: {e}"
        if line == "/test":
            try:
                return run(self.root, "pytest -q")[-3000:]
            except Exception as e:
                return f"error: {e}"
        if line.startswith("/run "):
            goal = line[5:].strip()
            res = run_task(self.root, goal)
            self.history.append({"op": "RUN", "target": goal})
            return "\n".join(res["log"][-12:]) + f"\nstatus={res['status']}"
        # plain chat turn
        out = self.answer(line)
        self.history.append({"op": "CHAT", "target": line})
        return out

    def repl(self) -> None:
        c = self.console
        c.print(Panel(BANNER, expand=False))
        c.print("[dim]Commands: /run /read /search /files /test /clear /help /quit[/]\n")
        while True:
            try:
                line = c.input("[bold green]jev>[/] ")
            except (EOFError, KeyboardInterrupt):
                c.print("\nbye")
                break
            out = self.handle(line)
            if out == "quit":
                c.print("bye")
                break
            if out:
                if out.startswith(("Commands:", "Plan:", "history", "error", "status")) or "\n" in out:
                    c.print(Panel(out[:6000], title="jev", expand=False))
                else:
                    c.print(Markdown(out[:4000]))
