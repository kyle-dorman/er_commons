"""Completion-last publication for a source-neutral chunk coordinator."""

from __future__ import annotations

from pathlib import Path

from er_commons.artifact_io import (
    artifact_inventory,
    read_json_object,
    sha256_file,
    write_json_atomic,
)
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.runtime.completion import verify_chunked_completion
from er_commons.chunked_conversion.runtime.contracts import (
    ExpectedChunkedConversionCompletion,
    ResourceObservation,
)
from er_commons.document_parsing.content_parsing.conversion_seal import (
    deep_audit_conversion_bundle,
)
from er_commons.document_parsing.content_parsing.evidence import verify_inventory


def publish_chunked_completion(
    run_root: Path,
    run_id: str,
    plan: RangePlan,
    aggregate_observation: ResourceObservation,
    max_aggregate_rss_bytes: int,
    interruption_checkpoint_exists: bool,
) -> Path:
    """Verify the sealed aggregate and publish the coordinator completion last."""
    reference = read_json_object(run_root / "records/aggregate_reference.json")
    aggregate_id = str(reference["conversion_id"])
    aggregate_root = Path(str(reference["path"]))
    deep_audit_conversion_bundle(aggregate_root, aggregate_id)
    write_json_atomic(
        run_root / "records/aggregate_resource_observation.json",
        aggregate_observation.model_dump(mode="json"),
    )
    write_json_atomic(
        run_root / "records/execution_summary.json",
        {
            "schema_version": "er_commons.chunked_conversion_summary.v1",
            "run_id": run_id,
            "plan_id": plan.plan_id,
            "range_count": len(plan.ranges),
            "aggregate_conversion_id": aggregate_id,
            "aggregate_path": aggregate_root.as_posix(),
            "selected_workers": 1,
            "aggregate_rss_limit_bytes": max_aggregate_rss_bytes,
            "interruption_checkpoint_reused": interruption_checkpoint_exists,
        },
    )
    inventory_path = run_root / "records/artifact_inventory.json"
    inventory = artifact_inventory(
        run_root,
        excluded={"records/artifact_inventory.json", "records/completion_record.json"},
    )
    write_json_atomic(inventory_path, inventory)
    verify_inventory(run_root, inventory)
    completion_path = run_root / "records/completion_record.json"
    write_json_atomic(
        completion_path,
        {
            "schema_version": "er_commons.chunked_conversion_completion.v1",
            "run_id": run_id,
            "status": "complete",
            "plan_id": plan.plan_id,
            "aggregate_conversion_id": aggregate_id,
            "artifact_inventory": "records/artifact_inventory.json",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "completion_last": True,
        },
    )
    verify_chunked_completion(
        run_root,
        ExpectedChunkedConversionCompletion(
            run_id=run_id,
            plan_id=plan.plan_id,
            aggregate_conversion_id=aggregate_id,
        ),
    )
    return completion_path


__all__ = ["publish_chunked_completion"]
