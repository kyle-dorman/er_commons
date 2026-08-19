"""Fast immutable lookup and explicit deep audit for hierarchy candidates."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from er_commons.hierarchy_inference.candidate_records import validate_reuse_metadata
from er_commons.hierarchy_inference.candidate_storage import ManagedFile, stream_file
from er_commons.hierarchy_inference.constants import MANAGED_PAYLOAD_PATHS
from er_commons.hierarchy_inference.digests import canonical_json_sha256
from er_commons.hierarchy_inference.progress import CandidatePhase, ProgressSnapshot
from er_commons.hierarchy_inference.publication_authorization import (
    SEMANTIC_PATHS,
    VerifiedMachinePublication,
    VerifiedPublicationAuthorization,
    _machine_authorization_from_verified_seal,
    candidate_semantic_sha256_from_inventory,
    is_verified_publication_authorization,
)
from er_commons.hierarchy_inference.record_schema import HierarchyRecordValidators

ProgressCallback = Callable[[ProgressSnapshot], None]


@dataclass(frozen=True)
class HierarchyAuditResult:
    """Human-usable facts from one exact full-byte candidate audit."""

    candidate_id: str
    completion_path: Path
    verified_file_count: int
    verified_bytes: int
    elapsed_seconds: float
    candidate_semantic_sha256: str
    artifact_inventory_sha256: str


def verify_completed_candidate(root: Path, candidate_id: str, schema_path: Path) -> Path:
    """Verify a completion-sealed candidate without rereading large semantic files."""
    completion_path = root / "records/completion_record.json"
    inventory_path = root / "records/artifact_inventory.json"
    if not completion_path.is_file() or not inventory_path.is_file():
        raise ValueError("candidate terminal records are missing")
    completion = json.loads(completion_path.read_text())
    inventory = json.loads(inventory_path.read_text())
    if completion.get("candidate_id") != candidate_id:
        raise ValueError("candidate completion identity differs")
    if completion.get("artifact_inventory_sha256") != canonical_json_sha256(inventory):
        raise ValueError("candidate completion inventory seal differs")
    expected_paths = list(MANAGED_PAYLOAD_PATHS)
    if [item.get("path") for item in inventory.get("files", [])] != expected_paths:
        raise ValueError("candidate inventory paths differ")
    managed_files: list[ManagedFile] = []
    for item in inventory["files"]:
        relative_path = Path(item["path"])
        path = root / relative_path
        if not path.is_file():
            raise ValueError(f"candidate inventory file is missing: {relative_path}")
        if path.stat().st_size != item["byte_size"]:
            raise ValueError(f"candidate inventory size differs: {relative_path}")
        managed_files.append(ManagedFile(item["path"], item["byte_size"], item["sha256"]))
    actual_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    expected_files = set(expected_paths) | {
        "records/artifact_inventory.json",
        "records/completion_record.json",
    }
    if actual_files != expected_files:
        raise ValueError("candidate managed file set differs")
    inventory_by_path = {item["path"]: item for item in inventory["files"]}
    for relative_name in expected_paths:
        if relative_name in SEMANTIC_PATHS:
            continue
        observed = stream_file(root / relative_name, relative_name)
        expected = inventory_by_path[relative_name]
        if observed.byte_size != expected["byte_size"] or observed.sha256 != expected["sha256"]:
            raise ValueError(f"candidate inventory checksum differs: {relative_name}")
    identity = json.loads((root / "records/identity.json").read_text())
    input_inventory = json.loads((root / "records/input_inventory.json").read_text())
    environment = json.loads((root / "records/environment.json").read_text())
    summary = json.loads((root / "records/summary.json").read_text())
    metrics = json.loads((root / "records/metrics.json").read_text())
    if identity.get("candidate_id") != candidate_id:
        raise ValueError("candidate identity differs")
    validate_reuse_metadata(
        identity=identity,
        input_inventory=input_inventory,
        environment=environment,
        summary=summary,
        metrics=metrics,
        inventory=inventory,
        completion=completion,
        managed_files=managed_files,
        validators=HierarchyRecordValidators.load(schema_path),
    )
    return completion_path


def deep_audit_completed_candidate(
    root: Path,
    candidate_id: str,
    schema_path: Path,
    *,
    progress: ProgressCallback | None = None,
) -> HierarchyAuditResult:
    """Stream-hash every managed byte and return exact audit measurements."""
    started = time.perf_counter()
    completion = verify_completed_candidate(root, candidate_id, schema_path)
    inventory = json.loads((root / "records/artifact_inventory.json").read_text())
    total_bytes = sum(item["byte_size"] for item in inventory["files"])
    processed_bytes = 0
    if progress is not None:
        progress(ProgressSnapshot(CandidatePhase.DEEP_AUDIT, 0, total_bytes, "bytes"))
    for item in inventory["files"]:

        def report_file_bytes(file_bytes: int, base_bytes: int = processed_bytes) -> None:
            if progress is not None:
                progress(
                    ProgressSnapshot(
                        CandidatePhase.DEEP_AUDIT,
                        base_bytes + file_bytes,
                        total_bytes,
                        "bytes",
                    )
                )

        observed = stream_file(
            root / item["path"],
            item["path"],
            progress=report_file_bytes,
        )
        if observed.byte_size != item["byte_size"] or observed.sha256 != item["sha256"]:
            raise ValueError(f"candidate inventory checksum differs: {item['path']}")
        processed_bytes += observed.byte_size
    return HierarchyAuditResult(
        candidate_id=candidate_id,
        completion_path=completion,
        verified_file_count=len(inventory["files"]),
        verified_bytes=processed_bytes,
        elapsed_seconds=time.perf_counter() - started,
        candidate_semantic_sha256=candidate_semantic_sha256_from_inventory(inventory),
        artifact_inventory_sha256=canonical_json_sha256(inventory),
    )


def machine_authorization_for_verified_candidate(
    root: Path,
    candidate_id: str,
    schema_path: Path,
) -> VerifiedMachinePublication:
    """Mint machine publication authority only after the sealed candidate verifies."""
    verify_completed_candidate(root, candidate_id, schema_path)
    inventory = json.loads((root / "records/artifact_inventory.json").read_text())
    return _machine_authorization_from_verified_seal(
        candidate_id,
        candidate_semantic_sha256_from_inventory(inventory),
    )


def reuse_completed_candidate(
    root: Path,
    candidate_id: str,
    schema_path: Path,
    authorization: VerifiedPublicationAuthorization,
) -> Path:
    """Reuse after immutable-publication metadata and external acceptance verify."""
    if not is_verified_publication_authorization(authorization):
        raise TypeError("publication authorization was not produced by a verified lifecycle")
    if authorization.candidate_id != candidate_id:
        raise ValueError("publication authorization candidate differs from reuse")
    completion = verify_completed_candidate(root, candidate_id, schema_path)
    inventory = json.loads((root / "records/artifact_inventory.json").read_text())
    if authorization.candidate_semantic_sha256 != candidate_semantic_sha256_from_inventory(
        inventory
    ):
        raise ValueError("publication authorization semantic differs from reuse")
    return completion
