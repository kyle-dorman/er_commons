"""Focused producer tests for visible TOCs, reconciliation, and regimes."""

from __future__ import annotations

from typing import Any

from er_commons.document_parsing.heading_evidence_parsing.source_features import (
    unique_footer_labels,
)
from er_commons.document_parsing.heading_evidence_parsing.text_evidence import parse_numbering
from er_commons.hierarchy_inference.numbering_scopes import (
    NumberingScopeCandidate,
    _assign_innermost_regimes,
    _materialize_regimes,
    _nested_candidates,
    build_numbering_regimes,
)
from er_commons.hierarchy_inference.toc_analysis import build_visible_toc
from er_commons.hierarchy_inference.toc_reconciliation import reconcile_toc_entries
from er_commons.hierarchy_inference.toc_regions import TocRegion
from er_commons.hierarchy_inference.toc_rows import parse_toc_region


def _feature(
    order: int,
    text: str,
    *,
    page: int,
    role: str = "text",
    layer: str = "body",
    parent: str = "#/body",
    outline_state: str = "absent",
) -> dict[str, Any]:
    return {
        "stable_item_key": f"{order + 1:064x}",
        "raw_self_ref": f"#/texts/{order}",
        "raw_parent_ref": parent,
        "text": text,
        "orig": text,
        "normalized_text": text.casefold(),
        "reading_order_index": order,
        "content_layer": layer,
        "raw_role": role,
        "raw_level": 1 if role == "section_header" else None,
        "physical_page": page,
        "page_width": 612.0,
        "page_height": 792.0,
        "bbox": {
            "l": 72.0,
            "t": 720.0 - order,
            "r": 300.0,
            "b": 700.0 - order,
            "coord_origin": "BOTTOMLEFT",
        },
        "charspan": [0, len(text)],
        "line_count": 1,
        "left_pt": 72.0,
        "height_pt": 20.0,
        "toc_region": False,
        "numbering_kind": "none",
        "numbering_token": None,
        "numbering_depth": None,
        "outline_state": outline_state,
        "outline_level": 3 if outline_state == "unique_exact" else None,
        "layout_state": "unique_aligned",
        "printed_page_label": None,
    }


def _outline(
    index: int,
    title: str,
    page: int,
    *,
    parent: str | None,
    depth: int = 3,
) -> dict[str, Any]:
    return {
        "outline_id": f"outline-{index:08d}",
        "parent_outline_id": parent,
        "title": title,
        "normalized_title": title.casefold(),
        "physical_page": page,
        "raw_depth": depth,
        "source_root_depth": 1,
        "effective_level": depth,
    }


def test_primary_toc_ends_at_later_outline_sibling_and_excludes_picture_target() -> None:
    features = [
        _feature(0, "TABLE OF CONTENTS", page=4, role="section_header"),
        _feature(1, "1", page=4),
        _feature(2, "INTRODUCTION", page=4),
        _feature(3, ".....", page=4),
        _feature(4, "5", page=4),
        _feature(5, "TABLE OF CONTENTS (CONTINUED)", page=6, role="section_header"),
        _feature(6, "Approval letter", page=7),
        _feature(7, "1 Introduction", page=8, role="section_header", outline_state="unique_exact"),
        _feature(8, "1 Introduction", page=8, parent="#/pictures/0"),
        _feature(9, "Body", page=8),
        _feature(10, "Page 5 of 99", page=8, role="page_footer", layer="furniture"),
    ]
    outlines = (
        _outline(0, "Water Supply Assessment", 3, parent=None, depth=2),
        _outline(1, "TABLE OF CONTENTS", 4, parent="outline-00000000"),
        _outline(2, "Approval letter", 7, parent="outline-00000000"),
        _outline(3, "1 Introduction", 8, parent="outline-00000000"),
    )
    result = build_visible_toc(features, outlines)

    assert result.regions[0].end == 6
    assert all(item["toc_region"] for item in result.features[:6])
    assert not result.features[6]["toc_region"]
    assert len(result.entries) == 1
    assert result.entries[0]["title_with_marker_normalized"] == "1 introduction"
    assert result.reconciliations[0]["state"] == "exact"
    assert result.reconciliations[0]["candidate_keys"] == [features[7]["stable_item_key"]]


