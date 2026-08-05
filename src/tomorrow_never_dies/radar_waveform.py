"""Pulse-compression waveform analysis — the radar's counter to stealth.

A low-RCS hull reduces the *reflected* energy, but the radar can claw range
back on the *processing* side: a long modulated pulse carries the same peak
power as a short one while concentrating its energy through pulse
compression. This module implements the three canonical waveforms and their
figures of merit:

* **Unmodulated pulse** — no compression; bandwidth ``1/T``.
* **LFM chirp** — linear frequency modulation over ``T`` seconds and ``B``
  Hz; matched-filter output is the sinc ``|sinc(B tau)|`` envelope with a
  time-bandwidth product ``B*T`` processing gain and ~ -13.2 dB range
  sidelobes (no weighting).
* **Barker-13 phase code** — a 13-chip bi-phase code whose autocorrelation
  is 13 at zero lag and unit at every other lag: -22.3 dB sidelobes, the
  best *uniform* sidelobe floor for a single code.

For each waveform the module computes the matched-filter (pulse-compression)
output, range resolution ``c / (2B)``, processing gain, peak sidelobe ratio,
the fourth-root detection-range improvement, and the actual detection range
of a low-RCS target through the radar equation with the compression gain
treated as coherent integration (consistent with
:mod:`tomorrow_never_dies.stealth_detection`).

Everything is deterministic (the waveforms are pure functions of their
parameters; the FFT-free matched filter is an exact convolution).
Infrastructure-free (stdlib + numpy only, plus the sibling pure module).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from tomorrow_never_dies.stealth_detection import (
    SPEED_OF_LIGHT,
    RadarConfig,
    detection_range,
)

__all__ = [
    "BARKER13_CODE",
    "WAVEFORM_KINDS",
    "Waveform",
    "compress",
    "generate_waveform",
    "peak_sidelobe_ratio",
    "processing_gain",
    "range_improvement",
    "range_resolution",
    "waveform_bandwidth",
    "waveform_detection_range",
]

#: The 13-chip Barker bi-phase code.
BARKER13_CODE: tuple[int, ...] = (1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1)

#: Supported waveform kinds.
WAVEFORM_KINDS = ("unmodulated", "lfm", "barker13")

#: Returned when a waveform has no range sidelobes (unmodulated pulse).
NO_SIDELOBES_DB = float("-inf")


@dataclass(frozen=True)
class Waveform:
    """A radar transmit waveform: kind, duration, bandwidth, sampling."""

    kind: str = "lfm"
    #: Pulse duration in seconds.
    pulse_width_s: float = 50.0e-6
    #: Modulation bandwidth in Hz (used by ``lfm``; effective bandwidth for
    #: the other kinds is derived from the chip/rect structure).
    bandwidth_hz: float = 10.0e6
    #: Complex-baseband sample rate in Hz (>= 2x effective bandwidth).
    sample_rate_hz: float = 40.0e6

    def __post_init__(self) -> None:
        if self.kind not in WAVEFORM_KINDS:
            raise ValueError(f"kind must be one of {WAVEFORM_KINDS}")
        for label, value in (
            ("pulse_width_s", self.pulse_width_s),
            ("bandwidth_hz", self.bandwidth_hz),
            ("sample_rate_hz", self.sample_rate_hz),
        ):
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or value <= 0
            ):
                raise ValueError(f"{label} must be a positive number")
        if self.sample_rate_hz < 2.0 * waveform_bandwidth(self):
            raise ValueError(
                "sample_rate_hz must be >= 2x the effective bandwidth (Nyquist)"
            )


def waveform_bandwidth(waveform: Waveform) -> float:
    """Effective bandwidth (Hz) of a waveform.

    Unmodulated: ``1/T`` (the rect spectrum nulls). LFM: the modulation
    bandwidth ``B``. Barker-13: the chip rate ``13/T``.
    """
    if waveform.kind == "unmodulated":
        return 1.0 / waveform.pulse_width_s
    if waveform.kind == "lfm":
        return waveform.bandwidth_hz
    return 13.0 / waveform.pulse_width_s


def range_resolution(waveform: Waveform) -> float:
    """Range resolution ``c / (2B)`` in meters after compression."""
    return float(SPEED_OF_LIGHT / (2.0 * waveform_bandwidth(waveform)))


def processing_gain(waveform: Waveform) -> float:
    """Coherent processing gain of the waveform (dimensionless).

    Unmodulated: 1 (no compression). LFM: the time-bandwidth product ``B*T``.
    Barker-13: the code length 13.
    """
    if waveform.kind == "unmodulated":
        return 1.0
    if waveform.kind == "lfm":
        return float(waveform.bandwidth_hz * waveform.pulse_width_s)
    return 13.0


def generate_waveform(waveform: Waveform) -> np.ndarray:
    """Complex baseband samples of the waveform (deterministic)."""
    n_samples = round(waveform.pulse_width_s * waveform.sample_rate_hz)
    if n_samples < 2:
        raise ValueError("pulse_width_s * sample_rate_hz must yield >= 2 samples")
    if waveform.kind == "unmodulated":
        return np.ones(n_samples, dtype=complex)
    time = (np.arange(n_samples) - (n_samples - 1) / 2.0) / waveform.sample_rate_hz
    if waveform.kind == "lfm":
        chirp_rate = waveform.bandwidth_hz / waveform.pulse_width_s
        return np.exp(1j * np.pi * chirp_rate * time**2).astype(complex)
    chip_samples = int(np.ceil(n_samples / 13))
    chips = np.repeat(np.asarray(BARKER13_CODE, dtype=float), chip_samples)
    return chips[:n_samples].astype(complex)


def compress(received: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Matched-filter (pulse-compression) output via exact convolution.

    ``y = convolve(received, conj(reference[::-1]))`` — the time-reversed,
    conjugated reference is the matched filter for ``reference``. The output
    is the full convolution, so its peak marks the target's delay.
    """
    received_arr = np.asarray(received)
    reference_arr = np.asarray(reference)
    if received_arr.ndim != 1 or reference_arr.ndim != 1:
        raise ValueError("received and reference must be 1-D arrays")
    if received_arr.size == 0 or reference_arr.size == 0:
        raise ValueError("received and reference must not be empty")
    return np.convolve(received_arr, np.conj(reference_arr[::-1]))


