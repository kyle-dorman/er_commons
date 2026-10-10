"""Mixed-source closure must never discard a table, figure or limiting narrative."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from er_commons.group_evidence_mixed import assemble_mixed_section, validate_mixed_section
from er_commons.pilot_citation_units import validate_units


@pytest.fixture
def mixed(tmp_path: Path):
    """Build two-page mixed text, complete table and uninterpreted figure context."""
    common = dict(
        document_id="ex/document/deir_main",
        extraction_id="ex",
        section_id="s1",
        regions=[{"page_id": "ex/page/deir_main/p00001"}],
    )
    blocks = [
        {
            **common,
            "id": i,
            "block_type": kind,
            "content_layer": "body",
            "sequence": n,
            "canonical_text": text,
        }
        for n, (i, kind, text) in enumerate(
            [
                ("h1", "heading", "Forecast"),
                ("b1", "paragraph", "Conditional forecast."),
                ("cap", "caption", "Table 1"),
                ("note", "paragraph", "Assumes future growth."),
                ("fcap", "caption", "Figure 1"),
                ("h2", "heading", "Next"),
            ]
        )
    ]
    blocks[-1]["section_id"] = "s2"
    table = {
        **common,
        "id": "t1",
        "cells": [
            {"text": "AM", "row_index": 0, "column_index": 0},
            {"text": "12", "row_index": 0, "column_index": 1},
        ],
        "table_family_id": "fam1",
    }
    figure = {**common, "id": "f1", "regions": [{"page_id": "ex/page/deir_main/p00002"}]}
    section = {
        "id": "s1",
        "heading_block_id": "h1",
        "section_path_ids": ["s1"],
        "ordered_child_ids": ["h1", "b1", "cap", "t1", "note", "f1", "fcap"],
    }
    files = {}
    for kind, rows in [
        ("blocks", blocks),
        ("sections", [section]),
        ("tables", [table]),
        ("figures", [figure]),
    ]:
        path = tmp_path / (kind + ".jsonl")
        path.write_text("\n".join(json.dumps(r) for r in rows))
        files[kind] = {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    source = {"source_id": "deir_main", "extraction_id": "ex", "files": files}
    args = dict(
        source=source,
        section_id="s1",
        data_root=tmp_path,
        printed_labels_by_page={1: "1", 2: "2"},
        metadata={"pdf_url": "https://example.org/source.pdf"},
    )
    return assemble_mixed_section(**args)[0], args


def test_mixed_complete_closure(mixed):
    """Table cells and context remain ordered while figure content is never invented."""
    candidate, args = mixed
    validate_units([candidate], args["data_root"])
    assert candidate["physical_pages"] == [1, 2]
    assert (
        candidate["quote"] == "Forecast\n\nConditional forecast.\n\nTable 1\n\nAM\n\n12\n\n"
        "Assumes future growth.\n\nFigure 1"
    )
    assert candidate["citation_unit"]["kind"] == "table"
    assert candidate["display_segments"][5]["kind"] == "figure"


def test_mixed_source_display_keeps_tables_and_figures(mixed):
    """Full source display retains table cells, narrative and figure link in order."""
    from er_commons.pilot_evidence import _source_excerpt_html

    candidate, _ = mixed
    candidate.update(source_url=candidate["pdf_url"], edition="Synthetic Draft")
    rendered = _source_excerpt_html(candidate, "S1")
    assert rendered.index("Conditional forecast.") < rendered.index("<td>12</td>")
    assert rendered.index("<td>12</td>") < rendered.index("Assumes future growth.")
    assert rendered.index("Assumes future growth.") < rendered.index("Figure — open original PDF")


@pytest.mark.parametrize(
    "field",
    [
        "anchors",
        "quote",
        "physical_pages",
        "figure_refs",
        "table_ids",
        "display_segments",
        "source_id",
        "section_member_record_ids",
    ],
)
def test_mixed_mutation_rejected(mixed, field):
    """Every context type and source binding is fail-closed when altered."""
    candidate, args = copy.deepcopy(mixed)
    if field in ["figure_refs", "table_ids", "section_member_record_ids"]:
        candidate["citation_unit"][field] = []
    else:
        candidate[field] = [] if isinstance(candidate[field], list) else "altered"
    with pytest.raises((ValueError, KeyError)):
        validate_mixed_section(candidate, args["data_root"])


def test_mixed_missing_family_rejected(mixed):
    """A continuation outside the section cannot be silently omitted."""
    _, args = mixed
    path = args["data_root"] / "tables.jsonl"
    row = json.loads(path.read_text())
    other = {**row, "id": "t2", "section_id": "s2"}
    path.write_text(json.dumps(row) + "\n" + json.dumps(other))
    args["source"]["files"]["tables"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="continuation"):
        assemble_mixed_section(**args)


def test_mixed_heading_crossing_rejected(mixed):
    """No audit override silently changes a canonical heading boundary."""
    _, args = mixed
    path = args["data_root"] / "blocks.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[3]["sequence"] = 7
    path.write_text("\n".join(json.dumps(row) for row in rows))
    args["source"]["files"]["blocks"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="crosses"):
        assemble_mixed_section(**args)
