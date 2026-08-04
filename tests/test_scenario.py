"""Tests for the CARVER mission scenario runner."""

from __future__ import annotations

import pytest

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
    assert set(scenario) == {"seed", "version", "media", "stealth", "gps", "input_hash"}
    media, stealth, gps = scenario["media"], scenario["stealth"], scenario["gps"]
    assert 0.0 < media["belief_share"] < 1.0
    assert stealth["reference_range_m"] > 0.0
    assert stealth["stealth_range_m"] < stealth["reference_range_m"]
    assert gps["cascade_fraction"] > 0.0


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
        "stealth_ref_range_km",
        "stealth_range_km",
        "stealth_rcs_reduction_db",
        "stealth_range_ratio",
        "gps_pdop",
        "gps_jnr_db",
        "gps_error_clean_m",
        "gps_error_jammed_m",
        "gps_cascade_fraction",
        "gps_cascade_rounds",
    ):
        assert key in metrics
        assert metrics[key] >= 0.0
    assert metrics["stealth_range_ratio"] == pytest.approx(0.316227766, rel=1e-3)
    assert metrics["gps_error_jammed_m"] > metrics["gps_error_clean_m"]
