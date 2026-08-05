# Scope and Related Work

## Scope

CARVER is a didactic mission-software model, not an operational tool. The six
domain analyses use idealised physics and synthetic but deterministic data:
the radar model assumes free-space, clutter-free propagation; the
disinformation and narrative models use stylised belief states rather than a
cognitively grounded opinion-dynamics scheme; the GPS/RAIM models use a fixed
constellation geometry and a single jamming source rather than a full
receiver-in-the-loop simulation. These simplifications keep every
computation transparent, deterministic, and verifiable.

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
