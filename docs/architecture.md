# Architecture

Layer contract for the CARVER mission package. The dependency arrow is
one-directional: `scripts/ → src/` and `src/tomorrow_never_dies/mission.py →
bond_api`; the pure domain core depends on nothing but numpy.

## Layers

| Layer | Modules | Imports | Responsibility |
|---|---|---|---|
| Pure domain core | `media_manipulation.py`, `stealth_detection.py`, `gps_denial.py`, `scenario.py` | stdlib + numpy | All math and models |
| Protocol adapter | `mission.py` | `bond_api.*`, domain core | `MissionProvider` (CARVER) + gadget registration |
| Workflow | `figures.py`, `manuscript_variables.py` | matplotlib / yaml + core | Render figures; inject tokens |
| Orchestrators | `scripts/*.py` | `src/` | Thin CLIs per mission phase |

## Module map

* `src/tomorrow_never_dies/media_manipulation.py` — belief-state model,
  Watts–Strogatz / Barabási–Albert networks, media + social spread,
  influence maximization, echo-chamber and amplification metrics.
* `src/tomorrow_never_dies/narrative_control.py` — bounded-confidence opinion
  dynamics (Hegselmann–Krause) with media injection; polarization /
  bimodal-split / media-capture metrics and critical broadcast reach.
* `src/tomorrow_never_dies/stealth_detection.py` — radar equation, Marcum-Q
  / Swerling detection probabilities, detection range, RCS metrics.
* `src/tomorrow_never_dies/radar_waveform.py` — LFM / Barker-13 pulse
  compression: matched filter, processing gain, resolution, sidelobes,
  detection-range gain.
* `src/tomorrow_never_dies/gps_denial.py` — constellation, DOP, jamming
  degradation, UERE/position error, navigation failure cascade.
* `src/tomorrow_never_dies/gnss_integrity.py` — RAIM: chi-square quantile,
  SVD parity space, detection threshold, HPL/VPL, noncentral bias detection.
* `src/tomorrow_never_dies/scenario.py` — the canonical deterministic run
  (six blocks) shared by the mission outcome, manuscript tokens, and figures.
* `src/tomorrow_never_dies/mission.py` — the BOND-API `MissionProvider`.
* `src/tomorrow_never_dies/manuscript_variables.py` — `{{TOKEN}}` map.
* `src/tomorrow_never_dies/figures.py` — six deterministic figures.

## How to add an algorithm

1. Add the math to the appropriate pure domain module (or a new one — keep it
   infrastructure-free).
2. Expose it as needed in `scenario.py` and/or register it as a gadget in
   `mission.py`.
3. Add a real-data test file under `tests/`.
4. Re-run the gate and regenerate figures + manuscript tokens.
