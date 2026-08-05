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

Every producer is seeded and wall-clock-free, so re-running regeneration on
the same checkout and interpreter restores a byte-identical, git-clean tree —
including the six PNGs.

The scope words "same interpreter" are load-bearing. Exactly one generated
token, `PYTHON_VERSION`, is read from the running interpreter
(`sys.version_info`), so the resolved manuscript differs between a 3.12 and a
3.14 run. Nothing else in `output/` depends on the environment, and nothing at
all depends on the moment of the run: there is no generation timestamp. The
manuscript's date is `paper.date` from `manuscript/config.yaml`, a committed
value that only changes when someone edits it.

This is enforced, not asserted:
`tests/test_scripts_smoke.py::test_regeneration_is_byte_identical` invokes
`scripts/z_generate_manuscript_variables.py` twice in separate subprocesses,
deliberately separated by more than one second, and compares the sha256 of
every file under `output/`. A wall-clock value re-entering any persisted
artifact turns that test red — which is precisely what an earlier
`GENERATION_TIMESTAMP` token did to this claim, undetected, because the only
determinism test at the time pinned the clock with a `now=` override instead
of running the generator twice for real.
