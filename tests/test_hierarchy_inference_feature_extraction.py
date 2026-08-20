"""Focused tests for deterministic Task 03E.2 producer feature extraction."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    FloatObject,
    IndirectObject,
    NameObject,
    NullObject,
    TextStringObject,
)

from er_commons.document_parsing.heading_evidence_parsing.alignment_projection import (
    AlignmentPage,
)
from er_commons.document_parsing.heading_evidence_parsing.pdf_observations import (
    extract_outline_observations,
    extract_page_labels,
)
from er_commons.document_parsing.heading_evidence_parsing.source_features import (
    build_feature_seeds,
    document_index_text_pointers,
    traverse_provenance_text,
)
from er_commons.document_parsing.heading_evidence_parsing.text_evidence import (
    LayoutEvidence,
    align_parsed_line,
    normalize_text,
    parse_numbering,
)
from er_commons.hierarchy_inference.errors import HierarchyInferenceContractError


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
        {1: AlignmentPage(1, 612.0, 792.0, {"1. heading": LayoutEvidence("unique_aligned", 1)})},
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
    with pytest.raises(HierarchyInferenceContractError, match="picture caption"):
        traverse_provenance_text(document)


def test_feature_seed_uses_stable_key_layout_outline_and_footer_evidence() -> None:
    alignment_pages = {
        1: AlignmentPage(
            1,
            612.0,
            792.0,
            {"1. heading": LayoutEvidence("unique_aligned", 1)},
        )
    }
    outline = (
        {
            "normalized_title": "1. heading",
            "physical_page": 1,
            "effective_level": 2,
        },
    )
    features = build_feature_seeds(_document(), alignment_pages, outline_observations=outline)
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

    with pytest.raises(HierarchyInferenceContractError, match="child list has no parent"):
        extract_outline_observations(reader)


def test_pdf_observations_flatten_destinationless_filename_container() -> None:
    reader = _Reader()
    reader.outline = [
        SimpleNamespace(title="2020 NOP", page=0),
        [
            SimpleNamespace(title="TRT.pdf", page=9),
            [
                SimpleNamespace(title="TRT Comments", page=0),
                SimpleNamespace(title="Attachment", page=1),
            ],
        ],
    ]

    result = extract_outline_observations(reader)

    assert [item["title"] for item in result.observations] == [
        "2020 NOP",
        "TRT Comments",
        "Attachment",
    ]
    parent, first_child, second_child = result.observations
    assert first_child["parent_outline_id"] == parent["outline_id"]
    assert second_child["parent_outline_id"] == parent["outline_id"]
    assert first_child["raw_depth"] == 2
    assert second_child["raw_depth"] == 2
    assert result.diagnostics == (
        {
            "reading_order_index": None,
            "stable_item_key": None,
            "code": "OUTLINE_FILENAME_CONTAINER_OMITTED",
            "detail": (
                "Omitted destinationless PDF filename container 'TRT.pdf' and "
                "flattened 2 ordered child bookmarks."
            ),
        },
    )


class _MalformedOutlineReader:
    """Expose one raw malformed node and its post-normalization outline view."""

    def __init__(self, children: list[SimpleNamespace]) -> None:
        self._container_reference = IndirectObject(8875, 0, self)
        self._child_reference = IndirectObject(8876, 0, self)
        self._raw_container = DictionaryObject(
            {
                NameObject("/Title"): TextStringObject("Appendix_071024.pdf"),
                NameObject("/Dest"): ArrayObject(
                    [NullObject(), FloatObject(0.0), FloatObject(0.0), FloatObject(1.0)]
                ),
                NameObject("/First"): self._child_reference,
            }
        )
        self._raw_child = DictionaryObject({NameObject("/Title"): TextStringObject("Placeholder")})
        self._children = children
        self.custom_outline: list[Any] | None = None
        self.pages = [object(), object()]
        self.trailer = {
            "/Root": {
                "/Outlines": {
                    "/First": self._container_reference,
                }
            }
        }

    def get_destination_page_number(self, destination: Any) -> int:
        return int(destination.page)

    def get_object(self, reference: IndirectObject) -> DictionaryObject:
        return (
            self._raw_container
            if reference.idnum == self._container_reference.idnum
            else self._raw_child
        )

    @property
    def outline(self) -> list[Any]:
        destination = cast(ArrayObject, self._raw_container["/Dest"])
        if destination[1] != "/Fit":
            raise ValueError("Unknown Destination Type: '0.0'")
        container = self.malformed_container()
        return self.custom_outline or [container, self._children]

    def malformed_container(self) -> SimpleNamespace:
        return SimpleNamespace(
            title="Appendix_071024.pdf",
            page=9,
            indirect_reference=self._container_reference,
        )


def test_pdf_observations_drop_only_invalid_children_of_malformed_container() -> None:
    reader = _MalformedOutlineReader(
        [
            SimpleNamespace(title="Sustainability_Appendix_Page.pdf", page=9),
            SimpleNamespace(title="Battery Storage", page=0),
            SimpleNamespace(title="Solar Farm", page=1),
            SimpleNamespace(title="Water Recycling Detailed Report", page=9),
        ]
    )

    result = extract_outline_observations(reader)

    assert [item["title"] for item in result.observations] == [
        "Battery Storage",
        "Solar Farm",
    ]
    assert [item["raw_depth"] for item in result.observations] == [1, 1]
    assert [item["code"] for item in result.diagnostics] == [
        "OUTLINE_FILENAME_CONTAINER_OMITTED",
        "TOC_TARGET_MISSING",
        "TOC_TARGET_MISSING",
    ]
    assert "retained 2 ordered descendant bookmarks" in result.diagnostics[0]["detail"]
    assert "2 invalid leaf bookmarks" in result.diagnostics[0]["detail"]


def test_pdf_observations_reject_malformed_container_with_unordered_valid_children() -> None:
    reader = _MalformedOutlineReader(
        [
            SimpleNamespace(title="Later", page=1),
            SimpleNamespace(title="Earlier", page=0),
        ]
    )

    with pytest.raises(HierarchyInferenceContractError, match="children are unordered"):
        extract_outline_observations(reader)


def test_pdf_observations_deduplicate_broken_nested_filename_subtree() -> None:
    reader = _MalformedOutlineReader([])
    reader.custom_outline = [
        SimpleNamespace(title="Binder4.pdf", page=9),
        [
            SimpleNamespace(title="_BuildingConst_Appendix_Complete_091423", page=9),
            [
                SimpleNamespace(title="BuildingConst_Appendix_Page.pdf", page=9),
                SimpleNamespace(title="Building A", page=0),
                SimpleNamespace(title="Building B", page=1),
            ],
            SimpleNamespace(title="_Sustainability_Appendix_Complete_091323", page=9),
            [
                SimpleNamespace(title="Battery Report", page=9),
                SimpleNamespace(title="Water Recycling Detailed Report (4)", page=9),
            ],
        ],
        reader.malformed_container(),
        [
            SimpleNamespace(title="Sustainability_Appendix_Page.pdf", page=9),
            SimpleNamespace(title="Battery Report", page=0),
            SimpleNamespace(title="Water Recycling Detailed Report (4)", page=9),
            SimpleNamespace(title="Water Tank", page=1),
        ],
        SimpleNamespace(title="_EmissionMatrix_Appendix_Complete", page=1),
        [
            SimpleNamespace(title="EmissionMatrix_Pages", page=9),
            [SimpleNamespace(title="Emissions", page=9)],
        ],
    ]
    water_heading = {
        "content_layer": "body",
        "raw_role": "section_header",
        "normalized_text": "bbl water recycling detailed report updated",
    }

    result = extract_outline_observations(
        reader,
        heading_features=[water_heading],  # type: ignore[list-item]
    )

    assert [item["title"] for item in result.observations] == [
        "Building A",
        "Building B",
        "Battery Report",
        "Water Tank",
        "_EmissionMatrix_Appendix_Complete",
    ]
    assert sum(item["title"] == "Battery Report" for item in result.observations) == 1
    assert any(
        "Omitted duplicate broken outline subtree" in item["detail"] for item in result.diagnostics
    )
    assert any("EmissionMatrix_Pages" in item["detail"] for item in result.diagnostics)


@pytest.mark.parametrize(
    "children",
    [
        [
            SimpleNamespace(title="Later", page=1),
            SimpleNamespace(title="Earlier", page=0),
        ],
        [SimpleNamespace(title="Missing", page=9)],
    ],
)
def test_pdf_observations_reject_unsupported_filename_container(
    children: list[SimpleNamespace],
) -> None:
    reader = _Reader()
    reader.outline = [SimpleNamespace(title="Folder.pdf", page=9), children]

    with pytest.raises(HierarchyInferenceContractError, match="child list has no parent"):
        extract_outline_observations(reader)


def test_pdf_observations_recover_unique_adjacent_appendix_container() -> None:
    reader = _Reader()
    reader.outline = [
        SimpleNamespace(title="Appendix A Exhibits.pdf", page=9),
        [SimpleNamespace(title="E1. Project Desc", page=1)],
    ]
    heading = {
        "content_layer": "body",
        "raw_role": "section_header",
        "physical_page": 1,
        "text": "APPENDIX A: EXHIBITS",
        "normalized_text": "appendix a: exhibits",
        "reading_order_index": 12,
        "stable_item_key": "a" * 64,
    }

    result = extract_outline_observations(reader, heading_features=[heading])  # type: ignore[list-item]

    assert [item["title"] for item in result.observations] == [
        "Appendix A Exhibits.pdf",
        "E1. Project Desc",
    ]
    container, child = result.observations
    assert container["physical_page"] == 1
    assert container["normalized_title"] == "appendix a: exhibits"
    assert child["parent_outline_id"] == container["outline_id"]
    assert result.diagnostics[0]["code"] == "OUTLINE_CONTAINER_RECOVERED"
    assert result.diagnostics[0]["stable_item_key"] == "a" * 64


def test_pdf_observations_reject_ambiguous_or_nonmatching_container() -> None:
    reader = _Reader()
    reader.outline = [
        SimpleNamespace(title="Appendix A Exhibits.pdf", page=9),
        [SimpleNamespace(title="E1. Project Desc", page=1)],
    ]
    nonmatch = {
        "content_layer": "body",
        "raw_role": "section_header",
        "physical_page": 1,
        "text": "APPENDIX B: EXHIBITS",
        "normalized_text": "appendix b: exhibits",
        "reading_order_index": 12,
        "stable_item_key": "b" * 64,
    }

    with pytest.raises(HierarchyInferenceContractError, match="child list has no parent"):
        extract_outline_observations(reader, heading_features=[nonmatch])  # type: ignore[list-item]


@pytest.mark.parametrize(
    ("title", "preceding_text", "child_text", "expected_page"),
    [
        (
            "J90411-1 UDS Level 2 Report Final Report.pdf",
            "APPENDIX I Analytical Laboratory Reports",
            "ANALYTICAL REPORT TestAmerica Job ID: 720-90411-1",
            2,
        ),
        (
            "AppJ-DataValRpts.pdf",
            "APPENDIX J Data Validation Summaries",
            "Stage 2A Data Validation Work Order 720-89864-1",
            1,
        ),
    ],
)
def test_pdf_observations_recover_unique_fuzzy_adjacent_container(
    title: str,
    preceding_text: str,
    child_text: str,
    expected_page: int,
) -> None:
    class Page:
        def __init__(self, text: str) -> None:
            self.text = text

        def extract_text(self) -> str:
            return self.text

    reader = _Reader()
    reader.pages = [Page(preceding_text), Page(child_text)]
    reader.outline = [
        SimpleNamespace(title=title, page=9),
        [
            SimpleNamespace(title="1. Cover Page", page=1),
            [SimpleNamespace(title="1.1 Nested child", page=1)],
        ],
    ]

    result = extract_outline_observations(reader)

    assert result.observations[0]["physical_page"] == expected_page
    assert result.observations[1]["parent_outline_id"] == result.observations[0]["outline_id"]
    assert result.diagnostics[0]["code"] == "OUTLINE_CONTAINER_RECOVERED"
    assert "unique fuzzy title evidence" in result.diagnostics[0]["detail"]


def test_pdf_observations_reject_fuzzy_container_when_both_pages_match() -> None:
    class Page:
        def extract_text(self) -> str:
            return "TestAmerica Job ID: 720-90411-1"

    reader = _Reader()
    reader.pages = [Page(), Page()]
    reader.outline = [
        SimpleNamespace(title="J90411-1 UDS Level 2 Report Final Report.pdf", page=9),
        [SimpleNamespace(title="1. Cover Page", page=1)],
    ]

    with pytest.raises(HierarchyInferenceContractError, match="child list has no parent"):
        extract_outline_observations(reader)
