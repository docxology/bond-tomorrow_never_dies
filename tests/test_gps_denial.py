"""Tests for the GPS-denial impact analysis.

Zero mocks: DOP from real geometry matrices, C/N0 degradation from the
jamming model, and failure cascades from deterministic graph propagation.
"""

from __future__ import annotations

import numpy as np
import pytest

from tomorrow_never_dies.gps_denial import (
    Constellation,
    Satellite,
    compute_dop,
    effective_cno_dbhz,
    geometry_matrix,
    jamming_to_noise_db,
    maritime_dependency_network,
    position_error_meters,
    simulate_navigation_cascade,
    uere_meters,
    unit_vector,
    walker_constellation,
)


def test_walker_constellation_deterministic() -> None:
    a = walker_constellation(24, 6, seed=7)
    b = walker_constellation(24, 6, seed=7)
    assert a.satellites == b.satellites
    assert len(a.satellites) == 24
    assert all(5.0 <= sat.elevation_deg <= 90.0 for sat in a.satellites)


def test_walker_constellation_errors() -> None:
    with pytest.raises(ValueError):
        walker_constellation(3)
    with pytest.raises(ValueError):
        walker_constellation(24, 0)
    with pytest.raises(ValueError):
        walker_constellation(24, 25)
    with pytest.raises(ValueError):
        walker_constellation(24, 6, seed=-1)


def test_visible_filter() -> None:
    constellation = Constellation(
        satellites=(Satellite("A", 0.0, 5.0), Satellite("B", 90.0, 45.0))
    )
    assert [s.name for s in constellation.visible(10.0)] == ["B"]
    assert len(constellation.visible(0.0)) == 2


def test_satellite_and_constellation_validation() -> None:
    with pytest.raises(ValueError):
        Satellite("", 0.0, 45.0)
    with pytest.raises(ValueError):
        Satellite("A", 360.0, 45.0)
    with pytest.raises(ValueError):
        Satellite("A", 0.0, 95.0)
    with pytest.raises(ValueError):
        Constellation(satellites=())
    with pytest.raises(ValueError):
        Constellation(satellites=(1,))


def test_unit_vector() -> None:
    assert np.allclose(unit_vector(0.0, 0.0), [0.0, 1.0, 0.0])
    assert np.allclose(unit_vector(0.0, 90.0), [0.0, 0.0, 1.0])
    assert np.allclose(unit_vector(90.0, 0.0), [1.0, 0.0, 0.0])


def test_geometry_matrix() -> None:
    sats = (
        Satellite("A", 30.0, 40.0),
        Satellite("B", 120.0, 50.0),
        Satellite("C", 210.0, 60.0),
        Satellite("D", 300.0, 25.0),
    )
    g = geometry_matrix(sats)
    assert g.shape == (4, 4)
    with pytest.raises(ValueError):
        geometry_matrix(())


def test_compute_dop() -> None:
    sats = tuple(walker_constellation(24, 6, seed=7).visible(10.0))
    dop = compute_dop(sats)
    assert dop.gdop > 0 and dop.pdop > 0 and dop.hdop > 0 and dop.vdop > 0
    assert dop.pdop**2 == pytest.approx(dop.hdop**2 + dop.vdop**2)
    assert dop.gdop >= dop.pdop
    with pytest.raises(ValueError):
        compute_dop(sats[:3])


def test_jamming_to_noise() -> None:
    near = jamming_to_noise_db(1.0, 50.0e3)
    far = jamming_to_noise_db(1.0, 200.0e3)
    assert near > far
    strong = jamming_to_noise_db(10.0, 100.0e3)
    weak = jamming_to_noise_db(1.0, 100.0e3)
    assert strong - weak == pytest.approx(10.0, rel=1e-6)  # 10x power -> +10 dB
    with pytest.raises(ValueError):
        jamming_to_noise_db(0.0, 100.0e3)
    with pytest.raises(ValueError):
        jamming_to_noise_db(1.0, -5.0)


def test_effective_cno() -> None:
    # A vanishingly weak jammer barely degrades C/N0.
    assert effective_cno_dbhz(45.0, -30.0) == pytest.approx(45.0, abs=0.01)
    assert effective_cno_dbhz(45.0, 10.0) < 45.0
    # 0 dB JNR means jammer power equals noise power -> -3.01 dB degradation.
    assert effective_cno_dbhz(45.0, 0.0) == pytest.approx(45.0 - 3.0102999566, rel=1e-3)
    with pytest.raises(ValueError):
        effective_cno_dbhz(0.0, 1.0)
    with pytest.raises(ValueError):
        effective_cno_dbhz(45.0, float("nan"))


