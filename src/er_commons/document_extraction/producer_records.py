"""Typed JSON records shared by complete-document producer stages."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from er_commons.document_extraction.routing import TableRoute

MachineStatus = Literal[
    "not_started",
    "running",
    "complete",
    "complete_with_warnings",
    "partial",
    "failed",
    "not_applicable",
]


class ProducerRecord(BaseModel):
    """Reject unknown fields in persisted producer-owned records."""

    model_config = ConfigDict(extra="forbid")


class LayoutTableObservation(ProducerRecord):
    """One Docling table-region observation retained for lineage."""

    raw_object_ref: str
    provenance_index: int = Field(ge=0)
    bbox_pdf_points_bottom_left: list[float] = Field(min_length=4, max_length=4)


class PageRouteRecord(ProducerRecord):
    """One complete native-text and layout routing decision."""

    physical_pdf_page: int = Field(gt=0)
    page_size_pdf_points: list[float] = Field(min_length=2, max_length=2)
    native_character_count: int = Field(ge=0)
    nonspace_character_count: int = Field(ge=0)
    native_text_rectangle_count: int = Field(ge=0)
    nonempty_line_count: int = Field(ge=0)
    text_width_fraction: float = Field(ge=0)
    text_height_fraction: float = Field(ge=0)
    nonspace_characters_per_square_point: float = Field(ge=0)
    digit_fraction: float = Field(ge=0, le=1)
    coordinate_key_count: int = Field(ge=0)
    strict_table_dominant: bool
    strict_checks: dict[str, bool]
    numeric_table_bearing: bool
    numeric_checks: dict[str, bool]
    layout_table_region_count: int = Field(ge=0)
    layout_table_regions_pdf_points_bottom_left: list[list[float]]
    route: TableRoute
    source_id: str
    layout_table_observations: list[LayoutTableObservation]
    status: Literal["complete"]


class ConversionObservation(ProducerRecord):
    """Terminal facts about one complete Docling conversion."""

    source_id: str
    raw_status: str
    status: MachineStatus
    errors: list[dict[str, Any]]
    captured_python_warnings: list[str]
    source_manifest_warnings: list[str]
    expected_physical_pages: list[int]
    converted_physical_pages: list[int]
    page_coverage_complete: bool
    asset_count: int = Field(ge=0)
    wall_seconds: float = Field(ge=0)
    cpu_seconds: float = Field(ge=0)
    peak_rss_bytes: int = Field(ge=0)


class RoutingSummary(ProducerRecord):
    """Complete-document routing coverage and route counts."""

    status: Literal["complete"]
    document_scope_complete: Literal[True]
    page_count: int = Field(ge=0)
    route_counts: dict[TableRoute, int]


class TableStageObservation(ProducerRecord):
    """Terminal contract for the complete clean table stage."""

    status: MachineStatus
    document_scope_complete: Literal[True]
    verified_no_table_routes: bool | None = None
    routed_pages: list[int]
    routed_page_count: int = Field(ge=0)
    logical_table_count: int = Field(ge=0)
    family_assignment_count: int = Field(ge=0)
    family_count: int = Field(ge=0)
    zero_table_pages: list[int]
    manifest: str | None = None


class ProducerSummary(ProducerRecord):
    """Human-readable terminal summary written before the completion seal."""

    producer_run_id: str
    producer_status: MachineStatus
    publication_status: Literal["complete"]
    source_id: str
    physical_page_count: int = Field(gt=0)
    routing: dict[TableRoute, int]
    tables: TableStageObservation
    asset_count: int = Field(ge=0)
    warnings: list[str]
    error_count: int = Field(ge=0)
    wall_seconds: float = Field(ge=0)
    conversion_cpu_seconds: float = Field(ge=0)
    peak_rss_bytes: int = Field(ge=0)
    output_bytes_before_inventory: int = Field(ge=0)


class CompletionRecord(ProducerRecord):
    """Final non-inventoried seal for one immutable producer publication."""

    schema_version: Literal["1.0.0"]
    producer_run_id: str
    producer_status: MachineStatus
    publication_status: Literal["complete"]
    source_id: str
    source_sha256: str
    source_manifest_sha256: str
    artifact_inventory: Literal["records/artifact_inventory.json"]
    artifact_inventory_sha256: str
    completed_at_utc: str


class AttemptRecord(ProducerRecord):
    """Terminal failure evidence that can never resemble a completed run."""

    schema_version: Literal["1.0.0"]
    attempt_id: str
    producer_run_id: str | None
    status: Literal["failed"]
    failed_stage: str
    exception_type: str
    message: str
    started_at_utc: str
    finished_at_utc: str
    wall_seconds: float = Field(ge=0)
    completion_record: None
    removed_invalid_completion_marker: bool
