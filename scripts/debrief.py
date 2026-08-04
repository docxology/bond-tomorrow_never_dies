"""CARVER mission phase CLI: debrief.

Thin orchestrator — runs the full mission and prints the debrief lessons.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bond_api.protocol import (  # type: ignore[import-untyped]
    ReconRequest,
    run_mission,
)

from tomorrow_never_dies.mission import MissionProvider

DEFAULT_GOAL = "debrief the CARVER media-warfare assessment"


def main(argv: list[str] | None = None) -> int:
    """Run the full mission and print lessons learned."""
    args = list(argv) if argv is not None else sys.argv[1:]
    goal = " ".join(args) if args else DEFAULT_GOAL
    provider = MissionProvider()
    debrief = run_mission(provider, ReconRequest(goal=goal))
    outcome = debrief.outcome
    print(f"Mission success: {outcome.success}")
    print("Lessons:")
    for lesson in debrief.lessons:
        print(f"  - {lesson}")
    return 0 if outcome.success else 1


if __name__ == "__main__":
    sys.exit(main())
