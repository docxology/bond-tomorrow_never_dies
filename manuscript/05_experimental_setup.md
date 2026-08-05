# Experimental Setup

## Scenario configuration

All results derive from one canonical, deterministic scenario
(`src/tomorrow_never_dies/scenario.py`), parameterised in
`manuscript/config.yaml` and `SCENARIO_PARAMS`, executed with a fixed seed
{{CARVER_SEED}}:

Every value below is an injected token read out of `SCENARIO_PARAMS` itself,
not a transcription of it: changing a parameter rewrites this section on the next
regeneration, so the setup can never describe a run that did not happen.

* **Media**: a {{MEDIA_NODES}}-node small-world network; a broadcast reaching
  {{MEDIA_REACH_PCT}}% of it, per-exposure persuasion {{MEDIA_PERSUASION}}, per-edge
  social spread {{MEDIA_SPREAD_RATE}}, over {{MEDIA_STEPS}} rounds.
* **Narrative**: bounded-confidence opinion dynamics over
  {{NARRATIVE_AGENTS}} agents with confidence radius {{NARRATIVE_CONFIDENCE}}, a
  manufactured line at {{NARRATIVE_MEDIA_OPINION}}, media weight
  {{NARRATIVE_MEDIA_WEIGHT}}, broadcast reach {{NARRATIVE_REACH_PCT}}%, over
  {{NARRATIVE_STEPS}} rounds; the critical-reach search targets a
  {{NARRATIVE_TARGET_SHARE_PCT}}% belief share.
* **Stealth**: a monostatic radar with a {{RADAR_FREQUENCY_GHZ}} GHz (X-band)
  carrier and {{RADAR_PULSES}} coherently integrated pulses; a reference RCS of
  {{STEALTH_REF_RCS_SQM}} m² and a stealth RCS of {{STEALTH_RCS_SQM}} m² at a
  false-alarm probability of {{STEALTH_PFA}} and a {{STEALTH_PD_TARGET}} detection
  target.
* **Waveform**: an LFM chirp ({{WAVEFORM_BANDWIDTH_MHZ}} MHz bandwidth,
  {{WAVEFORM_PULSE_WIDTH_US}} µs, {{WAVEFORM_SAMPLE_RATE_MHZ}} MHz sampling) for
  pulse compression, compared against an unmodulated pulse of equal peak power
  *and equal range resolution* ({{WAVEFORM_UNMOD_WIDTH_US}} µs) and against the
  Barker-13 phase code.
* **GPS**: a {{GPS_SATELLITES}}-satellite Walker-delta constellation in
  {{GPS_PLANES}} planes at {{GPS_INCLINATION_DEG}}° inclination, seen from a
  receiver at {{GPS_RECEIVER_LAT_DEG}}°N {{GPS_RECEIVER_LON_DEG}}°E in the
  South China Sea (elevation mask {{GPS_MASK_ANGLE_DEG}}°, leaving
  {{GPS_VISIBLE_SATS}} satellites in view at the modelled epoch), a
  {{GPS_JAMMER_POWER_W}} W jammer at
  {{GPS_JAMMER_STANDOFF_KM}} km standoff, a clean C/N0 of {{GPS_CNO_CLEAN_DBHZ}}
  dB-Hz, and a maritime dependency network of {{GPS_NETWORK_SIZE}} systems.
* **Integrity**: RAIM at a false-alarm rate of {{INTEGRITY_PFA}}, a
  missed-detection rate of {{INTEGRITY_PMD}}, a measurement sigma of
  {{INTEGRITY_SIGMA_M}} m, and a maritime alert limit of
  {{INTEGRITY_ALERT_LIMIT_M}} m (0.3 NM); the detection probe is a
  {{RAIM_BIAS_M}} m measurement bias.

## Software environment

* Package: {{CARVER_IDENTITY}}, version {{CARVER_VERSION}}, maintained by
  {{CARVER_AUTHOR}}.
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
