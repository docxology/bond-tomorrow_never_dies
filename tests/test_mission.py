"""Tests for the CARVER mission provider (BOND-API adaptation).

Zero mocks: the provider runs real domain computation; discovery uses the real
``bond_api`` machinery; serialization round-trips through the real wire format.
"""

from __future__ import annotations

from bond_api.discovery import discover, load_provider
from bond_api.protocol import (
    MissionOutcome,
    ReconRequest,
    run_mission,
)
from bond_api.protocol import (
    MissionProvider as ProtocolProvider,
)
from bond_api.registry import GadgetRegistry
from bond_api.serialization import from_dict, to_dict

from tomorrow_never_dies import CONCEPTS
from tomorrow_never_dies.mission import (
    FILM,
    GADGET_REGISTRY,
    MissionProvider,
    register_gadgets,
)
from tomorrow_never_dies.scenario import canonical_input_hash

GADGET_NAMES = (
    "carver_scenario",
    "critical_reach",
    "matched_filter",
    "media_campaign",
    "navigation_cascade",
    "opinion_dynamics",
    "radar_detection",
    "radar_equation",
    "raim_detection",
)


def test_provider_satisfies_protocol() -> None:
    provider = MissionProvider()
    assert isinstance(provider, ProtocolProvider)


def test_film_identity() -> None:
    assert MissionProvider.film == "tomorrow_never_dies"
    assert MissionProvider().film == FILM


def test_brief() -> None:
    brief = MissionProvider().brief()
    assert brief.film == FILM
    assert brief.codename == "CARVER"
    # One objective per pure-domain concept module.
    assert len(brief.objectives) == len(CONCEPTS)
    assert len(brief.assets) == 3
    assert any(constraint.kind == "determinism" for constraint in brief.constraints)


def test_recon() -> None:
    provider = MissionProvider()
    report = provider.recon(ReconRequest(goal="probe the theater"))
    assert len(report.findings) == 8
    assert report.findings[0].label == "goal"
    assert report.findings[0].detail == "probe the theater"


def test_plan() -> None:
    provider = MissionProvider()
    plan = provider.plan(provider.brief())
    assert [step.name for step in plan.steps] == [
        "media",
        "narrative",
        "stealth",
        "waveform",
        "gps",
        "integrity",
        "synthesize",
    ]
    assert all(step.action for step in plan.steps)


def test_execute() -> None:
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    assert outcome.success is True
    assert outcome.results["steps_completed"] == 7
    assert set(outcome.results["per_step"]) == {
        "media",
        "narrative",
        "stealth",
        "waveform",
        "gps",
        "integrity",
        "synthesize",
    }
    assert outcome.provenance.seed == 7
    assert outcome.provenance.wall_time_s == 0.0
    assert outcome.provenance.input_hash == canonical_input_hash()
    assert outcome.provenance.package_version == "0.1.0"


def test_execute_deterministic() -> None:
    provider = MissionProvider()
    plan = provider.plan(provider.brief())
    first = provider.execute(plan)
    second = provider.execute(plan)
    assert first.results == second.results
    assert first.provenance.input_hash == second.provenance.input_hash


def test_debrief() -> None:
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    debrief = provider.debrief(outcome)
    assert len(debrief.lessons) >= 3
    assert debrief.outcome is outcome
    assert all(isinstance(lesson, str) and lesson for lesson in debrief.lessons)


def test_debrief_quantities_are_derived_not_hardcoded() -> None:
    """Every number the debrief quotes must come from the executed outcome.

    Guards against a lesson string drifting from the scenario: the RCS
    reduction and range ratio are re-derived here from the outcome's own
    ``per_step`` block and must appear verbatim in the lesson text.
    """
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    stealth = outcome.results["per_step"]["stealth"]
    lessons = provider.debrief(outcome).lessons
    quantitative = [text for text in lessons if "RCS" in text and "dB" in text]
    assert len(quantitative) == 1
    assert f"{stealth['rcs_reduction_db']:.0f} dB" in quantitative[0]
    assert f"{stealth['range_ratio']:.3f}" in quantitative[0]


def test_debrief_without_per_step_omits_quantities() -> None:
    """A results payload with no ``per_step`` yields only the fixed lessons."""
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    bare = MissionOutcome(
        success=outcome.success,
        results={"steps_completed": 0},
        provenance=outcome.provenance,
    )
    lessons = provider.debrief(bare).lessons
    assert len(lessons) == 6
    assert not any("belief share" in lesson for lesson in lessons)


def test_run_mission_full_flow() -> None:
    provider = MissionProvider()
    debrief = run_mission(provider, ReconRequest(goal="full flow"))
    assert debrief.outcome.success is True
    assert len(debrief.lessons) >= 3


def test_gadget_registry_registration() -> None:
    assert FILM in GADGET_REGISTRY
    for name in GADGET_NAMES:
        assert GADGET_REGISTRY.contains(FILM, name)
        assert callable(GADGET_REGISTRY.lookup(FILM, name))


def test_register_gadgets_fresh_registry() -> None:
    registry = GadgetRegistry()
    returned = register_gadgets(registry)
    assert returned is registry
    assert registry.contains(FILM, "media_campaign")


def test_discovery_load_provider() -> None:
    provider = load_provider("tomorrow_never_dies")
    assert isinstance(provider, ProtocolProvider)
    assert provider.film == "tomorrow_never_dies"


def test_discovery_autodiscover() -> None:
    found = discover(slugs=["tomorrow_never_dies"])
    assert "tomorrow_never_dies" in found


def test_serialization_round_trip() -> None:
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    restored = from_dict(to_dict(outcome))
    assert restored == outcome
