# scripts/ — CARVER Mission CLIs

Thin, deterministic per-phase CLIs for the CARVER mission package.

```bash
uv run python scripts/brief.py        # mission brief
uv run python scripts/recon.py "goal" # recon findings
uv run python scripts/plan.py         # plan steps
uv run python scripts/execute.py      # outcome + provenance
uv run python scripts/debrief.py      # lessons learned
uv run python scripts/run_mission.py  # full five-stage flow
uv run python scripts/z_generate_manuscript_variables.py  # figures + {{TOKEN}}s
```

See [`AGENTS.md`](AGENTS.md) for the delegation table.
