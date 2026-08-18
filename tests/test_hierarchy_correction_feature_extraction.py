"""Focused tests for deterministic Task 03E.2 producer feature extraction."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from er_commons.hierarchy_correction.errors import HierarchyCorrectionContractError
from er_commons.hierarchy_correction.features import (
    align_parsed_line,
    build_feature_seeds,
    document_index_text_pointers,
    normalize_text,
    parse_numbering,
    traverse_provenance_text,
)
from er_commons.hierarchy_correction.pdf_observations import (
    extract_outline_observations,
    extract_page_labels,
)


def _text(
    index: int,
    parent: str,
    text: str,
    *,
    label: str = "text",
    layer: str = "body",
) -> dict[str, Any]:
    return {
        "self_ref": f"#/texts/{index}",
        "parent": {"$ref": parent},
        "label": label,
        "text": text,
        "orig": text,
        "content_layer": layer,
        "prov": [
            {
                "page_no": 1,
                "bbox": {
                    "l": 72.0,
                    "t": 720.0,
                    "r": 300.0,
                    "b": 700.0,
                    "coord_origin": "BOTTOMLEFT",
                },
                "charspan": [0, len(text)],
            }
        ],
    }


def _document() -> dict[str, Any]:
    caption = _text(0, "#/pictures/0", "Figure 1", label="caption")
    descendant = _text(1, "#/pictures/0", "Map annotation")
    footer = _text(2, "#/pictures/0", "P1", label="page_footer", layer="furniture")
    body = _text(3, "#/body", "1. Heading", label="section_header")
    return {
        "body": {"children": [{"$ref": "#/pictures/0"}, {"$ref": "#/texts/3"}]},
        "furniture": {"children": []},
        "groups": [],
        "tables": [],
        "pictures": [
            {
                "self_ref": "#/pictures/0",
                "parent": {"$ref": "#/body"},
                "content_layer": "body",
                "children": [
                    {"$ref": "#/texts/0"},
                    {"$ref": "#/texts/1"},
                    {"$ref": "#/texts/2"},
                ],
                "captions": [{"$ref": "#/texts/0"}],
                "prov": [
                    {
                        "page_no": 1,
                        "bbox": dict(caption["prov"][0]["bbox"]),
                        "charspan": [0, 0],
                    }
                ],
            }
        ],
        "texts": [caption, descendant, footer, body],
    }


def test_normalization_numbering_and_exact_line_alignment() -> None:
    assert normalize_text("  Caf\u00e9\N{NO-BREAK SPACE}\tA  ") == "caf\u00e9 a"
    assert parse_numbering("2025 Heading", raw_role="section_header").kind == "none"
    assert parse_numbering("2025. Heading", raw_role="section_header").kind == "decimal"
    assert parse_numbering("IV. Topic", raw_role="section_header").kind == "upper_roman"
    assert parse_numbering("A. Topic", raw_role="section_header", article_regime=True).depth == 3
    assert parse_numbering("1. Item", raw_role="list_item").kind == "none"

    parsed = {"textline_cells": [{"text": " Exact\u00a0line "}]}
    assert align_parsed_line("exact line", parsed).state == "unique_aligned"
    parsed["textline_cells"].append({"text": "EXACT LINE"})
    assert align_parsed_line("exact line", parsed).state == "ambiguous"


def test_picture_descendants_are_preserved_and_only_declared_caption_is_caption() -> None:
    traversed = traverse_provenance_text(_document())
    assert [item.pointer for item in traversed] == [
        "#/texts/0",
        "#/texts/1",
        "#/texts/2",
        "#/texts/3",
    ]
    assert [item.picture_caption for item in traversed] == [True, False, False, False]
    assert traversed[2].content_layer == "furniture"


def test_document_index_text_pointers_include_nested_descendants_only() -> None:
    document = _document()
    document["groups"] = [
        {
            "self_ref": "#/groups/0",
            "children": [{"$ref": "#/texts/3"}],
        }
    ]
    document["tables"] = [
        {
            "self_ref": "#/tables/0",
            "label": "document_index",
            "children": [{"$ref": "#/groups/0"}],
        },
        {
            "self_ref": "#/tables/1",
            "label": "table",
            "children": [{"$ref": "#/texts/1"}],
        },
    ]

    assert document_index_text_pointers(document) == frozenset({"#/texts/3"})


def test_exact_duplicate_text_representations_receive_distinct_stable_keys() -> None:
    document = _document()
    duplicate = _text(4, "#/pictures/0", "1. Heading", label="section_header")
    duplicate["prov"] = [dict(document["texts"][3]["prov"][0])]
    document["texts"].append(duplicate)
    document["pictures"][0]["children"].append({"$ref": "#/texts/4"})

    traversed = traverse_provenance_text(document)
    features = build_feature_seeds(
        document,
        {
            "pages": [
                {
                    "page_no": 1,
                    "size": {"width": 612.0, "height": 792.0},
                    "parsed_page": {"textline_cells": [{"text": "1. Heading"}]},
                }
            ]
        },
    )

    assert len(traversed) == 5
    assert len({item["stable_item_key"] for item in features}) == 5


@pytest.mark.parametrize("failure", ["label", "parent", "page"])
def test_picture_caption_disagreement_fails_closed(failure: str) -> None:
    document = _document()
    caption = document["texts"][0]
    if failure == "label":
        caption["label"] = "text"
    elif failure == "parent":
        caption["parent"] = {"$ref": "#/body"}
    else:
        caption["prov"][0]["page_no"] = 2
    with pytest.raises(HierarchyCorrectionContractError, match="picture caption"):
        traverse_provenance_text(document)


def test_feature_seed_uses_stable_key_layout_outline_and_footer_evidence() -> None:
    conversion_pages = {
        "pages": [
            {
                "page_no": 1,
                "size": {"width": 612.0, "height": 792.0},
                "parsed_page": {"textline_cells": [{"text": "1. Heading"}]},
            }
        ]
    }
    outline = (
        {
            "normalized_title": "1. heading",
            "physical_page": 1,
            "effective_level": 2,
        },
    )
    features = build_feature_seeds(_document(), conversion_pages, outline_observations=outline)
    heading = features[-1]
    assert len(heading["stable_item_key"]) == 64
    assert heading["raw_parent_ref"] == "#/body"
    assert heading["outline_state"] == "unique_exact"
    assert heading["outline_level"] == 2
    assert heading["layout_state"] == "unique_aligned"
    assert heading["numbering_kind"] == "decimal"
    assert heading["printed_page_label"] == "P1"


class _Reader:
    pages = [object(), object()]
    page_labels = ["i", "1"]

    def __init__(self) -> None:
        parent = SimpleNamespace(title="Appendix P", page=0)
        child = SimpleNamespace(title="Article 1", page=1)
        self.outline = [parent, [child]]

    def get_destination_page_number(self, destination: Any) -> int:
        return int(destination.page)


def test_pdf_observations_preserve_nested_outline_and_page_labels() -> None:
    reader = _Reader()
    result = extract_outline_observations(reader)
    observations = result.observations
    assert extract_page_labels(reader) == {1: "i", 2: "1"}
    assert result.diagnostics == ()
    assert observations[0]["parent_outline_id"] is None
    assert observations[1]["parent_outline_id"] == observations[0]["outline_id"]
    assert observations[1]["physical_page"] == 2
    assert observations[1]["effective_level"] == 2


def test_pdf_observations_omit_only_destinationless_outline_leaves() -> None:
    reader = _Reader()
    reader.outline.append(SimpleNamespace(title="Missing appendix", page=9))

    result = extract_outline_observations(reader)

    assert [item["title"] for item in result.observations] == ["Appendix P", "Article 1"]
    assert result.diagnostics == (
        {
            "reading_order_index": None,
            "stable_item_key": None,
            "code": "TOC_TARGET_MISSING",
            "detail": (
                "PDF outline leaf has no valid destination and was omitted: Missing appendix"
            ),
        },
    )


def test_pdf_observations_reject_destinationless_outline_parent() -> None:
    reader = _Reader()
    reader.outline = [
        SimpleNamespace(title="Missing parent", page=9),
        [SimpleNamespace(title="Child", page=1)],
    ]

    with pytest.raises(HierarchyCorrectionContractError, match="child list has no parent"):
        extract_outline_observations(reader)
