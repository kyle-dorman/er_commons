"""Ownership and restart characterization for the pre-aggregate boundary."""

import weakref
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from er_commons.artifact_io import write_json_atomic, write_jsonl
from er_commons.chunked_conversion.runtime.contracts import PreAggregateContext
from er_commons.document_parsing.content_parsing.chunked_application import (
    _table_stage_claims_completion,
    _validate_table_suppression_coverage,
    _verify_reusable_projection,
)
from er_commons.document_parsing.content_parsing.ordering_projection import (
    OrderingProjectionArtifact,
    OrderingTableStageObservation,
    TableEvidenceDecision,
    TableEvidenceOutcome,
    build_ordering_projection,
    capture_table_stage_reference,
)
from er_commons.document_parsing.content_parsing.page_projection import PageEvidenceProjection
from er_commons.document_parsing.content_parsing.range_projection_reuse import (
    verified_core_page_projections,
)
from er_commons.document_parsing.content_parsing.records import (
    PageRouteRecord,
    TableStageObservation,
)
from er_commons.document_parsing.content_parsing.sources import CompleteResolvedSource


def test_preaggregate_context_requires_absolute_contract_paths(tmp_path: Path) -> None:
    context = PreAggregateContext(
        child_root=(tmp_path / "child").resolve(),
        data_root=(tmp_path / "data").resolve(),
        config_path=(tmp_path / "config.json").resolve(),
        plan_path=(tmp_path / "plan.json").resolve(),
        run_id="run-1",
        plan_id="plan-1",
    )

    assert context.child_root.is_absolute()
    assert context.plan_id == "plan-1"
    with pytest.raises(ValueError, match="absolute"):
        PreAggregateContext(
            child_root=Path("relative"),
            data_root=context.data_root,
            config_path=context.config_path,
            plan_path=context.plan_path,
            run_id=context.run_id,
            plan_id=context.plan_id,
        )


def test_publication_roles_are_distinct() -> None:
    publication = {
        "ordered_non_table_content": "documents/x/producer/docling/document.json",
        "canonical_tables": "pre_aggregate/documents/x/producer/tables",
        "raw_evidence": "ranges/<range_id>/pages",
    }

    assert len(set(publication.values())) == 3
    assert publication["raw_evidence"] != publication["canonical_tables"]


def test_partial_table_evidence_may_fail_closed_without_suppression() -> None:
    """Invalid geometry must retain tables without authorizing text suppression."""
    tables = [
        {
            "physical_pdf_page": 7,
            "table_id": "table-7",
        }
    ]
    decisions = [
        TableEvidenceDecision(
            physical_pdf_page=7,
            outcome=TableEvidenceOutcome.PARTIAL,
            reason="table records lack valid suppression geometry",
        )
    ]

    _validate_table_suppression_coverage(decisions, tables)


def test_table_without_confirmed_or_partial_decision_is_rejected() -> None:
    tables = [
        {
            "physical_pdf_page": 7,
            "table_id": "table-7",
        }
    ]
    decisions = [
        TableEvidenceDecision(
            physical_pdf_page=7,
            outcome=TableEvidenceOutcome.UNMATCHED,
            reason="no table-stage page record",
        )
    ]

    with pytest.raises(ValueError, match="unexplained_missing_count=1"):
        _validate_table_suppression_coverage(decisions, tables)


def test_core_projection_verification_releases_each_decoded_range() -> None:
    """Pre-aggregate projection rebuild must not retain all large range payloads."""

    class Verified:
        pass

    class Store:
        def __init__(self) -> None:
            self.previous: weakref.ReferenceType[Verified] | None = None

        def verify(self, range_id: str) -> Verified:
            if self.previous is not None:
                assert self.previous() is None
            page = 1 if range_id == "r1" else 2
            value = Verified()
            value.projections = (SimpleNamespace(physical_pdf_page=page),)
            self.previous = weakref.ref(value)
            return value

    ranges = tuple(
        SimpleNamespace(
            range_id=f"r{page}",
            core=SimpleNamespace(contains=lambda candidate, page=page: candidate == page),
        )
        for page in (1, 2)
    )
    plan = cast(Any, SimpleNamespace(ranges=ranges))

    projections = verified_core_page_projections(cast(Any, Store()), plan, 2)

    assert [projection.physical_pdf_page for projection in projections] == [1, 2]


def test_plan_scoped_projection_reuses_verified_no_table_evidence(tmp_path: Path) -> None:
    child_root = tmp_path / "plan"
    projection_path = child_root / "records/ordering_projection.json"
    table_root = child_root / "pre_aggregate/documents/source/producer/tables"
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
    _write_no_table_handoff(table_root, observation)
    decisions = [
        TableEvidenceDecision(
            physical_pdf_page=page,
            outcome=TableEvidenceOutcome.UNMATCHED,
        )
        for page in (1, 2)
    ]
    pages = [_page_projection(page) for page in (1, 2)]
    artifact = OrderingProjectionArtifact(
        table_stage_observation=OrderingTableStageObservation.model_validate(
            observation.model_dump(mode="python")
        ),
        table_stage=capture_table_stage_reference(child_root.resolve(), table_root, observation),
        pages=build_ordering_projection(pages, decisions).pages,
        decisions=tuple(decisions),
    )
    write_json_atomic(projection_path, artifact.model_dump(mode="json"))
    source = cast(
        CompleteResolvedSource,
        SimpleNamespace(source_id="source", source_page_count=2),
    )

    _verify_reusable_projection(projection_path, source)

    wrong_source = cast(
        CompleteResolvedSource,
        SimpleNamespace(source_id="source", source_page_count=3),
    )
    with pytest.raises(ValueError, match="complete source"):
        _verify_reusable_projection(projection_path, wrong_source)


def _page_projection(page: int) -> PageEvidenceProjection:
    """Return one strict page-local projection for restart tests."""
    return PageEvidenceProjection(
        source_id="source",
        physical_pdf_page=page,
        features={
            "physical_pdf_page": page,
            "page_size_pdf_points": [100.0, 100.0],
            "displayed_page_size_pdf_points": [100.0, 100.0],
            "source_page_bbox_pdf_points_bottom_left": [0.0, 0.0, 100.0, 100.0],
            "routing_page_bbox_pdf_points_bottom_left": [0.0, 0.0, 100.0, 100.0],
            "routing_coordinate_system": "displayed_pdf_points_bottom_left",
            "page_rotation_degrees": 0,
            "native_character_count": 0,
            "nonspace_character_count": 0,
            "native_text_rectangle_count": 0,
            "nonempty_line_count": 0,
            "text_width_fraction": 0.0,
            "text_height_fraction": 0.0,
            "nonspace_characters_per_square_point": 0.0,
            "digit_fraction": 0.0,
            "coordinate_key_count": 0,
        },
        layout_table_observations=[],
        boundary_markers_before_first_table=[],
        range_id=f"range-{page}",
    )


def _write_no_table_handoff(root: Path, observation: TableStageObservation) -> None:
    """Write all files required by the producer's empty table contract."""
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


def test_partial_table_directory_is_resumable_not_reusable(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    table_root.mkdir()
    route = cast(PageRouteRecord, SimpleNamespace(route="layout_regions"))

    assert not _table_stage_claims_completion(table_root, [route])

    (table_root / "pages").mkdir()
    (table_root / "manifest.json").write_text("{}\n", encoding="utf-8")
    assert _table_stage_claims_completion(table_root, [route])
