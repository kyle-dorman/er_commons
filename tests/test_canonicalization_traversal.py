"""Focused tests for saved-dictionary Docling traversal."""

from __future__ import annotations

import copy

import pytest

from er_commons.canonical_extraction import ContractError
from er_commons.canonical_extraction.traversal import traverse_docling_document


def tiny_document() -> dict[str, object]:
    """Return a graph covering groups, tables, captions, pictures, and furniture."""
    return {
        "body": {
            "children": [
                {"$ref": "#/groups/0"},
                {"$ref": "#/tables/0"},
                {"$ref": "#/tables/1"},
                {"$ref": "#/pictures/0"},
            ]
        },
        "furniture": {"children": []},
        "groups": [
            {
                "children": [{"$ref": "#/texts/0"}],
                "content_layer": "body",
            },
            {
                "children": [{"$ref": "#/texts/1"}],
                "content_layer": "body",
            },
            {
                "children": [{"$ref": "#/texts/2"}],
                "content_layer": "body",
            },
        ],
        "texts": [
            {"content_layer": "body", "children": []},
            {"content_layer": "body", "children": []},
            {"content_layer": "body", "children": []},
            {"content_layer": "body", "children": []},
            {"content_layer": "furniture", "children": []},
            {"content_layer": "furniture", "children": []},
        ],
        "tables": [
            {
                "content_layer": "body",
                "children": [{"$ref": "#/groups/1"}],
                "captions": [],
            },
            {
                "content_layer": "body",
                "children": [{"$ref": "#/groups/2"}],
                "captions": [],
            },
        ],
        "pictures": [
            {
                "content_layer": "body",
                "children": [{"$ref": "#/texts/5"}],
                "captions": [{"$ref": "#/texts/3"}],
            }
        ],
    }


def test_mapped_table_replaces_descendants_and_zero_table_falls_back() -> None:
    result = traverse_docling_document(
        tiny_document(),
        {"#/tables/0": ("producer_t1",)},
    )

    assert [(event.kind, event.pointer, event.producer_table_id) for event in result.events] == [
        ("text", "#/texts/0", None),
        ("table", "#/tables/0", "producer_t1"),
        ("text", "#/texts/2", None),
        ("figure", "#/pictures/0", None),
        ("text", "#/texts/3", None),
        ("text", "#/texts/4", None),
    ]
    assert result.suppressed_text_pointers == {"#/texts/1", "#/texts/5"}
    assert result.suppressed_picture_furniture_pointers == {"#/texts/5"}
    assert result.zero_table_pointers == {"#/tables/1"}


def test_furniture_is_appended_by_pointer_not_furniture_root() -> None:
    result = traverse_docling_document(tiny_document(), {})
    furniture = [event.pointer for event in result.events if event.content_layer == "furniture"]
    assert furniture == ["#/texts/4"]


def test_explicit_invalid_geometry_text_is_suppressed_and_accounted() -> None:
    result = traverse_docling_document(
        tiny_document(),
        {},
        {"#/texts/0", "#/texts/4"},
    )

    assert "#/texts/0" not in {event.pointer for event in result.events}
    assert "#/texts/4" not in {event.pointer for event in result.events}
    assert result.invalid_geometry_text_pointers == {"#/texts/0", "#/texts/4"}
    assert {"#/texts/0", "#/texts/4"} <= result.suppressed_text_pointers


def test_group_cycle_is_fatal() -> None:
    document = tiny_document()
    groups = document["groups"]
    assert isinstance(groups, list)
    groups[0]["children"] = [{"$ref": "#/groups/0"}]
    with pytest.raises(ContractError, match="group cycle"):
        traverse_docling_document(document, {})


def test_unknown_pointer_is_fatal() -> None:
    document = tiny_document()
    body = document["body"]
    assert isinstance(body, dict)
    body["children"] = [{"$ref": "#/texts/999"}]
    with pytest.raises(ContractError, match="unknown Docling pointer"):
        traverse_docling_document(document, {})


def test_duplicate_semantic_traversal_is_fatal() -> None:
    document = tiny_document()
    body = document["body"]
    assert isinstance(body, dict)
    children = body["children"]
    assert isinstance(children, list)
    children.insert(1, copy.deepcopy(children[0]))
    with pytest.raises(ContractError, match="duplicate Docling semantic traversal"):
        traverse_docling_document(document, {})
