"""Read-only models for immutable document-workflow v1 evidence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.corpus_extraction_contract_v1_1 import validate_production_identity
from er_commons.document_publication.config import (
    DocumentProcessConfigs,
    DocumentProcessSelection,
    HierarchyDisposition,
    ResourcePolicy,
)


class _V1Model(BaseModel):
    """Reject unknown legacy fields and prevent accidental mutation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class V1ResourcePolicy(_V1Model):
    """The exact resource-policy shape used by document-run-spec v1."""

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


class V1ContentOwnerConfigs(_V1Model):
    """The six historical process keys, accepted only by this reader."""

    baseline_producer: Path
    hierarchy_producer: Path
    canonical: Path
    hierarchy_correction: Path
    semantic: Path
    cross_references: Path


class V1DocumentOwnerSelection(_V1Model):
    """One historical source/config selection."""

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    lineage_mode: Literal["sealed_inputs", "fresh_build"] = "sealed_inputs"
    configs: V1ContentOwnerConfigs


class V1HierarchyDisposition(_V1Model):
    """Historical per-document hierarchy authority."""

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    authority: Literal["machine_validation", "bounded_acceptance"]
    authorization_relative_path: Path | None = None


class V1DocumentRunSpec(_V1Model):
    """Exact immutable document-run-spec v1 input shape."""

    schema_version: Literal["er_commons.document_run_spec.v1"]
    production_extraction_id: str = Field(pattern=r"^exv1-[0-9a-f]{64}$")
    production_identity_relative_path: Path
    scope_kind: Literal["fixture", "engineering_smoke", "representative_pilot", "production_full"]
    source_release_version: str
    source_manifest_relative_path: Path
    artifact_relative_root: Path
    document_owners: tuple[V1DocumentOwnerSelection, ...]
    hierarchy_dispositions: tuple[V1HierarchyDisposition, ...]
    resource_policy: V1ResourcePolicy

    @model_validator(mode="after")
    def validate_selection(self) -> V1DocumentRunSpec:
        """Reject malformed historical evidence without converting its keys."""
        process_ids = [item.source_id for item in self.document_owners]
        hierarchy_ids = [item.source_id for item in self.hierarchy_dispositions]
        if len(process_ids) != len(set(process_ids)) or len(hierarchy_ids) != len(
            set(hierarchy_ids)
        ):
            raise ValueError("v1 document selections contain duplicate source IDs")
        if set(process_ids) != set(hierarchy_ids):
            raise ValueError("v1 document selections and hierarchy dispositions differ")
        return self

    def hierarchy_disposition(self, source_id: str) -> V1HierarchyDisposition:
        """Return the one historical hierarchy disposition for a source."""
        matches = [item for item in self.hierarchy_dispositions if item.source_id == source_id]
        if len(matches) != 1:
            raise ValueError(f"v1 run spec lacks one hierarchy disposition: {source_id}")
        return matches[0]


def load_document_run_spec_v1(path: Path) -> tuple[V1DocumentRunSpec, str]:
    """Read immutable v1 bytes without adapting them into an executable v2 spec."""
    raw = path.read_bytes()
    return V1DocumentRunSpec.model_validate_json(raw), hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class Task03G2ReadinessSpec:
    """Non-executable projection used only to audit the historical Task 03G.2 inputs."""

    production_extraction_id: str
    production_identity_relative_path: Path
    scope_kind: Literal["fixture", "engineering_smoke", "representative_pilot", "production_full"]
    source_release_version: str
    source_manifest_relative_path: Path
    artifact_relative_root: Path
    document_processes: tuple[DocumentProcessSelection, ...]
    hierarchy_dispositions: tuple[HierarchyDisposition, ...]
    resource_policy: ResourcePolicy

    def hierarchy_disposition(self, source_id: str) -> HierarchyDisposition:
        """Return the historical hierarchy choice for readiness validation only."""
        matches = [item for item in self.hierarchy_dispositions if item.source_id == source_id]
        if len(matches) != 1:
            raise ValueError(f"Task 03G.2 readiness spec lacks one disposition: {source_id}")
        return matches[0]


def build_task03g2_readiness_spec(spec: V1DocumentRunSpec) -> Task03G2ReadinessSpec:
    """Project immutable v1 evidence into the bounded historical readiness DTO."""
    processes = tuple(
        DocumentProcessSelection(
            source_id=selection.source_id,
            lineage_mode=selection.lineage_mode,
            configs=DocumentProcessConfigs(
                content_parsing=selection.configs.baseline_producer,
                heading_evidence_parsing=selection.configs.hierarchy_producer,
                record_mapping=selection.configs.canonical,
                hierarchy_inference=selection.configs.hierarchy_correction,
                document_structure=selection.configs.semantic,
                document_reference_linking=selection.configs.cross_references,
            ),
        )
        for selection in spec.document_owners
    )
    dispositions = tuple(
        HierarchyDisposition.model_validate(item.model_dump(mode="json"))
        for item in spec.hierarchy_dispositions
    )
    return Task03G2ReadinessSpec(
        production_extraction_id=spec.production_extraction_id,
        production_identity_relative_path=spec.production_identity_relative_path,
        scope_kind=spec.scope_kind,
        source_release_version=spec.source_release_version,
        source_manifest_relative_path=spec.source_manifest_relative_path,
        artifact_relative_root=spec.artifact_relative_root,
        document_processes=processes,
        hierarchy_dispositions=dispositions,
        resource_policy=ResourcePolicy.model_validate(spec.resource_policy.model_dump(mode="json")),
    )


__all__ = [
    "V1DocumentRunSpec",
    "Task03G2ReadinessSpec",
    "build_task03g2_readiness_spec",
    "load_document_run_spec_v1",
    "validate_production_identity",
]
