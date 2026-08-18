"""Verification of one configured hierarchy candidate and its bounded control."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from er_commons.document_records.document_structure.bundle import JsonObject
from er_commons.document_records.document_structure.errors import StructureContractError
from er_commons.document_records.document_structure.policies.control import (
    validate_control_provenance,
)
from er_commons.hierarchy_inference.bounded_acceptance import (
    verify_bounded_acceptance,
    verify_bounded_acceptance_policy,
)
from er_commons.hierarchy_inference.candidate_publication import (
    verify_completed_candidate as verify_hierarchy_candidate,
)

COMPLETION_RELATIVE_PATH = Path("records/completion_record.json")
INVENTORY_RELATIVE_PATH = Path("records/artifact_inventory.json")


def verify_bounded_hierarchy_control(
    *,
    data_root: Path,
    candidate_root: Path,
    candidate_id: str,
    hierarchy_schema_path: Path,
    acceptance_path: Path,
    acceptance_policy_path: Path,
    producer_comparison_path: Path,
    baseline_producer_run_id: str,
    hierarchy_producer_run_id: str,
) -> JsonObject:
    """Compose maintained hierarchy verifiers and project their checked evidence."""
    try:
        verify_hierarchy_candidate(candidate_root, candidate_id, hierarchy_schema_path)
        policy = verify_bounded_acceptance_policy(acceptance_policy_path, data_root)
        verified = verify_bounded_acceptance(
            path=acceptance_path,
            policy=policy,
            candidate_root=candidate_root,
            candidate_id=candidate_id,
            data_root=data_root,
        )
    except (OSError, ValueError) as error:
        raise StructureContractError(f"hierarchy bounded handoff is invalid: {error}") from error

    completion = _load_json_object(candidate_root / COMPLETION_RELATIVE_PATH)
    acceptance = _load_json_object(acceptance_path)
    comparison_sha256 = _verify_producer_comparison(
        producer_comparison_path,
        baseline_producer_run_id=baseline_producer_run_id,
        hierarchy_producer_run_id=hierarchy_producer_run_id,
    )
    control = _build_control_record(
        completion=completion,
        acceptance=acceptance,
        acceptance_sha256=hashlib.sha256(acceptance_path.read_bytes()).hexdigest(),
        semantic_file_set_sha256=verified.candidate_semantic_sha256,
        aggregate_semantic_sha256=verified.frozen_semantic_sha256,
        producer_comparison_sha256=comparison_sha256,
    )
    validate_control_provenance(control)
    return control


def _verify_producer_comparison(
    path: Path,
    *,
    baseline_producer_run_id: str,
    hierarchy_producer_run_id: str,
) -> str:
    """Require a machine-pass comparison for the two configured producer IDs."""
    raw = _read_required_bytes(path)
    value = _json_object(raw, path)
    if value.get("machine_status") != "pass":
        raise StructureContractError("producer comparison is not a machine pass")
    proofs = value.get("proofs")
    if not isinstance(proofs, list) or not all(isinstance(item, dict) for item in proofs):
        raise StructureContractError("producer comparison proofs are not JSON objects")
    by_role = {item.get("role"): item for item in proofs}
    if set(by_role) != {"baseline", "hierarchy"} or len(proofs) != 2:
        raise StructureContractError("producer comparison roles differ")
    expected_ids = {
        "baseline": baseline_producer_run_id,
        "hierarchy": hierarchy_producer_run_id,
    }
    changed = [
        role
        for role, expected_id in expected_ids.items()
        if by_role[role].get("refreshed_producer_run_id") != expected_id
        or by_role[role].get("equivalent") is not True
    ]
    if changed:
        raise StructureContractError(
            "producer comparison does not verify configured lineage: " + ", ".join(changed)
        )
    return hashlib.sha256(raw).hexdigest()


def _build_control_record(
    *,
    completion: JsonObject,
    acceptance: JsonObject,
    acceptance_sha256: str,
    semantic_file_set_sha256: str,
    aggregate_semantic_sha256: str,
    producer_comparison_sha256: str,
) -> JsonObject:
    """Project verified external evidence into the compact downstream record."""
    candidate = _required_object(acceptance, "candidate")
    scope = _required_object(acceptance, "scope")
    return {
        "candidate_id": completion["candidate_id"],
        "completion_status": completion["status"],
        "artifact_inventory_sha256": completion["artifact_inventory_sha256"],
        "semantic_file_set_sha256": semantic_file_set_sha256,
        "aggregate_semantic_sha256": aggregate_semantic_sha256,
        "bounded_acceptance_sha256": acceptance_sha256,
        "authorization_id": acceptance["authorization_id"],
        "acceptance_status": acceptance["status"],
        "source_id": scope["source_id"],
        "physical_page_count": scope["physical_page_count"],
        "corpus_wide_acceptance": scope["corpus_wide_acceptance"],
        "authorized_uses": scope["authorized_uses"],
        "limitations": acceptance["limitations"],
        "semantic_counts": candidate["counts"],
        "producer_comparison_sha256": producer_comparison_sha256,
    }


def _required_object(value: JsonObject, key: str) -> JsonObject:
    selected = value.get(key)
    if not isinstance(selected, dict):
        raise StructureContractError(f"bounded acceptance has no {key} object")
    return selected


def _load_json_object(path: Path) -> JsonObject:
    return _json_object(_read_required_bytes(path), path)


def _json_object(raw: bytes, path: Path) -> JsonObject:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise StructureContractError(f"invalid JSON evidence at {path}: {error.msg}") from error
    if not isinstance(value, dict):
        raise StructureContractError(f"expected JSON object: {path}")
    return value


def _read_required_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError as error:
        raise StructureContractError(f"required hierarchy evidence is missing: {path}") from error
