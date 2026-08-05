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
  about what those rates are for any real population.
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
  range–Doppler coupling, all of which degrade a real LFM chirp.
* **GPS denial** — one jamming source, a fixed constellation geometry, and a
  dependency cascade with a single scalar coupling factor on every edge
  rather than a real receiver-in-the-loop or per-link model.
* **GNSS integrity** — single-fault RAIM only. Multiple simultaneous faults,
  the case that most concerns a deliberate spoofer, are outside the
  parity-space assumption used here.

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