def test_document_index_header_is_toc_content_even_without_parsed_rows() -> None:
    features = [
        _feature(
            0,
            "DOCUMENT INDEX HEADER",
            page=11,
            role="section_header",
            parent="#/tables/34",
            outline_state="unique_exact",
        ),
        _feature(1, "Header-only index note", page=11, parent="#/texts/0"),
    ]

    result = build_visible_toc(
        features,
        (),
        document_index_text_refs=frozenset({"#/texts/0", "#/texts/1"}),
    )

    assert result.features[0]["toc_region"] is True
    assert result.features[1]["toc_region"] is True
    assert result.entries == ()
    assert result.diagnostics == (
        {
            "reading_order_index": 1,
            "stable_item_key": features[1]["stable_item_key"],
            "code": "TOC_ROW_UNPARSEABLE",
            "detail": "document-index text retained without a parseable TOC row",
        },
    )


def test_embedded_toc_uses_roman_to_arabic_footer_transition() -> None:
    features = [
        _feature(0, "TABLE OF CONTENTS", page=112, role="section_header"),
        _feature(1, "Article 1.", page=112),
        _feature(2, "Parties", page=112),
        _feature(3, ".....", page=112),
        _feature(4, "1", page=112),
        _feature(5, "i", page=112, role="page_footer", layer="furniture"),
        _feature(6, "Article 1. Parties", page=117, role="section_header"),
        _feature(7, "1.01. Definitions", page=117, role="section_header"),
        _feature(8, "Body", page=117),
        _feature(9, "1", page=117, role="page_footer", layer="furniture"),
    ]
    result = build_visible_toc(features, ())

    assert result.regions[0].end == 6
    assert result.features[6]["toc_region"] is False
    assert result.features[7]["toc_region"] is False
    assert result.entries[0]["numbering_token"] == "1"
    assert result.entries[0]["depth"] == 1
    assert result.reconciliations[0]["state"] == "exact"
    assert result.reconciliations[0]["target_key"] == features[6]["stable_item_key"]


def test_embedded_toc_accepts_unnumbered_inline_leader_rows() -> None:
    features = [
        _feature(0, "TABLE OF CONTENTS", page=27, role="section_header"),
        _feature(1, "Definitions/Glossary . . . . .", page=27),
        _feature(2, "3", page=27),
        _feature(3, "Page 2 of 100", page=27, role="page_footer", layer="furniture"),
        _feature(4, "Qualifiers", page=28, role="section_header"),
        _feature(5, "Qualifier body", page=28),
        _feature(6, "Definitions/Glossary", page=28, role="section_header"),
        _feature(7, "Glossary body", page=28),
        _feature(8, "Page 3 of 100", page=28, role="page_footer", layer="furniture"),
    ]

    result = build_visible_toc(features, ())

    assert result.regions[0].end == 4
    assert result.features[4]["toc_region"] is False
    assert result.entries[0]["title_without_marker_normalized"] == "definitions/glossary"
    assert result.entries[0]["printed_page"] == "3"
    assert result.reconciliations[0]["target_key"] == features[6]["stable_item_key"]


