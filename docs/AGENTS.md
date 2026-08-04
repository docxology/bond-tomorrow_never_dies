# docs/ — Agent-Facing Documentation Hub

Technical guide for `projects/working/bond/tomorrow_never_dies/docs/` — the
operational rulebook for agents and developers working inside the CARVER
package. Every document here is a hard constraint, not a suggestion.

## File Inventory

| File | Purpose |
|---|---|
| `README.md` | Quick navigation and entry points |
| `AGENTS.md` | This index |
| `agent_instructions.md` | Behavioral constraints (read-first priority) |
| `architecture.md` | Layer contract and module boundaries |
| `testing_philosophy.md` | Zero-mock policy; coverage mechanics |
| `style_guide.md` | 7 style rules (code, docs, types, errors) |
| `output_conventions.md` | `output/` layout and regeneration |

## Reading order

1. `agent_instructions.md`
2. `architecture.md`
3. `testing_philosophy.md`
4. `style_guide.md`
5. `output_conventions.md`

## Key conventions

* **Pure domain core**: `media_manipulation.py`, `stealth_detection.py`,
  `gps_denial.py`, `scenario.py` are stdlib + numpy only; they never import
  `infrastructure.*` or `bond_api`.
* **Single protocol adapter**: `mission.py` is the only contact with
  `bond_api` and registers CARVER's gadgets with the BOND `GadgetRegistry`.
* **Zero mocks**: no `unittest.mock` / `MagicMock` / `@patch` anywhere in
  `tests/`; real data and real computation only.
* **Thin orchestrators**: `scripts/` only import from `src/` and forward.
* **Manuscript tokens**: metrics in prose are injected `{{TOKEN}}`s; never
  hand-authored.

## Verification

These commands verify the critical constraints; run all before submitting:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo Clean
rg -nE "^(from|import) infrastructure|^(from|import) bond_api" \
    src/tomorrow_never_dies/media_manipulation.py \
    src/tomorrow_never_dies/stealth_detection.py \
    src/tomorrow_never_dies/gps_denial.py \
    src/tomorrow_never_dies/scenario.py || echo Clean
rg -n "template[_]code_project" . --glob '!.git/**' --glob '!uv.lock' || echo Clean
```
