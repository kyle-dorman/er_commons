"""Reviewed configuration for the Task 03E.2 quality gate."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    """Reject unreviewed quality-evidence fields and mutation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class TrackedEvidence(StrictModel):
    """One tracked acceptance input and its exact byte digest."""

    path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ControlRange(StrictModel):
    """One frozen Task 03E main-report control range."""

    range_name: str = Field(min_length=1)
    first_page: int = Field(gt=0)
    last_page: int = Field(gt=0)
    purpose: str = Field(min_length=1)
    document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    conversion_pages_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class Task03D1Reference(StrictModel):
    """Accepted canonical reference identity and terminal seals."""

    artifact_relative_root: Path
    extraction_id: str = Field(pattern=r"^exv1-[0-9a-f]{64}$")
    completion_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class Task03EReviewReference(StrictModel):
    """Accepted Task 03E reports and fixed control-range artifact root."""

    artifact_relative_root: Path
    comparison_id: str = Field(pattern=r"^cmpv2-[0-9a-f]{64}$")
    control_ranges_relative_root: Path
    producer_comparison_report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bounded_review_report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    control_report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class QualityGateConfig(StrictModel):
    """Reviewed external inputs required before candidate publication."""

    schema_version: Literal["1.0.0"]
    quality_gate_id: str = Field(min_length=1)
    quality_profile: Literal["appendix_p_task03e2", "generic_document"] = "appendix_p_task03e2"
    development_cases: TrackedEvidence
    fixture_manifest: TrackedEvidence
    held_out_manifest: TrackedEvidence
    review_schema: TrackedEvidence
    task03e_evaluation_config: TrackedEvidence | None = None
    expected_exact_outline_anchor_count: int = Field(ge=0)
    expected_outline_r03_count: int = Field(default=28, ge=0)
    expected_outline_toc_override_count: int = Field(default=1, ge=0)
    expected_numbered_heading_count: int = Field(default=23, ge=0)
    expected_numbering_relation_count: int = Field(ge=0)
    document_review_pages: tuple[int, ...] = ()
    main_report_control_ranges: tuple[ControlRange, ...] = ()
    task03e_review_reference: Task03EReviewReference | None = None
    task03d1_reference: Task03D1Reference
    review_artifact_relative_root: Path

    @model_validator(mode="after")
    def validate_frozen_scope(self) -> QualityGateConfig:
        """Keep paths contained and pin the two accepted control ranges."""
        paths = (
            self.development_cases.path,
            self.fixture_manifest.path,
            self.held_out_manifest.path,
            self.review_schema.path,
            self.task03d1_reference.artifact_relative_root,
            self.review_artifact_relative_root,
        )
        optional_paths = (
            self.task03e_evaluation_config.path
            if self.task03e_evaluation_config is not None
            else None,
            self.task03e_review_reference.artifact_relative_root
            if self.task03e_review_reference is not None
            else None,
            self.task03e_review_reference.control_ranges_relative_root
            if self.task03e_review_reference is not None
            else None,
        )
        if any(
            path.is_absolute() or ".." in path.parts
            for path in (*paths, *optional_paths)
            if path is not None
        ):
            raise ValueError("quality-gate paths must be contained relative paths")
        controls = tuple(
            (item.range_name, item.first_page, item.last_page, item.purpose)
            for item in self.main_report_control_ranges
        )
        expected = (
            ("deir_main_pages_00044_00046", 44, 46, "false_positive_list_item_control"),
            (
                "deir_main_pages_02000_02000",
                2000,
                2000,
                "false_negative_visible_subheading_control",
            ),
        )
        if self.quality_profile == "appendix_p_task03e2":
            if controls != expected:
                raise ValueError("Task 03E main-report control ranges differ")
            if self.task03e_evaluation_config is None or self.task03e_review_reference is None:
                raise ValueError("Task 03E quality evidence differs from the frozen scope")
        elif (
            not self.document_review_pages
            or len(set(self.document_review_pages)) != len(self.document_review_pages)
            or min(self.document_review_pages) < 1
            or self.main_report_control_ranges
            or self.task03e_evaluation_config is not None
            or self.task03e_review_reference is not None
        ):
            raise ValueError("generic quality profile requires document-local review evidence")
        if self.expected_exact_outline_anchor_count != (
            self.expected_outline_r03_count + self.expected_outline_toc_override_count
        ):
            raise ValueError("quality outline subcounts do not sum to the declared total")
        return self


def load_quality_gate_config(path: Path) -> tuple[QualityGateConfig, str]:
    """Load the checked-in gate configuration and return its byte digest."""
    raw = path.read_bytes()
    return QualityGateConfig.model_validate_json(raw), hashlib.sha256(raw).hexdigest()


def fixed_control_ranges_root(config: QualityGateConfig, data_root: Path) -> Path:
    """Resolve the checksum-verified accepted Task 03E fixed-control root."""
    reference = config.task03e_review_reference
    if reference is None:
        raise ValueError("document-local quality profiles have no Task 03E control root")
    return (
        data_root
        / reference.artifact_relative_root
        / reference.comparison_id
        / reference.control_ranges_relative_root
    )
