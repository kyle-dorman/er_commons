"""Write and verify the durable outputs of the source-free Gate A proof."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from er_commons.artifact_io import (
    artifact_inventory,
    atomic_text_writer,
    read_json_object,
    sha256_file,
    write_json_atomic,
    write_json_atomic_streaming,
    write_jsonl,
)
from er_commons.chunked_conversion.qualification.diagnostics import require
from er_commons.chunked_conversion.range_bundle import verify_range_bundle
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.range_recomposition import (
    PartitionedEvidence,
    RangeItem,
    RangeShard,
    recompose_document,
)
from er_commons.document_parsing.content_parsing.evidence import verify_inventory


@dataclass(frozen=True)
class GateAExpectedCompletion:
    """Identity fields that an existing Gate A result must match exactly."""

    plan: RangePlan
    aggregate_id: str
    source_conversion_id: str
    aggregate_outputs: dict[str, dict[str, Any]]

    @property
    def plan_id(self) -> str:
        """Expose the durable plan identity used by the completion record."""
        return self.plan.plan_id


class GateACompletion(BaseModel):
    """Strict completion-last record for one source-free Gate A aggregate."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: Literal["er_commons.task03h2_gate_a_completion.v1"]
    status: Literal["complete"]
    plan_id: str
    aggregate_id: str
    source_conversion_id: str
    artifact_inventory: Literal["records/artifact_inventory.json"]
    artifact_inventory_sha256: str
    aggregate_outputs: dict[str, dict[str, Any]]
    child_count: int
    completion_last: Literal[True]


def range_item_record(item: RangeItem) -> dict[str, Any]:
    """Serialize one partition item without leaking dataclass implementation details."""
    return {
        "collection": item.collection,
        "source_index": item.source_index,
        "local_ref": item.local_ref,
        "source_ref": item.source_ref,
        "pages": list(item.pages),
        "value": item.value,
    }


def artifact_reference(path: Path) -> dict[str, Any]:
    """Return the byte identity used by Gate A's exact-output oracle."""
    return {"byte_size": path.stat().st_size, "sha256": sha256_file(path)}


def write_aggregate_payloads(
    root: Path,
    plan: RangePlan,
    partition: PartitionedEvidence,
    shards: tuple[RangeShard, ...],
    image_externalization: Any,
) -> dict[str, dict[str, Any]]:
    """Recompose and write the four stable G1 outputs in canonical order."""
    document = recompose_document(plan, partition, shards)
    canonical = sorted(shards, key=lambda shard: shard.core_pages[0])
    overlay = sorted(
        (record for shard in canonical for record in shard.heading_overlay),
        key=lambda record: str(record["raw_self_ref"]),
    )
    alignment = sorted(
        (record for shard in canonical for record in shard.alignment_pages),
        key=lambda record: int(record["page_no"]),
    )
    assets = sorted(
        (record for shard in canonical for record in shard.assets),
        key=lambda record: int(str(record["raw_object_ref"]).rsplit("/", 1)[1]),
    )
    write_json_atomic_streaming(root / "docling/document.json", document)
    write_jsonl(root / "docling/heading_overlay.jsonl", overlay)
    with atomic_text_writer(root / "docling/alignment_pages.jsonl") as stream:
        for record in alignment:
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            stream.write("\n")
    write_json_atomic(
        root / "asset_inventory.json",
        {"assets": assets, "image_externalization": image_externalization},
    )
    return {
        "document": artifact_reference(root / "docling/document.json"),
        "heading_overlay": artifact_reference(root / "docling/heading_overlay.jsonl"),
        "alignment_pages": artifact_reference(root / "docling/alignment_pages.jsonl"),
        "asset_inventory": artifact_reference(root / "asset_inventory.json"),
    }


def write_partition_root(
    path: Path,
    plan: RangePlan,
    partition: PartitionedEvidence,
    image_externalization: Any,
) -> None:
    """Record the document-global partition state required for reconstruction."""
    write_json_atomic_streaming(
        path,
        {
            "schema_version": "er_commons.docling_partition_root.v1",
            "plan_id": plan.plan_id,
            "root": partition.root,
            "collection_counts": dict(partition.collection_counts),
            "global_items": [range_item_record(item) for item in partition.global_items],
            "image_externalization": image_externalization,
        },
    )


