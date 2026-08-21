"""Characterization tests for the pre-aggregate page projection."""

import pytest

from er_commons.document_parsing.content_parsing.page_projection import (
    project_page_evidence,
)


def test_projection_is_page_local_and_copies_mutable_inputs() -> None:
    features = {
        "page_size_pdf_points": [612.0, 792.0],
        "text_width_fraction": 0.8,
        "text_height_fraction": 0.4,
        "nonempty_line_count": 90,
        "nonspace_characters_per_square_point": 0.03,
        "digit_fraction": 0.4,
    }
    observations = [{"bbox_pdf_points_bottom_left": [1.0, 2.0, 3.0, 4.0]}]
    projection = project_page_evidence(
        source_id="deir_example",
        range_id="range-0001",
        page_number=7,
        features=features,
        layout_table_observations=observations,
        boundary_markers_before_first_table=[],
    )

    features["text_width_fraction"] = 0.0
    observations[0]["bbox_pdf_points_bottom_left"][0] = 99.0

    assert projection.physical_pdf_page == 7
    assert projection.range_id == "range-0001"
    assert projection.features["text_width_fraction"] == 0.8
    assert projection.layout_table_observations[0]["bbox_pdf_points_bottom_left"][0] == 1.0


def test_projection_rejects_invalid_page_identity() -> None:
    with pytest.raises(ValueError, match="greater than 0"):
        project_page_evidence(
            source_id="deir_example",
            range_id="range-0001",
            page_number=0,
            features={},
            layout_table_observations=[],
            boundary_markers_before_first_table=[],
        )
