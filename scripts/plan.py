"""CARVER mission phase CLI: plan.

Thin orchestrator — prints the mission plan derived from the brief.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tomorrow_never_dies.mission import MissionProvider


def main() -> int:
    """Render the CARVER mission plan."""
    provider = MissionProvider()
    plan = provider.plan(provider.brief())
    for index, step in enumerate(plan.steps, start=1):
        print(f"{index}. {step.name} [{step.action}] {step.params}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
