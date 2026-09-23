"""Production contracts: config, logging, errors, CLI surface.

Run: python -m pytest tests/test_prod.py -v
"""
import logging
from pathlib import Path

import pytest


def test_config_defaults_and_init(tmp_path: Path):
    from jev_developer.config import init_config, load

    cfg = load(tmp_path)
    assert cfg["max_steps"] == 12 and cfg["trace"] is True
    p = init_config(tmp_path)
    assert p.exists() and "max_steps" in p.read_text()
    # never overwrites
    p.write_text("custom: 1\n")
    assert init_config(tmp_path).read_text() == "custom: 1\n"


def test_config_unknown_key_and_bad_steps(tmp_path: Path):
    from jev_developer.config import load

    (tmp_path / ".jev").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".jev" / "config.yaml").write_text("nope: 1\n")
    with pytest.raises(ValueError, match="unknown config key"):
        load(tmp_path)
    (tmp_path / ".jev" / "config.yaml").write_text("max_steps: 999\n")
    with pytest.raises(ValueError, match="max_steps"):
        load(tmp_path)


def test_config_env_override(tmp_path: Path, monkeypatch):
    from jev_developer.config import load

    monkeypatch.setenv("JEV_MAX_STEPS", "5")
    assert load(tmp_path)["max_steps"] == 5
    monkeypatch.setenv("JEV_MAX_STEPS", "abc")
    with pytest.raises(ValueError, match="JEV_MAX_STEPS"):
        load(tmp_path)


def test_errors_have_codes():
    from jev_developer.errors import JevError

    e = JevError("E_PATH", "escaped", "stay inside workspace")
    assert isinstance(e, ValueError) and e.code == "E_PATH" and "Hint" in str(e)


def test_logging_redacts_and_traces(tmp_path: Path):
    from jev_developer.logging_util import get_logger, redact, write_trace

    assert "***" in redact("key=ghp_abcdef123456 rest")
    assert "hello" in redact("hello")
    log = get_logger()
    assert isinstance(log.level, int) and log.level == logging.INFO
    write_trace(tmp_path, {"event": "test", "x": 1})
    assert list((tmp_path / ".jev" / "logs").glob("*.jsonl"))


def test_provider_needs_key(monkeypatch):
    from jev_developer.errors import JevError
    from jev_developer import providers

    monkeypatch.delenv("JEV_API_KEY", raising=False)
    monkeypatch.delenv("TEXT_MODEL_API_KEY", raising=False)
    with pytest.raises(JevError) as ei:
        providers.complete([{"role": "user", "content": "hi"}])
    assert ei.value.code == "E_PROVIDER"


def test_cli_eight_commands():
    from typer.testing import CliRunner

    from jev_developer.cli import app

    out = CliRunner().invoke(app, ["--help"]).output
    for cmd in ("run", "ask", "benchmark", "chat", "tui", "init", "doctor", "version"):
        assert cmd in out


def test_doctor_and_version_and_init(tmp_path: Path):
    from typer.testing import CliRunner

    from jev_developer.cli import app

    r = CliRunner()
    assert r.invoke(app, ["version"]).exit_code == 0
    assert r.invoke(app, ["doctor", "--path", str(tmp_path)]).exit_code == 0
    assert r.invoke(app, ["init", "--path", str(tmp_path)]).exit_code == 0
    assert (tmp_path / ".jev" / "config.yaml").exists()
