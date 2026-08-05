"""CARVER — mission software for *Tomorrow Never Dies* (1997).

PROJECT BOND film package. Mission codename: CARVER. The package models six
concepts from Elliot Carver's media-warfare playbook, each as a deterministic,
infrastructure-free domain module:

* :mod:`tomorrow_never_dies.media_manipulation` — disinformation propagation
  (Carver-style media control): belief diffusion on a small-world network with
  media-campaign injection and greedy influence maximization.
* :mod:`tomorrow_never_dies.narrative_control` — bounded-confidence opinion
  dynamics (Hegselmann–Krause) with a media-injection term: polarization,
  echo-chamber fragmentation, media capture, and the critical broadcast reach.
* :mod:`tomorrow_never_dies.stealth_detection` — low-RCS analysis: the radar
  equation, Neyman-Pearson detection, Marcum-Q detection probability, and the
  detection-range penalty of a stealthy hull (the *Sea Vengeance*).
* :mod:`tomorrow_never_dies.radar_waveform` — pulse compression (the radar's
  counter): LFM / Barker-13 matched filtering, processing gain, range
  resolution, sidelobe floor, and the fourth-root detection-range gain.
* :mod:`tomorrow_never_dies.gps_denial` — GPS-denial impact: satellite
  geometry and dilution of precision, jamming-to-noise degradation of C/N0,
  position-error growth, and navigation failure cascades across a maritime
  dependency network.
* :mod:`tomorrow_never_dies.gnss_integrity` — RAIM: scipy-free chi-square /
  parity-space fault detection, HPL/VPL protection levels, and the
  probability of catching a corrupted navigation measurement.

:mod:`tomorrow_never_dies.mission` adapts this core to the frozen
``bond_api`` protocol (codename THE PROTOCOL): a ``MissionProvider`` named
CARVER that any coordinator can discover by slug ``tomorrow_never_dies``.

The domain modules import nothing beyond the standard library and numpy, so
the scientific core is usable even when the BOND protocol dependency is not
installed.
"""

from __future__ import annotations

__version__ = "0.1.0"

#: BOND film identity and mission codename (single source of truth).
MANUSCRIPT_IDENTITY = "Tomorrow Never Dies"
CODENAME = "CARVER"

#: The six pure-domain concept modules this film packages, in manuscript
#: order (media → narrative → stealth → waveform → gps → integrity). This is
#: the declared concept surface; ``tests/test_package_surface.py`` pins it
#: against the modules that actually ship, so it cannot drift.
CONCEPTS = (
    "media_manipulation",
    "narrative_control",
    "stealth_detection",
    "radar_waveform",
    "gps_denial",
    "gnss_integrity",
)

__all__ = [
    "CODENAME",
    "CONCEPTS",
    "MANUSCRIPT_IDENTITY",
    "__version__",
]
