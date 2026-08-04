# Agent Instructions — CARVER

Behavioral rules for AI agents working inside
`projects/working/bond/tomorrow_never_dies`. Read this file *before*
modifying any project file. Each rule states its consequence.

## Rule 1 — Zero mocks, real data only

Do not use `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec`
anywhere. Tests run the actual domain modules on real (deterministic) data.
Deterministic fakes that implement the real protocol are allowed.
*Consequence:* mock tests can pass while the math is wrong.

## Rule 2 — Pure domain core stays infrastructure-free

`media_manipulation.py`, `stealth_detection.py`, `gps_denial.py`, and
`scenario.py` may import only stdlib + numpy. They must not import
`infrastructure.*`, `bond_api`, or `matplotlib`. Only `mission.py` imports
`bond_api`; only `figures.py` imports matplotlib.
*Consequence:* the scientific core becomes unusable standalone.

## Rule 3 — Thin orchestrators

`scripts/` are glue. They bootstrap `src/` onto `sys.path`, import from `src/`,
and forward. No math, no model logic, no speculation in scripts.
*Consequence:* untestable business logic hides in scripts.

## Rule 4 — Manuscript tokens, never hand-authored metrics

A number that changes with `SCENARIO_PARAMS` or `config.yaml` belongs in the
`{{TOKEN}}` map from `src/tomorrow_never_dies/manuscript_variables.py` — never
hardcoded in prose. The live gate
`tests/test_manuscript_variables.py::test_manuscript_tokens_all_generated`
enforces this scan over `manuscript/[0-9]*.md`.
*Consequence:* stale, inaccurate manuscript.

## Rule 5 — Deterministic execution

Fixed seed (7). No untracked random reliance, no wall-clock in persisted
outcomes (`wall_time_s = 0`). Deterministic fakes only.
*Consequence:* non-reproducible results.

## Rule 6 — Type hints and docstrings

Every public function has type hints and a docstring. `ruff` and `mypy` run
on `src/` and `scripts/` as part of the gate.
*Consequence:* mypy/ruff CI failure.

## Rule 7 — Clear error messages

Raise `ValueError` with actionable messages for invalid inputs, and validate
at the boundary. *Consequence:* silent mis-behaviour.

## Verification checklist (run before declaring done)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90         # >=90% line+branch
uv run ruff check src/ scripts/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!.git/**' --glob '!uv.lock'   # aim zero
git status --short                                                    # clean after commit
```

Per the BOND suite guardrails this is a local-only tree: never push, commit
path-scoped inside this package only.
