"""Subprocess smoke tests for the thin CARVER phase CLIs.

Each script is invoked with the venv interpreter from the project root (so
the scripts' own ``sys.path`` bootstrap applies) and must exit 0.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
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
        "narrative_control.png",
        "stealth_detection.png",
        "waveform_pulse_compression.png",
        "gps_denial.png",
        "raim_detection.png",
    ):
        assert (figures_dir / name).is_file(), name


def _output_digest(root: Path) -> dict[str, str]:
    """sha256 every regenerable file under ``output/``, keyed by relative path."""
    out = root / "output"
    return {
        str(path.relative_to(out)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(out.rglob("*"))
        if path.is_file()
    }


def test_regeneration_is_byte_identical() -> None:
    """Two real regenerations, separated in time, must write the same bytes.

    This is the test that binds the package's byte-identical claim
    (`manuscript/06_reproducibility.md`, `docs/output_conventions.md`). It
    deliberately does *not* pin a clock: it runs the actual entry point twice
    in separate subprocesses, with a gap long enough to guarantee a
    second-boundary crossing, and compares the sha256 of every artifact under
    ``output/`` — JSON, resolved manuscript, and the six PNGs.

    The predecessor test injected a fixed ``now=`` into ``generate_variables``
    and compared the two return values. That proves a pure function is pure
    and nothing else, which is why a ``GENERATION_TIMESTAMP`` token read from
    ``datetime.now()`` sat in the rendered manuscript — falsifying the
    byte-identical claim on every single run — with the suite green. Any
    reintroduction of a wall clock into a persisted artifact turns this red.
    """
    first = run_script("z_generate_manuscript_variables.py")
    assert first.returncode == 0, first.stderr
    before = _output_digest(PROJECT_ROOT)
    assert before, "regeneration produced no artifacts to compare"

    # Cross a whole-second boundary: a %H:%M:%S stamp cannot survive this.
    time.sleep(1.1)

    second = run_script("z_generate_manuscript_variables.py")
    assert second.returncode == 0, second.stderr
    after = _output_digest(PROJECT_ROOT)

    assert sorted(after) == sorted(before), "regeneration changed the artifact set"
    drifted = sorted(name for name in before if before[name] != after[name])
    assert drifted == [], (
        f"regeneration is not byte-identical; these artifacts changed: {drifted}. "
        "Something in the generation path is reading the wall clock or another "
        "run-varying source."
    )


def test_resolved_manuscript_carries_no_wall_clock_time() -> None:
    """The persisted manuscript may carry a date, never a time-of-day.

    Complements the byte-identity test from the other side: that one would
    also go red if the clock were pinned to a constant by some future
    refactor, but this one states the actual invariant — no time-of-day is
    rendered into the tree the determinism claim covers.
    """
    result = run_script("z_generate_manuscript_variables.py")
    assert result.returncode == 0, result.stderr

    clockish = re.compile(r"\d{1,2}:\d{2}:\d{2}")
    offenders: list[str] = []
    for path in sorted((PROJECT_ROOT / "output" / "manuscript").glob("*.md")):
        offenders.extend(
            f"{path.name}: {match}" for match in clockish.findall(path.read_text())
        )
    variables_path = PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    variables = json.loads(variables_path.read_text(encoding="utf-8"))
    offenders.extend(
        f"manuscript_variables.json[{key}]: {value}"
        for key, value in sorted(variables.items())
        if clockish.search(value)
    )
    assert offenders == []
