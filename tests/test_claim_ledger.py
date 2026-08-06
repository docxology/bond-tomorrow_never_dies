"""Bind ``data/claim_ledger.yaml`` to live engine calls (V1).

Every numeric row in the evidence ledger must equal a value re-derived from a
live call to the cited module; every ``range`` row must hold for the canonical
scenario. Before this file existed, nothing read the ledger and two of its
values had drifted from the code they cite without a gate going red. Editing a
ledger ``value:`` so it no longer matches the engine must fail this suite.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tomorrow_never_dies.gnss_integrity import protection_levels
from tomorrow_never_dies.gps_denial import geometry_matrix, walker_constellation
from tomorrow_never_dies.radar_waveform import (
    Waveform,
    peak_sidelobe_ratio,
    processing_gain,
)
from tomorrow_never_dies.scenario import SCENARIO_PARAMS, run_carver_scenario
from tomorrow_never_dies.stealth_detection import (
    detection_probability,
    detection_range_ratio,
    rcs_reduction_db,
)

LEDGER = Path(__file__).resolve().parent.parent / "data" / "claim_ledger.yaml"

REQUIRED_CLAIM_IDS = {
    "stealth-rcs-reduction-db",
    "detection-range-fourth-root-ratio",
    "marcum-floor-at-zero-snr",
    "jammer-range-standoff",
    "march-cascade-fraction-bound",
    "media-belief-share-bounds",
    "lfm-time-bandwidth-gain",
    "barker-uniform-sidelobe-floor",
    "raim-hpl-scenario",
    "opinion-bimodal-split",
}


def _ledger() -> dict[str, dict]:
    import yaml

    data = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    return {row["claim_id"]: row for row in data["claims"]}


def test_all_expected_rows_are_present() -> None:
    """A row can neither be dropped silently nor left unbound."""
    assert set(_ledger()) == REQUIRED_CLAIM_IDS


def test_stealth_rcs_reduction_db() -> None:
    assert _ledger()["stealth-rcs-reduction-db"]["value"] == pytest.approx(
        rcs_reduction_db(1.0, 0.01), rel=1e-6
    )


def test_detection_range_fourth_root_ratio() -> None:
    assert _ledger()["detection-range-fourth-root-ratio"]["value"] == pytest.approx(
        detection_range_ratio(1.0, 0.01), rel=1e-6
    )


def test_marcum_floor_at_zero_snr() -> None:
    """P_d(snr=0) equals P_fa — the general property, bound at p_fa = 1e-6."""
    declared = _ledger()["marcum-floor-at-zero-snr"]
    p_fa = 1e-6
    measured = detection_probability(0.0, p_fa=p_fa, pulses=1)
    assert declared["value"] == pytest.approx(p_fa, rel=1e-3)
    assert measured == pytest.approx(p_fa, rel=1e-3)


def test_jammer_range_standoff() -> None:
    assert _ledger()["jammer-range-standoff"]["value"] == pytest.approx(
        SCENARIO_PARAMS["gps"]["jammer_distance_m"]
    )


def test_march_cascade_fraction_bound() -> None:
    assert _ledger()["march-cascade-fraction-bound"]["value"] == pytest.approx(
        run_carver_scenario()["gps"]["cascade_fraction"], rel=1e-4
    )


def test_media_belief_share_bounds() -> None:
    value = _ledger()["media-belief-share-bounds"]["value"]
    share = run_carver_scenario()["media"]["belief_share"]
    assert "0.0 < belief_share < 1.0" in value
    assert 0.0 < share < 1.0


def test_lfm_time_bandwidth_gain() -> None:
    lfm = Waveform(
        kind="lfm",
        pulse_width_s=50.0e-6,
        bandwidth_hz=10.0e6,
        sample_rate_hz=40.0e6,
    )
    assert _ledger()["lfm-time-bandwidth-gain"]["value"] == pytest.approx(
        processing_gain(lfm), rel=1e-6
    )


def test_barker_uniform_sidelobe_floor() -> None:
    """The declared floor is the sampled value the code returns, not the ideal."""
    barker = Waveform(
        kind="barker13",
        pulse_width_s=50.0e-6,
        bandwidth_hz=10.0e6,
        sample_rate_hz=40.0e6,
    )
    assert _ledger()["barker-uniform-sidelobe-floor"]["value"] == pytest.approx(
        peak_sidelobe_ratio(barker), rel=1e-4
    )


def test_raim_hpl_scenario() -> None:
    """HPL must match protection_levels on the canonical visible geometry."""
    declared = _ledger()["raim-hpl-scenario"]["value"]
    integrity = run_carver_scenario()["integrity"]
    params = SCENARIO_PARAMS["integrity"]
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
    levels = protection_levels(
        geometry,
        p_fa=float(params["p_fa"]),
        p_md=float(params["p_md"]),
        sigma=float(params["sigma_m"]),
    )
    assert levels.hpl == pytest.approx(integrity["hpl_m"], rel=1e-9)
    assert declared == pytest.approx(integrity["hpl_m"], rel=1e-3)


def test_opinion_bimodal_split() -> None:
    value = _ledger()["opinion-bimodal-split"]["value"]
    split = run_carver_scenario()["narrative"]["bimodal_split"]
    assert "0.0 < bimodal_split < 1.0" in value
    assert 0.0 < split < 1.0
