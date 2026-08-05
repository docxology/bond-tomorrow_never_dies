# Testing Philosophy — CARVER

## Zero-mock policy

No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in
`tests/`. Every test runs the real algorithm on real, deterministic data.

The reason is specific, not stylistic: this package's entire output is
numbers. A mocked `detection_probability` returning `0.9` proves the plumbing
works and proves nothing about whether the Marcum-Q quadrature converges. A
mocked filesystem proves nothing about whether a figure actually renders.
Since every model here is cheap and seeded, there is no cost to running the
real thing — the whole suite finishes in seconds.

What *is* allowed: deterministic values constructed by hand as inputs (a small
adjacency tuple, a known geometry matrix), and `tmp_path` for real file I/O.
The line is that nothing may stand in for the code under test.

## Coverage mechanics

The gate measures **line + branch** coverage over `src/tomorrow_never_dies/`
(branch coverage is enabled in `pyproject.toml`):

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

The floor is 90%. Achieved coverage and the live test count are recorded in
[`_generated/COUNTS.md`](_generated/COUNTS.md) and regenerated from a real
run — never quoted from memory in prose elsewhere in this package.

Branch coverage matters more than line coverage here. Every public function
validates its inputs at the boundary and raises `ValueError`, so a
line-coverage-only measurement would happily report success while every
validation branch went untested. Each of those branches is exercised by a
`pytest.raises(ValueError)` test, including the bool-is-an-int traps
(`snr_at_range(True, 1.0)` must be rejected, because `isinstance(True, int)`
is `True` in Python).

## Test file map

| File | Covers |
|---|---|
| `test_media_manipulation.py` | network builders, belief diffusion determinism, media effect, influence maximization, echo chamber, broadcast-footprint nesting, error branches |
| `test_narrative_control.py` | bounded-confidence dynamics, polarization / bimodal / capture, critical reach and its saturating edges, error branches |
| `test_stealth_detection.py` | radar equation, Marcum-Q known values, Swerling closed form, ROC, detection range and its search bound, boundary validation |
| `test_radar_waveform.py` | waveform generation, matched filter, PSLR for LFM and Barker-13, processing gain, detection-range gain, degenerate-pulse errors |
| `test_gps_denial.py` | constellation, DOP identities, jamming/C-N0, UERE, cascade fixpoint, `max_rounds` truncation, unknown-dependent rejection |
| `test_gnss_integrity.py` | chi-square / normal quantiles, parity space, RAIM thresholds, HPL/VPL, noncentral bias detection and its monotonicity |
| `test_mission.py` | protocol conformance, full `run_mission` flow, gadget registry, discovery, serialization round-trip, derived-not-hardcoded debrief quantities |
| `test_scenario.py` | canonical six-block scenario keys, determinism, input-hash stability |
| `test_manuscript_variables.py` | config loading, token map, the `{{TOKEN}}` cross-reference gate, the bare-numeral gate and its positive control, the orphan-token gate |
| `test_package_surface.py` | `CONCEPTS` vs shipped modules, pure-core import purity, no exception handlers in the core, scenario-block/param agreement |
| `test_figures.py` | all six figure generators write valid PNGs |
| `test_scripts_smoke.py` | subprocess smoke of every phase CLI + `z_generate` |

## Gates must be able to fail

A gate nobody can fail is decoration. Three habits keep them honest here:

1. **Positive controls.** `test_claim_section_gate_would_catch_a_hand_authored_number`
   poisons a copy of the results section with a literal percentage and asserts
   the numeral scanner flags it. Without that, a scanner with a broken regex
   would report a clean manuscript forever.
2. **Both directions.** Token coverage is checked twice: every token
   referenced in prose must be generated (`test_manuscript_tokens_all_generated`)
   *and* every token generated must be referenced
   (`test_every_generated_token_is_used_by_the_manuscript`). One direction
   alone lets dead variables accumulate.
3. **Derived, not asserted.** `test_debrief_quantities_are_derived_not_hardcoded`
   re-computes the expected strings from the outcome the provider itself
   produced, so a lesson string that drifts from the scenario fails even
   though it is still a valid-looking sentence.

## Determinism

Fixed seed `7` throughout. Every stochastic draw comes from a seeded
`numpy.random.default_rng`; the broadcast footprint is index-mixed rather than
drawn at all. Tests never depend on wall-clock time — `generate_variables`
takes a `now=` override to pin `GENERATION_TIMESTAMP`, and persisted mission
provenance records `wall_time_s = 0.0`. Re-running the full regeneration
restores a byte-identical tree.

## A note on what these tests do *not* prove

They prove the implementations are internally consistent, deterministic, and
match the closed forms and known values they claim to. They do not validate
the models against measured radar returns, real GNSS logs, or observed
opinion data — CARVER is a didactic mission model, and
[`../manuscript/07_scope_and_related_work.md`](../manuscript/07_scope_and_related_work.md)
states the idealisations. A green suite here means the mathematics is what the
manuscript says it is; it does not mean the world behaves this way.
