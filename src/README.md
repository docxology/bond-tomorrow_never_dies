# src/tomorrow_never_dies/ — CARVER Domain Core

Deterministic mission-software core for **Tomorrow Never Dies** (1997),
codename **CARVER**. Pure domain modules (stdlib + numpy only) implement the
three concepts; `mission.py` adapts them to the FROZEN `bond_api`
`MissionProvider` protocol.

```python
from tomorrow_never_dies.scenario import run_carver_scenario

scenario = run_carver_scenario()  # deterministic, seed 7

from tomorrow_never_dies.mission import MissionProvider

provider = MissionProvider()
print(provider.brief().codename)  # CARVER
```

Public surface: see [`AGENTS.md`](AGENTS.md). Verification:
`uv run pytest tests/ --cov=src --cov-fail-under=90`.
