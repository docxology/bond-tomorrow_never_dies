# COUNTS — CARVER (tomorrow_never_dies)

Live counts for this package. These are **generated**, not hand-authored:
re-run `uv run pytest tests/ --cov=src --cov-fail-under=90` after any change
and update the numbers below.

| Metric | Value | Command |
|---|---|---|
| Passing tests | 96 | `uv run pytest tests/ -q` |
| Skipped / failed | 0 / 0 | `uv run pytest tests/ -q` |
| Coverage (line + branch, `src/`) | 95.77% | `uv run pytest tests/ --cov=src` |
| Required gate | ≥ 90% line + branch | `pyproject.toml` → `[tool.coverage.report] fail_under` |

Generated 2026-08-04 (CARVER canonical scenario, seed 7).
