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

**Phase 6 — adversarial audit remediation (done).** An external audit found
the phase-5 record below overstated its reach, and it was right. Fixed, with
each repair mutation-tested (break the guarded thing, confirm the gate goes
red):

* `gnss_integrity.detection_probability` claimed the parity projection
  preserves a single-satellite bias norm and used noncentrality `(b/σ)²`. It
  does not: the correct value is `P_ii (b/σ)²` with `P_ii < 1`, and the
  module's own `test_statistic` disagreed with it (39.81 vs the assumed
  44.44). Added `parity_projection_factors`, made the factor a *required*
  argument — no default that silently restores the optimistic number — and
  the published RAIM detection probability fell from 65.9% to 25.2%
  (worst-placed satellite; 54.2% best-placed), both now reported.
* `walker_constellation` had no orbital-plane structure at all: azimuth was
  `(plane_phase + uniform(0,360)) % 360`, which is just uniform, and
  elevation was `uniform(5, 90)`, so 22 of 24 satellites cleared the mask.
  Replaced with a real Walker-delta pattern propagated as orbital geometry
  and projected onto a receiver's sky: 8 visible, PDOP 1.70 (was 1.21), RAIM
  dof 4 (was 18). Every downstream GPS/RAIM number moved accordingly.
* `waveform_detection_range` banked the full `B·T` compression gain on a
  noise floor ten times narrower than the waveform occupied — ~10 dB counted
  twice. The noise bandwidth now follows the waveform; the reported LFM range
  is 108.2 km (was 192.3 km). The 373% improvement survives because the
  baseline is now an equal-*resolution* unmodulated pulse, which is the only
  comparison in which that number means anything.
* The docs' "three belief states" were two: `UNAWARE` was never assigned in
  any code path. Removed the dead state; docs, manuscript and `state_counts`
  now say two.
* The pure-domain import ban was documented as covering `scenario.py` but
  iterated over `CONCEPTS`, which excludes it. The scanned list now comes
  from `layer_contract.yaml`.
* "Jamming pushes effective C/N0 negative" was false at the canonical
  standoff (+10.5 dB-Hz). Corrected, and the figure now shades the
  short-standoff region where the code-tracking model is extrapolated past a
  receiver's lock threshold.
* `scenario.py` re-derived integrity availability inline instead of calling
  the exported `integrity_availability`; it now calls it, and a structural
  gate rejects a re-introduced inline copy (a numerically identical duplicate
  passes every value test, so a value test could not have caught this).
* `tests/test_figures.py` reached 100% coverage of `figures.py` while
  asserting only that six PNGs exceeded 1000 bytes. Figures are now built by
  pure `build_*` functions and the tests compare the plotted series against
  the domain modules; swapping two datasets or plotting the flattering RAIM
  curve now fails.
* `references.bib` was entirely uncited and bound to nothing. `SYNTAX.md` no
  longer instructs a citation convention nothing follows, and
  `tests/test_references.py` binds the `.bib` to `99_references.md`
  entry-for-entry.

**Phase 5 — documentation truth + defect sweep (done, but overstated).** The
original claim here — "brought every doc and manuscript section into agreement
with the phase-4 code" — was not true: the two severe defects and four lesser
ones listed under phase 6 above survived it. What it actually did: tokenized the last
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
