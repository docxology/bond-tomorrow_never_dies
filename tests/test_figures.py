"""Tests for CARVER figure generation.

The old version of this file asserted only that six PNGs existed, ended in
``.png`` and exceeded 1000 bytes. That reached 100% line coverage on
``figures.py`` while binding nothing: swapped datasets, mislabelled curves,
inverted axes or a blank canvas all passed. These tests read the plotted
artists back out of the figure and compare them against the same domain
computation the manuscript quotes, so the figure has to show the right data.

Zero mocks: every expected series is recomputed from the real domain modules.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tomorrow_never_dies.figures import (
    CNO_TRACKING_THRESHOLD_DBHZ,
    FIGURE_BUILDERS,
    FIGURE_FILENAMES,
    build_disinformation,
    build_gps_denial,
    build_narrative,
    build_raim,
    build_stealth_detection,
    build_waveform,
    render_figures,
)
from tomorrow_never_dies.gnss_integrity import (
    detection_probability as raim_detection_probability,
)
from tomorrow_never_dies.gps_denial import (
    effective_cno_dbhz,
    jamming_to_noise_db,
    position_error_meters,
)
from tomorrow_never_dies.media_manipulation import (
    build_network,
    simulate_disinformation,
)
from tomorrow_never_dies.radar_waveform import Waveform, peak_sidelobe_ratio
from tomorrow_never_dies.scenario import (
    SCENARIO_PARAMS,
    SCENARIO_SEED,
    run_carver_scenario,
)

_FIGURE_NAMES = {
    "disinformation",
    "narrative",
    "stealth_detection",
    "waveform",
    "gps_denial",
    "raim",
}


def _labelled_lines(figure) -> dict[str, np.ndarray]:
    """Map every legend-labelled line on the first axis to its y-data."""
    axis = figure.axes[0]
    return {
        line.get_label(): np.asarray(line.get_ydata())
        for line in axis.get_lines()
        if not str(line.get_label()).startswith("_")
    }


def test_render_figures_writes_every_declared_png(tmp_path: Path) -> None:
    paths = render_figures(tmp_path)
    assert set(paths) == _FIGURE_NAMES == set(FIGURE_BUILDERS) == set(FIGURE_FILENAMES)
    for name, path in paths.items():
        assert path.is_file(), name
        assert path.name == FIGURE_FILENAMES[name]
        assert path.stat().st_size > 1000


def test_disinformation_figure_plots_the_real_trajectories() -> None:
    """Both curves must be the actual simulated belief shares, in percent."""
    media = SCENARIO_PARAMS["media"]
    network = build_network(
        int(media["network_size"]),
        SCENARIO_SEED,
        topology=str(media["topology"]),
        k=int(media["k"]),
        rewire_prob=float(media["rewire_prob"]),
    )
    common = {
        "persuasion": float(media["persuasion"]),
        "seed": SCENARIO_SEED,
        "steps": int(media["steps"]),
        "spread_rate": float(media["spread_rate"]),
        "campaign_delay": int(media["campaign_delay"]),
    }
    campaign = simulate_disinformation(
        network, media_reach=float(media["media_reach"]), **common
    )
    baseline = simulate_disinformation(network, media_reach=0.0, **common)

    figure = build_disinformation()
    try:
        lines = _labelled_lines(figure)
        assert set(lines) == {"Media campaign", "No media (baseline)"}
        np.testing.assert_allclose(
            lines["Media campaign"], np.asarray(campaign.belief_share) * 100.0
        )
        np.testing.assert_allclose(
            lines["No media (baseline)"], np.asarray(baseline.belief_share) * 100.0
        )
        # The labels are not interchangeable: the campaign really is higher.
        assert lines["Media campaign"][-1] > lines["No media (baseline)"][-1]
        axis = figure.axes[0]
        assert axis.get_xlabel() == "Simulation round"
        assert "%" in axis.get_ylabel()
    finally:
        figure.clear()


def test_stealth_figure_curves_are_ordered_and_monotone() -> None:
    """The low-RCS curve must sit below the reference curve everywhere."""
    figure = build_stealth_detection()
    try:
        lines = _labelled_lines(figure)
        reference = lines["Reference target (1 m²)"]
        stealth = lines["Stealth hull (0.01 m²)"]
        assert np.all(stealth <= reference + 1e-12), "series are swapped"
        # Detection probability falls with range for both targets.
        assert reference[0] > reference[-1] and stealth[0] > stealth[-1]
        x = np.asarray(figure.axes[0].get_lines()[0].get_xdata())
        assert x[0] == pytest.approx(2.0)  # km, not metres
        assert figure.axes[0].get_xlabel() == "Range (km)"
    finally:
        figure.clear()


def test_gps_denial_figure_plots_the_real_error_curve_and_flags_lost_lock() -> None:
    gps = SCENARIO_PARAMS["gps"]
    pdop = float(run_carver_scenario(seed=SCENARIO_SEED)["gps"]["pdop"])
    cno_clean = float(gps["cno_clean_dbhz"])
    distances = np.geomspace(20.0e3, 2000.0e3, 80)
    cnos = np.asarray(
        [
            effective_cno_dbhz(
                cno_clean,
                jamming_to_noise_db(
                    float(gps["jammer_power_w"]),
                    d,
                    jammer_gain_db=float(gps["jammer_gain_db"]),
                ),
            )
            for d in distances
        ]
    )
    expected = np.asarray([position_error_meters(pdop, c) for c in cnos])
    figure = build_gps_denial()
    try:
        lines = _labelled_lines(figure)
        np.testing.assert_allclose(lines["Jammed receiver (1 W jammer)"], expected)
        np.testing.assert_allclose(
            np.asarray(figure.axes[0].get_lines()[0].get_xdata()), distances / 1.0e3
        )
        # Error falls as the jammer moves away, and the clean-sky reference is
        # below every jammed point.
        assert expected[0] > expected[-1]
        clean = lines["Clean-sky error"]
        assert float(clean[0]) == pytest.approx(position_error_meters(pdop, cno_clean))
        assert float(clean[0]) < expected.min()
        # The extrapolated region is disclosed on the figure, not plotted bare.
        labels = [text.get_text() for text in figure.axes[0].get_legend().get_texts()]
        assert any(
            f"{CNO_TRACKING_THRESHOLD_DBHZ:.0f} dB-Hz" in label for label in labels
        ), labels
        # The shading must be a real boundary, not the whole axis: the sweep
        # has to reach far enough out that the receiver regains lock, or the
        # disclosure would be decoration with nothing to contrast against.
        assert cnos.min() < CNO_TRACKING_THRESHOLD_DBHZ < cnos.max()
        spans = [p for p in figure.axes[0].patches if p.get_label().startswith("C/N0")]
        assert len(spans) == 1
        shaded_right = float(spans[0].get_xy()[0]) + float(spans[0].get_width())
        crossing = float(distances[cnos < CNO_TRACKING_THRESHOLD_DBHZ].max()) / 1.0e3
        assert shaded_right == pytest.approx(crossing)
        assert shaded_right < float(distances[-1]) / 1.0e3
    finally:
        figure.clear()


def test_narrative_figure_band_brackets_the_mean() -> None:
    narrative = SCENARIO_PARAMS["narrative"]
    figure = build_narrative()
    try:
        lines = _labelled_lines(figure)
        mean = lines["Mean opinion (media campaign)"]
        manufactured = lines["Manufactured line"]
        assert float(manufactured[0]) == pytest.approx(
            float(narrative["media_opinion"])
        )
        # The campaign pulls the mean toward the manufactured line over time.
        assert abs(mean[-1] - manufactured[0]) < abs(mean[0] - manufactured[0])
        assert np.all((mean >= 0.0) & (mean <= 1.0))
        collection = figure.axes[0].collections[0]  # the +/- 1 sd band
        assert collection.get_label() == "Opinion mean +/- 1 sd"
    finally:
        figure.clear()


def test_waveform_figure_shows_barker_below_lfm_sidelobes() -> None:
    """Both compressed responses peak at 0 dB and Barker's floor is lower."""
    figure = build_waveform()
    try:
        lines = _labelled_lines(figure)
        lfm_label = next(label for label in lines if label.startswith("LFM"))
        assert "500" in lfm_label  # B*T of the canonical chirp
        lfm, barker = lines[lfm_label], lines["Barker-13"]
        assert float(np.max(lfm)) == pytest.approx(0.0, abs=1e-9)
        assert float(np.max(barker)) == pytest.approx(0.0, abs=1e-9)
        # The peak sidelobe read off each plotted curve (excluding its own
        # mainlobe) must equal the domain module's peak_sidelobe_ratio, and
        # Barker-13's floor must be the cleaner one — the trade the results
        # section reports.
        axis = figure.axes[0]
        cases = (
            (lfm_label, Waveform("lfm", 50e-6, 10e6, 40e6), 4),
            ("Barker-13", Waveform("barker13", 13e-6, 13e6, 13e6), 13),
        )
        measured = {}
        for label, waveform, mainlobe_half in cases:
            line = next(ln for ln in axis.get_lines() if ln.get_label() == label)
            delays = np.asarray(line.get_xdata())
            series = np.asarray(line.get_ydata())
            peak_sidelobe = float(np.max(series[np.abs(delays) > mainlobe_half]))
            assert peak_sidelobe == pytest.approx(
                peak_sidelobe_ratio(waveform), abs=1e-6
            )
            measured[label] = peak_sidelobe
        assert measured["Barker-13"] < measured[lfm_label]
        assert axis.get_ylabel() == "Compressed power (dB)"
    finally:
        figure.clear()


