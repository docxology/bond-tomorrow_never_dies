"""CARVER figure generation — deterministic publication-ready visualizations.

Three figures, one per concept, all drawn from the real domain modules with
fixed scenario parameters (no RNG beyond the seeded simulations):

* ``fig_disinformation`` — believing fraction over time, media campaign vs
  no-media baseline (media manipulation).
* ``fig_stealth_detection`` — detection probability vs range for a reference
  and a low-RCS (stealth) target (stealth detection).
* ``fig_gps_denial`` — position error vs jammer standoff distance, with the
  clean-sky error reference line (GPS denial).

The matplotlib backend is pinned to ``Agg`` so rendering is headless and
byte-deterministic given the same input data.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

import matplotlib

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from tomorrow_never_dies.gps_denial import (
    effective_cno_dbhz,
    jamming_to_noise_db,
    position_error_meters,
)
from tomorrow_never_dies.media_manipulation import (
    build_network,
    simulate_disinformation,
)
from tomorrow_never_dies.scenario import (
    SCENARIO_PARAMS,
    SCENARIO_SEED,
    run_carver_scenario,
)
from tomorrow_never_dies.stealth_detection import (
    RadarConfig,
    detection_probability,
    snr_at_range,
)

__all__ = ["FIGURES_DIR", "render_figures"]

#: Where figures are written (relative to the project root).
FIGURES_DIR = Path("output") / "figures"

_DPI = 150


def _save(figure: plt.Figure, path: Path) -> None:
    figure.savefig(path, dpi=_DPI, bbox_inches="tight")
    plt.close(figure)


def fig_disinformation(project_root: Path | str) -> Path:
    """Believing fraction over time: media campaign vs no-media baseline."""
    media = SCENARIO_PARAMS["media"]
    network = build_network(
        int(media["network_size"]),
        SCENARIO_SEED,
        topology=str(media["topology"]),
        k=int(media["k"]),
        rewire_prob=float(media["rewire_prob"]),
    )
    campaign = simulate_disinformation(
        network,
        media_reach=float(media["media_reach"]),
        persuasion=float(media["persuasion"]),
        seed=SCENARIO_SEED,
        steps=int(media["steps"]),
        spread_rate=float(media["spread_rate"]),
        campaign_delay=int(media["campaign_delay"]),
    )
    baseline = simulate_disinformation(
        network,
        media_reach=0.0,
        persuasion=float(media["persuasion"]),
        seed=SCENARIO_SEED,
        steps=int(media["steps"]),
        spread_rate=float(media["spread_rate"]),
        campaign_delay=int(media["campaign_delay"]),
    )
    figure, axis = plt.subplots(figsize=(7, 4.2))
    steps = list(range(len(campaign.belief_share)))
    axis.plot(
        steps,
        np.asarray(campaign.belief_share) * 100.0,
        marker="o",
        markersize=3,
        label="Media campaign",
    )
    axis.plot(
        steps,
        np.asarray(baseline.belief_share) * 100.0,
        marker="s",
        markersize=3,
        label="No media (baseline)",
    )
    axis.set_xlabel("Simulation round")
    axis.set_ylabel("Believing agents (%)")
    axis.set_title("Disinformation propagation: media + social spread")
    axis.grid(True, alpha=0.3)
    axis.legend()
    axis.set_ylim(bottom=0.0)
    path = Path(project_root) / FIGURES_DIR / "disinformation_propagation.png"
    _save(figure, path)
    return path


def fig_stealth_detection(project_root: Path | str) -> Path:
    """Detection probability vs range for a reference and a stealth target."""
    stealth = SCENARIO_PARAMS["stealth"]
    radar = SCENARIO_PARAMS["stealth"]["radar"]
    cfg = RadarConfig(
        peak_power_w=float(radar["peak_power_w"]),
        gain_db=float(radar["gain_db"]),
        frequency_hz=float(radar["frequency_hz"]),
        bandwidth_hz=float(radar["bandwidth_hz"]),
        noise_figure_db=float(radar["noise_figure_db"]),
        losses_db=float(radar["losses_db"]),
        pulses=int(radar["pulses"]),
    )
    p_fa = float(stealth["pfa"])
    ranges_m = np.linspace(2.0e3, 60.0e3, 120)

    def curve(rcs: float) -> np.ndarray:
        return np.asarray(
            [
                detection_probability(
                    snr_at_range(r, rcs, config=cfg), p_fa=p_fa, pulses=cfg.pulses
                )
                for r in ranges_m
            ]
        )

    figure, axis = plt.subplots(figsize=(7, 4.2))
    axis.plot(
        ranges_m / 1.0e3,
        curve(float(stealth["reference_rcs_sqm"])),
        label="Reference target (1 m²)",
    )
    axis.plot(
        ranges_m / 1.0e3,
        curve(float(stealth["stealth_rcs_sqm"])),
        label="Stealth hull (0.01 m²)",
    )
    axis.axhline(
        float(stealth["p_d_target"]),
        color="gray",
        linestyle="--",
        linewidth=1,
        label="P_d target",
    )
    axis.set_xlabel("Range (km)")
    axis.set_ylabel("Detection probability P_d")
    axis.set_title("Low-RCS stealth: detection probability vs range")
    axis.grid(True, alpha=0.3)
    axis.legend()
    axis.set_ylim(0.0, 1.02)
    path = Path(project_root) / FIGURES_DIR / "stealth_detection.png"
    _save(figure, path)
    return path


def fig_gps_denial(project_root: Path | str) -> Path:
    """Position error vs jammer standoff distance (fixed jammer power)."""
    gps = SCENARIO_PARAMS["gps"]
    scenario = run_carver_scenario(seed=SCENARIO_SEED)
    pdop = float(scenario["gps"]["pdop"])
    cno_clean = float(gps["cno_clean_dbhz"])
    distances = np.geomspace(20.0e3, 200.0e3, 60)

    def error_at(distance: float) -> float:
        jnr = jamming_to_noise_db(
            float(gps["jammer_power_w"]),
            distance,
            jammer_gain_db=float(gps["jammer_gain_db"]),
        )
        cno = effective_cno_dbhz(cno_clean, jnr)
        return position_error_meters(pdop, cno)

    figure, axis = plt.subplots(figsize=(7, 4.2))
    axis.semilogx(
        distances / 1.0e3,
        np.asarray([error_at(d) for d in distances]),
        marker="o",
        markersize=3,
        label="Jammed receiver (1 W jammer)",
    )
    axis.axhline(
        position_error_meters(pdop, cno_clean),
        color="gray",
        linestyle="--",
        linewidth=1,
        label="Clean-sky error",
    )
    axis.set_xlabel("Jammer standoff distance (km)")
    axis.set_ylabel("1-σ position error (m)")
    axis.set_title("GPS denial: navigation error vs jammer distance")
    axis.grid(True, alpha=0.3)
    axis.legend()
    path = Path(project_root) / FIGURES_DIR / "gps_denial.png"
    _save(figure, path)
    return path


def render_figures(project_root: Path | str) -> dict[str, Path]:
    """Render all CARVER figures under ``output/figures/``.

    Returns:
        Mapping of figure name to the written PNG path.
    """
    root = Path(project_root)
    out_dir = root / FIGURES_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    generators: dict[str, Callable[[Path], Path]] = {
        "disinformation": fig_disinformation,
        "stealth_detection": fig_stealth_detection,
        "gps_denial": fig_gps_denial,
    }
    return {name: generator(root) for name, generator in generators.items()}
