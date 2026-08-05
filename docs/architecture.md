# Architecture — CARVER (`tomorrow_never_dies`)

CARVER is four layers with a strictly one-directional dependency arrow:

```
scripts/*.py  ──►  mission.py  ──►  bond_api        (the only protocol edge)
     │                  │
     │                  ▼
     └──────────►  scenario.py  ──►  six pure-domain modules  ──►  numpy
                        ▲
   figures.py, manuscript_variables.py
```

Nothing points left. The six domain modules import numpy and each other; they
never import `bond_api`, `infrastructure.*`, or matplotlib, which is why the
science core stays usable when the BOND protocol package is not installed.
`tests/test_package_surface.py::test_pure_core_imports_no_bond_api_or_infrastructure`
enforces that by reading the source, not by convention.

## Layers

| Layer | Modules | May import | Responsibility |
|---|---|---|---|
| Pure domain core | `media_manipulation.py`, `narrative_control.py`, `stealth_detection.py`, `radar_waveform.py`, `gps_denial.py`, `gnss_integrity.py` | stdlib, numpy, sibling core modules | All math and models |
| Canonical run | `scenario.py` | the core | One deterministic execution of all six models; the single source of truth for every published number |
| Protocol adapter | `mission.py` | `bond_api.*`, the core, `scenario` | `MissionProvider` (CARVER) + gadget registration |
| Workflow | `figures.py`, `manuscript_variables.py` | matplotlib / yaml + `scenario` | Render figures; inject `{{TOKEN}}`s |
| Orchestrators | `scripts/*.py` | `src/` | Thin CLIs, one per mission phase |

## Module map — what each file actually computes

The six concepts form three adversarial pairs: for each of Carver's weapons,
the model of the weapon and the model of the thing that answers it.

### Media

**`media_manipulation.py`** (attack). Three-state belief diffusion
(unaware / susceptible / believing) on a graph. `build_network` produces
Watts–Strogatz small-world or Barabási–Albert preferential-attachment
adjacency as a tuple of tuples. `simulate_disinformation` runs two channels
per round: a media channel over a fixed broadcast footprint (selected by
`_target_score`, a deterministic index mix — *not* an RNG draw, so the
footprint is a pure function of size, reach, and seed, and nests as reach
grows) and a social channel over edges. `echo_chamber_coefficient` reports the
fraction of believers whose neighbourhood is majority-believing;
`amplification_factor` is believers per directly-exposed node.
`influence_maximization` is greedy Kempe–Kleinberg–Tardos seed selection, made
deterministic by the fixed simulation seed.

**`narrative_control.py`** (the finer instrument). Where
`media_manipulation` asks *whether* an agent believes, this asks *how far* a
continuous opinion moves. `simulate_opinions` runs Hegselmann–Krause
bounded-confidence updates — each agent averages the opinions within radius
`epsilon` — with an added media pull on the exposed subset, and simulates the
no-media baseline internally so `media_capture` is measured against a real
counterfactual rather than an assumption. `polarization_variance` and
`bimodal_split` (fraction of agent pairs further apart than `2*epsilon`)
quantify echo-chamber fragmentation. `critical_media_reach` bisects on
broadcast reach in the *discrete* model to find the minimum audience that tips
it past a target share.

### Radar

**`stealth_detection.py`** (attack). The monostatic radar equation
(`snr_at_range`, returning **per-pulse, pre-integration** SNR — integration is
applied exactly once, downstream in `detection_probability`), a square-law
threshold from a false-alarm probability (`threshold_power`), and detection
probability by numerical Marcum-Q quadrature (Swerling 0) or the Swerling-1
closed form. `marcum_q1` uses an exponentially scaled Bessel `I0e` and a
peak-adaptive grid so it does not overflow at close range. `detection_range`
binary-searches the range meeting a target `P_d`; `rcs_reduction_db` and
`detection_range_ratio` express the fourth-root stealth penalty.

**`radar_waveform.py`** (the counter). Three waveforms (unmodulated, LFM
chirp, Barker-13 phase code) with `generate_waveform`, an exact-convolution
matched filter (`compress`), `waveform_bandwidth`, `range_resolution`
(`c/2B`), `processing_gain` (`B·T` for LFM, 13 for Barker), and
`peak_sidelobe_ratio` — scanned at sample resolution for the LFM sinc floor
and at chip lags for the Barker code. `waveform_detection_range` folds the
compression gain in as coherent integration, so range recovery follows the
same fourth-root law as the stealth penalty it answers.

### Navigation

**`gps_denial.py`** (attack). `walker_constellation` builds a deterministic
pseudo-Walker sky; `geometry_matrix` and `compute_dop` give
GDOP/PDOP/HDOP/VDOP. `jamming_to_noise_db` computes J/N at a standoff
distance, `effective_cno_dbhz` degrades C/N0 by it, `uere_meters` grows the
code-tracking noise term as the signal weakens, and `position_error_meters` is
`PDOP · UERE`. `simulate_navigation_cascade` propagates stress through the
`maritime_dependency_network` until a fixpoint, returning failed systems,
round count, and failed fraction.

