from __future__ import annotations

import copy
import random
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from er_commons.chunked_conversion.range_bundle import (
    RangeBundleError,
    publish_range_bundle,
    resume_range_bundles,
    verify_range_bundle,
)
from er_commons.chunked_conversion.range_contract import (
    OverlapOwner,
    OverlapPolicy,
    PageInterval,
    RangeDefinition,
    RangePlanInputs,
    SourceIdentity,
    build_range_plan,
)
from er_commons.chunked_conversion.range_graph import RangeGraphError, build_document_graph
from er_commons.chunked_conversion.range_recomposition import (
    RangeRecompositionError,
    partition_document,
    recompose_document,
)


def _plan() -> Any:
    source = SourceIdentity(
        source_id="fixture",
        sha256="a" * 64,
        byte_size=1234,
        physical_page_count=4,
    )
    return build_range_plan(
        RangePlanInputs(
            source=source,
            sealed_source_release_identity="sealed-release",
            converter_identity="converter",
            package_identity="packages",
            model_identity="models",
            adapter_identity="adapter",
            page_evidence_contract_identity="page-evidence",
            range_conversion_identity="range-conversion",
            range_planner_identity="planner",
            aggregate_merge_identity="merge",
            target_range_size=2,
            hard_maximum=2,
            overlap_policy=OverlapPolicy(max_left_pages=1, max_right_pages=1),
            ranges=(
                RangeDefinition(
                    core=PageInterval(start=1, end=2),
                    read=PageInterval(start=1, end=3),
                    overlap_owners=(OverlapOwner(page=3, owner_core=PageInterval(start=3, end=4)),),
                ),
                RangeDefinition(
                    core=PageInterval(start=3, end=4),
                    read=PageInterval(start=2, end=4),
                    overlap_owners=(OverlapOwner(page=2, owner_core=PageInterval(start=1, end=2)),),
                ),
            ),
            aggregate_output_schema_identity="aggregate-output",
            global_interpretation_policy_identity="global-policy",
        )
    )


def _document() -> dict[str, Any]:
    bbox = {"l": 0.0, "t": 1.0, "r": 1.0, "b": 0.0, "coord_origin": "BOTTOMLEFT"}
    return {
        "schema_name": "DoclingDocument",
        "version": "1.0.0",
        "name": "fixture",
        "origin": None,
        "furniture": {"self_ref": "#/furniture", "children": []},
        "body": {
            "self_ref": "#/body",
            "children": [
                {"$ref": "#/groups/0"},
                {"$ref": "#/groups/1"},
                {"$ref": "#/tables/0"},
            ],
        },
        "groups": [
            {
                "self_ref": "#/groups/0",
                "parent": {"$ref": "#/body"},
                "children": [{"$ref": "#/texts/0"}, {"$ref": "#/texts/1"}],
                "name": "group",
                "label": "section",
            },
            {
                "self_ref": "#/groups/1",
                "parent": {"$ref": "#/body"},
                "children": [],
                "name": "empty-global",
                "label": "key_value_area",
            },
        ],
        "texts": [
            {
                "self_ref": "#/texts/0",
                "parent": {"$ref": "#/groups/0"},
                "label": "text",
                "prov": [{"page_no": 1, "bbox": bbox, "charspan": [0, 4]}],
                "orig": "left",
                "text": "left",
            },
            {
                "self_ref": "#/texts/1",
                "parent": {"$ref": "#/groups/0"},
                "label": "text",
                "prov": [
                    {"page_no": 2, "bbox": bbox, "charspan": [0, 3]},
                    {"page_no": 3, "bbox": bbox, "charspan": [3, 8]},
                ],
                "orig": "seam",
                "text": "seam",
            },
            {
                "self_ref": "#/texts/2",
                "parent": {"$ref": "#/tables/0"},
                "label": "caption",
                "prov": [{"page_no": 4, "bbox": bbox, "charspan": [0, 7]}],
                "orig": "caption",
                "text": "caption",
            },
        ],
        "pictures": [],
        "tables": [
            {
                "self_ref": "#/tables/0",
                "parent": {"$ref": "#/body"},
                "children": [{"$ref": "#/texts/2"}],
                "captions": [{"$ref": "#/texts/2"}],
                "footnotes": [],
                "references": [],
                "prov": [{"page_no": 4, "bbox": bbox, "charspan": [0, 0]}],
                "label": "table",
                "data": {"table_cells": [{"ref": {"$ref": "#/groups/0"}}]},
            }
        ],
        "key_value_items": [],
        "form_items": [],
        "pages": {
            str(page): {"page_no": page, "size": {"width": 10.0, "height": 20.0}}
            for page in range(1, 5)
        },
    }