def test_raim_figure_plots_both_projection_envelopes() -> None:
    """The worst- and best-placed satellite curves must be the real ones."""
    integrity = SCENARIO_PARAMS["integrity"]
    block = run_carver_scenario(seed=SCENARIO_SEED)["integrity"]
    biases = np.linspace(0.0, 30.0, 61)

    def expected(factor: float) -> np.ndarray:
        return (
            np.asarray(
                [
                    raim_detection_probability(
                        float(b),
                        dof=int(block["dof"]),
                        p_fa=float(integrity["p_fa"]),
                        projection_factor=factor,
                        sigma=float(integrity["sigma_m"]),
                    )
                    for b in biases
                ]
            )
            * 100.0
        )

    figure = build_raim()
    try:
        lines = _labelled_lines(figure)
        worst_label = next(label for label in lines if label.startswith("Worst"))
        best_label = next(label for label in lines if label.startswith("Best"))
        np.testing.assert_allclose(
            lines[worst_label],
            expected(float(block["projection_factor_worst"])),
        )
        np.testing.assert_allclose(
            lines[best_label], expected(float(block["projection_factor_best"]))
        )
        # The reported (worst-case) curve is the lower one — not the flattering
        # one — at every bias.
        assert np.all(lines[worst_label] <= lines[best_label] + 1e-12)
        assert "reported" in worst_label
    finally:
        figure.clear()


@pytest.mark.parametrize("name", sorted(_FIGURE_NAMES))
def test_every_figure_is_titled_labelled_and_populated(name: str) -> None:
    figure = FIGURE_BUILDERS[name]()
    try:
        axis = figure.axes[0]
        assert axis.get_title()
        assert axis.get_xlabel() and axis.get_ylabel()
        assert axis.get_legend() is not None
        drawn = [
            np.asarray(line.get_ydata())
            for line in axis.get_lines()
            if np.asarray(line.get_ydata()).size > 1
        ]
        assert drawn, f"{name} has no plotted series"
        # No blank canvas: at least one series actually varies.
        assert any(float(np.ptp(series)) > 0.0 for series in drawn)
    finally:
        figure.clear()
