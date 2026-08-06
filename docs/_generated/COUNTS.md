# COUNTS — CARVER (tomorrow_never_dies)

Live counts for this package. These are **generated from a real run**, not
hand-authored: re-run the commands below after any change and update the
table. No other file in this package quotes a coverage figure — they point
here or describe the gate instead.

| Metric | Value | Command |
|---|---|---|
| Passing tests | 216 | `uv run pytest tests/ -q` |
| Skipped / failed | 0 / 0 | `uv run pytest tests/ -q` |
| Coverage (line + branch, `src/`) | 99.26% | `uv run pytest tests/ --cov=src` |
| Required gate | ≥ 90% line + branch | `pyproject.toml` → `[tool.coverage.report] fail_under` |
| Statements / branches measured | 1292 / 476 | `uv run pytest tests/ --cov=src` |
| Modules in `src/tomorrow_never_dies/` | 11 | 6 concept cores + `scenario` + `mission` + `manuscript_variables` + `figures` + `__init__` |
| Declared concepts | 6 | `src/tomorrow_never_dies/__init__.py::CONCEPTS` |
| Figure generators | 6 | `src/tomorrow_never_dies/figures.py` (`FIGURE_BUILDERS`) |
| BOND gadgets | 9 | `src/tomorrow_never_dies/mission.py::GADGETS` |
| Manuscript tokens generated | 90 | `manuscript_variables.generate_variables` |
| Manuscript prose sections | 9 | `manuscript/[0-9]*.md` |

The tokens grew from 87 to 90 in round 2 when the canonical scenario began
reporting the Swerling-1 detection range and the Barker-13 detection range and
resolution (see `TODO.md` Round-2). The remaining partial branches are
defensive numerical-stabilisation fallbacks (Lentz `FPMIN` clamps, series /
continued-fraction convergence exhaustion, Barabási–Albert pool exhaustion)
and one fixed-parameters-only figure branch; each is documented in `TODO.md`
rather than chased.

Per-module coverage at the measured run:

| Module | Coverage |
|---|---|
| `figures.py` | 99.41% |
| `scenario.py` | 100.00% |
| `stealth_detection.py` | 100.00% |
| `narrative_control.py` | 100.00% |
| `gnss_integrity.py` | 97.40% |
| `mission.py` | 100.00% |
| `gps_denial.py` | 100.00% |
| `radar_waveform.py` | 100.00% |
| `media_manipulation.py` | 98.35% |
| `manuscript_variables.py` | 100.00% |

Measured 2026-08-06 on Python 3.14.6 (darwin), CARVER canonical scenario,
seed 7.