"""Review-bound finalization, no-clobber release publication and separate acceptance."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from er_commons.artifact_io import canonical_json_sha256
from er_commons.response_inventory.release_storage import (
    COMPLETION,
    MANIFEST,
    digest,
    encode,
    inventory_identity,
    no_symlinks,
    publish_container,
    read_container,
    write_file,
)


def require_authorization(spec: dict[str, Any], operation: str) -> None:
    """Stop before a write when the specific operation lacks explicit authorization."""
    gate = {
        "prepare": "execution",
        "review": "execution",
        "finalize": "finalization",
        "publish": "publication",
        "accept": "acceptance",
    }[operation]
    if spec["authorization"][gate] is not True:
        raise ValueError(f"Task 05H {operation} requires separate explicit {gate} authorization")


def validate_quality(
    quality: dict[str, Any],
    *,
    plan_id: str,
    semantic_digest: str,
    repository_bindings: list[dict[str, Any]],
) -> None:
    """Require independent human-maintainability review of the actual code and inputs."""
    expected = {
        "plan_id": plan_id,
        "input_semantic_digest": semantic_digest,
        "repository_bindings": repository_bindings,
        "status": "passed",
        "material_findings": [],
    }
    if any(quality.get(key) != value for key, value in expected.items()):
        raise ValueError(
            "05H quality report does not bind the current code, inputs or passing review"
        )
    reviewer = quality.get("reviewer")
    if (
        not isinstance(reviewer, str)
        or not reviewer.strip()
        or quality.get("independent_review") is not True
    ):
        raise ValueError("05H finalization requires an identified independent reviewer")
    dimensions = {"readability", "editability", "debuggability", "operations", "testing"}
    if quality.get("dimensions") != dict.fromkeys(sorted(dimensions), "passed"):
        raise ValueError("05H human-maintainability dimensions are incomplete")


def publish_inventory(
    candidate_root: Path, release_parent: Path, spec: dict[str, Any], *, plan_id: str
) -> dict[str, Any]:
    """Copy only compact 05H-owned payloads after finalization; never copy source components."""
    require_authorization(spec, "publish")
    completion, payloads = read_container(candidate_root, plan_id=plan_id)
    identity = inventory_identity(completion)
    root = release_parent / identity
    result = publish_container(
        root,
        payloads,
        plan_id=plan_id,
        semantic_digest=completion["semantic_digest"],
        status="complete_with_limitations",
    )
    if result != completion:
        raise ValueError("publication changed finalized completion identity")
    return {
        "status": "published_pending_acceptance",
        "inventory_id": identity,
        "inventory_root": str(root),
        "completion": result,
    }


def accept_inventory(
    inventory_root: Path,
    working_root: Path,
    spec: dict[str, Any],
    *,
    plan_id: str,
    accepted_by: str,
    accepted_at: str,
) -> dict[str, Any]:
    """Prepare acceptance evidence; only successful supervision permits designation."""
    require_authorization(spec, "accept")
    if (
        not accepted_by.strip()
        or datetime.fromisoformat(accepted_at.replace("Z", "+00:00")).tzinfo is None
    ):
        raise ValueError("acceptance requires a reviewer and timezone-aware timestamp")
    completion, payloads = read_container(inventory_root, plan_id=plan_id)
    identity = inventory_identity(completion)
    if inventory_root != working_root.parent.parent / identity:
        raise ValueError("acceptance must name the exact final inventory namespace")
    record = {
        "schema_version": "er_commons.response_inventory_release_acceptance.v1",
        "status": "accepted_with_limitations",
        "plan_id": plan_id,
        "inventory_id": identity,
        "completion_id": completion["completion_id"],
        "completion_sha256": digest((inventory_root / COMPLETION).read_bytes()),
        "manifest_sha256": digest((inventory_root / MANIFEST).read_bytes()),
        "handoff_sha256": digest(payloads["records/task07_task08_handoff.json"]),
        "accepted_by": accepted_by,
        "accepted_at": accepted_at,
        "explicit_authorization": True,
        "downstream_execution_authorized": False,
    }
    record["acceptance_id"] = "acceptance05hv1-" + canonical_json_sha256(record)
    pointer = working_root / "accepted.json"
    no_symlinks(pointer)
    if pointer.exists():
        old: dict[str, Any] = json.loads(pointer.read_bytes())
        if old != record:
            raise ValueError("different acceptance already exists; explicit supersession required")
        acceptance_path = working_root / "acceptances" / record["acceptance_id"] / "acceptance.json"
        if acceptance_path.read_bytes() != encode(record):
            raise ValueError("acceptance record does not match existing pointer")
        return old
    acceptance_root = working_root / "acceptances" / record["acceptance_id"]
    no_symlinks(acceptance_root)
    acceptance_root.mkdir(parents=True, exist_ok=True)
    path = acceptance_root / "acceptance.json"
    if path.exists():
        if path.read_bytes() != encode(record):
            raise ValueError("conflicting interrupted acceptance record")
    else:
        write_file(path, encode(record))
    # The supervisor has not completed yet: deliberately leave the pointer absent.
    return record


def designate_acceptance(
    inventory_root: Path,
    working_root: Path,
    spec: dict[str, Any],
    *,
    plan_id: str,
    accepted_by: str,
    accepted_at: str,
    execution_evidence: dict[str, Any],
    max_metadata_bytes: int = 65536,
) -> dict[str, Any]:
    """Publish the pointer last, after the caller verifies terminal supervisor success."""
    require_authorization(spec, "accept")
    prepared = accept_inventory(
        inventory_root,
        working_root,
        spec,
        plan_id=plan_id,
        accepted_by=accepted_by,
        accepted_at=accepted_at,
    )
    root = working_root / "acceptances" / prepared["acceptance_id"]
    evidence_path = root / "execution.json"
    no_symlinks(evidence_path)
    evidence = {
        "schema_version": "er_commons.task05h.acceptance_execution.v1",
        "acceptance_id": prepared["acceptance_id"],
        "inventory_id": prepared["inventory_id"],
        "execution": execution_evidence,
    }
    if len(encode(evidence)) + len(encode(prepared)) > max_metadata_bytes:
        raise ValueError("acceptance designation exceeds reserved metadata bytes")
    if evidence_path.exists():
        if evidence_path.read_bytes() != encode(evidence):
            raise ValueError("conflicting acceptance execution evidence")
    else:
        write_file(evidence_path, encode(evidence))
    pointer = working_root / "accepted.json"
    if pointer.exists():
        if pointer.read_bytes() != encode(prepared):
            raise ValueError("different acceptance already exists; explicit supersession required")
    else:
        write_file(pointer, encode(prepared))
    return prepared
