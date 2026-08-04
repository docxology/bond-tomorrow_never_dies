# scripts/ — CARVER Mission CLIs

`scripts/` holds **thin orchestrators only**. They bootstrap `src/` onto
`sys.path`, import from `src/`, and forward — no math or model logic lives
here. Business logic belongs in `src/tomorrow_never_dies/`.

| Script | Phase | Delegates to |
|---|---|---|
| `brief.py` | brief | `MissionProvider().brief()` |
| `recon.py` | recon | `MissionProvider().recon(ReconRequest(...))` |
| `plan.py` | plan | `MissionProvider().plan(...)` |
| `execute.py` | execute | `MissionProvider().execute(...)` |
| `debrief.py` | debrief | `bond_api.run_mission` |
| `run_mission.py` | full flow | `bond_api.run_mission` |
| `z_generate_manuscript_variables.py` | tokens+figures | `generate_variables` + `render_figures` |

All scripts are deterministic and exit 0 on success. `run_mission.py` and
`execute.py` return non-zero if the mission outcome reports failure.

Run from the package root:

```bash
uv run python scripts/run_mission.py
uv run python scripts/z_generate_manuscript_variables.py
```