def test_numeric_toc_marker_accepts_terminal_period_and_retains_clean_token() -> None:
    features = [
        _feature(0, "TABLE OF CONTENTS", page=112, role="section_header"),
        _feature(1, "1.01.", page=112),
        _feature(2, "Definitions", page=112),
        _feature(3, ".....", page=112),
        _feature(4, "24", page=112),
        _feature(5, "i", page=112, role="page_footer", layer="furniture"),
        _feature(6, "1.01 Definitions", page=117, role="section_header"),
        _feature(7, "Body", page=117),
        _feature(8, "1", page=117, role="page_footer", layer="furniture"),
    ]

    result = build_visible_toc(features, ())

    assert len(result.entries) == 1
    assert result.entries[0]["title_with_marker_normalized"] == "1.01. definitions"
    assert result.entries[0]["numbering_token"] == "1.01"
    assert result.entries[0]["printed_page"] == "24"


def test_split_numeric_marker_period_requires_adjacent_baseline_geometry() -> None:
    features = [
        _feature(0, "TABLE OF CONTENTS", page=112, role="section_header"),
        _feature(1, "3.14", page=112),
        _feature(2, ".", page=112),
        _feature(3, "Measurement of Water", page=112),
        _feature(4, ".....", page=112),
        _feature(5, "24", page=112),
        _feature(6, "i", page=112, role="page_footer", layer="furniture"),
        _feature(7, "3.14. Measurement of Water", page=117, role="section_header"),
        _feature(8, "Body", page=117),
        _feature(9, "24", page=117, role="page_footer", layer="furniture"),
    ]
    features[1]["bbox"].update({"l": 83.0, "r": 104.0, "b": 282.3, "t": 290.4})
    features[2]["bbox"].update({"l": 105.5, "r": 106.5, "b": 282.4, "t": 283.5})

    result = build_visible_toc(features, ())

    assert result.entries[0]["title_with_marker_normalized"] == "3.14. measurement of water"
    assert result.entries[0]["numbering_token"] == "3.14"
    assert result.entries[0]["source_item_keys"][:2] == [
        features[1]["stable_item_key"],
        features[2]["stable_item_key"],
    ]
    assert result.features[2]["text"] == "."
    assert result.reconciliations[0]["state"] == "exact"


def test_split_numeric_marker_period_rejects_gap_and_baseline_mismatch() -> None:
    def build(*, period_left: float, period_bottom: float) -> Any:
        features = [
            _feature(0, "TABLE OF CONTENTS", page=112, role="section_header"),
            _feature(1, "3.14", page=112),
            _feature(2, ".", page=112),
            _feature(3, "Measurement of Water", page=112),
            _feature(4, ".....", page=112),
            _feature(5, "24", page=112),
            _feature(6, "i", page=112, role="page_footer", layer="furniture"),
            _feature(7, "3.14. Measurement of Water", page=117, role="section_header"),
            _feature(8, "Body", page=117),
            _feature(9, "1", page=117, role="page_footer", layer="furniture"),
        ]
        features[1]["bbox"].update({"l": 83.0, "r": 104.0, "b": 282.3, "t": 290.4})
        features[2]["bbox"].update(
            {"l": period_left, "r": period_left + 1.0, "b": period_bottom, "t": 283.5}
        )
        return build_visible_toc(features, ())

    for result in (
        build(period_left=108.0, period_bottom=282.4),
        build(period_left=105.5, period_bottom=280.0),
    ):
        assert not result.entries
        assert any(item["code"] == "TOC_ROW_UNPARSEABLE" for item in result.diagnostics)


def test_terminal_page_token_is_not_reclassified_as_next_numeric_marker() -> None:
    features = [
        _feature(0, "TABLE OF CONTENTS", page=112, role="section_header"),
        _feature(1, "1.01.", page=112),
        _feature(2, "Definitions", page=112),
        _feature(3, ".....", page=112),
        _feature(4, "24", page=112),
        _feature(5, "24", page=112),
        _feature(6, "1.02.", page=112),
        _feature(7, "Parties", page=112),
        _feature(8, ".....", page=112),
        _feature(9, "25", page=112),
        _feature(10, "i", page=112, role="page_footer", layer="furniture"),
        _feature(11, "Article 1. Parties", page=117, role="section_header"),
        _feature(12, "Body", page=117),
        _feature(13, "1", page=117, role="page_footer", layer="furniture"),
    ]

    result = build_visible_toc(features, ())

    assert [entry["numbering_token"] for entry in result.entries] == ["1.01", "1.02"]
    assert [entry["printed_page"] for entry in result.entries] == ["24", "25"]
    assert any(
        diagnostic["stable_item_key"] == features[5]["stable_item_key"]
        and diagnostic["code"] == "TOC_ROW_UNPARSEABLE"
        for diagnostic in result.diagnostics
    )


