"""CARVER manuscript variable hydration + figure rendering.

Thin orchestrator: computes the ``{{TOKEN}}`` map from
``manuscript/config.yaml`` and the real domain modules, writes it to
``output/data/manuscript_variables.json``, renders the concept figures under
``output/figures/``, and writes the resolved manuscript tree to
``output/manuscript/``. Fails loudly when any ``{{TOKEN}}`` in a numbered
prose section remains unresolved.

Strict by design: there is no draft mode — every token in the prose sections
must resolve, because the metrics are computed, not hand-authored.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tomorrow_never_dies.figures import render_figures
from tomorrow_never_dies.manuscript_variables import generate_variables

_TOKEN_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


def main() -> int:
    """Hydrate manuscript variables, render figures, resolve the prose tree."""
    project_root = Path(__file__).resolve().parent.parent
    variables = generate_variables(project_root)

    data_dir = project_root / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    variables_path = data_dir / "manuscript_variables.json"
    variables_path.write_text(
        json.dumps(variables, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )

    figures = render_figures(project_root)

    manuscript_dir = project_root / "manuscript"
    resolved_dir = project_root / "output" / "manuscript"
    resolved_dir.mkdir(parents=True, exist_ok=True)
    sections = sorted(manuscript_dir.glob("[0-9]*.md"))
    unresolved: list[str] = []
    for section in sections:
        text = section.read_text(encoding="utf-8")
        resolved = _TOKEN_RE.sub(lambda m: variables.get(m.group(1), m.group(0)), text)
        (resolved_dir / section.name).write_text(resolved, encoding="utf-8")
        leftovers = sorted(set(_TOKEN_RE.findall(resolved)))
        if leftovers:
            unresolved.append(f"{section.name}: {leftovers}")

    if unresolved:
        print("UNRESOLVED TOKENS:")
        for entry in unresolved:
            print(f"  {entry}")
        return 1

    print(f"wrote {variables_path}")
    print(f"resolved {len(sections)} prose sections -> {resolved_dir}")
    for name, path in sorted(figures.items()):
        print(f"figure {name}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
