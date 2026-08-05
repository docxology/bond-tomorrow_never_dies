"""CARVER — the BOND-API mission provider for *Tomorrow Never Dies* (1997).

This module is the thin adapter between the pure domain core
(:mod:`tomorrow_never_dies.media_manipulation`,
:mod:`tomorrow_never_dies.stealth_detection`,
:mod:`tomorrow_never_dies.gps_denial`,
:mod:`tomorrow_never_dies.narrative_control`,
:mod:`tomorrow_never_dies.radar_waveform`,
:mod:`tomorrow_never_dies.gnss_integrity`,
:mod:`tomorrow_never_dies.scenario`)
and the frozen ``bond_api`` protocol (codename THE PROTOCOL).

Discovery contract: the orchestrator imports ``<slug>.mission``, instantiates
the ``MissionProvider`` class, binds ``film`` if undeclared, and verifies the
runtime-checkable protocol. This module therefore exposes ``MissionProvider``
at module top level (the stable name --- the public shape is frozen and shared
across the fleet) and registers the film's gadgets with a
:class:`bond_api.registry.GadgetRegistry` at import time.
"""

from __future__ import annotations

from typing import Any

from bond_api.protocol import (  # type: ignore[import-untyped]
    Asset,
    Constraint,
    Debrief,
    Finding,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
)
from bond_api.registry import GadgetRegistry  # type: ignore[import-untyped]

from tomorrow_never_dies import CODENAME, __version__
from tomorrow_never_dies.gnss_integrity import (
    detection_probability as raim_detection_probability,
)
from tomorrow_never_dies.gps_denial import simulate_navigation_cascade
from tomorrow_never_dies.media_manipulation import simulate_disinformation
from tomorrow_never_dies.narrative_control import (
    critical_media_reach,
    simulate_opinions,
)
from tomorrow_never_dies.radar_waveform import compress
from tomorrow_never_dies.scenario import (
    SCENARIO_PARAMS,
    SCENARIO_SEED,
    run_carver_scenario,
)
from tomorrow_never_dies.stealth_detection import detection_probability, snr_at_range

__all__ = ["GADGETS", "GADGET_REGISTRY", "MissionProvider", "register_gadgets"]

#: The stable film slug this provider answers to (matches the package name).
FILM = "tomorrow_never_dies"

#: Gadgets this film registers with the BOND GadgetRegistry: the domain
#: callables that back the mission's capabilities. Payloads are opaque to the
#: registry --- it stores and returns whatever the film registered.
GADGETS: dict[str, Any] = {
    "media_campaign": simulate_disinformation,
    "opinion_dynamics": simulate_opinions,
    "critical_reach": critical_media_reach,
    "radar_detection": detection_probability,
    "radar_equation": snr_at_range,
    "matched_filter": compress,
    "navigation_cascade": simulate_navigation_cascade,
    "raim_detection": raim_detection_probability,
    "carver_scenario": run_carver_scenario,
}


def register_gadgets(registry: GadgetRegistry) -> GadgetRegistry:
    """Register CARVER's gadgets on a :class:`GadgetRegistry` (idempotent merge)."""
    registry.register(FILM, GADGETS)
    return registry


#: Module-level registration so discovery and coordinators see the gadgets
#: the moment the film is imported.
GADGET_REGISTRY = register_gadgets(GadgetRegistry())


