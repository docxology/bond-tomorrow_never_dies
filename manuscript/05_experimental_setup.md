# Experimental Setup

## Scenario configuration

All results derive from one canonical, deterministic scenario
(`src/tomorrow_never_dies/scenario.py`), parameterised in
`manuscript/config.yaml` and `SCENARIO_PARAMS`, executed with a fixed seed
{{CARVER_SEED}}:

* **Media**: a {{MEDIA_NODES}}-node small-world network; the parameters of the
  campaign (reach, persuasion, spread rate, rounds) are constants in
  `SCENARIO_PARAMS`.
* **Stealth**: a monostatic radar with an X-band carrier, coherent pulse
  integration, a reference RCS of 1 m² and a stealth RCS of 0.01 m² at a
  false-alarm probability of 1e-6 and a 0.9 detection target.
* **GPS**: a 24-satellite Walker-style constellation (mask 10°), a 1 W
  jammer at 100 km standoff, a clean C/N0 of 45 dB-Hz, and a maritime
  dependency network of 7 systems.

## Software environment

* Package: {{CARVER_IDENTITY}}, version {{CARVER_VERSION}}.
* Python: {{PYTHON_VERSION}}.
* Determinism: fixed seed {{CARVER_SEED}}; no wall-clock in persisted
  outcomes (`wall_time_s = 0`); no untracked random draws.

## Regeneration

```bash
# Canonical results + figures + resolved manuscript:
uv run python scripts/z_generate_manuscript_variables.py
# Full mission lifecycle via the protocol:
uv run python scripts/run_mission.py
```

Generated at {{GENERATION_TIMESTAMP}}.
