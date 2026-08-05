"""GNSS integrity — Receiver Autonomous Integrity Monitoring (RAIM).

Carver can deny navigation not only by jamming the signal but by corrupting
it (spoofing) so a receiver quietly computes a wrong position. RAIM is the
receiver-side safeguard: it uses the redundancy of the satellite
constellation to detect a faulty measurement and bound the resulting position
error. This module implements the baseline RAIM algorithm in full:

* **Statistical core** — the chi-square CDF (regularized lower incomplete
  gamma, series form) and its quantile inverse (bisection), plus the normal
  CDF/quantile needed for protection-level margins. Scipy-free and
  deterministic.
* **Parity space** — the orthogonal projection onto the (n-4)-dimensional
  parity space, built from the full SVD of the geometry matrix (its trailing
  left singular vectors span the left null space); a fault drives the parity
  residual away from zero.
* **Detection** — the RAIM test statistic, a threshold from the chi-square
  distribution at a target false-alarm rate, and the probability of detecting
  a measurement bias of a given size (noncentral chi-square, Poisson-series).
* **Protection levels** — horizontal and vertical protection levels (HPL/VPL)
  built from the worst-case fault slope and the missed-detection margin, and
  an integrity-availability check against an alert limit.

All randomness is absent; the module is infrastructure-free (stdlib + numpy,
plus the sibling geometry helpers).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

__all__ = [
    "ProtectionLevels",
    "chi_square_cdf",
    "chi_square_ppf",
    "detection_probability",
    "integrity_availability",
    "least_squares_position",
    "noncentral_chi2_cdf",
    "normal_cdf",
    "normal_ppf",
    "parity_matrix",
    "protection_levels",
    "raim_threshold",
    "slopes",
    "test_statistic",
]

#: Inverse-normal bisection bracket.
_NORMAL_LO, _NORMAL_HI = -8.2, 8.2
#: Chi-square quantile bisection bracket upper bound (dof-scaled).
_CHI_SQ_HI_SCALE = 12.0
_CHI_SQ_HI_OFFSET = 60.0
#: Series/space convergence thresholds.
_GAMMA_TOL = 1e-15
_GAMMA_MAX_TERMS = 1000
_POISSON_TOL = 1e-12
_POISSON_MAX_K = 3000


@dataclass(frozen=True)
class ProtectionLevels:
    """RAIM horizontal/vertical protection levels plus the detection setup."""

    hpl: float
    vpl: float
    threshold: float
    dof: int


def normal_cdf(z: float) -> float:
    """Standard normal CDF (scipy-free, via ``math.erf``)."""
    if not isinstance(z, (int, float)) or isinstance(z, bool):
        raise ValueError("z must be a number")
    return float(0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))


def normal_ppf(p: float) -> float:
    """Standard normal quantile (bisection on :func:`normal_cdf`)."""
    if not isinstance(p, (int, float)) or isinstance(p, bool) or not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    low, high = _NORMAL_LO, _NORMAL_HI
    for _ in range(120):
        mid = 0.5 * (low + high)
        if normal_cdf(mid) < p:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def chi_square_cdf(x: float, dof: int) -> float:
    """Chi-square CDF with ``dof`` degrees of freedom.

    Computed as the regularized lower incomplete gamma ``P(dof/2, x/2)`` via
    its convergent series.
    """
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x < 0:
        raise ValueError("x must be a non-negative number")
    if not isinstance(dof, int) or dof < 1:
        raise ValueError("dof must be an integer >= 1")
    if x == 0.0:
        return 0.0
    a = dof / 2.0
    y = x / 2.0
    log_prefix = a * math.log(y) - y - math.lgamma(a)
    prefix = math.exp(log_prefix)
    term = 1.0 / a  # k=0 of the series y^k / (a)_(k+1)
    total = 0.0
    for k in range(_GAMMA_MAX_TERMS):
        total += term
        if k >= 1 and abs(term) < _GAMMA_TOL * abs(total):
            break
        term *= y / (a + k + 1)
    return float(min(1.0, max(0.0, prefix * total)))


def chi_square_ppf(p: float, dof: int) -> float:
    """Chi-square quantile (bisection on :func:`chi_square_cdf`)."""
    if not isinstance(p, (int, float)) or isinstance(p, bool) or not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    if not isinstance(dof, int) or dof < 1:
        raise ValueError("dof must be an integer >= 1")
    high = dof + _CHI_SQ_HI_SCALE * math.sqrt(dof) + _CHI_SQ_HI_OFFSET
    low = 0.0
    for _ in range(200):
        mid = 0.5 * (low + high)
        if chi_square_cdf(mid, dof) < p:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def parity_matrix(geometry: np.ndarray) -> np.ndarray:
    """Orthogonal projection into parity space (rows span the fault space).

    Given the ``n x 4`` geometry matrix (n > 4), the last ``(n-4)`` left
    singular vectors span its left null space (the parity space). The parity
    matrix ``P`` is the ``(n-4) x n`` matrix with orthonormal rows and
    ``P @ G = 0``. Built from the full SVD, which is robust and deterministic
    in numpy (unlike ``mode=\"complete\"`` QR, whose reduced-Q shape varies).
    """
    array = np.asarray(geometry, dtype=float)
    if array.ndim != 2 or array.shape[1] != 4 or array.shape[0] <= 4:
        raise ValueError("geometry must be an n x 4 matrix with n > 4")
    u_matrix, _, _ = np.linalg.svd(array, full_matrices=True)
    return u_matrix[:, 4:].T


def least_squares_position(
    geometry: np.ndarray, measurements: np.ndarray
) -> np.ndarray:
    """Least-squares position/time solution from the geometry and ranges."""
    array = np.asarray(geometry, dtype=float)
    meas = np.asarray(measurements, dtype=float)
    if array.ndim != 2 or array.shape[1] != 4 or array.shape[0] < 4:
        raise ValueError("geometry must be an n x 4 matrix with n >= 4")
    if meas.shape != (array.shape[0],):
        raise ValueError("measurements must have one value per geometry row")
    return np.linalg.pinv(array) @ meas


def test_statistic(
    measurements: np.ndarray,
    geometry: np.ndarray,
    position: np.ndarray,
    sigma: float = 3.0,
) -> float:
    """Normalized RAIM test statistic ``||P (y - G x)||^2 / sigma^2``.

    Fault-free this is drawn from a chi-square distribution with
    ``n - 4`` degrees of freedom; a measurement bias inflates it.
    """
    array = np.asarray(geometry, dtype=float)
    meas = np.asarray(measurements, dtype=float)
    pos = np.asarray(position, dtype=float)
    if isinstance(sigma, bool) or not isinstance(sigma, (int, float)) or sigma <= 0:
        raise ValueError("sigma must be a positive number")
    residual = meas - array @ pos
    p_matrix = parity_matrix(array)
    return float(np.sum((p_matrix @ residual) ** 2)) / float(sigma) ** 2


def raim_threshold(dof: int, p_fa: float) -> float:
    """Detection threshold on the test statistic for a false-alarm rate.

    ``T_thr = chi2_ppf(1 - p_fa, n - 4)``.
    """
    if not isinstance(dof, int) or dof < 1:
        raise ValueError("dof must be an integer >= 1")
    if (
        not isinstance(p_fa, (int, float))
        or isinstance(p_fa, bool)
        or not 0.0 < p_fa < 1.0
    ):
        raise ValueError("p_fa must be in (0, 1)")
    return chi_square_ppf(1.0 - p_fa, dof)


def slopes(geometry: np.ndarray) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Per-satellite horizontal and vertical fault slopes.

    ``slope_h[i] = sqrt(A_1i^2 + A_2i^2) / sqrt(P_ii)`` and
    ``slope_v[i] = |A_3i| / sqrt(P_ii)``, where ``A`` is the position
    projection and ``P_ii`` the parity row norm. The worst slope bounds how
    large a position error a just-threshold fault can hide.
    """
    array = np.asarray(geometry, dtype=float)
    n_rows = array.shape[0]
    if array.ndim != 2 or array.shape[1] != 4 or n_rows <= 4:
        raise ValueError("geometry must be an n x 4 matrix with n > 4")
    a_matrix = np.linalg.pinv(array)
    p_matrix = parity_matrix(array)
    # P_ii = diag(P^T P) = squared column norm of P.
    p_norm2 = np.einsum("ij,ij->j", p_matrix, p_matrix)
    horizontal = [
        float(
            math.sqrt(float(a_matrix[0, i]) ** 2 + float(a_matrix[1, i]) ** 2)
            / math.sqrt(float(p_norm2[i]))
        )
        for i in range(n_rows)
    ]
    vertical = [
        float(abs(float(a_matrix[2, i])) / math.sqrt(float(p_norm2[i])))
        for i in range(n_rows)
    ]
    return tuple(horizontal), tuple(vertical)


def protection_levels(
    geometry: np.ndarray,
    *,
    p_fa: float = 1e-5,
    p_md: float = 1e-3,
    sigma: float = 3.0,
) -> ProtectionLevels:
    """Horizontal/vertical protection levels for the given geometry.

    ``HPL = max(slope_h) * sqrt(T_thr) * sigma + k_md * sigma_h`` where
    ``sigma_h`` is the fault-free horizontal position error and ``k_md =
    normal_ppf(1 - p_md)`` accounts for the missed-detection margin.
    """
    array = np.asarray(geometry, dtype=float)
    n_rows = array.shape[0]
    if array.ndim != 2 or array.shape[1] != 4 or n_rows <= 4:
        raise ValueError("geometry must be an n x 4 matrix with n > 4")
    for label, value in (
        ("p_fa", p_fa),
        ("p_md", p_md),
    ):
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not 0.0 < value < 1.0
        ):
            raise ValueError(f"{label} must be in (0, 1)")
    if isinstance(sigma, bool) or not isinstance(sigma, (int, float)) or sigma <= 0:
        raise ValueError("sigma must be a positive number")

    dof = n_rows - 4
    threshold = raim_threshold(dof, p_fa)
    horizontal_slopes, vertical_slopes = slopes(array)
    q_matrix = np.linalg.inv(array.T @ array)
    sigma_h = sigma * math.sqrt(float(q_matrix[0, 0] + q_matrix[1, 1]))
    sigma_v = sigma * math.sqrt(float(q_matrix[2, 2]))
    k_md = normal_ppf(1.0 - p_md)
    root = math.sqrt(threshold) * sigma
    hpl = max(horizontal_slopes) * root + k_md * sigma_h
    vpl = max(vertical_slopes) * root + k_md * sigma_v
    return ProtectionLevels(
        hpl=float(hpl), vpl=float(vpl), threshold=float(threshold), dof=dof
    )


