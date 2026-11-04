---
name: tomorrow-never-dies
description: PROJECT BOND film package (CARVER) — disinformation propagation, stealth-vessel detection, GPS-denial impact, BOND-API MissionProvider.
version: 0.1.0
author: Active Inference Institute
license: MIT
tags: [bond, carver, mission-software, disinformation, stealth-detection, gps-denial, determinism]
---

# tomorrow-never-dies — CARVER

Project-scoped skill for the BOND suite film package published at
`docxology/bond-tomorrow_never_dies` — a sibling of the other `bond-*`
directories; the template-era `projects/working/bond/` path is gone. Load this
when working inside the package.

## When to Use

- Editing or running the CARVER mission package (its domain core, the
  BOND-API `MissionProvider` in `mission.py`, thin CLIs, or manuscript).
- Regenerating figures / manuscript tokens / the resolved manuscript.
- Verifying the BOND guardrails (no mocks, ≥90% line+branch coverage, thin
  orchestrators, no exemplar-lineage strings, path-scoped commits).

## Quick Reference

```bash
cd "$(git rev-parse --show-toplevel)"
uv sync --extra dev
uv run python scripts/run_mission.py                          # full 5-stage mission
uv run python scripts/z_generate_manuscript_variables.py      # figures + {{TOKEN}}s + resolved manuscript
uv run pytest tests/ --cov=src --cov-fail-under=90            # gate (>=90% line+branch)
uv run ruff check src/ scripts/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

## Concepts (pure domain core, stdlib + numpy only)

| Concept | Module | Core functions |
|---|---|---|
| Disinformation propagation | `media_manipulation.py` | `build_network`, `simulate_disinformation`, `influence_maximization`, `echo_chamber_coefficient`, `amplification_factor` |
| Narrative control | `narrative_control.py` | `simulate_opinions`, `bimodal_split`, `media_capture`, `critical_media_reach` |
| Stealth-vessel detection | `stealth_detection.py` | `snr_at_range`, `detection_probability`, `marcum_q1`, `detection_range`, `roc_curve`, `rcs_reduction_db` |
| Pulse compression | `radar_waveform.py` | `Waveform`, `generate_waveform`, `compress`, `peak_sidelobe_ratio`, `processing_gain`, `waveform_detection_range` |
| GPS-denial impact | `gps_denial.py` | `walker_constellation` (Walker-delta orbital geometry), `compute_dop`, `jamming_to_noise_db`, `effective_cno_dbhz`, `uere_meters`, `simulate_navigation_cascade` |
| GNSS integrity (RAIM) | `gnss_integrity.py` | `chi_square_cdf`/`ppf`, `parity_matrix`, `protection_levels`, `parity_projection_factors`, `detection_probability`, `integrity_availability` |

Six figures live in `src/tomorrow_never_dies/figures.py`; the film's gadgets
(now nine) are registered via the unchanged `register_gadgets` /
`GADGET_REGISTRY` convention.

## Integration

- `mission.py` implements the **FROZEN `bond_api` `MissionProvider`** protocol
  (slug `tomorrow_never_dies`, codename CARVER) and registers gadgets with the
  `GadgetRegistry`; discoverable via `bond_api.discovery`.
- `scenario.py::run_carver_scenario` is the single source of truth for the
  numbers used by the mission outcome, manuscript tokens, and figures.

## Pitfalls

- **Keep the pure core clean.** `media_manipulation.py`, `stealth_detection.py`,
  `gps_denial.py`, `scenario.py` must not import `bond_api` or
  `infrastructure.*` — only `mission.py` touches `bond_api`.
- **No mocks.** Real data + computation only; deterministic fakes implement
  the real protocol.
- **No exemplar-lineage strings** (aim zero; the scaffold's name survives only
  as provenance in `AGENTS.md`). `output/` is
  git-ignored and regenerable — never hand-edit.
- **Determinism:** fixed seed 7; `now=` overrides pin timestamps; no
  wall-clock in persisted outcomes.
- **Manuscript tokens:** metrics are `{{TOKEN}}`s from
  `manuscript_variables.py`; never hand-author numbers in prose.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md) · README:
  [`README.md`](../../../README.md) · TODO: [`TODO.md`](../../../TODO.md)
- Rulebook: [`docs/agent_instructions.md`](../../../docs/agent_instructions.md)
