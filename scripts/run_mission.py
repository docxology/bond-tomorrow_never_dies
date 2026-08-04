"""CARVER mission CLI: full five-stage run.

Thin orchestrator — drives brief → recon → plan → execute → debrief through
the frozen ``bond_api.run_mission`` flow and prints every stage's output.
Exit code is 0 iff the mission outcome reports success.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bond_api.protocol import ReconRequest  # type: ignore[import-untyped]

from tomorrow_never_dies.mission import MissionProvider

DEFAULT_GOAL = "run the full CARVER assessment: media, stealth, and navigation denial"


def main(argv: list[str] | None = None) -> int:
    """Execute the complete CARVER mission flow."""
    args = list(argv) if argv is not None else sys.argv[1:]
    goal = " ".join(args) if args else DEFAULT_GOAL
    provider = MissionProvider()

    brief = provider.brief()
    print(f"=== BRIEF: {brief.film} / {brief.codename} ===")
    for objective in brief.objectives:
        print(f"  objective: {objective}")

    report = provider.recon(ReconRequest(goal=goal))
    print("=== RECON ===")
    for finding in report.findings:
        print(f"  {finding.label}: {finding.detail}")

    plan = provider.plan(brief)
    print("=== PLAN ===")
    for index, step in enumerate(plan.steps, start=1):
        print(f"  {index}. {step.name} [{step.action}]")

    outcome = provider.execute(plan)
    print(f"=== EXECUTE: success={outcome.success} ===")
    print(f"  steps completed: {outcome.results['steps_completed']}")
    print(f"  input hash: {outcome.provenance.input_hash}")
    print(f"  seed: {outcome.provenance.seed}")

    debrief = provider.debrief(outcome)
    print("=== DEBRIEF ===")
    for lesson in debrief.lessons:
        print(f"  - {lesson}")

    return 0 if outcome.success else 1


if __name__ == "__main__":
    sys.exit(main())
