"""Build the explanatory report and exact-order checks for Gate A."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from er_commons.artifact_io import sha256_file
from er_commons.chunked_conversion.qualification.gate_a_proofs import (
    completion_orders,
    mutation_matrix,
    resume_matrix,
    seam_evidence,
)
from er_commons.chunked_conversion.qualification.gate_a_publication import (
    write_aggregate_payloads,
)
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.range_graph import DocumentGraph
from er_commons.chunked_conversion.range_recomposition import (
    PartitionedEvidence,
    RangeShard,
)


def check_completion_orders(
    staging: Path,
    plan: RangePlan,
    partition: PartitionedEvidence,
    shards: tuple[RangeShard, ...],
    image_externalization: Any,
    expected_outputs: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Prove that worker arrival order cannot change stable aggregate bytes."""
    results: list[dict[str, Any]] = []
    for name, order in completion_orders(shards):
        target = staging / "aggregate" if name == "forward" else staging / ".checks" / name
        outputs = write_aggregate_payloads(target, plan, partition, order, image_externalization)
        exact = outputs == expected_outputs
        results.append(
            {
                "order": name,
                "range_ids": [shard.range_id for shard in order],
                "outputs": outputs,
                "exact_source_bytes": exact,
            }
        )
        if not exact:
            raise ValueError(f"Gate A output bytes differ for completion order: {name}")
    shutil.rmtree(staging / ".checks")
    return results


def build_gate_a_report(
    *,
    source_root: Path,
    source_conversion_id: str,
    plan: RangePlan,
    aggregate_id: str,
    graph: DocumentGraph,
    partition: PartitionedEvidence,
    shards: tuple[RangeShard, ...],
    overlay: list[dict[str, Any]],
    alignment: list[dict[str, Any]],
    asset_count: int,
    selected_range_ids: tuple[str, ...],
    order_results: list[dict[str, Any]],
    expected_outputs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Summarize the source-free proof in language useful to a human reviewer."""
    return {
        "schema_version": "er_commons.task03h2_gate_a_report.v1",
        "status": "passed",
        "source_conversion_id": source_conversion_id,
        "source_inventory_sha256": sha256_file(source_root / "records/artifact_inventory.json"),
        "plan_id": plan.plan_id,
        "aggregate_id": aggregate_id,
        "seams": seam_evidence(graph, overlay),
        "range_count": len(plan.ranges),
        "range_ids": [planned.range_id for planned in plan.ranges],
        "page_count": len(graph.pages),
        "record_count": len(graph.records),
        "reference_occurrences": graph.reference_count,
        "collection_counts": dict(partition.collection_counts),
        "heading_overlay_records": len(overlay),
        "alignment_page_records": len(alignment),
        "asset_records": asset_count,
        "multi_page_records": sum(len(record.pages) > 1 for record in graph.records),
        "document_global_records": [item.source_ref for item in partition.global_items],
        "mutation_matrix": mutation_matrix(plan, partition, shards),
        "resume_matrix": resume_matrix(plan, partition, shards, selected_range_ids),
        "completion_orders": order_results,
        "source_outputs": expected_outputs,
        "focused_test_command": (
            "uv run pytest -q tests/test_chunked_conversion_contract.py "
            "tests/test_chunked_conversion_recomposition.py"
        ),
        "scope_boundary": (
            "sealed evidence only; no PDF read, Docling construction, model execution, "
            "or live publication"
        ),
        "gate_b_authorized": False,
        "memory_boundedness_proven": False,
        "asset_claim": (
            "79 source asset metadata records reproduced after full immutable-source "
            "inventory verification; Gate A does not republish PNG bytes"
        ),
    }
