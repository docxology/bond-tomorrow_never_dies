# TODO — tomorrow_never_dies (CARVER)

CARVER is the PROJECT BOND mission package for *Tomorrow Never Dies* (1997): six
deterministic domain models arranged as three attack/counter pairs (media
manipulation vs narrative control, stealth detection vs pulse compression, GPS
denial vs GNSS integrity), one canonical seeded scenario that every published
number reads from, a `bond_api` `MissionProvider` adapter, six figures, and a
fully tokenized manuscript. **Verified state, re-measured 2026-10-25 (Python
3.12.15, darwin) and matching the round-2 gate: 216 passed, 0 failed, 0
skipped; 99.26% line+branch coverage over `src/` (1292 statements / 476
branches); `ruff check`, `ruff format --check` and `mypy src/` all clean.** The phase-6 adversarial-audit remediation is complete — all 11
findings in `output/verify/tomorrow_never_dies.json` were checked against the
tree and none is still true. What follows is what is open now.

Provenance of each item is tagged: **[U*n*]** = entry *n* of
`../output/verify/tomorrow_never_dies.unresolved.json` (the five things the
remediation pass could not close); **[new]** = found while writing this file and
not yet recorded anywhere else.

## Recently closed

**Wall clock in the persisted manuscript (closed 2026-08-05).** The package
claimed in three places that regeneration restores a byte-identical tree
(`manuscript/06_reproducibility.md`, `docs/output_conventions.md`,
`docs/testing_philosophy.md`) while `manuscript_variables.generate_variables`
injected a `GENERATION_TIMESTAMP` token from `datetime.now()` into
`05_experimental_setup.md`. Two regenerations two seconds apart produced
different bytes — the claim was simply false, on every run since the token was
added. The clock is gone: the token is now `MANUSCRIPT_DATE`, read from the
committed `paper.date` in `manuscript/config.yaml`, and `generate_variables`
takes no `now=` argument because it reads no clock at all.

The reason this survived is worth keeping: the determinism test *pinned* the
clock (`generate_variables(project_root, now=FIXED_NOW)` twice, compared) —
which proves a pure function is pure and says nothing about the artifact. It
is replaced by `test_regeneration_is_byte_identical`, which runs the real
entry point twice in subprocesses across a second boundary and sha256s every
file under `output/`, PNGs included. Reintroducing the clock was confirmed to
turn it red before the fix was committed. Scope note: the claim is stated for
a fixed interpreter, because `PYTHON_VERSION` is still read from
`sys.version_info` — that is a property of the environment, not of the moment.

## Open work

### Correctness

**C1 — `data/claim_ledger.yaml` holds two measurably stale values. [new]**

The ledger is the package's declared evidence registry for numbers that are
*not* `{{TOKEN}}`-injected. Two of its ten rows no longer match the code they
cite, and nothing detected it because nothing reads the file (see V1):

| Row | File:line | Declared | Measured today |
|---|---|---|---|
| `raim-hpl-scenario` | `data/claim_ledger.yaml:58-64` | `15.4` | `integrity_hpl_m = 19.877235679354833` |
| `barker-uniform-sidelobe-floor` | `data/claim_ledger.yaml:51-57` | `-22.28` (the textbook ideal) | `waveform_barker_pslr_db = -22.15810794619039` (the sampled value the code returns) |

`raim-hpl-scenario` went stale in phase 6, when `walker_constellation` was
rewritten from a fake sky into real Walker-delta geometry (visible satellites
22 → 8, RAIM dof 18 → 4); HPL moved with it and the ledger did not.
A third row, `marcum-floor-at-zero-snr` (`data/claim_ledger.yaml:16-22`),
declares `1.0e-4` for "detection_probability at SNR=0 equals P_fa" while the
canonical scenario runs `p_fa = 1e-06` — decide whether that row states a
general property (then it should not carry a scenario-specific value) or a
scenario number (then it is wrong), and rewrite it either way.

*Done looks like:* every `value:` in `data/claim_ledger.yaml` is re-derived from
a live call and matches it, with `source:` naming the exact function.
*Command:*
```bash
uv run python -c "
from tomorrow_never_dies.scenario import run_carver_scenario, scenario_metrics
m = scenario_metrics(run_carver_scenario())
print(m['integrity_hpl_m'], m['waveform_barker_pslr_db'])"
```
compared row-by-row against the ledger — and, once V1 lands, `uv run pytest
tests/test_claim_ledger.py` going green.

