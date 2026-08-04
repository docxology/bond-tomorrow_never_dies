"""Tests for CARVER figure generation."""

from __future__ import annotations

from pathlib import Path

from tomorrow_never_dies.figures import render_figures


def test_render_figures(tmp_path: Path) -> None:
    paths = render_figures(tmp_path)
    assert set(paths) == {"disinformation", "stealth_detection", "gps_denial"}
    for name, path in paths.items():
        assert path.is_file(), name
        assert path.suffix == ".png"
        assert path.stat().st_size > 1000
