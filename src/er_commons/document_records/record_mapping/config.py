"""Strict document-scoped record-mapping configuration."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictConfigModel(BaseModel):
    """Reject unreviewed configuration fields and in-place mutation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class MaterializedDocument(StrictConfigModel):
    """One ordered source document selected from the full sealed release."""

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    pdf_page_count: int = Field(gt=0)


class RecordMappingConfig(StrictConfigModel):
    """Reviewed identity and artifact paths for the one-document pilot."""

    schema_version: Literal["1.0.0"]
    canonicalization_policy_version: str = Field(min_length=1)
    mapping_policy_version: str = Field(min_length=1)
    mapping_policy_relative_path: Path = Path("docs/specs/task03d_appendix_p_mapping_v1.md")
    candidate_version_name: str = Field(min_length=1)
    candidate_scope: Literal["document_scoped_non_release"]
    acceptance_profile: Literal["generic_complete_document"] = "generic_complete_document"
    source_release_version: str = Field(min_length=1)
    source_manifest_relative_path: Path
    ordered_materialization_scope: tuple[MaterializedDocument, ...] = Field(
        min_length=1,
        max_length=1,
    )
    producer_artifact_relative_root: Path
    producer_run_id: str = Field(pattern=r"^prv1-[0-9a-f]{64}$")
    artifact_relative_root: Path

    @property
    def source_manifest_path(self) -> Path:
        """Expose the relative sealed-manifest path expected by release verification."""
        return self.source_manifest_relative_path

    @property
    def selected_source_id(self) -> str:
        """Return the sole source selected by this document-scoped task."""
        return self.ordered_materialization_scope[0].source_id

    @model_validator(mode="after")
    def validate_task_scope(self) -> RecordMappingConfig:
        """Keep every configured artifact path contained."""
        for path in (
            self.source_manifest_relative_path,
            self.mapping_policy_relative_path,
            self.producer_artifact_relative_root,
            self.artifact_relative_root,
        ):
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("record-mapping paths must be contained relative paths")

        return self


def load_record_mapping_config(path: Path) -> tuple[RecordMappingConfig, str]:
    """Load the reviewed JSON config and return its exact byte checksum."""
    raw = path.read_bytes()
    return RecordMappingConfig.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
