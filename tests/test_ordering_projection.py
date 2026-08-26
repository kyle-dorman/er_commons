"""Source-free tests for table-evidence suppression policy."""

import shutil
from pathlib import Path

import pytest

from er_commons.artifact_io import read_json_object, write_json_atomic, write_jsonl
from er_commons.document_parsing.content_parsing.ordering_projection import (
    OrderingProjectionArtifact,
    OrderingTableStageObservation,
    TableArtifactSeal,
    TableEvidenceOutcome,
    TableStageReference,
    build_ordering_projection,
    capture_table_stage_reference,
    classify_table_evidence,
    verify_table_stage_reference,
)
from er_commons.document_parsing.content_parsing.page_projection import PageEvidenceProjection
from er_commons.document_parsing.content_parsing.records import TableStageObservation


def page_projection(page: int) -> PageEvidenceProjection:
    """Return one complete typed routing projection."""
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
            "native_character_count": 1,
            "nonspace_character_count": 1,
            "native_text_rectangle_count": 1,
            "nonempty_line_count": 1,
            "text_width_fraction": 0.1,
            "text_height_fraction": 0.1,
            "nonspace_characters_per_square_point": 0.0001,
            "digit_fraction": 0.0,
            "coordinate_key_count": 0,
        },
        layout_table_observations=[],
        boundary_markers_before_first_table=[],
        range_id="range",
    )


def no_table_observation() -> OrderingTableStageObservation:
    """Return a strict empty table-stage observation for envelope tests."""
    return OrderingTableStageObservation(
        status="not_applicable",
        document_scope_complete=True,
        verified_no_table_routes=True,
        routed_pages=(),
        routed_page_count=0,
        logical_table_count=0,
        family_assignment_count=0,
        family_count=0,
        zero_table_pages=(),
    )


def table_reference() -> TableStageReference:
    """Return deterministic reference evidence for pure schema tests."""
    return TableStageReference(
        relative_path="tables",
        completion_marker="no_table_stage.json",
        completion_marker_sha256="0" * 64,
        no_table_handoff=tuple(
            TableArtifactSeal(path=name, sha256="0" * 64)
            for name in (
                "summary.json",
                "pages.jsonl",
                "tables.jsonl",
                "family_assignments.jsonl",
                "table_families.json",
                "manifest.json",
            )
        ),
    )


def write_no_table_handoff(root: Path, observation: TableStageObservation) -> None:
    """Write the complete producer-owned empty table handoff."""
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


def table_record(table_id: str) -> dict[str, object]:
    """Return the geometry-bearing shape emitted by the production table stage."""
    return {
        "table_id": table_id,
        "bbox_pdf_points_bottom_left": [10.0, 20.0, 90.0, 80.0],
        "page_size_pdf_points": [100.0, 100.0],
    }


def test_only_complete_confirmed_tables_can_be_suppressed() -> None:
    confirmed = classify_table_evidence(
        physical_pdf_page=4,
        route="layout_regions",
        page_record={"physical_pdf_page": 4, "table_count": 1},
        table_records=[table_record("table-4-1")],
    )
    partial = classify_table_evidence(
        physical_pdf_page=5,
        route="layout_regions",
        page_record={"status": "partial"},
        table_records=[table_record("table-5-1")],
    )
    route_only = classify_table_evidence(
        physical_pdf_page=6,
        route="full_page_numeric",
        page_record=None,
        table_records=[],
    )

    assert confirmed.outcome is TableEvidenceOutcome.CONFIRMED
    assert confirmed.may_suppress_table_text
    assert not partial.may_suppress_table_text
    assert route_only.outcome is TableEvidenceOutcome.UNMATCHED
    assert not route_only.may_suppress_table_text


def test_projection_retains_raw_page_fields_and_marks_suppression_only() -> None:
    pages = [page_projection(4), page_projection(5)]
    decisions = [
        classify_table_evidence(
            physical_pdf_page=4,
            route="layout_regions",
            page_record={"physical_pdf_page": 4, "table_count": 1},
            table_records=[table_record("table-4-1")],
        ),
        classify_table_evidence(
            physical_pdf_page=5,
            route="layout_regions",
            page_record={"status": "partial"},
            table_records=[{"table_id": "table-5-1"}],
        ),
    ]

    projection = build_ordering_projection(pages, decisions)

    assert projection.pages[0].source_id == pages[0].source_id
    assert projection.pages[0].ordering_suppressed_table_refs == ("table-4-1",)
    assert len(projection.pages[0].ordering_suppressed_table_regions) == 1
    assert projection.pages[1].source_id == pages[1].source_id
    assert projection.pages[1].ordering_suppressed_table_refs == ()
    assert pages[0].features["physical_pdf_page"] == 4


