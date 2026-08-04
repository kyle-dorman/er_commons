"""Objective human-ownership gates for the Task 03G.1 diagnostic runtime."""

from __future__ import annotations

import ast
import json
from pathlib import Path

RUNTIME_ROOT = Path("src/er_commons/smoke_extraction")
SPEC_PATH = Path("configs/brisbane_baylands_2025_deir_task03g1_smoke_v1.json")


def test_public_workflow_remains_a_short_application_shell() -> None:
    """The public workflow should remain readable as preparation, sources, and publication."""
    source = (RUNTIME_ROOT / "workflow.py").read_text()
    assert len(source.splitlines()) <= 150
    imported_modules = {
        node.module for node in ast.parse(source).body if isinstance(node, ast.ImportFrom)
    }
    assert {
        "er_commons.smoke_extraction.publication",
        "er_commons.smoke_extraction.reporting",
        "er_commons.smoke_extraction.source_processing",
    } <= imported_modules


def test_runtime_modules_and_functions_have_bounded_responsibilities() -> None:
    """Growth beyond one readable responsibility requires an explicit module split."""
    for path in RUNTIME_ROOT.glob("*.py"):
        source = path.read_text()
        assert len(source.splitlines()) <= 220, f"split the responsibilities in {path.name}"
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 80, f"split {path.name}:{node.name} ({length} lines)"


def test_behavior_tests_do_not_depend_on_private_workflow_helpers() -> None:
    """Behavior tests should survive internal orchestration edits."""
    source = Path("tests/test_smoke_extraction.py").read_text()
    tree = ast.parse(source)
    workflow_imports = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "er_commons.smoke_extraction.workflow"
    ]
    assert len(workflow_imports) == 1
    assert [alias.name for alias in workflow_imports[0].names] == ["run_smoke"]


def test_smoke_identity_inventory_covers_every_runtime_module() -> None:
    """A new runtime owner cannot evade future smoke identity invalidation."""
    spec = json.loads(SPEC_PATH.read_text())
    owned = set(spec["owned_code_paths"])
    runtime = {path.as_posix() for path in RUNTIME_ROOT.glob("*.py")}
    assert runtime <= owned
