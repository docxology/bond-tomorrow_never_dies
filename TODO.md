# TODO — CARVER (tomorrow_never_dies)

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
