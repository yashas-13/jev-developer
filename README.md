# JEV-Developer ⚡

Offline-first AI CLI coding agent with a **typed tool-call policy**: the model
*chooses* (`READ/SEARCH/EDIT/RUN/DONE/BLOCKED`) instead of emitting arbitrary
shell. Inspired by `jev-ultrafast` (one indexed choice per step, independent
verification).

## Why different (vs generic LLM CLIs)

| Capability | JEV-Developer | Typical LLM CLI |
|---|---|---|
| Action space | Typed, observed files/commands only | Free-form shell |
| Secret guard | Deny `.env/.ssh/gh hosts/keys` + workspace jail | Often none |
| Command guard | Allow-list (`pytest/ruff/node --check/git status\|diff`) + deny destructive patterns | Direct exec |
| Offline mode | Deterministic heuristic policy, zero API calls | Requires key |
| Verification | `benchmark` + 21 pytest contracts | Ad-hoc |

> Honest note: "bypass competitors" = architecture
> (choice-not-generation + guardrails + offline tests), not benchmark proof.
> Run `jev-dev benchmark` and extend `tests/`.

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
jev-dev chat --path ./myrepo     # REPL: /run /read /search /files /test /clear /help /quit
jev-dev tui --path ./myrepo      # full-screen: files sidebar + log, Tab switches pane, Enter sends
```

LLM mode (optional): set `JEV_API_KEY` + `JEV_BASE_URL`
(OpenRouter-compatible) + `JEV_MODEL`. Offline heuristic is the default.

TUI uses stdlib `curses` only (Termux-safe, no extra deps); falls back to
chat REPL if unavailable.

## How it works (full explanation)

**One loop, four stages:**

```text
1. OBSERVE  collect_files() → sorted code/text files (caches skipped)
2. CHOOSE   choose(goal, files, history) → one Decision(op, target, reason)
3. ACT      guarded tool: read / search / edit / run
4. VERIFY   log step → repeat (max 12) → done/budget/blocked/needs-human-edit
```

**Decision order** (`policy.py`): file named in goal → first unread file →
search (once, if asked) → `pytest -q` (if asked, after reads) → EDIT proposal
(if asked, after reads) → DONE. Targets are always observed, never invented.

**Safety** (`tools.py`): paths jailed to workspace; secrets (`.env`, `.ssh`,
gh hosts, keys, `.npmrc`) blocked case-insensitively; destructive commands
denied then allow-list checked; edits need exact-once `old` match; invalid
regex surfaced as error, loop never crashes (3 strikes → `blocked`); EDIT is
human-gated (`needs-human-edit` + filename, no autonomous writes).

**Interfaces** (`chat.py`/`tui.py`/`cli.py`): REPL with `/run /read /search
/files /test /clear /help /quit`; curses TUI with sidebar + log + status bar;
5 CLI commands (`run ask benchmark chat tui`). Details:
`docs/ARCHITECTURE.md`.

## Tests & validation

```bash
python -m pytest -v   # 21 passed (~1s), all offline
jev-dev benchmark     # 3 smoke checks → pass
```

Coverage: policy 9 + tools 7 + loop/chat/cli 5. Full map + latest run +
manual checklist: `docs/TEST_REPORT.md`. `DONE` is a claim, not proof —
re-run tests after every change.

## Layout

- `jev_developer/policy.py` — typed choice (`choose`, `Decision`, keyword sets)
- `jev_developer/tools.py` — guarded `read/search/edit/run` + deny/allow lists
- `jev_developer/agent.py` — `collect_files`, `run_task` loop (never raises)
- `jev_developer/chat.py` — `ChatSession` REPL + slash commands
- `jev_developer/tui.py` — curses TUI + REPL fallback
- `jev_developer/providers.py` — optional OpenAI-compatible `complete()`
- `jev_developer/cli.py` — `run/ask/benchmark/chat/tui`
- `tests/test_policy.py`, `test_tools.py`, `test_loop.py` — offline contracts
- `docs/ARCHITECTURE.md`, `docs/TEST_REPORT.md` — design + verification