def _evidence(plan: Any, document: dict[str, Any]) -> Any:
    partition = partition_document(plan, build_document_graph(document, page_count=4))
    return replace(
        partition,
        shards=tuple(
            replace(
                shard,
                alignment_pages=tuple({"page_no": page} for page in shard.core_pages),
                overlap_evidence=tuple(
                    replace(evidence, alignment_page={"page_no": evidence.page})
                    for evidence in shard.overlap_evidence
                ),
            )
            for shard in partition.shards
        ),
    )


def test_partition_recomposes_exact_document_in_any_completion_order() -> None:
    plan = _plan()
    document = _document()
    evidence = _evidence(plan, document)
    assert [item.source_ref for item in evidence.global_items] == ["#/groups/1"]
    orders = [list(evidence.shards), list(reversed(evidence.shards))]
    shuffled = list(evidence.shards)
    random.Random(42).shuffle(shuffled)
    orders.append(shuffled)
    for shards in orders:
        assert recompose_document(plan, evidence, shards) == document


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "reordered", "identity"])
def test_recomposition_rejects_contextual_range_corruption(mutation: str) -> None:
    plan = _plan()
    document = _document()
    evidence = _evidence(plan, document)
    shards = list(evidence.shards)
    range_id = shards[0].range_id
    if mutation == "missing":
        shards.pop()
    elif mutation == "duplicate":
        shards.append(shards[0])
    elif mutation == "reordered":
        shards[0] = replace(shards[0], items=tuple(reversed(shards[0].items)))
    else:
        shards[0] = replace(shards[0], plan_id="foreign-plan")
    with pytest.raises(RangeRecompositionError) as caught:
        recompose_document(plan, evidence, shards)
    assert plan.plan_id in str(caught.value)
    assert "path=" in str(caught.value)
    if mutation != "missing":
        assert range_id in str(caught.value)


def test_recomposition_rejects_overlap_semantic_mismatch() -> None:
    plan = _plan()
    evidence = _evidence(plan, _document())
    first = evidence.shards[0]
    changed = replace(
        first,
        overlap_evidence=(
            replace(first.overlap_evidence[0], record_digests=()),
            *first.overlap_evidence[1:],
        ),
    )
    with pytest.raises(RangeRecompositionError, match="overlap_semantic_identity"):
        recompose_document(plan, evidence, (changed, *evidence.shards[1:]))


@pytest.mark.parametrize("mutation", ["duplicate_child", "wrong_parent"])
def test_graph_rejects_nonreciprocal_tree(mutation: str) -> None:
    document = copy.deepcopy(_document())
    if mutation == "duplicate_child":
        document["body"]["children"].append({"$ref": "#/groups/0"})
    else:
        document["texts"][0]["parent"] = {"$ref": "#/body"}
    with pytest.raises(RangeGraphError):
        build_document_graph(document, page_count=4)


def test_bundle_seal_detects_byte_corruption_with_range_and_path(tmp_path: Path) -> None:
    plan = _plan()
    evidence = _evidence(plan, _document())
    shard = evidence.shards[0]
    root = publish_range_bundle(tmp_path, plan, shard)
    assert verify_range_bundle(root, plan, shard.range_id) == shard
    with (root / "shard.json").open("a", encoding="utf-8") as stream:
        stream.write(" ")
    with pytest.raises(RangeBundleError) as caught:
        verify_range_bundle(root, plan, shard.range_id)
    assert shard.range_id in str(caught.value)
    assert str(root) in str(caught.value)


def test_bundle_publish_rejects_same_identity_with_different_proposed_shard(
    tmp_path: Path,
) -> None:
    plan = _plan()
    evidence = _evidence(plan, _document())
    shard = evidence.shards[0]
    publish_range_bundle(tmp_path, plan, shard)
    first_item = shard.items[0]
    changed_item = replace(first_item, value={**first_item.value, "text": "different"})
    changed = replace(shard, items=(changed_item, *shard.items[1:]))

    with pytest.raises(RangeBundleError) as caught:
        publish_range_bundle(tmp_path, plan, changed)

    message = str(caught.value)
    assert shard.range_id in message
    assert "path=" in message
    assert "invariant=existing_bundle_collision" in message


def test_resume_executes_only_missing_ranges(tmp_path: Path) -> None:
    plan = _plan()
    evidence = _evidence(plan, _document())
    publish_range_bundle(tmp_path, plan, evidence.shards[0])
    by_id = {shard.range_id: shard for shard in evidence.shards}
    calls: list[str] = []

    def execute(range_id: str) -> Any:
        calls.append(range_id)
        return by_id[range_id]

    resumed = resume_range_bundles(plan, tmp_path, execute)
    assert resumed == evidence.shards
    assert calls == [evidence.shards[1].range_id]