def publish_completion(
    staging: Path,
    expected: GateAExpectedCompletion,
    aggregate_outputs: dict[str, dict[str, Any]],
    *,
    child_count: int,
) -> None:
    """Seal all staged bytes, verify them, then publish completion last."""
    inventory_path = staging / "records/artifact_inventory.json"
    inventory = artifact_inventory(
        staging,
        excluded={"records/artifact_inventory.json", "records/completion_record.json"},
    )
    write_json_atomic(inventory_path, inventory)
    verify_inventory(staging, inventory)
    write_json_atomic(
        staging / "records/completion_record.json",
        {
            "schema_version": "er_commons.task03h2_gate_a_completion.v1",
            "status": "complete",
            "plan_id": expected.plan_id,
            "aggregate_id": expected.aggregate_id,
            "source_conversion_id": expected.source_conversion_id,
            "artifact_inventory": "records/artifact_inventory.json",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "aggregate_outputs": aggregate_outputs,
            "child_count": child_count,
            "completion_last": True,
        },
    )


def write_failure_record(
    staging: Path,
    expected: GateAExpectedCompletion,
    error: BaseException,
    *,
    stage: str,
) -> Path:
    """Retain the first contextual aggregate failure without publishing completion."""
    path = staging / "records/failure.json"
    if path.exists():
        return path
    write_json_atomic(
        path,
        {
            "schema_version": "er_commons.task03h2_gate_a_failure.v1",
            "status": "failed",
            "stage": stage,
            "plan_id": expected.plan_id,
            "aggregate_id": expected.aggregate_id,
            "source_conversion_id": expected.source_conversion_id,
            "error_type": type(error).__name__,
            "error": str(error),
            "completion_published": False,
            "recovery": "repair the cause and rerun; verified child bundles are reusable",
        },
    )
    return path


def verify_gate_a_completion(root: Path, expected: GateAExpectedCompletion) -> Path:
    """Deep-verify a completed Gate A result and its exact semantic identity."""
    completion_path = root / "records/completion_record.json"
    completion = GateACompletion.model_validate_json(completion_path.read_bytes())
    checks = {
        "schema_version": "er_commons.task03h2_gate_a_completion.v1",
        "status": "complete",
        "plan_id": expected.plan_id,
        "aggregate_id": expected.aggregate_id,
        "source_conversion_id": expected.source_conversion_id,
        "completion_last": True,
        "artifact_inventory": "records/artifact_inventory.json",
        "aggregate_outputs": expected.aggregate_outputs,
        "child_count": len(expected.plan.ranges),
    }
    for field, wanted in checks.items():
        require(
            getattr(completion, field) == wanted,
            "completion_identity",
            stage="gate_a_reuse",
            path=f"{completion_path}.{field}",
            expected=wanted,
            actual=getattr(completion, field),
        )
    inventory_path = root / "records/artifact_inventory.json"
    require(
        completion.artifact_inventory_sha256 == sha256_file(inventory_path),
        "inventory_digest",
        stage="gate_a_reuse",
        path=str(inventory_path),
        expected=completion.artifact_inventory_sha256,
        actual=sha256_file(inventory_path),
    )
    verify_inventory(root, read_json_object(inventory_path))
    actual_outputs = {
        "document": artifact_reference(root / "aggregate/docling/document.json"),
        "heading_overlay": artifact_reference(root / "aggregate/docling/heading_overlay.jsonl"),
        "alignment_pages": artifact_reference(root / "aggregate/docling/alignment_pages.jsonl"),
        "asset_inventory": artifact_reference(root / "aggregate/asset_inventory.json"),
    }
    require(
        actual_outputs == expected.aggregate_outputs,
        "aggregate_output_bytes",
        stage="gate_a_reuse",
        path=str(root / "aggregate"),
        expected=expected.aggregate_outputs,
        actual=actual_outputs,
    )
    require(
        root.name == expected.aggregate_id,
        "aggregate_root_identity",
        stage="gate_a_reuse",
        path=str(root),
        expected=expected.aggregate_id,
        actual=root.name,
    )
    range_root = root.parent.parent / "range_plans" / expected.plan_id / "ranges"
    for planned in expected.plan.ranges:
        verify_range_bundle(range_root / planned.range_id, expected.plan, planned.range_id)
    closure_path = root / "records/child_closure.json"
    require(
        read_json_object(closure_path) == child_closure_record(range_root, expected.plan),
        "child_closure",
        stage="gate_a_reuse",
        path=str(closure_path),
        expected="exact verified planned-child closure",
        actual="different closure",
    )
    return completion_path


def child_closure_record(range_root: Path, plan: RangePlan) -> dict[str, Any]:
    """Return exact completion and inventory digests for every planned child."""
    children = []
    for planned in plan.ranges:
        records = range_root / planned.range_id / "records"
        children.append(
            {
                "range_id": planned.range_id,
                "completion_sha256": sha256_file(records / "completion_record.json"),
                "inventory_sha256": sha256_file(records / "artifact_inventory.json"),
            }
        )
    return {"children": children}
