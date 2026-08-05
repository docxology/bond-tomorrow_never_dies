"""Surface tests: the package's declared shape must match what ships.

These are drift gates, not shape tests for their own sake. Each one is
written so that adding or removing a real module — without updating the
declared surface — fails. Zero mocks: everything is read off the installed
package and the real filesystem.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import yaml

import tomorrow_never_dies
from tomorrow_never_dies import CODENAME, CONCEPTS, MANUSCRIPT_IDENTITY, __version__
from tomorrow_never_dies.scenario import SCENARIO_BLOCKS, SCENARIO_PARAMS

#: Modules that are deliberately NOT domain concepts.
NON_CONCEPT_MODULES = {
    "__init__",
    "figures",
    "manuscript_variables",
    "mission",
    "scenario",
}


def _package_dir() -> Path:
    return Path(tomorrow_never_dies.__file__).resolve().parent


def _project_root() -> Path:
    return Path(tomorrow_never_dies.__file__).resolve().parents[2]


def _contract() -> dict:
    path = _project_root() / "manuscript" / "layer_contract.yaml"
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _declared_pure_domain() -> tuple[str, ...]:
    """The pure-domain module stems the contract actually declares.

    Read from the YAML rather than from ``CONCEPTS`` on purpose: the contract
    covers the six concepts **plus** ``scenario``, and deriving the scanned set
    from ``CONCEPTS`` alone silently exempted ``scenario.py`` from the import
    ban that three documents claim covers it.
    """
    modules = tuple(
        Path(entry).stem for entry in _contract()["surfaces"]["pure_domain"]["modules"]
    )
    assert len(modules) == len(CONCEPTS) + 1, "contract must cover CONCEPTS + scenario"
    return modules


def test_concepts_match_shipped_modules() -> None:
    """``CONCEPTS`` is exactly the set of pure-domain modules on disk."""
    on_disk = {
        path.stem
        for path in _package_dir().glob("*.py")
        if path.stem not in NON_CONCEPT_MODULES
    }
    assert set(CONCEPTS) == on_disk
    assert len(CONCEPTS) == len(set(CONCEPTS)), "CONCEPTS must not repeat a module"


def test_every_concept_module_is_importable_and_documented() -> None:
    for name in CONCEPTS:
        module = importlib.import_module(f"tomorrow_never_dies.{name}")
        assert module.__doc__, f"{name} must carry a module docstring"
        assert getattr(module, "__all__", None), f"{name} must declare __all__"


def test_pure_core_imports_no_bond_api_or_infrastructure() -> None:
    """The domain core must stay usable without the BOND protocol installed.

    Scans every module the layer contract declares pure-domain — the six
    concepts *and* ``scenario.py`` — which is exactly what README, AGENTS.md
    and ``layer_contract.yaml`` say this gate covers.
    """
    banned = ("bond_api", "infrastructure", "matplotlib")
    scanned = _declared_pure_domain()
    assert "scenario" in scanned
    for name in scanned:
        source = (_package_dir() / f"{name}.py").read_text(encoding="utf-8")
        for token in banned:
            assert f"import {token}" not in source, f"{name} imports {token}"
            assert f"from {token}" not in source, f"{name} imports from {token}"


def test_scenario_blocks_match_scenario_params() -> None:
    """The declared result blocks line up with the parameter blocks."""
    assert set(SCENARIO_BLOCKS) == set(SCENARIO_PARAMS)
    assert len(SCENARIO_BLOCKS) == len(CONCEPTS)


def test_layer_contract_declares_the_real_pure_domain_surface() -> None:
    """``manuscript/layer_contract.yaml`` must list exactly the core modules.

    The YAML is documentation that other tooling reads; without this it drifts
    the moment a module is added.
    """
    assert set(_declared_pure_domain()) == set(CONCEPTS) | {"scenario"}


def test_scenario_defers_integrity_availability_to_the_exported_predicate() -> None:
    """One implementation of the published "integrity is available" claim.

    ``scenario.py`` used to recompute ``levels.hpl <= alert_limit_m`` inline
    while ``gnss_integrity.integrity_availability`` existed for exactly that.
    Two copies of one claim agree until they don't, and a value test cannot
    catch a duplicate that is still correct — so this checks the structure:
    the predicate is called, and no inline alert-limit comparison remains.
    """
    source = (_package_dir() / "scenario.py").read_text(encoding="utf-8")
    assert "integrity_availability(" in source, "scenario must call the predicate"
    offenders = [
        line.strip()
        for line in source.splitlines()
        if "alert_limit" in line and ("<=" in line or "<" in line or ">" in line)
    ]
    assert offenders == [], (
        f"inline availability re-derivation in scenario: {offenders}"
    )


def test_identity_constants() -> None:
    assert CODENAME == "CARVER"
    assert MANUSCRIPT_IDENTITY == "Tomorrow Never Dies"
    assert __version__.count(".") == 2


@pytest.mark.parametrize("name", CONCEPTS)
def test_concept_module_has_no_bare_except(name: str) -> None:
    """No silent failure paths: the domain core never swallows an exception."""
    source = (_package_dir() / f"{name}.py").read_text(encoding="utf-8")
    assert "except" not in source, f"{name} contains an exception handler"
