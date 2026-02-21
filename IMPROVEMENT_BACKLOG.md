# Improvement Backlog

## P0
- Migrate dependency management from `requirements.txt` to `pyproject.toml` + `uv.lock`.
- Add one executable smoke test in CI (core module import + minimal run).

## P1
- Add `pytest` baseline and at least 3 regression tests for analysis pipeline.
- Add static checks (`ruff` or `flake8`) in CI.

## P2
- Add sample dataset fixture and reproducible benchmark command.
- Add release notes template for model/data updates.
