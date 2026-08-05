"""Bounded-confidence opinion dynamics — Carver's narrative control.

The discrete belief model (:mod:`tomorrow_never_dies.media_manipulation`)
tracks *whether* an agent believes; this module tracks *how strongly* a
continuous opinion moves under media pressure, following the classic
Hegselmann–Krause bounded-confidence model with a Carver-style media
injection term:

* **Bounded-confidence update** — each round, agent ``i`` moves to the mean
  opinion of every agent (including itself) within confidence radius
  ``epsilon``; outside that radius, opinions do not interact. This is the
  mechanism by which echo chambers form and consensus either emerges or
  fragments.
* **Media injection** — a deterministic subset of agents (``media_reach``)
  is additionally pulled toward the manufactured line ``m`` with weight
  ``media_weight``. The pull is Carver's broadcast: reach determines who
  hears it, weight determines how much they move.
* **Metrics** — final consensus, opinion variance (polarization), the
  bimodal split (fraction of agent pairs that end farther apart than
  ``2 * epsilon``), and *media capture*: how far the final mean moved
  toward the manufactured line relative to a no-media baseline.
* **Critical reach** — bisection on the broadcast reach in the discrete
  belief model that just achieves a target belief share: the *minimum*
  audience Carver must reach to tip the network.

Everything is deterministic (seeded draws only in :func:`initial_opinions`;
the HK update itself is a pure averaging operation). Infrastructure-free
(stdlib + numpy only, plus the sibling pure module).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from tomorrow_never_dies.media_manipulation import (
    simulate_disinformation,
)

__all__ = [
    "OpinionResult",
    "bimodal_split",
    "critical_media_reach",
    "initial_opinions",
    "media_capture",
    "polarization_variance",
    "simulate_opinions",
]

#: Bisection iterations for the critical-reach search (deterministic).
_CRITICAL_REACH_ITERATIONS = 40
#: Series-convergence epsilon for the HK mean (defensive only).
_EPSILON = 1e-12


@dataclass(frozen=True)
class OpinionResult:
    """Outcome of a bounded-confidence opinion simulation."""

    steps: int
    #: Initial opinions (deterministic seeded draw).
    initial: tuple[float, ...]
    #: Final opinions after ``steps`` rounds.
    final: tuple[float, ...]
    #: Full trajectory: opinions after each round, including round 0.
    trajectory: tuple[tuple[float, ...], ...]
    #: Final mean opinion.
    consensus: float
    #: Final population variance (polarization measure).
    variance: float
    #: Fraction of agent pairs separated by more than ``2 * confidence``.
    bimodal_split: float
    #: Normalized shift of the final mean toward the media line, in [0, 1].
    media_capture: float


def initial_opinions(n_agents: int, seed: int) -> np.ndarray:
    """Deterministic uniform initial opinions in [0, 1)."""
    if not isinstance(n_agents, int) or n_agents < 2:
        raise ValueError("n_agents must be an integer >= 2")
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    rng = np.random.default_rng(seed)
    return rng.uniform(0.0, 1.0, size=n_agents)


def _hk_update(
    opinions: np.ndarray,
    confidence: float,
    media_opinion: float,
    media_weight: float,
    exposed: np.ndarray,
) -> np.ndarray:
    """One deterministic bounded-confidence round with media injection."""
    distances = np.abs(opinions[None, :] - opinions[:, None])
    within = distances <= confidence
    counts = within.sum(axis=1).astype(float)
    means = (within @ opinions) / counts
    pull = media_weight * exposed
    return (1.0 - pull) * means + pull * media_opinion


def _exposed_mask(n_agents: int, media_reach: float, seed: int) -> np.ndarray:
    """Deterministic exposed subset: first ``round(reach * n)`` seeded draws."""
    count = round(media_reach * n_agents)
    mask = np.zeros(n_agents, dtype=float)
    if count > 0:
        rng = np.random.default_rng(seed)
        indices = rng.choice(n_agents, size=count, replace=False)
        mask[indices] = 1.0
    return mask


def _run_opinions(
    opinions: np.ndarray,
    confidence: float,
    media_opinion: float,
    media_weight: float,
    exposed: np.ndarray,
    steps: int,
) -> list[np.ndarray]:
    """Run the deterministic HK-with-media loop, recording every round."""
    trajectory: list[np.ndarray] = [opinions.copy()]
    current = opinions
    for _ in range(steps):
        current = _hk_update(current, confidence, media_opinion, media_weight, exposed)
        trajectory.append(current.copy())
    return trajectory


def simulate_opinions(
    n_agents: int,
    seed: int,
    *,
    confidence: float = 0.2,
    media_opinion: float = 0.9,
    media_weight: float = 0.06,
    media_reach: float = 0.6,
    steps: int = 30,
) -> OpinionResult:
    """Run bounded-confidence opinion dynamics under a media campaign.

    Args:
        n_agents: Number of agents (>= 2).
        seed: Fixed RNG seed for the initial opinions and exposure set.
        confidence: Bounded-confidence radius ``epsilon`` in (0, 1].
        media_opinion: The manufactured narrative line, in [0, 1].
        media_weight: Per-round pull weight of the media message, in [0, 1].
        media_reach: Fraction of agents exposed to the media message.
        steps: Number of update rounds (>= 1).

    Returns:
        :class:`OpinionResult` with the trajectory and polarization/capture
        metrics (the no-media baseline is simulated internally).
    """
    if not isinstance(n_agents, int) or n_agents < 2:
        raise ValueError("n_agents must be an integer >= 2")
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    for label, value in (
        ("confidence", confidence),
        ("media_opinion", media_opinion),
        ("media_weight", media_weight),
        ("media_reach", media_reach),
    ):
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not 0.0 <= value <= 1.0
        ):
            raise ValueError(f"{label} must be in [0, 1]")
    if confidence == 0.0:
        raise ValueError("confidence must be > 0")
    if not isinstance(steps, int) or steps < 1:
        raise ValueError("steps must be an integer >= 1")

    initial = initial_opinions(n_agents, seed)
    baseline = _run_opinions(
        initial.copy(), confidence, media_opinion, 0.0, np.ones(n_agents), steps
    )
    exposed = _exposed_mask(n_agents, media_reach, seed)
    trajectory = _run_opinions(
        initial.copy(), confidence, media_opinion, media_weight, exposed, steps
    )

    final = trajectory[-1]
    baseline_final = baseline[-1]
    capture = media_capture(final, baseline_final, media_opinion)
    return OpinionResult(
        steps=steps,
        initial=tuple(float(v) for v in initial),
        final=tuple(float(v) for v in final),
        trajectory=tuple(tuple(float(v) for v in frame) for frame in trajectory),
        consensus=float(np.mean(final)),
        variance=polarization_variance(final),
        bimodal_split=bimodal_split(final, confidence),
        media_capture=capture,
    )


def polarization_variance(opinions: np.ndarray) -> float:
    """Population variance of an opinion vector (0 = full consensus)."""
    values = np.asarray(opinions, dtype=float)
    return float(np.mean((values - np.mean(values)) ** 2))


def bimodal_split(opinions: np.ndarray, confidence: float) -> float:
    """Fraction of agent pairs whose opinions are separated by > 2*epsilon.

    A value near 1 means the audience has fragmented into disconnected
    clusters (echo chambers); near 0 means a single connected opinion space.
    """
    values = np.asarray(opinions, dtype=float)
    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not 0.0 < confidence <= 1.0
    ):
        raise ValueError("confidence must be in (0, 1]")
    n_agents = values.size
    if n_agents < 2:
        raise ValueError("opinions must contain at least 2 agents")
    distances = np.abs(values[None, :] - values[:, None])
    separated = distances > 2.0 * confidence
    # Count ordered pairs once (upper triangle, excluding the diagonal).
    pairs = separated[np.triu_indices(n_agents, k=1)]
    return float(np.mean(pairs))


def media_capture(
    final: np.ndarray, baseline: np.ndarray, media_opinion: float
) -> float:
    """Normalized shift of the final mean toward the manufactured line.

    ``capture = (mean_final - mean_baseline) / (media_opinion - mean_baseline)``
    clipped to [0, 1]: 1.0 means the audience mean reached the media line,
    0.0 means the media had no aggregate effect.
    """
    final_mean = float(np.mean(np.asarray(final, dtype=float)))
    baseline_mean = float(np.mean(np.asarray(baseline, dtype=float)))
    if (
        not isinstance(media_opinion, (int, float))
        or isinstance(media_opinion, bool)
        or not 0.0 <= media_opinion <= 1.0
    ):
        raise ValueError("media_opinion must be in [0, 1]")
    denominator = media_opinion - baseline_mean
    if abs(denominator) < _EPSILON:
        return 0.0
    return float(min(1.0, max(0.0, (final_mean - baseline_mean) / denominator)))


def critical_media_reach(
    network: tuple[tuple[int, ...], ...],
    *,
    target_share: float = 0.5,
    seed: int = 7,
    steps: int = 15,
    persuasion: float = 0.12,
    spread_rate: float = 0.05,
    campaign_delay: int = 2,
) -> float:
    """Minimum broadcast reach that tips the belief model to ``target_share``.

    Runs the deterministic disinformation simulation (:mod:`media_manipulation`)
    and bisects on ``media_reach`` to find the smallest audience fraction that
    achieves at least ``target_share`` final believers. Returns ``0.0`` when
    social spread alone already tips the network and ``1.0`` when even full
    reach cannot.

    Args:
        network: Adjacency tuple from :func:`build_network`.
        target_share: Belief-share target in (0, 1).
        seed: Fixed simulation seed.
        steps: Simulation rounds.
        persuasion: Media conversion probability.
        spread_rate: Social conversion probability.
        campaign_delay: Campaign start round.

    Returns:
        The critical reach in [0, 1].
    """
    if not network:
        raise ValueError("network must not be empty")
    if (
        not isinstance(target_share, (int, float))
        or isinstance(target_share, bool)
        or not 0.0 < target_share < 1.0
    ):
        raise ValueError("target_share must be in (0, 1)")
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")

    def share_at(reach: float) -> float:
        result = simulate_disinformation(
            network,
            media_reach=reach,
            persuasion=persuasion,
            seed=seed,
            steps=steps,
            spread_rate=spread_rate,
            campaign_delay=campaign_delay,
        )
        return result.belief_share[-1]

    if share_at(0.0) >= target_share:
        return 0.0
    if share_at(1.0) < target_share:
        return 1.0
    low, high = 0.0, 1.0
    for _ in range(_CRITICAL_REACH_ITERATIONS):
        mid = 0.5 * (low + high)
        if share_at(mid) >= target_share:
            high = mid
        else:
            low = mid
    return 0.5 * (low + high)
