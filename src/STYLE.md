# STYLE — src/tomorrow_never_dies

1. Ruff formatting, 88-col line length; run `uv run ruff format` then
   `uv run ruff check`.
2. `from __future__ import annotations` at the top of every module.
3. Full type hints on all public functions; `mypy_path = ["src"]` and
   `explicit_package_bases = true` in `pyproject.toml`.
4. Frozen dataclasses for immutable domain values; validate in
   `__post_init__` with actionable `ValueError` messages.
5. Deterministic: fixed seeds; never read the clock into persisted outcomes.
6. Pure core imports only stdlib + numpy; mission.py is the single `bond_api`
   contact.
