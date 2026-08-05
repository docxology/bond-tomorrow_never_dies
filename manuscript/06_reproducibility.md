# Reproducibility

## Determinism guarantees

* **Fixed seed**: every stochastic draw flows from `numpy.random.default_rng({{CARVER_SEED}})`;
  identical inputs produce byte-identical trajectories.
* **No wall-clock in outcomes**: mission provenance records `wall_time_s = 0`.
* **Canonical input hash**: the `script/driver` records a sha256
  fingerprint of `SCENARIO_PARAMS` so any outcome can be audited against its
  inputs without re-running the film.

## Verification

The suite is verified with the gates in the package preamble:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
rg -n "template[_]code_project" . --glob '!.git/**' --glob '!uv.lock'   # -> zero
git status --short                                                       # clean
```

Live test count and achieved coverage are tracked in
[`docs/_generated/COUNTS.md`](../docs/_generated/COUNTS.md), not hardcoded in
this manuscript.

## Artifacts

* Figures (one per domain concept):
  `output/figures/disinformation_propagation.png`,
  `output/figures/narrative_control.png`,
  `output/figures/stealth_detection.png`,
  `output/figures/waveform_pulse_compression.png`,
  `output/figures/gps_denial.png`,
  `output/figures/raim_detection.png`.
* Variables: `output/data/manuscript_variables.json`.
* Resolved manuscript: `output/manuscript/*.md`.

All under `output/` are regenerable and git-ignored.

## What is *not* reproducible from this manuscript alone

The section files hold token placeholders, not numbers. Reading the raw
`manuscript/*.md` gives the argument but no values; the values only exist
after `z_generate_manuscript_variables.py` has run the canonical scenario.
That is deliberate — it makes a stale number impossible to ship, because
there is no number in the source to go stale.
