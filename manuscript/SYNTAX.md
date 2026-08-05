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
| `{#fig:disinformation}` | `output/figures/disinformation_propagation.png` | `src/tomorrow_never_dies/figures.py::fig_disinformation` |
| `{#fig:narrative}` | `output/figures/narrative_control.png` | `src/tomorrow_never_dies/figures.py::fig_narrative` |
| `{#fig:stealth}` | `output/figures/stealth_detection.png` | `src/tomorrow_never_dies/figures.py::fig_stealth_detection` |
| `{#fig:waveform}` | `output/figures/waveform_pulse_compression.png` | `src/tomorrow_never_dies/figures.py::fig_waveform` |
| `{#fig:gps}` | `output/figures/gps_denial.png` | `src/tomorrow_never_dies/figures.py::fig_gps_denial` |
| `{#fig:raim}` | `output/figures/raim_detection.png` | `src/tomorrow_never_dies/figures.py::fig_raim` |

## Citations

Use the BibTeX keys in `references.bib` (e.g. `@marcum1960statistical`) via
Pandoc `[@key]` / `@key`.

The numbered prose sections that carry tokens are `00_abstract`, `02_methodology`,
`03_results`, `05_experimental_setup`, `06_reproducibility` — the live gate
scans exactly the `[0-9]*.md` files.
