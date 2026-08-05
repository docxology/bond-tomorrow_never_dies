# tests/ — CARVER Test Suite

The `tests/` directory verifies the CARVER domain core, the BOND-API mission
adapter, manuscript token hydration, figure generation, and the thin CLIs.
**Zero mocks**: every test runs the real algorithms on real, deterministic
data.

## Files

| File | Covers |
|---|---|
| `test_media_manipulation.py` | network builders, belief diffusion, influence maximization, metrics, error branches |
| `test_narrative_control.py` | bounded-confidence opinion dynamics, polarization / bimodal / capture, critical reach |
| `test_stealth_detection.py` | radar equation, Marcum-Q, Swerling, ROC, detection range, error branches |
| `test_radar_waveform.py` | waveform generation, matched filter, PSLR, processing gain, detection-range gain |
| `test_gps_denial.py` | constellation, DOP, jamming/C-N0, UERE, cascades, error branches |
| `test_gnss_integrity.py` | chi-square math, parity space, RAIM thresholds, HPL/VPL, bias detection |
| `test_mission.py` | protocol conformance, `run_mission`, gadgets, discovery, serialization |
| `test_scenario.py` | canonical six-block scenario, determinism, input hash |
| `test_manuscript_variables.py` | config loading, token map, live `{{TOKEN}}` cross-reference gate |
| `test_figures.py` | all six figure generators |
| `test_scripts_smoke.py` | subprocess smoke of every phase CLI + `z_generate` |

## Key conventions

- **Zero-mock**: no mock objects — the suite enforces a strict no-mock
  policy (see `../docs/testing_philosophy.md`).
- **Deterministic**: fixed seed (7); `now=` overrides pin timestamps.
- **Branch coverage**: every `ValueError` validation branch in `src/` is
  exercised via `pytest.raises`.

Live test count + coverage: [`docs/_generated/COUNTS.md`](../docs/_generated/COUNTS.md).

## Run

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```
