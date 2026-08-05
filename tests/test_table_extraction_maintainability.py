"""Human-ownership gates for the Task 03G.1a table repairs."""

from __future__ import annotations

import ast
import json
from pathlib import Path

TABLE_ROOT = Path("src/er_commons/table_extraction")
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


def test_learned_fallback_facade_stays_small_and_stable() -> None:
    """Callers should not need to know the internal responsibility split."""
    source = (TABLE_ROOT / "learned_fallback.py").read_text()
    assert len(source.splitlines()) <= 40
    exported = {
        element.value
        for node in ast.parse(source).body
        if isinstance(node, ast.Assign)
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


def test_production_identity_owns_every_learned_runtime_module() -> None:
    """A new fallback owner cannot evade production identity invalidation."""
    preimage = json.loads(IDENTITY_PREIMAGE.read_text())
    owned = {
        Path(item["path"]).name for item in preimage["preimage"]["producer_contract"]["owned_code"]
    }
    assert LEARNED_MODULES <= owned
