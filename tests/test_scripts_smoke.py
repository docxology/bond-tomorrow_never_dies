"""Subprocess smoke tests for the thin CARVER phase CLIs.

Each script is invoked with the venv interpreter from the project root (so
the scripts' own ``sys.path`` bootstrap applies) and must exit 0.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PHASE_SCRIPTS = (
    "brief.py",
    "recon.py",
    "plan.py",
    "execute.py",
    "debrief.py",
    "run_mission.py",
)


def run_script(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["MPLBACKEND"] = "Agg"
    return subprocess.run(  # noqa: PLW1510 — returncode inspected below
        [sys.executable, str(PROJECT_ROOT / "scripts" / name), *args],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )


@pytest.mark.parametrize("script", PHASE_SCRIPTS)
def test_phase_scripts_exit_zero(script: str) -> None:
    result = run_script(script)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()


def test_recon_with_goal_argument() -> None:
    result = run_script("recon.py", "scan", "the", "theater")
    assert result.returncode == 0
    assert "scan the theater" in result.stdout


def test_z_generate_manuscript_variables() -> None:
    result = run_script("z_generate_manuscript_variables.py")
    assert result.returncode == 0, result.stderr

    variables_path = PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    assert variables_path.is_file()
    variables = json.loads(variables_path.read_text(encoding="utf-8"))
    assert variables["CARVER_CODENAME"] == "CARVER"
    assert float(variables["STEALTH_RCS_REDUCTION_DB"]) == pytest.approx(20.0)

    resolved_dir = PROJECT_ROOT / "output" / "manuscript"
    sections = sorted(resolved_dir.glob("[0-9]*.md"))
    assert sections
    for section in sections:
        assert "{{" not in section.read_text(encoding="utf-8")

    figures_dir = PROJECT_ROOT / "output" / "figures"
    for name in (
        "disinformation_propagation.png",
        "stealth_detection.png",
        "gps_denial.png",
    ):
        assert (figures_dir / name).is_file(), name
