"""Typed configuration and page-selection models for document extraction."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from er_commons.document_extraction.routing import (
    NumericTableThresholds,
    StrictTableThresholds,
)
from er_commons.table_extraction.models import CleanupConfig, DetectionConfig


class PageRange(BaseModel):
    """One inclusive range of one-based physical PDF pages."""

    first_page: int = Field(ge=1)
    last_page: int = Field(ge=1)
    expected_printed_labels: list[str]
    stressors: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_order(self) -> PageRange:
        """Reject a reversed physical-page range."""
        if self.last_page < self.first_page:
            raise ValueError("last_page must be greater than or equal to first_page")
        return self


class SelectedSource(BaseModel):
    """One checksum-pinned source selected for extraction."""

    source_id: str
    expected_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_pdf_page_count: int = Field(gt=0)
    page_ranges: list[PageRange] = Field(min_length=1)


class SelectionSpec(BaseModel):
    """Fixed Task 03A document and page selection."""

    pilot_spec_schema_version: str
    pilot_id: str
    source_release_version: str
    source_manifest_path: Path
    page_number_basis: Literal["one_based_physical_pdf_page"]
    sources: list[SelectedSource] = Field(min_length=1)
    expected_selected_page_count: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_selection(self) -> SelectionSpec:
        """Require unique source IDs and unique selected physical pages."""
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("pilot source IDs must be unique")
        selected = [
            (source.source_id, page)
            for source in self.sources
            for page_range in source.page_ranges
            for page in range(page_range.first_page, page_range.last_page + 1)
        ]
        if len(selected) != len(set(selected)):
            raise ValueError("pilot physical pages must be unique")
        if len(selected) != self.expected_selected_page_count:
            raise ValueError("selected page count does not match expected_selected_page_count")
        if self.source_manifest_path.is_absolute():
            raise ValueError("source manifest path must be relative to ER_COMMONS_DATA_ROOT")
        return self


class PipelineConfig(BaseModel):
    """Complete clean-pipeline execution and comparison contract."""

    schema_version: str
    pipeline_id: str
    selection_spec_path: Path
    artifact_relative_root: Path
    model_inventory_relative_path: Path
    baseline_run_relative_root: Path
    configuration_id: Literal["docling_native_pypdfium2_heron_layout_only_cpu"]
    backend: Literal["pypdfium2"]
    device: Literal["cpu"]
    thread_count: Literal[4]
    expected_selected_page_count: Literal[10]
    expected_range_names: list[str] = Field(min_length=1)
    strict_table_dominant_thresholds: StrictTableThresholds
    numeric_table_bearing_thresholds: NumericTableThresholds
    expected_page_routes: dict[str, Literal["full_page_numeric", "layout_regions"]]
    table_detection: DetectionConfig
    table_cleanup: CleanupConfig

    @model_validator(mode="after")
    def validate_paths_and_ranges(self) -> PipelineConfig:
        """Keep committed paths relative and range names unique."""
        paths = (
            self.selection_spec_path,
            self.artifact_relative_root,
            self.model_inventory_relative_path,
            self.baseline_run_relative_root,
        )
        if any(path.is_absolute() for path in paths):
            raise ValueError("document pipeline paths must be relative")
        if len(self.expected_range_names) != len(set(self.expected_range_names)):
            raise ValueError("expected range names must be unique")
        return self


def load_json_model(path: Path, model: type[BaseModel]) -> tuple[BaseModel, str]:
    """Load one Pydantic JSON contract and return its byte-level SHA-256."""
    raw = path.read_bytes()
    return model.model_validate_json(raw), hashlib.sha256(raw).hexdigest()


def load_pipeline_config(path: Path) -> tuple[PipelineConfig, str]:
    """Load the tracked pipeline execution contract."""
    value, digest = load_json_model(path, PipelineConfig)
    return PipelineConfig.model_validate(value), digest


def load_selection_spec(path: Path) -> tuple[SelectionSpec, str]:
    """Load the fixed Task 03A page-selection contract."""
    value, digest = load_json_model(path, SelectionSpec)
    return SelectionSpec.model_validate(value), digest


def contiguous_ranges(source: SelectedSource) -> Iterator[tuple[int, int]]:
    """Yield minimal contiguous ranges in physical-page order."""
    pages = sorted(
        {
            page
            for selected in source.page_ranges
            for page in range(selected.first_page, selected.last_page + 1)
        }
    )
    start = previous = pages[0]
    for page in pages[1:]:
        if page != previous + 1:
            yield start, previous
            start = page
        previous = page
    yield start, previous


def range_name(source_id: str, first_page: int, last_page: int) -> str:
    """Return the stable range directory name used by both pilot runs."""
    return f"{source_id}_pages_{first_page:05d}_{last_page:05d}"