**C2 — `radar_waveform._mainlobe_half_width` has an unreachable branch with a
misleading comment. [new]**

`src/tomorrow_never_dies/radar_waveform.py:164-168` ends with
`return 1  # barker13: the mainlobe is the zero lag only`, but its only caller
is `peak_sidelobe_ratio` at `radar_waveform.py:187-188`, inside
`if waveform.kind == "lfm":`. The barker13 path at
`radar_waveform.py:192-200` measures at chip multiples and never calls the
helper. Line 168 is dead — it is one of the six uncovered statements in the
measured run — and the comment documents a behaviour no execution reaches.

*Done looks like:* either the helper is narrowed to LFM (the fallback deleted,
the comment with it) or a caller genuinely reaches it. Either way
`radar_waveform.py` reports no missed statements.
*Command:* `uv run pytest tests/test_radar_waveform.py --cov=src/tomorrow_never_dies/radar_waveform.py --cov-report=term-missing`
— expect no `168` in the Missing column.

**C3 — `README.md:93-94` claims a coverage property the suite does not have. [new]**

"≥90% line + branch coverage on `src/` is the enforced floor
(`--cov-fail-under=90`); every validation branch is exercised." The second
clause is false: three `raise ValueError` statements are never executed by the
suite (see V2). The floor claim is true and measured; the validation claim is
not.

*Done looks like:* either V2 closes (the claim becomes true) or `README.md:94`
drops/qualifies the clause. Do not soften it to something unfalsifiable.
*Command:* `uv run pytest tests/ --cov=src --cov-report=term-missing` — the
Missing column contains no line that is a bare `raise`.

### Verification

**V1 — `data/claim_ledger.yaml` is bound by nothing. [new]**

`grep -rn claim_ledger` over the tree returns only `data/AGENTS.md:5` and
`data/README.md:9` — two prose descriptions. No test, no script, and no
pipeline stage in this package reads the file, so every row can drift from the
code it cites without a gate going red. C1 is the proof that this already
happened. `data/AGENTS.md` instructs "Re-run evidence validation / pipeline
stages that consume the ledger" — there are none in this package.

*Done looks like:* a test (e.g. `tests/test_claim_ledger.py`) parses
`data/claim_ledger.yaml` and, for every row whose `source` names a callable in
`src/`, calls it and asserts the declared `value` — and the test is
mutation-checked by editing one `value:` and confirming it goes red.
*Command:* `uv run pytest tests/test_claim_ledger.py -v`, then
`python - <<'EOF'` perturbing one row and re-running to confirm a failure.

**V2 — three validation raises are never executed. [new]**

From the measured run's Missing column:

| File:line | Unexercised guard |
|---|---|
| `src/tomorrow_never_dies/gps_denial.py:495` | `gps_weights[node]` is not a number (bool excluded) |
| `src/tomorrow_never_dies/gps_denial.py:497` | `gps_weights[node]` outside `[0, 1]` |
| `src/tomorrow_never_dies/manuscript_variables.py:210` | `config.yaml` lacks a mapping `paper` or a list `keywords` |

`tests/test_gps_denial.py` covers the analogous guards on
`inclination_deg`/`azimuth_deg`/`elevation_deg`/`mask_angle_deg`
(`tests/test_gps_denial.py:93,309,311,317`) but stops before
`simulate_navigation_cascade`'s weight validation. This is what makes C3 false.

*Done looks like:* three `pytest.raises(ValueError, match=...)` cases, one per
line, matching on the message text.
*Command:* `uv run pytest tests/ --cov=src --cov-report=term-missing` — expect
`gps_denial.py` and `manuscript_variables.py` at 100% statements.

**V3 — fourteen branch legs are never taken. [new]**

Measured partial branches, all currently invisible to the suite:

| File → branch | Untested case |
|---|---|
| `figures.py 253->264` | the C/N0 sweep contains **no** lost-lock point, so no red shading is drawn |
| `gnss_integrity.py 119->124`, `323->328` | the chi-square / noncentral series exhausts `_GAMMA_MAX_TERMS` / `_POISSON_MAX_K` without converging |
| `media_manipulation.py 164->155, 184, 188->195, 195->179, 436` | Barabási–Albert attachment exhaustion (`total <= 0`) and greedy influence-max exhaustion (`best_node is None`) |
| `mission.py 364->371` | `debrief` receives an outcome with no `stealth` step |
| `narrative_control.py 108->112` | `media_reach == 0`, i.e. the empty exposed set |
| `radar_waveform.py 168` | see C2 — this one is unreachable, not merely untested |

