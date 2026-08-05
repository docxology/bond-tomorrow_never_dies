"""Tests for manuscript variable generation and the live {{TOKEN}} gate."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from tomorrow_never_dies.manuscript_variables import (
    generate_variables,
    load_mission_config,
)

TOKEN_KEYS = (
    "CARVER_IDENTITY",
    "CARVER_SUBTITLE",
    "CARVER_CODENAME",
    "CARVER_VERSION",
    "CARVER_AUTHOR",
    "CARVER_KEYWORDS",
    "CARVER_OBJECTIVES",
    "CARVER_SEED",
    "MEDIA_NODES",
    "MEDIA_BELIEF_SHARE_PCT",
    "MEDIA_ECHO_CHAMBER",
    "MEDIA_AMPLIFICATION",
    "NARRATIVE_MEDIA_OPINION",
    "NARRATIVE_CONSENSUS",
    "NARRATIVE_POLARIZATION",
    "NARRATIVE_BIMODAL_SPLIT",
    "NARRATIVE_MEDIA_CAPTURE",
    "NARRATIVE_CRITICAL_REACH_PCT",
    "STEALTH_REF_RANGE_KM",
    "STEALTH_RANGE_KM",
    "STEALTH_RCS_REDUCTION_DB",
    "STEALTH_RANGE_RATIO",
    "WAVEFORM_BANDWIDTH_MHZ",
    "WAVEFORM_RES_M",
    "WAVEFORM_GAIN_DB",
    "WAVEFORM_PSLR_DB",
    "WAVEFORM_RANGE_KM",
    "WAVEFORM_IMPROVEMENT_PCT",
    "GPS_PDOP",
    "GPS_JNR_DB",
    "GPS_ERROR_CLEAN_M",
    "GPS_ERROR_JAMMED_M",
    "GPS_CASCADE_FRACTION",
    "GPS_CASCADE_ROUNDS",
    "RAIM_DOF",
    "RAIM_THRESHOLD",
    "RAIM_HPL_M",
    "RAIM_VPL_M",
    "RAIM_BIAS_M",
    "RAIM_PROJECTION_WORST",
    "RAIM_PROJECTION_BEST",
    "RAIM_PD",
    "RAIM_PD_BEST",
    "GPS_VISIBLE_SATS",
    "GPS_CNO_JAMMED_DBHZ",
    "GPS_LOCK_THRESHOLD_DBHZ",
    "WAVEFORM_UNMOD_RANGE_KM",
    "WAVEFORM_UNMOD_WIDTH_US",
    "PYTHON_VERSION",
    "MANUSCRIPT_DATE",
)


def test_load_mission_config(project_root: Path) -> None:
    config = load_mission_config(project_root)
    assert config["paper"]["title"].startswith("Tomorrow Never Dies")
    assert config["paper"]["codename"] == "CARVER" or config["paper"].get("subtitle")


def test_load_mission_config_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_mission_config(tmp_path / "nope")


def test_load_mission_config_not_mapping(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "config.yaml").write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_mission_config(tmp_path)


def test_generate_variables_keys(project_root: Path) -> None:
    variables = generate_variables(project_root)
    for key in TOKEN_KEYS:
        assert key in variables, key
    assert variables["CARVER_CODENAME"] == "CARVER"
    assert float(variables["STEALTH_RCS_REDUCTION_DB"]) == pytest.approx(20.0)
    assert float(variables["STEALTH_RANGE_RATIO"]) == pytest.approx(
        0.316227766, rel=1e-3
    )
    assert float(variables["GPS_ERROR_JAMMED_M"]) > float(
        variables["GPS_ERROR_CLEAN_M"]
    )
    assert float(variables["MEDIA_BELIEF_SHARE_PCT"]) > 0.0


def test_generate_variables_deterministic(project_root: Path) -> None:
    assert generate_variables(project_root) == generate_variables(project_root)


def test_manuscript_date_is_the_committed_config_value(project_root: Path) -> None:
    """The date token is read from config, not from the clock.

    Binds the token to ``paper.date`` by value, so replacing the committed
    date with anything clock-derived (which would not equal the config field
    on any day but one) fails here as well as in the byte-identity test.
    """
    config = load_mission_config(project_root)
    committed = config["paper"]["date"]
    committed = committed if isinstance(committed, str) else committed.isoformat()
    variables = generate_variables(project_root)
    assert variables["MANUSCRIPT_DATE"] == committed


def test_no_generated_token_looks_like_a_wall_clock(project_root: Path) -> None:
    """No persisted token may carry a time-of-day.

    A date alone cannot distinguish "committed" from "today", but a *time*
    can only have come from a clock. This is the cheap in-process guard; the
    real one is ``test_regeneration_is_byte_identical``.
    """
    variables = generate_variables(project_root)
    clockish = re.compile(r"\d{1,2}:\d{2}(:\d{2})?")
    offenders = sorted(k for k, v in variables.items() if clockish.search(v))
    assert offenders == []


def test_generate_variables_requires_a_committed_date(
    project_root: Path, tmp_path: Path
) -> None:
    """A missing ``paper.date`` is an error, never a silent clock read."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = (project_root / "manuscript" / "config.yaml").read_text(encoding="utf-8")
    config = yaml.safe_load(source)
    config["paper"].pop("date", None)
    (manuscript / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(ValueError, match=r"paper\.date"):
        generate_variables(tmp_path)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('date: "2026-08-04"', "2026-08-04"),
        ("date: 2026-08-04", "2026-08-04"),
        ("date: 2026-08-04 12:00:00", "2026-08-04"),
    ],
)
def test_manuscript_date_normalises_yaml_scalar_forms(
    project_root: Path, tmp_path: Path, raw: str, expected: str
) -> None:
    """Quoted str, bare date, and bare datetime all render the same token.

    PyYAML resolves these three spellings to ``str``, ``datetime.date`` and
    ``datetime.datetime`` respectively; the rendered manuscript must not
    depend on which one the config happens to use.
    """
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    config = yaml.safe_load(
        (project_root / "manuscript" / "config.yaml").read_text(encoding="utf-8")
    )
    config["paper"].pop("date", None)
    text = yaml.safe_dump(config) + "\n"
    # Re-inject the date verbatim so the YAML scalar form is preserved.
    text = text.replace("paper:\n", f"paper:\n  {raw}\n", 1)
    (manuscript / "config.yaml").write_text(text, encoding="utf-8")
    assert generate_variables(tmp_path)["MANUSCRIPT_DATE"] == expected


