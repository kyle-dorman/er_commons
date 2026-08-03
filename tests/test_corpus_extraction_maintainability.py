"""Objective ownership checks for the human-maintained stage-one runtime."""

from __future__ import annotations

import ast
from pathlib import Path

RUNTIME_ROOT = Path("src/er_commons/corpus_extraction")


def test_application_shells_stay_small_enough_to_read_as_a_whole() -> None:
    """The two orchestration shells must remain navigation aids, not subsystems."""
    limits = {"workflow.py": 180, "content_owners.py": 180}
    for name, maximum_lines in limits.items():
        lines = (RUNTIME_ROOT / name).read_text().splitlines()
        assert len(lines) <= maximum_lines, f"{name} has grown past its ownership boundary"


def test_runtime_modules_and_functions_have_bounded_responsibilities() -> None:
    """Large control modules and functions require an explicit ownership split."""
    for path in RUNTIME_ROOT.glob("*.py"):
        source = path.read_text()
        assert len(source.splitlines()) <= 350, f"split the responsibilities in {path.name}"
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 100, f"split {path.name}:{node.name} ({length} lines)"


def test_runtime_tests_use_public_fault_injection_hooks() -> None:
    """Crash-window tests should survive internal refactors of the workflow."""
    source = Path("tests/test_corpus_extraction_workflow.py").read_text()
    assert "WorkflowHooks(" in source
    assert "workflow_module._" not in source
    assert "content_owners_module._" not in source
