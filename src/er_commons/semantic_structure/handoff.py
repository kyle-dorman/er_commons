"""Verification of the immutable hierarchy input accepted by Task 03E.2d."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import rfc8785

from er_commons.semantic_structure.bundle import JsonObject
from er_commons.semantic_structure.constants import (
    EXPECTED_ACCEPTANCE_SHA256,
    EXPECTED_CANDIDATE_ID,
    EXPECTED_INVENTORY_DIGEST,
    EXPECTED_PRODUCER_COMPARISON_SHA256,
    PRODUCER_COMPARISON_RELATIVE_PATH,
)
from er_commons.semantic_structure.errors import SemanticContractError
from er_commons.semantic_structure.policies.control import validate_control_provenance

COMPLETION_RELATIVE_PATH = Path("records/completion_record.json")
INVENTORY_RELATIVE_PATH = Path("records/artifact_inventory.json")


def verify_task03e2d_control(candidate_root: Path, acceptance_path: Path) -> JsonObject:
    """Verify the sealed candidate, bounded authorization, and producer bridge evidence."""
    completion = _load_json_object(candidate_root / COMPLETION_RELATIVE_PATH)
    inventory = _load_json_object(candidate_root / INVENTORY_RELATIVE_PATH)
    acceptance = _load_verified_acceptance(acceptance_path)

    _verify_completion(completion)
    managed_files = _verify_inventory(inventory)
    _verify_managed_files(candidate_root, managed_files)
    _verify_producer_comparison(candidate_root)

    control = _build_control_record(completion, acceptance)
    validate_control_provenance(control)
    return control


def _verify_completion(completion: JsonObject) -> None:
    """Require the exact completion-last record of the accepted candidate."""
    expected = {
        "artifact_inventory_sha256": EXPECTED_INVENTORY_DIGEST,
        "candidate_id": EXPECTED_CANDIDATE_ID,
        "status": "complete_with_ambiguities",
    }
    if completion != expected:
        changed = sorted(
            key
            for key in set(completion) | set(expected)
            if completion.get(key) != expected.get(key)
        )
        raise SemanticContractError(f"hierarchy correction completion differs: {changed}")


def _verify_inventory(inventory: JsonObject) -> dict[str, JsonObject]:
    """Verify the canonical inventory digest and index its managed files."""
    actual_digest = hashlib.sha256(rfc8785.dumps(inventory)).hexdigest()
    if actual_digest != EXPECTED_INVENTORY_DIGEST:
        raise SemanticContractError(
            "hierarchy artifact inventory digest differs: "
            f"expected {EXPECTED_INVENTORY_DIGEST}, got {actual_digest}"
        )

    files = inventory.get("files")
    if not isinstance(files, list):
        raise SemanticContractError("hierarchy artifact inventory has no file list")
    managed = {item["path"]: item for item in files}
    if len(managed) != len(files):
        raise SemanticContractError("hierarchy artifact inventory contains duplicate paths")
    return managed


def _verify_managed_files(candidate_root: Path, managed: dict[str, JsonObject]) -> None:
    """Verify every managed byte and reject unrecorded files."""
    for relative_path, expected in managed.items():
        path = candidate_root / relative_path
        raw = _read_required_bytes(path)
        _verify_file_bytes(path, raw, expected)

    actual_paths = {
        path.relative_to(candidate_root).as_posix()
        for path in candidate_root.rglob("*")
        if path.is_file()
    }
    expected_paths = set(managed) | {
        INVENTORY_RELATIVE_PATH.as_posix(),
        COMPLETION_RELATIVE_PATH.as_posix(),
    }
    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)
        extra = sorted(actual_paths - expected_paths)
        raise SemanticContractError(
            f"hierarchy managed file set differs: missing={missing}, extra={extra}"
        )


def _verify_file_bytes(path: Path, raw: bytes, expected: JsonObject) -> None:
    """Check one inventory entry's exact length and SHA-256."""
    if len(raw) != expected["byte_size"]:
        raise SemanticContractError(
            f"hierarchy artifact byte size differs: {path} "
            f"expected {expected['byte_size']}, got {len(raw)}"
        )
    actual_digest = hashlib.sha256(raw).hexdigest()
    if actual_digest != expected["sha256"]:
        raise SemanticContractError(
            f"hierarchy artifact checksum differs: {path} "
            f"expected {expected['sha256']}, got {actual_digest}"
        )


def _load_verified_acceptance(path: Path) -> JsonObject:
    """Load the bounded authorization only after its exact bytes verify."""
    raw = _read_required_bytes(path)
    actual_digest = hashlib.sha256(raw).hexdigest()
    if actual_digest != EXPECTED_ACCEPTANCE_SHA256:
        raise SemanticContractError(
            "bounded-acceptance bytes differ: "
            f"expected {EXPECTED_ACCEPTANCE_SHA256}, got {actual_digest}"
        )
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise SemanticContractError(f"expected JSON object: {path}")
    return value


def _verify_producer_comparison(candidate_root: Path) -> None:
    """Verify the machine-pass evidence connecting the two producer runs."""
    data_root = _data_root_from_candidate(candidate_root)
    comparison_path = data_root / PRODUCER_COMPARISON_RELATIVE_PATH
    raw = _read_required_bytes(comparison_path)
    actual_digest = hashlib.sha256(raw).hexdigest()
    if actual_digest != EXPECTED_PRODUCER_COMPARISON_SHA256:
        raise SemanticContractError(
            "producer comparison bytes differ: "
            f"expected {EXPECTED_PRODUCER_COMPARISON_SHA256}, got {actual_digest}"
        )


def _data_root_from_candidate(candidate_root: Path) -> Path:
    """Recover the configured artifact root from a task-scoped candidate path."""
    pipelines_root = next(
        (parent for parent in candidate_root.parents if parent.name == "pipelines"),
        None,
    )
    if pipelines_root is None:
        raise SemanticContractError(
            f"hierarchy candidate is not below a pipelines root: {candidate_root}"
        )
    return pipelines_root.parent


def _build_control_record(completion: JsonObject, acceptance: JsonObject) -> JsonObject:
    """Project verified external evidence into the compact downstream record."""
    candidate = acceptance["candidate"]
    scope = acceptance["scope"]
    return {
        "candidate_id": completion["candidate_id"],
        "completion_status": completion["status"],
        "artifact_inventory_sha256": completion["artifact_inventory_sha256"],
        "semantic_file_set_sha256": candidate["candidate_semantic_sha256"],
        "aggregate_semantic_sha256": candidate["frozen_semantic_sha256"],
        "bounded_acceptance_sha256": EXPECTED_ACCEPTANCE_SHA256,
        "authorization_id": acceptance["authorization_id"],
        "acceptance_status": acceptance["status"],
        "source_id": scope["source_id"],
        "physical_page_count": scope["physical_page_count"],
        "corpus_wide_acceptance": scope["corpus_wide_acceptance"],
        "authorized_uses": scope["authorized_uses"],
        "limitations": acceptance["limitations"],
        "semantic_counts": candidate["counts"],
        "producer_comparison_sha256": EXPECTED_PRODUCER_COMPARISON_SHA256,
    }


def _load_json_object(path: Path) -> JsonObject:
    """Load one required JSON object with a useful path in the error."""
    raw = _read_required_bytes(path)
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise SemanticContractError(f"expected JSON object: {path}")
    return value


def _read_required_bytes(path: Path) -> bytes:
    """Read a required file while translating absence into a contract error."""
    try:
        return path.read_bytes()
    except FileNotFoundError as error:
        raise SemanticContractError(f"required hierarchy evidence is missing: {path}") from error
