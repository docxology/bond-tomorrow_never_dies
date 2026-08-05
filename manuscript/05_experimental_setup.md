# Experimental Setup

## Scenario configuration

All results derive from one canonical, deterministic scenario
(`src/tomorrow_never_dies/scenario.py`), parameterised in
`manuscript/config.yaml` and `SCENARIO_PARAMS`, executed with a fixed seed
{{CARVER_SEED}}:

* **Media**: a {{MEDIA_NODES}}-node small-world network; the parameters of the
  campaign (reach, persuasion, spread rate, rounds) are constants in
  `SCENARIO_PARAMS`.
* **Narrative**: bounded-confidence opinion dynamics over the same agent
  population, with a confidence radius, a manufactured line, a media weight,
  a broadcast reach, and a critical-reach target share.
* **Stealth**: a monostatic radar with an X-band carrier, coherent pulse
  integration, a reference RCS of 1 m² and a stealth RCS of 0.01 m² at a
  false-alarm probability of 1e-6 and a 0.9 detection target.
* **Waveform**: an LFM chirp ({{WAVEFORM_BANDWIDTH_MHZ}} MHz bandwidth, 50 µs,
  40 MHz sampling) for pulse compression, compared against an unmodulated
  pulse of equal peak power.
* **GPS**: a 24-satellite Walker-style constellation (mask 10°), a 1 W
  jammer at 100 km standoff, a clean C/N0 of 45 dB-Hz, and a maritime
  dependency network of 7 systems.
* **Integrity**: RAIM at a false-alarm rate of 1e-5, a missed-detection rate
  of 1e-3, a measurement sigma of 3 m, and a 0.3 NM maritime alert limit;
  the detection probe is a {{RAIM_BIAS_M}} m measurement bias.

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
