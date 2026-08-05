# COUNTS — CARVER (tomorrow_never_dies)

Live counts for this package. These are **generated from a real run**, not
hand-authored: re-run the commands below after any change and update the
table. No other file in this package quotes a coverage figure — they point
here or describe the gate instead.

| Metric | Value | Command |
|---|---|---|
| Passing tests | 187 | `uv run pytest tests/ -q` |
| Skipped / failed | 0 / 0 | `uv run pytest tests/ -q` |
| Coverage (line + branch, `src/`) | 98.83% | `uv run pytest tests/ --cov=src` |
| Required gate | ≥ 90% line + branch | `pyproject.toml` → `[tool.coverage.report] fail_under` |
| Statements / branches measured | 1249 / 454 | `uv run pytest tests/ --cov=src` |
| Modules in `src/tomorrow_never_dies/` | 11 | 6 concept cores + `scenario` + `mission` + `manuscript_variables` + `figures` + `__init__` |
| Declared concepts | 6 | `src/tomorrow_never_dies/__init__.py::CONCEPTS` |
| Figure generators | 6 | `src/tomorrow_never_dies/figures.py` (`FIGURE_BUILDERS`) |
| BOND gadgets | 9 | `src/tomorrow_never_dies/mission.py::GADGETS` |
| Manuscript tokens generated | 87 | `manuscript_variables.generate_variables` |
| Manuscript prose sections | 9 | `manuscript/[0-9]*.md` |

Coverage of `figures.py` fell from 100.00% to 99.41% in the audit-remediation
pass, and that is an improvement, not a regression: the old figure of 100%
came from a test that asserted six PNGs existed and exceeded 1000 bytes,
binding no figure content at all. The current tests compare plotted series
against the domain modules.

Per-module coverage at the measured run:

| Module | Coverage |
|---|---|
| `figures.py` | 99.41% |
| `scenario.py` | 100.00% |
| `stealth_detection.py` | 100.00% |
| `narrative_control.py` | 99.34% |
| `gnss_integrity.py` | 99.14% |
| `mission.py` | 98.81% |
| `gps_denial.py` | 98.68% |
| `radar_waveform.py` | 98.35% |
| `media_manipulation.py` | 97.72% |
| `manuscript_variables.py` | 96.15% |

Measured 2026-08-05 on Python 3.14.6 (darwin), CARVER canonical scenario,
seed 7.
