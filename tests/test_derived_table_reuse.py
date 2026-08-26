"""Regression tests for chunk-aggregate table reuse by derived publication."""

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

import er_commons.document_parsing.content_parsing.derived_table_reuse as table_reuse
from er_commons.artifact_io import write_json_atomic, write_jsonl
from er_commons.document_parsing.content_parsing.conversion_seal import SealedConversion
from er_commons.document_parsing.content_parsing.derived_table_reuse import (
    reuse_aggregate_table_stage,
)
from er_commons.document_parsing.content_parsing.ordering_projection import (
    OrderingProjectionArtifact,
    OrderingTableStageObservation,
    capture_table_stage_reference,
)
from er_commons.document_parsing.content_parsing.records import TableStageObservation
from er_commons.document_parsing.table_reconstruction.pipeline import artifact_inventory


def _no_table_aggregate(root: Path) -> SealedConversion:
    observation = TableStageObservation(
        status="not_applicable",
        document_scope_complete=True,
        verified_no_table_routes=True,
        routed_pages=[],
        routed_page_count=0,
        logical_table_count=0,
        family_assignment_count=0,
        family_count=0,
        zero_table_pages=[],
        manifest=None,
    )
    _write_no_table_handoff(root / "tables", observation)
    projection = OrderingProjectionArtifact(
        table_stage_observation=OrderingTableStageObservation.model_validate(
            observation.model_dump(mode="python")
        ),
        table_stage=capture_table_stage_reference(root.resolve(), root / "tables", observation),
        pages=(),
        decisions=(),
    )
    write_json_atomic(
        root / "records/ordering_projection.json",
        projection.model_dump(mode="json"),
    )
    return cast(SealedConversion, SimpleNamespace(root=root))


def _write_no_table_handoff(root: Path, observation: TableStageObservation) -> None:
    """Write the complete empty aggregate table handoff."""
    write_json_atomic(
        root / "summary.json",
        {
            "physical_pdf_pages": [],
            "page_count": 0,
            "logical_table_count": 0,
            "family_count": 0,
            "zero_table_pages": [],
            "review_derivatives_retained": False,
        },
    )
    for name in ("pages.jsonl", "tables.jsonl", "family_assignments.jsonl"):
        write_jsonl(root / name, [])
    write_json_atomic(root / "table_families.json", {"families": [], "continuation_decisions": []})
    write_json_atomic(
        root / "manifest.json",
        {
            "schema_version": "1.0.0",
            "source_id": "source",
            "physical_pdf_pages": [],
            "summary": "summary.json",
            "pages": "pages.jsonl",
            "tables": "tables.jsonl",
            "family_assignments": "family_assignments.jsonl",
            "table_families": "table_families.json",
        },
    )
    write_json_atomic(
        root / "no_table_stage.json",
        observation.model_dump(mode="json", exclude_none=True),
    )


def test_derived_publication_reuses_sealed_aggregate_tables(tmp_path: Path) -> None:
    sealed = _no_table_aggregate(tmp_path / "aggregate")
    target = tmp_path / "producer/tables"

    observation = reuse_aggregate_table_stage(sealed, target)

    assert observation.status == "not_applicable"
    assert (target / "no_table_stage.json").stat().st_ino == (
        sealed.root / "tables/no_table_stage.json"
    ).stat().st_ino


def test_derived_table_reuse_rejects_observation_drift(tmp_path: Path) -> None:
    sealed = _no_table_aggregate(tmp_path / "aggregate")
    write_json_atomic(sealed.root / "tables/no_table_stage.json", {"status": "corrupt"})

    with pytest.raises(ValueError, match="completion marker differs"):
        reuse_aggregate_table_stage(sealed, tmp_path / "producer/tables")


def test_relocated_aggregate_manifest_is_rebound_to_producer_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "aggregate"
    observation = TableStageObservation(
        status="complete",
        document_scope_complete=True,
        routed_pages=[1],
        routed_page_count=1,
        logical_table_count=1,
        family_assignment_count=1,
        family_count=1,
        zero_table_pages=[],
        manifest="documents/document/producer/tables/manifest.json",
    )
    table_root = root / "tables"
    write_json_atomic(table_root / "summary.json", {"table_count": 1})
    write_json_atomic(
        table_root / "artifact_inventory.json",
        artifact_inventory(table_root, {"artifact_inventory.json", "manifest.json"}),
    )
    write_json_atomic(
        table_root / "manifest.json",
        {"source_id": "document", "artifact_inventory": "artifact_inventory.json"},
    )
    projection = OrderingProjectionArtifact(
        table_stage_observation=OrderingTableStageObservation.model_validate(
            observation.model_dump(mode="python")
        ),
        table_stage=capture_table_stage_reference(root.resolve(), table_root, observation),
        pages=(),
        decisions=(),
    )
    write_json_atomic(
        root / "records/ordering_projection.json",
        projection.model_dump(mode="json"),
    )
    relocated = observation.model_copy(
        update={"manifest": "documents/docling_conversions/producer/tables/manifest.json"}
    )
    monkeypatch.setattr(table_reuse, "validate_table_artifacts", lambda *_args: relocated)
    sealed = cast(SealedConversion, SimpleNamespace(root=root))

    actual = reuse_aggregate_table_stage(sealed, tmp_path / "producer/tables")

    assert actual == observation
