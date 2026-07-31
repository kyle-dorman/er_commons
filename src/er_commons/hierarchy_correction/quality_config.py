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
    quality_gate_id: Literal["brisbane_baylands_2025_deir_task03e2_quality_gate_v1"]
    development_cases: TrackedEvidence
    fixture_manifest: TrackedEvidence
    held_out_manifest: TrackedEvidence
    review_schema: TrackedEvidence
    task03e_evaluation_config: TrackedEvidence
    expected_exact_outline_anchor_count: Literal[29]
    expected_numbering_relation_count: Literal[21]
    main_report_control_ranges: tuple[ControlRange, ControlRange]
    task03e_review_reference: Task03EReviewReference
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
            self.task03e_evaluation_config.path,
            self.task03e_review_reference.artifact_relative_root,
            self.task03e_review_reference.control_ranges_relative_root,
            self.task03d1_reference.artifact_relative_root,
            self.review_artifact_relative_root,
        )
        if any(path.is_absolute() or ".." in path.parts for path in paths):
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
        if controls != expected:
            raise ValueError("Task 03E main-report control ranges differ")
        return self


def load_quality_gate_config(path: Path) -> tuple[QualityGateConfig, str]:
    """Load the checked-in gate configuration and return its byte digest."""
    raw = path.read_bytes()
    return QualityGateConfig.model_validate_json(raw), hashlib.sha256(raw).hexdigest()


def fixed_control_ranges_root(config: QualityGateConfig, data_root: Path) -> Path:
    """Resolve the checksum-verified accepted Task 03E fixed-control root."""
    reference = config.task03e_review_reference
    return (
        data_root
        / reference.artifact_relative_root
        / reference.comparison_id
        / reference.control_ranges_relative_root
    )
