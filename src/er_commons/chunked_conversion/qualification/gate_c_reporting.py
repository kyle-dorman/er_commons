"""Gate C equivalence, resource disposition, and terminal run publication."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from er_commons.artifact_io import (
    artifact_inventory,
    read_json_object,
    sha256_file,
    write_json_atomic,
)
from er_commons.chunked_conversion.qualification.completion_validation import (
    verify_gate_c_completion,
)
from er_commons.chunked_conversion.qualification.contracts import (
    ExpectedGateCCompletion,
    ResourceObservation,
)
from er_commons.chunked_conversion.qualification.gate_c_inputs import SOURCE_ID
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.document_parsing.content_parsing.conversion_seal import (
    deep_audit_conversion_bundle,
)
from er_commons.document_parsing.content_parsing.evidence import verify_inventory


def select_concurrency(
    range_observations: list[dict[str, Any]],
    aggregate_observation: ResourceObservation,
    *,
    max_aggregate_rss_bytes: int,
) -> dict[str, Any]:
    """Select one worker unless two measured peaks fit below the accepted ceiling."""
    peaks = [item.get("process_tree_peak_rss_bytes") for item in range_observations]
    if not peaks or not all(isinstance(item, int) and item > 0 for item in peaks):
        raise ValueError("range process-tree observations are incomplete")
    range_peak = max(item for item in peaks if isinstance(item, int))
    aggregate_peak = aggregate_observation.process_tree_peak_rss_bytes
    if aggregate_peak < 1:
        raise ValueError("aggregate process-tree observation is incomplete")
    projected_two_worker_peak = 2 * range_peak
    ceiling = min(max_aggregate_rss_bytes, 10 * 1024**3)
    if projected_two_worker_peak <= ceiling:
        raise ValueError(
            "sequential measurements leave potential two-worker headroom; "
            "run the bounded two-worker qualification before completing Gate C"
        )
    return {
        "selected_workers": 1,
        "two_worker_executed": False,
        "range_process_tree_peak_rss_bytes": range_peak,
        "aggregate_process_tree_peak_rss_bytes": aggregate_peak,
        "projected_two_worker_peak_rss_bytes": projected_two_worker_peak,
        "accepted_concurrent_ceiling_bytes": ceiling,
        "reason": "two measured range peaks would exceed the accepted memory ceiling",
    }


def publish_gate_c_completion(
    *,
    run_root: Path,
    run_id: str,
    source_root: Path,
    plan: RangePlan,
    aggregate_observation: ResourceObservation,
    max_aggregate_rss_bytes: int,
    interruption_checkpoint_exists: bool,
) -> Path:
    """Verify exact G1 outputs and publish the Gate C completion record last."""
    aggregate_reference = read_json_object(run_root / "records/aggregate_reference.json")
    aggregate_id = str(aggregate_reference["conversion_id"])
    aggregate_root = run_root / "aggregate" / aggregate_id
    sealed = deep_audit_conversion_bundle(aggregate_root, aggregate_id)
    comparison = compare_with_sealed_g1(source_root, aggregate_root)
    write_json_atomic(run_root / "records/aggregate_comparison.json", comparison)
    write_json_atomic(
        run_root / "records/aggregate_resource_observation.json",
        aggregate_observation.model_dump(mode="json"),
    )
    write_json_atomic(
        run_root / "records/downstream_compatibility.json",
        downstream_compatibility(source_root, sealed.output.document_payload),
    )
    range_observations = [
        read_json_object(run_root / "records" / f"resource_{planned.range_id}.json")
        for planned in plan.ranges
    ]
    write_json_atomic(
        run_root / "records/gate_c_report.json",
        {
            "schema_version": "er_commons.task03h2_gate_c_report.v1",
            "run_id": run_id,
            "status": "conversion_qualification_passed_pending_downstream",
            "plan_id": plan.plan_id,
            "range_count": len(plan.ranges),
            "aggregate_conversion_id": aggregate_id,
            "checks": {
                "document_driven_plan": True,
                "all_children_independently_sealed": True,
                "interruption_resume_zero_recompute": interruption_checkpoint_exists,
                "global_recomposition_exact": comparison["all_stable_outputs_exact"],
                "downstream_input_interface_exact": True,
                "full_downstream_qualification_complete": False,
                "g2_not_inspected": True,
            },
            "concurrency_selection": select_concurrency(
                range_observations,
                aggregate_observation,
                max_aggregate_rss_bytes=max_aggregate_rss_bytes,
            ),
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
            "schema_version": "er_commons.task03h2_gate_c_completion.v1",
            "run_id": run_id,
            "status": "complete",
            "plan_id": plan.plan_id,
            "aggregate_conversion_id": aggregate_id,
            "artifact_inventory": "records/artifact_inventory.json",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "completion_last": True,
        },
    )
    verify_gate_c_completion(
        run_root,
        ExpectedGateCCompletion(
            run_id=run_id,
            plan_id=plan.plan_id,
            aggregate_conversion_id=aggregate_id,
        ),
    )
    return completion_path


def compare_with_sealed_g1(source_root: Path, aggregate_root: Path) -> dict[str, Any]:
    """Require byte-exact stable outputs and warning/status equivalence."""
    source_producer = source_root / "documents" / SOURCE_ID / "producer"
    aggregate_producer = aggregate_root / "documents" / SOURCE_ID / "producer"
    relative_paths = (
        "docling/document.json",
        "docling/heading_overlay.jsonl",
        "docling/alignment_pages.jsonl",
        "asset_inventory.json",
    )
    rows = []
    for relative in relative_paths:
        expected = source_producer / relative
        actual = aggregate_producer / relative
        rows.append(
            {
                "path": relative,
                "expected_sha256": sha256_file(expected),
                "actual_sha256": sha256_file(actual),
                "expected_bytes": expected.stat().st_size,
                "actual_bytes": actual.stat().st_size,
                "exact": expected.read_bytes() == actual.read_bytes(),
            }
        )
    if not all(row["exact"] for row in rows):
        raise ValueError(f"aggregate stable G1 output differs: {rows}")
    source_observation = read_json_object(source_producer / "docling/conversion_observation.json")
    aggregate_observation = read_json_object(
        aggregate_producer / "docling/conversion_observation.json"
    )
    warning_fields = (
        "captured_python_warnings",
        "source_manifest_warnings",
        "errors",
        "raw_status",
        "status",
        "expected_physical_pages",
        "converted_physical_pages",
        "page_coverage_complete",
        "asset_count",
    )
    if not all(
        source_observation.get(field) == aggregate_observation.get(field)
        for field in warning_fields
    ):
        raise ValueError("aggregate warning/status projection differs from sealed G1")
    return {
        "schema_version": "er_commons.task03h2_gate_c_aggregate_comparison.v1",
        "all_stable_outputs_exact": True,
        "warning_status_projection_exact": True,
        "warning_fields": list(warning_fields),
        "outputs": rows,
    }


def downstream_compatibility(source_root: Path, document: dict[str, Any]) -> dict[str, Any]:
    """Require the exact immutable document payload consumed by descendants."""
    sealed_document = read_json_object(
        source_root / "documents" / SOURCE_ID / "producer/docling/document.json"
    )
    if document != sealed_document:
        raise ValueError("downstream compatibility document differs")
    return {
        "schema_version": "er_commons.task03h2_gate_c_downstream_compatibility.v1",
        "status": "input_interface_exact_pending_full_qualification",
        "interface": "SealedConversion.output.document_payload",
        "document_payload_exact": True,
        "routing_table_record_hierarchy_document_consumers": "byte-identical accepted input",
        "descendant_reexecution": False,
        "reason": "full isolated downstream execution is a separate required Gate C substage",
    }


__all__ = ["publish_gate_c_completion", "select_concurrency"]
