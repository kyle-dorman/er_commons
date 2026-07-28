"""Tests for the explicit mixed-pipeline acceptance policy."""

from er_commons.document_extraction.acceptance import evaluate_acceptance


def test_table_ranges_are_informational_but_other_ranges_gate() -> None:
    """A routed table page cannot hide drift on an unrelated document range."""
    comparison = {
        "exact_semantic_match": False,
        "ranges": [
            {"range_name": "narrative", "equal": True},
            {"range_name": "table", "equal": False},
        ],
    }
    routes = [{"source_id": "source", "physical_pdf_page": 2, "route": "full_page_numeric"}]
    result = evaluate_acceptance(
        comparison,
        {
            "narrative": {("source", 1)},
            "table": {("source", 2)},
        },
        routes,
        {"source:2": "full_page_numeric"},
        {"all_complete": True},
    )

    assert result["accepted"] is True
    assert result["docling_non_table_ranges_match"] is True
    assert result["full_docling_match_informational"] is False
    assert result["routed_table_ranges_excluded_from_docling_gate"] == ["table"]


def test_each_independent_gate_can_reject_the_run() -> None:
    """Routing and complete table orchestration remain mandatory."""
    comparison = {"exact_semantic_match": True, "ranges": [{"range_name": "page", "equal": True}]}
    result = evaluate_acceptance(
        comparison,
        {"page": {("source", 1)}},
        [{"source_id": "source", "physical_pdf_page": 1, "route": "layout_regions"}],
        {"source:1": "full_page_numeric"},
        {"all_complete": False},
    )

    assert result["accepted"] is False
    assert result["routing"]["exact_match"] is False
    assert result["table_stage_complete"] is False
