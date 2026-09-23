# Test report — JEV-Developer

## How to run (everything offline, no keys)

```bash
cd ~/jev-developer
pip install -e .
python -m pytest -v        # full suite, ~1s
jev-dev benchmark          # 3 smoke checks
printf '/help\n/files\n/quit\n' | jev-dev chat --path .
```

## Validate = what to check manually

1. `python -m pytest -v` → **21 passed** (policy 9, tools 7, loop 5).
2. `jev-dev benchmark` → `{'benchmark': 'pass', 'checks': 3}`.
3. `jev-dev --help` lists `run ask benchmark chat tui`.
4. `jev-dev chat` → `/files` lists repo files, `/read` shows content,
   `/read .env` → `error: blocked secret path`, `/quit` → `bye`.
5. `jev-dev tui` → sidebar + log render; `Tab`/`Enter` work; falls back
   to REPL if curses missing.

## Latest verified run (2026-09-23, Termux, Python 3.14.6, pytest 9.1.1)

```text
tests/test_loop.py: 5 passed (collect/run_task/chat/cli/tui)
tests/test_policy.py: 9 passed (mention/observe/search/run/edit/done/guards)
tests/test_tools.py: 7 passed (secrets/escape/search/edit/run)
21 passed in 1.04s
```

## Coverage map (requirement → test)

| Requirement | Test |
|---|---|
| Mentioned file read first | `test_mentioned_file_first` |
| Skip visited mention | `test_skips_visited_mention` |
| Observe before acting | `test_observe_before_act` |
| Search once then done | `test_search_once_then_done` |
| Run verify after reads | `test_run_verify_after_all_read` |
| Smallest edit gated | `test_edit_smallest_after_all_read`, `test_run_task_paths` |
| Done fallback | `test_done_fallback` |
| Invalid op rejected | `test_rejects_unknown_op` |
| Targets never invented | `test_target_never_invented` |
| Secrets blocked (6 patterns) | `test_secret_paths_blocked` |
| Escape/empty/dir blocked | `test_escape_empty_dir_blocked` |
| Missing + line limit | `test_read_missing_and_limit` |
| Search skips caches | `test_search_skips_caches` |
| Bad regex + result limit | `test_search_bad_regex_and_limit`, `test_chat_full` |
| Edit once/empty/missing/ambiguous | `test_edit_cases` |
| Destructive + non-listed cmds denied | `test_run_deny_and_allow` |
| Collect sorted, skips caches | `test_collect_sorted_skips_caches` |
| Loop never raises | `test_run_task_never_raises` |
| Chat all commands + guards | `test_chat_full` |
| CLI has 5 commands, TUI imports | `test_tui_and_cli` |

## Known limits (not covered)

- Live LLM (`providers.complete`) needs `JEV_API_KEY`; untested here.
- Full-screen TUI needs a real terminal; CI-tested via import only.
- `EDIT` writes require human approval by design — no autonomous-write test.
