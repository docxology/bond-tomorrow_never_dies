# docs/ — CARVER Documentation Hub

Everything an agent or a human needs to work inside the
`tomorrow_never_dies` (CARVER) mission package, excluding the manuscript
(which documents itself under [`../manuscript/`](../manuscript/)) and the
package overview (which lives in [`../README.md`](../README.md)).

## What is here

| File | Read it when |
|---|---|
| [`agent_instructions.md`](agent_instructions.md) | **Read first.** Eight behavioral rules, each with its consequence, plus the verification checklist |
| [`architecture.md`](architecture.md) | You need the layer contract, what each of the six domain modules computes, or how `mission.py` satisfies the frozen `MissionProvider` protocol |
| [`testing_philosophy.md`](testing_philosophy.md) | You are writing or changing tests — the no-mock doctrine, branch-coverage reasoning, the test file map, and why every gate carries a positive control |
| [`style_guide.md`](style_guide.md) | You are writing code and want the seven house rules |
| [`output_conventions.md`](output_conventions.md) | You are producing or consuming anything under `output/` |
| [`AGENTS.md`](AGENTS.md) | You want the file inventory, reading order, and copy-paste constraint checks for this directory |
| [`_generated/COUNTS.md`](_generated/COUNTS.md) | You need the live test count, coverage, module count, or gadget count — **generated**, never quoted from memory |

## The short version

CARVER models six concepts from *Tomorrow Never Dies* as three adversarial
pairs — disinformation vs. narrative dynamics, stealth vs. pulse compression,
GPS denial vs. RAIM integrity — each a deterministic, infrastructure-free
module under `src/tomorrow_never_dies/`. `scenario.py` runs all six once with
seed 7; that single run feeds the mission outcome, the manuscript tokens, and
the figures, so they cannot disagree. `mission.py` adapts the same core to the
frozen `bond_api` protocol so any coordinator can drive it by slug.

Three properties are non-negotiable and are enforced by tests rather than by
convention: zero mocks, determinism, and no hand-authored numbers in the
manuscript.

## Where else to look

Package entry points: [`../README.md`](../README.md) ·
[`../AGENTS.md`](../AGENTS.md) · [`../TODO.md`](../TODO.md).
Manuscript conventions: [`../manuscript/SYNTAX.md`](../manuscript/SYNTAX.md).
Layer contract as data: [`../manuscript/layer_contract.yaml`](../manuscript/layer_contract.yaml).
