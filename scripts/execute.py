"""CARVER mission phase CLI: execute.

Thin orchestrator — executes the mission plan and prints the deterministic
outcome with full provenance.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tomorrow_never_dies.mission import MissionProvider


def main() -> int:
    """Execute the CARVER plan and print the outcome."""
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    print(f"Success: {outcome.success}")
    print("Results:")
    print(json.dumps(outcome.results, sort_keys=True, indent=2))
    provenance = outcome.provenance
    print("Provenance:")
    print(
        json.dumps(
            {
                "package_version": provenance.package_version,
                "seed": provenance.seed,
                "input_hash": provenance.input_hash,
                "wall_time_s": provenance.wall_time_s,
            },
            sort_keys=True,
            indent=2,
        )
    )
    return 0 if outcome.success else 1


if __name__ == "__main__":
    sys.exit(main())
