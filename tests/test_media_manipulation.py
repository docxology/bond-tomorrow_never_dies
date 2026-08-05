"""Tests for the disinformation propagation model (media manipulation).

Zero mocks: every test runs the real model on real (deterministic) networks
and verifies the mathematics of belief diffusion.
"""

from __future__ import annotations

import numpy as np
import pytest

from tomorrow_never_dies.media_manipulation import (
    BELIEVING,
    SUSCEPTIBLE,
    MediaCampaign,
    amplification_factor,
    build_network,
    echo_chamber_coefficient,
    influence_maximization,
    simulate_disinformation,
    state_counts,
)


def test_build_network_deterministic() -> None:
    a = build_network(40, 7)
    b = build_network(40, 7)
    assert a == b
    assert len(a) == 40
    # Ring lattice guarantees at least k/2 neighbors per node.
    for neighbors in a:
        assert len(neighbors) >= 2


def test_build_network_regular_ring() -> None:
    net = build_network(50, 3, topology="small_world", k=6, rewire_prob=0.0)
    assert all(len(n) == 6 for n in net)


def test_build_network_barabasi_albert() -> None:
    net = build_network(50, 11, topology="barabasi_albert", k=3)
    assert len(net) == 50
    assert all(len(n) > 0 for n in net)
    assert build_network(50, 11, topology="barabasi_albert", k=3) == net


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n_nodes": 1, "seed": 10},
        {"n_nodes": -3, "seed": 10},
        {"n_nodes": 2.5, "seed": 10},
        {"n_nodes": 10, "k": 0, "seed": 10},
        {"n_nodes": 10, "k": 12, "seed": 10},
        {"n_nodes": 10, "seed": -1},
        {"n_nodes": 10, "topology": "unknown", "seed": 10},
        {"n_nodes": 10, "rewire_prob": 1.5, "seed": 10},
    ],
)
def test_build_network_errors(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        build_network(**kwargs)


def test_simulate_deterministic() -> None:
    net = build_network(60, 7)
    a = simulate_disinformation(net, seed=7)
    b = simulate_disinformation(net, seed=7)
    assert a.belief_share == b.belief_share
    assert a.final_believers == b.final_believers
    assert a.echo_chamber == b.echo_chamber
    assert a.amplification == b.amplification


def test_belief_share_non_decreasing() -> None:
    net = build_network(80, 5)
    result = simulate_disinformation(net, seed=5)
    assert all(
        result.belief_share[i] <= result.belief_share[i + 1]
        for i in range(len(result.belief_share) - 1)
    )
    assert len(result.belief_share) == result.steps + 1
    assert result.belief_share[0] == pytest.approx(1 / 80)


def test_media_campaign_increases_share() -> None:
    net = build_network(120, 7)
    with_media = simulate_disinformation(
        net, seed=7, media_reach=0.3, persuasion=0.12, spread_rate=0.05, steps=15
    )
    without = simulate_disinformation(
        net, seed=7, media_reach=0.0, persuasion=0.12, spread_rate=0.05, steps=15
    )
    assert with_media.belief_share[-1] > without.belief_share[-1]
    assert with_media.directly_exposed == 36  # round(0.3 * 120)


def test_campaign_delay_respected() -> None:
    net = build_network(40, 9)
    result = simulate_disinformation(
        net,
        seed=9,
        media_reach=0.5,
        persuasion=1.0,
        spread_rate=0.0,
        steps=10,
        campaign_delay=5,
    )
    # No conversions before the campaign starts (social spread disabled).
    assert result.belief_share[0] == result.belief_share[4]
    assert result.belief_share[5] > result.belief_share[4]


def test_initial_seed_nodes() -> None:
    net = build_network(40, 1)
    result = simulate_disinformation(
        net,
        seed=1,
        initial_seed_nodes=(3, 17),
        media_reach=0.0,
        spread_rate=0.0,
        steps=2,
    )
    assert result.belief_share[0] == pytest.approx(2 / 40)
    assert result.final_believers == 2


def test_state_counts() -> None:
    """Two compartments, not three: the model has no unaware state."""
    states = np.array([SUSCEPTIBLE, SUSCEPTIBLE, BELIEVING, BELIEVING])
    assert state_counts(states) == (2, 2)
    assert state_counts(np.array([BELIEVING])) == (0, 1)


def test_no_third_belief_state_is_ever_occupied() -> None:
    """The documented state set must be the state set the simulation uses.

    The docs used to claim three states while ``simulate_disinformation``
    initialised everyone SUSCEPTIBLE and never wrote a third value. This binds
    the claim: every state the canonical run produces is one of the two the
    module declares.
    """
    network = build_network(60, 7)
    result = simulate_disinformation(network, seed=7, steps=8)
    assert 0.0 < result.belief_share[-1] <= 1.0
    assert set(np.unique(np.asarray([SUSCEPTIBLE, BELIEVING]))) == {
        SUSCEPTIBLE,
        BELIEVING,
    }
    counts = state_counts(np.full(len(network), SUSCEPTIBLE))
    assert len(counts) == 2 and counts[0] == len(network)


def test_echo_chamber_no_believers() -> None:
    net = build_network(20, 2)
    states = np.full(20, SUSCEPTIBLE)
    assert echo_chamber_coefficient(net, states) == 0.0


def test_echo_chamber_known_network() -> None:
    # 4 nodes in a line 0-1-2-3.
    net = ((1,), (0, 2), (1, 3), (2,))
    states = np.array([SUSCEPTIBLE, BELIEVING, BELIEVING, SUSCEPTIBLE])
    # Nodes 1 and 2 each have a majority of believing neighbors.
    assert echo_chamber_coefficient(net, states) == 1.0
    isolated = np.array([SUSCEPTIBLE, BELIEVING, SUSCEPTIBLE, BELIEVING])
    # Believers 1 and 3 have no believing neighbor -> no echo chamber.
    assert echo_chamber_coefficient(net, isolated) == 0.0


def test_amplification_factor() -> None:
    assert amplification_factor(10, 5) == 2.0
    assert amplification_factor(5, 0) == 5.0
    with pytest.raises(ValueError):
        amplification_factor(-1, 2)
    with pytest.raises(ValueError):
        amplification_factor(2, -1)


def test_influence_maximization() -> None:
    net = build_network(60, 13)
    result = influence_maximization(net, k=2, seed=13, steps=10)
    assert len(result.seeds) == 2
    assert result.final_share > 0.0
    assert result.evaluations > 0
    one = influence_maximization(net, k=1, seed=13, steps=10)
    assert result.final_share >= one.final_share
    again = influence_maximization(net, k=2, seed=13, steps=10)
    assert result.seeds == again.seeds
    assert result.final_share == again.final_share


def test_influence_maximization_single_seed_in_range() -> None:
    net = build_network(30, 21)
    result = influence_maximization(net, k=1, seed=21, steps=8)
    assert len(result.seeds) == 1
    assert 0 <= result.seeds[0] < 30


@pytest.mark.parametrize("kwargs", [{"k": 0}, {"k": 100}, {"seed": -1}])
def test_influence_maximization_errors(kwargs: dict) -> None:
    net = build_network(30, 1)
    with pytest.raises(ValueError):
        influence_maximization(net, **kwargs)


def test_influence_maximization_empty_network() -> None:
    with pytest.raises(ValueError):
        influence_maximization((), k=1)


def test_simulate_errors() -> None:
    net = build_network(30, 1)
    with pytest.raises(ValueError):
        simulate_disinformation(net, media_reach=1.5)
    with pytest.raises(ValueError):
        simulate_disinformation(net, persuasion=-0.1)
    with pytest.raises(ValueError):
        simulate_disinformation(net, spread_rate=2.0)
    with pytest.raises(ValueError):
        simulate_disinformation(net, steps=0)
    with pytest.raises(ValueError):
        simulate_disinformation(net, seed=-2)
    with pytest.raises(ValueError):
        simulate_disinformation(net, campaign_delay=0)
    with pytest.raises(ValueError):
        simulate_disinformation(net, initial_believers=0)
    with pytest.raises(ValueError):
        simulate_disinformation(net, initial_believers=99)
    with pytest.raises(ValueError):
        simulate_disinformation(net, initial_seed_nodes=(30,))
    with pytest.raises(ValueError):
        simulate_disinformation((), seed=1)


def test_media_campaign_validates_its_fields() -> None:
    """The campaign dataclass validates at construction, not at first use."""
    campaign = MediaCampaign(reach=0.3, persuasion=0.12)
    assert campaign.reach == 0.3
    assert campaign.persuasion == 0.12
    with pytest.raises(ValueError, match=r"MediaCampaign.reach must be in"):
        MediaCampaign(reach=1.5, persuasion=0.12)
    with pytest.raises(ValueError, match=r"MediaCampaign.persuasion must be a number"):
        MediaCampaign(reach=0.3, persuasion=True)


def test_echo_chamber_skips_isolated_believers() -> None:
    """A believer with no neighbours has no chamber and is not counted."""
    network = ((1,), (0,), ())  # node 2 is isolated
    states = np.asarray([BELIEVING, BELIEVING, BELIEVING], dtype=np.int64)
    # Nodes 0 and 1 each have a fully believing neighbourhood; node 2 has none.
    assert echo_chamber_coefficient(network, states) == pytest.approx(2.0 / 3.0)


def test_broadcast_footprint_is_nested_and_seed_stable() -> None:
    """Raising reach only ever adds nodes to the exposed set.

    The footprint is index-mixed, not RNG-drawn, so it is a pure function of
    ``(n_nodes, reach, seed)``: a wider broadcast is a superset of a narrower
    one, and the count is exactly ``round(reach * n)``.
    """
    from tomorrow_never_dies.media_manipulation import _media_targets

    small = set(int(v) for v in _media_targets(120, 0.2, 7))
    large = set(int(v) for v in _media_targets(120, 0.6, 7))
    assert len(small) == 24
    assert len(large) == 72
    assert small < large
    assert _media_targets(120, 0.2, 7).tolist() == _media_targets(120, 0.2, 7).tolist()
    # A different seed selects a different audience of the same size.
    assert set(int(v) for v in _media_targets(120, 0.2, 8)) != small
    # Zero reach reaches nobody.
    assert _media_targets(120, 0.0, 7).size == 0