def test_tiered_canonical_and_multi_item_body_matches_are_auditable() -> None:
    features = [
        _feature(0, "TABLE OF CONTENTS", page=112, role="section_header"),
        _feature(1, "7.05.", page=112),
        _feature(2, "Auditor’s Report", page=112),
        _feature(3, ".....", page=112),
        _feature(4, "1", page=112),
        _feature(5, "4.03.", page=112),
        _feature(6, "Transfers of Interim Supply Allocations", page=112),
        _feature(7, ".....", page=112),
        _feature(8, "1", page=112),
        _feature(9, "i", page=112, role="page_footer", layer="furniture"),
        _feature(10, "Article 1. Parties", page=117, role="section_header"),
        _feature(11, "Body", page=117),
        _feature(12, "7.05 Auditor's Report", page=117, role="section_header"),
        _feature(13, "4.03.", page=117),
        _feature(14, "Transfers of Interim Supply Allocations", page=117),
        _feature(15, "1", page=117, role="page_footer", layer="furniture"),
    ]

    result = build_visible_toc(features, ())

    assert [item["state"] for item in result.reconciliations] == ["exact", "exact"]
    assert [item["match_basis"] for item in result.reconciliations] == [
        "typographic_canonical",
        "multi_item_heading",
    ]
    multi = result.reconciliations[1]
    assert features[13]["raw_role"] == "text"
    assert multi["target_key"] == features[13]["stable_item_key"]
    assert multi["target_evidence_keys"] == [
        features[13]["stable_item_key"],
        features[14]["stable_item_key"],
    ]


def test_native_pdf_bbox_exact_reconciles_one_glyph_docling_tail_artifact() -> None:
    features = [
        _feature(0, "TABLE OF CONTENTS", page=112, role="section_header"),
        _feature(1, "6.2.3", page=112),
        _feature(2, "Scenario 3: Implementation of the Proposed Voluntary Agreement", page=112),
        _feature(3, ".....", page=112),
        _feature(4, "57", page=112),
        _feature(5, "i", page=112, role="page_footer", layer="furniture"),
        _feature(
            6,
            "6.2.3 Scenario 3: Implementation of the Proposed Voluntary Agreement t",
            page=117,
            role="section_header",
        ),
        _feature(7, "Body", page=117),
        _feature(8, "57", page=117, role="page_footer", layer="furniture"),
    ]
    clean = "6.2.3 scenario 3: implementation of the proposed voluntary agreement"
    outlines = (_outline(0, clean, 117, parent=None, depth=5),)
    native = {
        features[6]["stable_item_key"]: {
            "physical_page": 117,
            "bbox": dict(features[6]["bbox"]),
            "normalized_text": clean,
        }
    }

    result = build_visible_toc(features, outlines, native_heading_observations=native)

    reconciliation = result.reconciliations[0]
    assert reconciliation["state"] == "exact"
    assert reconciliation["match_basis"] == "native_pdf_bbox_exact"
    assert reconciliation["target_key"] == features[6]["stable_item_key"]
    assert reconciliation["native_pdf_evidence"] == {
        **native[features[6]["stable_item_key"]],
        "outline_ids": ["outline-00000000"],
    }
    assert result.features[6]["text"].endswith(" t")


