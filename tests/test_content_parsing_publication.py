"""Failure safety and immutable reuse tests for producer publication."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.document_parsing.content_parsing.evidence import (
    CompletedRunInvariantError,
    verify_completed_run,
    write_inventory,
)
from er_commons.document_parsing.content_parsing.identity import canonical_json_sha256
from er_commons.document_parsing.content_parsing.publication import (
    preserve_failed_attempt,
    publish_workspace,
    reserve_workspace,
)
from er_commons.document_parsing.content_parsing.records import (
    CompletionRecord,
    ProducerSummary,
    TableStageObservation,
)


def _completed_run(root: Path) -> tuple[str, Path]:
    identity = {
        "source": {"source_id": "document", "sha256": "a" * 64},
        "sealed_release": {"manifest_sha256": "b" * 64},
        "policy": "test",
    }
    producer_run_id = f"prv1-{canonical_json_sha256(identity)}"
    run_root = root / producer_run_id
    artifact = run_root / "documents" / "document" / "producer" / "document.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}\n")
    write_json_atomic(
        run_root / "records" / "producer_identity.json",
        {"producer_run_id": producer_run_id, "identity": identity},
    )
    summary = ProducerSummary(
        producer_run_id=producer_run_id,
        producer_status="complete",
        publication_status="complete",
        source_id="document",
        physical_page_count=1,
        routing={
            "no_table_route": 1,
            "layout_regions": 0,
            "full_page_numeric": 0,
        },
        tables=TableStageObservation(
            status="not_applicable",
            document_scope_complete=True,
            verified_no_table_routes=True,
            routed_pages=[],
            routed_page_count=0,
            logical_table_count=0,
            family_assignment_count=0,
            family_count=0,
            zero_table_pages=[],
            manifest=None,
        ),
        asset_count=0,
        warnings=[],
        error_count=0,
        wall_seconds=1,
        conversion_cpu_seconds=1,
        peak_rss_bytes=1,
        output_bytes_before_inventory=1,
    )
    write_json_atomic(
        run_root / "records" / "producer_summary.json",
        summary.model_dump(mode="json", exclude_none=True),
    )
    inventory_path = write_inventory(run_root)
    completion = CompletionRecord(
        schema_version="1.0.0",
        producer_run_id=producer_run_id,
        producer_status="complete",
        publication_status="complete",
        source_id="document",
        source_sha256="a" * 64,
        source_manifest_sha256="b" * 64,
        artifact_inventory="records/artifact_inventory.json",
        artifact_inventory_sha256=sha256_file(inventory_path),
        completed_at_utc="2026-01-01T00:00:00+00:00",
    )
    write_json_atomic(
        run_root / "records" / "completion_record.json",
        completion.model_dump(mode="json"),
    )
    return producer_run_id, artifact


def test_completed_run_reuse_verifies_every_inventoried_file(
    tmp_path: Path,
) -> None:
    producer_run_id, artifact = _completed_run(tmp_path)
    run_root = tmp_path / producer_run_id

    assert verify_completed_run(run_root, producer_run_id).name == "completion_record.json"

    artifact.write_text('{"changed": true}\n')
    with pytest.raises(CompletedRunInvariantError) as captured:
        verify_completed_run(run_root, producer_run_id)
    assert captured.value.invariant == "inventory_file_size"


def test_completed_run_reuse_rejects_uninventoried_files(tmp_path: Path) -> None:
    producer_run_id, _artifact = _completed_run(tmp_path)
    run_root = tmp_path / producer_run_id
    (run_root / "unexpected.txt").write_text("not inventoried")

    with pytest.raises(CompletedRunInvariantError) as captured:
        verify_completed_run(run_root, producer_run_id)

    assert captured.value.invariant == "complete_file_set"


def test_inventory_excludes_its_own_seal_records(tmp_path: Path) -> None:
    (tmp_path / "records").mkdir()
    (tmp_path / "payload.txt").write_text("payload")
    write_json_atomic(
        tmp_path / "records" / "completion_record.json",
        {"status": "stale"},
    )

    inventory = json.loads(write_inventory(tmp_path).read_text())
    paths = {record["path"] for record in inventory["files"]}

    assert "payload.txt" in paths
    assert "records/completion_record.json" not in paths
    assert "records/artifact_inventory.json" not in paths


def test_failed_attempt_preserves_partial_work_without_completion(
    tmp_path: Path,
) -> None:
    task_root = tmp_path / "task"
    staging = task_root / ".tmp" / "prv1-example.random"
    staging.mkdir(parents=True)
    (staging / "partial.json").write_text("{}\n")
    write_json_atomic(
        staging / "records" / "completion_record.json",
        {"publication_status": "complete"},
    )
    started = datetime(2026, 1, 1, tzinfo=UTC)
    finished = datetime(2026, 1, 1, 0, 0, 2, tzinfo=UTC)

    attempt = preserve_failed_attempt(
        staging_root=staging,
        task_root=task_root,
        producer_run_id="prv1-example",
        failed_stage="tables",
        started_at=started,
        finished_at=finished,
        wall_seconds=2,
        error=RuntimeError("simulated"),
        token="12345678abcdef",
    )

    record = json.loads((attempt / "attempt_record.json").read_text())
    assert record["failed_stage"] == "tables"
    assert record["started_at_utc"] == started.isoformat()
    assert (attempt / "partial.json").is_file()
    assert not (attempt / "records" / "completion_record.json").exists()
    assert record["removed_invalid_completion_marker"]
    assert not staging.exists()


def test_publication_race_never_overwrites_final_output(tmp_path: Path) -> None:
    workspace = reserve_workspace(tmp_path, "prv1-example", token="token")
    workspace.final_root.mkdir()

    with pytest.raises(FileExistsError, match="appeared during publication"):
        publish_workspace(workspace)

    assert workspace.staging_root.is_dir()
    assert workspace.final_root.is_dir()


def test_publication_refuses_workspace_without_completion(tmp_path: Path) -> None:
    workspace = reserve_workspace(tmp_path, "prv1-example", token="token")
    (workspace.staging_root / "payload.json").write_text("{}\n")

    with pytest.raises(ValueError, match="no completion record"):
        publish_workspace(workspace)

    assert workspace.staging_root.is_dir()
    assert not workspace.final_root.exists()
