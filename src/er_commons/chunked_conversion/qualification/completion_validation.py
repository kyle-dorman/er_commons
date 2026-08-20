"""Fail-closed completed-run readers for qualification reuse."""

from __future__ import annotations

from pathlib import Path

from er_commons.artifact_io import read_json_object, sha256_file
from er_commons.chunked_conversion.qualification.contracts import (
    ExpectedGateCCompletion,
    GateCCompletion,
)
from er_commons.chunked_conversion.qualification.diagnostics import QualificationError, require
from er_commons.document_parsing.content_parsing.evidence import (
    CompletedRunInvariantError,
    verify_inventory,
)


def verify_gate_c_completion(root: Path, expected: ExpectedGateCCompletion) -> GateCCompletion:
    """Verify identity, lineage, inventory closure, and terminal Gate C state."""
    stage = "gate_c_reuse"
    completion_path = root / "records/completion_record.json"
    inventory_path = root / "records/artifact_inventory.json"
    require(
        completion_path.is_file() and inventory_path.is_file(),
        "terminal_records_missing",
        stage=stage,
        path=root.as_posix(),
        expected=["records/completion_record.json", "records/artifact_inventory.json"],
        actual={
            "completion": completion_path.is_file(),
            "inventory": inventory_path.is_file(),
        },
    )
    completion = GateCCompletion.model_validate_json(completion_path.read_bytes())
    _verify_gate_c_identity(completion, expected, root)
    require(
        completion.status == "complete" and completion.completion_last,
        "terminal_state",
        stage=stage,
        path=completion_path.as_posix(),
        expected={"status": "complete", "completion_last": True},
        actual={"status": completion.status, "completion_last": completion.completion_last},
    )
    require(
        completion.artifact_inventory == "records/artifact_inventory.json",
        "inventory_path",
        stage=stage,
        path=completion_path.as_posix(),
        expected="records/artifact_inventory.json",
        actual=completion.artifact_inventory,
    )
    require(
        completion.artifact_inventory_sha256 == sha256_file(inventory_path),
        "inventory_seal",
        stage=stage,
        path=inventory_path.as_posix(),
        expected=completion.artifact_inventory_sha256,
        actual=sha256_file(inventory_path),
    )
    try:
        verify_inventory(root, read_json_object(inventory_path))
    except CompletedRunInvariantError as error:
        raise QualificationError(
            f"inventory_{error.invariant}",
            stage=stage,
            path=root.as_posix(),
            context={"detail": str(error)},
        ) from error
    return completion


def _verify_gate_c_identity(
    completion: GateCCompletion, expected: ExpectedGateCCompletion, root: Path
) -> None:
    actual = {
        "run_id": completion.run_id,
        "plan_id": completion.plan_id,
        "aggregate_conversion_id": completion.aggregate_conversion_id,
    }
    wanted = {
        "run_id": expected.run_id,
        "plan_id": expected.plan_id,
        "aggregate_conversion_id": expected.aggregate_conversion_id,
    }
    matches = completion.run_id == expected.run_id and completion.plan_id == expected.plan_id
    if expected.aggregate_conversion_id is not None:
        matches = matches and completion.aggregate_conversion_id == expected.aggregate_conversion_id
    require(
        matches,
        "completion_identity",
        stage="gate_c_reuse",
        path=(root / "records/completion_record.json").as_posix(),
        expected=wanted,
        actual=actual,
    )
