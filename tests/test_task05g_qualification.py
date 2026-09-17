"""Source-free supplemental-alias qualification boundaries."""

from copy import deepcopy

from er_commons.response_inventory.reference_replay_qualification import (
    qualify_supplemental_aliases,
)


def evidence():
    page = {"id": "p1", "document_id": "doc", "printed_page_label": None}
    caption = {
        "id": "b1",
        "document_id": "doc",
        "section_id": "s1",
        "block_type": "caption",
        "content_layer": "body",
        "is_toc_row": False,
        "canonical_text": "Table C-8. Mode Share Comparisons",
        "regions": [{"page_id": "p1", "bbox": [10, 80, 100, 90]}],
    }
    table = {
        "id": "t1",
        "document_id": "doc",
        "section_id": "s1",
        "content_layer": "body",
        "is_toc_row": False,
        "regions": [{"page_id": "p1", "bbox": [10, 20, 100, 75]}],
    }
    return {
        "source_id": "synthetic",
        "source_ordinal": 1,
        "candidate_id": "candidate",
        "blocks": [caption],
        "tables": [table],
        "pages": [page],
    }


def test_alphabetic_caption_is_qualified_without_mutation():
    inputs = evidence()
    old = deepcopy(inputs)
    rows = qualify_supplemental_aliases(**inputs)
    assert len(rows) == 1
    assert rows[0]["target_id"] == "t1"
    assert rows[0]["evidence_record_ids"] == ["b1", "t1"]
    assert inputs == old
    assert qualify_supplemental_aliases(**inputs) == rows


def test_overlap_and_different_section_rejected():
    inputs = evidence()
    inputs["tables"][0]["regions"][0]["bbox"][3] = 83
    assert qualify_supplemental_aliases(**inputs) == []
    inputs = evidence()
    inputs["tables"][0]["section_id"] = "other"
    assert qualify_supplemental_aliases(**inputs) == []


def test_intervening_prose_toc_and_missing_page_rejected():
    inputs = evidence()
    block = deepcopy(inputs["blocks"][0])
    block.update(id="b2", canonical_text="ordinary prose", block_type="paragraph")
    block["regions"][0]["bbox"] = [10, 76, 100, 78]
    inputs["blocks"].append(block)
    assert qualify_supplemental_aliases(**inputs) == []
    inputs = evidence()
    inputs["blocks"][0]["is_toc_row"] = True
    assert qualify_supplemental_aliases(**inputs) == []
    inputs = evidence()
    inputs["pages"] = []
    assert qualify_supplemental_aliases(**inputs) == []


def footer_inputs():
    inputs = evidence()
    inputs["tables"] = []
    inputs["blocks"][0].update(
        block_type="page_footer", content_layer="furniture", canonical_text="2-21"
    )
    return inputs


def test_footer_is_specific_page_not_document():
    rows = qualify_supplemental_aliases(**footer_inputs())
    assert len(rows) == 1
    assert rows[0]["lookup_key"] == "page 2-21"
    assert rows[0]["target_type"] == "page"
    assert rows[0]["target_id"] == "p1"


def test_conflicting_canonical_and_duplicate_footer_pages_rejected():
    inputs = footer_inputs()
    inputs["pages"][0]["printed_page_label"] = "2-22"
    assert qualify_supplemental_aliases(**inputs) == []
    inputs = footer_inputs()
    inputs["pages"].append({"id": "p2", "document_id": "doc", "printed_page_label": "2-21"})
    assert qualify_supplemental_aliases(**inputs) == []
    inputs = footer_inputs()
    second = deepcopy(inputs["blocks"][0])
    second.update(id="b2", canonical_text="3-21")
    inputs["blocks"].append(second)
    assert qualify_supplemental_aliases(**inputs) == []


def test_numeric_table_caption_reuses_geometry():
    inputs = evidence()
    inputs["blocks"][0]["canonical_text"] = "Table 6: Parking"
    assert len(qualify_supplemental_aliases(**inputs)) == 1


def test_appendix_scope_comes_from_heading_ancestry():
    inputs = evidence()
    heading = deepcopy(inputs["blocks"][0])
    heading.update(
        id="heading", canonical_text="Appendix C.2. Mode Share Methodology", block_type="heading"
    )
    heading["regions"][0]["bbox"] = [10, 95, 100, 100]
    inputs["blocks"].append(heading)
    inputs["sections"] = [
        {"id": "s1", "document_id": "doc", "heading_block_id": "heading", "parent_section_id": None}
    ]
    rows = qualify_supplemental_aliases(**inputs)
    assert rows[0]["inner_appendix_identifier"] == "c.2"
    assert rows[0]["evidence_record_ids"] == ["b1", "t1", "s1", "heading"]


def test_same_caption_for_two_tables_does_not_select_one():
    inputs = evidence()
    caption = deepcopy(inputs["blocks"][0])
    caption["id"] = "b2"
    caption["regions"][0]["page_id"] = "p2"
    table = deepcopy(inputs["tables"][0])
    table["id"] = "t2"
    table["regions"][0]["page_id"] = "p2"
    inputs["blocks"].append(caption)
    inputs["tables"].append(table)
    inputs["pages"].append({"id": "p2", "document_id": "doc", "printed_page_label": None})
    rows = qualify_supplemental_aliases(**inputs)
    assert {row["target_id"] for row in rows} == {"t1", "t2"}
    from types import SimpleNamespace

    from er_commons.response_inventory.reference_replay_inner import propose_inner

    existing = {
        "lookup_key": "table c-8. mode share comparisons",
        "target_id": "t1",
        "target_type": "table",
        "source_id": "synthetic",
    }
    proposal = propose_inner(
        SimpleNamespace(before="Table C-8 of ", after=""), ["synthetic"], [existing, *rows]
    )
    assert {row["target_id"] for row in proposal.candidates} == {"t1", "t2"}
    assert proposal.selected is None


def test_body_number_is_not_footer_evidence():
    inputs = footer_inputs()
    inputs["blocks"][0].update(block_type="paragraph", content_layer="body")
    assert qualify_supplemental_aliases(**inputs) == []


def test_figure_and_prose_are_not_table_aliases():
    for text in ["Figure C-8. Example", "Table are also included", "Table C-8x. Example"]:
        inputs = evidence()
        inputs["blocks"][0]["canonical_text"] = text
        assert qualify_supplemental_aliases(**inputs) == []
