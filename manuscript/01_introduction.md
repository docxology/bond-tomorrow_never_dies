# Introduction

In *Tomorrow Never Dies* (1997), Elliot Carver builds a global media empire
whose reach lets him manufacture the conflicts he then reports. His two
instrumental capabilities are a stealth cruiser that evades radar and the
ability to deny an adversary their navigation. This package — codename
{{CARVER_CODENAME}} — models those capabilities as deterministic physics
and computation, forming a single reproducible "mission software" artifact.

Each capability is modelled twice: once as the attack, once as the defence
that answers it. The result is {{CARVER_OBJECTIVES}} infrastructure-free domain
modules in three adversarial pairs.

**Media.**

* **Disinformation propagation** (`media_manipulation.py`): a two-channel
  belief-diffusion model on a social network, with media-campaign injection
  and greedy influence maximization — *whether* an agent believes.
* **Narrative control** (`narrative_control.py`): Hegselmann–Krause
  bounded-confidence opinion dynamics with a media-injection term — *how far*
  an opinion moves, how the audience fragments into echo chambers, and the
  minimum broadcast reach that tips the network.

**Radar.**

* **Stealth-vessel detection** (`stealth_detection.py`): the radar equation,
  Neyman-Pearson detection, Marcum-Q and Swerling detection probabilities,
  and the detection-range penalty of a low-RCS hull.
* **Pulse compression** (`radar_waveform.py`): the radar's counter — LFM and
  Barker-13 matched filtering, processing gain, range resolution, sidelobe
  floor, and the fourth-root detection-range recovery.

**Navigation.**

* **GPS-denial impact** (`gps_denial.py`): satellite geometry and dilution of
  precision, jamming degradation of carrier-to-noise, position-error growth,
  and navigation failure cascades.
* **GNSS integrity** (`gnss_integrity.py`): the receiver's counter — RAIM
  parity-space fault detection, protection levels, and the probability of
  catching a corrupted measurement before it becomes a wrong position.

The same core is wired to the BOND-API mission protocol (codename THE
PROTOCOL): a `MissionProvider` named CARVER lets any coordinator discover the
package by slug and drive the full brief → recon → plan → execute → debrief
lifecycle, with every outcome carrying deterministic provenance. All numbers
in this manuscript are injected from `manuscript/config.yaml` and the real
domain modules — none are hand-authored in the prose.