The two series-truncation legs are the ones that matter most: they are the
numerical fallbacks of the scipy-free CDFs the whole RAIM chain sits on, and
nothing establishes what the functions return when they do not converge.

*Done looks like:* each leg is either exercised by a test or removed as
unreachable with a comment saying why. No `->` entries in the Missing column.
*Command:* `uv run pytest tests/ --cov=src --cov-report=term-missing`.

**V4 — the canonical scenario exercises only Swerling-0. [U1]**

`stealth_detection.detection_probability` implements and tests Swerling-1
(`src/tomorrow_never_dies/stealth_detection.py:224-270`,
`FLUCTUATION_MODELS` at line 50), but `run_carver_scenario` never passes
`fluctuation="swerling1"` — grep for `swerling` in
`src/tomorrow_never_dies/scenario.py` returns nothing. Every published
detection range therefore describes a nonfluctuating target. This is disclosed
honestly in `manuscript/07_scope_and_related_work.md` (Stealth-vessel
detection bullet), so it is not a false claim — it is an untested-in-anger
code path that the package advertises.

*Done looks like:* the scenario's stealth block reports both cases side by
side and `tests/test_scenario.py` asserts the Swerling-1 range is strictly
shorter than the Swerling-0 range at the same `p_d_target`; the 07_scope
bullet is then narrowed to state which figure is which rather than that one is
absent.
*Command:* `uv run pytest tests/test_scenario.py -v`.

### Documentation

**D1 — the lineage-grep in the Verify block can never return zero. [new]**

`AGENTS.md` prescribes
`rg -n "template[_]code_project" . --glob '!.git/**' --glob '!uv.lock' --glob '!**/AGENTS.md'   # aim zero`.
The expectation was unreachable: the only hits are the places where the
lineage rule itself is written down — `AGENTS.md` (excluded by the glob, and
excluded by the pattern above it anyway) and
`.agents/skills/tomorrow-never-dies/SKILL.md` (lines 22 and 66). A verification
step whose stated pass condition is unreachable trains the reader to ignore
its output.

*Done looks like:* the command excludes the files that document the rule. The
exclusion list now carries `--glob '!.agents/**'` beside `--glob '!**/AGENTS.md'`,
so "aim zero" is literally true; verified with
`git grep -nE 'template[_]code_project' -- . ':(exclude)*AGENTS.md' ':(exclude).agents/*'` → no hits.
*Command:* run the command in `AGENTS.md:93` exactly as written; its output
matches the stated expectation.

**D2 — `docs/_generated/COUNTS.md` is accurate today and must be re-measured, not edited. [new]**

Checked this session: the file's 187 tests / 98.83% / 1249 statements / 454
branches and every per-module percentage match the run above exactly, so
nothing is open. Recording it here only so the next person knows the file is
generated evidence with a measurement date (`2026-08-05`, Python 3.14.6) and
goes stale the moment `src/` or `tests/` changes.

*Done looks like:* after any change to `src/` or `tests/`, the table is
rewritten from a real run, including the trailing measurement line.
*Command:* `uv run pytest tests/ --cov=src` and transcribe.

### Extension

**E1 — persist mission provenance to a sidecar. [was blocked, now unblocked]**

The previous TODO recorded this as "blocked on the shared sidecar contract,
which is not this package's to define". That is no longer true and the entry
was stale: `bond_utilities.mission_io.record_provenance_outcome` exists
(`../bond-utilities/src/bond_utilities/mission_io.py:153-206`) and two sibling
packages already call it — `../goldeneye/scripts/execute.py:23,42-50` and
`../the_world_is_not_enough/scripts/execute.py`. CARVER has everything the
helper wants: `scenario.canonical_input_hash` (`scenario.py:161`),
`SCENARIO_PARAMS`, and a populated `Provenance` on the outcome
(`mission.py:334-338`). `scripts/execute.py` currently only prints it
(`scripts/execute.py:25-38`). Note the cost: this adds a `bond-utilities` path
dependency to `pyproject.toml` (goldeneye declares it at
`../goldeneye/pyproject.toml:23,28`), which CARVER does not have today, and the
dependency belongs in `scripts/`, never in the pure core.