def test_uere() -> None:
    clean = uere_meters(45.0)
    jammed = uere_meters(15.0)
    assert jammed > clean
    assert clean > 4.0  # dominated by the ionosphere budget
    # A negative effective C/N0 (severely jammed) yields huge but finite error.
    severe = uere_meters(-5.0)
    assert np.isfinite(severe)
    assert severe > jammed
    with pytest.raises(ValueError):
        uere_meters(float("nan"))
    with pytest.raises(ValueError):
        uere_meters(float("inf"))
    with pytest.raises(ValueError):
        uere_meters(45.0, iono_m=-1.0)


def test_position_error() -> None:
    assert position_error_meters(2.0, 45.0) == pytest.approx(2.0 * uere_meters(45.0))
    with pytest.raises(ValueError):
        position_error_meters(0.0, 45.0)


def test_maritime_network_consistency() -> None:
    dependencies, weights = maritime_dependency_network()
    assert set(dependencies) == set(weights)
    for dependents in dependencies.values():
        for dependent in dependents:
            assert dependent in weights
    assert all(0.0 <= w <= 1.0 for w in weights.values())


def test_cascade_no_jamming() -> None:
    dependencies, weights = maritime_dependency_network()
    result = simulate_navigation_cascade(dependencies, weights, jamming_strength=0.0)
    assert result.failed == ()
    assert result.total_fraction == 0.0
    assert result.rounds == 0


def test_cascade_deterministic_and_monotone() -> None:
    dependencies, weights = maritime_dependency_network()
    low = simulate_navigation_cascade(dependencies, weights, jamming_strength=0.3)
    high = simulate_navigation_cascade(dependencies, weights, jamming_strength=0.85)
    again = simulate_navigation_cascade(dependencies, weights, jamming_strength=0.85)
    assert high == again
    assert high.total_fraction >= low.total_fraction
    assert high.failed == ("commercial_shipping", "hms_devonshire", "sea_lanes")
    assert high.rounds == 3
    assert high.per_round[0] == 1  # hms_devonshire fails first


def test_cascade_strong_jamming_multi_fail_round() -> None:
    dependencies, weights = maritime_dependency_network()
    result = simulate_navigation_cascade(dependencies, weights, jamming_strength=0.9)
    assert result.rounds == 2  # two nodes fail in round 1
    assert result.per_round[0] == 2
    assert len(result.failed) == 3


def test_cascade_errors() -> None:
    dependencies, weights = maritime_dependency_network()
    bad_weights = dict(weights)
    bad_weights["extra"] = 0.5
    with pytest.raises(ValueError):
        simulate_navigation_cascade(dependencies, bad_weights)
    bad_deps = dict(dependencies)
    bad_deps.pop("carver_tower")
    with pytest.raises(ValueError):
        simulate_navigation_cascade(bad_deps, weights)
    with pytest.raises(ValueError):
        simulate_navigation_cascade({}, {})
    with pytest.raises(ValueError):
        simulate_navigation_cascade(dependencies, weights, jamming_strength=1.5)
    with pytest.raises(ValueError):
        simulate_navigation_cascade(dependencies, weights, fail_threshold=0.0)
    with pytest.raises(ValueError):
        simulate_navigation_cascade(dependencies, weights, propagation_factor=-0.1)
    with pytest.raises(ValueError):
        simulate_navigation_cascade(dependencies, weights, max_rounds=0)


def test_cascade_rejects_unknown_dependent() -> None:
    """A dependent with no weight fails at the boundary, not with a KeyError."""
    dependencies, weights = maritime_dependency_network()
    bad_deps = dict(dependencies)
    bad_deps["hms_devonshire"] = ("hms_devonshire_tender",)
    with pytest.raises(ValueError, match="unknown node"):
        simulate_navigation_cascade(bad_deps, weights)


def test_cascade_max_rounds_truncates_before_fixpoint() -> None:
    """``max_rounds`` bounds the cascade even when failures are still spreading."""
    dependencies, weights = maritime_dependency_network()
    full = simulate_navigation_cascade(dependencies, weights, jamming_strength=0.85)
    clipped = simulate_navigation_cascade(
        dependencies, weights, jamming_strength=0.85, max_rounds=1
    )
    assert clipped.rounds == 1
    assert len(clipped.failed) < len(full.failed)


def test_satellite_rejects_non_numeric_angles() -> None:
    with pytest.raises(ValueError, match="azimuth_deg must be a number"):
        Satellite(name="PRN01", azimuth_deg=True, elevation_deg=30.0)
    with pytest.raises(ValueError, match="elevation_deg must be a number"):
        Satellite(name="PRN01", azimuth_deg=10.0, elevation_deg="high")  # type: ignore[arg-type]


def test_visible_rejects_non_numeric_mask() -> None:
    constellation = walker_constellation(8, 2, seed=7)
    with pytest.raises(ValueError, match="mask_angle_deg must be a number"):
        constellation.visible(mask_angle_deg=True)
    with pytest.raises(ValueError, match=r"\[0, 90\]"):
        constellation.visible(mask_angle_deg=120.0)
