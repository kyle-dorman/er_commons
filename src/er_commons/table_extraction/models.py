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
    validation_scope: Literal["ten_page_review", "first_600"] = "ten_page_review"
    comparison_relative_root: Path | None = None
    comparison_scope: Literal["exact", "baseline_pages"] = "exact"
    execution: ExecutionConfig
    detection: DetectionConfig
    cleanup: CleanupConfig

    @model_validator(mode="after")
    def validate_review_scope(self) -> TableExtractionConfig:
        """Prevent an accidental first-600-page run during code review."""
        expected_pages = (
            REVIEW_SAMPLE_PAGES if self.validation_scope == "ten_page_review" else FIRST_600_PAGES
        )
        if self.physical_pdf_pages != expected_pages:
            raise ValueError(f"{self.validation_scope} requires its exact reviewed physical pages")
        if len(set(self.physical_pdf_pages)) != len(self.physical_pdf_pages):
            raise ValueError("physical pages must be unique")
        if self.artifact_relative_root.is_absolute():
            raise ValueError("artifact root must be relative to ER_COMMONS_DATA_ROOT")
        if (
            self.comparison_relative_root is not None
            and self.comparison_relative_root.is_absolute()
        ):
            raise ValueError("comparison root must be relative to ER_COMMONS_DATA_ROOT")
        if self.comparison_scope == "baseline_pages" and self.comparison_relative_root is None:
            raise ValueError("baseline-pages comparison requires a comparison root")
        return self


def load_config(path: Path) -> tuple[TableExtractionConfig, str]:
    """Load the tracked configuration and return its SHA-256."""
    import hashlib

    raw = path.read_bytes()
    return TableExtractionConfig.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
