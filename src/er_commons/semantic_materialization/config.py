"""Strict Task 03E.4 configuration and frozen Appendix P selections."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

BASELINE_CANDIDATE_ID = "exv1-2ea82d10c3459d4a4249b875c0ec1cbe594bc81a1c1b541f2fe85554b6854b28"
BASELINE_PRODUCER_RUN_ID = "prv1-93dfb03242a3651b90ee5424f36b7f6c58b5ac814dd48e1495b6359cdc6e92e0"
HIERARCHY_PRODUCER_RUN_ID = "prv1-92170ee8b5f5d51ffa738749ee872d7c7e9e5e7dbcb16cf6150bcf33d10d68e1"
SOURCE_ID = "deir_appendix_p"
SOURCE_SHA256 = "2dfceac46931a946bc343d52b09104b7b58ed8831bc4f49a03f0b8655e4e6ea1"


@dataclass(frozen=True)
class AppendixPScope:
    """Frozen Appendix P counts and review sample accepted by Task 03E.4."""

    page_count: int
    section_count: int
    bridge_entry_count: int
    canonical_block_count: int
    heading_count: int
    direct_membership_count: int
    mapped_block_count: int
    table_replacement_count: int
    figure_suppression_count: int
    review_pages: tuple[int, ...]


APPENDIX_P_SCOPE = AppendixPScope(
    page_count=222,
    section_count=248,
    bridge_entry_count=5_340,
    canonical_block_count=3_024,
    heading_count=246,
    direct_membership_count=4_571,
    mapped_block_count=2_255,
    table_replacement_count=2_314,
    figure_suppression_count=2,
    review_pages=(2, 4, 8, 73, 82, 96, 105, 112, 166, 220),
)


class StrictConfigModel(BaseModel):
    """Reject undeclared configuration and mutation after validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SemanticSource(StrictConfigModel):
    """The sole source authorized for Task 03E.4."""

    source_id: Literal["deir_appendix_p"]
    source_sha256: Literal["2dfceac46931a946bc343d52b09104b7b58ed8831bc4f49a03f0b8655e4e6ea1"]
    physical_page_count: Literal[222]


class SemanticMaterializationConfig(StrictConfigModel):
    """Content-bound paths and identities for the Appendix P semantic join."""

    schema_version: Literal["1.0.0"]
    semantic_policy_version: Literal["task03e4-v1"]
    candidate_version_name: Literal["appendix_p_semantic_candidate_v2"]
    candidate_scope: Literal["document_scoped_non_release"]
    source: SemanticSource
    source_manifest_relative_path: Path
    baseline_candidate_relative_root: Path
    baseline_candidate_id: Literal[
        "exv1-2ea82d10c3459d4a4249b875c0ec1cbe594bc81a1c1b541f2fe85554b6854b28"
    ]
    baseline_producer_relative_root: Path
    baseline_producer_run_id: Literal[
        "prv1-93dfb03242a3651b90ee5424f36b7f6c58b5ac814dd48e1495b6359cdc6e92e0"
    ]
    hierarchy_producer_relative_root: Path
    hierarchy_producer_run_id: Literal[
        "prv1-92170ee8b5f5d51ffa738749ee872d7c7e9e5e7dbcb16cf6150bcf33d10d68e1"
    ]
    hierarchy_candidate_relative_root: Path
    hierarchy_candidate_id: Literal[
        "hcorv1-aab01b14c3122dbc0f5cec57147b5be2eadaf1cd895311ef7dafa46b469348b1"
    ]
    bounded_acceptance_relative_path: Path
    producer_comparison_relative_path: Path
    semantic_spec_relative_path: Path
    semantic_schema_relative_path: Path
    artifact_relative_root: Path
    mvp_reference_candidate_id: Literal[
        "exv1-c500c1731aa02a97d3cebe1b582eb8b03671a75b29eb3f1df349edd2f34fe5bf"
    ]
    review_cache_relative_root: Path
    rewrite_review_relative_root: Path
    review_pages: tuple[int, ...] = Field(min_length=10, max_length=10)

    @model_validator(mode="after")
    def validate_frozen_scope(self) -> SemanticMaterializationConfig:
        """Keep every configured path contained and the review sample exact."""
        paths = (
            self.source_manifest_relative_path,
            self.baseline_candidate_relative_root,
            self.baseline_producer_relative_root,
            self.hierarchy_producer_relative_root,
            self.hierarchy_candidate_relative_root,
            self.bounded_acceptance_relative_path,
            self.producer_comparison_relative_path,
            self.semantic_spec_relative_path,
            self.semantic_schema_relative_path,
            self.artifact_relative_root,
            self.review_cache_relative_root,
            self.rewrite_review_relative_root,
        )
        if any(path.is_absolute() or ".." in path.parts for path in paths):
            raise ValueError("Task 03E.4 paths must be contained relative paths")
        if self.review_pages != APPENDIX_P_SCOPE.review_pages:
            raise ValueError("Task 03E.4 review pages differ from the frozen sample")
        return self


def load_semantic_materialization_config(
    path: Path,
) -> tuple[SemanticMaterializationConfig, str]:
    """Load the reviewed config and return the checksum of its exact bytes."""
    raw = path.read_bytes()
    return SemanticMaterializationConfig.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
