"""Tests for bounded-confidence narrative control (Hegselmann-Krause + media)."""

from __future__ import annotations

import numpy as np
import pytest

from tomorrow_never_dies.media_manipulation import build_network
from tomorrow_never_dies.narrative_control import (
    bimodal_split,
    critical_media_reach,
    initial_opinions,
    media_capture,
    polarization_variance,
    simulate_opinions,
)


def test_initial_opinions() -> None:
    opinions = initial_opinions(50, 7)
    assert opinions.shape == (50,)
    assert np.all(opinions >= 0.0) and np.all(opinions < 1.0)
    np.testing.assert_array_equal(initial_opinions(50, 7), opinions)
    with pytest.raises(ValueError):
        initial_opinions(1, 7)
    with pytest.raises(ValueError):
        initial_opinions(10, -1)


def test_simulate_opinions_deterministic_and_shapes() -> None:
    a = simulate_opinions(40, 7)
    b = simulate_opinions(40, 7)
    assert a.final == b.final
    assert a.media_capture == b.media_capture
    assert len(a.trajectory) == a.steps + 1
    assert len(a.initial) == 40 and len(a.final) == 40
    assert 0.0 <= a.consensus <= 1.0
    assert a.variance >= 0.0
    assert 0.0 <= a.bimodal_split <= 1.0
    assert 0.0 <= a.media_capture <= 1.0


def test_simulate_opinions_no_media_capture() -> None:
    result = simulate_opinions(40, 7, media_weight=0.0, media_reach=1.0, steps=10)
    assert result.media_capture == pytest.approx(0.0, abs=1e-9)
    # A stronger broadcast pulls the mean harder toward the media line.
    weak = simulate_opinions(60, 7, media_weight=0.05, media_reach=1.0, steps=20)
    strong = simulate_opinions(60, 7, media_weight=0.2, media_reach=1.0, steps=20)
    assert strong.media_capture >= weak.media_capture


def test_simulate_opinions_errors() -> None:
    with pytest.raises(ValueError):
        simulate_opinions(1, 7)
    with pytest.raises(ValueError):
        simulate_opinions(10, -1)
    with pytest.raises(ValueError):
        simulate_opinions(10, 7, confidence=0.0)
    with pytest.raises(ValueError):
        simulate_opinions(10, 7, confidence=-0.1)
    with pytest.raises(ValueError):
        simulate_opinions(10, 7, media_opinion=1.5)
    with pytest.raises(ValueError):
        simulate_opinions(10, 7, media_weight=-0.1)
    with pytest.raises(ValueError):
        simulate_opinions(10, 7, media_reach=1.1)
    with pytest.raises(ValueError):
        simulate_opinions(10, 7, steps=0)


def test_polarization_and_bimodal_metrics() -> None:
    uniform = np.full(20, 0.5)
    assert polarization_variance(uniform) == pytest.approx(0.0)
    split = np.asarray([0.0, 1.0, 0.0, 1.0])
    assert polarization_variance(split) == pytest.approx(0.25)
    # Two far clusters: the cross-cluster pairs are separated (4 of 6 pairs).
    assert bimodal_split(
        np.asarray([0.0, 0.0, 1.0, 1.0]), confidence=0.1
    ) == pytest.approx(4 / 6)
    assert bimodal_split(uniform, confidence=0.2) == pytest.approx(0.0)
    with pytest.raises(ValueError):
        bimodal_split(np.asarray([0.5]), confidence=0.1)
    with pytest.raises(ValueError):
        bimodal_split(uniform, confidence=0.0)
    with pytest.raises(ValueError):
        bimodal_split(uniform, confidence=1.5)


def test_media_capture() -> None:
    assert media_capture(np.asarray([0.5]), np.asarray([0.5]), 0.9) == pytest.approx(
        0.0
    )
    # Final reaches the media line -> full capture.
    assert media_capture(np.asarray([0.9]), np.asarray([0.5]), 0.9) == pytest.approx(
        1.0
    )
    # Denominator zero -> no capture defined, returns 0.
    assert media_capture(np.asarray([0.5]), np.asarray([0.9]), 0.9) == pytest.approx(
        0.0
    )
    # Capture clamps to [0, 1].
    assert 0.0 <= media_capture(np.asarray([0.9]), np.asarray([0.52]), 0.8) <= 1.0
    with pytest.raises(ValueError):
        media_capture(np.asarray([0.5]), np.asarray([0.5]), 1.5)


def test_critical_media_reach() -> None:
    network = build_network(60, 7)
    reach = critical_media_reach(network, target_share=0.5, seed=7)
    assert 0.0 <= reach <= 1.0
    # Deterministic.
    assert reach == critical_media_reach(network, target_share=0.5, seed=7)
    # A higher target needs at least as much reach to tip the network.
    low = critical_media_reach(network, target_share=0.4, seed=7)
    high = critical_media_reach(network, target_share=0.6, seed=7)
    assert high >= low


def test_critical_media_reach_edges() -> None:
    # No social spread -> without a campaign only the initial believer converts.
    network = build_network(40, 3)
    easy = critical_media_reach(
        network, target_share=0.01, seed=3, steps=6, persuasion=0.5, spread_rate=0.0
    )
    assert easy == pytest.approx(0.0)  # baseline already exceeds a trivial target
    # One campaign round at 30% persuasion and no social spread cannot reach
    # 99.9% of the network however wide the broadcast, so the search saturates.
    hard = critical_media_reach(
        network, target_share=0.999, seed=3, steps=2, persuasion=0.3, spread_rate=0.0
    )
    assert hard == pytest.approx(1.0)  # even full reach cannot saturate the network
    mid = critical_media_reach(
        network, target_share=0.5, seed=3, steps=6, persuasion=0.5, spread_rate=0.0
    )
    assert 0.0 < mid < 1.0  # a reachable interior tipping point


def test_critical_media_reach_errors() -> None:
    network = build_network(20, 1)
    with pytest.raises(ValueError):
        critical_media_reach((), target_share=0.5)
    with pytest.raises(ValueError):
        critical_media_reach(network, target_share=0.0)
    with pytest.raises(ValueError):
        critical_media_reach(network, target_share=1.0)
    with pytest.raises(ValueError):
        critical_media_reach(network, target_share=0.5, seed=-1)