def test_native_pdf_bbox_match_rejects_nonexact_or_nonunique_evidence() -> None:
    def build(*, suffix: str, native_text: str, duplicate: bool = False) -> Any:
        features = [
            _feature(0, "TABLE OF CONTENTS", page=112, role="section_header"),
            _feature(1, "6.2.3", page=112),
            _feature(2, "Scenario 3", page=112),
            _feature(3, ".....", page=112),
            _feature(4, "57", page=112),
            _feature(5, "i", page=112, role="page_footer", layer="furniture"),
            _feature(6, "1 Start", page=117, role="section_header"),
            _feature(7, "Intro", page=117),
            _feature(8, f"6.2.3 Scenario 3{suffix}", page=117, role="section_header"),
            _feature(9, "Body", page=117),
            _feature(10, "1", page=117, role="page_footer", layer="furniture"),
        ]
        if duplicate:
            features.insert(9, _feature(11, "6.2.3 Scenario 3 t", page=117, role="section_header"))
        native = {
            feature["stable_item_key"]: {
                "physical_page": 117,
                "bbox": dict(feature["bbox"]),
                "normalized_text": native_text,
            }
            for feature in features
            if feature["text"].startswith("6.2.3")
        }
        return build_visible_toc(features, (), native_heading_observations=native)

    for result in (
        build(suffix=" trailing", native_text="6.2.3 scenario 3"),
        build(suffix=" t", native_text="6.2.3 scenario 3 differs"),
        build(suffix=" t", native_text="6.2.3 scenario 3", duplicate=True),
    ):
        assert result.reconciliations[0]["state"] == "missing"
        assert result.reconciliations[0]["native_pdf_evidence"] is None


def test_toc_row_parser_rejection_branches_keep_source_specific_diagnostics() -> None:
    scenarios = (
        ([(_feature(1, "7", page=1))], "TOC row starts without marker or title"),
        (
            [
                _feature(1, "Introduction", page=1),
                _feature(2, "TABLE OF CONTENTS (CONTINUED)", page=1, role="section_header"),
            ],
            "continued TOC heading interrupts a row",
        ),
        (
            [_feature(1, "Unexpected heading", page=1, role="section_header")],
            "unexpected heading in TOC",
        ),
        (
            [_feature(1, "Introduction", page=1), _feature(2, "7", page=1)],
            "TOC row has a page token before its leader",
        ),
        (
            [_feature(1, "Appendix A", page=1, role="section_header")],
            "TOC row has no title",
        ),
        (
            [
                _feature(1, "Introduction", page=1),
                _feature(2, ".....", page=1),
                _feature(3, "not a page", page=1),
            ],
            "TOC leader is not followed by one page token",
        ),
        (
            [
                _feature(1, "1", page=1),
                _feature(2, "Project 2025", page=1),
                _feature(3, ".....", page=1),
                _feature(4, "7", page=1),
            ],
            "TOC title contains inseparable trailing digits",
        ),
    )

    for items, detail in scenarios:
        header = _feature(0, "TABLE OF CONTENTS", page=1, role="section_header")
        boundary_order = max(item["reading_order_index"] for item in items) + 1
        features = [header, *items, _feature(boundary_order, "Body", page=2)]
        region = TocRegion(
            0, len(features) - 1, len(features), header["stable_item_key"], None, None
        )

        entries, diagnostics = parse_toc_region(features, region, ())

        assert entries == []
        assert diagnostics
        assert {item["detail"] for item in diagnostics} == {detail}


