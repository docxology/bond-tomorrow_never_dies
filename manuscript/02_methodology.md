# Methodology

Each concept is a self-contained deterministic model with clear physical or
algorithmic grounding.

## Disinformation propagation

Agents occupy one of three belief states — unaware, susceptible, or believing —
on a Watts–Strogatz small-world network of {{MEDIA_NODES}} nodes (seed
{{CARVER_SEED}}). `simulate_disinformation`
(`src/tomorrow_never_dies/media_manipulation.py`) converts susceptible agents
through a media channel (a deterministic exposed subset converts with a
persuasion probability) and a social channel (believing agents convert
susceptible neighbors). Belief share, the echo-chamber coefficient, and the
amplification factor are recorded; `influence_maximization` applies a greedy
Kempe–Kleinberg–Tardos seed selection.

## Narrative control (bounded confidence)

`narrative_control.py` models *how strongly* opinions move, using the
Hegselmann–Krause bounded-confidence model with a Carver-style media
injection term. Each round agent ``i`` moves to the mean opinion of the agents
within confidence radius ``epsilon``, and exposed agents are additionally
pulled toward the manufactured line ``m`` with a media weight. `simulate_opinions`
returns the final consensus, the opinion variance (polarization), the bimodal
split (fraction of agent pairs separated by more than ``2 * epsilon`` — a
measure of echo-chamber fragmentation), and the media capture (the normalized
shift of the mean toward the manufactured line versus a no-media baseline).
`critical_media_reach` bisects the broadcast reach that just tips the discrete
belief model to a target share: the *minimum* audience Carver must reach.

## Stealth-vessel detection

`stealth_detection.py` evaluates the monostatic radar equation
`snr_at_range`: \begin{equation} \mathrm{SNR} = \frac{P_t G^2 \lambda^2 \sigma}{(4\pi)^3 R^4 k T_0 B F L}, \end{equation}
yielding the per-pulse SNR (coherent integration is applied by
`detection_probability`). A false-alarm probability sets a square-law
threshold; `detection_probability` returns $P_d$ by numerically integrating
the Marcum Q function (Swerling 0) or the closed form (Swerling 1).
`detection_range` binary-searches the range at which $P_d$ reaches a target.

## Pulse compression (waveform design)

`radar_waveform.py` analyzes the radar's *counter* to stealth: a modulated
pulse concentrates its energy through pulse compression. Three waveforms are
implemented — unmodulated (gain 1), the LFM chirp (time-bandwidth product
{{WAVEFORM_BANDWIDTH_MHZ}} MHz-bandwidth, processing gain {{WAVEFORM_GAIN_DB}} dB,
range resolution {{WAVEFORM_RES_M}} m, and the sinc sidelobe floor of
{{WAVEFORM_PSLR_DB}} dB), and the Barker-13 phase code (uniform -22.3 dB
sidelobes). The matched filter is an exact convolution; the resulting
compression gain is treated as coherent integration, so the detection range
of a low-RCS target follows the fourth-root law
``R ∝ gain^(1/4)`` (`waveform_detection_range`).

## GPS-denial impact

`gps_denial.py` builds a deterministic Walker-style constellation, computes the
geometry matrix and dilution of precision, and quantifies jamming degradation
of carrier-to-noise (which pushes effective C/N0 negative) into position-error
growth (``PDOP * UERE``). `simulate_navigation_cascade` then propagates failure
across a maritime dependency network until a fixpoint.

## GNSS integrity (RAIM)

`gnss_integrity.py` implements Receiver Autonomous Integrity Monitoring: a
scipy-free chi-square CDF/quantile (regularized incomplete gamma, series) and
normal quantile; the parity matrix built from the full SVD of the geometry
matrix; a test statistic and detection threshold at a target false-alarm
rate; per-satellite fault slopes; and horizontal/vertical protection levels
(HPL/VPL) with a missed-detection margin. `detection_probability` reports the
probability of catching a measurement bias of a given size via the noncentral
chi-square.
