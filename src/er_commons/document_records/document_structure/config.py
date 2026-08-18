"""Strict configuration for document-structure mapping."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocumentStructureExpectations(BaseModel):
    """Per-document reviewed counts; values live in config, not runtime literals."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    section_count: int
    bridge_entry_count: int
    canonical_block_count: int
    heading_count: int
    direct_membership_count: int
    mapped_block_count: int
    table_replacement_count: int
    figure_suppression_count: int


class StrictConfigModel(BaseModel):
    """Reject undeclared configuration and mutation after validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class DocumentStructureSource(StrictConfigModel):
    """One checksum-pinned source authorized for structure mapping."""

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    physical_page_count: int = Field(gt=0)


class DocumentStructureConfig(StrictConfigModel):
    """Content-bound paths and identities for the Appendix P semantic join."""

    schema_version: Literal["1.0.0"]
    semantic_policy_version: str = Field(min_length=1)
    candidate_version_name: str = Field(min_length=1)
    candidate_scope: Literal["document_scoped_non_release"]
    control_profile: Literal["task03e2d_bounded", "strict_quality_gate"] = "task03e2d_bounded"
    source: DocumentStructureSource
    source_manifest_relative_path: Path
    baseline_candidate_relative_root: Path
    baseline_candidate_id: str = Field(pattern=r"^exv1-[0-9a-f]{64}$")
    baseline_producer_relative_root: Path
    baseline_producer_run_id: str = Field(pattern=r"^prv1-[0-9a-f]{64}$")
    hierarchy_producer_relative_root: Path
    hierarchy_producer_run_id: str = Field(pattern=r"^prv1-[0-9a-f]{64}$")
    hierarchy_candidate_relative_root: Path
    hierarchy_candidate_id: str = Field(pattern=r"^hcorv1-[0-9a-f]{64}$")
    hierarchy_schema_relative_path: Path = Path(
        "benchmarks/er_bench/schemas/hierarchy_correction/v1/records.schema.json"
    )
    bounded_acceptance_relative_path: Path | None = None
    bounded_acceptance_policy_relative_path: Path | None = None
    producer_comparison_relative_path: Path | None = None
    semantic_spec_relative_path: Path
    semantic_schema_relative_path: Path
    artifact_relative_root: Path
    expectations: DocumentStructureExpectations | None = None

    @model_validator(mode="after")
    def validate_frozen_scope(self) -> DocumentStructureConfig:
        """Keep every configured path contained and the review sample exact."""
        paths = tuple(
            path
            for path in (
                self.source_manifest_relative_path,
                self.baseline_candidate_relative_root,
                self.baseline_producer_relative_root,
                self.hierarchy_producer_relative_root,
                self.hierarchy_candidate_relative_root,
                self.hierarchy_schema_relative_path,
                self.bounded_acceptance_relative_path,
                self.bounded_acceptance_policy_relative_path,
                self.producer_comparison_relative_path,
                self.semantic_spec_relative_path,
                self.semantic_schema_relative_path,
                self.artifact_relative_root,
            )
            if path is not None
        )
        if any(path.is_absolute() or ".." in path.parts for path in paths):
            raise ValueError("Task 03E.4 paths must be contained relative paths")
        if self.control_profile == "task03e2d_bounded" and (
            self.bounded_acceptance_relative_path is None
            or self.bounded_acceptance_policy_relative_path is None
            or self.producer_comparison_relative_path is None
        ):
            raise ValueError("bounded semantic control requires policy, acceptance, and comparison")
        if self.control_profile == "task03e2d_bounded" and self.expectations is None:
            raise ValueError("bounded semantic control requires reviewed expectations")
        if self.hierarchy_candidate_relative_root.name != self.hierarchy_candidate_id:
            raise ValueError("hierarchy candidate root must end with its configured candidate ID")
        if (
            self.control_profile == "task03e2d_bounded"
            and self.bounded_acceptance_relative_path is not None
            and self.bounded_acceptance_relative_path.parent.name != self.hierarchy_candidate_id
        ):
            raise ValueError("bounded acceptance root must match the hierarchy candidate ID")
        return self


def load_document_structure_config(
    path: Path,
) -> tuple[DocumentStructureConfig, str]:
    """Load the reviewed config and return the checksum of its exact bytes."""
    raw = path.read_bytes()
    return DocumentStructureConfig.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
