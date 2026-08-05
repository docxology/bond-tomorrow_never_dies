"""Tests for GNSS integrity / RAIM (chi-square math, parity space, HPL/VPL)."""

from __future__ import annotations

import numpy as np
import pytest

from tomorrow_never_dies.gnss_integrity import (
    chi_square_cdf,
    chi_square_ppf,
    detection_probability,
    integrity_availability,
    least_squares_position,
    noncentral_chi2_cdf,
    normal_cdf,
    normal_ppf,
    parity_matrix,
    protection_levels,
    raim_threshold,
    slopes,
)
from tomorrow_never_dies.gnss_integrity import (
    test_statistic as raim_test_statistic,  # alias: pytest-collectable name
)
from tomorrow_never_dies.gps_denial import geometry_matrix, walker_constellation

# Realistic geometry: the canonical constellation's visible satellites.
_SCENARIO_GEOMETRY = geometry_matrix(
    tuple(walker_constellation(24, 6, seed=7).visible(10.0))
)


def test_normal_cdf_quantile() -> None:
    assert normal_cdf(0.0) == pytest.approx(0.5)
    assert normal_ppf(0.5) == pytest.approx(0.0, abs=1e-4)
    for z in (-2.0, -0.5, 0.0, 1.0, 2.5):
        assert normal_ppf(normal_cdf(z)) == pytest.approx(z, abs=1e-4)
    for bad in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(ValueError):
            normal_ppf(bad)


def test_chi_square_cdf_known_values() -> None:
    assert chi_square_cdf(0.0, 1) == 0.0
    assert chi_square_cdf(1.0, 1) == pytest.approx(0.682689, rel=1e-4)  # erf(sqrt(1/2))
    assert chi_square_cdf(2.0, 2) == pytest.approx(1 - np.e**-1, rel=1e-4)
    assert chi_square_cdf(100.0, 2) == pytest.approx(1.0, abs=1e-6)
    with pytest.raises(ValueError):
        chi_square_cdf(-1.0, 2)
    with pytest.raises(ValueError):
        chi_square_cdf(1.0, 0)


def test_chi_square_ppf_round_trip() -> None:
    for p in (0.1, 0.5, 0.95, 0.999):
        quantile = chi_square_ppf(p, 18)
        assert chi_square_cdf(quantile, 18) == pytest.approx(p, abs=1e-3)
    with pytest.raises(ValueError):
        chi_square_ppf(0.0, 18)
    with pytest.raises(ValueError):
        chi_square_ppf(0.5, 0)


def test_parity_matrix() -> None:
    geometry = _SCENARIO_GEOMETRY
    n_rows, n_cols = geometry.shape
    parity = parity_matrix(geometry)
    assert parity.shape == (n_rows - n_cols, n_rows)
    # Orthonormal rows and orthogonal to the geometry.
    np.testing.assert_allclose(parity @ parity.T, np.eye(parity.shape[0]), atol=1e-9)
    np.testing.assert_allclose(
        parity @ geometry, np.zeros((n_rows - n_cols, n_cols)), atol=1e-9
    )
    with pytest.raises(ValueError):
        parity_matrix(geometry[:n_cols])
    with pytest.raises(ValueError):
        parity_matrix(np.zeros((10, 3)))


def test_least_squares_position() -> None:
    geometry = _SCENARIO_GEOMETRY
    truth = np.asarray([1.0, -2.0, 3.0, 0.5])
    measurements = geometry @ truth
    recovered = least_squares_position(geometry, measurements)
    np.testing.assert_allclose(recovered, truth, atol=1e-6)
    with pytest.raises(ValueError):
        least_squares_position(geometry, np.zeros(5))
    with pytest.raises(ValueError):
        least_squares_position(np.zeros((3, 4)), np.zeros(3))


