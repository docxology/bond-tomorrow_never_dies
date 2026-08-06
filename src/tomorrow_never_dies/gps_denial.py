"""GPS-denial impact analysis — jamming, DOP, and navigation failure cascades.

When Carver denies an adversary their navigation, the effect is not local: a
jammed GPS receiver loses accuracy, and every system that depends on that
navigation — ships, lanes, ports, aircraft — degrades in a cascade. This
module quantifies the whole chain deterministically:

* **Satellite geometry** — a Walker-delta constellation propagated as real
  orbital geometry (circular orbits, evenly spaced right ascensions and
  in-plane phasing) and projected onto a receiver's local sky; the geometry
  matrix and the dilution-of-precision (GDOP/PDOP/HDOP/VDOP) that scales
  ranging errors into position errors.
* **Jamming** — jammer-to-noise ratio for a given jammer power, gain, and
  standoff distance; effective C/N0 degradation; UERE (user equivalent range
  error) growth; the resulting position error ``PDOP * UERE``; and
  :func:`maintains_lock`, the carrier-lock check that says whether that
  position error describes a receiver at all or is the formula extrapolated
  past the point where a real one has stopped tracking.
* **Navigation failure cascade** — a dependency network of maritime systems
  where direct GPS stress plus propagated stress from failed dependencies
  pushes nodes past a failure threshold, round by round, until a fixpoint.

All randomness is absent or seeded; the module is infrastructure-free
(stdlib + numpy only).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "CNO_TRACKING_THRESHOLD_DBHZ",
    "EARTH_RADIUS_M",
    "GPS_ALTITUDE_M",
    "GPS_INCLINATION_DEG",
    "RECEIVER_LAT_DEG",
    "RECEIVER_LON_DEG",
    "CascadeResult",
    "Constellation",
    "DopResult",
    "Satellite",
    "compute_dop",
    "effective_cno_dbhz",
    "geometry_matrix",
    "jamming_to_noise_db",
    "maintains_lock",
    "maritime_dependency_network",
    "position_error_meters",
    "simulate_navigation_cascade",
    "uere_meters",
    "unit_vector",
    "walker_constellation",
]

#: Speed of light, m/s.
SPEED_OF_LIGHT = 299792458.0
#: Boltzmann constant, J/K.
K_BOLTZMANN = 1.380649e-23
#: Reference noise temperature, K.
REFERENCE_TEMPERATURE_K = 290.0
#: GPS L1 carrier frequency, Hz.
L1_FREQUENCY_HZ = 1575.42e6
#: GPS C/A code bandwidth, Hz.
CA_BANDWIDTH_HZ = 2.046e6
#: GPS constellation altitude, m.
GPS_ALTITUDE_M = 20180000.0
#: Mean Earth radius, m (spherical Earth — no oblateness model here).
EARTH_RADIUS_M = 6378137.0
#: GPS orbital-plane inclination, degrees.
GPS_INCLINATION_DEG = 55.0
#: Canonical receiver: the South China Sea theatre of *Tomorrow Never Dies*.
RECEIVER_LAT_DEG = 15.0
RECEIVER_LON_DEG = 115.0
#: Carrier-lock threshold, dB-Hz. A C/A receiver holding carrier phase needs
#: roughly this much C/N0; below it, it does not track badly, it stops
#: tracking. :func:`uere_meters` has no notion of that, so its code-tracking
#: term is an extrapolation below this line, not a prediction — see
#: :func:`maintains_lock`.
CNO_TRACKING_THRESHOLD_DBHZ = 25.0


@dataclass(frozen=True)
class Satellite:
    """A satellite in the local-sky model: name plus azimuth/elevation."""

    name: str
    azimuth_deg: float
    elevation_deg: float

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Satellite.name must be a non-empty string")
        if not isinstance(self.azimuth_deg, (int, float)) or isinstance(
            self.azimuth_deg, bool
        ):
            raise ValueError("Satellite.azimuth_deg must be a number")
        if not 0.0 <= self.azimuth_deg < 360.0:
            raise ValueError("Satellite.azimuth_deg must be in [0, 360)")
        if not isinstance(self.elevation_deg, (int, float)) or isinstance(
            self.elevation_deg, bool
        ):
            raise ValueError("Satellite.elevation_deg must be a number")
        if not 0.0 <= self.elevation_deg <= 90.0:
            raise ValueError("Satellite.elevation_deg must be in [0, 90]")


@dataclass(frozen=True)
class Constellation:
    """A deterministic satellite constellation over a fixed receiver."""

    satellites: tuple[Satellite, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.satellites, tuple) or not self.satellites:
            raise ValueError("Constellation.satellites must be a non-empty tuple")
        for sat in self.satellites:
            if not isinstance(sat, Satellite):
                raise ValueError(
                    "Constellation.satellites entries must be Satellite instances"
                )

    def visible(self, mask_angle_deg: float = 10.0) -> tuple[Satellite, ...]:
        """Satellites above the elevation mask (deterministic filter)."""
        if not isinstance(mask_angle_deg, (int, float)) or isinstance(
            mask_angle_deg, bool
        ):
            raise ValueError("mask_angle_deg must be a number")
        if not 0.0 <= mask_angle_deg <= 90.0:
            raise ValueError("mask_angle_deg must be in [0, 90]")
        return tuple(s for s in self.satellites if s.elevation_deg >= mask_angle_deg)


@dataclass(frozen=True)
class DopResult:
    """Dilution-of-precision components (unitless)."""

    gdop: float
    pdop: float
    hdop: float
    vdop: float


@dataclass(frozen=True)
class CascadeResult:
    """Outcome of a navigation failure cascade."""

    failed: tuple[str, ...]
    rounds: int
    total_fraction: float
    per_round: tuple[int, ...]


def walker_constellation(
    n_sats: int = 24,
    n_planes: int = 6,
    *,
    phasing: int = 1,
    inclination_deg: float = GPS_INCLINATION_DEG,
    altitude_m: float = GPS_ALTITUDE_M,
    receiver_lat_deg: float = RECEIVER_LAT_DEG,
    receiver_lon_deg: float = RECEIVER_LON_DEG,
    epoch_deg: float = 0.0,
) -> Constellation:
    """Walker-delta constellation ``T/P/F`` seen from a receiver's local sky.

    A real Walker pattern, not a random sky: ``n_sats`` satellites are split
    evenly across ``n_planes`` circular orbits of the given inclination, plane
    ``p`` takes right ascension ``360 p / n_planes``, and satellite ``s`` in
    that plane takes argument of latitude
    ``360 s / (n_sats / n_planes) + 360 F p / n_sats`` (the ``F = phasing``
    inter-plane offset). Positions are computed in an Earth-centred frame at
    ``epoch_deg`` of orbital phase and projected into the receiver's
    east/north/up frame on a spherical Earth, so azimuth and elevation are
    *derived* geometry.

    Only the satellites geometrically above the horizon are returned, so a
    typical mid-latitude receiver sees the realistic 8-12 of a 24-satellite
    constellation rather than all of them. ``n_sats`` must divide evenly into
    ``n_planes`` — an uneven split is not a Walker pattern.

    No RNG is involved: the constellation is a pure function of its orbital
    arguments.
    """
    if not isinstance(n_sats, int) or n_sats < 4:
        raise ValueError("n_sats must be an integer >= 4")
    if not isinstance(n_planes, int) or not 1 <= n_planes <= n_sats:
        raise ValueError("n_planes must be an integer in [1, n_sats]")
    if n_sats % n_planes != 0:
        raise ValueError("n_sats must be an integer multiple of n_planes")
    if not isinstance(phasing, int) or isinstance(phasing, bool) or phasing < 0:
        raise ValueError("phasing must be a non-negative integer")
    for label, value in (
        ("inclination_deg", inclination_deg),
        ("receiver_lat_deg", receiver_lat_deg),
        ("receiver_lon_deg", receiver_lon_deg),
        ("epoch_deg", epoch_deg),
    ):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{label} must be a number")
    if not 0.0 <= inclination_deg <= 180.0:
        raise ValueError("inclination_deg must be in [0, 180]")
    if not -90.0 <= receiver_lat_deg <= 90.0:
        raise ValueError("receiver_lat_deg must be in [-90, 90]")
    if (
        not isinstance(altitude_m, (int, float))
        or isinstance(altitude_m, bool)
        or altitude_m <= 0
    ):
        raise ValueError("altitude_m must be a positive number")

    per_plane = n_sats // n_planes
    radius = EARTH_RADIUS_M + float(altitude_m)
    inclination = np.deg2rad(float(inclination_deg))
    lat = np.deg2rad(float(receiver_lat_deg))
    lon = np.deg2rad(float(receiver_lon_deg))

    receiver = EARTH_RADIUS_M * np.asarray(
        [np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)]
    )
    east = np.asarray([-np.sin(lon), np.cos(lon), 0.0])
    north = np.asarray(
        [-np.sin(lat) * np.cos(lon), -np.sin(lat) * np.sin(lon), np.cos(lat)]
    )
    up = receiver / EARTH_RADIUS_M

    satellites: list[Satellite] = []
    for index in range(n_sats):
        plane, slot = divmod(index, per_plane)
        raan = 2.0 * np.pi * plane / n_planes
        arg_lat = (
            2.0 * np.pi * slot / per_plane
            + 2.0 * np.pi * phasing * plane / n_sats
            + np.deg2rad(float(epoch_deg))
        )
        position = radius * np.asarray(
            [
                np.cos(arg_lat) * np.cos(raan)
                - np.sin(arg_lat) * np.cos(inclination) * np.sin(raan),
                np.cos(arg_lat) * np.sin(raan)
                + np.sin(arg_lat) * np.cos(inclination) * np.cos(raan),
                np.sin(arg_lat) * np.sin(inclination),
            ]
        )
        line_of_sight = position - receiver
        e_comp = float(line_of_sight @ east)
        n_comp = float(line_of_sight @ north)
        u_comp = float(line_of_sight @ up)
        elevation = float(np.rad2deg(np.arctan2(u_comp, np.hypot(e_comp, n_comp))))
        if elevation < 0.0:
            continue  # below the horizon: not in view at this epoch
        azimuth = float(np.rad2deg(np.arctan2(e_comp, n_comp)) % 360.0)
        satellites.append(
            Satellite(
                name=f"PRN{index + 1:02d}",
                azimuth_deg=azimuth,
                elevation_deg=min(elevation, 90.0),
            )
        )
    if not satellites:
        raise ValueError("no satellite is above the horizon for this configuration")
    return Constellation(satellites=tuple(satellites))


def unit_vector(azimuth_deg: float, elevation_deg: float) -> np.ndarray:
    """Unit line-of-sight vector in ENU coordinates for an az/el pair."""
    az = np.deg2rad(azimuth_deg)
    el = np.deg2rad(elevation_deg)
    return np.asarray(
        [np.cos(el) * np.sin(az), np.cos(el) * np.cos(az), np.sin(el)],
        dtype=float,
    )


def geometry_matrix(satellites: tuple[Satellite, ...]) -> np.ndarray:
    """Navigation geometry matrix G (n x 4) for a set of satellites.

    Rows are ``[-u_x, -u_y, -u_z, 1]`` in ENU coordinates.
    """
    if not satellites:
        raise ValueError("satellites must not be empty")
    rows = []
    for sat in satellites:
        u = unit_vector(sat.azimuth_deg, sat.elevation_deg)
        rows.append([-u[0], -u[1], -u[2], 1.0])
    return np.asarray(rows, dtype=float)


def compute_dop(satellites: tuple[Satellite, ...]) -> DopResult:
    """Dilution of precision from a satellite set (needs >= 4 satellites)."""
    if not isinstance(satellites, tuple) or len(satellites) < 4:
        raise ValueError("compute_dop requires at least 4 satellites")
    g = geometry_matrix(satellites)
    q = np.linalg.inv(g.T @ g)
    gdop = float(np.sqrt(np.trace(q)))
    pdop = float(np.sqrt(q[0, 0] + q[1, 1] + q[2, 2]))
    hdop = float(np.sqrt(q[0, 0] + q[1, 1]))
    vdop = float(np.sqrt(q[2, 2]))
    return DopResult(gdop=gdop, pdop=pdop, hdop=hdop, vdop=vdop)


def jamming_to_noise_db(
    jammer_power_w: float,
    distance_m: float,
    *,
    jammer_gain_db: float = 30.0,
    frequency_hz: float = L1_FREQUENCY_HZ,
    bandwidth_hz: float = CA_BANDWIDTH_HZ,
) -> float:
    """Jammer-to-noise ratio in dB at a receiver.

    ``J/N = P_j G_j lambda^2 / ((4 pi)^2 d^2 k T0 B)`` — the jammer's power
    arriving at the victim receiver, normalized by receiver thermal noise.
    """
    for label, value in (
        ("jammer_power_w", jammer_power_w),
        ("distance_m", distance_m),
        ("jammer_gain_db", jammer_gain_db),
        ("frequency_hz", frequency_hz),
        ("bandwidth_hz", bandwidth_hz),
    ):
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{label} must be a positive number")
    lam = SPEED_OF_LIGHT / frequency_hz
    gain = 10 ** (jammer_gain_db / 10.0)
    jammer_flux = jammer_power_w * gain * lam**2 / ((4 * np.pi) ** 2 * distance_m**2)
    noise_flux = K_BOLTZMANN * REFERENCE_TEMPERATURE_K * bandwidth_hz
    return float(10.0 * np.log10(jammer_flux / noise_flux))


def effective_cno_dbhz(cno_clean_dbhz: float, jnr_db: float) -> float:
    """Effective carrier-to-noise density (dB-Hz) under jamming.

    ``C/N0_eff = C/N0 - 10 log10(1 + 10^(J/N / 10))`` — the standard
    signal-in-noise-plus-jammer degradation.
    """
    if (
        not isinstance(cno_clean_dbhz, (int, float))
        or isinstance(cno_clean_dbhz, bool)
        or cno_clean_dbhz <= 0
    ):
        raise ValueError("cno_clean_dbhz must be a positive number")
    if (
        not isinstance(jnr_db, (int, float))
        or isinstance(jnr_db, bool)
        or not np.isfinite(jnr_db)
    ):
        raise ValueError("jnr_db must be a finite number")
    degradation = 10.0 * np.log10(1.0 + 10 ** (jnr_db / 10.0))
    return float(cno_clean_dbhz - degradation)


def uere_meters(
    cno_dbhz: float,
    *,
    iono_m: float = 4.0,
    tropo_m: float = 0.7,
    ephemeris_m: float = 1.5,
    clock_m: float = 2.5,
    multipath_m: float = 1.0,
) -> float:
    """User equivalent range error (m) at a given C/N0.

    The code-tracking noise component grows as the signal weakens:
    ``sigma_noise ~ 47 * 10^(-C/N0 / 20)`` meters (classic C/A-code tracking
    approximation); the other UERE terms are fixed environmental budgets.
    """
    if (
        not isinstance(cno_dbhz, (int, float))
        or isinstance(cno_dbhz, bool)
        or not np.isfinite(cno_dbhz)
    ):
        raise ValueError("cno_dbhz must be a finite number")
    for label, value in (
        ("iono_m", iono_m),
        ("tropo_m", tropo_m),
        ("ephemeris_m", ephemeris_m),
        ("clock_m", clock_m),
        ("multipath_m", multipath_m),
    ):
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{label} must be a non-negative number")
    noise_m = 47.0 * 10 ** (-cno_dbhz / 20.0)
    return float(
        np.sqrt(
            iono_m**2
            + tropo_m**2
            + ephemeris_m**2
            + clock_m**2
            + multipath_m**2
            + noise_m**2
        )
    )


def maintains_lock(
    cno_dbhz: float, *, threshold_dbhz: float = CNO_TRACKING_THRESHOLD_DBHZ
) -> bool:
    """Whether a receiver still tracks the signal at this effective C/N0.

    The UERE model degrades smoothly forever, which a real receiver does not:
    below the carrier-lock threshold it produces no solution at all. Anything
    :func:`uere_meters` or :func:`position_error_meters` reports at a C/N0
    failing this predicate is the formula extrapolated past its validity, and
    must be labelled as such rather than quoted as a navigation error.
    """
    for label, value in (("cno_dbhz", cno_dbhz), ("threshold_dbhz", threshold_dbhz)):
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not np.isfinite(value)
        ):
            raise ValueError(f"{label} must be a finite number")
    return bool(cno_dbhz >= threshold_dbhz)


def position_error_meters(pdop: float, cno_dbhz: float, **uere_kwargs: float) -> float:
    """1-sigma position error ``PDOP * UERE`` at a given C/N0.

    Physically meaningful only where :func:`maintains_lock` holds.
    """
    if not isinstance(pdop, (int, float)) or isinstance(pdop, bool) or pdop <= 0:
        raise ValueError("pdop must be a positive number")
    return float(pdop * uere_meters(cno_dbhz, **uere_kwargs))


def maritime_dependency_network() -> tuple[
    dict[str, tuple[str, ...]], dict[str, float]
]:
    """Deterministic maritime navigation dependency network.

    Returns ``(dependencies, gps_weights)`` where ``dependencies[u]`` lists
    the systems that depend on ``u``: when ``u`` fails, each dependent
    accumulates coupled stress. The network mirrors the *Tomorrow Never Dies*
    theater: Carver Tower orchestrates, the stealth cruiser *Sea Vengeance*
    navigates the South China Sea lanes, and the HMS *Devonshire* and
    commercial shipping depend on those lanes and on GPS directly.
    """
    dependencies: dict[str, tuple[str, ...]] = {
        "gps_constellation": (
            "carver_tower",
            "sea_vengeance",
            "hms_devonshire",
            "commercial_shipping",
        ),
        "carver_tower": ("sea_vengeance",),
        "sea_vengeance": ("carver_tower", "hms_devonshire"),
        "hms_devonshire": ("commercial_shipping",),
        "commercial_shipping": ("sea_lanes",),
        "sea_lanes": ("sea_vengeance", "hms_devonshire", "commercial_shipping"),
        "south_china_sea_port": ("sea_lanes",),
    }
    gps_weights: dict[str, float] = {
        "gps_constellation": 0.0,
        "carver_tower": 0.3,
        "sea_vengeance": 0.5,
        "hms_devonshire": 0.9,
        "commercial_shipping": 0.8,
        "sea_lanes": 0.6,
        "south_china_sea_port": 0.4,
    }
    return dependencies, gps_weights


def simulate_navigation_cascade(
    dependencies: dict[str, tuple[str, ...]],
    gps_weights: dict[str, float],
    *,
    jamming_strength: float = 0.5,
    fail_threshold: float = 0.7,
    propagation_factor: float = 0.5,
    max_rounds: int = 30,
    edge_weights: dict[tuple[str, str], float] | None = None,
) -> CascadeResult:
    """Simulate the GPS-denial failure cascade to its fixpoint.

    A node's stress starts at ``gps_weights[v] * jamming_strength`` (direct
    GPS dependence). Each round, every node whose stress meets
    ``fail_threshold`` fails; a newly failed node ``u`` adds
    ``factor * gps_weights[v] * jamming_strength`` stress to each of its
    dependents, where ``factor`` is the per-edge coupling ``edge_weights[(u,
    v)]`` when given, else the scalar ``propagation_factor``. Rounds repeat
    until no new failures occur or ``max_rounds`` is exhausted. The default
    (``edge_weights=None``) is byte-for-byte the old single-scalar model, so
    every published number is unchanged; per-edge weights let the maritime
    graph distinguish "depends on GPS for navigation" from "depends on GPS for
    scheduling", which is exactly the distinction the film's plot turns on.

    Returns:
        :class:`CascadeResult` — failed systems (deterministic order), the
        number of cascade rounds, the failed fraction, and failures per round.
    """
    nodes = tuple(gps_weights)
    if not nodes:
        raise ValueError("gps_weights must not be empty")
    for node in nodes:
        if not isinstance(gps_weights[node], (int, float)) or isinstance(
            gps_weights[node], bool
        ):
            raise ValueError(f"gps_weights[{node!r}] must be a number")
        if not 0.0 <= gps_weights[node] <= 1.0:
            raise ValueError(f"gps_weights[{node!r}] must be in [0, 1]")
        if node not in dependencies:
            raise ValueError(f"dependencies has no entry for node {node!r}")
    # Every dependent must be a weighted node, or stress propagation would
    # raise KeyError mid-cascade instead of failing at the boundary.
    for source, dependents in dependencies.items():
        for dependent in dependents:
            if dependent not in gps_weights:
                raise ValueError(
                    f"dependencies[{source!r}] names unknown node {dependent!r} "
                    "(every dependent must have a gps_weights entry)"
                )
    if edge_weights is not None:
        for (source, dependent), weight in edge_weights.items():
            if source not in gps_weights or dependent not in gps_weights:
                raise ValueError(
                    "edge_weights keys must name nodes with a gps_weights entry"
                )
            if not isinstance(weight, (int, float)) or isinstance(weight, bool):
                raise ValueError(
                    f"edge_weights[{source!r} -> {dependent!r}] must be a number"
                )
            if not 0.0 <= float(weight) <= 1.0:
                raise ValueError(
                    f"edge_weights[{source!r} -> {dependent!r}] must be in [0, 1]"
                )
    for label, value in (
        ("jamming_strength", jamming_strength),
        ("propagation_factor", propagation_factor),
    ):
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not 0.0 <= value <= 1.0
        ):
            raise ValueError(f"{label} must be in [0, 1]")
    if (
        not isinstance(fail_threshold, (int, float))
        or isinstance(fail_threshold, bool)
        or not 0.0 < fail_threshold <= 1.0
    ):
        raise ValueError("fail_threshold must be in (0, 1]")
    if not isinstance(max_rounds, int) or max_rounds < 1:
        raise ValueError("max_rounds must be an integer >= 1")

    stress = {node: float(gps_weights[node]) * jamming_strength for node in nodes}
    failed: set[str] = set()
    per_round: list[int] = []
    for _ in range(max_rounds):
        newly = [
            node
            for node in nodes
            if node not in failed and stress[node] >= fail_threshold
        ]
        if not newly:
            break
        failed.update(newly)
        per_round.append(len(newly))
        for source in newly:
            for dependent in dependencies.get(source, ()):
                if dependent not in failed:
                    factor = (
                        propagation_factor
                        if edge_weights is None
                        else edge_weights.get((source, dependent), propagation_factor)
                    )
                    stress[dependent] += (
                        factor * gps_weights[dependent] * jamming_strength
                    )
    return CascadeResult(
        failed=tuple(sorted(failed)),
        rounds=len(per_round),
        total_fraction=len(failed) / len(nodes),
        per_round=tuple(per_round),
    )
