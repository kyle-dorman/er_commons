"""Regression tests for bounded chunk-derived routing reuse."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from er_commons.artifact_io import write_json_atomic
from er_commons.document_parsing.content_parsing.config import ContentParsingConfig
from er_commons.document_parsing.content_parsing.derived_publication_support import (
    rebind_aggregate_references,
)
from er_commons.document_parsing.content_parsing.derived_route_reuse import (
    routes_from_aggregate_projection,
)
from er_commons.document_parsing.content_parsing.ordering_projection import (
    OrderingProjectionArtifact,
    OrderingTableStageObservation,
    TableArtifactSeal,
    TableStageReference,
    build_ordering_projection,
    classify_table_evidence,
)
from er_commons.document_parsing.content_parsing.page_projection import (
    PageEvidenceProjection,
)
from er_commons.document_parsing.content_parsing.records import PageRouteRecord
from er_commons.document_parsing.content_parsing.routing import (
    NumericTableThresholds,
    StrictTableThresholds,
    layout_table_observations,
)
from er_commons.document_parsing.content_parsing.routing_execution import (
    route_page_projections,
)
from er_commons.document_parsing.content_parsing.table_markers import (
    markers_before_first_table,
)


def _config() -> ContentParsingConfig:
    return cast(
        ContentParsingConfig,
        SimpleNamespace(
            strict_table_dominant_thresholds=StrictTableThresholds(
                minimum_text_width_fraction=0.7,
                minimum_text_height_fraction=0.75,
                minimum_partial_text_height_fraction=0.35,
                minimum_nonempty_line_count=80,
                minimum_nonspace_characters_per_square_point=0.02,
                minimum_digit_fraction=0.35,
            ),
            numeric_table_bearing_thresholds=NumericTableThresholds(
                minimum_text_width_fraction=0.7,
                minimum_nonempty_line_count=20,
                minimum_nonspace_characters_per_square_point=0.005,
                minimum_digit_fraction=0.5,
            ),
        ),
    )


def _projection(page_number: int) -> PageEvidenceProjection:
    return PageEvidenceProjection(
        source_id="source-a",
        physical_pdf_page=page_number,
        features={
            "physical_pdf_page": page_number,
            "page_size_pdf_points": [100.0, 200.0],
            "displayed_page_size_pdf_points": [100.0, 200.0],
            "source_page_bbox_pdf_points_bottom_left": [0.0, 0.0, 100.0, 200.0],
            "routing_page_bbox_pdf_points_bottom_left": [0.0, 0.0, 100.0, 200.0],
            "routing_coordinate_system": "displayed_pdf_points_bottom_left",
            "page_rotation_degrees": 0,
            "native_character_count": 10,
            "nonspace_character_count": 8,
            "native_text_rectangle_count": 2,
            "nonempty_line_count": 2,
            "text_width_fraction": 0.2,
            "text_height_fraction": 0.1,
            "nonspace_characters_per_square_point": 0.0004,
            "digit_fraction": 0.0,
            "coordinate_key_count": 0,
        },
        layout_table_observations=[],
        boundary_markers_before_first_table=[],
        range_id=f"range-{page_number}",
    )


def _write_projection(path: Path, projections: list[PageEvidenceProjection]) -> None:
    decisions = [
        classify_table_evidence(
            physical_pdf_page=item.physical_pdf_page,
            route="no_table_route",
            page_record=None,
            table_records=[],
        )
        for item in projections
    ]
    artifact = OrderingProjectionArtifact(
        table_stage_observation=OrderingTableStageObservation(
            status="not_applicable",
            document_scope_complete=True,
            verified_no_table_routes=True,
            routed_pages=(),
            routed_page_count=0,
            logical_table_count=0,
            family_assignment_count=0,
            family_count=0,
            zero_table_pages=(),
        ),
        table_stage=TableStageReference(
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
        ),
        pages=build_ordering_projection(projections, decisions).pages,
        decisions=tuple(decisions),
    )
    write_json_atomic(path, artifact.model_dump(mode="json"))


def test_routes_from_aggregate_projection_match_original_page_routing(tmp_path: Path) -> None:
    projections = [_projection(1), _projection(2)]
    path = tmp_path / "ordering_projection.json"
    _write_projection(path, projections)

    reused = routes_from_aggregate_projection(
        path,
        _config(),
        source_id="source-a",
        source_page_count=2,
    )

    assert reused == route_page_projections(projections, _config())


def test_routes_from_aggregate_projection_reject_source_drift(tmp_path: Path) -> None:
    path = tmp_path / "ordering_projection.json"
    _write_projection(path, [_projection(1)])

    with pytest.raises(ValueError, match="source identity differs"):
        routes_from_aggregate_projection(
            path,
            _config(),
            source_id="source-b",
            source_page_count=1,
        )


def test_indexed_reference_rebinding_matches_page_scanning_reference() -> None:
    payload: dict[str, Any] = {
        "tables": [
            {"prov": [{"page_no": 1, "bbox": {"l": 10, "b": 20, "r": 90, "t": 80}}]},
            {"prov": [{"page_no": 2, "bbox": {"l": 5, "b": 10, "r": 95, "t": 70}}]},
        ],
        "texts": [
            {
                "label": "section_header",
                "text": "Heading",
                "prov": [{"page_no": 1, "bbox": {"l": 10, "b": 90, "r": 50, "t": 100}}],
            },
            {
                "label": "caption",
                "text": "Below",
                "prov": [{"page_no": 2, "bbox": {"l": 10, "b": 5, "r": 50, "t": 9}}],
            },
        ],
    }
    routes = route_page_projections([_projection(1), _projection(2)], _config())
    expected: list[PageRouteRecord] = []
    for route in routes:
        observations = layout_table_observations(payload, route.physical_pdf_page)
        expected.append(
            PageRouteRecord.model_validate(
                {
                    **route.model_dump(mode="json"),
                    "layout_table_observations": observations,
                    "boundary_markers_before_first_table": markers_before_first_table(
                        payload, route.physical_pdf_page, observations
                    ),
                }
            )
        )

    assert rebind_aggregate_references(routes, payload) == expected
