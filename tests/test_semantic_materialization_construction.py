"""Focused tests for pure Task 03E.4 semantic construction."""

from __future__ import annotations

import copy

import pytest

from er_commons.semantic_materialization.aliases import (
    AliasSeed,
    build_appendix_p_alias_seeds,
    build_target_aliases,
    prefer_reconciled_toc_evidence,
)
from er_commons.semantic_materialization.bridge import BridgeItem, build_cross_producer_bridge
from er_commons.semantic_materialization.comparison import compare_baseline_collections
from er_commons.semantic_materialization.config import SemanticExpectations
from er_commons.semantic_materialization.errors import SemanticMaterializationInvariantError
from er_commons.semantic_materialization.page_labels import build_page_label_observations
from er_commons.semantic_materialization.producer_evidence import (
    ProducerEvidence,
    aligned_stable_key_maps,
)
from er_commons.semantic_materialization.sections import build_semantic_sections
from er_commons.semantic_materialization.support import _bridge_payload
from er_commons.semantic_structure import SemanticContractError

OLD_ID = "exv1-" + "a" * 64
NEW_ID = "exv1-" + "b" * 64
DOCUMENT_ID = f"{NEW_ID}/document/deir_appendix_p"
REF = {"path": "artifacts/item_features.jsonl", "sha256": "c" * 64}


def test_bridge_is_built_from_complete_independent_correspondence() -> None:
    items = [
        BridgeItem("1" * 64, "#/texts/0", "#/texts/0"),
        BridgeItem("2" * 64, "#/texts/1", "#/texts/1"),
    ]
    rows, evidence = build_cross_producer_bridge(
        items,
        hierarchy_producer_run_id="prv1-" + "3" * 64,
        baseline_producer_run_id="prv1-" + "4" * 64,
        canonical_block_by_key={"1" * 64: f"{NEW_ID}/block/deir_appendix_p/blk000001"},
        disposition_by_key={"2" * 64: "canonical_table_replacement_descendant"},
    )

    assert [row["status"] for row in rows] == ["mapped", "permitted_unmapped"]
    assert rows[1]["canonical_record_ids"] == []
    assert evidence["1" * 64].baseline_raw_pointer == "#/texts/0"
    with pytest.raises(SemanticContractError, match="coverage differs"):
        build_cross_producer_bridge(
            items,
            hierarchy_producer_run_id="prv1-" + "3" * 64,
            baseline_producer_run_id="prv1-" + "4" * 64,
            canonical_block_by_key={},
            disposition_by_key={"2" * 64: "canonical_table_replacement_descendant"},
        )


def test_producer_text_alignment_accepts_unique_subpoint_bbox_drift() -> None:
    baseline = _docling_text_document(_docling_text("#/texts/0", left=10.0, right=30.0))
    hierarchy = _docling_text_document(_docling_text("#/texts/7", left=10.2, right=29.9))

    baseline_keys, hierarchy_keys = aligned_stable_key_maps(baseline, hierarchy)

    assert baseline_keys["#/texts/0"] == hierarchy_keys["#/texts/7"]


def test_producer_text_alignment_rejects_ambiguous_bbox_drift() -> None:
    baseline = _docling_text_document(
        _docling_text("#/texts/0", left=10.0, right=30.0),
        _docling_text("#/texts/1", left=10.1, right=30.1),
    )
    hierarchy = _docling_text_document(
        _docling_text("#/texts/7", left=10.2, right=30.2),
        _docling_text("#/texts/8", left=10.3, right=30.3),
    )

    with pytest.raises(SemanticMaterializationInvariantError, match="align uniquely"):
        aligned_stable_key_maps(baseline, hierarchy)


