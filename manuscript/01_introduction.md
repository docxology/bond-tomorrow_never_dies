# Introduction

In *Tomorrow Never Dies* (1997), Elliot Carver builds a global media empire
whose reach lets him manufacture the conflicts he then reports. His two
instrumental capabilities are a stealth cruiser that evades radar and the
ability to deny an adversary their navigation. This package — codename
{{CARVER_CODENAME}} — models all three capabilities as deterministic physics
and computation, forming a single reproducible "mission software" artifact.

The package is organized around three concepts, each an infrastructure-free
domain module:

* **Disinformation propagation** (`media_manipulation.py`): a two-channel
  belief-diffusion model on a social network, with media-campaign injection
  and greedy influence maximization.
* **Stealth-vessel detection** (`stealth_detection.py`): the radar equation,
  Neyman-Pearson detection, Marcum-Q and Swerling detection probabilities,
  and the detection-range penalty of a low-RCS hull.
* **GPS-denial impact** (`gps_denial.py`): satellite geometry and dilution of
  precision, jamming degradation of carrier-to-noise, position-error growth,
  and navigation failure cascades.

The same core is wired to the BOND-API mission protocol (codename THE
PROTOCOL): a `MissionProvider` named CARVER lets any coordinator discover the
package by slug and drive the full brief → recon → plan → execute → debrief
lifecycle, with every outcome carrying deterministic provenance. All numbers
in this manuscript are injected from `manuscript/config.yaml` and the real
domain modules — none are hand-authored in the prose.
