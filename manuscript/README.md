# Manuscript — CARVER (Tomorrow Never Dies, 1997)

The manuscript for the CARVER mission package: a deterministic study of six
paired models — disinformation propagation and narrative control,
stealth-vessel detection and pulse compression, GPS denial and RAIM
integrity.

* `config.yaml` — mission identity + paper metadata (tokens injected from here
  and from `src/tomorrow_never_dies/scenario.py`).
* `00_abstract.md` … `99_references.md` — numbered prose sections.
* `SYNTAX.md` — figure / citation / token reference.
* `layer_contract.yaml` — the import boundary, checked by
  `tests/test_package_surface.py`.

No section file contains a literal number: results *and* scenario parameters
are injected tokens, so the raw prose cannot go stale.

Regenerate the resolved tree (writing `output/data/manuscript_variables.json`,
`output/figures/*.png`, and `output/manuscript/*.md`):

```bash
uv run python scripts/z_generate_manuscript_variables.py
```