def noncentral_chi2_cdf(x: float, dof: int, noncentrality: float) -> float:
    """Noncentral chi-square CDF via the Poisson-weighted central series.

    ``X ~ chi2'(dof, nc)`` mixes central chi-squares with dof + 2k degrees of
    freedom weighted by a Poisson(nc/2) distribution.
    """
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x < 0:
        raise ValueError("x must be a non-negative number")
    if not isinstance(dof, int) or dof < 1:
        raise ValueError("dof must be an integer >= 1")
    if (
        not isinstance(noncentrality, (int, float))
        or isinstance(noncentrality, bool)
        or noncentrality < 0
    ):
        raise ValueError("noncentrality must be a non-negative number")

    total = 0.0
    poisson_weight = math.exp(-noncentrality / 2.0)
    weight = poisson_weight
    for k in range(_POISSON_MAX_K):
        total += weight * chi_square_cdf(x, dof + 2 * k)
        if k >= 1 and weight < _POISSON_TOL * total:
            break
        weight *= (noncentrality / 2.0) / (k + 1)
    return float(min(1.0, max(0.0, total)))


def detection_probability(
    bias_m: float,
    *,
    dof: int,
    p_fa: float,
    sigma: float = 3.0,
) -> float:
    """Probability of detecting a measurement bias of ``bias_m`` meters.

    The parity projection preserves the norm of a single-satellite bias, so
    the test statistic under a fault ``b`` is noncentral chi-square with
    noncentrality ``(b / sigma)^2``; ``P_d = 1 - F_nc(T_thr)``.
    """
    if isinstance(bias_m, bool) or not isinstance(bias_m, (int, float)) or bias_m < 0:
        raise ValueError("bias_m must be a non-negative number")
    if not isinstance(dof, int) or dof < 1:
        raise ValueError("dof must be an integer >= 1")
    if (
        not isinstance(p_fa, (int, float))
        or isinstance(p_fa, bool)
        or not 0.0 < p_fa < 1.0
    ):
        raise ValueError("p_fa must be in (0, 1)")
    if isinstance(sigma, bool) or not isinstance(sigma, (int, float)) or sigma <= 0:
        raise ValueError("sigma must be a positive number")
    threshold = raim_threshold(dof, p_fa)
    noncentrality = float(bias_m / sigma) ** 2
    return float(1.0 - noncentral_chi2_cdf(threshold, dof, noncentrality))


def integrity_availability(
    geometry: np.ndarray,
    *,
    p_fa: float = 1e-5,
    p_md: float = 1e-3,
    sigma: float = 3.0,
    alert_limit_m: float = 556.0,
) -> tuple[bool, ProtectionLevels]:
    """Whether HPL stays within the alert limit (integrity available).

    Returns ``(available, protection_levels)``. A 0.3 NM (``556 m``) alert
    limit is the default, matching a maritime non-precision approach margin.
    """
    levels = protection_levels(geometry, p_fa=p_fa, p_md=p_md, sigma=sigma)
    if (
        isinstance(alert_limit_m, bool)
        or not isinstance(alert_limit_m, (int, float))
        or alert_limit_m <= 0
    ):
        raise ValueError("alert_limit_m must be a positive number")
    return levels.hpl <= alert_limit_m, levels
