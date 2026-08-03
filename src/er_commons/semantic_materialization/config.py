"""Strict configuration for historical and generalized semantic materialization."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

BASELINE_CANDIDATE_ID = "exv1-2ea82d10c3459d4a4249b875c0ec1cbe594bc81a1c1b541f2fe85554b6854b28"
BASELINE_PRODUCER_RUN_ID = "prv1-93dfb03242a3651b90ee5424f36b7f6c58b5ac814dd48e1495b6359cdc6e92e0"
HIERARCHY_PRODUCER_RUN_ID = "prv1-92170ee8b5f5d51ffa738749ee872d7c7e9e5e7dbcb16cf6150bcf33d10d68e1"
SOURCE_ID = "deir_appendix_p"
SOURCE_SHA256 = "2dfceac46931a946bc343d52b09104b7b58ed8831bc4f49a03f0b8655e4e6ea1"


class SemanticExpectations(BaseModel):
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


HISTORICAL_EXPECTATIONS = SemanticExpectations(
    section_count=248,
    bridge_entry_count=5_340,
    canonical_block_count=3_024,
    heading_count=246,
    direct_membership_count=4_571,
    mapped_block_count=2_255,
    table_replacement_count=2_314,
    figure_suppression_count=2,
)


class StrictConfigModel(BaseModel):
    """Reject undeclared configuration and mutation after validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SemanticSource(StrictConfigModel):
    """The sole source authorized for Task 03E.4."""

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    physical_page_count: int = Field(gt=0)


class SemanticMaterializationConfig(StrictConfigModel):
    """Content-bound paths and identities for the Appendix P semantic join."""

    schema_version: Literal["1.0.0"]
    semantic_policy_version: str = Field(min_length=1)
    candidate_version_name: str = Field(min_length=1)
    candidate_scope: Literal["document_scoped_non_release"]
    control_profile: Literal["task03e2d_bounded", "strict_quality_gate"] = "task03e2d_bounded"
    reference_profile: Literal["frozen_equivalence", "independent_build"] = "frozen_equivalence"
    source: SemanticSource
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
    producer_comparison_relative_path: Path | None = None
    semantic_spec_relative_path: Path
    semantic_schema_relative_path: Path
    artifact_relative_root: Path
    mvp_reference_candidate_id: str | None = Field(default=None, pattern=r"^exv1-[0-9a-f]{64}$")
    review_cache_relative_root: Path | None = None
    rewrite_review_relative_root: Path | None = None
    review_pages: tuple[int, ...] = ()
    expectations: SemanticExpectations = HISTORICAL_EXPECTATIONS

    @model_validator(mode="after")
    def validate_frozen_scope(self) -> SemanticMaterializationConfig:
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
                self.producer_comparison_relative_path,
                self.semantic_spec_relative_path,
                self.semantic_schema_relative_path,
                self.artifact_relative_root,
                self.review_cache_relative_root,
                self.rewrite_review_relative_root,
            )
            if path is not None
        )
        if any(path.is_absolute() or ".." in path.parts for path in paths):
            raise ValueError("Task 03E.4 paths must be contained relative paths")
        if self.control_profile == "task03e2d_bounded" and (
            self.bounded_acceptance_relative_path is None
            or self.producer_comparison_relative_path is None
        ):
            raise ValueError("bounded semantic control requires acceptance and comparison")
        if self.reference_profile == "frozen_equivalence" and (
            self.mvp_reference_candidate_id is None
            or self.review_cache_relative_root is None
            or self.rewrite_review_relative_root is None
            or not self.review_pages
        ):
            raise ValueError("frozen semantic equivalence requires reference and review inputs")
        return self


def load_semantic_materialization_config(
    path: Path,
) -> tuple[SemanticMaterializationConfig, str]:
    """Load the reviewed config and return the checksum of its exact bytes."""
    raw = path.read_bytes()
    return SemanticMaterializationConfig.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
