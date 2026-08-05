"""Tests for pulse-compression waveform analysis (radar counter to stealth)."""

from __future__ import annotations

import numpy as np
import pytest

from tomorrow_never_dies.radar_waveform import (
    BARKER13_CODE,
    WAVEFORM_KINDS,
    Waveform,
    compress,
    generate_waveform,
    peak_sidelobe_ratio,
    processing_gain,
    range_improvement,
    range_resolution,
    waveform_bandwidth,
    waveform_detection_range,
)
from tomorrow_never_dies.stealth_detection import (
    SPEED_OF_LIGHT,
    RadarConfig,
    detection_range,
)

LFM = Waveform(kind="lfm", pulse_width_s=50e-6, bandwidth_hz=10e6, sample_rate_hz=40e6)
UNMOD = Waveform(kind="unmodulated", pulse_width_s=50e-6, sample_rate_hz=1e6)
BARKER = Waveform(kind="barker13", pulse_width_s=13e-6, sample_rate_hz=13e6)


def test_waveform_validation() -> None:
    with pytest.raises(ValueError):
        Waveform(kind="chirp")
    with pytest.raises(ValueError):
        Waveform(pulse_width_s=0.0)
    with pytest.raises(ValueError):
        Waveform(bandwidth_hz=-1.0)
    with pytest.raises(ValueError):
        Waveform(sample_rate_hz=0.0)
    # Nyquist violation: sample rate below 2x effective bandwidth.
    with pytest.raises(ValueError):
        Waveform(kind="lfm", bandwidth_hz=10e6, sample_rate_hz=5e6)


def test_waveform_kinds() -> None:
    assert set(WAVEFORM_KINDS) == {"unmodulated", "lfm", "barker13"}
    assert len(BARKER13_CODE) == 13


def test_bandwidth_and_resolution() -> None:
    assert waveform_bandwidth(UNMOD) == pytest.approx(1 / 50e-6)
    assert waveform_bandwidth(LFM) == pytest.approx(10e6)
    assert waveform_bandwidth(BARKER) == pytest.approx(13 / 13e-6)
    assert range_resolution(LFM) == pytest.approx(SPEED_OF_LIGHT / (2 * 10e6))
    assert range_resolution(UNMOD) == pytest.approx(SPEED_OF_LIGHT * 50e-6 / 2)


def test_processing_gain() -> None:
    assert processing_gain(UNMOD) == pytest.approx(1.0)
    assert processing_gain(LFM) == pytest.approx(500.0)  # B*T
    assert processing_gain(BARKER) == pytest.approx(13.0)


def test_generate_waveform() -> None:
    unmod = generate_waveform(UNMOD)
    assert unmod.size == round(50e-6 * 1e6)
    assert np.allclose(unmod, np.ones(unmod.size, dtype=complex))
    lfm = generate_waveform(LFM)
    assert lfm.size == round(50e-6 * 40e6)
    assert np.allclose(np.abs(lfm), 1.0)  # constant envelope
    barker = generate_waveform(BARKER)
    assert barker.size == round(13e-6 * 13e6)
    assert set(np.unique(barker)) == {1 + 0j, -1 + 0j}
    # Deterministic.
    np.testing.assert_array_equal(lfm, generate_waveform(LFM))
    with pytest.raises(ValueError):
        generate_waveform(Waveform(kind="lfm", pulse_width_s=1e-9, sample_rate_hz=1e6))


def test_compress() -> None:
    waveform = LFM
    signal = generate_waveform(waveform)
    delay = 30
    echo = np.concatenate([np.zeros(delay), signal])
    compressed = compress(echo, signal)
    assert compressed.size == echo.size + signal.size - 1
    # Matched-filter peak sits at (delay + N - 1) in the full convolution.
    assert int(np.argmax(np.abs(compressed))) == delay + signal.size - 1
    with pytest.raises(ValueError):
        compress(np.zeros((2, 2)), signal)
    with pytest.raises(ValueError):
        compress(np.zeros(0), signal)
    with pytest.raises(ValueError):
        compress(signal, np.zeros((2, 2)))


