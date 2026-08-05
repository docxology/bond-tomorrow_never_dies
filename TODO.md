# TODO — CARVER (tomorrow_never_dies)

## Phase 4 — deep improvement (DONE)

Added three more pure-domain algorithm modules, deepening each concept area:

- `narrative_control.py` — bounded-confidence opinion dynamics
  (Hegselmann–Krause) with a Carver-style media injection; polarization /
  bimodal-split metrics, media capture, and `critical_media_reach`
  (bisection on the broadcast reach that tips the belief model).
- `radar_waveform.py` — pulse compression: LFM chirp and Barker-13
  matched filtering; processing gain, range resolution, peak sidelobe
  ratio, and `waveform_detection_range` (fourth-root gain).
- `gnss_integrity.py` — RAIM: scipy-free chi-square quantile, SVD parity
  space, detection threshold, HPL/VPL protection levels, and noncentral
  chi-square bias-detection probability.

Deepened the canonical scenario to six blocks (media / narrative / stealth /
waveform / gps / integrity), added three figures (narrative, waveform, raim),
three new manuscript tokens families (`NARRATIVE_*`, `WAVEFORM_*`, `RAIM_*`),
new BOND gadgets (`opinion_dynamics`, `critical_reach`, `matched_filter`,
`raim_detection`), and updated the manuscript + bibliography (Hegselmann–Krause,
DeGroot, Barker, Parkinson–Axelrad, Brown). **Protocol shape unchanged**: the
frozen `bond_api.MissionProvider` and the `GADGETS`/`register_gadgets`/
`GADGET_REGISTRY` convention are preserved; discovery and serialization round-
trip unchanged. Fixes hardened along the way: integration gain is now counted
exactly once across `snr_at_range` → `detection_probability`, and the parity
matrix is built from the full SVD (not complete-QR, whose reduced shape varies
in numpy).

## What phase-2 built (DONE)

- **Pure domain core** (infrastructure-free, deterministic, real math):
  - `media_manipulation.py` — belief-state disinformation model on
    Watts–Strogatz / Barabási–Albert networks; media + social spread;
    greedy influence maximization; echo-chamber + amplification metrics.
  - `stealth_detection.py` — radar equation, Marcum-Q (numerically
    integrated) and Swerling detection probabilities, detection range,
    RCS metrics.
  - `gps_denial.py` — Walker-style constellation, DOP, jamming→C/N0
    degradation, UERE/position error, navigation failure cascade.
  - `scenario.py` — the canonical seeded run shared by outcome/tokens/figures.
- **BOND-API adapter**: `mission.py` implements the FROZEN `bond_api`
  `MissionProvider` (slug `tomorrow_never_dies`, codename CARVER); registers
  five gadgets with the `GadgetRegistry`; discoverable via `bond_api`
  discovery; serialization round-trips through the wire format.
- **Thin CLIs**: `brief.py`, `recon.py`, `plan.py`, `execute.py`,
  `debrief.py`, `run_mission.py`, `z_generate_manuscript_variables.py`.
- **Manuscript**: sections `00`–`07` + `99`, config identity, figures (3),
  `manuscript_variables.py` token injection with live cross-reference gate.
- **Tests**: per-module, mission/protocol, scenario, manuscript cross-ref,
  figures, scripts smoke — zero mocks, ≥90% line+branch.

## Declared integration points

- **Provenance persistence**: outcomes currently carry the protocol's
  `Provenance` (package version, seed, canonical input hash, wall-time 0).
  Bind to `bond_utilities.mission_io.record_provenance_outcome` once the
  shared provenance sidecar contract is wired into the suite; acceptance: a
  mission outcome's input hash matches a persisted `provenance.input_hash`.
- **Coordinator handoff**: the orchestrator discovers CARVER by slug via
  `bond_api` discovery (already exercised in `tests/test_mission.py`). No
  further work expected unless the coordinator adds per-film scheduling
  fields.

## Not in scope

- No operational radar/GPS/fleet tooling — this is a didactic mission model.
- No `infrastructure.*` reuse (pure core is intentionally standalone).
