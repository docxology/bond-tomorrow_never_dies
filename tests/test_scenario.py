"""Tests for the CARVER mission scenario runner."""

from __future__ import annotations

import numpy as np
import pytest

from tomorrow_never_dies.gnss_integrity import integrity_availability
from tomorrow_never_dies.gps_denial import geometry_matrix, walker_constellation
from tomorrow_never_dies.scenario import (
    SCENARIO_PARAMS,
    SCENARIO_SEED,
    canonical_input_hash,
    run_carver_scenario,
    scenario_metrics,
)


def test_scenario_keys_and_values() -> None:
    scenario = run_carver_scenario()
    assert scenario["seed"] == SCENARIO_SEED
    assert set(scenario) == {
        "seed",
        "version",
        "media",
        "narrative",
        "stealth",
        "waveform",
        "gps",
        "integrity",
        "input_hash",
    }
    media, narrative = scenario["media"], scenario["narrative"]
    stealth, waveform = scenario["stealth"], scenario["waveform"]
    gps, integrity = scenario["gps"], scenario["integrity"]
    assert 0.0 < media["belief_share"] < 1.0
    assert 0.0 < narrative["media_capture"] < 1.0
    assert 0.0 < narrative["bimodal_split"] <= 1.0
    assert stealth["reference_range_m"] > 0.0
    assert stealth["stealth_range_m"] < stealth["reference_range_m"]
    assert waveform["detection_range_m"] > waveform["unmodulated_range_m"]
    assert gps["cascade_fraction"] > 0.0
    assert integrity["available"] is True
    assert 0.0 < integrity["detection_probability"] < 1.0
    # The reported figure is the worst-placed satellite, so it is never the
    # flattering one; both are bounded by the projection factors they use.
    assert integrity["detection_probability"] <= integrity["detection_probability_best"]
    assert (
        0.0
        < integrity["projection_factor_worst"]
        <= integrity["projection_factor_best"]
        < 1.0
    )


def test_scenario_availability_matches_the_exported_predicate() -> None:
    """``available`` must come from ``integrity_availability``, not a copy.

    The scenario used to recompute ``hpl <= alert_limit`` inline, so two
    implementations of one published claim could drift. This pins them
    together, including at a limit that flips the answer.
    """
    integrity = run_carver_scenario()["integrity"]
    geometry = geometry_matrix(
        walker_constellation(
            int(SCENARIO_PARAMS["gps"]["n_sats"]),
            int(SCENARIO_PARAMS["gps"]["n_planes"]),
            phasing=int(SCENARIO_PARAMS["gps"]["phasing"]),
            inclination_deg=float(SCENARIO_PARAMS["gps"]["inclination_deg"]),
            receiver_lat_deg=float(SCENARIO_PARAMS["gps"]["receiver_lat_deg"]),
            receiver_lon_deg=float(SCENARIO_PARAMS["gps"]["receiver_lon_deg"]),
        ).visible(float(SCENARIO_PARAMS["gps"]["mask_angle_deg"]))
    )
    params = SCENARIO_PARAMS["integrity"]
    available, levels = integrity_availability(
        geometry,
        p_fa=float(params["p_fa"]),
        p_md=float(params["p_md"]),
        sigma=float(params["sigma_m"]),
        alert_limit_m=float(params["alert_limit_m"]),
    )
    assert available is integrity["available"]
    assert levels.hpl == pytest.approx(integrity["hpl_m"])
    blocked, _ = integrity_availability(
        geometry,
        p_fa=float(params["p_fa"]),
        p_md=float(params["p_md"]),
        sigma=float(params["sigma_m"]),
        alert_limit_m=levels.hpl / 2.0,
    )
    assert blocked is False  # the predicate can say no


def test_scenario_deterministic() -> None:
    assert run_carver_scenario() == run_carver_scenario()


def test_scenario_seed_changes_media() -> None:
    a = run_carver_scenario(seed=7)
    b = run_carver_scenario(seed=8)
    assert a["media"]["belief_share"] != b["media"]["belief_share"]


def test_scenario_invalid_seed() -> None:
    with pytest.raises(ValueError):
        run_carver_scenario(seed=-1)


def test_input_hash_stable() -> None:
    assert canonical_input_hash() == canonical_input_hash(SCENARIO_PARAMS)
    assert len(canonical_input_hash()) == 64
    changed = dict(SCENARIO_PARAMS)
    changed["media"] = dict(changed["media"])
    changed["media"]["steps"] = 14
    assert canonical_input_hash(changed) != canonical_input_hash()


def test_scenario_metrics() -> None:
    metrics = scenario_metrics(run_carver_scenario())
    for key in (
        "media_belief_share",
        "media_echo_chamber",
        "media_amplification",
        "narrative_consensus",
        "narrative_polarization",
        "narrative_bimodal_split",
        "narrative_media_capture",
        "narrative_critical_reach",
        "stealth_ref_range_km",
        "stealth_range_km",
        "stealth_rcs_reduction_db",
        "stealth_range_ratio",
        "waveform_bandwidth_mhz",
        "waveform_resolution_m",
        "waveform_gain_db",
        "waveform_pslr_db",
        "waveform_range_km",
        "waveform_improvement_pct",
        "gps_pdop",
        "gps_jnr_db",
        "gps_error_clean_m",
        "gps_error_jammed_m",
        "gps_cascade_fraction",
        "gps_cascade_rounds",
        "gps_visible_satellites",
        "gps_cno_jammed_dbhz",
        "gps_cno_tracking_threshold_dbhz",
        "waveform_unmodulated_range_km",
        "waveform_unmodulated_width_us",
        "integrity_dof",
        "integrity_threshold",
        "integrity_hpl_m",
        "integrity_vpl_m",
        "integrity_projection_worst",
        "integrity_projection_best",
        "integrity_detection_probability",
        "integrity_detection_probability_best",
    ):
        assert key in metrics
        assert np.isfinite(metrics[key])
        if key != "waveform_pslr_db":
            assert metrics[key] >= 0.0
    # PSLR is a (negative) dB sidelobe level, distinct from the non-negative set.
    assert metrics["waveform_pslr_db"] < 0.0
    assert metrics["stealth_range_ratio"] == pytest.approx(0.316227766, rel=1e-3)
    assert metrics["gps_error_jammed_m"] > metrics["gps_error_clean_m"]
    # Pulse compression extends the stealth-hull detection range.
    assert metrics["waveform_range_km"] > metrics["stealth_range_km"]
    # The improvement token is the ratio against the equal-resolution
    # unmodulated pulse, not against the surveillance pulse: bind it to the
    # baseline it is quoted against so the two cannot be conflated again.
    assert metrics["waveform_improvement_pct"] == pytest.approx(
        (metrics["waveform_range_km"] / metrics["waveform_unmodulated_range_km"] - 1.0)
        * 100.0
    )
    assert metrics["waveform_unmodulated_width_us"] == pytest.approx(
        1.0e6 / float(SCENARIO_PARAMS["waveform"]["bandwidth_hz"])
    )
    # A realistic single-epoch sky, not the whole constellation.
    assert 8 <= metrics["gps_visible_satellites"] <= 12
    # The canonical jamming case is BELOW carrier lock: the reported jammed
    # position error is an extrapolation, and the scenario says so.
    assert metrics["gps_cno_jammed_dbhz"] < metrics["gps_cno_tracking_threshold_dbhz"]
    assert run_carver_scenario()["gps"]["tracks_under_jamming"] is False