def test_producer_text_alignment_preserves_exact_duplicates_by_parent_collection() -> None:
    picture_item = _docling_text("#/texts/0", left=10.0, right=30.0)
    picture_item["parent"] = {"$ref": "#/pictures/4"}
    group_item = _docling_text("#/texts/1", left=10.0, right=30.0)
    group_item["parent"] = {"$ref": "#/groups/7"}
    baseline = _docling_text_document(picture_item, group_item)

    hierarchy_group = copy.deepcopy(group_item)
    hierarchy_group["self_ref"] = "#/texts/8"
    hierarchy_picture = copy.deepcopy(picture_item)
    hierarchy_picture["self_ref"] = "#/texts/9"
    hierarchy = _docling_text_document(hierarchy_group, hierarchy_picture)

    baseline_keys, hierarchy_keys = aligned_stable_key_maps(baseline, hierarchy)

    assert baseline_keys["#/texts/0"] == hierarchy_keys["#/texts/9"]
    assert baseline_keys["#/texts/1"] == hierarchy_keys["#/texts/8"]
    assert len(set(hierarchy_keys.values())) == 2


def test_toc_aliases_use_only_exact_reconciliations(tmp_path) -> None:
    hierarchy_root = tmp_path / "hierarchy"
    baseline_root = tmp_path / "baseline"
    (hierarchy_root / "artifacts").mkdir(parents=True)
    (baseline_root / "canonical").mkdir(parents=True)
    for relative in (
        "artifacts/decisions.jsonl",
        "artifacts/item_features.jsonl",
        "artifacts/toc_reconciliation.jsonl",
    ):
        (hierarchy_root / relative).write_text("")
    (baseline_root / "canonical/documents.jsonl").write_text("")
    key = "1" * 64
    section_id = f"{NEW_ID}/section/deir_appendix_d/sec000001"
    evidence = ProducerEvidence(
        baseline_document={},
        hierarchy_document={},
        item_features=[{"stable_item_key": key, "text": "Exact target"}],
        decisions=[],
        hierarchy={},
        visible_toc_entries=[
            {
                "toc_entry_id": "toc-missing",
                "title_with_marker_normalized": "Missing target",
            },
            {
                "toc_entry_id": "toc-exact",
                "title_with_marker_normalized": "Exact target",
            },
        ],
        toc_reconciliations=[
            {"toc_entry_id": "toc-missing", "state": "missing", "target_key": None},
            {"toc_entry_id": "toc-exact", "state": "exact", "target_key": key},
        ],
        baseline_key_by_pointer={},
        hierarchy_key_by_pointer={},
    )
    seeds = build_appendix_p_alias_seeds(
        collections={
            "documents": [{"id": "document", "title": "Appendix D"}],
            "blocks": [
                {
                    "stable_item_key": key,
                    "canonical_text": "Exact target",
                    "sequence": 1,
                }
            ],
            "pages": [],
        },
        sections=[
            {
                "source_stable_item_key": key,
                "section_kind": "semantic",
                "id": section_id,
            }
        ],
        evidence=evidence,
        page_labels=[],
        hierarchy_root=hierarchy_root,
        baseline_root=baseline_root,
    )

    assert [seed.raw_value for seed in seeds] == ["Appendix D", "Exact target", "Exact target"]


def test_strict_bridge_report_does_not_claim_a_reviewed_producer_comparison() -> None:
    expectations = SemanticExpectations(
        section_count=0,
        bridge_entry_count=0,
        canonical_block_count=0,
        heading_count=0,
        direct_membership_count=0,
        mapped_block_count=0,
        table_replacement_count=0,
        figure_suppression_count=0,
    )
    build = type("Build", (), {"bridge_entries": []})()

    report = _bridge_payload(build, {"control_kind": "strict_quality_gate"}, expectations)

    assert report["producer_comparison_sha256"] is None


