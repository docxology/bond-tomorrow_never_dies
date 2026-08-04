# Manuscript — CARVER (Tomorrow Never Dies, 1997)

The manuscript for the CARVER mission package: a deterministic study of
disinformation propagation, stealth-vessel detection, and GPS-denial impact.

* `config.yaml` — mission identity + paper metadata (tokens injected from here
  and from `src/tomorrow_never_dies/scenario.py`).
* `00_abstract.md` … `99_references.md` — numbered prose sections.
* `SYNTAX.md` — figure / citation / `{{TOKEN}}` reference.

Regenerate the resolved tree (writing `output/data/manuscript_variables.json`,
`output/figures/*.png`, and `output/manuscript/*.md`):

```bash
uv run python scripts/z_generate_manuscript_variables.py
```