def test_reconciliation_validation_keeps_page_level_and_order_conflicts_distinct() -> None:
    source_a = _feature(1, "row a", page=1)
    source_b = _feature(2, "row b", page=1)
    target_a = _feature(3, "1 Alpha", page=8, role="section_header")
    target_b = _feature(4, "2 Beta", page=9, role="section_header")
    features = [
        _feature(0, "TABLE OF CONTENTS", page=1, role="section_header"),
        source_a,
        source_b,
        target_a,
        target_b,
    ]
    region = TocRegion(0, 3, 5, features[0]["stable_item_key"], None, None)

    def entry(
        entry_id: str,
        source: dict[str, Any],
        marker: str,
        title: str,
        *,
        depth: int = 1,
        printed_page: str | None = None,
    ) -> dict[str, Any]:
        return {
            "toc_entry_id": entry_id,
            "source_item_keys": [source["stable_item_key"]],
            "reading_order_index": source["reading_order_index"],
            "title_with_marker_normalized": f"{marker} {title}",
            "title_without_marker_normalized": title,
            "numbering_token": marker,
            "depth": depth,
            "depth_source": "numbering",
            "printed_page": printed_page,
        }

    page_records, _ = reconcile_toc_entries(
        [entry("page", source_a, "1", "alpha", printed_page="7")],
        features,
        (region,),
        (),
        {8: "8"},
        {},
    )
    level_records, _ = reconcile_toc_entries(
        [entry("level", source_a, "1", "alpha", depth=1)],
        features,
        (region,),
        (_outline(0, "1 Alpha", 8, parent="root", depth=2),),
        {},
        {},
    )
    order_records, _ = reconcile_toc_entries(
        [
            entry("first", source_a, "2", "beta"),
            entry("second", source_b, "1", "alpha"),
        ],
        features,
        (region,),
        (),
        {},
        {},
    )

    assert page_records[0]["state"] == "page_conflict"
    assert level_records[0]["state"] == "level_conflict"
    assert [item["state"] for item in order_records] == ["exact", "order_conflict"]


def test_composite_appendices_are_individual_and_attachment_list_is_not_a_row() -> None:
    features = [_feature(0, "TABLE OF CONTENTS", page=112, role="section_header")]
    order = 1
    for letter in "ABCDE":
        features.append(_feature(order, f"Appendix {letter}", page=112))
        order += 1
        features.append(_feature(order, f"Description {letter}", page=112))
        order += 1
    features.extend(
        [
            _feature(order, "LIST OF ATTACHMENTS", page=112, role="section_header"),
            _feature(order + 1, "M-2 Attachment", page=112, role="list_item"),
            _feature(order + 2, "i", page=112, role="page_footer", layer="furniture"),
            _feature(order + 3, "Article 1. Parties", page=117, role="section_header"),
            _feature(order + 4, "Body", page=117),
            _feature(order + 5, "1", page=117, role="page_footer", layer="furniture"),
        ]
    )
    order += 6
    for letter in "ABCDE":
        features.append(
            _feature(order, f"Appendix {letter}", page=117 + order, role="section_header")
        )
        order += 1
        features.append(_feature(order, f"Description {letter}", page=117 + order))
        order += 1

    result = build_visible_toc(features, ())

    assert [entry["numbering_token"] for entry in result.entries] == [
        "Appendix A",
        "Appendix B",
        "Appendix C",
        "Appendix D",
        "Appendix E",
    ]
    assert all(item["state"] == "exact" for item in result.reconciliations)
    assert all(item["match_basis"] == "composite_appendix" for item in result.reconciliations)
    assert all(
        "m-2 attachment" not in entry["title_without_marker_normalized"] for entry in result.entries
    )
    assert any(
        diagnostic["stable_item_key"] == features[12]["stable_item_key"]
        and diagnostic["code"] == "TOC_ROW_UNPARSEABLE"
        for diagnostic in result.diagnostics
    )


