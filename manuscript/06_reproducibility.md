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

* Figures: `output/figures/disinformation_propagation.png`,
  `output/figures/stealth_detection.png`, `output/figures/gps_denial.png`.
* Variables: `output/data/manuscript_variables.json`.
* Resolved manuscript: `output/manuscript/*.md`.

All under `output/` are regenerable and git-ignored.
