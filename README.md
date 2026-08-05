# tomorrow_never_dies — CARVER

**CARVER** — *Special-Agent Mission Software* for **Tomorrow Never Dies** (1997) ·
PROJECT BOND film package.

A deterministic, infrastructure-free mission package that turns Elliot
Carver's media-warfare playbook into six reproducible scientific analyses
(three original concept areas, deepened in phase 4 with three more):

| Concept | Module | What it computes |
|---|---|---|
| Disinformation propagation | `media_manipulation.py` | belief diffusion on a social network with media-campaign injection and greedy influence maximization |
| Narrative control | `narrative_control.py` | bounded-confidence opinion dynamics (Hegselmann–Krause) with media injection; echo-chamber polarization, media capture, critical reach |
| Stealth-vessel detection | `stealth_detection.py` | radar equation, Marcum-Q / Swerling detection probabilities, detection range of a low-RCS hull |
| Pulse compression | `radar_waveform.py` | LFM / Barker-13 matched filtering: processing gain, range resolution, sidelobe levels, detection-range gain |
| GPS-denial impact | `gps_denial.py` | satellite geometry and DOP, jamming degradation of C/N0, position-error growth, navigation failure cascades |
| GNSS integrity (RAIM) | `gnss_integrity.py` | chi-square/parity-space detection, HPL/VPL protection levels, bias-detection probability |

The same core is exposed through the **FROZEN `bond_api` `MissionProvider`
protocol** (codename THE PROTOCOL): `src/tomorrow_never_dies/mission.py` lets
any coordinator discover the package by slug `tomorrow_never_dies` and drive
the full brief → recon → plan → execute → debrief lifecycle.

## Quick start

```bash
uv sync --extra dev                 # installs deps + bond-api path dep
uv run python scripts/run_mission.py          # full five-stage mission
uv run python scripts/z_generate_manuscript_variables.py  # figures + tokens
uv run pytest tests/ --cov=src --cov-fail-under=90         # gate
```

## Layer contract

* Pure domain core (`media_manipulation`, `stealth_detection`,
  `gps_denial`, `scenario`): stdlib + numpy only — no `infrastructure.*`, no
  `bond_api`.
* `mission.py`: the single `bond_api` adapter + gadget registration.
* `scripts/`: thin orchestrators per mission phase.

See [`docs/agent_instructions.md`](docs/agent_instructions.md) for the
operational rulebook and full verification checklist.

## Testing & gates

* 90%+ line+branch on `src/` (all validation branches exercised).
* Zero mocks — real data + real computation only.
* `ruff` + `mypy` clean on `src/` and `scripts/`.
* No `template_code_project` lineage strings.

Live test count + coverage: [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).

## Manuscript

Numbered sections under `manuscript/`; every metric is a `{{TOKEN}}` injected
from `manuscript/config.yaml` + the canonical scenario, never hand-authored.