def test_peak_sidelobe_ratio() -> None:
    # Unmodulated pulse has no range sidelobes.
    assert np.isneginf(peak_sidelobe_ratio(UNMOD))
    # LFM sinc sidelobes ~ -13.2 dB; Barker-13 ~ -22.3 dB.
    assert peak_sidelobe_ratio(LFM) == pytest.approx(-13.2, abs=0.6)
    assert peak_sidelobe_ratio(BARKER) == pytest.approx(-22.3, abs=0.6)
    assert peak_sidelobe_ratio(BARKER) < peak_sidelobe_ratio(LFM)


def test_range_improvement() -> None:
    assert range_improvement(UNMOD) == pytest.approx(1.0)
    assert range_improvement(LFM) == pytest.approx(500.0**0.25, rel=1e-6)
    assert range_improvement(BARKER) == pytest.approx(13.0**0.25, rel=1e-6)


def test_waveform_detection_range() -> None:
    cfg = RadarConfig(pulses=4)
    rcs = 0.01
    base = detection_range(rcs, p_fa=1e-6, p_d_target=0.9, config=cfg)
    unmod_range = waveform_detection_range(rcs, UNMOD, config=cfg)
    lfm_range = waveform_detection_range(rcs, LFM, config=cfg)
    # An uncompressed pulse with the same radar config matches the base range.
    assert unmod_range == pytest.approx(base, rel=1e-6)
    # Compression extends the detection range by the fourth root of the gain.
    assert lfm_range > unmod_range
    assert lfm_range / unmod_range == pytest.approx(500.0**0.25, rel=1e-3)
    # More processing gain -> monotonically longer detection range.
    barker_range = waveform_detection_range(rcs, BARKER, config=cfg)
    assert lfm_range > barker_range > unmod_range


def test_generate_waveform_rejects_sub_two_sample_pulse() -> None:
    """A pulse shorter than two samples cannot be compressed at all."""
    waveform = Waveform(
        kind="lfm",
        pulse_width_s=1.0e-7,
        bandwidth_hz=1.0e6,
        sample_rate_hz=2.0e6,
    )
    with pytest.raises(ValueError, match=">= 2 samples"):
        generate_waveform(waveform)


def test_barker13_sidelobe_floor_matches_code_length() -> None:
    """Barker-13's measured floor sits at the theoretical 1/13 (-22.3 dB)."""
    barker = Waveform(
        kind="barker13",
        pulse_width_s=50.0e-6,
        bandwidth_hz=10.0e6,
        sample_rate_hz=40.0e6,
    )
    theoretical = 20.0 * np.log10(1.0 / len(BARKER13_CODE))
    measured = peak_sidelobe_ratio(barker)
    assert processing_gain(barker) == float(len(BARKER13_CODE))
    # Chip quantisation at a finite sample rate keeps the measured floor
    # slightly above the ideal value, never below it.
    assert theoretical <= measured <= theoretical + 0.5
    # And it is a genuinely lower floor than the unweighted LFM sinc.
    lfm = Waveform(
        kind="lfm",
        pulse_width_s=50.0e-6,
        bandwidth_hz=10.0e6,
        sample_rate_hz=40.0e6,
    )
    assert measured < peak_sidelobe_ratio(lfm)


def test_lfm_with_mainlobe_covering_every_lag_reports_no_sidelobes() -> None:
    """When the mainlobe spans the whole response there is nothing left to scan."""
    waveform = Waveform(
        kind="lfm",
        pulse_width_s=4.0e-6,
        bandwidth_hz=1.0e5,
        sample_rate_hz=1.0e6,
    )
    assert peak_sidelobe_ratio(waveform) == float("-inf")
