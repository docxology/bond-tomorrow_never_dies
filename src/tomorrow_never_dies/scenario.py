"""CARVER mission scenario — the canonical deterministic run of all concepts.

:func:`run_carver_scenario` executes one fixed, reproducible campaign across
the six domain analyses: disinformation propagation and bounded-confidence
narrative control (media manipulation), stealth-vessel detection and
pulse-compression waveforms (radar), and GPS-denial and RAIM integrity
(navigation). It is the single source of truth for the numbers the mission
outcome, the manuscript tokens, and the figures all report, so prose and
plots can never drift apart.

The scenario is infrastructure-free (stdlib + numpy only) and fully
deterministic: fixed seed ``7``, no wall-clock, no network, no I/O.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np

from tomorrow_never_dies import __version__
from tomorrow_never_dies.gnss_integrity import (
    detection_probability,
    integrity_availability,
    parity_projection_factors,
)
from tomorrow_never_dies.gps_denial import (
    CNO_TRACKING_THRESHOLD_DBHZ,
    compute_dop,
    effective_cno_dbhz,
    geometry_matrix,
    jamming_to_noise_db,
    maintains_lock,
    maritime_dependency_network,
    position_error_meters,
    simulate_navigation_cascade,
    walker_constellation,
)
from tomorrow_never_dies.media_manipulation import (
    build_network,
    simulate_disinformation,
)
from tomorrow_never_dies.narrative_control import (
    critical_media_reach,
    simulate_opinions,
)
from tomorrow_never_dies.radar_waveform import (
    Waveform,
    peak_sidelobe_ratio,
    processing_gain,
    range_resolution,
    waveform_bandwidth,
    waveform_detection_range,
)
from tomorrow_never_dies.stealth_detection import (
    RadarConfig,
    detection_range,
    detection_range_ratio,
    rcs_reduction_db,
)

__all__ = [
    "SCENARIO_BLOCKS",
    "SCENARIO_PARAMS",
    "SCENARIO_SEED",
    "canonical_input_hash",
    "run_carver_scenario",
    "scenario_metrics",
]

#: The six result blocks :func:`run_carver_scenario` always returns, in
#: manuscript order. Pinned by ``tests/test_scenario.py``.
SCENARIO_BLOCKS = (
    "media",
    "narrative",
    "stealth",
    "waveform",
    "gps",
    "integrity",
)

#: The fixed seed every CARVER scenario uses (determinism guarantee).
SCENARIO_SEED = 7

#: Canonical scenario parameters — changing any value changes the input hash.
SCENARIO_PARAMS: dict[str, Any] = {
    "media": {
        "network_size": 120,
        "topology": "small_world",
        "k": 4,
        "rewire_prob": 0.1,
        "media_reach": 0.3,
        "persuasion": 0.12,
        "spread_rate": 0.05,
        "steps": 15,
        "campaign_delay": 2,
        "initial_believers": 1,
    },
    "narrative": {
        "n_agents": 120,
        "confidence": 0.10,
        "media_opinion": 0.85,
        "media_weight": 0.10,
        "media_reach": 0.4,
        "steps": 20,
        "target_share": 0.5,
    },
    "stealth": {
        "pfa": 1e-6,
        "p_d_target": 0.9,
        "reference_rcs_sqm": 1.0,
        "stealth_rcs_sqm": 0.01,
        "max_range_m": 2.0e6,
        "radar": {
            "peak_power_w": 1.0e6,
            "gain_db": 40.0,
            "frequency_hz": 10.0e9,
            "bandwidth_hz": 1.0e6,
            "noise_figure_db": 3.0,
            "losses_db": 6.0,
            "pulses": 4,
        },
    },
    "waveform": {
        "kind": "lfm",
        "pulse_width_s": 50.0e-6,
        "bandwidth_hz": 10.0e6,
        "sample_rate_hz": 40.0e6,
        "pfa": 1e-6,
        "p_d_target": 0.9,
        "max_range_m": 2.0e6,
    },
    "gps": {
        "n_sats": 24,
        "n_planes": 6,
        "phasing": 1,
        "inclination_deg": 55.0,
        "receiver_lat_deg": 15.0,
        "receiver_lon_deg": 115.0,
        "mask_angle_deg": 10.0,
        "cno_clean_dbhz": 45.0,
        "jammer_power_w": 1.0,
        "jammer_gain_db": 30.0,
        "jammer_distance_m": 100_000.0,
        "jamming_strength": 0.85,
        "fail_threshold": 0.7,
        "propagation_factor": 0.5,
    },
    "integrity": {
        "p_fa": 1e-5,
        "p_md": 1e-3,
        "sigma_m": 3.0,
        "alert_limit_m": 556.0,
        "bias_probe_m": 20.0,
    },
}


def canonical_input_hash(params: dict[str, Any] | None = None) -> str:
    """Stable sha256 fingerprint of the scenario parameters.

    The hash is computed over a key-sorted, compact JSON serialization so it
    is byte-deterministic across runs and platforms.
    """
    payload = params if params is not None else SCENARIO_PARAMS
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _radar_config(params: dict[str, Any]) -> RadarConfig:
    radar = params["stealth"]["radar"]
    return RadarConfig(
        peak_power_w=float(radar["peak_power_w"]),
        gain_db=float(radar["gain_db"]),
        frequency_hz=float(radar["frequency_hz"]),
        bandwidth_hz=float(radar["bandwidth_hz"]),
        noise_figure_db=float(radar["noise_figure_db"]),
        losses_db=float(radar["losses_db"]),
        pulses=int(radar["pulses"]),
    )


def run_carver_scenario(*, seed: int = SCENARIO_SEED) -> dict[str, Any]:
    """Run the full CARVER scenario and return the computed results.

    Returns:
        A nested dict with the six result blocks named by
        :data:`SCENARIO_BLOCKS` — ``media``, ``narrative``, ``stealth``,
        ``waveform``, ``gps``, ``integrity`` — plus ``seed``, ``version``,
        and the ``input_hash`` of the scenario parameters.
    """
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    params = SCENARIO_PARAMS

    # --- Media manipulation: two-channel disinformation on a small world. ---
    media = params["media"]
    network = build_network(
        int(media["network_size"]),
        seed,
        topology=str(media["topology"]),
        k=int(media["k"]),
        rewire_prob=float(media["rewire_prob"]),
    )
    media_result = simulate_disinformation(
        network,
        media_reach=float(media["media_reach"]),
        persuasion=float(media["persuasion"]),
        seed=seed,
        steps=int(media["steps"]),
        initial_believers=int(media["initial_believers"]),
        spread_rate=float(media["spread_rate"]),
        campaign_delay=int(media["campaign_delay"]),
    )
    # The counterfactual: identical network, identical seed, no broadcast.
    # Every "the campaign did X" claim is measured against this, never eyeballed.
    baseline_result = simulate_disinformation(
        network,
        media_reach=0.0,
        persuasion=float(media["persuasion"]),
        seed=seed,
        steps=int(media["steps"]),
        initial_believers=int(media["initial_believers"]),
        spread_rate=float(media["spread_rate"]),
        campaign_delay=int(media["campaign_delay"]),
    )
    baseline_share = baseline_result.belief_share[-1]
    media_block = {
        "nodes": len(network),
        "final_believers": media_result.final_believers,
        "belief_share": media_result.belief_share[-1],
        "baseline_belief_share": baseline_share,
        "campaign_lift": (
            media_result.belief_share[-1] / baseline_share
            if baseline_share > 0.0
            else float("inf")
        ),
        "echo_chamber": media_result.echo_chamber,
        "amplification": media_result.amplification,
        "directly_exposed": media_result.directly_exposed,
    }

    # --- Narrative control: bounded-confidence opinion dynamics + tipping. ---
    narrative = params["narrative"]
    opinion_result = simulate_opinions(
        int(narrative["n_agents"]),
        seed,
        confidence=float(narrative["confidence"]),
        media_opinion=float(narrative["media_opinion"]),
        media_weight=float(narrative["media_weight"]),
        media_reach=float(narrative["media_reach"]),
        steps=int(narrative["steps"]),
    )
    tipping_reach = critical_media_reach(
        network,
        target_share=float(narrative["target_share"]),
        seed=seed,
        steps=int(media["steps"]),
        persuasion=float(media["persuasion"]),
        spread_rate=float(media["spread_rate"]),
        campaign_delay=int(media["campaign_delay"]),
    )
    narrative_block = {
        "n_agents": int(narrative["n_agents"]),
        "media_opinion": float(narrative["media_opinion"]),
        "confidence": float(narrative["confidence"]),
        "consensus": opinion_result.consensus,
        "polarization_variance": opinion_result.variance,
        "bimodal_split": opinion_result.bimodal_split,
        "media_capture": opinion_result.media_capture,
        "critical_reach": tipping_reach,
    }

    # --- Stealth detection: detection range of a reference vs stealth hull. ---
    stealth = params["stealth"]
    radar = _radar_config(params)
    ref_range = detection_range(
        float(stealth["reference_rcs_sqm"]),
        p_fa=float(stealth["pfa"]),
        p_d_target=float(stealth["p_d_target"]),
        config=radar,
        max_range_m=float(stealth["max_range_m"]),
    )
    stealth_range = detection_range(
        float(stealth["stealth_rcs_sqm"]),
        p_fa=float(stealth["pfa"]),
        p_d_target=float(stealth["p_d_target"]),
        config=radar,
        max_range_m=float(stealth["max_range_m"]),
    )
    stealth_block = {
        "reference_rcs_sqm": float(stealth["reference_rcs_sqm"]),
        "stealth_rcs_sqm": float(stealth["stealth_rcs_sqm"]),
        "reference_range_m": ref_range,
        "stealth_range_m": stealth_range,
        "rcs_reduction_db": rcs_reduction_db(
            float(stealth["reference_rcs_sqm"]), float(stealth["stealth_rcs_sqm"])
        ),
        "range_ratio": detection_range_ratio(
            float(stealth["reference_rcs_sqm"]), float(stealth["stealth_rcs_sqm"])
        ),
        "p_fa": float(stealth["pfa"]),
        "p_d_target": float(stealth["p_d_target"]),
    }

    # --- Pulse compression: the radar's counter to stealth. ---
    wfm = params["waveform"]
    chirp = Waveform(
        kind=str(wfm["kind"]),
        pulse_width_s=float(wfm["pulse_width_s"]),
        bandwidth_hz=float(wfm["bandwidth_hz"]),
        sample_rate_hz=float(wfm["sample_rate_hz"]),
    )
    # The compression baseline is an unmodulated pulse of the SAME RANGE
    # RESOLUTION, i.e. duration 1/B — not the same duration. Matched filtering
    # makes detection range depend on pulse energy alone, so an unmodulated
    # pulse of equal *duration* has equal range and would show 0% improvement;
    # what pulse compression actually buys is that resolution stops costing
    # range. Its bandwidth is therefore B, and so is its noise bandwidth.
    plain_width_s = 1.0 / float(wfm["bandwidth_hz"])
    plain = Waveform(
        kind="unmodulated",
        pulse_width_s=plain_width_s,
        bandwidth_hz=float(wfm["bandwidth_hz"]),
        sample_rate_hz=float(wfm["sample_rate_hz"]),
    )
    barker = Waveform(
        kind="barker13",
        pulse_width_s=float(wfm["pulse_width_s"]),
        bandwidth_hz=float(wfm["bandwidth_hz"]),
        sample_rate_hz=float(wfm["sample_rate_hz"]),
    )
    wfm_gain = processing_gain(chirp)
    lfm_range = waveform_detection_range(
        float(stealth["stealth_rcs_sqm"]),
        chirp,
        config=radar,
        p_fa=float(wfm["pfa"]),
        p_d_target=float(wfm["p_d_target"]),
        max_range_m=float(wfm["max_range_m"]),
    )
    unmodulated_range = waveform_detection_range(
        float(stealth["stealth_rcs_sqm"]),
        plain,
        config=radar,
        p_fa=float(wfm["pfa"]),
        p_d_target=float(wfm["p_d_target"]),
        max_range_m=float(wfm["max_range_m"]),
    )
    waveform_block = {
        "kind": str(wfm["kind"]),
        "bandwidth_mhz": waveform_bandwidth(chirp) / 1.0e6,
        "range_resolution_m": range_resolution(chirp),
        "processing_gain": wfm_gain,
        "gain_db": float(10.0 * np.log10(wfm_gain)) if wfm_gain > 1.0 else 0.0,
        "pslr_db": peak_sidelobe_ratio(chirp),
        "barker_gain": processing_gain(barker),
        "barker_pslr_db": peak_sidelobe_ratio(barker),
        "detection_range_m": lfm_range,
        "unmodulated_range_m": unmodulated_range,
        "unmodulated_pulse_width_s": plain_width_s,
        "improvement_pct": (lfm_range / unmodulated_range - 1.0) * 100.0,
    }

    # --- GPS denial: geometry, jamming, and the navigation cascade. ---
    gps = params["gps"]
    constellation = walker_constellation(
        int(gps["n_sats"]),
        int(gps["n_planes"]),
        phasing=int(gps["phasing"]),
        inclination_deg=float(gps["inclination_deg"]),
        receiver_lat_deg=float(gps["receiver_lat_deg"]),
        receiver_lon_deg=float(gps["receiver_lon_deg"]),
    )
    visible = constellation.visible(mask_angle_deg=float(gps["mask_angle_deg"]))
    dop = compute_dop(visible)
    jnr_db = jamming_to_noise_db(
        float(gps["jammer_power_w"]),
        float(gps["jammer_distance_m"]),
        jammer_gain_db=float(gps["jammer_gain_db"]),
    )
    cno_clean = float(gps["cno_clean_dbhz"])
    cno_jammed = effective_cno_dbhz(cno_clean, jnr_db)
    error_clean = position_error_meters(dop.pdop, cno_clean)
    error_jammed = position_error_meters(dop.pdop, cno_jammed)
    dependencies, gps_weights = maritime_dependency_network()
    cascade = simulate_navigation_cascade(
        dependencies,
        gps_weights,
        jamming_strength=float(gps["jamming_strength"]),
        fail_threshold=float(gps["fail_threshold"]),
        propagation_factor=float(gps["propagation_factor"]),
    )
    gps_block = {
        "visible_satellites": len(visible),
        "gdop": dop.gdop,
        "pdop": dop.pdop,
        "hdop": dop.hdop,
        "vdop": dop.vdop,
        "jnr_db": jnr_db,
        "cno_clean_dbhz": cno_clean,
        "cno_jammed_dbhz": cno_jammed,
        "error_clean_m": error_clean,
        # NOTE: physically meaningful only if `tracks_under_jamming` is true;
        # otherwise it is the UERE formula extrapolated below carrier lock.
        "error_jammed_m": error_jammed,
        "cno_tracking_threshold_dbhz": CNO_TRACKING_THRESHOLD_DBHZ,
        "tracks_under_jamming": maintains_lock(cno_jammed),
        "cascade_fraction": cascade.total_fraction,
        "cascade_rounds": cascade.rounds,
        "cascade_failed": list(cascade.failed),
    }

    # --- GNSS integrity: RAIM detection and protection levels. ---
    integrity = params["integrity"]
    geometry = geometry_matrix(visible)
    # Availability comes from the exported predicate, never re-derived inline:
    # one implementation of the published "integrity is available" claim.
    available, levels = integrity_availability(
        geometry,
        p_fa=float(integrity["p_fa"]),
        p_md=float(integrity["p_md"]),
        sigma=float(integrity["sigma_m"]),
        alert_limit_m=float(integrity["alert_limit_m"]),
    )
    bias_probe = float(integrity["bias_probe_m"])
    # Detection probability is satellite-dependent: the parity projection sees
    # only P_ii of a fault on satellite i. Report the worst-placed satellite
    # (the conservative integrity figure, matching the worst-slope convention
    # protection_levels already uses) alongside the best-placed one.
    projection_factors = parity_projection_factors(geometry)
    worst_factor = min(projection_factors)
    best_factor = max(projection_factors)
    pd_worst = detection_probability(
        bias_probe,
        dof=levels.dof,
        p_fa=float(integrity["p_fa"]),
        projection_factor=worst_factor,
        sigma=float(integrity["sigma_m"]),
    )
    pd_best = detection_probability(
        bias_probe,
        dof=levels.dof,
        p_fa=float(integrity["p_fa"]),
        projection_factor=best_factor,
        sigma=float(integrity["sigma_m"]),
    )
    integrity_block = {
        "visible_satellites": len(visible),
        "dof": levels.dof,
        "threshold": levels.threshold,
        "hpl_m": levels.hpl,
        "vpl_m": levels.vpl,
        "bias_probe_m": bias_probe,
        "projection_factor_worst": worst_factor,
        "projection_factor_best": best_factor,
        "detection_probability": pd_worst,
        "detection_probability_best": pd_best,
        "alert_limit_m": float(integrity["alert_limit_m"]),
        "available": available,
    }

    return {
        "seed": seed,
        "version": __version__,
        "media": media_block,
        "narrative": narrative_block,
        "stealth": stealth_block,
        "waveform": waveform_block,
        "gps": gps_block,
        "integrity": integrity_block,
        "input_hash": canonical_input_hash(params),
    }


def scenario_metrics(scenario: dict[str, Any] | None = None) -> dict[str, float]:
    """Flatten the scenario into the scalar metrics used by manuscript tokens.

    Deterministic given the scenario dict; used by
    :mod:`tomorrow_never_dies.manuscript_variables`.
    """
    data = scenario if scenario is not None else run_carver_scenario()
    media = data["media"]
    narrative = data["narrative"]
    stealth = data["stealth"]
    waveform = data["waveform"]
    gps = data["gps"]
    integrity = data["integrity"]
    return {
        "media_belief_share": float(media["belief_share"]),
        "media_baseline_share": float(media["baseline_belief_share"]),
        "media_campaign_lift": float(media["campaign_lift"]),
        "media_echo_chamber": float(media["echo_chamber"]),
        "media_amplification": float(media["amplification"]),
        "narrative_consensus": float(narrative["consensus"]),
        "narrative_polarization": float(narrative["polarization_variance"]),
        "narrative_bimodal_split": float(narrative["bimodal_split"]),
        "narrative_media_capture": float(narrative["media_capture"]),
        "narrative_critical_reach": float(narrative["critical_reach"]),
        "stealth_ref_range_km": float(stealth["reference_range_m"]) / 1000.0,
        "stealth_range_km": float(stealth["stealth_range_m"]) / 1000.0,
        "stealth_rcs_reduction_db": float(stealth["rcs_reduction_db"]),
        "stealth_range_ratio": float(stealth["range_ratio"]),
        "stealth_range_loss_pct": (1.0 - float(stealth["range_ratio"])) * 100.0,
        "waveform_bandwidth_mhz": float(waveform["bandwidth_mhz"]),
        "waveform_resolution_m": float(waveform["range_resolution_m"]),
        "waveform_gain_db": float(waveform["gain_db"]),
        "waveform_pslr_db": float(waveform["pslr_db"]),
        "waveform_barker_gain": float(waveform["barker_gain"]),
        "waveform_barker_pslr_db": float(waveform["barker_pslr_db"]),
        "waveform_range_km": float(waveform["detection_range_m"]) / 1000.0,
        "waveform_unmodulated_range_km": (
            float(waveform["unmodulated_range_m"]) / 1000.0
        ),
        "waveform_unmodulated_width_us": (
            float(waveform["unmodulated_pulse_width_s"]) * 1.0e6
        ),
        "waveform_improvement_pct": float(waveform["improvement_pct"]),
        "gps_visible_satellites": float(gps["visible_satellites"]),
        "gps_pdop": float(gps["pdop"]),
        "gps_jnr_db": float(gps["jnr_db"]),
        "gps_cno_jammed_dbhz": float(gps["cno_jammed_dbhz"]),
        "gps_cno_tracking_threshold_dbhz": float(gps["cno_tracking_threshold_dbhz"]),
        "gps_error_clean_m": float(gps["error_clean_m"]),
        "gps_error_jammed_m": float(gps["error_jammed_m"]),
        "gps_cascade_fraction": float(gps["cascade_fraction"]),
        "gps_cascade_rounds": float(gps["cascade_rounds"]),
        "integrity_dof": float(integrity["dof"]),
        "integrity_threshold": float(integrity["threshold"]),
        "integrity_hpl_m": float(integrity["hpl_m"]),
        "integrity_vpl_m": float(integrity["vpl_m"]),
        "integrity_projection_worst": float(integrity["projection_factor_worst"]),
        "integrity_projection_best": float(integrity["projection_factor_best"]),
        "integrity_detection_probability": float(integrity["detection_probability"]),
        "integrity_detection_probability_best": float(
            integrity["detection_probability_best"]
        ),
    }
