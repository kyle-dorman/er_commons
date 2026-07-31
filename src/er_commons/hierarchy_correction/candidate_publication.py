"""Failure-safe publication and exact reuse for Task 03E.2 candidates."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from er_commons.hierarchy_correction.candidate_records import (
    JSONL_PATHS,
    CandidateMeasurements,
    CandidatePayload,
    PreparedCandidate,
    build_attempt_record,
    prepare_candidate,
    stable_json_bytes,
    validate_attempt_record,
    validate_candidate_bundle,
)
from er_commons.hierarchy_correction.constants import MANAGED_PAYLOAD_PATHS
from er_commons.hierarchy_correction.digests import canonical_json_sha256
from er_commons.hierarchy_correction.quality_gate import (
    VerifiedQualityGatePass,
    candidate_semantic_sha256,
)


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
    measurements: CandidateMeasurements,
    schema_path: Path,
) -> CandidateSeal:
    """Validate in memory, write 13 payloads and inventory, then completion last."""
    if workspace.final_root.exists():
        raise FileExistsError(f"candidate destination already exists: {workspace.final_root}")
    prepared = prepare_candidate(
        payload=payload,
        measurements=measurements,
        schema_path=schema_path,
    )
    written: list[str] = []
    for relative in MANAGED_PAYLOAD_PATHS:
        _write_bytes(workspace.staging_root / relative, prepared.managed_bytes[relative])
        written.append(relative)
    inventory_relative = "records/artifact_inventory.json"
    _write_bytes(
        workspace.staging_root / inventory_relative,
        stable_json_bytes(prepared.bundle["artifact_inventory"]),
    )
    written.append(inventory_relative)
    completion_relative = "records/completion_record.json"
    _write_bytes(
        workspace.staging_root / completion_relative,
        stable_json_bytes(prepared.bundle["completion"]),
    )
    written.append(completion_relative)
    return CandidateSeal(
        completion_path=workspace.staging_root / completion_relative,
        written_paths=tuple(written),
    )


def retain_failed_attempt(
    *,
    workspace: CandidateWorkspace,
    candidate_id: str,
    fatal_code: str,
    detail: str,
    schema_path: Path,
) -> Path:
    """Retain one schema-valid failure, retracting a premature completion."""
    completion = workspace.staging_root / "records/completion_record.json"
    if completion.exists():
        completion.unlink()
    record = build_attempt_record(
        candidate_id=candidate_id,
        fatal_code=fatal_code,
        detail=detail,
    )
    validate_attempt_record(record, schema_path)
    path = workspace.staging_root / "records/attempt_record.json"
    _write_bytes(path, stable_json_bytes(record))
    return path


def publish_workspace(
    workspace: CandidateWorkspace,
    quality_gate_pass: VerifiedQualityGatePass,
) -> Path:
    """Publish only a completed staging tree with verified external acceptance."""
    completion = workspace.staging_root / "records/completion_record.json"
    if not completion.is_file():
        raise ValueError("candidate staging tree has no completion record")
    candidate_id = workspace.final_root.name
    if quality_gate_pass.candidate_id != candidate_id:
        raise ValueError("quality-gate pass candidate differs from publication")
    if quality_gate_pass.candidate_semantic_sha256 != candidate_semantic_sha256(
        workspace.staging_root
    ):
        raise ValueError("quality-gate semantic differs from publication")
    if workspace.final_root.exists():
        raise FileExistsError(f"candidate destination already exists: {workspace.final_root}")
    workspace.staging_root.rename(workspace.final_root)
    return workspace.final_root / "records/completion_record.json"


def preserve_failed_workspace(workspace: CandidateWorkspace, attempts_root: Path) -> Path:
    """Move an incomplete attempt from opaque staging to a stable attempts path."""
    attempt = workspace.staging_root / "records/attempt_record.json"
    completion = workspace.staging_root / "records/completion_record.json"
    if not attempt.is_file() or completion.exists():
        raise ValueError("failed workspace must contain attempt evidence without completion")
    attempts_root.mkdir(parents=True, exist_ok=True)
    destination = attempts_root / workspace.staging_root.name
    if destination.exists():
        raise FileExistsError(f"attempt destination already exists: {destination}")
    workspace.staging_root.rename(destination)
    return destination / "records/attempt_record.json"


def verify_completed_candidate(root: Path, candidate_id: str, schema_path: Path) -> Path:
    """Require exact checksums, managed files, schema, and cross-record validity."""
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
    managed_bytes: dict[str, bytes] = {}
    for item in inventory["files"]:
        relative = Path(item["path"])
        path = root / relative
        if not path.is_file():
            raise ValueError(f"candidate inventory file is missing: {relative}")
        value = path.read_bytes()
        if len(value) != item["byte_size"] or hashlib.sha256(value).hexdigest() != item["sha256"]:
            raise ValueError(f"candidate inventory checksum differs: {relative}")
        managed_bytes[item["path"]] = value
    actual_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    expected_files = set(expected_paths) | {
        "records/artifact_inventory.json",
        "records/completion_record.json",
    }
    if actual_files != expected_files:
        raise ValueError("candidate managed file set differs")
    prepared = _load_prepared_candidate(managed_bytes, inventory, completion, schema_path)
    if prepared.bundle["identity"]["candidate_id"] != candidate_id:
        raise ValueError("candidate identity differs")
    expected_artifact_bytes = (
        sum(item["byte_size"] for item in inventory["files"])
        + inventory_path.stat().st_size
        + completion_path.stat().st_size
    )
    if prepared.bundle["metrics"]["artifact_bytes"] != expected_artifact_bytes:
        raise ValueError("candidate artifact-byte metric differs from final files")
    return completion_path


def reuse_completed_candidate(
    root: Path,
    candidate_id: str,
    schema_path: Path,
    quality_gate_pass: VerifiedQualityGatePass,
) -> Path:
    """Reuse only after candidate checksums and external acceptance verify."""
    if quality_gate_pass.candidate_id != candidate_id:
        raise ValueError("quality-gate pass candidate differs from reuse")
    if quality_gate_pass.candidate_semantic_sha256 != candidate_semantic_sha256(root):
        raise ValueError("quality-gate semantic differs from reuse")
    return verify_completed_candidate(root, candidate_id, schema_path)


def _load_prepared_candidate(
    managed_bytes: dict[str, bytes],
    inventory: dict[str, object],
    completion: dict[str, object],
    schema_path: Path,
) -> PreparedCandidate:
    """Reconstruct and revalidate a completed aggregate without rebuilding it."""

    def load(path: str) -> object:
        text = managed_bytes[path].decode()
        if path in JSONL_PATHS:
            return [json.loads(line) for line in text.splitlines()]
        return json.loads(text)

    bundle = {
        "identity": load("records/identity.json"),
        "input_inventory": load("records/input_inventory.json"),
        "features": load("artifacts/item_features.jsonl"),
        "toc_entries": load("artifacts/visible_toc_entries.jsonl"),
        "reconciliations": load("artifacts/toc_reconciliation.jsonl"),
        "regimes": load("artifacts/regimes.jsonl"),
        "decisions": load("artifacts/decisions.jsonl"),
        "hierarchy": load("artifacts/hierarchy.json"),
        "ambiguities": load("artifacts/ambiguities.jsonl"),
        "warnings": load("artifacts/warnings.jsonl"),
        "summary": load("records/summary.json"),
        "metrics": load("records/metrics.json"),
        "artifact_inventory": inventory,
        "completion": completion,
    }
    # Environment is managed and verified but intentionally absent from the
    # aggregate schema because it is diagnostic rather than semantic evidence.
    json.loads(managed_bytes["records/environment.json"].decode())
    validate_candidate_bundle(bundle, schema_path)
    return PreparedCandidate(bundle=bundle, managed_bytes=managed_bytes)


def _write_bytes(path: Path, value: bytes) -> None:
    """Write exact prepared bytes while creating only the containing folder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)