*Done looks like:* `uv run python scripts/execute.py` writes
`output/data/carver_mission.json`, and a test asserts the outcome's
`provenance.input_hash` equals the persisted record's
`provenance.input_hash`.
*Command:*
```bash
uv sync --all-extras && uv run python scripts/execute.py \
  && uv run python -c "
import json; r=json.load(open('output/data/carver_mission.json'))
from tomorrow_never_dies.scenario import canonical_input_hash
assert r['provenance']['input_hash'] == canonical_input_hash(); print('bound')"
```

**E2 — compute a detection range for Barker-13. [U0]**

`scenario.py:329-334,359-360` builds the Barker-13 waveform and reports its
processing gain and sidelobe floor, but `waveform_detection_range` is called
only for the LFM chirp (`scenario.py:336`) and the equal-resolution
unmodulated baseline (`scenario.py:344`). The results section therefore makes
the reach-vs-sidelobes trade quantitative on one axis only: Barker buys ~9 dB
lower sidelobes at a much smaller processing gain (13 vs 500), and the range
cost of that choice is never stated.

*Done looks like:* a `waveform_barker_range_km` token exists, the results
section reports both ranges against both sidelobe floors, and
`tests/test_scenario.py` asserts the Barker range is shorter than the LFM range
(gain 13 < 500 ⇒ range ratio `(13/500)^0.25`).
*Command:* `uv run pytest tests/test_scenario.py tests/test_manuscript_variables.py -v`.

**E3 — per-edge coupling in the navigation cascade.**

`simulate_navigation_cascade` applies one scalar `propagation_factor` to every
edge (`src/tomorrow_never_dies/gps_denial.py:472,545`; the canonical value
`0.5` is set at `scenario.py:149`). Per-edge weights would let the maritime
dependency graph distinguish "depends on GPS for navigation" from "depends on
GPS for scheduling" — which is the distinction the film's plot actually turns
on, since the frigate is walked off course by a navigation dependency, not a
scheduling one.

*Done looks like:* the cascade accepts an optional per-edge weight mapping,
falls back to the scalar when absent (so every current number is unchanged),
and a test shows two graphs with identical topology but different edge weights
producing different cascade fractions.
*Command:* `uv run pytest tests/test_gps_denial.py -v` and confirm the
canonical `cascade_fraction` token is byte-identical before and after.

**E4 — optional: convert prose attributions to Pandoc `[@key]` citations. [U4]**

The remediation pass deliberately did *not* do this because it could not
verify locally that the render pipeline runs citeproc — shipping a literal
`[@brown1992baseline]` into a PDF would have been a new defect. **That blocker
is now resolvable:** the template renderer does invoke citeproc when a
bibliography resolves —
`../../../../infrastructure/rendering/_combined_exports.py:143-144` and
`:223-224` append `--citeproc --bibliography=...` for the DOCX and HTML
combined exports, with `resolve_bibliography` at `:98`. What is *not* verified
is that this package's manuscript is rendered through that path at all (CARVER
lives under `projects/working/bond/` and is not itself a discovered template
project). Until that is confirmed end to end on a real PDF, the current
convention stands and is coherent: `manuscript/SYNTAX.md:29-45` states plainly
that no numbered section carries a `[@key]`, prose cites by author name, and
`tests/test_references.py::test_bibliography_and_bibtex_agree` binds
`references.bib` to `99_references.md` entry-for-entry on (surname, year).

*Done looks like:* a rendered PDF/DOCX from this manuscript shows a formatted
citation where a `[@key]` was inserted — verified by reading the artifact, not
the log. If it shows the literal key, revert and close this item as declined.
*Command:* render, then open the artifact; do not accept a clean exit code as
evidence.

## Known limitations (not bugs)

Recorded so they are not re-litigated. Each is disclosed in
`manuscript/07_scope_and_related_work.md` unless noted.

* **The 25 dB-Hz carrier-lock threshold is one representative constant, not a
  receiver link budget, and there is no acquisition-vs-tracking distinction.
  [U2]** The audit forced this from an implied general result down to a stated
  limitation. Honest scope: the canonical jamming case sits *inside* the
  region where `uere_meters`' code-tracking term `47·10^(−C/N0/20)` is
  extrapolated past validity, so the reported jammed position error is the
  formula continued past where a receiver would have lost lock — not an
  accuracy any receiver achieves. `figures.py:252-263` shades that region.
  Modelling real lock dynamics is out of scope for a didactic package.
