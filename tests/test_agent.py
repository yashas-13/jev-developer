from pathlib import Path

from jev_developer.agent import run_task
from jev_developer.policy import choose
from jev_developer.tools import edit, read, run, search


def test_choose_reads_mentioned_file():
    d = choose("fix bug in server.py now", ["server.py", "other.py"], [])
    assert d.operation == "READ" and d.target == "server.py"


def test_blocked_secret_path(tmp_path: Path):
    try:
        read(tmp_path, ".env")
        assert False, "should block"
    except ValueError:
        pass


def test_blocked_command(tmp_path: Path):
    try:
        run(tmp_path, "rm -rf /")
        assert False, "should block"
    except ValueError:
        pass


def test_allowlisted_run(tmp_path: Path):
    (tmp_path / "x.txt").write_text("hi")
    out = run(tmp_path, "git status")
    assert isinstance(out, str)


def test_edit_once(tmp_path: Path):
    (tmp_path / "a.txt").write_text("hello world")
    edit(tmp_path, "a.txt", "world", "jev")
    assert (tmp_path / "a.txt").read_text() == "hello jev"


def test_run_task_done(tmp_path: Path):
    (tmp_path / "main.py").write_text("print(1)")
    res = run_task(tmp_path, "read the main file", max_steps=4)
    assert res["status"] in ("done", "budget", "needs-human-edit")
