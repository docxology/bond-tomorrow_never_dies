# tomorrow_never_dies — CARVER

**CARVER** — *Special-Agent Mission Software* for **Tomorrow Never Dies**
(1997) · PROJECT BOND film package.

In the film, Elliot Carver runs a media empire wide enough to manufacture the
wars he then reports, a stealth cruiser radar cannot see, and a GPS spoof that
walks a British frigate into Chinese waters. This package turns that playbook
into six deterministic, reproducible scientific analyses — and, deliberately,
into three **adversarial pairs**: for each weapon, the model of the thing that
answers it.

| Pair | Attack | Counter |
|---|---|---|
| **Media** | `media_manipulation.py` — *whether* people believe | `narrative_control.py` — *how far* opinion moves, and what it costs in fragmentation |
| **Radar** | `stealth_detection.py` — how much range a low-RCS hull buys | `radar_waveform.py` — how much of it pulse compression takes back |
| **Navigation** | `gps_denial.py` — jamming, error growth, cascade | `gnss_integrity.py` — RAIM detection and protection levels |

## Modules

Every module under `src/tomorrow_never_dies/`:

| Module | What it computes |
|---|---|
| `media_manipulation.py` | Two-state belief diffusion (susceptible / believing) on Watts–Strogatz / Barabási–Albert networks; media + social channels; greedy Kempe–Kleinberg–Tardos influence maximization; echo-chamber and amplification metrics |
| `narrative_control.py` | Hegselmann–Krause bounded-confidence opinion dynamics with a media-injection term; polarization variance, bimodal split, media capture against an internal no-media baseline, and the critical broadcast reach found by bisection |
| `stealth_detection.py` | Monostatic radar equation, square-law threshold from `P_fa`, Marcum-Q (numerically integrated) and Swerling-1 detection probabilities, ROC curves, detection range by binary search, RCS-reduction and fourth-root range-ratio metrics |
| `radar_waveform.py` | LFM chirp, Barker-13 phase code, and unmodulated pulses; exact-convolution matched filter; processing gain, range resolution, peak sidelobe ratio, and compression-aware detection range |
| `gps_denial.py` | Walker-delta constellation from real orbital geometry (planes, inclination, receiver-local az/el, horizon culling), geometry matrix and GDOP/PDOP/HDOP/VDOP, jammer-to-noise ratio, C/N0 degradation, UERE and position error, and a maritime dependency-failure cascade run to fixpoint |
| `gnss_integrity.py` | Scipy-free chi-square and noncentral chi-square CDFs and quantiles, SVD parity space, RAIM test statistic and threshold, per-satellite fault slopes, HPL/VPL protection levels, per-satellite parity-projection factors, satellite-specific bias-detection probability |
| `scenario.py` | The one canonical seeded run of all six models (plus the no-media counterfactual) that the mission outcome, the tokens, and the figures all read |
| `mission.py` | The `bond_api` `MissionProvider` adapter and the gadget registry |
| `manuscript_variables.py` | The `{{TOKEN}}` map — scenario inputs *and* results |
| `figures.py` | Six deterministic figures, one per concept |

## Quick start

```bash
uv sync --extra dev                                        # deps + bond-api path dep
uv run python scripts/run_mission.py                       # full five-stage mission
uv run python scripts/z_generate_manuscript_variables.py   # figures + resolved manuscript
uv run pytest tests/ --cov=src --cov-fail-under=90         # the gate
```

`bond-api` is not on PyPI: `[tool.uv.sources]` points `uv` at the PROJECT BOND
monorepo path, so a bare checkout cannot `uv sync` (nor run `run_mission.py`).
The domain core and the test suite do run there — put `src` on `PYTHONPATH`
(plus a `bond_api` copy for the protocol tests) and run
`python -m pytest tests/`.

Individual mission phases have their own thin CLIs: `scripts/brief.py`,
`recon.py`, `plan.py`, `execute.py`, `debrief.py`.

## The MissionProvider surface

`src/tomorrow_never_dies/mission.py` implements the **frozen `bond_api`
`MissionProvider` protocol** (codename THE PROTOCOL), so any coordinator can
discover this package by slug `tomorrow_never_dies` and drive it:

```python
from bond_api.discovery import load_provider
from bond_api.protocol import ReconRequest, run_mission

debrief = run_mission(load_provider("tomorrow_never_dies"), ReconRequest(goal="..."))
```

* `film` → `"tomorrow_never_dies"`; codename `CARVER`.
* `brief()` → objectives (one per concept), three model assets, determinism
  and fidelity constraints.
* `recon(request)` → findings across the six concepts.
* `plan(brief)` → seven steps: one per concept, then `synthesize`.
* `execute(plan)` → a `MissionOutcome` carrying per-step results and
  `Provenance(package_version, seed, input_hash, wall_time_s=0.0)`.
* `debrief(outcome)` → lessons; every quantity re-read from the outcome.
* `GADGETS` / `register_gadgets(registry)` / `GADGET_REGISTRY` → the film's
  callables (`media_campaign`, `opinion_dynamics`, `critical_reach`,
  `radar_detection`, `radar_equation`, `matched_filter`,
  `navigation_cascade`, `raim_detection`, `carver_scenario`), registered at
  import time.

This surface is frozen because `bond-cli`, the coordinator, and the
orchestrator consume it across the whole fleet. Depth goes inside the methods.

## Layer contract

* **Pure domain core** (the six concept modules + `scenario.py`): stdlib +
  numpy only — no `infrastructure.*`, no `bond_api`, no matplotlib. Enforced
  by `tests/test_package_surface.py`, not by convention: the scanned set is
  read from `manuscript/layer_contract.yaml`, so all seven modules —
  `scenario.py` included — are actually grepped.
* **`mission.py`**: the single `bond_api` adapter + gadget registration.
* **`scripts/`**: thin orchestrators, one per mission phase — no math.

See [`docs/architecture.md`](docs/architecture.md) for the full map and
[`docs/agent_instructions.md`](docs/agent_instructions.md) for the rulebook.

## Testing & gates

* **≥90% line + branch** coverage on `src/` is the enforced floor
  (`--cov-fail-under=90`); every `raise ValueError` validation guard in
  `src/` is exercised by a `pytest.raises` test (a small number of defensive
  numerical-stabilisation branches that only fire on pathological input are
  documented in `TODO.md`, not chased).
* **Zero mocks** — real data and real computation only.
* **`ruff` + `mypy`** clean on `src/` and `scripts/`.
* **No hand-authored numbers** in the manuscript's claim-bearing sections —
  gated, with a positive control proving the gate can fail.

Live test count and measured coverage: [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).
Doctrine: [`docs/testing_philosophy.md`](docs/testing_philosophy.md).

## Manuscript

Numbered sections `00`–`07` plus `99_references.md` under `manuscript/`.
Every metric — and every scenario *parameter* — is a `{{TOKEN}}` injected from
`manuscript/config.yaml` and `src/tomorrow_never_dies/manuscript_variables.py`.
The raw sections contain no numbers at all, which is what makes a stale number
impossible to ship. Resolve them with
`scripts/z_generate_manuscript_variables.py`.
