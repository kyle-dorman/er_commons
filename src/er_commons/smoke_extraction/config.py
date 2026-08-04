"""Typed configuration for the diagnostic-only Task 03G.1 smoke."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.document_extraction.routing import (
    NumericTableThresholds,
    StrictTableThresholds,
)
from er_commons.table_extraction.models import CleanupConfig, DetectionConfig


class SmokeModel(BaseModel):
    """Reject undeclared fields in the checked-in smoke contract."""

    model_config = ConfigDict(extra="forbid")


class SmokeSource(SmokeModel):
    """One manifest-ordered source and its deterministic diagnostic pages."""

    source_id: str
    expected_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_byte_size: int = Field(gt=0)
    expected_pdf_page_count: int = Field(gt=0)
    selected_physical_pages: list[int] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def validate_pages(self) -> SmokeSource:
        """Require the exact front/middle/end rule for this source."""
        expected = selected_pages(self.expected_pdf_page_count)
        if self.selected_physical_pages != expected:
            raise ValueError(f"selected pages differ from frozen rule: {self.source_id}")
        return self


class ResourcePolicy(SmokeModel):
    """POC-sized sequential resource and stop controls."""

    maximum_source_workers: Literal[1]
    converter_thread_count: Literal[4]
    minimum_free_bytes_before_source: int = Field(gt=0)
    continue_after_source_failure: Literal[True]
    stop_before_pdf_run_without_explicit_approval: Literal[True]


class PlanningEstimate(SmokeModel):
    """Pre-run planning bounds that are not acceptance thresholds."""

    wall_time_hours_low: float = Field(gt=0)
    wall_time_hours_high: float = Field(gt=0)
    retained_bytes_low: int = Field(gt=0)
    retained_bytes_high: int = Field(gt=0)
    basis: str

    @model_validator(mode="after")
    def validate_bounds(self) -> PlanningEstimate:
        """Keep each planning interval ordered."""
        if self.wall_time_hours_high < self.wall_time_hours_low:
            raise ValueError("wall-time estimate is reversed")
        if self.retained_bytes_high < self.retained_bytes_low:
            raise ValueError("retained-byte estimate is reversed")
        return self


class SmokeSpec(SmokeModel):
    """Complete checked-in contract for one bounded diagnostic run."""

    schema_version: Literal["er_commons.task03g1_smoke.v1"]
    smoke_policy_version: Literal["task03g1-v1"]
    source_release_version: str
    source_manifest_relative_path: Path
    artifact_relative_root: Path
    production_extraction_id: str = Field(pattern=r"^exv1-[0-9a-f]{64}$")
    smoke_identity_prefix: Literal["smokev1-"]
    page_number_basis: Literal["one_based_physical_pdf_page"]
    selection_rule: Literal["all_if_at_most_10_else_first_3_center_4_last_3"]
    expected_source_count: Literal[35]
    expected_selected_page_count: Literal[342]
    selection_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    sources: list[SmokeSource]
    model_inventory_relative_path: Path
    configuration_id: Literal["docling_native_pypdfium2_heron_layout_only_cpu"]
    backend: Literal["pypdfium2"]
    device: Literal["cpu"]
    strict_table_dominant_thresholds: StrictTableThresholds
    numeric_table_bearing_thresholds: NumericTableThresholds
    table_detection: DetectionConfig
    table_cleanup: CleanupConfig
    retain_review_derivatives: Literal[False]
    resource_policy: ResourcePolicy
    planning_estimate: PlanningEstimate
    owned_code_paths: list[Path] = Field(min_length=1)

    @property
    def source_manifest_path(self) -> Path:
        """Expose the shared sealed-manifest verification interface."""
        return self.source_manifest_relative_path

    @model_validator(mode="after")
    def validate_contract(self) -> SmokeSpec:
        """Require contained paths, exact counts, ordering, and selection seal."""
        paths = (
            self.source_manifest_relative_path,
            self.artifact_relative_root,
            self.model_inventory_relative_path,
            *self.owned_code_paths,
        )
        if any(path.is_absolute() or ".." in path.parts for path in paths):
            raise ValueError("smoke paths must be contained relative paths")
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != self.expected_source_count or len(source_ids) != len(set(source_ids)):
            raise ValueError("smoke source count or uniqueness differs")
        pairs = ordered_page_pairs(self.sources)
        if len(pairs) != self.expected_selected_page_count:
            raise ValueError("smoke selected-page count differs")
        if selection_sha256(pairs) != self.selection_sha256:
            raise ValueError("smoke selection checksum differs")
        return self


def selected_pages(page_count: int) -> list[int]:
    """Apply the frozen deterministic spread rule to one page count."""
    if page_count <= 0:
        raise ValueError("page count must be positive")
    if page_count <= 10:
        return list(range(1, page_count + 1))
    center_start = (page_count - 4) // 2 + 1
    return [
        1,
        2,
        3,
        *range(center_start, center_start + 4),
        page_count - 2,
        page_count - 1,
        page_count,
    ]


def ordered_page_pairs(sources: list[SmokeSource]) -> list[list[str | int]]:
    """Return the exact ordered source/page identity surface."""
    return [
        [source.source_id, page] for source in sources for page in source.selected_physical_pages
    ]


def selection_sha256(pairs: list[list[str | int]]) -> str:
    """Hash the ordered selection with RFC 8785 canonical JSON."""
    import rfc8785

    return hashlib.sha256(rfc8785.dumps(pairs)).hexdigest()


def load_smoke_spec(path: Path) -> tuple[SmokeSpec, str]:
    """Load the smoke contract and return its byte-level checksum."""
    raw = path.read_bytes()
    return SmokeSpec.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
