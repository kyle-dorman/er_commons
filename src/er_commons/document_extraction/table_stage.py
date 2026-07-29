"""Bridge document routing into the complete clean table pipeline.

This module owns the integration contract.  It creates one validated,
source-scoped table request, invokes the public table orchestrator, and checks
that cleanup and family assignment completed for every resulting table.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from er_commons.document_extraction.artifacts import load_json, read_jsonl
from er_commons.document_extraction.config import PipelineConfig, SelectionSpec
from er_commons.document_extraction.sources import ResolvedSource
from er_commons.source_freeze import write_json_atomic
from er_commons.table_extraction.models import (
    CleanupConfig,
    DetectionConfig,
    ExecutionConfig,
    RoutedPageConfig,
    TableExtractionConfig,
)
from er_commons.table_extraction.pipeline import run_table_extraction


def build_table_request(
    document_config: PipelineConfig,
    selection: SelectionSpec,
    source: ResolvedSource,
    route_records: list[dict[str, Any]],
) -> TableExtractionConfig:
    """Build one validated source-scoped request from positive page routes."""
    return build_complete_table_request(
        pipeline_id=document_config.pipeline_id,
        source_release_version=selection.source_release_version,
        source=source,
        route_records=route_records,
        artifact_relative_root=(
            document_config.artifact_relative_root / "table_pipeline" / source.source_id
        ),
        detection=document_config.table_detection,
        cleanup=document_config.table_cleanup,
        retain_review_derivatives=True,
    )


def build_complete_table_request(
    *,
    pipeline_id: str,
    source_release_version: str,
    source: ResolvedSource,
    route_records: list[dict[str, Any]],
    artifact_relative_root: Path,
    detection: DetectionConfig,
    cleanup: CleanupConfig,
    retain_review_derivatives: bool,
) -> TableExtractionConfig:
    """Adapt positive routes to the accepted clean table-pipeline contract."""
    ordered = sorted(route_records, key=lambda item: int(item["physical_pdf_page"]))
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
        comparison_relative_root=None,
        comparison_scope="exact",
        retain_review_derivatives=retain_review_derivatives,
        execution=ExecutionConfig(maximum_workers=1),
        detection=detection,
        cleanup=cleanup,
    )


def validate_table_run(table_root: Path, expected_page_count: int) -> dict[str, Any]:
    """Validate the full table-pipeline artifacts used by the document gate."""
    summary = load_json(table_root / "summary.json")
    tables = read_jsonl(table_root / "tables.jsonl")
    assignments = read_jsonl(table_root / "family_assignments.jsonl")
    assigned_ids = {str(item["table_id"]) for item in assignments}
    table_ids = {str(item["table_id"]) for item in tables}
    complete = bool(
        summary["page_count"] == expected_page_count
        and not summary["zero_table_pages"]
        and len(table_ids) == len(tables)
        and assigned_ids == table_ids
    )
    return {
        "summary": summary,
        "table_count": len(tables),
        "family_assignment_count": len(assignments),
        "complete": complete,
    }


def run_table_stage(
    data_root: Path,
    document_root: Path,
    config: PipelineConfig,
    selection: SelectionSpec,
    sources: list[ResolvedSource],
    route_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run one complete table pipeline per source containing positive routes."""
    positive = [record for record in route_records if record["route"] != "no_table_route"]
    by_source = {source.source_id: source for source in sources}
    runs = []
    for source_id in sorted({str(record["source_id"]) for record in positive}):
        source_routes = [record for record in positive if record["source_id"] == source_id]
        request = build_table_request(config, selection, by_source[source_id], source_routes)
        request_path = document_root / "table_pipeline_requests" / f"{source_id}.json"
        write_json_atomic(request_path, request.model_dump(mode="json"))
        manifest_path = run_table_extraction(data_root, request_path)
        validation = validate_table_run(manifest_path.parent, len(source_routes))
        runs.append(
            {
                "source_id": source_id,
                "manifest": manifest_path.relative_to(document_root).as_posix(),
                **validation,
            }
        )
    result = {
        "runs": runs,
        "all_complete": all(run["complete"] for run in runs),
    }
    write_json_atomic(document_root / "table_pipeline_summary.json", result)
    return result
