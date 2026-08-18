"""Objective readability gates for machine extraction reporting."""

from __future__ import annotations

import ast
from pathlib import Path

REPORTING_ROOT = Path("src/er_commons/extraction_reporting")


def test_reporting_shell_remains_short_and_responsibility_driven() -> None:
    """The public flow should read as validation, documents, anomalies, and report."""
    source = (REPORTING_ROOT / "reporting.py").read_text()
    assert len(source.splitlines()) <= 220
    imported_modules = {
        node.module for node in ast.parse(source).body if isinstance(node, ast.ImportFrom)
    }
    assert {
        "er_commons.extraction_reporting.anomalies",
        "er_commons.extraction_reporting.candidate_metrics",
        "er_commons.extraction_reporting.collection_metrics",
        "er_commons.extraction_reporting.inputs",
    } <= imported_modules


def test_reporting_modules_and_functions_have_bounded_responsibilities() -> None:
    """Growth beyond one readable responsibility requires a deliberate split."""
    for path in REPORTING_ROOT.glob("*.py"):
        source = path.read_text()
        assert len(source.splitlines()) <= 320, f"split the responsibilities in {path.name}"
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 90, f"split {path.name}:{node.name} ({length} lines)"


def test_reporting_and_human_review_do_not_import_collection_storage() -> None:
    """Consumer surfaces use neutral artifact I/O rather than collection internals."""
    roots = [REPORTING_ROOT, Path("src/er_commons/human_review_support")]
    for root in roots:
        for path in root.glob("*.py"):
            assert "er_commons.collection_processing.storage" not in path.read_text(), path


def test_human_review_uses_one_selection_model_without_retired_aliases() -> None:
    """Requested plans and generated manifests share one public selection concept."""
    review_root = Path("src/er_commons/human_review_support")
    source = "\n".join(path.read_text() for path in review_root.glob("*.py"))
    assert "class ReviewSelection" in source
    assert "class RenderPlan" in source
    assert "class GeneratedReviewManifest" in source
    for retired_name in ("ReviewRequest", "RenderRequest", "RenderSelection"):
        assert retired_name not in source
