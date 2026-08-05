"""Strict configuration for one restartable document transaction."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    """Reject undeclared fields and mutation after validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ResourcePolicy(StrictModel):
    """Bound process, batching, accelerator, and retry resources."""

    document_concurrency: int = Field(ge=1, le=4)
    page_batch_size: int = Field(ge=1, le=32)
    stage_batch_size: int = Field(ge=1, le=32)
    queue_capacity: int = Field(ge=1, le=256)
    cpu_threads_per_document: int = Field(ge=1, le=16)
    device: Literal["cpu", "mps", "cuda", "auto"]
    memory_estimate_bytes: int = Field(gt=0)
    storage_estimate_bytes: int = Field(gt=0)
    docling_timeout_seconds: float | None = Field(default=None, gt=0)
    outer_process_deadline_seconds: float | None = Field(default=None, gt=0)
    cancellation_grace_seconds: float = Field(gt=0, le=60)
    retry_limit: int = Field(ge=0, le=5)

    @model_validator(mode="after")
    def validate_deadlines(self) -> ResourcePolicy:
        """Keep the hard deadline outside the cooperative timeout."""
        if (
            self.docling_timeout_seconds is not None
            and self.outer_process_deadline_seconds is not None
            and self.outer_process_deadline_seconds <= self.docling_timeout_seconds
        ):
            raise ValueError("outer process deadline must exceed Docling timeout")
        return self


class ContentOwnerConfigs(StrictModel):
    """Explicit reviewed configurations for the existing content-policy owners."""

    baseline_producer: Path
    hierarchy_producer: Path
    canonical: Path
    hierarchy_correction: Path
    semantic: Path
    cross_references: Path

    @model_validator(mode="after")
    def validate_paths(self) -> ContentOwnerConfigs:
        """Require contained repository-relative configuration paths."""
        for value in self.__class__.model_fields:
            path = getattr(self, value)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("content-owner configs must be contained relative paths")
        return self


class DocumentOwnerSelection(StrictModel):
    """Data-driven owner configurations for one manifest source."""

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    lineage_mode: Literal["sealed_inputs", "fresh_build"] = "sealed_inputs"
    configs: ContentOwnerConfigs


class HierarchyDisposition(StrictModel):
    """Document-specific authority; Appendix P acceptance cannot propagate."""

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    authority: Literal["machine_validation", "bounded_acceptance"]
    authorization_relative_path: Path | None = None

    @model_validator(mode="after")
    def validate_authority(self) -> HierarchyDisposition:
        """Require explicit evidence for bounded acceptance."""
        path = self.authorization_relative_path
        if self.authority == "bounded_acceptance" and path is None:
            raise ValueError("bounded hierarchy acceptance requires authorization evidence")
        if self.authority == "machine_validation" and path is not None:
            raise ValueError("machine hierarchy authority cannot cite bounded acceptance")
        if path is not None and (path.is_absolute() or ".." in path.parts):
            raise ValueError("hierarchy authorization path must be contained")
        return self


class RunSpec(StrictModel):
    """One explicit manifest-selected stage-one execution scope."""

    schema_version: Literal["er_commons.document_run_spec.v1"]
    production_extraction_id: str = Field(pattern=r"^exv1-[0-9a-f]{64}$")
    production_identity_relative_path: Path
    scope_kind: Literal["fixture", "engineering_smoke", "representative_pilot", "production_full"]
    source_release_version: str
    source_manifest_relative_path: Path
    artifact_relative_root: Path
    document_owners: tuple[DocumentOwnerSelection, ...]
    hierarchy_dispositions: tuple[HierarchyDisposition, ...]
    resource_policy: ResourcePolicy

    @property
    def source_manifest_path(self) -> Path:
        """Expose the sealed-release selection interface."""
        return self.source_manifest_relative_path

    @model_validator(mode="after")
    def validate_paths_and_dispositions(self) -> RunSpec:
        """Keep outputs contained and hierarchy authority unambiguous."""
        for path in (
            self.production_identity_relative_path,
            self.source_manifest_relative_path,
            self.artifact_relative_root,
        ):
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("run-spec paths must be contained relative paths")
        ids = [item.source_id for item in self.hierarchy_dispositions]
        owner_ids = [item.source_id for item in self.document_owners]
        if len(ids) != len(set(ids)) or len(owner_ids) != len(set(owner_ids)):
            raise ValueError("hierarchy dispositions contain duplicate source IDs")
        if set(ids) != set(owner_ids):
            raise ValueError("document owners and hierarchy dispositions select different sources")
        return self

    def hierarchy_disposition(self, source_id: str) -> HierarchyDisposition:
        """Return the one explicit document-specific hierarchy authority."""
        matches = [item for item in self.hierarchy_dispositions if item.source_id == source_id]
        if len(matches) != 1:
            raise ValueError(f"run spec lacks one hierarchy disposition: {source_id}")
        return matches[0]

    def content_owners(self, source_id: str) -> ContentOwnerConfigs:
        """Return the explicit owner configuration set for one source."""
        matches = [item.configs for item in self.document_owners if item.source_id == source_id]
        if len(matches) != 1:
            raise ValueError(f"run spec lacks one content-owner selection: {source_id}")
        return matches[0]

    def lineage_mode(self, source_id: str) -> Literal["sealed_inputs", "fresh_build"]:
        """Return the explicit upstream-binding policy for one source."""
        matches = [
            item.lineage_mode for item in self.document_owners if item.source_id == source_id
        ]
        if len(matches) != 1:
            raise ValueError(f"run spec lacks one lineage mode: {source_id}")
        return matches[0]


def load_run_spec(path: Path) -> tuple[RunSpec, str]:
    """Load a run specification and return its exact checksum."""
    raw = path.read_bytes()
    return RunSpec.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
