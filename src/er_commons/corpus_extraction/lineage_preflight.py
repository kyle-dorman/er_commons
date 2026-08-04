"""Build and verify a checksummed parent-to-worker execution snapshot."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.corpus_extraction.config import RunSpec
from er_commons.corpus_extraction.identity import canonical_digest
from er_commons.corpus_extraction.lineage_validation import validate_lineage_bindings
from er_commons.corpus_extraction.owner_inputs import OwnerConfigs, prepare_owner_configs
from er_commons.corpus_extraction.records import STAGE_COMPLETION_ROLE_SET, ArtifactRef
from er_commons.document_extraction.complete_document import prepare_producer
from er_commons.document_extraction.producer_config import load_producer_config
from er_commons.document_extraction.producer_services import ProducerServices
from er_commons.source_freeze import sha256_file


class SnapshotModel(BaseModel):
    """Closed immutable base for a parent-to-worker preflight record."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ProducerLineage(SnapshotModel):
    """Code-bound producer IDs available without converting the source PDF."""

    baseline: str = Field(pattern=r"^prv1-[0-9a-f]{64}$")
    hierarchy: str = Field(pattern=r"^prv1-[0-9a-f]{64}$")


class ExecutionPreflight(SnapshotModel):
    """Checksummed snapshot of every config admitted by the parent process."""

    schema_version: Literal["er_commons.execution_preflight.v1"] = (
        "er_commons.execution_preflight.v1"
    )
    run_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str
    config_refs: dict[str, ArtifactRef]
    producer_lineage: ProducerLineage
    authorization_ref: ArtifactRef | None
    final_artifact_relative_root: Path

    @model_validator(mode="after")
    def require_all_owner_configs(self) -> ExecutionPreflight:
        """Keep the config snapshot aligned with the six-owner handoff."""
        if set(self.config_refs) != STAGE_COMPLETION_ROLE_SET:
            raise ValueError("execution preflight must seal exactly six owner configs")
        if self.final_artifact_relative_root.is_absolute() or (
            ".." in self.final_artifact_relative_root.parts
        ):
            raise ValueError("final owner artifact root must be contained")
        return self

    @property
    def digest(self) -> str:
        """Return the canonical checksum passed separately to the worker."""
        return canonical_digest(self.model_dump(mode="json"))


def build_execution_preflight(
    *,
    data_root: Path,
    project_root: Path,
    run_spec: RunSpec,
    run_spec_sha256: str,
    source_id: str,
) -> ExecutionPreflight:
    """Validate execution-only inputs and build a sealed worker snapshot."""
    configs = prepare_owner_configs(
        project_root=project_root,
        data_root=data_root,
        run_spec=run_spec,
        source_id=source_id,
    )
    lineage = _derive_producer_lineage(data_root, configs)
    final_relative_root, authorization_ref = validate_lineage_bindings(
        configs=configs,
        source_id=source_id,
        disposition=run_spec.hierarchy_disposition(source_id),
        lineage=lineage,
        data_root=data_root,
        project_root=project_root,
    )
    return ExecutionPreflight(
        run_spec_sha256=run_spec_sha256,
        source_id=source_id,
        config_refs=_config_refs(configs, project_root),
        producer_lineage=lineage,
        authorization_ref=authorization_ref,
        final_artifact_relative_root=final_relative_root,
    )


def verify_execution_preflight(
    *,
    snapshot: ExecutionPreflight,
    expected_digest: str,
    data_root: Path,
    project_root: Path,
    run_spec: RunSpec,
    run_spec_sha256: str,
    source_id: str,
) -> OwnerConfigs:
    """Verify parent-admitted bytes in the child and return those exact configs."""
    if snapshot.digest != expected_digest:
        raise ValueError("execution preflight snapshot checksum differs")
    if snapshot.run_spec_sha256 != run_spec_sha256 or snapshot.source_id != source_id:
        raise ValueError("execution preflight run spec or source differs")
    configs = prepare_owner_configs(
        project_root=project_root,
        data_root=data_root,
        run_spec=run_spec,
        source_id=source_id,
    )
    if _config_refs(configs, project_root) != snapshot.config_refs:
        raise ValueError("content-owner configs changed after parent preflight")
    authorization = snapshot.authorization_ref
    if authorization is not None:
        path = (data_root / authorization.path).resolve()
        if (
            not path.is_relative_to(data_root.resolve())
            or not path.is_file()
            or sha256_file(path) != authorization.sha256
        ):
            raise ValueError("bounded authorization changed after parent preflight")
    final_root, _authorization = validate_lineage_bindings(
        configs=configs,
        source_id=source_id,
        disposition=run_spec.hierarchy_disposition(source_id),
        lineage=snapshot.producer_lineage,
        data_root=data_root,
        project_root=project_root,
    )
    if final_root != snapshot.final_artifact_relative_root:
        raise ValueError("final owner artifact root changed after parent preflight")
    return configs


def _derive_producer_lineage(data_root: Path, configs: OwnerConfigs) -> ProducerLineage:
    """Construct effective runtimes and derive both producer identities only."""
    services = ProducerServices()

    def derive(path: Path) -> str:
        config, digest = load_producer_config(path)
        return prepare_producer(
            data_root,
            config=config,
            config_sha256=digest,
            services=services,
        ).identity.run_id

    return ProducerLineage(
        baseline=derive(configs.baseline_producer),
        hierarchy=derive(configs.hierarchy_producer),
    )


def _config_refs(configs: OwnerConfigs, project_root: Path) -> dict[str, ArtifactRef]:
    """Checksum the exact six config bytes admitted for execution."""
    return {
        role: ArtifactRef(
            path=path.relative_to(project_root).as_posix(),
            sha256=sha256_file(path),
        )
        for role, path in configs.as_dict().items()
    }


__all__ = [
    "ExecutionPreflight",
    "ProducerLineage",
    "build_execution_preflight",
    "validate_lineage_bindings",
    "verify_execution_preflight",
]
