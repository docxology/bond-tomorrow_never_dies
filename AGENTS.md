# AGENTS.md — CARVER (tomorrow_never_dies)

**PROJECT BOND · Phase 2 film package · mission codename CARVER · Tomorrow
Never Dies (1997).**

This is an active mission package in `projects/working/bond/`. It started as a
`template_code_project` exemplar scaffold and was phase-2-converted into a
deterministic mission-software package. This AGENTS.md is the package's own
operational contract; the shared BOND guardrail preamble governs every package
(scoped to this directory only, local-only tree, path-scoped commits, no mocks,
≥90% coverage, thin orchestrators, no `template_code_project` lineage).

## Concepts

The mission packages three deterministic analyses of Carver-style media
warfare:

1. **Disinformation propagation** (`media_manipulation.py`) — two-channel
   belief diffusion (media exposure + social spread) on a small-world
   network, plus greedy influence maximization and echo-chamber /
   amplification metrics.
2. **Stealth-vessel detection** (`stealth_detection.py`) — monostatic radar
   equation, Marcum-Q / Swerling detection probabilities, detection range of
   a low-RCS hull (the *Sea Vengeance*).
3. **GPS-denial impact** (`gps_denial.py`) — DOP geometry, jamming
   degradation of C/N0, position-error growth, navigation failure cascades.

## Layer contract (enforced by `manuscript/layer_contract.yaml`)

| Surface | Modules | Rule |
|---|---|---|
| Pure domain core | `media_manipulation.py`, `stealth_detection.py`, `gps_denial.py`, `scenario.py` | stdlib + numpy only; no `infrastructure.*`, no `bond_api` |
| Protocol adapter | `mission.py` | The only `bond_api` consumer; registers gadgets |
| Workflow | `figures.py`, `manuscript_variables.py` | matplotlib / yaml + core; render & inject |
| Orchestrators | `scripts/*.py` | Thin CLIs; no business logic |

`mission.py` implements the **FROZEN `bond_api` `MissionProvider`** protocol
(see the bond-api phase-1 build record). It is discoverable by slug
`tomorrow_never_dies` and registers its gadgets with the BOND `GadgetRegistry`.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!.git/**' --glob '!uv.lock'   # aim zero
git status --short                                                     # clean after commit
```

Live test count + coverage: [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).

## Manuscript

Metrics in `manuscript/` are injected `{{TOKEN}}`s from `config.yaml` +
`src/tomorrow_never_dies/scenario.py` via `manuscript_variables.py` — never
hand-authored. Figures live in `output/figures/` (git-ignored, regenerable).

## Docs

Operational rulebook: [`docs/agent_instructions.md`](docs/agent_instructions.md) ·
architecture: [`docs/architecture.md`](docs/architecture.md) ·
testing: [`docs/testing_philosophy.md`](docs/testing_philosophy.md).
