"""Disinformation propagation model — Carver-style media control.

Elliot Carver's media empire manufactures the news it then broadcasts: a
global outlet with a fixed reach converts a fraction of its audience to a
manufactured belief, and believing agents then convert their social
neighbors. This module makes that dynamic quantitative and deterministic.

The model is a two-channel belief-diffusion on a graph:

* **Media channel** — each campaign round, a deterministic subset of nodes
  (the ``reach``) is exposed; every susceptible exposed node converts to the
  manufactured belief with probability ``persuasion``.
* **Social channel** — every believing node converts each susceptible neighbor
  with probability ``spread_rate`` per round.

All randomness is drawn from a seeded ``numpy.random.Generator``; identical
inputs produce byte-identical trajectories. The module also ships a
deterministic greedy influence-maximization procedure (Kempe–Kleinberg–Tardos
style) that picks the ``k`` seed nodes maximizing the final belief share, and
two social-epidemiology metrics: the echo-chamber coefficient and the
amplification factor.

This module is infrastructure-free: stdlib + numpy only. It never imports
``bond_api`` or anything else from the BOND suite.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "BELIEVING",
    "SUSCEPTIBLE",
    "UNAWARE",
    "InfluenceResult",
    "MediaCampaign",
    "SimulationResult",
    "amplification_factor",
    "build_network",
    "echo_chamber_coefficient",
    "influence_maximization",
    "simulate_disinformation",
    "state_counts",
]

#: Agent state: has not encountered the manufactured message.
UNAWARE = 0
#: Agent state: has encountered the message but does not (yet) believe it.
SUSCEPTIBLE = 1
#: Agent state: believes the manufactured message and spreads it socially.
BELIEVING = 2

#: Node-index mixing constant (Knuth's 32-bit golden-ratio multiplier) for the
#: deterministic media-target sweep.
_TARGET_MIX = 2654435761
#: Seed mixing constant, coprime with :data:`_TARGET_MIX`, so the seed
#: reorders the audience instead of merely offsetting every score by a
#: constant (which would leave the sort order — and therefore the selected
#: audience — effectively seed-independent).
_SEED_MIX = 40503
#: Modulus of the target-score space (32-bit).
_SCORE_MODULUS = 2**32


@dataclass(frozen=True)
class MediaCampaign:
    """A broadcast campaign: reach (fraction of the network exposed) and
    persuasion (per-exposure conversion probability)."""

    reach: float
    persuasion: float

    def __post_init__(self) -> None:
        _require_unit_interval(self.reach, "MediaCampaign.reach")
        _require_unit_interval(self.persuasion, "MediaCampaign.persuasion")


@dataclass(frozen=True)
class SimulationResult:
    """The deterministic outcome of one disinformation simulation."""

    steps: int
    #: Believing fraction after each round, including round 0 (the seed set).
    belief_share: tuple[float, ...]
    final_believers: int
    total_nodes: int
    #: Fraction of believers whose believing-neighbor share >= 0.5.
    echo_chamber: float
    #: Final believers divided by directly exposed nodes.
    amplification: float
    directly_exposed: int


@dataclass(frozen=True)
class InfluenceResult:
    """Greedy influence maximization output: the chosen seed nodes and the
    final belief share they achieve."""

    seeds: tuple[int, ...]
    final_share: float
    evaluations: int


def _require_unit_interval(value: float, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be a number in [0, 1]")
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{label} must be in [0, 1]")


def build_network(
    n_nodes: int,
    seed: int,
    *,
    topology: str = "small_world",
    k: int = 4,
    rewire_prob: float = 0.1,
) -> tuple[tuple[int, ...], ...]:
    """Build a deterministic social network as a tuple-of-tuples adjacency.

    Args:
        n_nodes: Number of agents (>= 2).
        seed: Fixed RNG seed (determinism guarantee).
        topology: ``"small_world"`` (Watts–Strogatz ring lattice with
            ``rewire_prob`` edge rewiring) or ``"barabasi_albert"``
            (preferential attachment, ``k`` edges per arriving node).
        k: Ring degree / attachment edges per node.
        rewire_prob: Watts–Strogatz rewiring probability.

    Returns:
        Adjacency list as a tuple of sorted neighbor tuples.
    """
    if not isinstance(n_nodes, int) or n_nodes < 2:
        raise ValueError("n_nodes must be an integer >= 2")
    if not isinstance(k, int) or k < 1 or k >= n_nodes:
        raise ValueError("k must be an integer in [1, n_nodes)")
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    rng = np.random.default_rng(seed)

    if topology == "small_world":
        if not 0.0 <= rewire_prob <= 1.0:
            raise ValueError("rewire_prob must be in [0, 1]")
        # Ring lattice: every node i connects to its k nearest ring neighbors.
        adj: list[set[int]] = [set() for _ in range(n_nodes)]
        for i in range(n_nodes):
            for offset in range(1, k // 2 + 1):
                adj[i].add((i + offset) % n_nodes)
                adj[i].add((i - offset) % n_nodes)
        # Rewire each existing edge endpoint with probability rewire_prob.
        for i in range(n_nodes):
            neighbors = list(adj[i])
            for j in neighbors:
                if j <= i:
                    continue  # each undirected edge rewired once
                if rng.random() < rewire_prob:
                    adj[i].discard(j)
                    adj[j].discard(i)
                    candidates = [
                        c for c in range(n_nodes) if c != i and c not in adj[i]
                    ]
                    if candidates:
                        new = int(candidates[rng.integers(0, len(candidates))])
                        adj[i].add(new)
                        adj[new].add(i)
    elif topology == "barabasi_albert":
        adj = [set() for _ in range(n_nodes)]
        # Seed clique on the first k+1 nodes, then attach each new node to k
        # existing nodes chosen by degree-proportional preferential attachment.
        for i in range(k + 1):
            for j in range(i + 1, k + 1):
                adj[i].add(j)
                adj[j].add(i)
        degrees = [len(adj[i]) for i in range(n_nodes)]
        for new in range(k + 1, n_nodes):
            targets: set[int] = set()
            while len(targets) < k:
                total = sum(
                    degrees[i] for i in range(n_nodes) if i not in targets and i < new
                )
                if total <= 0:
                    break
                r = rng.integers(0, total)
                acc = 0
                chosen = -1
                for i in range(new):
                    if i in targets:
                        continue
                    acc += degrees[i]
                    if r < acc:
                        chosen = i
                        break
                if chosen >= 0:
                    targets.add(chosen)
            for t in targets:
                adj[new].add(t)
                adj[t].add(new)
                degrees[new] += 1
                degrees[t] += 1
    else:
        raise ValueError(
            f"unknown topology {topology!r} (choose 'small_world' or 'barabasi_albert')"
        )

    return tuple(tuple(sorted(adj[i])) for i in range(n_nodes))


def state_counts(states: np.ndarray) -> tuple[int, int, int]:
    """Return ``(unaware, susceptible, believing)`` counts for a state array."""
    counts = np.bincount(states, minlength=3)
    return int(counts[UNAWARE]), int(counts[SUSCEPTIBLE]), int(counts[BELIEVING])


def _target_score(index: int, seed: int) -> int:
    """Deterministic 32-bit broadcast-priority score for one node.

    The seed is folded in multiplicatively and XOR-mixed, not added: an
    additive seed shifts every score by the same constant and therefore
    leaves the sort order (and the selected audience) unchanged, which would
    make ``seed`` a no-op for audience selection.
    """
    mixed = ((index + 1) * _TARGET_MIX) ^ ((seed + 1) * _SEED_MIX)
    mixed = (mixed ^ (mixed >> 15)) * _TARGET_MIX
    return mixed % _SCORE_MODULUS


def _media_targets(n_nodes: int, reach: float, seed: int) -> np.ndarray:
    """Deterministic exposed subset: ``round(reach * n_nodes)`` nodes.

    Index-mixed rather than RNG-drawn on purpose. The footprint is a pure
    function of ``(n_nodes, reach, seed)``, independent of the simulation's
    draw history, so it is stable no matter where in the campaign it is
    computed — and it *nests*: raising ``reach`` only ever adds nodes to the
    exposed set, it never reshuffles the ones already in it. Carver's
    transmitter coverage grows; it does not move.

    Note this concerns *selection* only. Each exposed, still-susceptible node
    consumes one persuasion draw per campaign round, so the belief trajectory
    does still depend on ``reach`` through those rolls.
    """
    count = round(reach * n_nodes)
    if count <= 0:
        return np.zeros(0, dtype=np.int64)
    # Mix node indices so the exposed set is spread across the ring.
    scores = np.asarray(
        [_target_score(i, seed) for i in range(n_nodes)],
        dtype=np.int64,
    )
    order = np.argsort(scores, kind="stable")
    return order[:count].astype(np.int64)


def simulate_disinformation(
    network: tuple[tuple[int, ...], ...],
    *,
    media_reach: float = 0.3,
    persuasion: float = 0.15,
    seed: int = 7,
    steps: int = 20,
    initial_believers: int = 1,
    spread_rate: float = 0.2,
    campaign_delay: int = 2,
    initial_seed_nodes: tuple[int, ...] | None = None,
) -> SimulationResult:
    """Run the deterministic two-channel disinformation simulation.

    Args:
        network: Adjacency tuple from :func:`build_network`.
        media_reach: Fraction of nodes in the broadcast footprint. The
            exposed set is fixed for the whole campaign; each round every
            still-susceptible member of it re-rolls ``persuasion``.
        persuasion: Per-exposure conversion probability (media channel).
        seed: Fixed RNG seed.
        steps: Number of simulation rounds (>= 1).
        initial_believers: How many leading nodes start believing.
        spread_rate: Per-edge social conversion probability.
        campaign_delay: Rounds before the media campaign starts (>= 1).
        initial_seed_nodes: Explicit seed set overriding ``initial_believers``
            (used by influence maximization).

    Returns:
        :class:`SimulationResult` with the belief-share trajectory and the
        social metrics.
    """
    n_nodes = len(network)
    if n_nodes == 0:
        raise ValueError("network must not be empty")
    _require_unit_interval(media_reach, "media_reach")
    _require_unit_interval(persuasion, "persuasion")
    _require_unit_interval(spread_rate, "spread_rate")
    if not isinstance(steps, int) or steps < 1:
        raise ValueError("steps must be an integer >= 1")
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if not isinstance(campaign_delay, int) or campaign_delay < 1:
        raise ValueError("campaign_delay must be an integer >= 1")
    if initial_seed_nodes is not None:
        seed_nodes = tuple(int(v) for v in initial_seed_nodes)
        if not seed_nodes or any(v < 0 or v >= n_nodes for v in seed_nodes):
            raise ValueError(
                "initial_seed_nodes must be non-empty node indices within the network"
            )
    else:
        if (
            not isinstance(initial_believers, int)
            or not 1 <= initial_believers <= n_nodes
        ):
            raise ValueError("initial_believers must be an integer in [1, n_nodes]")
        seed_nodes = tuple(range(initial_believers))

    rng = np.random.default_rng(seed)
    states = np.full(n_nodes, SUSCEPTIBLE, dtype=np.int64)
    for node in seed_nodes:
        states[node] = BELIEVING

    targets = _media_targets(n_nodes, media_reach, seed)
    directly_exposed = int(targets.size)

    share: list[float] = [float(np.count_nonzero(states == BELIEVING)) / n_nodes]
    for step in range(1, steps + 1):
        if step >= campaign_delay and targets.size:
            for node in targets:
                if states[node] == SUSCEPTIBLE and rng.random() < persuasion:
                    states[node] = BELIEVING
        believing = np.flatnonzero(states == BELIEVING)
        for u_raw in believing:
            u = int(u_raw)
            for v in network[u]:
                if states[v] == SUSCEPTIBLE and rng.random() < spread_rate:
                    states[v] = BELIEVING
        share.append(float(np.count_nonzero(states == BELIEVING)) / n_nodes)

    final_believers = int(np.count_nonzero(states == BELIEVING))
    return SimulationResult(
        steps=steps,
        belief_share=tuple(share),
        final_believers=final_believers,
        total_nodes=n_nodes,
        echo_chamber=echo_chamber_coefficient(network, states),
        amplification=amplification_factor(final_believers, directly_exposed),
        directly_exposed=directly_exposed,
    )


def echo_chamber_coefficient(
    network: tuple[tuple[int, ...], ...], states: np.ndarray
) -> float:
    """Fraction of believing agents whose believing-neighbor share is >= 0.5.

    Returns ``0.0`` when nobody believes (no audience, no echo chamber).
    """
    believing = np.flatnonzero(states == BELIEVING)
    if believing.size == 0:
        return 0.0
    counts = 0
    for u_raw in believing:
        u = int(u_raw)
        neighbors = network[u]
        if not neighbors:
            continue
        believing_neighbors = sum(1 for v in neighbors if states[v] == BELIEVING)
        if believing_neighbors / len(neighbors) >= 0.5:
            counts += 1
    return counts / int(believing.size)


def amplification_factor(final_believers: int, directly_exposed: int) -> float:
    """Belief amplification: final believers per directly exposed node.

    A value above 1 means social spread multiplied the media's direct effect.
    """
    if final_believers < 0 or directly_exposed < 0:
        raise ValueError("counts must be non-negative")
    if directly_exposed == 0:
        return float(final_believers)
    return final_believers / directly_exposed


def influence_maximization(
    network: tuple[tuple[int, ...], ...],
    k: int = 3,
    *,
    seed: int = 7,
    steps: int = 15,
    media_reach: float = 0.3,
    persuasion: float = 0.15,
    spread_rate: float = 0.2,
) -> InfluenceResult:
    """Greedy seed selection maximizing the final belief share.

    Each round, every candidate node is tried as an additional seed by running
    a full deterministic simulation; the candidate with the largest final
    belief share is kept (ties broken by smallest node index). This is the
    classic Kempe–Kleinberg–Tardos greedy approximation for influence
    maximization, made deterministic by the fixed simulation seed.

    Returns:
        :class:`InfluenceResult` with the chosen seeds, achieved share, and
        the number of simulations evaluated.
    """
    n_nodes = len(network)
    if n_nodes == 0:
        raise ValueError("network must not be empty")
    if not isinstance(k, int) or not 1 <= k <= n_nodes:
        raise ValueError("k must be an integer in [1, n_nodes]")
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")

    selected: list[int] = []
    evaluations = 0
    for _ in range(k):
        best_node: int | None = None
        best_share = -1.0
        for candidate in range(n_nodes):
            if candidate in selected:
                continue
            trial = simulate_disinformation(
                network,
                media_reach=media_reach,
                persuasion=persuasion,
                seed=seed,
                steps=steps,
                spread_rate=spread_rate,
                initial_seed_nodes=tuple([*selected, candidate]),
            )
            evaluations += 1
            if trial.belief_share[-1] > best_share:
                best_share = trial.belief_share[-1]
                best_node = candidate
        if best_node is None:
            break
        selected.append(best_node)

    final = simulate_disinformation(
        network,
        media_reach=media_reach,
        persuasion=persuasion,
        seed=seed,
        steps=steps,
        spread_rate=spread_rate,
        initial_seed_nodes=tuple(selected),
    )
    return InfluenceResult(
        seeds=tuple(selected),
        final_share=final.belief_share[-1],
        evaluations=evaluations,
    )