def test_manuscript_tokens_all_generated(project_root: Path) -> None:
    """Live gate: every {{TOKEN}} in a numbered prose section must resolve."""
    variables = generate_variables(project_root)
    token_re = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")
    missing: list[str] = []
    for section in sorted((project_root / "manuscript").glob("[0-9]*.md")):
        tokens = token_re.findall(section.read_text(encoding="utf-8"))
        missing.extend(
            f"{section.name}: {token}" for token in tokens if token not in variables
        )
    assert missing == []


#: Claim-bearing sections: every quantity here is a *result* and must arrive
#: as an injected token. Methodology and references are excluded on purpose —
#: they legitimately carry structural constants (two belief states, the
#: 13-chip Barker code, equation exponents) and bibliographic page numbers.
CLAIM_SECTIONS = ("00_abstract.md", "03_results.md", "04_conclusion.md")

_TOKEN_SPAN = re.compile(r"\{\{\s*[A-Za-z0-9_]+\s*\}\}")
_LINK_SPAN = re.compile(r"!?\[[^\]]*\]\([^)]*\)")
_CODE_SPAN = re.compile(r"`[^`]*`")
_MATH_SPAN = re.compile(r"\$[^$]*\$")
# A standalone numeral: not part of a hyphenated compound ("1-sigma",
# "Barker-13") and not attached to a word or decimal run.
_BARE_NUMERAL = re.compile(r"(?<![\w.$-])\d+(?:\.\d+)?(?![\w.-])")


def test_no_hand_authored_numbers_in_claim_sections(project_root: Path) -> None:
    """Results prose must contain no bare numerals — only injected tokens.

    This is the gate that makes Rule 4 enforceable rather than aspirational:
    a number typed directly into the abstract, results, or conclusion fails
    here even if it happens to be correct today.
    """
    offenders: list[str] = []
    for name in CLAIM_SECTIONS:
        text = (project_root / "manuscript" / name).read_text(encoding="utf-8")
        stripped = _TOKEN_SPAN.sub(" ", text)
        stripped = _LINK_SPAN.sub(" ", stripped)
        stripped = _CODE_SPAN.sub(" ", stripped)
        stripped = _MATH_SPAN.sub(" ", stripped)
        offenders.extend(f"{name}: {hit}" for hit in _BARE_NUMERAL.findall(stripped))
    assert offenders == []


def test_claim_section_gate_would_catch_a_hand_authored_number(
    project_root: Path, tmp_path: Path
) -> None:
    """Positive control: the gate above is not vacuous.

    Injecting a bare numeral into a copy of the results section must make the
    same scan report an offender.
    """
    text = (project_root / "manuscript" / "03_results.md").read_text(encoding="utf-8")
    poisoned = text.replace(
        "{{MEDIA_BELIEF_SHARE_PCT}}% belief share", "57.5% belief share"
    )
    assert poisoned != text, "fixture string must exist in the real section"
    stripped = _TOKEN_SPAN.sub(" ", poisoned)
    stripped = _LINK_SPAN.sub(" ", stripped)
    stripped = _CODE_SPAN.sub(" ", stripped)
    stripped = _MATH_SPAN.sub(" ", stripped)
    assert "57.5" in _BARE_NUMERAL.findall(stripped)


def test_every_generated_token_is_used_by_the_manuscript(project_root: Path) -> None:
    """No orphan tokens: a variable nobody references is dead weight.

    The complementary direction (a referenced token nobody generates) is
    covered by ``test_manuscript_tokens_all_generated``.
    """
    variables = generate_variables(project_root)
    used: set[str] = set()
    for section in sorted((project_root / "manuscript").glob("[0-9]*.md")):
        used.update(
            re.findall(
                r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}", section.read_text(encoding="utf-8")
            )
        )
    # MANUSCRIPT_DATE and PYTHON_VERSION are provenance stamps; every other
    # token must earn its place by appearing in the prose.
    orphans = sorted(set(variables) - used)
    assert orphans == []
