# Scope and Related Work

## Scope

CARVER is a didactic mission-software model, not an operational tool. Every
model here is internally consistent, deterministic, and tested against its own
closed forms and known values — and none of them is calibrated against
measured data. The specific limitation differs per concept, so it is worth
naming each rather than gesturing at "simplifications":

* **Disinformation propagation** — conversion probabilities are free
  parameters, not fitted quantities. The model shows how a two-channel
  campaign behaves for a given persuasion and spread rate; it says nothing
  about what those rates are for any real population. The compartmental
  structure is deliberately two-state (susceptible, believing): there is no
  unaware compartment and no return path, so the model cannot represent
  reach-limited awareness or belief decay.
* **Narrative control** — the bounded-confidence update is a mechanism, not a
  measurement. Hegselmann–Krause has no empirical calibration here at all: the
  confidence radius and media weight are chosen, and the reported capture and
  bimodal split are properties of that choice.
* **Stealth-vessel detection** — free-space, clutter-free propagation, a point
  target with a single aspect-independent RCS, and a **nonfluctuating
  (Swerling 0)** target throughout the canonical scenario. The Swerling-1
  fluctuating case is implemented and tested but is not what the reported
  detection ranges describe.
* **Pulse compression** — the compression gain is treated as ideal coherent
  integration, with no weighting losses, no Doppler mismatch, and no
  range–Doppler coupling, all of which degrade a real LFM chirp. The noise
  bandwidth is set equal to the waveform bandwidth, which is the matched-filter
  ideal; a real receiver's noise bandwidth exceeds it. Because range then
  depends on pulse energy alone, the reported improvement is meaningful only
  against the stated equal-resolution baseline — quoting it against a pulse of
  equal *duration* would be wrong, and against the radar's surveillance pulse
  it would mix a resolution change into a range claim.
* **GPS denial** — one jamming source; a single-epoch snapshot of one Walker
  constellation over one receiver, on a spherical non-rotating Earth with no
  orbital eccentricity, no J2 drift, and no per-satellite signal budget, so
  the visible count and DOP describe that instant and not a daily
  distribution; and a dependency cascade with a single scalar coupling factor
  on every edge rather than a real receiver-in-the-loop or per-link model.
  The UERE code-tracking term ``47·10^(−C/N0/20)`` is extrapolated below a
  receiver's lock threshold, and the canonical jamming case is entirely inside
  that region: the reported jammed position error is the formula continued
  past its validity, not an accuracy any receiver would achieve. The figure is
  shaded accordingly. The threshold itself is a single representative
  constant, not a receiver-specific budget, and no acquisition-versus-tracking
  distinction is modelled.
* **GNSS integrity** — single-fault RAIM only. Multiple simultaneous faults,
  the case that most concerns a deliberate spoofer, are outside the
  parity-space assumption used here. Detection probability is also
  satellite-specific (noncentrality ``P_ii (b/σ)²``); the single figure
  reported is the worst-placed satellite, and no claim is made that a bias of
  the probed size is caught reliably — at this geometry it is not.

These restrictions are the price of keeping every computation transparent,
deterministic, and verifiable end to end from a bare checkout.

## Related work

* **Opinion dynamics / narrative control**: the bounded-confidence update is
  the Hegselmann–Krause model, generalising the DeGroot consensus framework
  to bounded interaction; the media-injection term models an exogenous
  broadcast pulling a subset of agents.
* **Radar detection and waveforms**: the radar equation and Marcum/Swerling
  detection probabilities follow classical radar detection theory; the LFM
  chirp and Barker-13 phase code follow the pulse-compression literature
  (Skolnik; Barker).
* **Influence maximisation**: the greedy seed-selection procedure follows the
  submodular influence-maximisation framework, applied here with
  deterministic simulations for reproducibility.
* **Disinformation propagation**: the belief-diffusion model is a
  compartmental epidemiological analogy (susceptible–believing) adapted to
  media-driven belief change.
* **GNSS denial and integrity**: dilution-of-precision and jamming-to-noise
  degradation follow standard satellite-navigation error models; the cascade
  is a thresholded dependency-graph propagation; RAIM follows the baseline
  autonomous-integrity scheme of Parkinson–Axelrad and Brown.

The package itself is one film in the BOND suite, interoperating through the
frozen `bond_api` `MissionProvider` protocol rather than bespoke interfaces.
