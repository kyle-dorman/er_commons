"""Build validated table-reconstruction requests from production routing records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from er_commons.document_parsing.content_parsing.records import PageRouteRecord
from er_commons.document_parsing.content_parsing.sources import CompleteResolvedSource
from er_commons.document_parsing.table_reconstruction.models import (
    CleanupConfig,
    DetectionConfig,
    ExecutionConfig,
    LearnedFallbackConfig,
    RoutedPageConfig,
    TableExtractionConfig,
)


@dataclass(frozen=True)
class TableSource:
    """Source identity needed to construct a table-reconstruction request."""

    source_id: str
    source_sha256: str
    source_page_count: int

    @classmethod
    def from_complete_source(cls, source: CompleteResolvedSource) -> TableSource:
        """Project a verified complete source onto the table-stage boundary."""
        return cls(source.source_id, source.source_sha256, source.source_page_count)


def _route_payload(record: PageRouteRecord | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(record, PageRouteRecord):
        return cast(Mapping[str, Any], record.model_dump(mode="json"))
    return record


def build_table_request(
    *,
    pipeline_id: str,
    source_release_version: str,
    source: TableSource,
    routes: Sequence[PageRouteRecord | Mapping[str, Any]],
    artifact_relative_root: Path,
    detection: DetectionConfig,
    cleanup: CleanupConfig,
    retain_review_derivatives: bool,
    learned_fallback: LearnedFallbackConfig | None = None,
) -> TableExtractionConfig:
    """Translate positive page routes into the persisted table-stage contract."""
    ordered = sorted(
        (_route_payload(record) for record in routes),
        key=lambda item: int(item["physical_pdf_page"]),
    )
    prefix = source.source_id.removeprefix("deir_")
    routed_pages = [
        RoutedPageConfig(
            physical_pdf_page=int(record["physical_pdf_page"]),
            route=record["route"],
            layout_regions_pdf_points_bottom_left=(
                record["layout_table_regions_pdf_points_bottom_left"]
                if record["route"] == "layout_regions"
                else []
            ),
            boundary_markers_before_first_table=record.get(
                "boundary_markers_before_first_table", []
            ),
        )
        for record in ordered
    ]
    return TableExtractionConfig(
        schema_version="1.0.0",
        pipeline_id=f"{pipeline_id}_{source.source_id}_tables",
        source_release_version=source_release_version,
        source_id=source.source_id,
        expected_source_sha256=source.source_sha256,
        expected_pdf_page_count=source.source_page_count,
        physical_pdf_pages=[item.physical_pdf_page for item in routed_pages],
        artifact_relative_root=artifact_relative_root,
        validation_scope="routed_pages",
        table_id_prefix=prefix,
        family_id_prefix=f"{prefix}_table",
        routed_pages=routed_pages,
        retain_review_derivatives=retain_review_derivatives,
        execution=ExecutionConfig(maximum_workers=1),
        detection=detection,
        cleanup=cleanup,
        learned_fallback=learned_fallback or LearnedFallbackConfig(),
    )
