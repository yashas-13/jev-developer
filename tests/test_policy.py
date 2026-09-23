"""Policy contracts: choose() is deterministic, observed-targets-only.

Run: python -m pytest tests/test_policy.py -v
"""
import pytest

from jev_developer.policy import OPS, Decision, choose


def test_mentioned_file_first():
    d = choose("fix bug in server.py now", ["server.py", "other.py"], [])
    assert d.operation == "READ" and d.target == "server.py"


def test_skips_visited_mention():
    d = choose("fix server.py", ["server.py", "other.py"], ["server.py"])
    assert d == Decision("READ", "other.py", "observe before acting")


def test_observe_before_act():
    d = choose("do something", ["b.py", "a.py"], [])
    assert (d.operation, d.target) == ("READ", "b.py")


def test_search_once_then_done():
    d = choose("find where login happens", [], [])
    assert d.operation == "SEARCH"
    d2 = choose("find where login happens", [], ["search:find where login ha"])
    assert d2.operation == "DONE"


def test_run_verify_after_all_read():
    assert choose("run tests please", ["a.py"], ["a.py"]).operation == "RUN"
    d = choose("run tests please", ["a.py"], ["a.py"])
    assert d.target == "pytest -q"


def test_edit_smallest_after_all_read():
    d = choose("fix the bug", ["a.py"], ["a.py"])
    assert (d.operation, d.target) == ("EDIT", "a.py")


def test_done_fallback():
    assert choose("hello", [], []).operation == "DONE"
    assert choose("hello", ["a.py"], ["a.py"]).operation == "DONE"


def test_rejects_unknown_op():
    with pytest.raises(ValueError):
        Decision("HACK", "x", "y")
    assert set(OPS) == {"READ", "SEARCH", "EDIT", "RUN", "DONE", "BLOCKED"}


def test_target_never_invented():
    files = ["real.py"]
    for goal in ("fix real.py", "do stuff", "run tests", "find things", "hello"):
        d = choose(goal, files, [])
        assert d.target in files or d.target in ("-", "pytest -q") or goal[:20] in d.target