def test_failed_and_unmatched_outcomes_are_explicit_fallbacks() -> None:
    failed = classify_table_evidence(
        physical_pdf_page=8,
        route="layout_regions",
        page_record={"status": "failed"},
        table_records=[],
    )
    unmatched = classify_table_evidence(
        physical_pdf_page=9,
        route="no_table_route",
        page_record=None,
        table_records=[],
    )

    assert failed.outcome is TableEvidenceOutcome.FAILED
    assert unmatched.outcome is TableEvidenceOutcome.UNMATCHED
    assert not failed.may_suppress_table_text
    assert not unmatched.may_suppress_table_text


def test_projection_artifact_rejects_page_decision_drift() -> None:
    with pytest.raises(ValueError, match="exact coverage"):
        OrderingProjectionArtifact(
            table_stage_observation=no_table_observation(),
            table_stage=table_reference(),
            pages=build_ordering_projection(
                [page_projection(4)],
                [
                    classify_table_evidence(
                        physical_pdf_page=4,
                        route="no_table_route",
                        page_record=None,
                        table_records=[],
                    )
                ],
            ).pages,
            decisions=(),
        )


def test_projection_artifact_serializes_decisions_without_model_internals() -> None:
    decision = classify_table_evidence(
        physical_pdf_page=4,
        route="layout_regions",
        page_record={"physical_pdf_page": 4, "table_count": 1},
        table_records=[table_record("table-4-1")],
    )
    page = build_ordering_projection([page_projection(4)], [decision]).pages[0]
    artifact = OrderingProjectionArtifact(
        table_stage_observation=no_table_observation(),
        table_stage=table_reference(),
        pages=(page,),
        decisions=(decision,),
    )

    assert artifact.model_dump(mode="json")["decisions"] == [decision.as_record()]


def test_table_stage_reference_is_relocatable_and_completion_bound(tmp_path: Path) -> None:
    owner = (tmp_path / "plan").resolve()
    table_root = owner / "pre_aggregate/tables"
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
    )
    marker = table_root / "no_table_stage.json"
    write_no_table_handoff(table_root, observation)

    reference = capture_table_stage_reference(owner, table_root, observation)

    assert reference.relative_path == "pre_aggregate/tables"
    assert verify_table_stage_reference(reference, owner) == table_root
    relocated_owner = (tmp_path / "aggregate").resolve()
    relocated_root = relocated_owner / "tables"
    for name in (*[item.path for item in reference.no_table_handoff], marker.name):
        source = table_root / name
        destination = relocated_root / name
        if name.endswith(".jsonl"):
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        else:
            write_json_atomic(destination, read_json_object(source))
    assert verify_table_stage_reference(reference.relocated("tables"), relocated_owner) == (
        relocated_root
    )


def test_table_stage_reference_rejects_absolute_paths_and_tampering(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="relative path"):
        TableStageReference(
            relative_path="/tmp/tables",
            completion_marker="no_table_stage.json",
            completion_marker_sha256="0" * 64,
        )
    owner = tmp_path.resolve()
    marker = owner / "tables/no_table_stage.json"
    write_json_atomic(marker, {"status": "complete"})
    reference = TableStageReference(
        relative_path="tables",
        completion_marker="no_table_stage.json",
        completion_marker_sha256="0" * 64,
        no_table_handoff=table_reference().no_table_handoff,
    )
    with pytest.raises(ValueError, match="completion marker differs"):
        verify_table_stage_reference(reference, owner)


def test_no_table_reference_rejects_marker_only_handoff(tmp_path: Path) -> None:
    owner = tmp_path.resolve()
    table_root = owner / "tables"
    observation = no_table_observation().as_producer_record()
    write_json_atomic(
        table_root / "no_table_stage.json",
        observation.model_dump(mode="json", exclude_none=True),
    )

    with pytest.raises(ValueError, match="handoff artifacts are missing"):
        capture_table_stage_reference(owner, table_root, observation)
