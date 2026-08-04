"""Shared pytest configuration: headless matplotlib + project root fixture."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Matplotlib must never open a display window during tests.
os.environ.setdefault("MPLBACKEND", "Agg")


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Absolute path to the package root (the parent of ``tests/``)."""
    return Path(__file__).resolve().parent.parent
