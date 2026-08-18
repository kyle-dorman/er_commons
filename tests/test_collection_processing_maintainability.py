"""Human-ownership gates for the maintained stage-two implementation."""

from __future__ import annotations

import ast
import json
from dataclasses import fields, is_dataclass
from enum import StrEnum
from pathlib import Path

import pytest
from pydantic import ValidationError

from er_commons.collection_processing.accounting import AccountingBuilder
from er_commons.collection_processing.attempt_storage import AttemptRecord
from er_commons.collection_processing.cross_document_linking import CrossDocumentLinkBuilder
from er_commons.collection_processing.domain import (
    CollectionHooks,
    StageBuild,
    StageHooks,
    StageName,
)
from er_commons.collection_processing.handoff_assembly import HandoffAssembler
from er_commons.collection_processing.mentions import DerivedMention, MentionManifest
from er_commons.collection_processing.record_target_indexing import RecordTargetIndexBuilder

RUNTIME_ROOT = Path("src/er_commons/collection_processing")


def test_public_workflow_is_a_short_application_shell() -> None:
    """The public entrypoint should read as verify, collect, then publish."""
    source = (RUNTIME_ROOT / "workflow.py").read_text()
    assert len(source.splitlines()) <= 60
    tree = ast.parse(source)
    imported_modules = {node.module for node in tree.body if isinstance(node, ast.ImportFrom)}
    assert {
        "er_commons.collection_processing.domain",
        "er_commons.collection_processing.document_evidence",
        "er_commons.collection_processing.pipeline",
        "er_commons.collection_processing.preflight",
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
    builders = (
        AccountingBuilder,
        RecordTargetIndexBuilder,
        CrossDocumentLinkBuilder,
        HandoffAssembler,
    )
    for builder in builders:
        filename = f"{builder.__module__.rsplit('.', maxsplit=1)[-1]}.py"
        source = (RUNTIME_ROOT / filename).read_text()
        tree = ast.parse(source)
        imports = {node.module for node in tree.body if isinstance(node, ast.ImportFrom)}
        assert "er_commons.collection_processing.publication" not in imports
        assert not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "write_bytes"
            for node in ast.walk(tree)
        )


def test_runtime_uses_typed_stage_and_mention_boundaries() -> None:
    """Core control flow is typed even though persisted JSON remains dictionary-shaped."""
    assert issubclass(StageName, StrEnum)
    for boundary in (StageBuild, DerivedMention, MentionManifest):
        assert is_dataclass(boundary)
        assert boundary.__dataclass_params__.frozen


def test_attempt_record_boundary_rejects_untyped_or_extra_fields() -> None:
    """Retained lifecycle evidence must cross a strict behavioral model boundary."""
    with pytest.raises(ValidationError):
        AttemptRecord.model_validate({})
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AttemptRecord.model_validate(
            {
                "schema_version": "er_commons.collection_stage_attempt_record.v2",
                "stage_type": "accounting",
                "stage_id": "acctv2-test",
                "attempt": 1,
                "disposition": "cancelled",
                "failure_class": "InterruptedPublication",
                "completion_path": None,
                "recorded_at_utc": "2026-08-18T00:00:00Z",
                "wall_seconds": None,
                "undeclared": True,
            }
        )


def test_runtime_tests_use_public_scope_hooks() -> None:
    """Crash-window tests should survive internal publication refactors."""
    assert [item.name for item in fields(CollectionHooks)] == [
        "accounting",
        "target_index",
        "resolution",
        "handoff",
    ]
    assert [item.name for item in fields(StageHooks)] == [
        "before_publish",
        "after_publish",
        "before_attempt_record",
    ]
    observed: list[Path] = []
    hooks = CollectionHooks(target_index=StageHooks(after_publish=observed.append))
    hooks.target_index.after_publish(Path("completion.json"))
    assert observed == [Path("completion.json")]


def test_accepted_v1_identity_remains_legacy_evidence() -> None:
    """The immutable pilot identity must not impersonate the moved v2 runtime."""
    identity = json.loads(
        Path(
            "benchmarks/er_bench/fixtures/corpus_extraction/v1_1/production_identity_preimage.json"
        ).read_text()
    )
    owned = {
        item["path"] for item in identity["preimage"]["corpus_workflow_contract"]["owned_code"]
    }
    assert any(path.startswith("src/er_commons/corpus_resolution/") for path in owned)
    assert not any(path.startswith("src/er_commons/collection_processing/") for path in owned)


def test_current_runtime_cannot_import_or_write_legacy_collection_contracts() -> None:
    """V1 readers stay explicit; maintained v2 modules own their write vocabulary."""
    allowed = {"compatibility_v1.py", "compatibility_v1_bundle.py"}
    legacy_schemas = (".v1_1", "corpus_target_order_v1")
    for path in RUNTIME_ROOT.glob("*.py"):
        if path.name in allowed:
            continue
        source = path.read_text()
        tree = ast.parse(source)
        imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        assert not any(
            module.startswith("er_commons.corpus_extraction_contract_v1_1") for module in imports
        ), path.name
        assert not any(schema in source for schema in legacy_schemas), path.name
