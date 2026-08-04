"""Low-RCS stealth-vessel detection analysis.

The *Sea Vengeance*, Carver's stealth cruiser, is designed to be nearly
invisible to radar. This module quantifies what that means in radar physics:

* the **radar equation** — received signal-to-noise ratio as a function of
  target radar cross-section (RCS) and range;
* **Neyman–Pearson detection** — a threshold set from a false-alarm
  probability, with detection probability computed exactly for a
  nonfluctuating target via numerical integration of the Marcum Q function,
  and by the closed form for a Swerling-1 fluctuating target;
* **detection range** — the range at which a given RCS meets a target
  detection probability (binary search on the radar equation);
* **stealth penalty metrics** — RCS reduction in dB and the resulting
  detection-range ratio ``(sigma_stealth / sigma_ref)^(1/4)``.

Everything is deterministic (fixed constants, no RNG) and infrastructure-free
(stdlib + numpy only).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "FLUCTUATION_MODELS",
    "RadarConfig",
    "RocCurve",
    "detection_probability",
    "detection_range",
    "detection_range_ratio",
    "rcs_reduction_db",
    "roc_curve",
    "snr_at_range",
    "snr_db",
    "threshold_power",
    "wavelength",
]

#: Boltzmann constant, J/K.
K_BOLTZMANN = 1.380649e-23
#: Speed of light, m/s.
SPEED_OF_LIGHT = 299792458.0
#: Reference noise temperature, K.
REFERENCE_TEMPERATURE_K = 290.0

#: Supported target fluctuation models.
FLUCTUATION_MODELS = ("swerling0", "swerling1")

#: Marcum-Q tail integration parameters (deterministic quadrature).
_MARCUM_SAMPLES = 20000
_MARCUM_TAIL = 40.0


@dataclass(frozen=True)
class RadarConfig:
    """Radar system parameters for the radar equation."""

    peak_power_w: float = 1.0e6
    gain_db: float = 30.0
    frequency_hz: float = 10.0e9
    bandwidth_hz: float = 1.0e6
    noise_figure_db: float = 3.0
    losses_db: float = 6.0
    pulses: int = 1

    def __post_init__(self) -> None:
        for label, value in (
            ("peak_power_w", self.peak_power_w),
            ("gain_db", self.gain_db),
            ("frequency_hz", self.frequency_hz),
            ("bandwidth_hz", self.bandwidth_hz),
            ("noise_figure_db", self.noise_figure_db),
            ("losses_db", self.losses_db),
        ):
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or value <= 0
            ):
                raise ValueError(f"{label} must be a positive number")
        if not isinstance(self.pulses, int) or self.pulses < 1:
            raise ValueError("pulses must be an integer >= 1")


def wavelength(frequency_hz: float) -> float:
    """Electromagnetic wavelength for a frequency in Hz."""
    if (
        not isinstance(frequency_hz, (int, float))
        or isinstance(frequency_hz, bool)
        or frequency_hz <= 0
    ):
        raise ValueError("frequency_hz must be a positive number")
    return SPEED_OF_LIGHT / frequency_hz


def snr_at_range(
    range_m: float,
    rcs_sqm: float,
    *,
    config: RadarConfig | None = None,
) -> float:
    """Linear signal-to-noise ratio from the monostatic radar equation.

    ``SNR = P_t G^2 lambda^2 sigma n_p / ((4 pi)^3 R^4 k T0 B F L)``
    """
    cfg = config or RadarConfig()
    if (
        not isinstance(range_m, (int, float))
        or isinstance(range_m, bool)
        or range_m <= 0
    ):
        raise ValueError("range_m must be a positive number")
    if (
        not isinstance(rcs_sqm, (int, float))
        or isinstance(rcs_sqm, bool)
        or rcs_sqm <= 0
    ):
        raise ValueError("rcs_sqm must be a positive number")
    lam = wavelength(cfg.frequency_hz)
    gain = 10 ** (cfg.gain_db / 10.0)
    noise_factor = 10 ** (cfg.noise_figure_db / 10.0)
    losses = 10 ** (cfg.losses_db / 10.0)
    numerator = cfg.peak_power_w * gain**2 * lam**2 * rcs_sqm * cfg.pulses
    denominator = (
        (4 * np.pi) ** 3
        * range_m**4
        * K_BOLTZMANN
        * REFERENCE_TEMPERATURE_K
        * cfg.bandwidth_hz
        * noise_factor
        * losses
    )
    return float(numerator / denominator)


def snr_db(snr_linear: float) -> float:
    """Convert a linear SNR ratio to dB."""
    if (
        not isinstance(snr_linear, (int, float))
        or isinstance(snr_linear, bool)
        or snr_linear <= 0
    ):
        raise ValueError("snr_linear must be a positive number")
    return float(10.0 * np.log10(snr_linear))


def threshold_power(p_fa: float) -> float:
    """Square-law detector threshold V_T for a false-alarm probability.

    For single-pulse detection against Rayleigh noise: ``P_fa = exp(-V_T)``,
    hence ``V_T = -ln(P_fa)``.
    """
    if (
        not isinstance(p_fa, (int, float))
        or isinstance(p_fa, bool)
        or not 0.0 < p_fa <= 1.0
    ):
        raise ValueError("p_fa must be in (0, 1]")
    return float(-np.log(p_fa))


def _i0e_scaled(values: np.ndarray) -> np.ndarray:
    """Exponentially scaled Bessel ``I0(z) * exp(-z)``, stable for large z.

    Uses ``numpy.i0`` directly below ``z = 100`` (no overflow risk) and the
    three-term asymptotic expansion ``(1 + 1/(8z) + 9/(128 z^2)) / sqrt(2 pi z)``
    above it, where the direct product would overflow.
    """
    z = np.asarray(values, dtype=float)
    result = np.empty_like(z)
    small = z < 100.0
    result[small] = np.i0(z[small]) * np.exp(-z[small])
    large = ~small
    if np.any(large):
        z_large = z[large]
        result[large] = (
            1.0 + 1.0 / (8.0 * z_large) + 9.0 / (128.0 * z_large * z_large)
        ) / np.sqrt(2.0 * np.pi * z_large)
    return result


def marcum_q1(a: float, b: float) -> float:
    """Generalized Marcum Q function Q_1(a, b) via deterministic quadrature.

    Computes the probability that a Rician variate with noncentrality ``a``
    exceeds ``b`` by integrating the Rician tail numerically. The integrand
    is rewritten with the exponentially scaled Bessel function,
    ``x exp(-(x - a)^2 / 2) I0e(a x)``, so it never overflows even for very
    large ``a`` (close-range, high-SNR targets); the quadrature grid is
    peak-adaptive so the unit-width Gaussian mass around ``x = a`` is always
    resolved. Known values: ``Q_1(0, b) = exp(-b^2/2)`` and ``Q_1(a, 0) = 1``.
    """
    if not isinstance(a, (int, float)) or isinstance(a, bool) or a < 0:
        raise ValueError("a must be a non-negative number")
    if not isinstance(b, (int, float)) or isinstance(b, bool) or b < 0:
        raise ValueError("b must be a non-negative number")
    if a <= 50.0:
        upper = max(b + 1.0, a + b + _MARCUM_TAIL)
        grid = np.linspace(b, upper, _MARCUM_SAMPLES)
    else:
        low = max(b, a - 10.0)
        high = a + 10.0
        if high <= low:
            return 0.0  # threshold far beyond the Rician peak: P_d ~ 0
        grid = np.linspace(low, high, _MARCUM_SAMPLES)
    integrand = grid * np.exp(-((grid - a) ** 2) / 2.0) * _i0e_scaled(a * grid)
    return float(np.trapezoid(integrand, grid))


def detection_probability(
    snr: float,
    *,
    p_fa: float = 1e-6,
    pulses: int = 1,
    fluctuation: str = "swerling0",
) -> float:
    """Probability of detection for a target at a given SNR.

    Args:
        snr: Linear SNR (after coherent integration of ``pulses`` pulses).
        p_fa: False-alarm probability setting the threshold.
        pulses: Coherently integrated pulse count (SNR gain is linear).
        fluctuation: ``"swerling0"`` (nonfluctuating, Marcum Q) or
            ``"swerling1"`` (scan-to-scan Rayleigh fluctuation, closed form
            ``P_d = P_fa^(1 / (1 + n_p SNR))``).
    """
    if not isinstance(snr, (int, float)) or isinstance(snr, bool) or snr < 0:
        raise ValueError("snr must be a non-negative number")
    if not isinstance(pulses, int) or pulses < 1:
        raise ValueError("pulses must be an integer >= 1")
    if fluctuation not in FLUCTUATION_MODELS:
        raise ValueError(f"fluctuation must be one of {FLUCTUATION_MODELS}")
    v_t = threshold_power(p_fa)
    total_snr = pulses * snr
    if fluctuation == "swerling0":
        a = float(np.sqrt(2.0 * total_snr))
        b = float(np.sqrt(2.0 * v_t))
        return marcum_q1(a, b)
    return float(p_fa ** (1.0 / (1.0 + total_snr)))


@dataclass(frozen=True)
class RocCurve:
    """A receiver-operating-characteristic curve: P_d as a function of P_fa."""

    p_fa: tuple[float, ...]
    p_d: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.p_fa) != len(self.p_d):
            raise ValueError("p_fa and p_d must have equal length")


def roc_curve(
    range_m: float,
    rcs_sqm: float,
    *,
    p_fa_values: tuple[float, ...] = (1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8),
    config: RadarConfig | None = None,
    fluctuation: str = "swerling0",
) -> RocCurve:
    """Build a deterministic ROC curve at a fixed range and RCS."""
    cfg = config or RadarConfig()
    if (
        not isinstance(range_m, (int, float))
        or isinstance(range_m, bool)
        or range_m <= 0
    ):
        raise ValueError("range_m must be a positive number")
    if (
        not isinstance(rcs_sqm, (int, float))
        or isinstance(rcs_sqm, bool)
        or rcs_sqm <= 0
    ):
        raise ValueError("rcs_sqm must be a positive number")
    if not p_fa_values:
        raise ValueError("p_fa_values must not be empty")
    snr = snr_at_range(range_m, rcs_sqm, config=cfg)
    p_d = tuple(
        detection_probability(snr, p_fa=pf, pulses=cfg.pulses, fluctuation=fluctuation)
        for pf in p_fa_values
    )
    return RocCurve(p_fa=p_fa_values, p_d=p_d)


def detection_range(
    rcs_sqm: float,
    *,
    p_fa: float = 1e-6,
    p_d_target: float = 0.9,
    config: RadarConfig | None = None,
    max_range_m: float = 2.0e6,
) -> float:
    """Range (m) at which a target of the given RCS reaches ``p_d_target``.

    Detection probability is monotonically decreasing in range, so a
    deterministic binary search on the radar equation converges to the
    detection range.
    """
    cfg = config or RadarConfig()
    if (
        not isinstance(rcs_sqm, (int, float))
        or isinstance(rcs_sqm, bool)
        or rcs_sqm <= 0
    ):
        raise ValueError("rcs_sqm must be a positive number")
    if (
        not isinstance(p_d_target, (int, float))
        or isinstance(p_d_target, bool)
        or not 0.0 < p_d_target < 1.0
    ):
        raise ValueError("p_d_target must be in (0, 1)")
    if (
        not isinstance(max_range_m, (int, float))
        or isinstance(max_range_m, bool)
        or max_range_m <= 0
    ):
        raise ValueError("max_range_m must be a positive number")

    def prob_at(r: float) -> float:
        return detection_probability(
            snr_at_range(r, rcs_sqm, config=cfg), p_fa=p_fa, pulses=cfg.pulses
        )

    if prob_at(max_range_m) > p_d_target:
        return max_range_m  # target is detectable beyond the search bound
    low, high = 0.0, max_range_m
    for _ in range(80):
        mid = 0.5 * (low + high)
        if prob_at(mid) > p_d_target:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def rcs_reduction_db(rcs_ref: float, rcs_stealth: float) -> float:
    """Stealth RCS reduction in dB: ``10 log10(sigma_ref / sigma_stealth)``."""
    for label, value in (("rcs_ref", rcs_ref), ("rcs_stealth", rcs_stealth)):
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{label} must be a positive number")
    return float(10.0 * np.log10(rcs_ref / rcs_stealth))


def detection_range_ratio(rcs_ref: float, rcs_stealth: float) -> float:
    """Detection-range ratio for two RCS values (radar-equation fourth root).

    ``R_stealth / R_ref = (sigma_stealth / sigma_ref)^(1/4)`` — the stealth
    hull is detected at this fraction of the reference range.
    """
    for label, value in (("rcs_ref", rcs_ref), ("rcs_stealth", rcs_stealth)):
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{label} must be a positive number")
    return float((rcs_stealth / rcs_ref) ** 0.25)
