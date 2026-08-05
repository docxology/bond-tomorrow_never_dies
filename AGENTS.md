# AGENTS.md — CARVER (tomorrow_never_dies)

**PROJECT BOND film package · mission codename CARVER · Tomorrow Never Dies
(1997).**

An active mission package in `projects/working/bond/`. It began as a
`template_code_project` exemplar scaffold, was converted in phase 2 into a
deterministic mission-software package, and was deepened in phase 4 to six
domain models. This file is the package's own operational contract; the shared
BOND guardrail preamble governs every package (scoped to this directory only,
local-only tree, path-scoped commits, no mocks, ≥90% coverage, thin
orchestrators, no `template_code_project` lineage strings).

## Concepts

Six deterministic analyses of Carver's playbook, arranged as three
attack/counter pairs:

1. **Disinformation propagation** (`media_manipulation.py`) — two-channel
   belief diffusion (media exposure + social spread) on a small-world
   network, greedy influence maximization, echo-chamber and amplification
   metrics.
2. **Narrative control** (`narrative_control.py`) — Hegselmann–Krause
   bounded-confidence opinion dynamics with a Carver-style media injection;
   polarization and bimodal-split metrics, media capture measured against an
   internally simulated no-media baseline, and the critical broadcast reach
   that tips the discrete belief model.
3. **Stealth-vessel detection** (`stealth_detection.py`) — monostatic radar
   equation, Marcum-Q / Swerling detection probabilities, detection range of
   a low-RCS hull (the *Sea Vengeance*).
4. **Pulse compression** (`radar_waveform.py`) — LFM chirp and Barker-13
   matched filtering: processing gain, range resolution, sidelobe floors, and
   the fourth-root detection-range recovery against a stealth hull.
5. **GPS-denial impact** (`gps_denial.py`) — DOP geometry, jamming
   degradation of C/N0, position-error growth, navigation failure cascades.
6. **GNSS integrity** (`gnss_integrity.py`) — scipy-free chi-square /
   parity-space RAIM: detection thresholds, HPL/VPL protection levels, and
   bias-detection probability.

The module list is not maintained by hand: `CONCEPTS` in
`src/tomorrow_never_dies/__init__.py` declares it and
`tests/test_package_surface.py` pins it against the files on disk.

## Layer contract (also declared in `manuscript/layer_contract.yaml`)

| Surface | Modules | Rule |
|---|---|---|
| Pure domain core | the six concept modules + `scenario.py` (the list `tests/test_package_surface.py` reads from `layer_contract.yaml` and greps) | stdlib + numpy + siblings only; no `infrastructure.*`, no `bond_api`, no matplotlib |
| Protocol adapter | `mission.py` | The only `bond_api` consumer; registers gadgets at import |
| Workflow | `figures.py`, `manuscript_variables.py` | matplotlib / yaml + `scenario`; render & inject |
| Orchestrators | `scripts/*.py` | Thin CLIs; no business logic |

`mission.py` implements the **FROZEN `bond_api` `MissionProvider`**. It is
discoverable by slug `tomorrow_never_dies` and registers its gadgets with the
BOND `GadgetRegistry`. Do not change that surface — see
[`docs/architecture.md`](docs/architecture.md) for the member-by-member map.

## Build

```bash
uv sync --extra dev        # installs deps + the bond-api path dependency
```

There is no compile step. `src/` is installed in editable mode via
`pyproject.toml`; `scripts/` bootstrap `src/` onto `sys.path` so every CLI
runs from a bare checkout.

## Test

```bash
# The gate (line + branch coverage over src/, floor 90%)
uv run pytest tests/ --cov=src --cov-fail-under=90

# A single file or test
uv run pytest tests/test_gnss_integrity.py -v
uv run pytest tests/test_mission.py::test_execute -v

# Regenerate outputs, then confirm the smoke path still passes
uv run python scripts/z_generate_manuscript_variables.py
uv run pytest tests/test_scripts_smoke.py
```

## Verify

Run all of these before declaring done:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90       # 0 failed, 0 skipped, >=90%
uv run ruff check src/ scripts/
uv run ruff format --check src/ scripts/
uv run mypy src/
uv run python scripts/run_mission.py                     # protocol end-to-end
rg -n "template[_]code_project" . --glob '!.git/**' --glob '!uv.lock'   # aim zero
git status --short                                       # clean after commit
```

`uv` cannot write its cache under a restrictive sandbox. A
`Failed to initialize cache` error is an environment restriction, not a
package failure — re-run with the sandbox disabled.

Live test count and measured coverage: [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).
Do not quote a coverage figure anywhere else in this package; reference the
gate or that generated file instead.

## Manuscript

Metrics in `manuscript/` are injected `{{TOKEN}}`s from `config.yaml` plus
`src/tomorrow_never_dies/scenario.py` via `manuscript_variables.py` — never
hand-authored. Scenario *parameters* are tokenized too, so the
experimental-setup section is generated rather than transcribed. Three tests
enforce this: tokens-all-resolve, no-orphan-tokens, and no-bare-numerals in
the abstract/results/conclusion (with a positive control). Figures live in
`output/figures/` (git-ignored, regenerable).

## Docs

Operational rulebook: [`docs/agent_instructions.md`](docs/agent_instructions.md) ·
architecture and protocol map: [`docs/architecture.md`](docs/architecture.md) ·
testing doctrine: [`docs/testing_philosophy.md`](docs/testing_philosophy.md) ·
style: [`docs/style_guide.md`](docs/style_guide.md) ·
outputs: [`docs/output_conventions.md`](docs/output_conventions.md).
