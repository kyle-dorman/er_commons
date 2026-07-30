"""Focused tests for the Task 03E hierarchy-only comparison boundary."""

from __future__ import annotations

from copy import deepcopy

from er_commons.document_extraction.hierarchy.document_comparison import (
    compare_docling_hierarchy,
    stable_key_collision_count,
)


def _prov(page: int, top: float) -> list[dict[str, object]]:
    return [
        {
            "page_no": page,
            "bbox": {
                "l": 10.0,
                "t": top,
                "r": 100.0,
                "b": top - 10,
                "coord_origin": "BOTTOMLEFT",
            },
            "charspan": [0, 7],
        }
    ]


def _document() -> dict[str, object]:
    return {
        "schema_name": "DoclingDocument",
        "version": "1",
        "name": "test",
        "origin": {"mimetype": "application/pdf"},
        "body": {
            "self_ref": "#/body",
            "children": [{"$ref": "#/texts/0"}, {"$ref": "#/texts/1"}],
        },
        "furniture": {"self_ref": "#/furniture", "children": []},
        "texts": [
            {
                "self_ref": "#/texts/0",
                "parent": {"$ref": "#/body"},
                "children": [],
                "content_layer": "body",
                "label": "section_header",
                "prov": _prov(1, 100),
                "orig": "1 Heading",
                "text": "1 Heading",
                "level": 1,
            },
            {
                "self_ref": "#/texts/1",
                "parent": {"$ref": "#/body"},
                "children": [],
                "content_layer": "body",
                "label": "list_item",
                "prov": _prov(1, 80),
                "orig": "2 Promoted",
                "text": "2 Promoted",
                "enumerated": True,
                "marker": "2",
            },
        ],
        "groups": [],
        "tables": [],
        "pictures": [],
        "key_value_items": [],
        "form_items": [],
        "pages": {},
    }


def test_level_change_and_exact_promotion_pass_with_reference_rewrites() -> None:
    baseline = _document()
    candidate = deepcopy(baseline)
    candidate["texts"] = [
        {
            **candidate["texts"][0],
            "self_ref": "#/texts/1",
            "level": 2,
        },
        {
            "self_ref": "#/texts/0",
            "parent": {"$ref": "#/body"},
            "children": [],
            "content_layer": "body",
            "label": "section_header",
            "prov": _prov(1, 80),
            "orig": "2 Promoted",
            "text": "2 Promoted",
            "level": 3,
        },
    ]
    candidate["body"]["children"] = [{"$ref": "#/texts/1"}, {"$ref": "#/texts/0"}]

    report = compare_docling_hierarchy(baseline, candidate, review_pages={1})

    assert report["status"] == "pass"
    assert [item["change_kind"] for item in report["hierarchy_changes"]] == [
        "heading_level",
        "list_item_promotion",
    ]
    assert report["item_alignment"]["semantic_reading_order_equal"] is True
    assert len(report["review_items"]) == 2


def test_text_geometry_and_semantic_parent_changes_fail() -> None:
    baseline = _document()
    candidate = deepcopy(baseline)
    candidate["texts"][0]["prov"][0]["bbox"]["t"] = 99.0

    geometry = compare_docling_hierarchy(baseline, candidate)

    assert geometry["status"] == "inconclusive"
    assert geometry["item_alignment"]["stable_key_sets_equal"] is False

    candidate = deepcopy(baseline)
    candidate["groups"] = [
        {
            "self_ref": "#/groups/0",
            "parent": {"$ref": "#/body"},
            "children": [{"$ref": "#/texts/0"}],
            "content_layer": "body",
            "name": "group",
            "label": "unspecified",
        }
    ]
    candidate["texts"][0]["parent"] = {"$ref": "#/groups/0"}
    candidate["body"]["children"][0] = {"$ref": "#/groups/0"}

    parent = compare_docling_hierarchy(baseline, candidate)

    assert parent["status"] == "reject"
    assert any(
        item["change_kind"] == "semantic_parent_change" for item in parent["unexpected_changes"]
    )


def test_duplicate_stable_key_is_inconclusive() -> None:
    baseline = _document()
    candidate = deepcopy(baseline)
    candidate["texts"].append(deepcopy(candidate["texts"][0]))
    candidate["texts"][-1]["self_ref"] = "#/texts/2"

    assert stable_key_collision_count(candidate) == 1
    report = compare_docling_hierarchy(baseline, candidate)
    assert report["status"] == "inconclusive"
    assert "duplicate stable text key" in report["reason"]
