"""Strict configuration for the Task 03D Appendix P canonicalization pilot."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ACCEPTED_PRODUCER_RUN_ID = "prv1-93dfb03242a3651b90ee5424f36b7f6c58b5ac814dd48e1495b6359cdc6e92e0"
APPENDIX_P_SOURCE_ID = "deir_appendix_p"
APPENDIX_P_SOURCE_SHA256 = "2dfceac46931a946bc343d52b09104b7b58ed8831bc4f49a03f0b8655e4e6ea1"
APPENDIX_P_PAGE_COUNT = 222


class StrictConfigModel(BaseModel):
    """Reject unreviewed configuration fields and in-place mutation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class MaterializedDocument(StrictConfigModel):
    """One ordered source document selected from the full sealed release."""

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    pdf_page_count: int = Field(gt=0)


class CanonicalizationConfig(StrictConfigModel):
    """Reviewed identity and artifact paths for the one-document pilot."""

    schema_version: Literal["1.0.0"]
    canonicalization_policy_version: Literal["task03d-v1"]
    mapping_policy_version: Literal["task03d-appendix-p-mapping-v1"]
    candidate_version_name: Literal["appendix_p_core_candidate_v1"]
    candidate_scope: Literal["document_scoped_non_release"]
    source_release_version: Literal["brisbane_baylands_2025_deir_sources_v1"]
    source_manifest_relative_path: Path
    ordered_materialization_scope: tuple[MaterializedDocument, ...] = Field(
        min_length=1,
        max_length=1,
    )
    producer_artifact_relative_root: Path
    producer_run_id: Literal[
        "prv1-93dfb03242a3651b90ee5424f36b7f6c58b5ac814dd48e1495b6359cdc6e92e0"
    ]
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
    def validate_task_scope(self) -> CanonicalizationConfig:
        """Keep paths contained and freeze the approved Appendix P selection."""
        for path in (
            self.source_manifest_relative_path,
            self.producer_artifact_relative_root,
            self.artifact_relative_root,
        ):
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("canonicalization paths must be contained relative paths")

        selected = self.ordered_materialization_scope[0]
        expected = (
            selected.source_id == APPENDIX_P_SOURCE_ID
            and selected.source_sha256 == APPENDIX_P_SOURCE_SHA256
            and selected.pdf_page_count == APPENDIX_P_PAGE_COUNT
        )
        if not expected:
            raise ValueError("Task 03D materialization scope must be the approved Appendix P")
        if self.producer_run_id != ACCEPTED_PRODUCER_RUN_ID:
            raise ValueError("Task 03D must consume the accepted Task 03C.1 producer run")
        return self


def load_canonicalization_config(path: Path) -> tuple[CanonicalizationConfig, str]:
    """Load the reviewed JSON config and return its exact byte checksum."""
    raw = path.read_bytes()
    return CanonicalizationConfig.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
