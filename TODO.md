# TODO — CARVER (tomorrow_never_dies)

Open work only. Completed phases are summarized at the bottom as a build
record, not as a task list.

## Open — integration points

* **Provenance persistence.** Mission outcomes carry the protocol's
  `Provenance` (package version, seed, canonical input hash, `wall_time_s=0`)
  but nothing writes it to a sidecar. Bind to
  `bond_utilities.mission_io.record_provenance_outcome` once the shared
  provenance contract is wired into the suite.
  *Acceptance:* a mission outcome's `input_hash` matches a persisted
  `provenance.input_hash` on disk, asserted in `tests/test_mission.py`.
  *Blocked on:* the shared sidecar contract, which is not this package's to
  define.

## Open — modelling

* **Fluctuating-target detection in the canonical scenario.**
  `stealth_detection.detection_probability` implements Swerling-1, and it is
  tested, but `run_carver_scenario` only ever exercises Swerling-0. The
  published detection ranges therefore describe a nonfluctuating target.
  `07_scope_and_related_work.md` now states this restriction explicitly; the
  remaining work is to add a Swerling-1 block to the scenario and report both
  cases side by side.
* **Barker-13 is analysed but not carried through.** The scenario computes
  its gain and sidelobe floor, and the results section reports the trade, but
  the detection-range recovery is only computed for the LFM chirp. Computing
  `waveform_detection_range` for the Barker code too would let the manuscript
  make the reach-vs-sidelobes trade quantitative on both axes rather than one.
* **Cascade propagation is single-parameter.** `simulate_navigation_cascade`
  applies one `propagation_factor` to every edge. Per-edge coupling weights
  would let the maritime network distinguish "depends on for navigation" from
  "depends on for scheduling", which is the distinction the film's plot
  actually turns on.

## Not in scope

* No operational radar/GPS/fleet tooling — this is a didactic mission model.
* No `infrastructure.*` reuse; the pure core is intentionally standalone.
* No changes to the `MissionProvider` surface or the gadget convention —
  they are frozen and consumed fleet-wide.

---

## Build record

**Phase 5 — documentation truth + defect sweep (done).** Brought every doc and
manuscript section into agreement with the phase-4 code; tokenized the last
hand-authored numbers (Barker-13 sidelobe floor, stealth range loss, campaign
lift) and all scenario *inputs* in the experimental-setup section; added
`tests/test_package_surface.py` (concept-list drift, import purity, no
exception handlers) and three manuscript gates (bare-numeral scan with a
positive control, orphan-token scan). Fixed genuine defects: the media-target
seed was an additive offset that left the sort order — and therefore the
selected audience — effectively seed-independent; `simulate_navigation_cascade`
raised `KeyError` mid-cascade on an unknown dependent instead of validating at
the boundary; `_media_targets` took an unused `rng`; `CONCEPTS` and several
module docstrings still described three concepts; the RAIM module docstring
claimed QR where the code uses SVD; the debrief hardcoded a "20 dB / two-thirds"
lesson.

**Phase 4 — deep improvement (done).** Added `narrative_control.py`,
`radar_waveform.py`, and `gnss_integrity.py`; deepened the canonical scenario
to six blocks; added three figures, three token families, and four gadgets;
extended the bibliography (Hegselmann–Krause, DeGroot, Barker,
Parkinson–Axelrad, Brown). Hardened along the way: integration gain is now
counted exactly once across `snr_at_range` → `detection_probability`, and the
parity matrix is built from the full SVD rather than complete-QR (whose
reduced shape varies in numpy). Protocol shape unchanged.

**Phase 2 — conversion (done).** Built the pure domain core
(`media_manipulation`, `stealth_detection`, `gps_denial`, `scenario`), the
`bond_api` adapter in `mission.py`, the thin phase CLIs, the manuscript with
token injection, and the zero-mock test suite.
