# src/tomorrow_never_dies/ — CARVER Domain Core

The importable logic for the CARVER mission package. Modules are split into a
**pure domain core** (stdlib + numpy only) and a thin **protocol adapter**
(the only `bond_api` consumer).

## Module map

| Module | Surface | Notes |
|---|---|---|
| `media_manipulation.py` | `build_network`, `simulate_disinformation`, `influence_maximization`, `echo_chamber_coefficient`, `amplification_factor` | Pure domain core |
| `narrative_control.py` | `simulate_opinions`, `initial_opinions`, `polarization_variance`, `bimodal_split`, `media_capture`, `critical_media_reach` | Pure domain core (Hegselmann–Krause + media) |
| `stealth_detection.py` | `snr_at_range`, `detection_probability`, `marcum_q1`, `detection_range`, `roc_curve`, `rcs_reduction_db`, `detection_range_ratio` | Pure domain core |
| `radar_waveform.py` | `Waveform`, `generate_waveform`, `compress`, `peak_sidelobe_ratio`, `processing_gain`, `range_resolution`, `range_improvement`, `waveform_detection_range` | Pure domain core (pulse compression) |
| `gps_denial.py` | `walker_constellation` (real Walker-delta orbital geometry), `compute_dop`, `jamming_to_noise_db`, `effective_cno_dbhz`, `uere_meters`, `position_error_meters`, `simulate_navigation_cascade` | Pure domain core |
| `gnss_integrity.py` | `chi_square_cdf`/`ppf`, `parity_matrix`, `test_statistic`, `raim_threshold`, `slopes`, `protection_levels`, `parity_projection_factors`, `detection_probability` (requires a per-satellite projection factor), `integrity_availability` | Pure domain core (RAIM) |
| `scenario.py` | `run_carver_scenario`, `scenario_metrics`, `canonical_input_hash` | Canonical deterministic run (six blocks) |
| `mission.py` | `MissionProvider` (CARVER), `GADGETS`, `register_gadgets`, `GADGET_REGISTRY` | Protocol adapter (imports `bond_api`) |
| `manuscript_variables.py` | `load_mission_config`, `generate_variables` | Workflow (reads `manuscript/config.yaml`) |
| `figures.py` | `render_figures` + six per-concept generators | Workflow (matplotlib) |

## Rules

* Pure core: `from __future__ import annotations`; no `infrastructure.*`, no
  `bond_api`, no `matplotlib`. Deterministic (fixed seed, no wall-clock).
* Validated boundaries: public functions raise `ValueError` with actionable
  messages; validation branches are covered by tests.
* `mission.py` exposes `MissionProvider` at module top level under the stable
  name required by the BOND discovery contract.

## Tests

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```