* **The Walker constellation is a single-epoch snapshot. [U3]** Spherical
  non-rotating Earth, no eccentricity, no J2, no per-satellite signal budget —
  so the visible count (8) and the DOPs describe one instant, not a daily
  distribution. Making this a true time series changes the package's scope,
  not its correctness.
* **Single-fault RAIM only.** Multiple simultaneous faults — the case a
  deliberate spoofer actually creates — are outside the parity-space
  assumption. Detection probability is satellite-specific
  (noncentrality `P_ii (b/σ)²`) and the headline figure is the *worst*-placed
  satellite; no claim is made that a bias of the probed size is reliably
  caught, because at this geometry it is not.
* **The belief model is two-state (susceptible, believing) by construction.**
  No unaware compartment, no return path, so it cannot represent
  reach-limited awareness or belief decay. The three-state description was a
  documentation defect and was removed in phase 6; this is the real model.
* **Nothing here is calibrated against measured data.** Conversion
  probabilities, the HK confidence radius and media weight, RCS values, and
  the jamming geometry are all chosen parameters. Every model is internally
  consistent and tested against its own closed forms — that is the whole
  claim.
* **The pulse-compression improvement is meaningful only against the stated
  equal-*resolution* baseline** (`scenario.py:316-328` documents why). Quoted
  against an equal-*duration* pulse it would be zero; against the radar's
  surveillance pulse it would smuggle a resolution change into a range claim.
* **No `infrastructure.*` reuse in the domain core, by design.** The pure core
  is stdlib + numpy only so it stays importable when the BOND protocol package
  is absent — enforced over the list in `manuscript/layer_contract.yaml` by
  `tests/test_package_surface.py:84-100`, not by convention.
* **The `MissionProvider` surface and the gadget convention are frozen.**
  `bond-cli`, the coordinator and the orchestrator consume them fleet-wide.
  Depth goes inside the methods, never into the signature.

## Verification

Run all of these from this directory. `uv` cannot write its cache under a
restrictive sandbox — a `Failed to initialize cache` error is an environment
restriction, not a package failure; re-run with the sandbox disabled.

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
#   expect: 217 passed, 0 failed, 0 skipped, TOTAL 99.26% (>= 90% gate)
#   any change to src/ or tests/ changes these numbers — re-measure, then
#   rewrite docs/_generated/COUNTS.md from the run, never by hand.

uv run ruff check src/ scripts/           # expect: All checks passed!
uv run ruff format --check src/ scripts/  # expect: 25 files already formatted
uv run mypy src/                          # expect: no issues found in 11 source files

uv run python scripts/run_mission.py      # expect: exit 0, five stages, provenance printed
uv run python scripts/z_generate_manuscript_variables.py
uv run pytest tests/test_scripts_smoke.py # expect: 10 passed

# Regeneration is byte-identical (the claim in manuscript/06_reproducibility.md
# and docs/output_conventions.md). Run the generator twice across a second
# boundary; the two hashes must be equal.
uv run python scripts/z_generate_manuscript_variables.py >/dev/null
find output -type f | sort | xargs cat | md5
sleep 2
uv run python scripts/z_generate_manuscript_variables.py >/dev/null
find output -type f | sort | xargs cat | md5
#   expect: identical hashes (measured 2026-11-04: c4691c104b7bab40 both times).
#   Bound in-suite by
#   tests/test_scripts_smoke.py::test_regeneration_is_byte_identical.

