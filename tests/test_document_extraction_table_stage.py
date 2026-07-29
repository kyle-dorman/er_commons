"""Tests for the document-to-table integration boundary."""

from pathlib import Path

from er_commons.document_extraction.config import (
    load_pipeline_config,
    load_selection_spec,
)
from er_commons.document_extraction.sources import ResolvedSource
from er_commons.document_extraction.table_stage import build_table_request


def test_routed_request_preserves_full_table_pipeline_contract() -> None:
    """The document stage creates a validated source-scoped table request."""
    config, _ = load_pipeline_config(
        Path("configs/brisbane_baylands_2025_deir_task03a15_document_pipeline_v4.json")
    )
    selection, _ = load_selection_spec(config.selection_spec_path)
    selected = next(item for item in selection.sources if item.source_id == "deir_appendix_g3")
    source = ResolvedSource(
        source_id=selected.source_id,
        source_path=Path("/tmp/appendix.pdf"),
        source_sha256=selected.expected_sha256,
        source_page_count=selected.expected_pdf_page_count,
        warnings=[],
        page_ranges=selected.page_ranges,
    )

    request = build_table_request(
        config,
        selection,
        source,
        [
            {
                "source_id": source.source_id,
                "physical_pdf_page": 1000,
                "route": "full_page_numeric",
                "layout_table_regions_pdf_points_bottom_left": [[1, 2, 3, 4]],
            }
        ],
    )

    assert request.validation_scope == "routed_pages"
    assert request.physical_pdf_pages == [1000]
    assert request.table_id_prefix == "appendix_g3"
    assert request.family_id_prefix == "appendix_g3_table"
    assert request.routed_pages[0].layout_regions_pdf_points_bottom_left == []
    assert request.cleanup == config.table_cleanup
    assert request.detection == config.table_detection
    assert request.retain_review_derivatives
