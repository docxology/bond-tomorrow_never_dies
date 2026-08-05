# Manuscript SYNTAX — CARVER

## `{{TOKEN}}` protocol

Numeric values derived from the scenario *must* use `{{TOKEN}}` syntax; they are
injected by `scripts/z_generate_manuscript_variables.py` from
`src/tomorrow_never_dies/manuscript_variables.py`. The authoritative map is
the return value of `generate_variables()`; the live cross-reference test
(`tests/test_manuscript_variables.py::test_manuscript_tokens_all_generated`)
gates that every `{{TOKEN}}` in a numbered prose section resolves.

**Never hand-author a metric in prose.** If a number would change when
`SCENARIO_PARAMS` or `config.yaml` changes, it is a token.

## Figures

Reference every figure via Pandoc-crossref `[@fig:label]` / `@fig:label`,
never with a hardcoded number:

| Label | PNG | Generator |
|---|---|---|
| `{#fig:disinformation}` | `output/figures/disinformation_propagation.png` | `src/tomorrow_never_dies/figures.py::build_disinformation` |
| `{#fig:narrative}` | `output/figures/narrative_control.png` | `src/tomorrow_never_dies/figures.py::build_narrative` |
| `{#fig:stealth}` | `output/figures/stealth_detection.png` | `src/tomorrow_never_dies/figures.py::build_stealth_detection` |
| `{#fig:waveform}` | `output/figures/waveform_pulse_compression.png` | `src/tomorrow_never_dies/figures.py::build_waveform` |
| `{#fig:gps}` | `output/figures/gps_denial.png` | `src/tomorrow_never_dies/figures.py::build_gps_denial` |
| `{#fig:raim}` | `output/figures/raim_detection.png` | `src/tomorrow_never_dies/figures.py::build_raim` |

## Citations

The rendered bibliography is the hand-numbered list in `99_references.md`, and
prose refers to works by author name (`Hegselmann–Krause`, `Skolnik`), not by
Pandoc citation key. **No numbered section carries a `[@key]` citation, and
none is expected to** — the only Pandoc-style references in prose are
`@fig:*` crossrefs.

`references.bib` exists so the same works are available machine-readably for
export and archival metadata. It is *not* decorative and *not* free to drift:
`tests/test_references.py::test_bibliography_and_bibtex_agree` binds the two
lists entry-for-entry on (first-author surname, year), so adding a work to one
without the other fails the suite. Add or remove a reference in both files.

The numbered prose sections that carry tokens are `00_abstract`, `02_methodology`,
`03_results`, `05_experimental_setup`, `06_reproducibility` — the live gate
scans exactly the `[0-9]*.md` files.