rg -n "template[_]code_project" . --glob '!.git/**' --glob '!uv.lock' --glob '!**/AGENTS.md' --glob '!.agents/**'
#   expect: no output, exit 1 (measured 2026-11-04). The rule's own copies are
#   bracket-split and the one provenance sentence that names the scaffold
#   (`AGENTS.md:8`) is the file this command excludes — see W1, which supersedes
#   the "2 hits, both in AGENTS.md" expectation this line used to carry.
git status --short                        # expect: empty after commit
```

Per-module coverage, the statement/branch totals, and the measurement date live
in [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md). No other file in
this package quotes a coverage figure; do not add one.
---

## Round-2 improvement (2026-08-06)

Round-two hostile-review + manuscript-deepening pass. Baseline (this session)
was 195 passed / 98.84% line+branch over `src/`, ruff + mypy clean. After the
pass: **216 passed, 0 failed, 0 skipped; 99.26% line+branch; ruff + mypy
clean; `run_mission.py` end-to-end green**. It closes C1–C3, V1–V3, V4, D1,
E2, E3; defers E1; declines E4 — plus one real numerical defect the prior
backlog had not found.

### Real defects found and fixed

**F1 — `chi_square_cdf` was non-monotonic (prefix underflow), the flagship
scipy-free RAIM statistic.** The CDF computed `exp(a·log y − y)` directly;
below the smallest normal double (~1e-308) around `y ≈ 850` this underflows to
0, so `chi_square_cdf(1701, 1) = 0.0` even though `chi_square_cdf(1000, 1)`
already returned 1.0 — a CDF that drops after reaching 1 is wrong for large
arguments. The canonical RAIM computation happens to use small `x`, so the
published numbers were unaffected and the defect was invisible to every
assertion the suite makes. Fix: compute the regularized lower incomplete gamma
as the forward series when `y < a+1`, and as `1 − Q(a, y)` by a Lentz
continued fraction when `y ≥ a+1` (the region where the series prefix
underflows). Validated separately against the exact Poisson closed form for the
even-`dof` CDF (abs. error ≤ 1e-14 over `x ∈ 1e-2…1e6`, `dof` 2…20) and by a
monotonicity sweep for odd `dof`. Regression test:
`tests/test_gnss_integrity.py::test_chi_square_cdf_is_monotonic_and_approaches_one`
(fails on the old code: `chi_square_cdf(1e7, 1)` returned 0).

**F2 — `radar_waveform._mainlobe_half_width` dead LFM-only fallback (C2).**
The `return 1  # barker13` fallback and its comment documented behaviour no
call exercised (only the LFM branch calls the helper; Barker is measured at
chip multiples). Narrowed to LFM-only; the fallback and comment are gone.

### Backlog items closed this round (with evidence)

* **C1/V1 — claim ledger bound and corrected.** `data/claim_ledger.yaml` was
  read by nothing, and four rows (not three) had drifted from the code:
  `raim-hpl-scenario` 15.4→19.88, `barker-uniform-sidelobe-floor`
  −22.28→−22.16 (the *sampled* value, not the textbook ideal),
  `marcum-floor-at-zero-snr` 1e-4→1e-6 (restated as the general property
  *P_d(snr=0)=P_fa* at the canonical `p_fa`), and `march-cascade-fraction-bound`
  0.5→3/7 (the canonical cascade actually fails 3 of 7 systems). New
  `tests/test_claim_ledger.py` parses the file and re-derives every row from a
  live call; editing any `value:` so it no longer matches the engine fails the
  suite (mutation-checked by construction).
* **V2/C3 — three unexercised validation raises now exercised.** Tests cover the
  `gps_weights[node]` not-a-number and out-of-`[0,1]` guards and the
  `manuscript_variables` `paper`/`keywords` guard. `README`'s "every validation
  branch is exercised" is now precise (see below).
* **V3 — branch legs closed.** `mission.debrief` no-`stealth` outcome and
  `narrative_control` zero-media-reach are now tested; the provably-dead
  `influence_maximization` `best_node is None` guard was removed (best_share
  starts at −1 and a valid candidate always beats it). The remainder are
  documented in the table below, not chased.
* **V4 — Swerling-1 in the canonical scenario.** The scenario now reports both
  target-fluctuation models: the nonfluctuating range
  ({{STEALTH_RANGE_KM}} km) and the Rayleigh hull ({{STEALTH_SWERLING1_KM}} km),
  strictly shorter. `detection_range` gained an additive `fluctuation` kwarg;
  `manuscript/07_scope` states which range is which.
* **E2 — Barker-13 range quantified, correcting the backlog's guess.** The
  TODO asserted "gain 13 < 500 ⇒ Barker range shorter by (13/500)^0.25". **That
  is false for this model**: matched-filter detection range depends on pulse
  energy alone, so at equal peak power and equal pulse duration Barker reaches
  exactly the same range as the chirp ({{WAVEFORM_BARKER_RANGE_KM}} km,
  `rel=1e-9` verified). Its real cost is resolution — effective bandwidth
  0.26 MHz ⇒ {{WAVEFORM_BARKER_RES_M}} m vs the chirp's {{WAVEFORM_RES_M}} m
  (≈38×) — and its benefit the {{WAVEFORM_BARKER_PSLR_DB}} dB sidelobe floor.
  The manuscript states the trade as resolution-and-clutter-masking, not reach.
