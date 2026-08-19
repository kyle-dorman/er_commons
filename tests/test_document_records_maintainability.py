"""Behavioral and structural maintainability gates for document records."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from er_commons.document_records.document_references.errors import ContractViolation
from er_commons.document_records.document_references.types import DocumentReferenceMention


def test_malformed_reference_names_artifact_and_record() -> None:
    """Boundary failures identify the exact persisted stream and record."""
    with pytest.raises(ContractViolation) as captured:
        DocumentReferenceMention.from_json(
            {"id": "candidate/cross-reference/doc/xref000042", "candidates": "invalid"},
            path="canonical/cross_references.jsonl",
        )

    error = captured.value
    assert error.stage == "read_mention"
    assert error.path == Path("canonical/cross_references.jsonl")
    assert error.record_id == "candidate/cross-reference/doc/xref000042"


def test_record_mapping_context_responsibilities_stay_bounded() -> None:
    """Traversal, ID allocation, and assembly must remain independently readable."""
    paths = (
        Path("src/er_commons/document_records/record_mapping/context.py"),
        Path("src/er_commons/document_records/document_references/validation.py"),
    )
    for path in paths:
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 80, f"split {path.name}:{node.name} ({length} lines)"


def test_document_transformation_application_responsibilities_stay_bounded() -> None:
    """Application paths keep verification, construction, and publication readable."""
    paths = (
        Path("src/er_commons/document_records/document_structure/inputs.py"),
        Path("src/er_commons/document_records/document_structure/sections.py"),
        Path("src/er_commons/document_records/document_structure/publication.py"),
        Path("src/er_commons/document_parsing/content_parsing/application.py"),
    )
    for path in paths:
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 90, f"split {path.name}:{node.name} ({length} lines)"


def test_record_mapping_table_responsibilities_stay_bounded() -> None:
    """Table types, cleanup, loading, families, and regions remain separate owners."""
    module_root = Path("src/er_commons/document_records/record_mapping")
    owner_paths = tuple(
        module_root / name
        for name in (
            "table_records.py",
            "table_cleanup.py",
            "table_families.py",
            "table_artifacts.py",
            "table_regions.py",
        )
    )
    facade = module_root / "tables.py"
    assert len(facade.read_text().splitlines()) <= 60
    for path in owner_paths:
        assert len(path.read_text().splitlines()) <= 300
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 80, f"split {path.name}:{node.name} ({length} lines)"


def test_responsibility_imports_remain_acyclic() -> None:
    """Hierarchy may consume parsing; records may consume both, never the reverse."""
    roots = {
        "er_commons.document_parsing": Path("src/er_commons/document_parsing"),
        "er_commons.hierarchy_inference": Path("src/er_commons/hierarchy_inference"),
        "er_commons.document_records": Path("src/er_commons/document_records"),
    }
    forbidden = {
        "er_commons.document_parsing": {
            "er_commons.hierarchy_inference",
            "er_commons.document_records",
        },
        "er_commons.hierarchy_inference": {"er_commons.document_records"},
        "er_commons.document_records": set(),
    }
    for owner, root in roots.items():
        for path in root.rglob("*.py"):
            imports = {
                node.module
                for node in ast.walk(ast.parse(path.read_text()))
                if isinstance(node, ast.ImportFrom) and node.module is not None
            }
            assert not any(
                imported.startswith(prefix) for prefix in forbidden[owner] for imported in imports
            ), f"reverse responsibility import in {path}"