def test_test_statistic() -> None:
    geometry = _SCENARIO_GEOMETRY
    n_rows = geometry.shape[0]
    position = np.asarray([0.0, 0.0, 0.0, 0.0])
    clean = np.zeros(n_rows, dtype=float)
    # Fault-free residual test statistic ~ chi-square with n-4 dof: small.
    t_clean = raim_test_statistic(clean, geometry, position, sigma=3.0)
    assert t_clean == pytest.approx(0.0, abs=1e-9)
    # A 20 m bias on a measurement inflates the statistic.
    biased = clean.copy()
    biased[0] = 20.0
    t_bias = raim_test_statistic(biased, geometry, position, sigma=3.0)
    assert t_bias > t_clean
    with pytest.raises(ValueError):
        raim_test_statistic(clean, geometry, position, sigma=0.0)


def test_raim_threshold() -> None:
    more = raim_threshold(20, 1e-4)
    fewer = raim_threshold(10, 1e-4)
    assert more > fewer  # more dof -> larger threshold
    loose = raim_threshold(18, 1e-2)
    strict = raim_threshold(18, 1e-8)
    assert loose < strict  # stricter p_fa -> larger threshold
    with pytest.raises(ValueError):
        raim_threshold(0, 1e-4)
    with pytest.raises(ValueError):
        raim_threshold(18, 0.0)


def test_slopes() -> None:
    geometry = _SCENARIO_GEOMETRY
    horizontal, vertical = slopes(geometry)
    assert len(horizontal) == len(vertical) == geometry.shape[0]
    assert all(h >= 0 for h in horizontal) and all(v >= 0 for v in vertical)
    with pytest.raises(ValueError):
        slopes(_SCENARIO_GEOMETRY[:4])


def test_protection_levels() -> None:
    geometry = _SCENARIO_GEOMETRY
    levels = protection_levels(geometry, p_fa=1e-5, p_md=1e-3, sigma=3.0)
    assert levels.hpl > 0 and levels.vpl > 0
    assert levels.dof == geometry.shape[0] - 4
    with pytest.raises(ValueError):
        protection_levels(geometry, p_fa=1.0)
    with pytest.raises(ValueError):
        protection_levels(geometry, p_md=0.0)
    with pytest.raises(ValueError):
        protection_levels(geometry, sigma=-1.0)
    with pytest.raises(ValueError):
        protection_levels(_SCENARIO_GEOMETRY[:4])


def test_detection_probability() -> None:
    dof = _SCENARIO_GEOMETRY.shape[0] - 4
    p_fa = 1e-5
    # Zero bias -> detection probability equals the false-alarm rate.
    assert detection_probability(0.0, dof=dof, p_fa=p_fa, sigma=3.0) == pytest.approx(
        p_fa, rel=1e-3
    )
    # Monotone increasing in bias, approaching 1.
    small = detection_probability(5.0, dof=dof, p_fa=p_fa, sigma=3.0)
    large = detection_probability(30.0, dof=dof, p_fa=p_fa, sigma=3.0)
    assert large >= small
    assert large == pytest.approx(1.0, abs=1e-3)
    with pytest.raises(ValueError):
        detection_probability(-1.0, dof=dof, p_fa=p_fa)
    with pytest.raises(ValueError):
        detection_probability(5.0, dof=dof, p_fa=1.0)
    with pytest.raises(ValueError):
        detection_probability(5.0, dof=dof, p_fa=p_fa, sigma=0.0)


def test_noncentral_chi2_matches_central_for_zero_nc() -> None:
    for x in (5.0, 20.0, 50.0):
        assert noncentral_chi2_cdf(x, 18, 0.0) == pytest.approx(chi_square_cdf(x, 18))
    with pytest.raises(ValueError):
        noncentral_chi2_cdf(-1.0, 18, 1.0)
    with pytest.raises(ValueError):
        noncentral_chi2_cdf(5.0, 18, -1.0)


def test_integrity_availability() -> None:
    geometry = _SCENARIO_GEOMETRY
    available, _ = integrity_availability(geometry, alert_limit_m=556.0)
    assert available is True  # HPL well inside the maritime alert limit
    blocked, _ = integrity_availability(geometry, alert_limit_m=1.0)
    assert blocked is False
    with pytest.raises(ValueError):
        integrity_availability(geometry, alert_limit_m=0.0)
