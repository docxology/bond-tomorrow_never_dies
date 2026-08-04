# CONVENTIONS — CARVER scripts

1. **Thin**: scripts import from `src/` and forward; they never contain math,
   model logic, or speculative formatting.
2. **Bootstrap**: each script inserts `<root>/src` onto `sys.path` (with
   `# noqa: E402`) so it runs as a plain `python scripts/x.py` too.
3. **Deterministic output**: plain `print`, stable ordering, no wall-clock,
   no timestamps in stdout that would break byte-determinism of artifacts.
4. **Exit codes**: `0` iff the phase succeeds; `run_mission` / `execute`
   return non-zero when `outcome.success` is false.
5. **`z_generate_manuscript_variables.py`** is strict: it fails loudly if any
   `{{TOKEN}}` in a numbered prose section remains unresolved.
