from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from er_commons.artifact_io import (
    artifact_inventory,
    read_json_object,
    sha256_file,
    write_json_atomic,
)
from er_commons.chunked_conversion.qualification.diagnostics import QualificationError
from er_commons.chunked_conversion.qualification.gate_a_application import (
    reuse_gate_a_if_complete,
)
from er_commons.chunked_conversion.qualification.gate_a_publication import (
    GateAExpectedCompletion,
    artifact_reference,
    child_closure_record,
    verify_gate_a_completion,
    write_failure_record,
)
from er_commons.chunked_conversion.range_bundle import publish_range_bundle
from er_commons.chunked_conversion.range_contract import (
    OverlapPolicy,
    PageInterval,
    RangeDefinition,
    RangePlan,
    RangePlanInputs,
    SourceIdentity,
    build_range_plan,
)
from er_commons.chunked_conversion.range_graph import build_document_graph
from er_commons.chunked_conversion.range_recomposition import partition_document


def _plan() -> RangePlan:
    return build_range_plan(
        RangePlanInputs(
            source=SourceIdentity(
                source_id="fixture", sha256="a" * 64, byte_size=1, physical_page_count=1
            ),
            sealed_source_release_identity="release",
            converter_identity="converter",
            package_identity="packages",
            model_identity="models",
            adapter_identity="adapter",
            page_evidence_contract_identity="evidence",
            range_conversion_identity="child-code",
            range_planner_identity="planner-code",
            aggregate_merge_identity="aggregate-code",
            target_range_size=1,
            hard_maximum=1,
            overlap_policy=OverlapPolicy(max_left_pages=0, max_right_pages=0),
            ranges=(
                RangeDefinition(
                    core=PageInterval(start=1, end=1),
                    read=PageInterval(start=1, end=1),
                ),
            ),
            aggregate_output_schema_identity="outputs",
            global_interpretation_policy_identity="global",
        )
    )


def _sealed_result(tmp_path: Path) -> tuple[Path, GateAExpectedCompletion]:
    plan = _plan()
    document = {
        "body": {"self_ref": "#/body", "children": []},
        "furniture": {"self_ref": "#/furniture", "children": []},
        "groups": [],
        "texts": [],
        "pictures": [],
        "tables": [],
        "key_value_items": [],
        "form_items": [],
        "pages": {"1": {"page_no": 1, "size": {"width": 1, "height": 1}}},
    }
    partition = partition_document(plan, build_document_graph(document, page_count=1))
    shard = replace(partition.shards[0], alignment_pages=({"page_no": 1},))
    output = tmp_path / "output"
    range_root = output / "range_plans" / plan.plan_id / "ranges"
    publish_range_bundle(range_root, plan, shard)
    root = output / "aggregates" / "aggregate"
    write_json_atomic(root / "aggregate/docling/document.json", {"document": True})
    (root / "aggregate/docling/heading_overlay.jsonl").write_text(
        '{"heading":true}\n', encoding="utf-8"
    )
    (root / "aggregate/docling/alignment_pages.jsonl").write_text(
        '{"page_no":1}\n', encoding="utf-8"
    )
    write_json_atomic(root / "aggregate/asset_inventory.json", {"assets": []})
    outputs = {
        "document": artifact_reference(root / "aggregate/docling/document.json"),
        "heading_overlay": artifact_reference(root / "aggregate/docling/heading_overlay.jsonl"),
        "alignment_pages": artifact_reference(root / "aggregate/docling/alignment_pages.jsonl"),
        "asset_inventory": artifact_reference(root / "aggregate/asset_inventory.json"),
    }
    expected = GateAExpectedCompletion(plan, "aggregate", "source", outputs)
    write_json_atomic(root / "payload.json", {"stable": True})
    write_json_atomic(root / "records/child_closure.json", child_closure_record(range_root, plan))
    inventory = artifact_inventory(
        root,
        excluded={"records/artifact_inventory.json", "records/completion_record.json"},
    )
    inventory_path = root / "records/artifact_inventory.json"
    write_json_atomic(inventory_path, inventory)
    write_json_atomic(
        root / "records/completion_record.json",
        {
            "schema_version": "er_commons.task03h2_gate_a_completion.v1",
            "status": "complete",
            "plan_id": expected.plan_id,
            "aggregate_id": expected.aggregate_id,
            "source_conversion_id": expected.source_conversion_id,
            "completion_last": True,
            "artifact_inventory": "records/artifact_inventory.json",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "aggregate_outputs": outputs,
            "child_count": 1,
        },
    )
    return root, expected


def test_gate_a_reuse_requires_exact_lineage_closure_and_inventory(tmp_path: Path) -> None:
    root, expected = _sealed_result(tmp_path)
    assert verify_gate_a_completion(root, expected).name == "completion_record.json"

    transplanted = replace(expected, aggregate_id="different")
    with pytest.raises(QualificationError, match="completion_identity"):
        verify_gate_a_completion(root, transplanted)

    (root / "payload.json").write_text('{"stable":false}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="inventory_file_size|inventory_file_sha256"):
        verify_gate_a_completion(root, expected)


def test_gate_a_failure_record_preserves_first_context(tmp_path: Path) -> None:
    _, expected = _sealed_result(tmp_path)
    attempt = tmp_path / "attempt"
    first = write_failure_record(attempt, expected, RuntimeError("first"), stage="proof")
    second = write_failure_record(attempt, expected, RuntimeError("second"), stage="rename")
    assert first == second
    assert read_json_object(first)["error"] == "first"


def test_gate_a_reuse_rejects_self_consistent_reseal_with_wrong_output(
    tmp_path: Path,
) -> None:
    root, expected = _sealed_result(tmp_path)
    write_json_atomic(root / "aggregate/docling/document.json", {"document": False})
    inventory = artifact_inventory(
        root,
        excluded={"records/artifact_inventory.json", "records/completion_record.json"},
    )
    inventory_path = root / "records/artifact_inventory.json"
    write_json_atomic(inventory_path, inventory)
    completion_path = root / "records/completion_record.json"
    completion = read_json_object(completion_path)
    completion["artifact_inventory_sha256"] = sha256_file(inventory_path)
    write_json_atomic(completion_path, completion)

    with pytest.raises(QualificationError, match="aggregate_output_bytes"):
        verify_gate_a_completion(root, expected)


def test_gate_a_reuse_rejects_unknown_completion_field(tmp_path: Path) -> None:
    root, expected = _sealed_result(tmp_path)
    path = root / "records/completion_record.json"
    completion = read_json_object(path)
    completion["unexpected"] = True
    write_json_atomic(path, completion)
    with pytest.raises(ValueError, match="extra_forbidden"):
        verify_gate_a_completion(root, expected)


def test_gate_a_application_reuses_complete_and_rejects_incomplete_final(
    tmp_path: Path,
) -> None:
    root, expected = _sealed_result(tmp_path)
    assert reuse_gate_a_if_complete(root, expected) is not None
    incomplete = tmp_path / "incomplete"
    incomplete.mkdir()
    with pytest.raises(QualificationError, match="incomplete_final"):
        reuse_gate_a_if_complete(incomplete, expected)
