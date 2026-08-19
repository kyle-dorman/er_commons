"""Structural ownership gates for content-parsing preparation and publication."""

from __future__ import annotations

import ast
from pathlib import Path

from er_commons.document_parsing.content_parsing import application, preparation

MODULE_ROOT = Path("src/er_commons/document_parsing/content_parsing")


def _function_lengths(path: Path) -> dict[str, int]:
    tree = ast.parse(path.read_text())
    return {
        node.name: (node.end_lineno or node.lineno) - node.lineno + 1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _imports(path: Path) -> set[str]:
    return {
        node.module
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }


def test_application_remains_a_short_orchestration_shell() -> None:
    """The shell coordinates reuse/failure flow without owning derived stages."""
    application = MODULE_ROOT / "application.py"
    assert len(application.read_text().splitlines()) <= 120
    assert max(_function_lengths(application).values()) <= 75
    imports = _imports(application)
    assert (
        not {
            "er_commons.artifact_io",
            "er_commons.document_parsing.content_parsing.records",
            "er_commons.document_parsing.content_parsing.routing_execution",
            "er_commons.document_parsing.content_parsing.table_processing",
        }
        & imports
    )


def test_application_preserves_preparation_public_api() -> None:
    """Existing callers can keep importing preparation types from the shell."""
    assert application.PreparedContentParsing is preparation.PreparedContentParsing
    assert application.prepare_content_parsing is preparation.prepare_content_parsing


def test_preparation_and_derived_publication_own_named_responsibilities() -> None:
    """Preflight identity and derived artifact work stay independently readable."""
    preparation = MODULE_ROOT / "preparation.py"
    derived = MODULE_ROOT / "derived_publication.py"
    assert len(preparation.read_text().splitlines()) <= 110
    assert len(derived.read_text().splitlines()) <= 270
    assert max(_function_lengths(preparation).values()) <= 60
    assert max(_function_lengths(derived).values()) <= 65
    assert {
        "er_commons.document_parsing.content_parsing.routing_execution",
        "er_commons.document_parsing.content_parsing.table_processing",
    } <= _imports(derived)


def test_conversion_verifier_keeps_invariant_groups_named_and_bounded() -> None:
    """Seal failures remain traceable to terminal, identity, source, and accounting owners."""
    seal = MODULE_ROOT / "conversion_seal.py"
    lengths = _function_lengths(seal)
    assert {
        "_load_terminal_records",
        "_verify_identity",
        "_verify_inventory_seal",
        "_verify_source",
        "_verify_terminal_observation",
        "_verify_alignment",
        "_verify_page_accounting",
        "_verify_asset_accounting",
    } <= lengths.keys()
    assert lengths["verify_conversion_bundle"] <= 25
    assert max(lengths.values()) <= 40
