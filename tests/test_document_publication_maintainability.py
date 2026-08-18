"""Objective ownership checks for the human-maintained stage-one runtime."""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from er_commons.document_publication.hooks import WorkflowHooks

RUNTIME_ROOT = Path("src/er_commons/document_publication")


def test_runtime_modules_and_functions_have_bounded_responsibilities() -> None:
    """Large control modules and functions require an explicit ownership split."""
    for path in RUNTIME_ROOT.glob("*.py"):
        if path.name == "task03g2_preparation.py":
            continue  # Historical read-only preservation helper.
        source = path.read_text()
        assert len(source.splitlines()) <= 350, f"split the responsibilities in {path.name}"
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 100, f"split {path.name}:{node.name} ({length} lines)"


def test_public_fault_injection_hooks_cover_publication_crash_windows() -> None:
    """The public hook contract exposes both sides of completion-last publication."""
    assert {field.name for field in fields(WorkflowHooks)} >= {
        "after_candidate_publish",
        "before_attempt_record",
    }


def test_behavior_tests_import_only_public_publication_symbols() -> None:
    """Behavior tests depend on public seams rather than module-private helpers."""
    for path in Path("tests").glob("test_document_publication*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            if not node.module.startswith("er_commons.document_publication"):
                continue
            private = [alias.name for alias in node.names if alias.name.startswith("_")]
            assert not private, f"private imports in {path.name}: {private}"


def test_historical_v1_projection_is_not_an_executable_document_spec() -> None:
    """The v1 reader may support readiness audits but cannot create a current run spec."""
    tree = ast.parse((RUNTIME_ROOT / "compatibility_v1.py").read_text())
    defined = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "Task03G2ReadinessSpec" in defined
    assert "adapt_document_run_spec_v1" not in defined
    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert "DocumentRunSpec" not in imported_names


def test_current_runtime_does_not_import_the_legacy_collection_contract() -> None:
    """Only the named v1 compatibility reader may depend on historical code."""
    for path in RUNTIME_ROOT.glob("*.py"):
        if path.name == "compatibility_v1.py":
            continue
        modules = {
            node.module
            for node in ast.walk(ast.parse(path.read_text()))
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        assert not any(
            module.startswith("er_commons.corpus_extraction_contract_v1_1") for module in modules
        ), path.name
