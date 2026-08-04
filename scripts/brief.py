"""CARVER mission phase CLI: brief.

Thin orchestrator — prints the mission brief from the BOND-API provider.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tomorrow_never_dies.mission import MissionProvider


def main() -> int:
    """Render the mission brief for CARVER."""
    brief = MissionProvider().brief()
    print(f"Film:     {brief.film}")
    print(f"Codename: {brief.codename}")
    print("Objectives:")
    for objective in brief.objectives:
        print(f"  - {objective}")
    print("Assets:")
    for asset in brief.assets:
        print(f"  - [{asset.kind}] {asset.name}: {asset.payload}")
    print("Constraints:")
    for constraint in brief.constraints:
        print(f"  - ({constraint.kind}) {constraint.detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
