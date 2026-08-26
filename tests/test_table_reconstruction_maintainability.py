"""Human-ownership gates for the Task 03G.1a table repairs."""

from __future__ import annotations

import ast
import json
from pathlib import Path

TABLE_ROOT = Path("src/er_commons/document_parsing/table_reconstruction")
IDENTITY_PREIMAGE = Path(
    "benchmarks/er_bench/fixtures/corpus_extraction/v1_1/production_identity_preimage.json"
)
LEARNED_MODULES = {
    "learned_fallback.py",
    "learned_table_acceptance.py",
    "learned_table_cells.py",
    "learned_table_geometry.py",
    "learned_table_page.py",
    "learned_table_text.py",
    "learned_table_types.py",
    "otsl.py",
    "tableformer_fallback.py",
}


def _region_stream_modules() -> set[str]:
    """Return every native-text or region Stream production owner."""
    return {"native_text.py"} | {path.name for path in TABLE_ROOT.glob("region_stream_*.py")}


def _page_modules() -> set[str]:
    """Return the facade and every one-page reconstruction owner."""
    return {path.name for path in TABLE_ROOT.glob("page*.py")}


def test_learned_fallback_facade_stays_small_and_stable() -> None:
    """Callers should not need to know the internal responsibility split."""
    source = (TABLE_ROOT / "learned_fallback.py").read_text()
    assert len(source.splitlines()) <= 40
    exported = {
        element.value
        for node in ast.parse(source).body
        if isinstance(node, ast.Assign) and isinstance(node.value, (ast.List, ast.Tuple, ast.Set))
        for element in node.value.elts
        if isinstance(element, ast.Constant) and isinstance(element.value, str)
    }
    assert exported == {
        "FallbackAttempt",
        "LearnedFallbackRunner",
        "VerifiedTableFormerFallback",
        "evaluate_prediction",
        "unmatched_layout_regions",
    }


def test_learned_modules_and_functions_have_bounded_responsibilities() -> None:
    """Large policy changes must introduce a named owner instead of a monolith."""
    for name in LEARNED_MODULES:
        path = TABLE_ROOT / name
        source = path.read_text()
        assert len(source.splitlines()) <= 350, f"split the responsibilities in {name}"
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 80, f"split {name}:{node.name} ({length} lines)"


def test_region_stream_modules_and_functions_have_bounded_responsibilities() -> None:
    """Region Stream changes must stay split across named human-owned responsibilities."""
    for name in _region_stream_modules():
        path = TABLE_ROOT / name
        source = path.read_text()
        assert len(source.splitlines()) <= 350, f"split the responsibilities in {name}"
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 80, f"split {name}:{node.name} ({length} lines)"


def test_page_modules_and_functions_have_bounded_responsibilities() -> None:
    """One-page extraction must remain a facade over bounded responsibility owners."""
    for name in _page_modules():
        path = TABLE_ROOT / name
        source = path.read_text()
        assert len(source.splitlines()) <= 350, f"split the responsibilities in {name}"
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 80, f"split {name}:{node.name} ({length} lines)"


def test_page_facade_preserves_the_established_public_boundary() -> None:
    """Pipeline and diagnostic callers keep one stable page-level import surface."""
    source = (TABLE_ROOT / "page.py").read_text()
    exported = {
        element.value
        for node in ast.parse(source).body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)
        and isinstance(node.value, (ast.List, ast.Tuple, ast.Set))
        for element in node.value.elts
        if isinstance(element, ast.Constant) and isinstance(element.value, str)
    }
    assert {
        "RenderedPage",
        "bbox_iou",
        "clean_rows",
        "column_type_signatures",
        "detect_ruled_regions",
        "extract_page",
        "parse_complex_page",
        "parse_footer",
        "parse_simple_page",
        "rectangle_union_coverage",
        "route_page_candidates",
        "table_rows",
        "visual_order_key",
    } <= exported


def test_production_identity_owns_every_learned_runtime_module() -> None:
    """A new fallback owner cannot evade production identity invalidation."""
    preimage = json.loads(IDENTITY_PREIMAGE.read_text())
    owned = {
        Path(item["path"]).name for item in preimage["preimage"]["producer_contract"]["owned_code"]
    }
    assert LEARNED_MODULES <= owned
