# Testing Philosophy

## Zero-mock policy

The suite enforces a strict no-mock policy: no `unittest.mock`, `MagicMock`,
`@patch`, or `create_autospec` anywhere in `tests/`. Tests exercise real
algorithms on real, deterministic data. This is the core tenet: mock tests
can pass while the mathematical logic is wrong.

## Coverage mechanics

The gate measures **line + branch** coverage over `src/tomorrow_never_dies/`
only (branch coverage is enabled in `pyproject.toml`):

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Live test count and achieved coverage are tracked in
[`docs/_generated/COUNTS.md`](../docs/_generated/COUNTS.md), not hardcoded.

## Test classes / coverage strategy

| File | Covers |
|---|---|
| `test_media_manipulation.py` | network builders, belief diffusion determinism, media effect, influence maximization, echo chamber, error branches |
| `test_narrative_control.py` | bounded-confidence dynamics, polarization / bimodal / capture, critical reach, error branches |
| `test_stealth_detection.py` | radar equation, Marcum-Q known values, Swerling closed form, ROC, detection range, error branches |
| `test_radar_waveform.py` | waveform generation, matched filter, PSLR, processing gain, detection-range gain, error branches |
| `test_gps_denial.py` | constellation, DOP identities, jamming/C-N0, UERE, cascade fixpoint + error branches |
| `test_gnss_integrity.py` | chi-square / normal quantiles, parity space, RAIM thresholds, HPL/VPL, noncentral bias detection, error branches |
| `test_mission.py` | protocol conformance, full `run_mission` flow, gadget registry, discovery, serialization round-trip |
| `test_scenario.py` | canonical six-block scenario keys, determinism, input-hash stability |
| `test_manuscript_variables.py` | config loading, token map, live `{{TOKEN}}` cross-reference gate |
| `test_figures.py` | all six figure generators write valid PNGs |
| `test_scripts_smoke.py` | subprocess smoke of every phase CLI + `z_generate` |

To keep branch coverage high, every validation and error branch in `src/` is
hit by a `pytest.raises(ValueError)` test.

## Determinism

Fixed seed (7). Tests avoid wall-clock dependence; `now=` overrides pin
`GENERATION_TIMESTAMP`. Any random draw is seeded or bounded and justified.
