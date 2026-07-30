"""Validated configuration boundary for the Task 03E hierarchy gate."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from er_commons.document_extraction.producer_config import HeadingHierarchyConfig


class HierarchyReviewPage(BaseModel):
    """One predeclared Appendix P page and the hierarchy risks it represents."""

    physical_page: int = Field(ge=1)
    stressors: list[str] = Field(min_length=1)


class HierarchyControlRange(BaseModel):
    """One fixed Task 03A main-report diagnostic range."""

    first_page: int = Field(ge=1)
    last_page: int = Field(ge=1)
    purpose: Literal[
        "false_positive_list_item_control",
        "false_negative_visible_subheading_control",
    ]
    context_only_pages: list[int]

    @model_validator(mode="after")
    def validate_range(self) -> HierarchyControlRange:
        """Keep context pages inside a forward inclusive range."""
        if self.last_page < self.first_page:
            raise ValueError("hierarchy control range is reversed")
        selected = set(range(self.first_page, self.last_page + 1))
        if not set(self.context_only_pages).issubset(selected):
            raise ValueError("context-only page falls outside its control range")
        return self


class ControlHarnessSpec(BaseModel):
    """Exact accepted harness inputs for the two hierarchy diagnostics."""

    accepted_pipeline_config_path: Path
    artifact_relative_root: Path
    source_id: Literal["deir_main"]
    expected_range_names: list[
        Literal[
            "deir_main_pages_00044_00046",
            "deir_main_pages_02000_02000",
        ]
    ]
    diagnostic_only: Literal[True]


class HierarchyThresholds(BaseModel):
    """Quantitative good-enough thresholds frozen before conversion."""

    maximum_undeclared_semantic_changes: Literal[0]
    maximum_material_failures: Literal[0]
    maximum_false_promotions: Literal[0]
    maximum_visible_toc_row_promotions: Literal[0]
    minimum_exact_level_rate_for_eligible_bookmark_headings: float = Field(ge=0, le=1)
    minimum_correct_relative_level_rate_for_reviewed_numbered_headings: float = Field(
        ge=0,
        le=1,
    )
    minimum_correct_level_rate_for_reviewed_bookmark_covered_unnumbered_headings: float = Field(
        ge=0,
        le=1,
    )
    maximum_repeat_build_mismatches: Literal[0]


class RepeatabilitySpec(BaseModel):
    """Independent build and immutable-publication sequence."""

    fresh_scratch_build_count: Literal[2]
    require_semantic_equality: Literal[True]
    require_candidate_owned_byte_equality_after_normalization: Literal[True]
    publish_after_repeat_gate: Literal[True]
    require_checksum_verified_reuse: Literal[True]


class ReviewCacheSpec(BaseModel):
    """Disposable render policy outside producer completion."""

    relative_root: Path
    include_only_declared_review_and_control_pages: Literal[True]
    excluded_from_producer_inventory: Literal[True]


class DiagnosticVariantSpec(BaseModel):
    """Prevent post-review tuning against an expanding sample."""

    allowed: Literal[False]
    reason: str


class StopConditions(BaseModel):
    """Plain-language terminal interpretations for the frozen gate."""

    accept: str
    reject: str
    inconclusive: str


class HierarchyEvaluationSpec(BaseModel):
    """Complete Task 03E comparison, review, and stop contract."""

    schema_version: Literal["1.0.0"]
    evaluation_id: Literal["brisbane_baylands_2025_deir_task03e_hierarchy_evaluation_v1"]
    baseline_producer_run_id: Literal[
        "prv1-93dfb03242a3651b90ee5424f36b7f6c58b5ac814dd48e1495b6359cdc6e92e0"
    ]
    candidate_config_path: Path
    source_id: Literal["deir_appendix_p"]
    source_sha256: Literal["2dfceac46931a946bc343d52b09104b7b58ed8831bc4f49a03f0b8655e4e6ea1"]
    physical_page_count: Literal[222]
    heading_hierarchy_options: HeadingHierarchyConfig
    appendix_p_review_pages: list[HierarchyReviewPage] = Field(min_length=1)
    main_report_controls: list[HierarchyControlRange] = Field(min_length=2)
    control_harness: ControlHarnessSpec
    stable_item_key: list[str] = Field(min_length=1)
    permitted_hierarchy_changes: list[str] = Field(min_length=1)
    exact_equality_surfaces: list[str] = Field(min_length=1)
    identity_normalizations: list[str] = Field(min_length=1)
    severity_categories: dict[str, str]
    thresholds: HierarchyThresholds
    repeatability: RepeatabilitySpec
    review_cache: ReviewCacheSpec
    diagnostic_variant: DiagnosticVariantSpec
    stop_conditions: StopConditions

    @model_validator(mode="after")
    def validate_frozen_scope(self) -> HierarchyEvaluationSpec:
        """Require unique bounded pages, exact controls, and relative paths."""
        pages = [item.physical_page for item in self.appendix_p_review_pages]
        if len(pages) != len(set(pages)):
            raise ValueError("Appendix P hierarchy review pages must be unique")
        if max(pages) > self.physical_page_count:
            raise ValueError("Appendix P hierarchy review page exceeds source coverage")
        controls = [
            (item.first_page, item.last_page, item.context_only_pages)
            for item in self.main_report_controls
        ]
        if controls != [(44, 46, [46]), (2000, 2000, [])]:
            raise ValueError("Task 03E main-report controls differ from the frozen ranges")
        for path in (
            self.candidate_config_path,
            self.review_cache.relative_root,
            self.control_harness.accepted_pipeline_config_path,
            self.control_harness.artifact_relative_root,
        ):
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Task 03E paths must be contained relative paths")
        if self.control_harness.expected_range_names != [
            "deir_main_pages_00044_00046",
            "deir_main_pages_02000_02000",
        ]:
            raise ValueError("Task 03E control range names differ")
        if set(self.severity_categories) != {
            "material",
            "retrieval_risk",
            "presentation_only",
        }:
            raise ValueError("Task 03E severity vocabulary differs")
        return self


def load_hierarchy_evaluation_spec(path: Path) -> tuple[HierarchyEvaluationSpec, str]:
    """Load the frozen hierarchy gate and return its byte-level SHA-256."""
    raw = path.read_bytes()
    return HierarchyEvaluationSpec.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
