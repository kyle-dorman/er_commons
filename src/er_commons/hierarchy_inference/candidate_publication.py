"""Failure-safe streaming publication for hierarchy candidates."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.hierarchy_inference import candidate_storage as storage
from er_commons.hierarchy_inference.candidate_records import (
    JSONL_PATHS,
    CandidatePayload,
    SemanticBuildMeasurements,
    build_attempt_record,
    build_metrics,
    validate_attempt_record,
    validate_semantic_payload,
    validate_terminal_records,
)
from er_commons.hierarchy_inference.constants import MANAGED_PAYLOAD_PATHS
from er_commons.hierarchy_inference.digests import canonical_json_sha256
from er_commons.hierarchy_inference.failures import RunStage
from er_commons.hierarchy_inference.progress import CandidatePhase, ProgressSnapshot
from er_commons.hierarchy_inference.publication_authorization import (
    VerifiedMachinePublication,
    VerifiedPublicationAuthorization,
    _machine_authorization_from_verified_seal,
    candidate_semantic_sha256_from_inventory,
    is_verified_publication_authorization,
)
from er_commons.hierarchy_inference.record_schema import HierarchyRecordValidators

ProgressCallback = Callable[[ProgressSnapshot], None]


@dataclass(frozen=True)
class CandidateWorkspace:
    """One isolated staging directory and deterministic final destination."""

    staging_root: Path
    final_root: Path


@dataclass(frozen=True)
class CandidateSeal:
    """Completion path plus exact write order for auditable sealing tests."""

    completion_path: Path
    written_paths: tuple[str, ...]
    machine_authorization: VerifiedMachinePublication


@dataclass(frozen=True)
class StreamedSemanticRecords:
    """Semantic files written before the acyclic terminal record tail."""

    records: dict[str, Any]
    managed_files: tuple[storage.ManagedFile, ...]
    written_paths: tuple[str, ...]


@dataclass(frozen=True)
class TerminalRecords:
    """Validated metrics and seal records ready for completion-last writes."""

    inventory: dict[str, Any]
    completion: dict[str, Any]
    written_paths: tuple[str, ...]


def reserve_workspace(task_root: Path, candidate_id: str, token: str) -> CandidateWorkspace:
    """Reserve a private `.tmp` staging tree without reusing existing bytes."""
    if not token or Path(token).name != token or not candidate_id.startswith("hcorv1-"):
        raise ValueError("candidate workspace components must be contained names")
    task_root.mkdir(parents=True, exist_ok=True)
    staging_root = task_root / ".tmp" / f"{candidate_id}.{token}"
    staging_root.mkdir(parents=True, exist_ok=False)
    return CandidateWorkspace(staging_root=staging_root, final_root=task_root / candidate_id)


def write_validate_and_seal_candidate(
    *,
    workspace: CandidateWorkspace,
    payload: CandidatePayload,
    measurements: SemanticBuildMeasurements,
    schema_path: Path,
    progress: ProgressCallback | None = None,
) -> CandidateSeal:
    """Validate resident semantics, stream managed files, and write completion last."""
    if workspace.final_root.exists():
        raise FileExistsError(f"candidate destination already exists: {workspace.final_root}")
    validators = HierarchyRecordValidators.load(schema_path)
    records = validate_semantic_payload(
        payload=payload,
        validators=validators,
        progress=progress,
    )
    semantic = _stream_semantic_records(workspace, records, progress)
    terminal = _build_and_validate_terminal_records(
        workspace=workspace,
        payload=payload,
        measurements=measurements,
        semantic=semantic,
        validators=validators,
        progress=progress,
    )
    return _seal_terminal_records(workspace, terminal, progress)


def _stream_semantic_records(
    workspace: CandidateWorkspace,
    records: dict[str, Any],
    progress: ProgressCallback | None,
) -> StreamedSemanticRecords:
    """Stream every preterminal semantic record in the frozen managed order."""
    path_values: dict[str, Any] = {
        "records/identity.json": records["identity"],
        "records/input_inventory.json": records["input_inventory"],
        "records/environment.json": records["environment"],
        "artifacts/item_features.jsonl": records["features"],
        "artifacts/visible_toc_entries.jsonl": records["toc_entries"],
        "artifacts/toc_reconciliation.jsonl": records["reconciliations"],
        "artifacts/regimes.jsonl": records["regimes"],
        "artifacts/decisions.jsonl": records["decisions"],
        "artifacts/hierarchy.json": records["hierarchy"],
        "artifacts/ambiguities.jsonl": records["ambiguities"],
        "artifacts/warnings.jsonl": records["warnings"],
        "records/summary.json": records["summary"],
    }
    written_paths: list[str] = []
    managed_files: list[storage.ManagedFile] = []
    total_stream_units = sum(
        len(path_values[relative]) if relative in JSONL_PATHS else 1
        for relative in MANAGED_PAYLOAD_PATHS
        if relative != "records/metrics.json"
    )
    streamed_units = 0
    if progress is not None:
        progress(
            ProgressSnapshot(
                CandidatePhase.STREAMING_PUBLICATION,
                streamed_units,
                total_stream_units,
                "records",
            )
        )
    for relative in MANAGED_PAYLOAD_PATHS:
        if relative == "records/metrics.json":
            continue
        value = path_values[relative]

        def record_progress(file_units: int, base_units: int = streamed_units) -> None:
            if progress is not None:
                progress(
                    ProgressSnapshot(
                        CandidatePhase.STREAMING_PUBLICATION,
                        base_units + file_units,
                        total_stream_units,
                        "records",
                    )
                )

        managed_file = (
            storage.write_jsonl(workspace.staging_root, relative, value, record_progress)
            if relative in JSONL_PATHS
            else storage.write_json(workspace.staging_root, relative, value)
        )
        streamed_units += len(value) if relative in JSONL_PATHS else 1
        if progress is not None:
            progress(
                ProgressSnapshot(
                    CandidatePhase.STREAMING_PUBLICATION,
                    streamed_units,
                    total_stream_units,
                    "records",
                )
            )
        managed_files.append(managed_file)
        written_paths.append(relative)
    return StreamedSemanticRecords(records, tuple(managed_files), tuple(written_paths))


def _build_and_validate_terminal_records(
    *,
    workspace: CandidateWorkspace,
    payload: CandidatePayload,
    measurements: SemanticBuildMeasurements,
    semantic: StreamedSemanticRecords,
    validators: HierarchyRecordValidators,
    progress: ProgressCallback | None,
) -> TerminalRecords:
    """Build, write, and validate the acyclic metrics/inventory/completion tail."""
    managed_files = list(semantic.managed_files)
    metrics = build_metrics(
        candidate_id=payload.identity["candidate_id"],
        measurements=measurements,
        payload_bytes=sum(item.byte_size for item in managed_files),
    )
    metrics_file = storage.write_json(workspace.staging_root, "records/metrics.json", metrics)
    managed_files.append(metrics_file)
    written_paths = (*semantic.written_paths, "records/metrics.json")
    inventory: dict[str, Any] = {"files": [item.as_record() for item in managed_files]}
    completion: dict[str, Any] = {
        "candidate_id": payload.identity["candidate_id"],
        "status": semantic.records["summary"]["status"],
        "artifact_inventory_sha256": canonical_json_sha256(inventory),
    }
    if progress is not None:
        progress(ProgressSnapshot(CandidatePhase.TERMINAL_VALIDATION, 0, 1, "checks"))
    validate_terminal_records(
        identity=semantic.records["identity"],
        summary=semantic.records["summary"],
        metrics=metrics,
        inventory=inventory,
        completion=completion,
        managed_files=managed_files,
        validators=validators,
    )
    if progress is not None:
        progress(ProgressSnapshot(CandidatePhase.TERMINAL_VALIDATION, 1, 1, "checks"))
    return TerminalRecords(inventory, completion, written_paths)


def _seal_terminal_records(
    workspace: CandidateWorkspace,
    terminal: TerminalRecords,
    progress: ProgressCallback | None,
) -> CandidateSeal:
    """Write inventory, fsync payloads, and create completion strictly last."""
    inventory_relative = "records/artifact_inventory.json"
    if progress is not None:
        progress(ProgressSnapshot(CandidatePhase.INVENTORY_SEAL, 0, 1, "files"))
    storage.write_json(workspace.staging_root, inventory_relative, terminal.inventory)
    written_paths = (*terminal.written_paths, inventory_relative)
    storage.fsync_directory(workspace.staging_root / "artifacts")
    storage.fsync_directory(workspace.staging_root / "records")
    storage.fsync_directory(workspace.staging_root)
    if progress is not None:
        progress(ProgressSnapshot(CandidatePhase.INVENTORY_SEAL, 1, 1, "files"))
    completion_relative = "records/completion_record.json"
    if progress is not None:
        progress(ProgressSnapshot(CandidatePhase.COMPLETION_SEAL, 0, 1, "files"))
    storage.write_json(workspace.staging_root, completion_relative, terminal.completion)
    storage.fsync_directory(workspace.staging_root / "records")
    storage.fsync_directory(workspace.staging_root)
    written_paths = (*written_paths, completion_relative)
    if progress is not None:
        progress(ProgressSnapshot(CandidatePhase.COMPLETION_SEAL, 1, 1, "files"))
    return CandidateSeal(
        completion_path=workspace.staging_root / completion_relative,
        written_paths=written_paths,
        machine_authorization=_machine_authorization_from_verified_seal(
            terminal.completion["candidate_id"],
            candidate_semantic_sha256_from_inventory(terminal.inventory),
        ),
    )


def retain_failed_attempt(
    *,
    workspace: CandidateWorkspace,
    candidate_id: str,
    fatal_code: str,
    detail: str,
    schema_path: Path,
    stage: RunStage | None = None,
    progress_snapshot: ProgressSnapshot | None = None,
) -> Path:
    """Retain one schema-valid failure, retracting a premature completion."""
    completion = workspace.staging_root / "records/completion_record.json"
    if completion.exists():
        completion.unlink()
        storage.fsync_directory(completion.parent)
    record = build_attempt_record(
        candidate_id=candidate_id,
        fatal_code=fatal_code,
        detail=detail,
        stage=stage.value if stage is not None else None,
        progress_snapshot=progress_snapshot,
    )
    validate_attempt_record(record, HierarchyRecordValidators.load(schema_path))
    path = workspace.staging_root / "records/attempt_record.json"
    storage.write_bytes(path, storage.stable_json_bytes(record))
    storage.fsync_directory(path.parent)
    storage.fsync_directory(workspace.staging_root)
    return path


def publish_workspace(
    workspace: CandidateWorkspace,
    authorization: VerifiedPublicationAuthorization,
) -> Path:
    """Publish only a completed staging tree with verified external acceptance."""
    completion = workspace.staging_root / "records/completion_record.json"
    if not completion.is_file():
        raise ValueError("candidate staging tree has no completion record")
    if not is_verified_publication_authorization(authorization):
        raise TypeError("publication authorization was not produced by a verified lifecycle")
    candidate_id = workspace.final_root.name
    if authorization.candidate_id != candidate_id:
        raise ValueError("publication authorization candidate differs")
    inventory = json.loads((workspace.staging_root / "records/artifact_inventory.json").read_text())
    if authorization.candidate_semantic_sha256 != candidate_semantic_sha256_from_inventory(
        inventory
    ):
        raise ValueError("publication authorization semantic differs")
    if workspace.final_root.exists():
        raise FileExistsError(f"candidate destination already exists: {workspace.final_root}")
    source_parent = workspace.staging_root.parent
    workspace.staging_root.rename(workspace.final_root)
    storage.fsync_directory(source_parent)
    storage.fsync_directory(workspace.final_root.parent)
    return workspace.final_root / "records/completion_record.json"


def preserve_failed_workspace(workspace: CandidateWorkspace, attempts_root: Path) -> Path:
    """Move an incomplete attempt from opaque staging to a stable attempts path."""
    attempt = workspace.staging_root / "records/attempt_record.json"
    completion = workspace.staging_root / "records/completion_record.json"
    if not attempt.is_file() or completion.exists():
        raise ValueError("failed workspace must contain attempt evidence without completion")
    attempts_root.mkdir(parents=True, exist_ok=True)
    storage.fsync_directory(attempts_root.parent)
    destination = attempts_root / workspace.staging_root.name
    if destination.exists():
        raise FileExistsError(f"attempt destination already exists: {destination}")
    source_parent = workspace.staging_root.parent
    workspace.staging_root.rename(destination)
    storage.fsync_directory(source_parent)
    storage.fsync_directory(attempts_root)
    return destination / "records/attempt_record.json"