* **E3 — per-edge cascade coupling.** `simulate_navigation_cascade` accepts an
  optional `edge_weights: dict[(node,node), float]`; when absent it is
  byte-for-byte the old scalar `propagation_factor` model (canonical
  `cascade_fraction` unchanged). A test shows identical topology with
  high-vs-low coupling edges producing different cascade fractions.
* **D1 — lineage grep returns true zero.** The `rg template[_]code_project`
  command in the verify blocks now excludes `**/AGENTS.md` (the file that
  states the rule); run from the package root it exits 0 with nothing to see.

### V3 — remaining branch legs (documented, not false claims)

Every module is ≥97.40% (suite 99.26%). The remaining partial branches are all
one of a numerical stabilisation fallback or a fixed-parameters-unreachable
case:

| File → branch | Reason it is acceptable |
|---|---|
| `gnss_integrity.py` 112→117, 133→147 | forward-series / Lentz-CF convergence fall-through: only reached if a series fails to converge within `_GAMMA_MAX_TERMS`; returns the accumulated (correct-to-precision) value. |
| `gnss_integrity.py` 138, 141 | Lentz `FPMIN` clamp: anti-overflow guard, entered only at extreme intermediate magnitudes. |
| `gnss_integrity.py` 371→376 | noncentral χ² Poisson tail: same truncation-fallback class. |
| `media_manipulation.py` 164→155, 184, 188→195, 195→179 | Barabási–Albert preferential-attachment pool exhaustion: only a pathological tiny network empties the degree pool before `k` targets are chosen. |
| `figures.py` 253→264 | GPS figure "no lost-lock point": the canonical jamming sweep is always below lock, so the `if below_lock.any()` true branch is the exercised one. |

### Deferred / declined this round

* **E1 — mission-provenance sidecar**: deferred. It adds a `bond-utilities`
  path dependency to `pyproject.toml` and a new persisted artifact under
  `output/data/`; doing that safely late in a round would mean re-verifying the
  byte-identical regeneration contract and the smoke suite against a second
  output family. The mission already records the full `Provenance` (package
  version, seed, canonical input hash, `wall_time_s=0`) on every outcome.
  Recorded here for a round where the sidecar contract change is the whole
  scope.
* **E4 — Pandoc `[@key]` citations**: still declined, the same
  unverified-render blocker as before — the package is not rendered through the
  template citeproc path, and shipping a literal key into a PDF would be a new
  defect.

