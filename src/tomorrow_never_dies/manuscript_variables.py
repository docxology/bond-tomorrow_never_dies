"""Manuscript variable generation — ``{{TOKEN}}`` hydration for CARVER.

The manuscript's prose never hand-authors numbers: every metric is injected
as a ``{{TOKEN}}`` produced by :func:`generate_variables`, which reads the
mission identity from ``manuscript/config.yaml`` and computes the concept
metrics from the real domain modules via the canonical CARVER scenario
(:mod:`tomorrow_never_dies.scenario`).

Determinism: pass ``now=`` to pin ``GENERATION_TIMESTAMP``; the scenario
metrics themselves are seed-fixed and never depend on the clock.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from tomorrow_never_dies import CODENAME, MANUSCRIPT_IDENTITY, __version__
from tomorrow_never_dies.scenario import (
    SCENARIO_PARAMS,
    SCENARIO_SEED,
    run_carver_scenario,
    scenario_metrics,
)

__all__ = ["generate_variables", "load_mission_config"]

#: The manuscript config file this module reads (relative to project root).
CONFIG_RELPATH = Path("manuscript") / "config.yaml"


def load_mission_config(project_root: Path | str) -> dict[str, Any]:
    """Load the mission identity and metadata from ``manuscript/config.yaml``."""
    root = Path(project_root)
    config_path = root / CONFIG_RELPATH
    if not config_path.is_file():
        raise FileNotFoundError(f"mission config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"{config_path} must contain a YAML mapping")
    return config


def _format_metrics(metrics: dict[str, float]) -> dict[str, str]:
    """Render the scenario metrics as manuscript-ready strings."""
    return {
        "MEDIA_NODES": str(SCENARIO_PARAMS["media"]["network_size"]),
        "MEDIA_BELIEF_SHARE_PCT": f"{100.0 * metrics['media_belief_share']:.1f}",
        "MEDIA_ECHO_CHAMBER": f"{metrics['media_echo_chamber']:.3f}",
        "MEDIA_AMPLIFICATION": f"{metrics['media_amplification']:.2f}",
        "STEALTH_REF_RANGE_KM": f"{metrics['stealth_ref_range_km']:.1f}",
        "STEALTH_RANGE_KM": f"{metrics['stealth_range_km']:.1f}",
        "STEALTH_RCS_REDUCTION_DB": f"{metrics['stealth_rcs_reduction_db']:.1f}",
        "STEALTH_RANGE_RATIO": f"{metrics['stealth_range_ratio']:.3f}",
        "GPS_PDOP": f"{metrics['gps_pdop']:.2f}",
        "GPS_JNR_DB": f"{metrics['gps_jnr_db']:.1f}",
        "GPS_ERROR_CLEAN_M": f"{metrics['gps_error_clean_m']:.1f}",
        "GPS_ERROR_JAMMED_M": f"{metrics['gps_error_jammed_m']:.1f}",
        "GPS_CASCADE_FRACTION": f"{metrics['gps_cascade_fraction']:.3f}",
        "GPS_CASCADE_ROUNDS": str(int(metrics["gps_cascade_rounds"])),
    }


def generate_variables(
    project_root: Path | str, *, now: datetime | None = None
) -> dict[str, str]:
    """Generate the full ``{{TOKEN}}`` → value map for the CARVER manuscript.

    Args:
        project_root: Package root containing ``manuscript/config.yaml``.
        now: Clock override for ``GENERATION_TIMESTAMP`` (determinism in
            tests); defaults to the current UTC time.

    Returns:
        Mapping of token name to resolved string value.
    """
    config = load_mission_config(project_root)
    paper = config.get("paper", {})
    authors = config.get("authors", [])
    first_author = authors[0].get("name", "") if authors else ""
    keywords = config.get("keywords", [])
    if not isinstance(paper, dict) or not isinstance(keywords, list):
        raise ValueError(
            "config.yaml must define 'paper' (mapping) and 'keywords' (list)"
        )

    metrics = scenario_metrics(run_carver_scenario(seed=SCENARIO_SEED))
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")

    variables: dict[str, str] = {
        # Identity (config-driven, never hand-authored in prose).
        "CARVER_IDENTITY": str(paper.get("title", MANUSCRIPT_IDENTITY)),
        "CARVER_SUBTITLE": str(paper.get("subtitle", "")),
        "CARVER_CODENAME": CODENAME,
        "CARVER_VERSION": str(paper.get("version", __version__)),
        "CARVER_AUTHOR": first_author,
        "CARVER_KEYWORDS": ", ".join(str(k) for k in keywords),
        "CARVER_OBJECTIVES": str(len(SCENARIO_PARAMS)),
        "CARVER_SEED": str(SCENARIO_SEED),
        # Environment / generation.
        "PYTHON_VERSION": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "GENERATION_TIMESTAMP": stamp,
    }
    variables.update(_format_metrics(metrics))
    return variables
