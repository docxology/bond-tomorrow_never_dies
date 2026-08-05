"""Bind the rendered bibliography to ``references.bib``.

``99_references.md`` is the list a reader sees; ``references.bib`` is the same
works in machine-readable form for export and archival metadata. Nothing
previously connected them, so an entry could be added to either alone and the
suite stayed green. These tests make the two lists one claim: same works, same
count, matched on (first-author surname, year).

Zero mocks: both files are parsed off disk.
"""

from __future__ import annotations

import re
from pathlib import Path

BIB_ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,]+),(.*?)\n\}", re.DOTALL)
BIB_FIELD = re.compile(r"(\w+)\s*=\s*\{(.*?)\}\s*,?\s*\n", re.DOTALL)
NUMBERED_ITEM = re.compile(r"^\s*(\d+)\.\s+(.*)$", re.MULTILINE)


def _strip_braces(value: str) -> str:
    return value.replace("{", "").replace("}", "").strip()


def _bib_entries(project_root: Path) -> dict[str, dict[str, str]]:
    text = (project_root / "manuscript" / "references.bib").read_text(encoding="utf-8")
    entries: dict[str, dict[str, str]] = {}
    for _kind, key, body in BIB_ENTRY.findall(text):
        fields = {
            name.lower(): _strip_braces(value)
            for name, value in BIB_FIELD.findall(body + "\n")
        }
        entries[key.strip()] = fields
    return entries


def _first_surname(entry: dict[str, str]) -> str:
    """Surname of the first author, in either BibTeX name order."""
    author = entry.get("author", "")
    if not author:
        return ""
    first = author.split(" and ")[0].strip()
    if "," in first:
        return first.split(",")[0].strip()
    return first.split()[-1].strip()


def _numbered_entries(project_root: Path) -> list[str]:
    text = (project_root / "manuscript" / "99_references.md").read_text(
        encoding="utf-8"
    )
    return [body for _number, body in NUMBERED_ITEM.findall(text)]


def test_bibtex_parses_into_the_expected_shape(project_root: Path) -> None:
    entries = _bib_entries(project_root)
    assert len(entries) >= 10
    for key, fields in entries.items():
        assert fields.get("title"), key
        assert fields.get("year"), key


def test_bibliography_and_bibtex_agree(project_root: Path) -> None:
    """Every BibTeX entry appears in the rendered list, and the counts match.

    This is the gate ``manuscript/SYNTAX.md`` points at. Adding a work to one
    file without the other fails here.
    """
    entries = _bib_entries(project_root)
    numbered = _numbered_entries(project_root)
    assert len(numbered) == len(entries), (
        f"{len(numbered)} numbered references vs {len(entries)} BibTeX entries"
    )

    joined = "\n".join(numbered)
    missing: list[str] = []
    for key, fields in entries.items():
        year = fields["year"]
        anchor = _first_surname(fields) or fields["title"].split(",")[0]
        pattern = re.compile(
            re.escape(anchor.split()[-1]) + r".{0,400}?" + re.escape(year),
            re.DOTALL,
        )
        if not pattern.search(joined):
            missing.append(f"{key} ({anchor} {year})")
    assert missing == [], f"in references.bib but not in 99_references.md: {missing}"


def test_numbered_references_are_sequential(project_root: Path) -> None:
    text = (project_root / "manuscript" / "99_references.md").read_text(
        encoding="utf-8"
    )
    numbers = [int(n) for n, _ in NUMBERED_ITEM.findall(text)]
    assert numbers == list(range(1, len(numbers) + 1))


def test_reference_gate_would_catch_an_unmirrored_bibtex_entry(
    project_root: Path,
) -> None:
    """Positive control: the binding above is not vacuous.

    A BibTeX entry with no counterpart in the numbered list must be reported.
    """
    entries = dict(_bib_entries(project_root))
    entries["fabricated2099"] = {
        "author": "Nobody, A.",
        "title": "A work that is not in the bibliography",
        "year": "2099",
    }
    joined = "\n".join(_numbered_entries(project_root))
    unmatched = [
        key
        for key, fields in entries.items()
        if not re.search(
            re.escape((_first_surname(fields) or fields["title"]).split()[-1])
            + r".{0,400}?"
            + re.escape(fields["year"]),
            joined,
            re.DOTALL,
        )
    ]
    assert unmatched == ["fabricated2099"]
