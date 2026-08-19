"""Build and verify a checksummed parent-to-worker execution snapshot."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.artifact_io import sha256_file
from er_commons.document_parsing.content_parsing.application import prepare_content_parsing
from er_commons.document_parsing.content_parsing.config import load_content_parsing_config
from er_commons.document_publication.config import DocumentRunSpec
from er_commons.document_publication.fresh_preflight import is_fresh_document_root
from er_commons.document_publication.identity import canonical_digest
from er_commons.document_publication.lineage_validation import validate_lineage_bindings
from er_commons.document_publication.process_inputs import ProcessConfigs, prepare_process_configs
from er_commons.document_publication.published_document import ProducerLineage
from er_commons.document_publication.records import DOCUMENT_PROCESS_NAME_SET, ArtifactRef


class SnapshotModel(BaseModel):
    """Closed immutable base for a parent-to-worker preflight record."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ExecutionPreflight(SnapshotModel):
    """Checksummed snapshot of every config admitted by the parent process."""

    schema_version: Literal["er_commons.execution_preflight.v1"] = (
        "er_commons.execution_preflight.v1"
    )
    run_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str
    lineage_mode: Literal["sealed_inputs", "fresh_build"]
    config_refs: dict[str, ArtifactRef]
    producer_lineage: ProducerLineage
    authorization_ref: ArtifactRef | None
    final_artifact_relative_root: Path

    @model_validator(mode="after")
    def require_all_process_configs(self) -> ExecutionPreflight:
        """Keep the config snapshot aligned with the six-process handoff."""
        if set(self.config_refs) != DOCUMENT_PROCESS_NAME_SET:
            raise ValueError("execution preflight must seal exactly six process configs")
        if self.final_artifact_relative_root.is_absolute() or (
            ".." in self.final_artifact_relative_root.parts
        ):
            raise ValueError("final document-product root must be contained")
        return self

    @property
    def digest(self) -> str:
        """Return the record_mapping checksum passed separately to the worker."""
        return canonical_digest(self.model_dump(mode="json"))


def build_execution_preflight(
    *,
    data_root: Path,
    project_root: Path,
    run_spec: DocumentRunSpec,
    run_spec_sha256: str,
    source_id: str,
) -> ExecutionPreflight:
    """Validate execution-only inputs and build a sealed worker snapshot."""
    configs = prepare_process_configs(
        project_root=project_root,
        data_root=data_root,
        run_spec=run_spec,
        source_id=source_id,
    )
    lineage = _derive_producer_lineage(data_root, configs)
    lineage_mode = run_spec.lineage_mode(source_id)
    if lineage_mode == "fresh_build" and not is_fresh_document_root(
        run_spec.artifact_relative_root
    ):
        raise ValueError("fresh document artifact root must use a task_03g2 or task_03h namespace")
    final_relative_root, authorization_ref = validate_lineage_bindings(
        configs=configs,
        source_id=source_id,
        disposition=run_spec.hierarchy_disposition(source_id),
        lineage=lineage,
        data_root=data_root,
        project_root=project_root,
        lineage_mode=lineage_mode,
    )
    return ExecutionPreflight(
        run_spec_sha256=run_spec_sha256,
        source_id=source_id,
        lineage_mode=lineage_mode,
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
    run_spec: DocumentRunSpec,
    run_spec_sha256: str,
    source_id: str,
) -> ProcessConfigs:
    """Verify parent-admitted bytes in the child and return those exact configs."""
    if snapshot.digest != expected_digest:
        raise ValueError("execution preflight snapshot checksum differs")
    if snapshot.run_spec_sha256 != run_spec_sha256 or snapshot.source_id != source_id:
        raise ValueError("execution preflight run spec or source differs")
    if snapshot.lineage_mode != run_spec.lineage_mode(source_id):
        raise ValueError("execution preflight lineage mode differs")
    configs = prepare_process_configs(
        project_root=project_root,
        data_root=data_root,
        run_spec=run_spec,
        source_id=source_id,
    )
    if _config_refs(configs, project_root) != snapshot.config_refs:
        raise ValueError("document-process configs changed after parent preflight")
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
        lineage_mode=snapshot.lineage_mode,
    )
    if final_root != snapshot.final_artifact_relative_root:
        raise ValueError("final document-product root changed after parent preflight")
    return configs


def _derive_producer_lineage(data_root: Path, configs: ProcessConfigs) -> ProducerLineage:
    """Construct effective runtimes and derive both producer identities only."""

    def derive(path: Path) -> str:
        config, digest = load_content_parsing_config(path)
        return prepare_content_parsing(
            data_root,
            config=config,
            config_sha256=digest,
        ).identity.run_id

    return ProducerLineage(
        baseline=derive(configs.content_parsing),
        hierarchy=derive(configs.heading_evidence_parsing),
    )


def _config_refs(configs: ProcessConfigs, project_root: Path) -> dict[str, ArtifactRef]:
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
