"""Application service for the source-free Gate A recomposition proof."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import write_json_atomic
from er_commons.chunked_conversion.qualification.diagnostics import QualificationError
from er_commons.chunked_conversion.qualification.gate_a_inputs import (
    GateAInputs,
    load_materialized_inputs,
    verify_source_identity,
)
from er_commons.chunked_conversion.qualification.gate_a_profile import (
    SOURCE_CONVERSION_ID,
    aggregate_id,
    build_gate_a_plan,
)
from er_commons.chunked_conversion.qualification.gate_a_projections import (
    attach_gate_a_projections,
)
from er_commons.chunked_conversion.qualification.gate_a_publication import (
    GateAExpectedCompletion,
    artifact_reference,
    child_closure_record,
    publish_completion,
    verify_gate_a_completion,
    write_failure_record,
    write_partition_root,
)
from er_commons.chunked_conversion.qualification.gate_a_report import (
    build_gate_a_report,
    check_completion_orders,
)
from er_commons.chunked_conversion.range_bundle import resume_range_bundles
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.range_graph import DocumentGraph, build_document_graph
from er_commons.chunked_conversion.range_recomposition import (
    PartitionedEvidence,
    partition_document,
)


@dataclass(frozen=True)
class GateARequest:
    """Paths required by the source-free proof; no source PDF path is accepted."""

    source_root: Path
    output_root: Path
    project_root: Path


def run_gate_a(request: GateARequest) -> Path:
    """Run or deeply reuse Gate A without reading the source PDF or running models."""
    source_root = request.source_root.resolve()
    output_root = request.output_root.resolve()
    identity = verify_source_identity(source_root)
    plan = build_gate_a_plan(identity, project_root=request.project_root.resolve())
    aggregate = aggregate_id(plan)
    producer = source_root / "documents/deir_appendix_g1/producer"
    expected_outputs = _source_output_references(producer)
    expected = GateAExpectedCompletion(plan, aggregate, SOURCE_CONVERSION_ID, expected_outputs)
    final = output_root / "aggregates" / aggregate
    reusable = reuse_gate_a_if_complete(final, expected)
    if reusable is not None:
        return reusable

    inputs = load_materialized_inputs(source_root)
    graph = build_document_graph(inputs.document, page_count=2488)
    partition = attach_gate_a_projections(
        partition_document(plan, graph),
        inputs.overlay,
        inputs.alignment,
        inputs.asset_inventory,
    )
    staging = _new_staging(output_root, aggregate)
    range_root = output_root / "range_plans" / plan.plan_id / "ranges"
    try:
        _write_proof(
            staging,
            source_root,
            range_root,
            plan,
            aggregate,
            graph,
            partition,
            inputs,
            expected_outputs,
        )
    except BaseException as error:
        write_failure_record(staging, expected, error, stage="aggregate_proof")
        raise
    completion = final / "records/completion_record.json"
    try:
        final.parent.mkdir(parents=True, exist_ok=True)
        staging.rename(final)
    except BaseException as error:
        write_failure_record(staging, expected, error, stage="aggregate_publication")
        raise
    return completion


def reuse_gate_a_if_complete(final: Path, expected: GateAExpectedCompletion) -> Path | None:
    """Deeply reuse a complete result or reject an ambiguous incomplete final."""
    if (final / "records/completion_record.json").is_file():
        return verify_gate_a_completion(final, expected)
    if not final.exists():
        return None
    raise QualificationError(
        code="incomplete_final",
        stage="gate_a_reuse",
        path=str(final),
        expected="absent or completion-sealed aggregate",
        actual="incomplete final directory",
    )


def _new_staging(output_root: Path, aggregate_id: str) -> Path:
    parent = output_root / "attempts"
    parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f".{aggregate_id}.", dir=parent))


def _write_proof(
    staging: Path,
    source_root: Path,
    range_root: Path,
    plan: RangePlan,
    aggregate: str,
    graph: DocumentGraph,
    partition: PartitionedEvidence,
    inputs: GateAInputs,
    expected_outputs: dict[str, dict[str, Any]],
) -> None:
    externalization = inputs.asset_inventory["image_externalization"]
    write_json_atomic(staging / "records/range_plan.json", plan)
    write_partition_root(staging / "records/partition_root.json", plan, partition, externalization)
    by_id = {shard.range_id: shard for shard in partition.shards}
    selected: list[str] = []

    def select_missing(range_id: str) -> Any:
        selected.append(range_id)
        return by_id[range_id]

    shards = resume_range_bundles(plan, range_root, select_missing)
    order_results = check_completion_orders(
        staging, plan, partition, shards, externalization, expected_outputs
    )
    raw_assets = inputs.asset_inventory.get("assets")
    if not isinstance(raw_assets, list):
        raise ValueError("asset inventory assets are invalid")
    report = build_gate_a_report(
        source_root=source_root,
        source_conversion_id=SOURCE_CONVERSION_ID,
        plan=plan,
        aggregate_id=aggregate,
        graph=graph,
        partition=partition,
        shards=shards,
        overlay=inputs.overlay,
        alignment=inputs.alignment,
        asset_count=len(raw_assets),
        selected_range_ids=tuple(selected),
        order_results=order_results,
        expected_outputs=expected_outputs,
    )
    write_json_atomic(staging / "records/gate_a_report.json", report)
    closure = child_closure_record(range_root, plan)
    write_json_atomic(staging / "records/child_closure.json", closure)
    publish_completion(
        staging,
        GateAExpectedCompletion(plan, aggregate, SOURCE_CONVERSION_ID, expected_outputs),
        expected_outputs,
        child_count=len(shards),
    )


def _source_output_references(producer: Path) -> dict[str, dict[str, Any]]:
    return {
        "document": artifact_reference(producer / "docling/document.json"),
        "heading_overlay": artifact_reference(producer / "docling/heading_overlay.jsonl"),
        "alignment_pages": artifact_reference(producer / "docling/alignment_pages.jsonl"),
        "asset_inventory": artifact_reference(producer / "asset_inventory.json"),
    }
