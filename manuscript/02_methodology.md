# Methodology

Each concept is a self-contained deterministic model with clear physical or
algorithmic grounding.

## Disinformation propagation

Agents occupy one of two belief states — susceptible or believing — on a
Watts–Strogatz small-world network of {{MEDIA_NODES}} nodes (seed
{{CARVER_SEED}}). The broadcast footprint — the {{MEDIA_REACH_PCT}}% of nodes the
media channel reaches — is selected by a deterministic index mix rather than
an RNG draw, so it is a pure function of network size, reach, and seed, and
widening the reach only ever *adds* nodes to the exposed set.
`simulate_disinformation`
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
{{WAVEFORM_PSLR_DB}} dB), and the Barker-13 phase code (gain
{{WAVEFORM_BARKER_GAIN}}x, measured sidelobe floor {{WAVEFORM_BARKER_PSLR_DB}} dB —
the code's autocorrelation is 13 at zero lag and unity elsewhere, the best
uniform sidelobe floor known for a single binary code, with the measured
value sitting just above the ideal ``20 log10(1/13)`` because a finite sample
rate quantizes the chip boundaries). The matched filter is an exact
convolution; the compression gain is treated as coherent integration *and*
the receiver noise bandwidth is set to the waveform's own bandwidth, which
together reduce the budget to matched-filter energy ``P_t T / N_0``. Both
substitutions are needed: banking the ``B·T`` gain against the radar's
narrower surveillance noise bandwidth would credit the gain twice.
Consequently a modulated and an unmodulated pulse of *equal duration* have
equal detection range, and the reported recovery
(`waveform_detection_range`) is measured against an unmodulated pulse of
equal range *resolution* — duration {{WAVEFORM_UNMOD_WIDTH_US}} µs — where
the fourth-root law ``R ∝ gain^(1/4)`` applies.

## GPS-denial impact

`gps_denial.py` builds a Walker-delta constellation as orbital geometry —
{{GPS_SATELLITES}} satellites split evenly across {{GPS_PLANES}} inclined
circular planes, propagated to Earth-centred positions and projected into the
receiver's east/north/up frame — so azimuth and elevation are derived, not
drawn, and only the {{GPS_VISIBLE_SATS}} satellites geometrically in view
above the {{GPS_MASK_ANGLE_DEG}}° mask enter the geometry matrix and the
dilution of precision. It then quantifies jamming degradation of
carrier-to-noise into position-error growth (``PDOP * UERE``).

That growth has a validity boundary, and the canonical scenario sits on the
wrong side of it. At the {{GPS_JAMMER_STANDOFF_KM}} km standoff the effective
C/N0 falls from {{GPS_CNO_CLEAN_DBHZ}} to {{GPS_CNO_JAMMED_DBHZ}} dB-Hz —
still positive, but far below the {{GPS_LOCK_THRESHOLD_DBHZ}} dB-Hz a C/A
receiver needs to hold carrier lock. `maintains_lock` reports that verdict
explicitly rather than leaving it implicit in a smooth curve. The honest
reading is therefore *denial*: a real receiver stops producing a solution,
and the {{GPS_ERROR_JAMMED_M}} m quoted in the results is what the
code-tracking formula extrapolates past its own validity, not an accuracy a
receiver would report. @fig:gps shades that region for the same reason and
extends to 2000 km so the standoff at which lock returns is visible.
Loss of navigation, not degraded navigation, is what
`simulate_navigation_cascade` then propagates across the maritime dependency
network until a fixpoint.

## GNSS integrity (RAIM)

`gnss_integrity.py` implements Receiver Autonomous Integrity Monitoring: a
scipy-free chi-square CDF/quantile (regularized incomplete gamma, series) and
normal quantile; the parity matrix built from the full SVD of the geometry
matrix; a test statistic and detection threshold at a target false-alarm
rate; per-satellite fault slopes; and horizontal/vertical protection levels
(HPL/VPL) with a missed-detection margin. `detection_probability` reports the
probability of catching a measurement bias of a given size via the noncentral
chi-square. The parity projection is *not* norm-preserving: a bias ``b`` on
satellite ``i`` lands in parity space with squared length ``P_ii b²``, where
``P_ii ≤ 1`` is that satellite's projection factor
(`parity_projection_factors`, summing to the ``n − 4`` degrees of freedom).
The noncentrality is therefore ``P_ii (b/σ)²`` and detection probability
depends on *which* satellite is faulted, so `detection_probability` requires
the factor as an argument rather than defaulting to one. The reported figure
is the worst-placed satellite, matching the worst-slope convention the
protection levels already use.
