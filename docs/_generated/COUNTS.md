# COUNTS — CARVER (tomorrow_never_dies)

Live counts for this package. These are **generated**, not hand-authored:
re-run `uv run pytest tests/ --cov=src --cov-fail-under=90` after any change
and update the numbers below.

| Metric | Value | Command |
|---|---|---|
| Passing tests | 126 | `uv run pytest tests/ -q` |
| Skipped / failed | 0 / 0 | `uv run pytest tests/ -q` |
| Coverage (line + branch, `src/`) | 96.48% | `uv run pytest tests/ --cov=src` |
| Required gate | ≥ 90% line + branch | `pyproject.toml` → `[tool.coverage.report] fail_under` |
| Domain modules | 10 | `src/tomorrow_never_dies/*.py` (6 concept cores + scenario + adapter + vars + figures) |
| Figure generators | 6 | `src/tomorrow_never_dies/figures.py` |
| BOND gadgets | 9 | `src/tomorrow_never_dies/mission.py::GADGETS` |

Generated 2026-08-04 (CARVER canonical scenario, seed 7).