def test_footer_policy_prefers_page_of_total_then_standalone_token() -> None:
    def text(index: int, value: str, page: int) -> dict[str, Any]:
        return {
            "self_ref": f"#/texts/{index}",
            "parent": {"$ref": "#/furniture"},
            "label": "page_footer",
            "text": value,
            "orig": value,
            "content_layer": "furniture",
            "prov": [
                {
                    "page_no": page,
                    "bbox": {
                        "l": 1,
                        "t": 2,
                        "r": 3,
                        "b": 1,
                        "coord_origin": "BOTTOMLEFT",
                    },
                    "charspan": [0, len(value)],
                }
            ],
        }

    document = {
        "texts": [
            text(0, "January 2025", 1),
            text(1, "Page 7 of 99", 1),
            text(2, "C40174.00", 1),
            text(3, "2021 Amended WSA", 2),
            text(4, "iv", 2),
            text(5, "17162043.1", 2),
        ]
    }
    assert unique_footer_labels(document) == {1: "7", 2: "iv"}


def test_nested_article_regime_starts_at_article_one_and_updates_alpha_depth() -> None:
    features = [
        _feature(0, "2 Previous", page=1, role="section_header"),
        _feature(1, "APPENDIX D", page=2, role="section_header", outline_state="unique_exact"),
        _feature(2, "Agreement title", page=3, role="section_header"),
        _feature(3, "Article 1. Parties", page=4, role="section_header"),
        _feature(4, "A. Definitions", page=4, role="section_header"),
        _feature(5, "Body", page=4),
    ]
    features[3]["printed_page_label"] = "1"
    outlines = (_outline(0, "APPENDIX D", 2, parent="outline-parent"),)
    result = build_numbering_regimes(features, outlines)

    assert len(result.regimes) == 2
    nested = result.regimes[1]
    assert nested["start_item_key"] == features[3]["stable_item_key"]
    assert nested["outline_anchor_key"] == features[1]["stable_item_key"]
    assert nested["page_label_reset"] is True
    assert result.features[4]["regime_id"] == nested["regime_id"]
    assert result.features[4]["numbering_kind"] == "upper_alpha"
    assert result.features[4]["numbering_depth"] == 3


def test_initial_regime_assigns_pre_body_furniture_but_starts_at_first_body() -> None:
    features = [
        _feature(
            0,
            "Repeated header",
            page=1,
            role="page_header",
            layer="furniture",
            parent="#/furniture",
        ),
        _feature(1, "1 Introduction", page=1, role="section_header"),
        _feature(2, "Body", page=1),
    ]

    result = build_numbering_regimes(features, ())

    assert result.regimes[0]["start_item_key"] == features[1]["stable_item_key"]
    assert {item["regime_id"] for item in result.features} == {result.regimes[0]["regime_id"]}


