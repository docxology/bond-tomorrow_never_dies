"""Manuscript variable generation — ``{{TOKEN}}`` hydration for CARVER.

The manuscript's prose never hand-authors numbers: every metric is injected
as a ``{{TOKEN}}`` produced by :func:`generate_variables`, which reads the
mission identity from ``manuscript/config.yaml`` and computes the concept
metrics from the real domain modules via the canonical CARVER scenario
(:mod:`tomorrow_never_dies.scenario`).

Determinism: this function reads no clock. The manuscript's date comes from
the committed ``paper.date`` field of ``manuscript/config.yaml``, and the
scenario metrics are seed-fixed, so regenerating on an unchanged tree rewrites
the same bytes. A wall-clock stamp used to be injected here as
``GENERATION_TIMESTAMP``; it made every regeneration differ and silently
falsified the package's own byte-identical claim, so it was removed rather
than pinned. The one remaining environment-derived token, ``PYTHON_VERSION``,
is a property of the interpreter, not of the moment — see the scope note in
``docs/output_conventions.md``.
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from tomorrow_never_dies import CODENAME, MANUSCRIPT_IDENTITY, __version__
from tomorrow_never_dies.gps_denial import maritime_dependency_network
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


def _manuscript_date(paper: dict[str, Any]) -> str:
    """Return the committed manuscript date as an ISO ``YYYY-MM-DD`` string.

    PyYAML resolves an unquoted ``date:`` scalar to :class:`datetime.date`
    and a quoted one to :class:`str`; both are accepted and normalised, so
    the rendered token does not depend on how the config was punctuated.
    There is deliberately no fallback to the current date — a missing
    ``paper.date`` is an error, not an invitation to read the clock.
    """
    value = paper.get("date")
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError(
        "config.yaml must define 'paper.date' (a committed ISO date, e.g. 2026-08-04)"
    )


def _format_params() -> dict[str, str]:
    """Render the *inputs* of the canonical scenario as manuscript strings.

    The experimental-setup section describes the configuration, not the
    results — but a configuration number written by hand drifts exactly as
    easily as a result does. Every value here is read straight out of
    :data:`~tomorrow_never_dies.scenario.SCENARIO_PARAMS`, so changing a
    parameter rewrites the setup section on the next regeneration.
    """
    media = SCENARIO_PARAMS["media"]
    narrative = SCENARIO_PARAMS["narrative"]
    stealth = SCENARIO_PARAMS["stealth"]
    radar = stealth["radar"]
    waveform = SCENARIO_PARAMS["waveform"]
    gps = SCENARIO_PARAMS["gps"]
    integrity = SCENARIO_PARAMS["integrity"]
    return {
        "MEDIA_REACH_PCT": f"{100.0 * float(media['media_reach']):.0f}",
        "MEDIA_PERSUASION": f"{float(media['persuasion']):.2f}",
        "MEDIA_SPREAD_RATE": f"{float(media['spread_rate']):.2f}",
        "MEDIA_STEPS": str(int(media["steps"])),
        "NARRATIVE_AGENTS": str(int(narrative["n_agents"])),
        "NARRATIVE_CONFIDENCE": f"{float(narrative['confidence']):.2f}",
        "NARRATIVE_MEDIA_WEIGHT": f"{float(narrative['media_weight']):.2f}",
        "NARRATIVE_REACH_PCT": f"{100.0 * float(narrative['media_reach']):.0f}",
        "NARRATIVE_STEPS": str(int(narrative["steps"])),
        "NARRATIVE_TARGET_SHARE_PCT": f"{100.0 * float(narrative['target_share']):.0f}",
        "STEALTH_REF_RCS_SQM": f"{float(stealth['reference_rcs_sqm']):g}",
        "STEALTH_RCS_SQM": f"{float(stealth['stealth_rcs_sqm']):g}",
        "STEALTH_PFA": f"{float(stealth['pfa']):g}",
        "STEALTH_PD_TARGET": f"{float(stealth['p_d_target']):g}",
        "RADAR_FREQUENCY_GHZ": f"{float(radar['frequency_hz']) / 1.0e9:.0f}",
        "RADAR_PULSES": str(int(radar["pulses"])),
        "WAVEFORM_PULSE_WIDTH_US": f"{float(waveform['pulse_width_s']) * 1.0e6:.0f}",
        "WAVEFORM_SAMPLE_RATE_MHZ": f"{float(waveform['sample_rate_hz']) / 1.0e6:.0f}",
        "GPS_SATELLITES": str(int(gps["n_sats"])),
        "GPS_PLANES": str(int(gps["n_planes"])),
        "GPS_INCLINATION_DEG": f"{float(gps['inclination_deg']):.0f}",
        "GPS_RECEIVER_LAT_DEG": f"{float(gps['receiver_lat_deg']):.0f}",
        "GPS_RECEIVER_LON_DEG": f"{float(gps['receiver_lon_deg']):.0f}",
        "GPS_MASK_ANGLE_DEG": f"{float(gps['mask_angle_deg']):.0f}",
        "GPS_JAMMER_POWER_W": f"{float(gps['jammer_power_w']):g}",
        "GPS_JAMMER_STANDOFF_KM": f"{float(gps['jammer_distance_m']) / 1000.0:.0f}",
        "GPS_CNO_CLEAN_DBHZ": f"{float(gps['cno_clean_dbhz']):.0f}",
        "GPS_NETWORK_SIZE": str(len(maritime_dependency_network()[1])),
        "INTEGRITY_PFA": f"{float(integrity['p_fa']):g}",
        "INTEGRITY_PMD": f"{float(integrity['p_md']):g}",
        "INTEGRITY_SIGMA_M": f"{float(integrity['sigma_m']):.0f}",
        "INTEGRITY_ALERT_LIMIT_M": f"{float(integrity['alert_limit_m']):.0f}",
    }


def _format_metrics(metrics: dict[str, float]) -> dict[str, str]:
    """Render the scenario metrics as manuscript-ready strings."""
    return {
        "MEDIA_NODES": str(SCENARIO_PARAMS["media"]["network_size"]),
        "MEDIA_BELIEF_SHARE_PCT": f"{100.0 * metrics['media_belief_share']:.1f}",
        "MEDIA_BASELINE_SHARE_PCT": f"{100.0 * metrics['media_baseline_share']:.1f}",
        "MEDIA_CAMPAIGN_LIFT": f"{metrics['media_campaign_lift']:.1f}",
        "MEDIA_ECHO_CHAMBER": f"{metrics['media_echo_chamber']:.3f}",
        "MEDIA_AMPLIFICATION": f"{metrics['media_amplification']:.2f}",
        "NARRATIVE_MEDIA_OPINION": f"{SCENARIO_PARAMS['narrative']['media_opinion']:.2f}",
        "NARRATIVE_CONSENSUS": f"{metrics['narrative_consensus']:.3f}",
        "NARRATIVE_POLARIZATION": f"{metrics['narrative_polarization']:.4f}",
        "NARRATIVE_BIMODAL_SPLIT": f"{metrics['narrative_bimodal_split']:.3f}",
        "NARRATIVE_MEDIA_CAPTURE": f"{100.0 * metrics['narrative_media_capture']:.1f}",
        "NARRATIVE_CRITICAL_REACH_PCT": f"{100.0 * metrics['narrative_critical_reach']:.1f}",
        "STEALTH_REF_RANGE_KM": f"{metrics['stealth_ref_range_km']:.1f}",
        "STEALTH_RANGE_KM": f"{metrics['stealth_range_km']:.1f}",
        "STEALTH_SWERLING1_KM": f"{metrics['stealth_swerling1_km']:.1f}",
        "STEALTH_RCS_REDUCTION_DB": f"{metrics['stealth_rcs_reduction_db']:.1f}",
        "STEALTH_RANGE_RATIO": f"{metrics['stealth_range_ratio']:.3f}",
        "STEALTH_RANGE_LOSS_PCT": f"{metrics['stealth_range_loss_pct']:.0f}",
        "WAVEFORM_BANDWIDTH_MHZ": f"{metrics['waveform_bandwidth_mhz']:.1f}",
        "WAVEFORM_RES_M": f"{metrics['waveform_resolution_m']:.1f}",
        "WAVEFORM_GAIN_DB": f"{metrics['waveform_gain_db']:.1f}",
        "WAVEFORM_PSLR_DB": f"{metrics['waveform_pslr_db']:.1f}",
        "WAVEFORM_BARKER_GAIN": f"{metrics['waveform_barker_gain']:.0f}",
        "WAVEFORM_BARKER_PSLR_DB": f"{metrics['waveform_barker_pslr_db']:.1f}",
        "WAVEFORM_BARKER_RANGE_KM": f"{metrics['waveform_barker_range_km']:.1f}",
        "WAVEFORM_BARKER_RES_M": f"{metrics['waveform_barker_resolution_m']:.0f}",
        "WAVEFORM_RANGE_KM": f"{metrics['waveform_range_km']:.1f}",
        "WAVEFORM_UNMOD_RANGE_KM": f"{metrics['waveform_unmodulated_range_km']:.1f}",
        "WAVEFORM_UNMOD_WIDTH_US": f"{metrics['waveform_unmodulated_width_us']:.2f}",
        "WAVEFORM_IMPROVEMENT_PCT": f"{metrics['waveform_improvement_pct']:.0f}",
        "GPS_VISIBLE_SATS": str(int(metrics["gps_visible_satellites"])),
        "GPS_PDOP": f"{metrics['gps_pdop']:.2f}",
        "GPS_JNR_DB": f"{metrics['gps_jnr_db']:.1f}",
        "GPS_CNO_JAMMED_DBHZ": f"{metrics['gps_cno_jammed_dbhz']:.1f}",
        "GPS_LOCK_THRESHOLD_DBHZ": (
            f"{metrics['gps_cno_tracking_threshold_dbhz']:.0f}"
        ),
        "GPS_ERROR_CLEAN_M": f"{metrics['gps_error_clean_m']:.1f}",
        "GPS_ERROR_JAMMED_M": f"{metrics['gps_error_jammed_m']:.1f}",
        "GPS_CASCADE_FRACTION": f"{metrics['gps_cascade_fraction']:.3f}",
        "GPS_CASCADE_ROUNDS": str(int(metrics["gps_cascade_rounds"])),
        "RAIM_DOF": str(int(metrics["integrity_dof"])),
        "RAIM_THRESHOLD": f"{metrics['integrity_threshold']:.1f}",
        "RAIM_HPL_M": f"{metrics['integrity_hpl_m']:.1f}",
        "RAIM_VPL_M": f"{metrics['integrity_vpl_m']:.1f}",
        "RAIM_BIAS_M": f"{SCENARIO_PARAMS['integrity']['bias_probe_m']:.0f}",
        "RAIM_PROJECTION_WORST": f"{metrics['integrity_projection_worst']:.2f}",
        "RAIM_PROJECTION_BEST": f"{metrics['integrity_projection_best']:.2f}",
        "RAIM_PD": f"{100.0 * metrics['integrity_detection_probability']:.1f}",
        "RAIM_PD_BEST": (
            f"{100.0 * metrics['integrity_detection_probability_best']:.1f}"
        ),
    }


def generate_variables(project_root: Path | str) -> dict[str, str]:
    """Generate the full ``{{TOKEN}}`` → value map for the CARVER manuscript.

    Reads no clock: ``MANUSCRIPT_DATE`` is the committed ``paper.date`` from
    ``manuscript/config.yaml``, so two regenerations of an unchanged tree
    produce identical bytes.

    Args:
        project_root: Package root containing ``manuscript/config.yaml``.

    Returns:
        Mapping of token name to resolved string value.

    Raises:
        ValueError: If ``paper``/``keywords`` are malformed, or if
            ``paper.date`` is missing — the manuscript date is a committed
            fact, and defaulting it to the clock is exactly the bug this
            function no longer has.
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

    manuscript_date = _manuscript_date(paper)

    metrics = scenario_metrics(run_carver_scenario(seed=SCENARIO_SEED))

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
        # Environment / generation. No clock is read here: MANUSCRIPT_DATE is
        # the committed config value, PYTHON_VERSION a property of the running
        # interpreter.
        "PYTHON_VERSION": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "MANUSCRIPT_DATE": manuscript_date,
    }
    variables.update(_format_params())
    variables.update(_format_metrics(metrics))
    return variables
