"""Strict configuration for the Task 03E.2 hierarchy-correction overlay."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ACCEPTED_PRODUCER_RUN_ID = "prv1-92170ee8b5f5d51ffa738749ee872d7c7e9e5e7dbcb16cf6150bcf33d10d68e1"
APPENDIX_P_SOURCE_ID = "deir_appendix_p"
APPENDIX_P_SOURCE_SHA256 = "2dfceac46931a946bc343d52b09104b7b58ed8831bc4f49a03f0b8655e4e6ea1"
APPENDIX_P_SOURCE_BYTES = 6_528_561
APPENDIX_P_PAGE_COUNT = 222


class StrictConfigModel(BaseModel):
    """Reject unreviewed fields and mutation in candidate-producing config."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class CorrectionSource(StrictConfigModel):
    """The sole checksum-pinned source allowed by the v1 correction task."""

    source_id: Literal["deir_appendix_p"]
    official_title: str = Field(min_length=1)
    expected_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_byte_size: int = Field(gt=0)
    expected_pdf_page_count: int = Field(gt=0)


class HierarchyCorrectionConfig(StrictConfigModel):
    """Reviewed paths and immutable identities for one correction candidate."""

    schema_version: Literal["1.0.0"]
    policy_version: Literal["1.0.0"]
    pipeline_id: Literal["brisbane_baylands_2025_deir_task03e2_hierarchy_correction_v1"]
    publication_authorization: Literal["strict_quality_gate", "bounded_acceptance"]
    source_release_version: Literal["brisbane_baylands_2025_deir_sources_v1"]
    source_manifest_relative_path: Path
    source: CorrectionSource
    producer_artifact_relative_root: Path
    producer_run_id: Literal[
        "prv1-92170ee8b5f5d51ffa738749ee872d7c7e9e5e7dbcb16cf6150bcf33d10d68e1"
    ]
    artifact_relative_root: Path
    review_artifact_relative_root: Path
    policy_relative_path: Path
    schema_relative_path: Path

    @property
    def source_manifest_path(self) -> Path:
        """Expose the sealed-release selection interface."""
        return self.source_manifest_relative_path

    @model_validator(mode="after")
    def validate_frozen_scope(self) -> HierarchyCorrectionConfig:
        """Keep paths contained and freeze the accepted producer and source."""
        for path in (
            self.source_manifest_relative_path,
            self.producer_artifact_relative_root,
            self.artifact_relative_root,
            self.review_artifact_relative_root,
            self.policy_relative_path,
            self.schema_relative_path,
        ):
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("hierarchy-correction paths must be contained relative paths")
        source = self.source
        if (
            source.source_id != APPENDIX_P_SOURCE_ID
            or source.expected_sha256 != APPENDIX_P_SOURCE_SHA256
            or source.expected_byte_size != APPENDIX_P_SOURCE_BYTES
            or source.expected_pdf_page_count != APPENDIX_P_PAGE_COUNT
        ):
            raise ValueError("Task 03E.2 source must be the approved Appendix P")
        if self.producer_run_id != ACCEPTED_PRODUCER_RUN_ID:
            raise ValueError("Task 03E.2 must consume the accepted Task 03E producer")
        return self


def load_hierarchy_correction_config(
    path: Path,
) -> tuple[HierarchyCorrectionConfig, str]:
    """Load reviewed JSON config and return its exact byte checksum."""
    raw = path.read_bytes()
    return HierarchyCorrectionConfig.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
