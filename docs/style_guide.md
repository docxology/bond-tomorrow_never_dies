# Style Guide

Seven rules for the CARVER package.

1. **Zero-Mock**: never use mocks; real data + computation only.
2. **Layer discipline**: pure domain core (stdlib + numpy only); the mission
   adapter is the only `bond_api` consumer; scripts are thin.
3. **Thin Orchestrator**: business logic lives in `src/`; `scripts/` forward.
4. **Show-Not-Tell**: manuscript references use explicit file paths and
   function names, and all metrics are `{{TOKEN}}`s — never implied numbers.
5. **Explicit Paths**: no magic paths; project-relative paths computed from
   `Path(__file__)` or passed explicitly.
6. **Type Hints**: full annotations on all public functions.
7. **Error Messages**: validate at the boundary and raise `ValueError` with
   actionable messages.

Formatting is `ruff` (88 cols), and `mypy` runs on `src/` and `scripts/`.
