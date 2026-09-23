# Production runbook — JEV-Developer v0.2.0

## Install (prod)

```bash
pip install jev-developer            # from PyPI (after release), or:
pip install -e ".[dev]"             # local dev install with pytest+ruff
jev-dev doctor                      # must show config ok
```

## Configure

Precedence: `--max-steps` flag > `JEV_*` env > `.jev/config.yaml` > defaults.

```bash
jev-dev init --path ./myrepo
cat ./myrepo/.jev/config.yaml
export JEV_MAX_STEPS=20 JEV_LOG_LEVEL=DEBUG   # optional overrides
```

## Operate

```bash
jev-dev run "goal" --path ./myrepo            # traced to .jev/logs/<date>.jsonl
jev-dev chat --path ./myrepo                  # interactive
JEV_LOG_LEVEL=DEBUG jev-dev run "goal" --path ./myrepo
```

## Observe

- Console logs: `INFO` default, `DEBUG` via `JEV_LOG_LEVEL`.
- Traces: `.jev/logs/<YYYYMMDD>.jsonl`, one JSON/line, secrets redacted.
- Health: `jev-dev doctor` before releases; `jev-dev version` for reports.

## Error codes

| Code | Where | Fix |
|---|---|---|
| `E_PATH` | path escapes workspace | stay inside `--path` root |
| `E_SECRET` | secret path | don't reference `.env/.ssh/keys` |
| `E_CMD` | blocked/non-listed cmd | use allow-listed test cmds |
| `E_EDIT` | bad/ambiguous edit | narrow `old` to one match |
| `E_CONFIG` | bad config | `jev-dev init`, fix key/range |
| `E_PROVIDER` | LLM key/network | set `JEV_API_KEY`, check URL |
| `E_TIMEOUT` | tool timeout | raise timeout / shrink task |
| `E_BUDGET` | max_steps hit | narrow goal / `--max-steps` |

## Release

```bash
python -m pytest -q && jev-dev benchmark
python -m build && twine upload dist/*
git tag v0.2.0 && git push origin v0.2.0
```
