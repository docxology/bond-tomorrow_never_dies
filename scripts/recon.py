"""CARVER mission phase CLI: recon.

Thin orchestrator — prints the recon findings for a recon goal.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bond_api.protocol import ReconRequest  # type: ignore[import-untyped]

from tomorrow_never_dies.mission import MissionProvider

DEFAULT_GOAL = (
    "assess Carver media-warfare capabilities across broadcast, stealth, and navigation"
)


def main(argv: list[str] | None = None) -> int:
    """Run reconnaissance for the given (or default) goal."""
    args = list(argv) if argv is not None else sys.argv[1:]
    goal = " ".join(args) if args else DEFAULT_GOAL
    report = MissionProvider().recon(ReconRequest(goal=goal))
    print(f"Recon goal: {goal}")
    for finding in report.findings:
        print(f"  - {finding.label}: {finding.detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
