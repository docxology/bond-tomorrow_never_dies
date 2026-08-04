# Methodology

Each concept is a self-contained deterministic model with clear physical or
algorithmic grounding.

## Disinformation propagation

Agents occupy one of three belief states — unaware, susceptible, or believing —
on a Watts–Strogatz small-world network of {{MEDIA_NODES}} nodes (seed
{{CARVER_SEED}}). Two channels convert susceptible agents to believers each
round `simulate_disinformation` (`src/tomorrow_never_dies/media_manipulation.py`):

* **Media channel**: a deterministic subset of nodes (the campaign reach) is
  exposed; each susceptible exposed node converts with probability
  *persuasion*.
* **Social channel**: every believing node converts each susceptible neighbor
  with probability *spread rate*.

Belief share is recorded after every round. `influence_maximization` applies
a greedy Kempe–Kleinberg–Tardos selection to choose the seed nodes that
maximise the final belief share. The echo-chamber coefficient measures
whether believers find themselves among believers; the amplification factor
compares final believers to the directly exposed audience.

## Stealth-vessel detection

`stealth_detection.py` evaluates the monostatic radar equation
`snr_at_range`: \begin{equation} \mathrm{SNR} = \frac{P_t G^2 \lambda^2 \sigma n_p}{(4\pi)^3 R^4 k T_0 B F L}, \end{equation}
where $\sigma$ is the radar cross-section and $R$ the range. A false-alarm
probability sets a square-law threshold; `detection_probability` returns the
probability of detection $P_d$ either by numerically integrating the Marcum Q
function (Swerling 0, nonfluctuating) or by the closed form
$P_d = P_{fa}^{1/(1+n_p \mathrm{SNR})}$ (Swerling 1). `detection_range` binary
searches the range at which $P_d$ reaches a target. A stealth hull with RCS
$\sigma_s$ is therefore detected at only
$(\sigma_s/\sigma_r)^{1/4}$ of the reference range.

## GPS-denial impact

`gps_denial.py` builds a deterministic Walker-style constellation and computes
the geometry matrix and dilution of precision (GDOP/PDOP/HDOP/VDOP). A jammer
produces a jammer-to-noise ratio `jamming_to_noise_db` that degrades the
carrier-to-noise density `effective_cno_dbhz`, inflating the user equivalent
range error `uere_meters` and hence the position error `PDOP · UERE`.

Finally `simulate_navigation_cascade` propagates failure across a maritime
dependency network: each system's GPS stress is weighted, thresholds trigger
failure, and failed systems add coupled stress to their dependents, round by
round, until the cascade reaches a fixpoint.
