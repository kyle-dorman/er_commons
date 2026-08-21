"""Fail-closed reuse tests for chunked-conversion completion records."""

from __future__ import annotations

from pathlib import Path

import pytest

from er_commons.artifact_io import artifact_inventory, sha256_file, write_json_atomic
from er_commons.chunked_conversion.runtime.completion import verify_chunked_completion
from er_commons.chunked_conversion.runtime.contracts import ExpectedChunkedConversionCompletion
from er_commons.chunked_conversion.runtime.diagnostics import ChunkedConversionError


def _completed_root(tmp_path: Path, *, run_id: str = "chunk1-a") -> Path:
    root = tmp_path / run_id
    (root / "records").mkdir(parents=True)
    write_json_atomic(root / "payload.json", {"value": 1})
    inventory_path = root / "records/artifact_inventory.json"
    write_json_atomic(
        inventory_path,
        artifact_inventory(
            root,
            excluded={"records/artifact_inventory.json", "records/completion_record.json"},
        ),
    )
    write_json_atomic(
        root / "records/completion_record.json",
        {
            "schema_version": "er_commons.chunked_conversion_completion.v1",
            "run_id": run_id,
            "status": "complete",
            "plan_id": "dplan1-a",
            "aggregate_conversion_id": "dconv1-a",
            "artifact_inventory": "records/artifact_inventory.json",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "completion_last": True,
        },
    )
    return root


def _expected(run_id: str = "chunk1-a") -> ExpectedChunkedConversionCompletion:
    return ExpectedChunkedConversionCompletion(
        run_id=run_id, plan_id="dplan1-a", aggregate_conversion_id="dconv1-a"
    )


def test_chunked_reuse_verifies_exact_identity_and_inventory(tmp_path: Path) -> None:
    completion = verify_chunked_completion(_completed_root(tmp_path), _expected())
    assert completion.aggregate_conversion_id == "dconv1-a"


def test_chunked_reuse_rejects_transplanted_completion(tmp_path: Path) -> None:
    root = _completed_root(tmp_path)
    with pytest.raises(ChunkedConversionError) as raised:
        verify_chunked_completion(root, _expected("chunk1-foreign"))
    assert raised.value.code == "completion_identity"
    assert raised.value.path.endswith("records/completion_record.json")


def test_chunked_reuse_rejects_same_size_payload_corruption(tmp_path: Path) -> None:
    root = _completed_root(tmp_path)
    payload = root / "payload.json"
    original = payload.read_bytes()
    corrupted = original.replace(b"1", b"2", 1)
    assert len(corrupted) == len(original)
    payload.write_bytes(corrupted)
    with pytest.raises(ChunkedConversionError) as raised:
        verify_chunked_completion(root, _expected())
    assert raised.value.code == "inventory_inventory_file_checksum"
    assert "payload.json" in str(raised.value.context["detail"])