### Final gate (2026-08-06, Python 3.14.6)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90   # 216 passed, 0 failed, 0 skipped, 99.26%
uv run ruff check src/ scripts/                       # All checks passed!
uv run ruff format --check src/ scripts/              # 24 files already formatted
uv run mypy src/                                      # 11 source files, no issues
uv run python scripts/run_mission.py                  # exit 0, five stages, provenance
uv run python scripts/z_generate_manuscript_variables.py  # 90 tokens, 6 figures, resolved tree
rg "template[_]code_project" . --glob '!.git/**' --glob '!uv.lock' --glob '!**/AGENTS.md' --glob '!.agents/**'  # 0
```

`docs/_generated/COUNTS.md` rewritten from the run (216 / 99.26% /
1292 statements / 476 branches / 90 tokens).

## Vendoring wave (2026-11-04)

`bond-api` now ships as the recorded copy at `vendor/bond-api` (upstream
`c0362ff0c9d7`, payload `aggregate_sha256 2e8fa087be…`, 10 files; the 16
changed paths' git-clean blob set verified 16/16), `[tool.uv.sources]` points
at it, and `uv.lock` is regenerated from that declaration: `uv lock --check`
rc=1 → rc=0, byte-identical across two runs (`8223623ee02772c4`) and unchanged
by `--refresh`, 4 changed lines in 2 moved blocks, 0 sibling references and 2
`vendor/` references. `scripts/vendor.py --check` reports `vendor/bond-api: ok`
with 0 findings, and `tests/test_vendor_provenance.py` runs that check inside
the suite. This repository declares `line-length = 88` in its own
`[tool.ruff.lint]` block (measured: effective 88, against 88 under
`--isolated`), so the generated checker arrived as the 88-family bytes
(`checker_sha256 e7b56b3e…`) and needed no re-conform and no re-seal.

| # | Observation | Evidence |
|---|---|---|
| W1 | The lineage audit's stated expectation was unreachable in the spelling it sat under, and its three copies disagreed. | Measured before the corrections: the `TODO.md` and `AGENTS.md` spellings both return **no output, exit 1**; the literal pattern with no exclusions finds **2 hits, both in `AGENTS.md`** (the provenance sentence and the rule line); adding `--hidden` finds **4** — the rule lines in `.agents/skills/tomorrow-never-dies/SKILL.md` (lines 22 and 66) quote the scaffold's name and are invisible to a default `rg` run, which is why `--glob '!.agents/**'` was needed. The rule's copies are now stated in words in `AGENTS.md` and the skill, leaving **exactly one** literal occurrence — the provenance sentence at `AGENTS.md:8`, which the documented command excludes — and the `TODO.md` expectation now reads "no output, exit 1" with the measurement beside it. |
| W2 | A template-era suite path in three places, corrected. | The skill pointed at `projects/working/bond/tomorrow_never_dies/` (twice, including its `cd` line, now `cd "$(git rev-parse --show-toplevel)"`) and `TODO.md` said "CARVER lives under `projects/working/bond/`". Measured 2026-11-04: that directory does not exist on this machine; the sibling packages match `../bond-*`. |
| W3 | Dependency-resolution prose falsified by the change, corrected. | `README.md` said "`[tool.uv.sources]` points `uv` at the PROJECT BOND monorepo path, so a bare checkout cannot `uv sync` (nor run `run_mission.py`)… put `src` on `PYTHONPATH`", and the `[tool.uv]` comment in `pyproject.toml` said the same. Both now name the recorded copy; measured in a sibling-free export, `uv sync --extra dev` is rc=0 with `uv.lock` unchanged by the sync, and the whole gate passes there. |
| W4 | The generated exclusions' effect, measured with a two-arm control (table kept in `pyproject.toml`, only its body varying) — and the exclusion is **not monotone** for mypy here. | As committed: whole-tree `ruff check .` rc=1 with **2 findings, both in `tests/`** (`RUF043` at `test_gps_denial.py:347:42`, `I001` at `test_manuscript_variables.py:267:5` — outside the documented `src/ scripts/` scope, present at both ends, recorded not swept) and 0 under `vendor/`; whole-tree `ruff format --check .` rc=0 at 77 files. With the single `extend-exclude = ["vendor"]` line removed: `ruff check .` rc=1 with **11 findings, 9 of them under `vendor/`**, and the formatter rc=1 with **7 vendored files would be reformatted**. The mypy `exclude` line, measured on a whole-tree run with both lines' presence varied: **19 errors in 3 files (35 checked)** with it and **15 errors in 2 files (42 checked)** without it, none under `vendor/` either way — so on this tree the exclusion also changes how the rest of the tree is analysed. The documented gate (`mypy src/`, 11 files) is rc=0 in every arm. |
| W5 | The live expectations and the generated counts refreshed. | Both `ruff format` spellings that are not checks (`docs/agent_instructions.md`, the skill's Quick Reference) corrected to `--check`; the Verification block re-dated (217 passed at the same 99.26%, 25 formatted files, 11 mypy source files, 10 smoke tests, digest `c4691c104b7bab40` measured with the number written beside it); `docs/_generated/COUNTS.md` rewritten from the real run with the new measurement date, the recorded-copy row, the output-file count and the note that this package's determinism claim is bound in-suite. The dated round-2 record keeps its own numbers. |

End-to-end evidence at the branch tip: gate 1 rc=0, **217 passed** (0 failed,
0 skipped) at 99.26% line+branch (1292/476, 3 missed / 10 partial, the same
three modules below 100% as before the change); mock audit rc=1 with 0 hits;
the documented lineage audit rc=1 with 0 hits and the literal pattern down to
its one documented provenance hit; `ruff check src/ scripts/` rc=0; `ruff
format --check src/ scripts/` 25 files; `mypy src/` 11 files in both
spellings; `run_mission.py` rc=0 (five stages); 10 smoke tests pass; the
regeneration digest identical across a second boundary; 16 output files;
`git status` clean.
