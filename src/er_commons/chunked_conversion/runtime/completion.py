"""Fail-closed completed-run readers for chunk-conversion reuse."""

from __future__ import annotations

from pathlib import Path

from er_commons.artifact_io import read_json_object, sha256_file
from er_commons.chunked_conversion.runtime.contracts import (
    ChunkedConversionCompletion,
    ExpectedChunkedConversionCompletion,
)
from er_commons.chunked_conversion.runtime.diagnostics import ChunkedConversionError, require
from er_commons.document_parsing.content_parsing.evidence import (
    CompletedRunInvariantError,
    verify_inventory,
)


def verify_chunked_completion(
    root: Path,
    expected: ExpectedChunkedConversionCompletion,
) -> ChunkedConversionCompletion:
    """Verify identity, lineage, inventory closure, and terminal chunk-conversion state."""
    stage = "chunked_reuse"
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
    completion = ChunkedConversionCompletion.model_validate_json(completion_path.read_bytes())
    _verify_chunked_identity(completion, expected, root)
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
        raise ChunkedConversionError(
            f"inventory_{error.invariant}",
            stage=stage,
            path=root.as_posix(),
            context={"detail": str(error)},
        ) from error
    return completion


def _verify_chunked_identity(
    completion: ChunkedConversionCompletion,
    expected: ExpectedChunkedConversionCompletion,
    root: Path,
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
        stage="chunked_reuse",
        path=(root / "records/completion_record.json").as_posix(),
        expected=wanted,
        actual=actual,
    )
