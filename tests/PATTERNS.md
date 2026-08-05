# Tests — Patterns

## Zero-mock pattern

Every test invokes the real `src/` functions. To test a "deterministic
provider" that must replay state (per BOND suite guidance), subclass a real
provider and override a method to raise — do not mock. This package's actors
are functions, so tests simply call them with fixed arguments.

## Determinism pattern

- Re-run the same function twice and assert byte-identical results
  (e.g. `test_scenario_deterministic`, `test_execute_deterministic`).
- **Never pin a clock to make a determinism test pass.** Injecting a fixed
  `now=` and comparing the two results proves the function is pure, not that
  the artifact is stable — this package shipped exactly that test while every
  regeneration wrote a different manuscript. The rule is now: no producer of a
  persisted artifact may read a clock, and the binding test runs the real
  entry point twice across a second boundary and diffs the bytes
  (`test_regeneration_is_byte_identical`).

## Branch coverage pattern

Every `raise ValueError` in `src/` validation has a matching
`pytest.raises(ValueError)` test (parametrized where useful), because branch
coverage is enabled and the gate is `--cov-fail-under=90`.

## Subprocess smoke pattern

CLIs are exercised end-to-end with `sys.executable` and `cwd=project_root`
(`test_scripts_smoke.py`), asserting exit code 0 and real artifacts.

## Live manuscript gate

`test_manuscript_tokens_all_generated` scans `manuscript/[0-9]*.md` for
`{{TOKEN}}`s and asserts each exists in `generate_variables()` — it fails if
prose ever introduces an ungenerated token.
