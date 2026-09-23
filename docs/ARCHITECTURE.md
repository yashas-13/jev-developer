# Architecture — JEV-Developer

How the agent thinks, acts, and stays safe. One page, no hand-waving.

## 1. Big idea (30 seconds)

Most coding CLIs let the LLM emit **arbitrary shell**. JEV-Developer flips it:
the model only **chooses** one typed operation per step —
`READ / SEARCH / EDIT / RUN / DONE / BLOCKED` — against **observed** targets
(files on disk, allow-listed commands). Code owns execution. This is the same
choice-not-generation pattern as `jev-ultrafast` (browser agent), applied to
code workspaces.

## 2. Data flow

```text
workspace files ──collect_files()──▶ [a.py, b.py, ...] (observed, sorted)
        goal + files + history ──choose()──▶ Decision(op, target, reason)
        Decision ──guarded tool──▶ read/search/edit/run
        result ──append log/history──▶ next step (max 12)
        DONE / blocked / budget / needs-human-edit ──▶ return + verify
```

## 3. Modules

| File | Role | Key guarantee |
|---|---|---|
| `policy.py` | `choose(goal, files, history)` | Target always observed; order: mention→unread→search→run→edit→done |
| `tools.py` | `read/search/edit/run` | Jail + deny + allow-list; exact-once edits |
| `agent.py` | `collect_files/run_task` | Never raises; 3-strikes blocked; EDIT human-gated |
| `chat.py` | `ChatSession.handle/repl` | Same guards; slash commands; history |
| `tui.py` | `run_tui` (curses) | No extra deps; falls back to REPL |
| `providers.py` | `complete()` | Optional LLM; offline default |
| `cli.py` | `run/ask/benchmark/chat/tui` | Thin wiring only |

## 4. Policy order (why this sequence)

1. **Mention → READ**: if the goal names `server.py`, read it first (grounding).
2. **Unread → READ**: observe before acting; avoids editing blind.
3. **SEARCH** (once): only when goal says find/grep/locate.
4. **RUN `pytest -q`**: only after all files read + goal asks test/verify.
5. **EDIT (human-gated)**: only after all files read + goal asks fix/add.
6. **DONE**: nothing observed left to do. `DONE` is a claim — re-run tests.

## 5. Security model

- Paths resolved vs root; `..` escape → `ValueError`.
- Secret fragments (`.env`, `.ssh`, `.config/gh`, `hosts.yml`,
  `id_ed25519`, `.npmrc`) → `ValueError` before I/O. Case-insensitive.
- `run`: deny regex first (rm-rf-/, mkfs, fork bomb, shutdown, nc,
  curl|sh), then allow-list prefix check. Empty → rejected.
- `edit`: empty/zero/ambiguous `old` → rejected. No silent rewrites.
- `search`: invalid regex raises `re.error` (surfaced as `error:` in chat,
  never crashes loop).

## 6. Statuses

| Status | Meaning | Next step |
|---|---|---|
| `done` | Policy satisfied | Re-run tests to prove it |
| `needs-human-edit` | EDIT proposed, file named | Human reviews + applies |
| `budget` | `max_steps` hit | Narrow goal / raise budget |
| `blocked` | 3 consecutive tool errors | Fix workspace, retry |

## 7. Testing

`tests/test_policy.py` (9) + `test_tools.py` (7) + `test_loop.py` (5) = 21.
All offline, tmp dirs, ~1s. See each file's docstring for the coverage map.
`jev-dev benchmark` = 3 smoke checks (policy + 2 guardrails).