def test_sections_project_sparse_hierarchy_toc_furniture_and_nontext() -> None:
    root_key, child_key, member_key, toc_key, furniture_key = (f"{i:064x}" for i in range(1, 6))
    content = [
        _content(1, root_key),
        _content(2, member_key),
        _content(3, child_key),
        _content(4, None, record_type="table"),
        _content(5, toc_key),
        _content(6, furniture_key, layer="furniture"),
    ]
    features = [
        _feature(root_key),
        _feature(member_key),
        _feature(child_key),
        _feature(toc_key, toc=True),
        _feature(furniture_key),
    ]
    decisions = [
        _decision(root_key, "heading", 1),
        _decision(member_key, "content", None),
        _decision(child_key, "heading", 3),
        _decision(toc_key, "content", None),
        _decision(furniture_key, "content", None),
    ]
    hierarchy = {
        "roots": [root_key],
        "edges": [{"parent_key": root_key, "child_key": child_key}],
        "direct_membership": [{"heading_key": root_key, "item_key": member_key}],
        "unassigned_content": [],
    }

    sections, placed = build_semantic_sections(
        content,
        document_id=DOCUMENT_ID,
        extraction_id=NEW_ID,
        source_id="deir_appendix_p",
        features=features,
        decisions=decisions,
        hierarchy=hierarchy,
        evidence_ref=REF,
    )

    assert [section["semantic_level"] for section in sections] == [None, None, 1, 3]
    assert placed[0]["semantic_placement"] == "heading_owner"
    assert placed[1]["semantic_placement"] == "direct_body"
    assert placed[3]["semantic_placement"] == "inherited_nontext"
    assert placed[3]["section_id"] == sections[3]["id"]
    assert placed[4]["semantic_placement"] == "toc_content"
    assert placed[4]["section_id"] == sections[0]["id"]
    assert placed[5]["section_id"] == sections[1]["id"]
    assert sections[2]["ordered_child_ids"][:2] == [placed[0]["id"], placed[1]["id"]]


def test_sections_project_table_replaced_heading_out_of_canonical_hierarchy() -> None:
    replaced_key, retained_key = (f"{i:064x}" for i in range(1, 3))
    content = [
        _content(1, retained_key),
        _content(2, None, record_type="table"),
    ]
    features = [_feature(replaced_key), _feature(retained_key)]
    decisions = [
        _decision(replaced_key, "heading", 1),
        _decision(retained_key, "heading", 2),
    ]
    hierarchy = {
        "roots": [replaced_key],
        "edges": [{"parent_key": replaced_key, "child_key": retained_key}],
        "direct_membership": [],
        "unassigned_content": [],
    }

    sections, placed = build_semantic_sections(
        content,
        document_id=DOCUMENT_ID,
        extraction_id=NEW_ID,
        source_id="deir_appendix_p",
        features=features,
        decisions=decisions,
        hierarchy=hierarchy,
        evidence_ref=REF,
        replacement_keys={replaced_key},
    )

    assert [section["source_stable_item_key"] for section in sections] == [
        None,
        None,
        retained_key,
    ]
    assert sections[2]["parent_section_id"] == sections[0]["id"]
    assert placed[1]["semantic_placement"] == "inherited_nontext"
    assert placed[1]["section_id"] == sections[2]["id"]


def test_page_labels_cover_missing_pages_and_apply_conflict_precedence() -> None:
    observations = build_page_label_observations(
        page_count=4,
        item_features=[
            {"physical_page": 1, "printed_page_label": "i"},
            {"physical_page": 3, "printed_page_label": "7"},
            {"physical_page": 3, "printed_page_label": "8"},
        ],
        visible_evidence_ref=REF,
        explicit_labels={1: ("1",), 4: ("iv",)},
        explicit_evidence_ref={"path": "source/page_labels.json", "sha256": "d" * 64},
    )

    assert [item["physical_page_number"] for item in observations] == [1, 2, 3, 4]
    assert observations[0]["resolved_state"] == "conflict"
    assert observations[1]["resolved_state"] == "unknown"
    assert observations[2]["visible_label"]["state"] == "conflict"
    assert observations[3]["resolution_basis"] == "explicit_pdf_page_labels"


def test_aliases_group_normalized_collisions_and_use_target_order() -> None:
    seeds = [
        AliasSeed(
            "section", "Repeated\u00a0 Heading", "section-2", "section", 20, "heading_text", REF
        ),
        AliasSeed("section", " repeated heading ", "section-1", "section", 10, "heading_text", REF),
        AliasSeed("section", "REPEATED HEADING", "section-1", "section", 10, "heading_text", REF),
        AliasSeed("printed_page", "7", "page-7", "page", 7, "resolved_printed_page_label", REF),
    ]
    aliases = build_target_aliases(
        seeds,
        extraction_id=NEW_ID,
        document_id=DOCUMENT_ID,
        source_id="deir_appendix_p",
    )

    assert aliases[0]["normalized_alias"] == "repeated heading"
    assert aliases[0]["resolution_status"] == "ambiguous"
    assert aliases[0]["raw_values"] == [
        " repeated heading ",
        "REPEATED HEADING",
        "Repeated\u00a0 Heading",
    ]
    assert [target["target_id"] for target in aliases[0]["targets"]] == ["section-1", "section-2"]
    assert aliases[1]["alias_kind"] == "printed_page"


