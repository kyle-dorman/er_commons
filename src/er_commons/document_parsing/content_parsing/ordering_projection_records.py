"""Strict immutable records persisted by the ordering projection stage."""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from er_commons.document_parsing.content_parsing.page_projection import PageEvidenceProjection
from er_commons.document_parsing.content_parsing.records import (
    LayoutTableObservation,
    TableBoundaryMarker,
    TableStageObservation,
)
from er_commons.document_parsing.content_parsing.table_stage_reference import (
    TableStageReference,
)


class ProjectionRecord(BaseModel):
    """Strict persisted contract for pre-aggregate ordering records."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class TableEvidenceOutcome(StrEnum):
    """Page-local extraction outcomes used by the suppression policy."""

    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    FAILED = "failed"
    ROUTE_ONLY = "route_only"
    UNMATCHED = "unmatched"


class ConfirmedTableRegion(ProjectionRecord):
    """One validated custom-table footprint in displayed PDF coordinates."""

    table_ref: str = Field(min_length=1)
    bbox_pdf_points_bottom_left: tuple[float, float, float, float]
    page_size_pdf_points: tuple[float, float]
    suppression_scope: Literal["region", "page"] = "region"

    @field_validator("bbox_pdf_points_bottom_left", "page_size_pdf_points", mode="before")
    @classmethod
    def accept_json_arrays(cls, value: Any) -> Any:
        """Normalize persisted JSON arrays into the immutable tuple contract."""
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_geometry(self) -> ConfirmedTableRegion:
        """Reject unusable geometry before it can authorize text suppression."""
        left, bottom, right, top = self.bbox_pdf_points_bottom_left
        width, height = self.page_size_pdf_points
        values = (left, bottom, right, top, width, height)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("confirmed table geometry must be finite")
        if width <= 0 or height <= 0 or right <= left or top <= bottom:
            raise ValueError("confirmed table geometry must have positive area")
        tolerance = 1e-4
        if (
            left < -tolerance
            or bottom < -tolerance
            or right > width + tolerance
            or top > height + tolerance
        ):
            raise ValueError("confirmed table geometry must lie on its displayed page")
        return self


class RoutingFeatures(ProjectionRecord):
    """Typed native-text and displayed-page measurements used by routing."""

    physical_pdf_page: int = Field(gt=0)
    page_size_pdf_points: tuple[float, float]
    displayed_page_size_pdf_points: tuple[float, float]
    source_page_bbox_pdf_points_bottom_left: tuple[float, float, float, float]
    routing_page_bbox_pdf_points_bottom_left: tuple[float, float, float, float]
    routing_coordinate_system: Literal["displayed_pdf_points_bottom_left"]
    page_rotation_degrees: Literal[0, 90, 180, 270]
    native_character_count: int = Field(ge=0)
    nonspace_character_count: int = Field(ge=0)
    native_text_rectangle_count: int = Field(ge=0)
    nonempty_line_count: int = Field(ge=0)
    text_width_fraction: float = Field(ge=0)
    text_height_fraction: float = Field(ge=0)
    nonspace_characters_per_square_point: float = Field(ge=0)
    digit_fraction: float = Field(ge=0, le=1)
    coordinate_key_count: int = Field(ge=0)

    @field_validator(
        "page_size_pdf_points",
        "displayed_page_size_pdf_points",
        "source_page_bbox_pdf_points_bottom_left",
        "routing_page_bbox_pdf_points_bottom_left",
        mode="before",
    )
    @classmethod
    def accept_json_arrays(cls, value: Any) -> Any:
        """Normalize JSON arrays into immutable coordinate tuples."""
        return tuple(value) if isinstance(value, list) else value


class OrderingProjectionPage(ProjectionRecord):
    """One complete, typed page-local input to aggregate ordering."""

    page_no: int = Field(gt=0)
    source_id: str = Field(min_length=1)
    physical_pdf_page: int = Field(gt=0)
    features: RoutingFeatures
    layout_table_observations: tuple[LayoutTableObservation, ...]
    boundary_markers_before_first_table: tuple[TableBoundaryMarker, ...]
    range_id: str = Field(min_length=1)
    ordering_suppressed_table_refs: tuple[str, ...] = ()
    ordering_suppressed_table_regions: tuple[ConfirmedTableRegion, ...] = ()

    @field_validator(
        "layout_table_observations",
        "boundary_markers_before_first_table",
        "ordering_suppressed_table_refs",
        "ordering_suppressed_table_regions",
        mode="before",
    )
    @classmethod
    def accept_json_collections(cls, value: Any) -> Any:
        """Normalize persisted arrays into immutable page collections."""
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_page(self) -> OrderingProjectionPage:
        """Require aligned page identities and suppression evidence."""
        if (
            self.page_no != self.physical_pdf_page
            or self.page_no != self.features.physical_pdf_page
        ):
            raise ValueError("ordering projection page identities must agree")
        if any(not ref for ref in self.ordering_suppressed_table_refs):
            raise ValueError("ordering projection table references must be non-empty")
        if len(set(self.ordering_suppressed_table_refs)) != len(
            self.ordering_suppressed_table_refs
        ):
            raise ValueError("ordering projection table references must be unique")
        region_refs = tuple(item.table_ref for item in self.ordering_suppressed_table_regions)
        if region_refs != self.ordering_suppressed_table_refs:
            raise ValueError("ordering projection table references and regions must agree")
        return self

    def as_page_evidence(self) -> PageEvidenceProjection:
        """Return the existing typed routing input without lossy dictionary picking."""
        return PageEvidenceProjection(
            source_id=self.source_id,
            physical_pdf_page=self.physical_pdf_page,
            features=self.features.model_dump(mode="json"),
            layout_table_observations=[
                item.model_dump(mode="json") for item in self.layout_table_observations
            ],
            boundary_markers_before_first_table=[
                item.model_dump(mode="json") for item in self.boundary_markers_before_first_table
            ],
            range_id=self.range_id,
        )


class OrderingTableStageObservation(ProjectionRecord):
    """Immutable table-stage completion facts bound into the projection."""

    status: Literal["complete", "complete_with_warnings", "not_applicable"]
    document_scope_complete: Literal[True]
    verified_no_table_routes: bool | None = None
    routed_pages: tuple[int, ...]
    routed_page_count: int = Field(ge=0)
    logical_table_count: int = Field(ge=0)
    family_assignment_count: int = Field(ge=0)
    family_count: int = Field(ge=0)
    zero_table_pages: tuple[int, ...]
    manifest: str | None = None

    @field_validator("routed_pages", "zero_table_pages", mode="before")
    @classmethod
    def accept_json_arrays(cls, value: Any) -> Any:
        """Normalize persisted page arrays into immutable tuples."""
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_completion(self) -> OrderingTableStageObservation:
        """Reject internally inconsistent successful table-stage claims."""
        if self.routed_page_count != len(self.routed_pages):
            raise ValueError("table-stage routed page count differs")
        if len(set(self.routed_pages)) != len(self.routed_pages):
            raise ValueError("table-stage routed pages must be unique")
        if not set(self.zero_table_pages) <= set(self.routed_pages):
            raise ValueError("zero-table pages must be routed pages")
        no_table = self.status == "not_applicable"
        if no_table and (
            self.verified_no_table_routes is not True
            or self.routed_pages
            or self.logical_table_count
            or self.family_assignment_count
            or self.family_count
            or self.manifest is not None
        ):
            raise ValueError("not-applicable table stages require explicit empty evidence")
        if not no_table and not self.manifest:
            raise ValueError("completed table stages require a manifest identity")
        return self

    def as_producer_record(self) -> TableStageObservation:
        """Return the shared producer record used by table-stage consumers."""
        return TableStageObservation.model_validate(self.model_dump(mode="python"))


class TableEvidenceDecision(ProjectionRecord):
    """One explicit page-local disposition for ordering projection."""

    physical_pdf_page: int = Field(gt=0)
    outcome: TableEvidenceOutcome
    confirmed_table_refs: tuple[str, ...] = ()
    confirmed_table_regions: tuple[ConfirmedTableRegion, ...] = ()
    reason: str = ""

    @model_validator(mode="after")
    def validate_refs(self) -> TableEvidenceDecision:
        """Reject duplicate or empty confirmed table references."""
        if any(not ref for ref in self.confirmed_table_refs):
            raise ValueError("confirmed table references must be non-empty")
        if len(set(self.confirmed_table_refs)) != len(self.confirmed_table_refs):
            raise ValueError("confirmed table references must be unique")
        region_refs = tuple(region.table_ref for region in self.confirmed_table_regions)
        if region_refs != self.confirmed_table_refs:
            raise ValueError("confirmed table references and regions must agree exactly")
        return self

    @property
    def may_suppress_table_text(self) -> bool:
        """Only complete confirmed extraction can authorize suppression."""
        return self.outcome is TableEvidenceOutcome.CONFIRMED and bool(self.confirmed_table_refs)

    def as_record(self) -> dict[str, Any]:
        """Return the stable JSON representation used by the aggregate worker."""
        return self.model_dump(mode="json")


def _validate_page_coverage(
    pages: tuple[OrderingProjectionPage, ...],
    decisions: tuple[TableEvidenceDecision, ...],
) -> None:
    """Require one ordered, unique decision for each projection page."""
    page_numbers = [page.page_no for page in pages]
    if len(set(page_numbers)) != len(page_numbers):
        raise ValueError("ordering projection pages must have unique page_no values")
    decision_numbers = [decision.physical_pdf_page for decision in decisions]
    if page_numbers != sorted(page_numbers):
        raise ValueError("ordering projection pages must be ordered")
    if page_numbers != decision_numbers:
        raise ValueError("ordering projection pages and decisions must have exact coverage")
    for page, decision in zip(pages, decisions, strict=True):
        if page.ordering_suppressed_table_refs != decision.confirmed_table_refs:
            raise ValueError("ordering projection pages and decisions must agree on suppression")


class OrderingProjection(ProjectionRecord):
    """Reduced ordering input plus immutable provenance for every page."""

    pages: tuple[OrderingProjectionPage, ...]
    decisions: tuple[TableEvidenceDecision, ...]

    @model_validator(mode="after")
    def validate_page_coverage(self) -> OrderingProjection:
        """Require one ordered decision for each ordered projection page."""
        _validate_page_coverage(self.pages, self.decisions)
        return self


class OrderingProjectionArtifact(ProjectionRecord):
    """Complete persisted envelope consumed by the aggregate worker."""

    schema_version: Literal["er_commons.ordering_projection.v3"] = (
        "er_commons.ordering_projection.v3"
    )
    table_stage_observation: OrderingTableStageObservation
    table_stage: TableStageReference
    pages: tuple[OrderingProjectionPage, ...]
    decisions: tuple[TableEvidenceDecision, ...]

    @model_validator(mode="after")
    def validate_page_coverage(self) -> OrderingProjectionArtifact:
        """Require aligned page decisions and table completion evidence."""
        _validate_page_coverage(self.pages, self.decisions)
        no_table = self.table_stage_observation.status == "not_applicable"
        if no_table != (self.table_stage.completion_marker == "no_table_stage.json"):
            raise ValueError("table-stage observation and completion marker differ")
        return self

    def relocated_table_stage(self, relative_path: str) -> OrderingProjectionArtifact:
        """Rebind the same sealed table evidence beneath a new runtime owner."""
        return self.model_copy(update={"table_stage": self.table_stage.relocated(relative_path)})


__all__ = [
    "ConfirmedTableRegion",
    "OrderingProjection",
    "OrderingProjectionArtifact",
    "OrderingProjectionPage",
    "OrderingTableStageObservation",
    "RoutingFeatures",
    "TableEvidenceDecision",
    "TableEvidenceOutcome",
]
