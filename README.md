# JEV-Developer ⚡ (v0.2.0 — production grade)

Offline-first AI CLI coding agent with a **typed tool-call policy**: the model
*chooses* (`READ/SEARCH/EDIT/RUN/DONE/BLOCKED`) instead of emitting arbitrary
shell. Inspired by `jev-ultrafast` (one indexed choice per step, independent
verification).

## Production qualities (checklist)

| Quality | How | Proof |
|---|---|---|
| Config | `.jev/config.yaml` + `JEV_*` env + CLI flags, validated | `test_prod.py` (3 tests) |
| Logging | `JEV_LOG_LEVEL`, console + `.jev/logs/*.jsonl`, secret redaction | `test_logging_redacts_and_traces` |
| Typed errors | `JevError(code, msg, hint)`, 8 codes | `test_errors_have_codes` |
| Retries/timeouts | LLM 3 tries exp-backoff, 60s timeout; tool `run` timeout | `providers.py`, `test_provider_needs_key` |
| Health check | `jev-dev doctor` (python/pytest/node/keys/config) | manual + test |
| Versioning | `jev-dev version`, `__version__ 0.2.0` | test |
| Tests | 29 offline, ~3s | `python -m pytest -v` |
| Packaging | hatchling wheel, `dev` extras, `dist/` ignored | `pyproject.toml` |
| Guardrails | jail + deny + allow-list + exact-once edits + 3-strikes blocked | `test_tools.py` (7) |
| Docs | README + ARCHITECTURE + TEST_REPORT + PRODUCTION | `docs/` |

## Why different (vs generic LLM CLIs)

| Capability | JEV-Developer | Typical LLM CLI |
|---|---|---|
| Action space | Typed, observed files/commands only | Free-form shell |
| Secret guard | Deny `.env/.ssh/gh hosts/keys` + workspace jail | Often none |
| Command guard | Allow-list + deny destructive patterns | Direct exec |
| Offline mode | Deterministic heuristic, zero API calls | Requires key |
| Verification | `benchmark` + 29 pytest contracts | Ad-hoc |
| Ops | config/logging/traces/doctor/version/retries | Varies |

## Install

```bash
cd ~/jev-developer
pip install -e ".[dev]"
jev-dev --help
jev-dev init --path ./myrepo   # starter .jev/config.yaml
jev-dev doctor --path ./myrepo # health check
```

## Use

```bash
jev-dev run "fix bug in server.py" --path ./myrepo [--max-steps 20]
jev-dev ask "how do I run tests?"
jev-dev benchmark
jev-dev chat --path ./myrepo
jev-dev tui --path ./myrepo
jev-dev version
```

Env: `JEV_MAX_STEPS`, `JEV_MODEL`, `JEV_BASE_URL`, `JEV_LOG_LEVEL`,
`JEV_API_KEY` (optional LLM). File: `.jev/config.yaml` (see `jev-dev init`).
Traces: `.jev/logs/<date>.jsonl` (secrets redacted).

## How it works (full explanation)

```text
1. OBSERVE  collect_files() → sorted code/text files (caches skipped)
2. CHOOSE   choose(goal, files, history) → one Decision(op, target, reason)
3. ACT      guarded tool: read / search / edit / run
4. VERIFY   log step → repeat (max_steps) → done/budget/blocked/needs-human-edit
```

Decision order: named file → unread → SEARCH(once) → `pytest -q` → EDIT
(human-gated) → DONE. Targets always observed. `DONE` is a claim — re-run
tests. Details: `docs/ARCHITECTURE.md`.

## Tests & validation

```bash
python -m pytest -v   # 29 passed (~3s), all offline
jev-dev benchmark     # 3 smoke checks → pass
```

Coverage: policy 9 + tools 7 + loop/chat/cli 5 + prod 8. Full map:
`docs/TEST_REPORT.md`. Production ops: `docs/PRODUCTION.md`.

## Layout

- `jev_developer/policy.py` — typed choice
- `jev_developer/tools.py` — guarded `read/search/edit/run`
- `jev_developer/agent.py` — `collect_files`, `run_task` (never raises)
- `jev_developer/chat.py` — `ChatSession` REPL
- `jev_developer/tui.py` — curses TUI + REPL fallback
- `jev_developer/providers.py` — LLM `complete()` with retries
- `jev_developer/config.py` — layered config + validation
- `jev_developer/logging_util.py` — logger + redaction + JSONL traces
- `jev_developer/errors.py` — `JevError` codes
- `jev_developer/cli.py` — 8 commands
- `tests/` — `test_policy/test_tools/test_loop/test_prod`
- `docs/` — `ARCHITECTURE/TEST_REPORT/PRODUCTION`