def test_alias_seed_preference_keeps_spelling_but_uses_reconciled_toc_evidence() -> None:
    heading = AliasSeed.canonical_target(
        alias_kind="section",
        raw_value="  Water Supply ",
        target_id="section-1",
        target_type="section",
        target_order=10,
        evidence_kind="heading_text",
        evidence_ref=REF,
    )
    toc_ref = {"path": "artifacts/toc_reconciliation.jsonl", "sha256": "d" * 64}
    toc = AliasSeed.reconciled_toc_target(
        alias_kind="section",
        raw_value="WATER SUPPLY",
        target_id="section-1",
        target_order=10,
        toc_reconciliation_ref=toc_ref,
    )

    preferred = prefer_reconciled_toc_evidence([heading, toc])

    assert preferred[0].raw_value == "  Water Supply "
    assert preferred[0].evidence_kind == "visible_toc_reconciliation"
    assert preferred[0].evidence_ref == toc_ref
    assert preferred[0].toc_reconciliation_ref == toc_ref


def test_preservation_comparison_allows_only_named_semantic_fields() -> None:
    old_block = {
        "schema_version": "er_commons.canonical_extraction.v1",
        "id": f"{OLD_ID}/block/deir_appendix_p/blk000001",
        "section_id": f"{OLD_ID}/section/deir_appendix_p/sec000001",
        "canonical_text": "unchanged",
    }
    new_block = {
        "schema_version": "er_commons.canonical_extraction.v2",
        "id": f"{NEW_ID}/block/deir_appendix_p/blk000001",
        "section_id": f"{NEW_ID}/section/deir_appendix_p/sec000003",
        "canonical_text": "unchanged",
        "semantic_placement": "heading_owner",
        "is_toc_row": False,
        "stable_item_key": "1" * 64,
    }
    report = compare_baseline_collections(
        {"blocks": [old_block]},
        {"blocks": [new_block]},
        baseline_candidate_id=OLD_ID,
        new_candidate_id=NEW_ID,
    )
    assert report["undeclared_difference_count"] == 0

    changed = copy.deepcopy(new_block)
    changed["canonical_text"] = "changed"
    report = compare_baseline_collections(
        {"blocks": [old_block]},
        {"blocks": [changed]},
        baseline_candidate_id=OLD_ID,
        new_candidate_id=NEW_ID,
    )
    assert report["undeclared_difference_count"] == 1


def _content(
    index: int,
    key: str | None,
    *,
    record_type: str = "block",
    layer: str = "body",
) -> dict[str, object]:
    return {
        "id": f"{NEW_ID}/{record_type}/deir_appendix_p/item{index:06d}",
        "record_type": record_type,
        "content_layer": layer,
        "section_id": f"{NEW_ID}/section/deir_appendix_p/sec000001",
        "sequence": index,
        "stable_item_key": key,
    }


def _feature(key: str, *, toc: bool = False) -> dict[str, object]:
    return {"stable_item_key": key, "toc_region": toc}


def _decision(key: str, role: str, level: int | None) -> dict[str, object]:
    return {"stable_item_key": key, "corrected_role": role, "corrected_level": level}


def _docling_text_document(*texts: dict[str, object]) -> dict[str, object]:
    return {
        "texts": list(texts),
        "groups": [],
        "tables": [],
        "pictures": [],
        "key_value_items": [],
        "form_items": [],
    }


def _docling_text(self_ref: str, *, left: float, right: float) -> dict[str, object]:
    return {
        "self_ref": self_ref,
        "text": "Map label",
        "orig": "Map label",
        "prov": [
            {
                "page_no": 15,
                "bbox": {
                    "l": left,
                    "t": 50.0,
                    "r": right,
                    "b": 40.0,
                    "coord_origin": "BOTTOMLEFT",
                },
                "charspan": [0, 9],
            }
        ],
    }