class MissionProvider:
    """Deterministic CARVER mission provider over the three domain concepts."""

    film = FILM

    def brief(self) -> MissionBrief:
        """Declare the CARVER mission: three objectives, three concept assets."""
        radar = SCENARIO_PARAMS["stealth"]["radar"]
        return MissionBrief(
            film=self.film,
            codename=CODENAME,
            objectives=(
                "model Carver-style disinformation propagation on a social network",
                "quantify low-RCS stealth-vessel detection limits",
                "analyze GPS-denial impact and navigation failure cascades",
            ),
            assets=(
                Asset(
                    kind="model",
                    name="media_network",
                    payload={
                        "nodes": SCENARIO_PARAMS["media"]["network_size"],
                        "topology": SCENARIO_PARAMS["media"]["topology"],
                    },
                ),
                Asset(
                    kind="model",
                    name="radar_equation",
                    payload={
                        "frequency_hz": radar["frequency_hz"],
                        "pulses": radar["pulses"],
                    },
                ),
                Asset(
                    kind="model",
                    name="gps_constellation",
                    payload={
                        "satellites": SCENARIO_PARAMS["gps"]["n_sats"],
                        "mask_angle_deg": SCENARIO_PARAMS["gps"]["mask_angle_deg"],
                    },
                ),
            ),
            constraints=(
                Constraint(
                    kind="determinism",
                    detail="fixed seed 7; no random draws without seeding",
                ),
                Constraint(
                    kind="fidelity",
                    detail="real radar/navigation physics; no mocked data",
                ),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the request against the six available concept assets."""
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(
                    label="media",
                    detail="belief diffusion + bounded-confidence opinion dynamics with media injection",
                ),
                Finding(
                    label="narrative",
                    detail="Hegselmann-Krause echo chambers and critical broadcast reach",
                ),
                Finding(
                    label="stealth",
                    detail="radar equation with Marcum-Q / Swerling detection probabilities",
                ),
                Finding(
                    label="waveform",
                    detail="pulse compression: LFM / Barker-13 processing gain and resolution",
                ),
                Finding(
                    label="gps",
                    detail="DOP geometry, jamming degradation, and failure cascades",
                ),
                Finding(
                    label="integrity",
                    detail="RAIM detection thresholds, HPL/VPL protection levels",
                ),
                Finding(
                    label="constraints",
                    detail="deterministic execution required; inputs hashed for provenance",
                ),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the seven steps: two per concept family plus synthesis."""
        return MissionPlan(
            steps=(
                Step(
                    name="media",
                    action="simulate_disinformation",
                    params={
                        "network_size": SCENARIO_PARAMS["media"]["network_size"],
                        "steps": SCENARIO_PARAMS["media"]["steps"],
                    },
                ),
                Step(
                    name="narrative",
                    action="bounded_confidence_opinions",
                    params={
                        "media_opinion": SCENARIO_PARAMS["narrative"]["media_opinion"],
                        "media_reach": SCENARIO_PARAMS["narrative"]["media_reach"],
                    },
                ),
                Step(
                    name="stealth",
                    action="detection_range_analysis",
                    params={
                        "p_fa": SCENARIO_PARAMS["stealth"]["pfa"],
                        "p_d_target": SCENARIO_PARAMS["stealth"]["p_d_target"],
                    },
                ),
                Step(
                    name="waveform",
                    action="pulse_compression",
                    params={
                        "kind": SCENARIO_PARAMS["waveform"]["kind"],
                        "bandwidth_mhz": SCENARIO_PARAMS["waveform"]["bandwidth_hz"]
                        / 1.0e6,
                    },
                ),
                Step(
                    name="gps",
                    action="gps_denial_analysis",
                    params={
                        "jamming_strength": SCENARIO_PARAMS["gps"]["jamming_strength"],
                        "fail_threshold": SCENARIO_PARAMS["gps"]["fail_threshold"],
                    },
                ),
                Step(
                    name="integrity",
                    action="raim_integrity",
                    params={
                        "p_fa": SCENARIO_PARAMS["integrity"]["p_fa"],
                        "alert_limit_m": SCENARIO_PARAMS["integrity"]["alert_limit_m"],
                    },
                ),
                Step(
                    name="synthesize",
                    action="assemble_mission_outcome",
                    params={"objectives": len(brief.objectives), "seed": SCENARIO_SEED},
                ),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the plan against the real domain modules; deterministic outcome.

        Every step in the plan maps to an actual computation over the scenario
        parameters, and the outcome carries full provenance (package version,
        seed, canonical input hash, zero wall-clock).
        """
        scenario = run_carver_scenario(seed=SCENARIO_SEED)
        media = scenario["media"]
        narrative = scenario["narrative"]
        stealth = scenario["stealth"]
        waveform = scenario["waveform"]
        gps = scenario["gps"]
        integrity = scenario["integrity"]

        per_step: dict[str, Any] = {}
        for step in plan.steps:
            if step.name == "media":
                per_step["media"] = {
                    "nodes": media["nodes"],
                    "final_believers": media["final_believers"],
                    "belief_share": media["belief_share"],
                    "echo_chamber": media["echo_chamber"],
                    "amplification": media["amplification"],
                    "directly_exposed": media["directly_exposed"],
                }
            elif step.name == "narrative":
                per_step["narrative"] = {
                    "consensus": narrative["consensus"],
                    "polarization_variance": narrative["polarization_variance"],
                    "bimodal_split": narrative["bimodal_split"],
                    "media_capture": narrative["media_capture"],
                    "critical_reach": narrative["critical_reach"],
                }
            elif step.name == "stealth":
                per_step["stealth"] = {
                    "reference_range_m": stealth["reference_range_m"],
                    "stealth_range_m": stealth["stealth_range_m"],
                    "rcs_reduction_db": stealth["rcs_reduction_db"],
                    "range_ratio": stealth["range_ratio"],
                }
            elif step.name == "waveform":
                per_step["waveform"] = {
                    "kind": waveform["kind"],
                    "range_resolution_m": waveform["range_resolution_m"],
                    "gain_db": waveform["gain_db"],
                    "pslr_db": waveform["pslr_db"],
                    "detection_range_m": waveform["detection_range_m"],
                    "improvement_pct": waveform["improvement_pct"],
                }
            elif step.name == "gps":
                per_step["gps"] = {
                    "visible_satellites": gps["visible_satellites"],
                    "pdop": gps["pdop"],
                    "jnr_db": gps["jnr_db"],
                    "error_clean_m": gps["error_clean_m"],
                    "error_jammed_m": gps["error_jammed_m"],
                    "cascade_fraction": gps["cascade_fraction"],
                    "cascade_rounds": gps["cascade_rounds"],
                    "cascade_failed": gps["cascade_failed"],
                }
            elif step.name == "integrity":
                per_step["integrity"] = {
                    "dof": integrity["dof"],
                    "threshold": integrity["threshold"],
                    "hpl_m": integrity["hpl_m"],
                    "vpl_m": integrity["vpl_m"],
                    "detection_probability": integrity["detection_probability"],
                    "available": integrity["available"],
                }
            else:
                per_step["synthesize"] = {
                    "objectives": step.params.get("objectives"),
                    "seed": step.params.get("seed"),
                }

        return MissionOutcome(
            success=True,
            results={
                "steps_completed": len(plan.steps),
                "outputs": tuple(step.name for step in plan.steps),
                "per_step": per_step,
                "input_hash": scenario["input_hash"],
            },
            provenance=Provenance(
                package_version=__version__,
                seed=SCENARIO_SEED,
                input_hash=scenario["input_hash"],
                wall_time_s=0.0,
            ),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarize the mission and record CARVER's standing lessons."""
        results = outcome.results
        per_step = results.get("per_step", {})
        lessons = [
            "media control converts exposure into belief; social spread amplifies the campaign",
            "bounded confidence lets a selective broadcast split the audience into echo chambers",
            "a 20 dB RCS reduction cuts detection range by ~two-thirds (fourth-root law)",
            "pulse compression restores detection range against a stealth hull",
            "GPS denial cascades through navigation dependencies: one jammed receiver can fail a fleet",
            "RAIM bounds the position error a corrupt navigation measurement can hide",
        ]
        if per_step:
            media_b = per_step.get("media", {})
            gps_b = per_step.get("gps", {})
            wave_b = per_step.get("waveform", {})
            lessons.append(
                f"belief share {media_b.get('belief_share', 0.0):.3f}; "
                f"compression gain {wave_b.get('gain_db', 0.0):.1f} dB; "
                f"cascade fraction {gps_b.get('cascade_fraction', 0.0):.3f}"
            )
        return Debrief(outcome=outcome, lessons=tuple(lessons))
