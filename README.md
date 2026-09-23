# JEV-Developer ⚡

Offline-first AI CLI coding agent with a **typed tool-call policy**: the model *chooses* (`READ/SEARCH/EDIT/RUN/DONE/BLOCKED`) instead of emitting arbitrary shell. Inspired by `jev-ultrafast` (one indexed choice per step, independent verification).

## Why different (vs generic LLM CLIs)

| Capability | JEV-Developer | Typical LLM CLI |
|---|---|---|
| Action space | Typed, observed files/commands only | Free-form shell |
| Secret guard | Deny `.env/.ssh/gh hosts/keys` + workspace jail | Often none |
| Command guard | Allow-list (`pytest/ruff/node --check/git status|diff`) + deny destructive patterns | Direct exec |
| Offline mode | Deterministic heuristic policy, zero API calls | Requires key |
| Verification | `benchmark` + pytest contract tests | Ad-hoc |

> Honest note: "bypass competitors" = architecture (choice-not-generation + guardrails + offline tests), not benchmark proof. Run `jev-dev benchmark` and extend `tests/`.

## Install

```bash
cd ~/jev-developer
pip install -e .
jev-dev --help
```

## Use

```bash
jev-dev run "fix bug in server.py" --path ./myrepo
jev-dev ask "how do I run tests?"
jev-dev benchmark
```

LLM mode (optional): set `JEV_API_KEY` + `JEV_BASE_URL` (OpenRouter-compatible) + `JEV_MODEL`.

## Guardrails

- Paths jailed to workspace; secrets blocked.
- Only allow-listed read-only/test commands run; destructive patterns rejected.
- Edits require exact-once `old_text` match.
- Every run returns a step log; `DONE` is not proof — re-run tests.

## Layout

- `jev_developer/policy.py` — typed choice
- `jev_developer/tools.py` — guarded read/search/edit/run
- `jev_developer/agent.py` — loop
- `jev_developer/cli.py` — `run/ask/benchmark`
- `tests/test_agent.py` — offline contracts
