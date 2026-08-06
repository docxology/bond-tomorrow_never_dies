# docs/ — Agent-Facing Documentation Hub

Technical guide for `projects/working/bond/tomorrow_never_dies/docs/` — the
operational rulebook for agents and developers working inside the CARVER
package. Every document here is a hard constraint, not a suggestion.

## File Inventory

| File | Purpose |
|---|---|
| `README.md` | Quick navigation and entry points |
| `AGENTS.md` | This index |
| `agent_instructions.md` | Eight behavioral constraints (read-first priority) |
| `architecture.md` | Layer contract, per-module computation map, and the frozen `MissionProvider` implementation |
| `testing_philosophy.md` | Zero-mock policy; branch-coverage mechanics; gate honesty |
| `style_guide.md` | 7 style rules (code, docs, types, errors) |
| `output_conventions.md` | `output/` layout and regeneration |

## Reading order

1. `agent_instructions.md`
2. `architecture.md`
3. `testing_philosophy.md`
4. `style_guide.md`
5. `output_conventions.md`

## Key conventions

* **Pure domain core**: `media_manipulation.py`, `narrative_control.py`,
  `stealth_detection.py`, `radar_waveform.py`, `gps_denial.py`,
  `gnss_integrity.py`, `scenario.py` are stdlib + numpy only; they never
  import `infrastructure.*` or `bond_api`.
* **Single protocol adapter**: `mission.py` is the only contact with
  `bond_api` and registers CARVER's gadgets with the BOND `GadgetRegistry`.
* **Zero mocks**: no `unittest.mock` / `MagicMock` / `@patch` anywhere in
  `tests/`; real data and real computation only.
* **Thin orchestrators**: `scripts/` only import from `src/` and forward.
* **Manuscript tokens**: metrics in prose are injected `{{TOKEN}}`s; never
  hand-authored. Scenario *inputs* are tokenized too — the experimental-setup
  section is generated from `SCENARIO_PARAMS`, not transcribed from it.
* **Frozen protocol**: `mission.py`'s `MissionProvider` surface and the
  `GADGETS` / `register_gadgets` / `GADGET_REGISTRY` convention are consumed
  fleet-wide. Deepen inside; never change the shape.

## Verification

These commands verify the critical constraints; run all before submitting:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo Clean
rg -nE "^(from|import) infrastructure|^(from|import) bond_api" \
    src/tomorrow_never_dies/media_manipulation.py \
    src/tomorrow_never_dies/narrative_control.py \
    src/tomorrow_never_dies/stealth_detection.py \
    src/tomorrow_never_dies/radar_waveform.py \
    src/tomorrow_never_dies/gps_denial.py \
    src/tomorrow_never_dies/gnss_integrity.py \
    src/tomorrow_never_dies/scenario.py || echo Clean
rg -n "template[_]code_project" . --glob '!.git/**' --glob '!uv.lock' --glob '!**/AGENTS.md' || echo Clean
uv run ruff check src/ scripts/ && uv run ruff format --check src/ scripts/
uv run mypy src/
```

The import-purity grep above is a convenience; the binding check is
`tests/test_package_surface.py`, which derives the module list from
`CONCEPTS` instead of a hand-maintained path list, so it cannot go stale when
a module is added.