def _brute_nested_candidates(
    features: list[dict[str, Any]], outlines: tuple[dict[str, Any], ...], after_last: int
) -> list[NumberingScopeCandidate]:
    """Preserve the pre-indexing candidate algorithm as a small semantic oracle."""
    anchors = [
        feature
        for feature in features
        if feature["content_layer"] == "body"
        and not feature.get("toc_region", False)
        and feature["outline_state"] == "unique_exact"
    ]
    candidates: list[NumberingScopeCandidate] = []
    for anchor_index, anchor in enumerate(anchors):
        next_anchor_order = (
            anchors[anchor_index + 1]["reading_order_index"]
            if anchor_index + 1 < len(anchors)
            else after_last
        )
        numbered = next(
            (
                feature
                for feature in features
                if anchor["reading_order_index"]
                < feature["reading_order_index"]
                < next_anchor_order
                and feature["content_layer"] == "body"
                and feature["raw_role"] == "section_header"
                and parse_numbering(feature["text"], raw_role=feature["raw_role"]).kind
                not in {"none", "bullet"}
            ),
            None,
        )
        if numbered is None:
            continue
        evidence = parse_numbering(numbered["text"], raw_role=numbered["raw_role"])
        is_start = (evidence.kind == "article" and evidence.token == "1") or (
            evidence.kind == "decimal" and evidence.token == "1" and evidence.depth == 1
        )
        prior_markers = [
            parse_numbering(feature["text"], raw_role=feature["raw_role"])
            for feature in features
            if feature["reading_order_index"] < anchor["reading_order_index"]
            and feature["raw_role"] == "section_header"
            and not feature.get("toc_region", False)
        ]
        has_different_marker = any(
            item.kind in {"article", "decimal"}
            and item.depth == 1
            and (item.kind, item.token) != (evidence.kind, evidence.token)
            for item in prior_markers
        )
        if not is_start or not has_different_marker:
            continue
        outline_matches = [
            item
            for item in outlines
            if item["physical_page"] == anchor["physical_page"]
            and item["normalized_title"] == anchor["normalized_text"]
        ]
        if len(outline_matches) != 1:
            continue
        outline_position = outlines.index(outline_matches[0])
        later_boundary = next(
            (
                item
                for item in outlines[outline_position + 1 :]
                if item["raw_depth"] <= outline_matches[0]["raw_depth"]
            ),
            None,
        )
        end = after_last
        if later_boundary is not None:
            end_matches = [
                feature
                for feature in features
                if feature["physical_page"] == later_boundary["physical_page"]
                and feature["normalized_text"] == later_boundary["normalized_title"]
                and feature["outline_state"] == "unique_exact"
            ]
            if len(end_matches) != 1:
                continue
            end = end_matches[0]["reading_order_index"]
        if numbered["reading_order_index"] < end:
            candidates.append(
                NumberingScopeCandidate(
                    start=numbered["reading_order_index"],
                    end=end,
                    anchor_key=anchor["stable_item_key"],
                    article=evidence.kind == "article",
                )
            )
    return candidates


def test_indexed_numbering_candidates_match_brute_force_semantics() -> None:
    features = [
        _feature(0, "2 Previous", page=1, role="section_header"),
        _feature(1, "APPENDIX D", page=2, role="section_header", outline_state="unique_exact"),
        _feature(2, "Article 1. Parties", page=3, role="section_header"),
        _feature(3, "Body", page=3),
        _feature(4, "APPENDIX E", page=4, role="section_header", outline_state="unique_exact"),
        _feature(5, "1 Introduction", page=5, role="section_header"),
        _feature(6, "Body", page=5),
    ]
    outlines = (
        _outline(0, "APPENDIX D", 2, parent="root", depth=2),
        _outline(1, "APPENDIX E", 4, parent="root", depth=2),
    )
    after_last = len(features)

    assert _nested_candidates(features, outlines, after_last) == _brute_nested_candidates(
        features, outlines, after_last
    )


def test_materialized_regimes_preserve_nested_and_peer_parentage() -> None:
    features = [_feature(order, f"item {order}", page=1) for order in range(8)]
    candidates = [
        NumberingScopeCandidate(start=1, end=7, anchor_key="outer", article=False),
        NumberingScopeCandidate(start=2, end=4, anchor_key="nested-a", article=False),
        NumberingScopeCandidate(start=4, end=7, anchor_key="nested-b", article=False),
    ]

    result = _materialize_regimes(
        features=features,
        candidates=candidates,
        initial_start=0,
        after_last=8,
        initial_id="initial",
        initial_item_key=features[0]["stable_item_key"],
    )

    initial, outer, nested_a, nested_b = result.regimes
    assert outer["parent_regime_id"] == initial["regime_id"]
    assert nested_a["parent_regime_id"] == outer["regime_id"]
    assert nested_b["parent_regime_id"] == outer["regime_id"]


def test_scope_assignment_preserves_first_materialized_regime_for_tied_starts() -> None:
    features = [_feature(order, f"item {order}", page=1) for order in range(4)]

    projected = _assign_innermost_regimes(
        features,
        {
            "initial": (0, 4),
            "first-tied": (1, 3),
            "second-tied": (1, 3),
        },
        frozenset(),
    )

    assert [item["regime_id"] for item in projected] == [
        "initial",
        "first-tied",
        "first-tied",
        "initial",
    ]
