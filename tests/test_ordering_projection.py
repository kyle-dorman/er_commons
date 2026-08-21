"""Source-free tests for table-evidence suppression policy."""

import pytest

from er_commons.document_parsing.content_parsing.ordering_projection import (
    OrderingProjectionArtifact,
    TableEvidenceOutcome,
    build_ordering_projection,
    classify_table_evidence,
)


def test_only_complete_confirmed_tables_can_be_suppressed() -> None:
    confirmed = classify_table_evidence(
        physical_pdf_page=4,
        route="layout_regions",
        page_record={"status": "complete"},
        table_records=[{"table_id": "table-4-1"}],
    )
    partial = classify_table_evidence(
        physical_pdf_page=5,
        route="layout_regions",
        page_record={"status": "partial"},
        table_records=[{"table_id": "table-5-1"}],
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
    pages = [
        {"page_no": 4, "assembled": {"elements": ["table text", "body text"]}},
        {"page_no": 5, "assembled": {"elements": ["unresolved text"]}},
    ]
    decisions = [
        classify_table_evidence(
            physical_pdf_page=4,
            route="layout_regions",
            page_record={"status": "complete"},
            table_records=[{"table_id": "table-4-1"}],
        ),
        classify_table_evidence(
            physical_pdf_page=5,
            route="layout_regions",
            page_record={"status": "partial"},
            table_records=[{"table_id": "table-5-1"}],
        ),
    ]

    projection = build_ordering_projection(pages, decisions)

    assert projection.pages[0]["assembled"] == pages[0]["assembled"]
    assert projection.pages[0]["ordering_suppressed_table_refs"] == ["table-4-1"]
    assert projection.pages[1]["assembled"] == pages[1]["assembled"]
    assert projection.pages[1]["ordering_suppressed_table_refs"] == []
    assert pages[0]["assembled"]["elements"] == ["table text", "body text"]


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
            table_stage_observation={},
            table_stage_root="/tmp/table-stage",
            pages=({"page_no": 4, "ordering_suppressed_table_refs": []},),
            decisions=(),
        )


def test_projection_artifact_serializes_decisions_without_model_internals() -> None:
    decision = classify_table_evidence(
        physical_pdf_page=4,
        route="layout_regions",
        page_record={"status": "complete"},
        table_records=[{"table_id": "table-4-1"}],
    )
    artifact = OrderingProjectionArtifact(
        table_stage_observation={},
        table_stage_root="/tmp/table-stage",
        pages=({"page_no": 4, "ordering_suppressed_table_refs": ["table-4-1"]},),
        decisions=(decision,),
    )

    assert artifact.model_dump(mode="json")["decisions"] == [decision.as_record()]
