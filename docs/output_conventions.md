# Output Conventions

`output/` holds regenerable artifacts only; it is git-ignored. Nothing that
must be versioned lives under `output/`.

## Layout

| Path | Producer | Consumer |
|---|---|---|
| `output/data/manuscript_variables.json` | `scripts/z_generate_manuscript_variables.py` | manuscript injection |
| `output/manuscript/*.md` | `scripts/z_generate_manuscript_variables.py` | rendered PDF / review |
| `output/figures/disinformation_propagation.png` | `src/tomorrow_never_dies/figures.py` | `manuscript/03_results.md` |
| `output/figures/narrative_control.png` | `src/tomorrow_never_dies/figures.py` | `manuscript/03_results.md` |
| `output/figures/stealth_detection.png` | `src/tomorrow_never_dies/figures.py` | `manuscript/03_results.md` |
| `output/figures/waveform_pulse_compression.png` | `src/tomorrow_never_dies/figures.py` | `manuscript/03_results.md` |
| `output/figures/gps_denial.png` | `src/tomorrow_never_dies/figures.py` | `manuscript/03_results.md` |
| `output/figures/raim_detection.png` | `src/tomorrow_never_dies/figures.py` | `manuscript/03_results.md` |

## Regeneration

```bash
uv run python scripts/z_generate_manuscript_variables.py
```

Run the smoke test to confirm regeneration is clean:
`uv run pytest tests/test_scripts_smoke.py`.

## Determinism

Because every producer is seeded and wall-clock-free, re-running regeneration
restores a byte-identical, git-clean tree.
