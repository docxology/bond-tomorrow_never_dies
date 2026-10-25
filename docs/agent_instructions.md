# Agent Instructions — CARVER

Behavioral rules for AI agents working inside this package
(`docxology/bond-tomorrow_never_dies`). Read this file *before* modifying any
project file. Each rule states its consequence.

## Rule 1 — Zero mocks, real data only

Do not use `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec`
anywhere. Tests run the actual domain modules on real (deterministic) data.
Deterministic fakes that implement the real protocol are allowed.
*Consequence:* mock tests can pass while the math is wrong.

## Rule 2 — Pure domain core stays infrastructure-free

All six concept modules — `media_manipulation.py`, `narrative_control.py`,
`stealth_detection.py`, `radar_waveform.py`, `gps_denial.py`,
`gnss_integrity.py` — plus `scenario.py` may import only stdlib, numpy, and
each other. They must not import `infrastructure.*`, `bond_api`, or
`matplotlib`. Only `mission.py` imports `bond_api`; only `figures.py` imports
matplotlib. The list of concept modules lives in `CONCEPTS`
(`src/tomorrow_never_dies/__init__.py`); `tests/test_package_surface.py`
pins it against the files on disk and greps each one for banned imports, so
adding a module without declaring it fails the suite.
*Consequence:* the scientific core becomes unusable standalone.

## Rule 3 — Thin orchestrators

`scripts/` are glue. They bootstrap `src/` onto `sys.path`, import from `src/`,
and forward. No math, no model logic, no speculation in scripts.
*Consequence:* untestable business logic hides in scripts.

## Rule 4 — Manuscript tokens, never hand-authored metrics

A number that changes with `SCENARIO_PARAMS` or `config.yaml` belongs in the
`{{TOKEN}}` map from `src/tomorrow_never_dies/manuscript_variables.py` — never
hardcoded in prose. This applies to scenario **inputs** as much as to results:
`_format_params` tokenizes the experimental-setup values so a parameter change
rewrites the setup section instead of silently contradicting it.

Three live gates in `tests/test_manuscript_variables.py` enforce this:

* `test_manuscript_tokens_all_generated` — every token used in
  `manuscript/[0-9]*.md` resolves.
* `test_every_generated_token_is_used_by_the_manuscript` — no orphan tokens.
* `test_no_hand_authored_numbers_in_claim_sections` — no bare numerals in
  `00_abstract.md`, `03_results.md`, or `04_conclusion.md`. Methodology and
  references are exempt (structural constants, page numbers). If you add a
  quantitative claim, add the variable; do not type the number.

*Consequence:* stale, inaccurate manuscript.

## Rule 5 — Deterministic execution

Fixed seed (7). No untracked random reliance, no wall-clock in persisted
outcomes (`wall_time_s = 0`). Deterministic fakes only.
*Consequence:* non-reproducible results.

## Rule 6 — Type hints and docstrings

Every public function has type hints and a docstring. `ruff` and `mypy` run
on `src/` and `scripts/` as part of the gate.
*Consequence:* mypy/ruff CI failure.

## Rule 7 — Clear error messages, and no swallowed ones

Raise `ValueError` with actionable messages for invalid inputs, and validate
at the boundary — including the bool-is-an-int trap, since `isinstance(True,
int)` is `True`. There are **no `try`/`except` blocks anywhere in the domain
core**, and `tests/test_package_surface.py` asserts there are none: a model
that swallows an exception returns a plausible wrong number instead of
failing. *Consequence:* silent mis-behaviour.

## Rule 8 — Do not change the protocol surface

`mission.py` exposes the frozen `bond_api` `MissionProvider` (`film`,
`brief`, `recon`, `plan`, `execute`, `debrief`) plus `GADGETS`,
`register_gadgets`, and `GADGET_REGISTRY`. `bond-cli`, the coordinator's
reconcile step, and the orchestrator consume these across the fleet. Add
depth *inside* the methods; adding, renaming, or re-signing a member breaks
sibling packages you cannot see from here.
*Consequence:* fleet-wide discovery failure.

## Verification checklist (run before declaring done)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90         # >=90% line+branch
uv run ruff check src/ scripts/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!.git/**' --glob '!uv.lock' --glob '!**/AGENTS.md' --glob '!.agents/**'   # aim zero (rule text excluded)
git status --short                                                    # clean after commit
```

Per the BOND suite guardrails, commit path-scoped inside this package only;
the package is published at `github.com/docxology/bond-tomorrow_never_dies`
(the `origin` remote), so finished work lands on `main` there.
