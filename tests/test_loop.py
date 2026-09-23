"""Agent + chat + CLI contracts.

Run: python -m pytest tests/test_loop.py -v
"""
from pathlib import Path

from jev_developer.agent import collect_files, run_task
from jev_developer.chat import ChatSession


def test_collect_sorted_skips_caches(tmp_path: Path):
    (tmp_path / "b.py").write_text("x")
    (tmp_path / "a.py").write_text("x")
    (tmp_path / "img.png").write_text("x")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "v.py").write_text("x")
    assert collect_files(tmp_path) == ["a.py", "b.py"]


def test_run_task_paths(tmp_path: Path):
    (tmp_path / "main.py").write_text("print(1)")
    assert run_task(tmp_path, "read the main file", 4)["status"] in ("done", "budget", "needs-human-edit")
    (tmp_path / "a.py").write_text("x")
    r = run_task(tmp_path, "fix the bug", 6)
    assert r["status"] == "needs-human-edit" and r["file"] == "a.py"
    assert run_task(tmp_path, "do something vague", 1)["status"] == "budget"


def test_run_task_never_raises(tmp_path: Path):
    assert run_task(tmp_path, "anything", 3)["status"] in ("done", "budget", "blocked", "needs-human-edit")


def test_chat_full(tmp_path: Path):
    (tmp_path / "main.py").write_text("print(1)")
    s = ChatSession(tmp_path)
    assert "/" in s.handle("/help")
    assert "main.py" in s.handle("/files")
    assert "print(1)" in s.handle("/read main.py")
    assert "(no matches)" in s.handle("/search zzz_no_match_xyz")
    assert "error" in s.handle("/read .env")
    assert "error" in s.handle("/search ([bad")
    assert "status=" in s.handle("/run read the main file")
    assert isinstance(s.handle("/test"), str)
    assert "Plan:" in s.handle("hello world")
    assert "history cleared" in s.handle("/clear")
    assert s.handle("/quit") == "quit"
    assert s.handle("exit") == "quit"
    assert s.handle("") == ""


def test_tui_and_cli():
    import jev_developer.tui as tui

    assert hasattr(tui, "run_tui")
    from typer.testing import CliRunner

    from jev_developer.cli import app

    r = CliRunner().invoke(app, ["--help"])
    assert r.exit_code == 0
    for cmd in ("run", "ask", "benchmark", "chat", "tui"):
        assert cmd in r.output
