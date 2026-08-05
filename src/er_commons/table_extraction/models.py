"""Configuration models for the clean table-extraction pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

REVIEW_SAMPLE_PAGES = [19, 20, 273, 274, 527, 528, 540, 541, 592, 593]
FIRST_600_PAGES = list(range(1, 601))


class ExecutionConfig(BaseModel):
    """Sequential execution required by native PDF library state."""

    maximum_workers: Literal[1]


class DetectionConfig(BaseModel):
    """Reviewable thresholds for routing and region fusion."""

    render_scale: float = Field(gt=0)
    horizontal_kernel_pixels: int = Field(gt=0)
    vertical_kernel_pixels: int = Field(gt=0)
    minimum_region_width_pixels: int = Field(gt=0)
    minimum_region_height_pixels: int = Field(gt=0)
    minimum_intersections: int = Field(ge=4)
    complex_page_minimum_regions: int = Field(ge=2)
    maximum_network_ruling_coverage: float = Field(ge=0, le=1)
    minimum_region_match_iou: float = Field(gt=0, le=1)


class CleanupConfig(BaseModel):
    """Text cleanup and header-signature rules."""

    footer_pattern: str
    footer_counter_pattern: str
    leading_filename_pattern: str
    maximum_header_rows: int = Field(gt=0)
    minimum_numeric_cell_fraction_for_data_row: float = Field(ge=0, le=1)


class LearnedFallbackConfig(BaseModel):
    """Checksum-bound accurate TableFormer policy for unmatched Heron regions."""

    enabled: bool = False
    model_inventory_relative_path: Path | None = None
    expected_weights_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    expected_model_config_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    render_scale: float = Field(default=2.0, gt=0)
    cpu_threads: int = Field(default=8, gt=0)
    minimum_rows: int = Field(default=2, gt=0)
    minimum_columns: int = Field(default=2, gt=0)
    minimum_native_text_coverage: float = Field(default=0.9, ge=0, le=1)
    maximum_bbox_overshoot_pixels: float = Field(default=3.0, ge=0, le=10)

    @model_validator(mode="after")
    def validate_enabled_model_identity(self) -> LearnedFallbackConfig:
        """Require explicit immutable model identity whenever fallback is enabled."""
        if self.enabled and (
            self.model_inventory_relative_path is None
            or self.expected_weights_sha256 is None
            or self.expected_model_config_sha256 is None
        ):
            raise ValueError("enabled learned fallback requires exact model inventory and hashes")
        if self.model_inventory_relative_path is not None and (
            self.model_inventory_relative_path.is_absolute()
            or ".." in self.model_inventory_relative_path.parts
        ):
            raise ValueError("learned fallback model inventory must be data-root relative")
        return self


class BoundaryMarkerConfig(BaseModel):
    """Source marker that can block a cross-page continuation."""

    raw_object_ref: str
    provenance_index: int = Field(ge=0)
    label: Literal["caption", "section_header"]
    text: str
    bbox_pdf_points_bottom_left: list[float] = Field(min_length=4, max_length=4)


class RoutedPageConfig(BaseModel):
    """One upstream-selected page and the evidence needed by its parser route."""

    physical_pdf_page: int = Field(gt=0)
    route: Literal["full_page_numeric", "layout_regions"]
    layout_regions_pdf_points_bottom_left: list[list[float]] = Field(default_factory=list)
    boundary_markers_before_first_table: list[BoundaryMarkerConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_route_evidence(self) -> RoutedPageConfig:
        """Require bounded layout evidence only for the layout-region route."""
        if self.route == "layout_regions" and not self.layout_regions_pdf_points_bottom_left:
            raise ValueError("layout_regions route requires at least one region")
        if self.route == "full_page_numeric" and self.layout_regions_pdf_points_bottom_left:
            raise ValueError("full_page_numeric does not consume layout regions")
        if any(len(box) != 4 for box in self.layout_regions_pdf_points_bottom_left):
            raise ValueError("each layout region must contain four PDF coordinates")
        return self


class TableExtractionConfig(BaseModel):
    """Complete machine-readable clean table-pipeline contract."""

    schema_version: str
    pipeline_id: str
    source_release_version: str
    source_id: str
    expected_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_pdf_page_count: int = Field(gt=0)
    physical_pdf_pages: list[int]
    artifact_relative_root: Path
    validation_scope: Literal["ten_page_review", "first_600", "routed_pages"] = "ten_page_review"
    table_id_prefix: str = Field(default="g3", pattern=r"^[a-z0-9_]+$")
    family_id_prefix: str = Field(default="g3_table", pattern=r"^[a-z0-9_]+$")
    routed_pages: list[RoutedPageConfig] = Field(default_factory=list)
    retain_review_derivatives: bool = True
    execution: ExecutionConfig
    detection: DetectionConfig
    cleanup: CleanupConfig
    learned_fallback: LearnedFallbackConfig = Field(default_factory=LearnedFallbackConfig)

    @model_validator(mode="after")
    def validate_review_scope(self) -> TableExtractionConfig:
        """Prevent an accidental first-600-page run during code review."""
        if self.validation_scope == "ten_page_review":
            expected_pages = REVIEW_SAMPLE_PAGES
        elif self.validation_scope == "first_600":
            expected_pages = FIRST_600_PAGES
        else:
            expected_pages = [item.physical_pdf_page for item in self.routed_pages]
            if not expected_pages:
                raise ValueError("routed_pages requires at least one routed page")
        if self.physical_pdf_pages != expected_pages:
            raise ValueError(
                f"{self.validation_scope} requires its exact configured physical pages"
            )
        if self.physical_pdf_pages != sorted(self.physical_pdf_pages):
            raise ValueError("physical pages must be sorted")
        if len(set(self.physical_pdf_pages)) != len(self.physical_pdf_pages):
            raise ValueError("physical pages must be unique")
        if self.artifact_relative_root.is_absolute():
            raise ValueError("artifact root must be relative to ER_COMMONS_DATA_ROOT")
        if self.validation_scope != "routed_pages" and self.routed_pages:
            raise ValueError("fixed validation scopes cannot include routed page requests")
        return self


def load_config(path: Path) -> tuple[TableExtractionConfig, str]:
    """Load the tracked configuration and return its SHA-256."""
    import hashlib

    raw = path.read_bytes()
    return TableExtractionConfig.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
