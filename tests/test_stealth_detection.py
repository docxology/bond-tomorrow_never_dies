"""Tests for the low-RCS stealth detection analysis.

Zero mocks: detection probabilities come from the real Marcum-Q quadrature
and Swerling closed forms; ranges come from binary search on the radar
equation.
"""

from __future__ import annotations

import numpy as np
import pytest

from tomorrow_never_dies.stealth_detection import (
    FLUCTUATION_MODELS,
    RadarConfig,
    RocCurve,
    detection_probability,
    detection_range,
    detection_range_ratio,
    marcum_q1,
    rcs_reduction_db,
    roc_curve,
    snr_at_range,
    snr_db,
    threshold_power,
    wavelength,
)


def test_wavelength() -> None:
    assert wavelength(1.0e9) == pytest.approx(0.299792458)


def test_snr_at_range_monotonic() -> None:
    snr_10 = snr_at_range(10.0e3, 1.0)
    snr_20 = snr_at_range(20.0e3, 1.0)
    assert snr_10 > snr_20
    # Fourth power law: doubling the range divides SNR by 16.
    assert snr_10 / snr_20 == pytest.approx(16.0, rel=1e-6)
    # Linear in RCS.
    assert snr_at_range(10.0e3, 2.0) / snr_10 == pytest.approx(2.0, rel=1e-6)


def test_snr_at_range_default_config() -> None:
    cfg = RadarConfig()
    assert snr_at_range(50.0e3, 1.0) == pytest.approx(
        snr_at_range(50.0e3, 1.0, config=cfg)
    )


def test_snr_db() -> None:
    assert snr_db(100.0) == pytest.approx(20.0)


def test_threshold_power() -> None:
    assert threshold_power(np.exp(-1)) == pytest.approx(1.0)
    for bad in (0.0, 1.5, -0.1):
        with pytest.raises(ValueError):
            threshold_power(bad)


def test_marcum_known_values() -> None:
    assert marcum_q1(0.0, 1.0) == pytest.approx(np.exp(-0.5), rel=1e-3)
    assert marcum_q1(2.0, 0.0) == pytest.approx(1.0, abs=1e-4)
    # Large-a (close-range, high-SNR) stability: finite, ~1.
    large = marcum_q1(1.0e4, 0.5)
    assert np.isfinite(large)
    assert 0.999 < large <= 1.0
    with pytest.raises(ValueError):
        marcum_q1(-1.0, 1.0)
    with pytest.raises(ValueError):
        marcum_q1(1.0, -1.0)


def test_detection_probability_floor() -> None:
    # At zero SNR, detection probability equals the false-alarm rate.
    assert detection_probability(0.0, p_fa=1e-4) == pytest.approx(1e-4, rel=1e-3)
    assert detection_probability(
        0.0, p_fa=1e-4, fluctuation="swerling1"
    ) == pytest.approx(1e-4, rel=1e-6)


def test_detection_probability_monotone() -> None:
    values = [detection_probability(s) for s in (0.5, 2.0, 8.0, 32.0)]
    assert all(values[i] < values[i + 1] for i in range(len(values) - 1))
    assert all(0.0 <= value <= 1.0 for value in values)


def test_detection_probability_swerling1_closed_form() -> None:
    # P_d = P_fa^(1 / (1 + n_p * SNR)).
    expected = (1e-6) ** (1.0 / 3.0)
    assert detection_probability(
        1.0, p_fa=1e-6, pulses=2, fluctuation="swerling1"
    ) == pytest.approx(expected)


def test_detection_probability_integration_gain() -> None:
    single = detection_probability(2.0, p_fa=1e-6, pulses=1)
    integrated = detection_probability(0.5, p_fa=1e-6, pulses=4)  # same total SNR
    assert integrated == pytest.approx(single, rel=1e-3)


def test_detection_probability_errors() -> None:
    with pytest.raises(ValueError):
        detection_probability(-1.0)
    with pytest.raises(ValueError):
        detection_probability(1.0, pulses=0)
    with pytest.raises(ValueError):
        detection_probability(1.0, fluctuation="swerling5")


def test_roc_curve() -> None:
    curve = roc_curve(30.0e3, 0.1)
    assert len(curve.p_fa) == len(curve.p_d)
    # Stricter false-alarm rate lowers detection probability.
    assert all(curve.p_d[i] > curve.p_d[i + 1] for i in range(len(curve.p_d) - 1))
    assert all(0.0 <= probability <= 1.0 for probability in curve.p_d)


def test_roc_curve_errors() -> None:
    with pytest.raises(ValueError):
        roc_curve(0.0, 1.0)
    with pytest.raises(ValueError):
        roc_curve(30.0e3, -1.0)
    with pytest.raises(ValueError):
        roc_curve(30.0e3, 1.0, p_fa_values=())
    with pytest.raises(ValueError):
        RocCurve(p_fa=(1e-3,), p_d=(0.5, 0.6))


def test_detection_range_stealth_penalty() -> None:
    ref = detection_range(1.0)
    stealth = detection_range(0.01)
    assert ref > stealth
    # Fourth-root law: range scales as RCS^(1/4).
    assert stealth / ref == pytest.approx((0.01) ** 0.25, rel=1e-3)
    # Recompute P_d at the returned range: it should equal the target.
    probability = detection_probability(
        snr_at_range(ref, 1.0), p_fa=1e-6, pulses=RadarConfig().pulses
    )
    assert probability == pytest.approx(0.9, abs=1e-2)


def test_detection_range_errors() -> None:
    with pytest.raises(ValueError):
        detection_range(0.0)
    with pytest.raises(ValueError):
        detection_range(1.0, p_d_target=1.0)
    with pytest.raises(ValueError):
        detection_range(1.0, p_d_target=0.0)
    with pytest.raises(ValueError):
        detection_range(1.0, max_range_m=-5.0)


def test_rcs_metrics() -> None:
    assert rcs_reduction_db(1.0, 0.01) == pytest.approx(20.0)
    assert detection_range_ratio(1.0, 0.01) == pytest.approx(0.316227766, rel=1e-6)
    with pytest.raises(ValueError):
        rcs_reduction_db(0.0, 1.0)
    with pytest.raises(ValueError):
        detection_range_ratio(1.0, -1.0)


def test_radar_config_validation() -> None:
    with pytest.raises(ValueError):
        RadarConfig(peak_power_w=0.0)
    with pytest.raises(ValueError):
        RadarConfig(pulses=0)
    with pytest.raises(ValueError):
        RadarConfig(frequency_hz=-1.0)


def test_fluctuation_models() -> None:
    assert set(FLUCTUATION_MODELS) == {"swerling0", "swerling1"}