def _mainlobe_half_width(waveform: Waveform) -> int:
    """Half-width (in lags) of the compressed mainlobe, for sidelobe scans."""
    if waveform.kind == "lfm":
        return max(1, round(waveform.sample_rate_hz / waveform_bandwidth(waveform)))
    return 1  # barker13: the mainlobe is the zero lag only


def peak_sidelobe_ratio(waveform: Waveform) -> float:
    """Peak sidelobe ratio of the compressed pulse, in dB.

    Ratio of the largest range sidelobe to the mainlobe peak of the
    waveform's matched-filter autocorrelation. The LFM chirp is scanned at
    sample resolution (sinc envelope, ~ -13.2 dB); the Barker-13 code is
    scanned at chip resolution (its code sidelobes lie at multiples of the
    chip duration, ~ -22.3 dB). An unmodulated pulse has no range sidelobes
    and returns ``-inf`` dB.
    """
    samples = generate_waveform(waveform)
    if waveform.kind == "unmodulated":
        return NO_SIDELOBES_DB
    compressed = np.abs(compress(samples, samples))
    peak = float(np.max(compressed))
    center = int(np.argmax(compressed))
    if waveform.kind == "lfm":
        half = _mainlobe_half_width(waveform)
        left = compressed[: max(0, center - half)]
        right = compressed[center + half + 1 :]
        sidelobes = np.concatenate((left, right))
    else:
        # Barker-13: measure at chip multiples (the code's true sidelobe lags).
        chip = max(1, round(waveform.sample_rate_hz * (waveform.pulse_width_s / 13.0)))
        lags = [
            float(compressed[center + k * chip])
            for k in range(1, compressed.size // chip + 1)
            if center + k * chip < compressed.size
        ]
        sidelobes = np.asarray(lags)
    if sidelobes.size == 0 or float(np.max(sidelobes)) <= 0.0:
        return NO_SIDELOBES_DB
    return float(20.0 * np.log10(float(np.max(sidelobes)) / peak))


def range_improvement(waveform: Waveform) -> float:
    """Detection-range improvement factor over an unmodulated pulse.

    The radar equation's fourth root: range scales as
    ``(processing_gain)^(1/4)`` for the same peak power.
    """
    return float(processing_gain(waveform) ** 0.25)


def waveform_detection_range(
    rcs_sqm: float,
    waveform: Waveform,
    *,
    config: RadarConfig | None = None,
    p_fa: float = 1e-6,
    p_d_target: float = 0.9,
    max_range_m: float = 2.0e6,
) -> float:
    """Detection range (m) of a target when the waveform's compression gain
    is treated as coherent integration.

    The effective pulse count is ``config.pulses * processing_gain``, so the
    range follows the radar equation exactly as in
    :func:`stealth_detection.detection_range`.
    """
    cfg = config or RadarConfig()
    gain = processing_gain(waveform)
    effective_pulses = max(1, round(cfg.pulses * gain))
    compressed_cfg = replace(cfg, pulses=effective_pulses)
    return detection_range(
        rcs_sqm,
        p_fa=p_fa,
        p_d_target=p_d_target,
        config=compressed_cfg,
        max_range_m=max_range_m,
    )
