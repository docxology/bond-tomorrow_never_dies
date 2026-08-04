# Scope and Related Work

## Scope

CARVER is a didactic mission-software model, not an operational tool. The
three domain modules use idealised physics and synthetic but deterministic
data: the radar model assumes free-space propagation with no clutter or
multipath; the disinformation model uses a stylised three-state belief system
rather than a cognitively grounded opinion-dynamics model; the GPS model uses
a fixed geometry and a single jamming source rather than a full
receiver-in-the-loop simulation. These simplifications keep every computation
transparent, deterministic, and verifiable.

## Related work

* **Radar detection**: the radar equation and Marcum/Swerling detection
  models follow the classical treatment of radar detection theory (Marcum;
  Swerling). Detection probability is computed by direct numerical
  integration of the Marcum Q function rather than a lookup table.
* **Influence maximisation**: the greedy seed-selection procedure follows
  the submodular influence-maximisation framework, applied here with
  deterministic simulations for reproducibility.
* **Influence dynamics / disinformation**: the belief-diffusion model is a
  compartmental epidemiological analogy (susceptible–believing) adapted to
  media-driven belief change.
* **GNSS denial**: dilution-of-precision and jamming-to-noise degradation
  follow standard satellite-navigation error models; the cascade is a
  thresholded dependency-graph propagation.

The package itself is one film in the BOND suite, interoperating through the
frozen `bond_api` `MissionProvider` protocol rather than bespoke interfaces.