**`gnss_integrity.py`** (the counter). A scipy-free statistical core:
`chi_square_cdf` (regularized lower incomplete gamma, series),
`chi_square_ppf` and `normal_ppf` (bisection), and `noncentral_chi2_cdf`
(Poisson-weighted central series). `parity_matrix` takes the trailing left
singular vectors of the full SVD of the geometry matrix — deliberately SVD and
not `mode="complete"` QR, whose reduced-Q shape varies across numpy versions.
`test_statistic`, `raim_threshold`, `slopes`, and `protection_levels` produce
HPL/VPL with a missed-detection margin; `detection_probability` gives the
probability of catching a bias of a given size.

### The supporting four

* **`scenario.py`** — `SCENARIO_PARAMS` (the canonical inputs; any change
  changes `canonical_input_hash`), `SCENARIO_BLOCKS` (the six result-block
  names), `run_carver_scenario` (one seeded execution of all six models plus
  the no-media counterfactual), and `scenario_metrics` (the flat scalar map
  the manuscript and figures both read). Because outcome, tokens, and plots
  all derive from this one function, prose and plots cannot drift apart.
* **`mission.py`** — the BOND-API adapter (see below).
* **`manuscript_variables.py`** — `_format_params` (scenario *inputs*) and
  `_format_metrics` (scenario *results*) build the `{{TOKEN}}` map;
  `load_mission_config` reads identity from `manuscript/config.yaml`.
* **`figures.py`** — six deterministic figures, one per concept, matplotlib
  pinned to `Agg`.

## How `mission.py` implements the frozen `MissionProvider`

`bond_api.protocol.MissionProvider` is a **runtime-checkable protocol** shared
by all film packages in the fleet. It is frozen: `bond-cli`, the coordinator's
reconcile step, and the orchestrator all consume this exact surface, so depth
is added *inside* the methods and never to their shape.

CARVER satisfies it structurally — it does not subclass anything:

| Member | CARVER's implementation |
|---|---|
| `film` | Class attribute `= FILM = "tomorrow_never_dies"`, matching the package name so discovery by slug works |
| `brief()` | A `MissionBrief` with one objective per concept module, three `Asset`s (media network, radar equation, GPS constellation) whose payloads are read from `SCENARIO_PARAMS`, and `Constraint`s declaring determinism and no-mocked-data |
| `recon(request)` | A `ReconReport` of `Finding`s: the caller's goal echoed back, plus one per concept and one for constraints |
| `plan(brief)` | A `MissionPlan` of seven `Step`s — one per concept, then `synthesize` — each carrying real parameters from `SCENARIO_PARAMS` |
| `execute(plan)` | Runs `run_carver_scenario` once and projects each step onto its result block; returns a `MissionOutcome` with `Provenance(package_version, seed, input_hash, wall_time_s=0.0)` |
| `debrief(outcome)` | A `Debrief` of lessons. Qualitative lines are fixed; every *quantity* is read back out of the outcome's own `per_step`, never written by hand |

Two module-level names complete the discovery contract:

* `GADGETS` — a `dict[str, Any]` mapping gadget name to the domain callable
  that backs it: `media_campaign`, `opinion_dynamics`, `critical_reach`,
  `radar_detection`, `radar_equation`, `matched_filter`,
  `navigation_cascade`, `raim_detection`, `carver_scenario`.
* `register_gadgets(registry)` / `GADGET_REGISTRY` — registration happens at
  import time onto a module-level `GadgetRegistry`, so a coordinator sees the
  gadgets the moment the film is imported, while `register_gadgets` stays
  available for merging into a shared registry.

`wall_time_s` is pinned to `0.0` on purpose: an outcome must be byte-identical
across runs, and a wall-clock field would make provenance non-reproducible.

## How to add an algorithm

1. Put the math in the appropriate pure-domain module, or add a new one — it
   must stay infrastructure-free, and adding it means adding its name to
   `CONCEPTS` in `__init__.py` (`test_package_surface.py` fails until you do).
2. Wire it into `scenario.py` if it produces a published number, and add the
   scalar to `scenario_metrics`.
3. Add the `{{TOKEN}}` in `manuscript_variables.py` and reference it in the
   prose. Never type the number into the manuscript — the claim-section gate
   in `tests/test_manuscript_variables.py` rejects bare numerals, and the
   orphan-token gate rejects variables nobody references.
4. Register it as a gadget in `mission.py` if a coordinator should be able to
   call it. Do not change the `MissionProvider` method signatures.
5. Add a real-data test file, re-run the gate, regenerate figures + tokens.
