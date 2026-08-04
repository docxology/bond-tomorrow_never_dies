"""CARVER mission scenario — the canonical deterministic run of all concepts.

:func:`run_carver_scenario` executes one fixed, reproducible campaign across
the three domain modules: media manipulation, stealth-vessel detection, and
GPS-denial impact. It is the single source of truth for the numbers the
mission outcome, the manuscript tokens, and the figures all report, so prose
and plots can never drift apart.

The scenario is infrastructure-free (stdlib + numpy only) and fully
deterministic: fixed seed ``7``, no wall-clock, no network, no I/O.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from tomorrow_never_dies import __version__
from tomorrow_never_dies.gps_denial import (
    compute_dop,
    effective_cno_dbhz,
    jamming_to_noise_db,
    maritime_dependency_network,
    position_error_meters,
    simulate_navigation_cascade,
    walker_constellation,
)
from tomorrow_never_dies.media_manipulation import (
    build_network,
    simulate_disinformation,
)
from tomorrow_never_dies.stealth_detection import (
    RadarConfig,
    detection_range,
    detection_range_ratio,
    rcs_reduction_db,
)

__all__ = [
    "SCENARIO_SEED",
    "canonical_input_hash",
    "run_carver_scenario",
]

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
    "gps": {
        "n_sats": 24,
        "n_planes": 6,
        "mask_angle_deg": 10.0,
        "cno_clean_dbhz": 45.0,
        "jammer_power_w": 1.0,
        "jammer_gain_db": 30.0,
        "jammer_distance_m": 100_000.0,
        "jamming_strength": 0.85,
        "fail_threshold": 0.7,
        "propagation_factor": 0.5,
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
        A nested dict with ``media``, ``stealth``, and ``gps`` result blocks
        plus the ``input_hash`` of the scenario parameters.
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
    media_block = {
        "nodes": len(network),
        "final_believers": media_result.final_believers,
        "belief_share": media_result.belief_share[-1],
        "echo_chamber": media_result.echo_chamber,
        "amplification": media_result.amplification,
        "directly_exposed": media_result.directly_exposed,
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

    # --- GPS denial: geometry, jamming, and the navigation cascade. ---
    gps = params["gps"]
    constellation = walker_constellation(
        int(gps["n_sats"]), int(gps["n_planes"]), seed=seed
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
        "error_jammed_m": error_jammed,
        "cascade_fraction": cascade.total_fraction,
        "cascade_rounds": cascade.rounds,
        "cascade_failed": list(cascade.failed),
    }

    return {
        "seed": seed,
        "version": __version__,
        "media": media_block,
        "stealth": stealth_block,
        "gps": gps_block,
        "input_hash": canonical_input_hash(params),
    }


def scenario_metrics(scenario: dict[str, Any] | None = None) -> dict[str, float]:
    """Flatten the scenario into the scalar metrics used by manuscript tokens.

    Deterministic given the scenario dict; used by
    :mod:`tomorrow_never_dies.manuscript_variables`.
    """
    data = scenario if scenario is not None else run_carver_scenario()
    media = data["media"]
    stealth = data["stealth"]
    gps = data["gps"]
    return {
        "media_belief_share": float(media["belief_share"]),
        "media_echo_chamber": float(media["echo_chamber"]),
        "media_amplification": float(media["amplification"]),
        "stealth_ref_range_km": float(stealth["reference_range_m"]) / 1000.0,
        "stealth_range_km": float(stealth["stealth_range_m"]) / 1000.0,
        "stealth_rcs_reduction_db": float(stealth["rcs_reduction_db"]),
        "stealth_range_ratio": float(stealth["range_ratio"]),
        "gps_pdop": float(gps["pdop"]),
        "gps_jnr_db": float(gps["jnr_db"]),
        "gps_error_clean_m": float(gps["error_clean_m"]),
        "gps_error_jammed_m": float(gps["error_jammed_m"]),
        "gps_cascade_fraction": float(gps["cascade_fraction"]),
        "gps_cascade_rounds": float(gps["cascade_rounds"]),
    }
