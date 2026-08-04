"""Human-ownership gates for the maintained stage-two implementation."""

from __future__ import annotations

import ast
import json
from pathlib import Path

RUNTIME_ROOT = Path("src/er_commons/corpus_resolution")


def test_public_workflow_is_a_short_application_shell() -> None:
    """The public entrypoint should read as verify, collect, then publish."""
    source = (RUNTIME_ROOT / "workflow.py").read_text()
    assert len(source.splitlines()) <= 60
    tree = ast.parse(source)
    imported_modules = {node.module for node in tree.body if isinstance(node, ast.ImportFrom)}
    assert {
        "er_commons.corpus_resolution.domain",
        "er_commons.corpus_resolution.evidence",
        "er_commons.corpus_resolution.pipeline",
        "er_commons.corpus_resolution.preflight",
    } <= imported_modules


def test_modules_and_functions_fit_named_responsibilities() -> None:
    """Large ownership units require an explicit architectural split."""
    for path in RUNTIME_ROOT.glob("*.py"):
        source = path.read_text()
        assert len(source.splitlines()) <= 220, f"split the responsibilities in {path.name}"
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 80, f"split {path.name}:{node.name} ({length} lines)"


def test_contract_builders_are_named_and_distinct_from_publication() -> None:
    """Semantic construction must remain inspectable without filesystem lifecycle code."""
    expected = {
        "accounting.py": "AccountingBuilder",
        "indexing.py": "TargetIndexBuilder",
        "resolution.py": "ResolutionBuilder",
        "handoff.py": "HandoffBuilder",
    }
    for filename, class_name in expected.items():
        source = (RUNTIME_ROOT / filename).read_text()
        classes = {node.name for node in ast.parse(source).body if isinstance(node, ast.ClassDef)}
        assert class_name in classes
        assert "StagePublisher" not in source
        assert ".write_bytes(" not in source


def test_runtime_uses_typed_stage_and_mention_boundaries() -> None:
    """Core control flow is typed even though persisted JSON remains dictionary-shaped."""
    domain = (RUNTIME_ROOT / "domain.py").read_text()
    mentions = (RUNTIME_ROOT / "mentions.py").read_text()
    assert "class StageName(StrEnum)" in domain
    assert "class StageBuild:" in domain
    assert "@dataclass(frozen=True)\nclass DerivedMention:" in mentions
    assert "@dataclass(frozen=True)\nclass MentionManifest:" in mentions


def test_runtime_tests_use_public_scope_hooks() -> None:
    """Crash-window tests should survive internal publication refactors."""
    source = Path("tests/test_corpus_resolution_workflow.py").read_text()
    assert "ScopeHooks(" in source
    assert "StageHooks(" in source
    assert "workflow_module._" not in source


def test_production_identity_covers_active_code() -> None:
    """Every active output-affecting owner participates in invalidation."""
    identity = json.loads(
        Path(
            "benchmarks/er_bench/fixtures/corpus_extraction/v1_1/production_identity_preimage.json"
        ).read_text()
    )
    owned = {
        item["path"] for item in identity["preimage"]["corpus_workflow_contract"]["owned_code"]
    }
    runtime = {path.as_posix() for path in RUNTIME_ROOT.glob("*.py")}
    contract = {
        path.as_posix()
        for path in Path("src/er_commons/corpus_extraction_contract_v1_1").glob("*.py")
    }
    assert runtime | contract <= owned
