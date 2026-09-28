"""Section citations are complete parsed units, independent of support decisions."""

import copy
import json
from pathlib import Path

import pytest

from er_commons.pilot_citation_units import validate_units
from er_commons.pilot_evidence import _source_excerpt_html


@pytest.fixture
def section_candidate(tmp_path: Path):
    """Provide a section followed by two headings to detect dishonest boundaries."""
    blocks = [
        {
            "id": identity,
            "canonical_text": text,
            "block_type": kind,
            "sequence": i,
            "section_id": "s1" if i < 2 else f"s{i}",
            "content_layer": "body",
            "document_id": "ex/document/source",
        }
        for i, (identity, text, kind) in enumerate(
            [
                ("h1", "1.1 Existing setting", "heading"),
                ("b1", "Existing emissions.", "paragraph"),
                ("h2", "1.2 Future setting", "heading"),
                ("h3", "1.3 Other setting", "heading"),
            ]
        )
    ]
    section = {
        "id": "s1",
        "document_id": "ex/document/source",
        "heading_block_id": "h1",
        "ordered_child_ids": ["h1", "b1"],
        "section_path_ids": ["s1"],
    }
    (tmp_path / "blocks.jsonl").write_text("\n".join(json.dumps(b) for b in blocks))
    (tmp_path / "sections.jsonl").write_text(json.dumps(section))

    def anchor(block):
        return {
            "path": "blocks.jsonl",
            "record_id_field": "id",
            "record_id": block["id"],
            "record": block,
            "text_field": "canonical_text",
            "start": 0,
            "end": len(block["canonical_text"]),
            "quote": block["canonical_text"],
        }

    unit = {
        "schema_version": "er_commons.task07d.citation_unit.v1",
        "kind": "section",
        "boundary_policy": "heading_to_next_heading_exclusive",
        "section_id": "s1",
        "section_record": {
            "path": "sections.jsonl",
            "record_id_field": "id",
            "record_id": "s1",
            "record": section,
        },
        "heading_anchor": anchor(blocks[0]),
        "next_heading_anchor": anchor(blocks[2]),
        "start_block_id": "h1",
        "breadcrumb": [
            {
                "section_id": "s1",
                "heading_block_id": "h1",
                "heading_text": blocks[0]["canonical_text"],
            }
        ],
        "section_member_record_ids": ["h1", "b1"],
        "member_record_ids": ["h1", "b1"],
        "separately_cited_units": [],
        "citation_label": "1.1 Existing setting (pp. 1)",
        "table_id": None,
    }
    candidate = {
        "citation_unit": unit,
        "anchors": [anchor(b) for b in blocks[:2]],
        "quote": "\n\n".join(b["canonical_text"] for b in blocks[:2]),
        "source_id": "source",
        "source_url": "https://example.org/source.pdf",
        "edition": "Draft",
        "physical_pages": [1],
        "printed_labels": ["1"],
        "limitations": [],
        "title": "Invented old title",
    }
    return candidate, tmp_path, anchor(blocks[3])


def test_complete_section_and_canonical_heading_render(section_candidate):
    candidate, root, _ = section_candidate
    validate_units([candidate], root)
    rendered = _source_excerpt_html(candidate, "E01")
    assert "1.1 Existing setting" in rendered
    assert "Invented old title" not in rendered
    assert "1.2 Future setting" not in rendered


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_unit",
        "wrong_next",
        "next_included",
        "missing_body",
        "partial_block",
        "forged_membership",
        "forged_exclusion",
        "wrong_breadcrumb",
        "wrong_label",
        "wrong_source",
    ],
)
def test_rejects_incomplete_or_cross_section_units(section_candidate, mutation):
    candidate, root, later = copy.deepcopy(section_candidate)
    unit = candidate["citation_unit"]
    if mutation == "missing_unit":
        candidate.pop("citation_unit")
    elif mutation == "wrong_next":
        unit["next_heading_anchor"] = later
    elif mutation == "next_included":
        candidate["anchors"].append(unit["next_heading_anchor"])
        unit["member_record_ids"].append("h2")
    elif mutation == "missing_body":
        candidate["anchors"].pop()
        unit["member_record_ids"].pop()
    elif mutation == "partial_block":
        candidate["anchors"][1]["end"] -= 1
    elif mutation == "forged_membership":
        unit["section_member_record_ids"].pop()
    elif mutation == "wrong_label":
        unit["citation_label"] = "Invented title"
    elif mutation == "wrong_source":
        candidate["source_id"] = "other"
    elif mutation == "wrong_breadcrumb":
        unit["breadcrumb"][0]["heading_text"] = "Different section"
    else:
        unit["separately_cited_units"] = [
            {"kind": "table", "table_id": "fake", "member_record_ids": ["b1"]}
        ]
    with pytest.raises(ValueError):
        validate_units([candidate], root)


@pytest.mark.parametrize("omit", [None, "note", "cell"])
def test_table_preserves_caption_notes_and_cells(section_candidate, omit):
    candidate, root, _ = section_candidate
    blocks = [json.loads(line) for line in (root / "blocks.jsonl").read_text().splitlines()]
    blocks[1]["block_type"] = "caption"
    blocks[1]["canonical_text"] = "Table 1. Existing emissions"
    note = {
        **blocks[1],
        "id": "note",
        "sequence": 1.5,
        "block_type": "paragraph",
        "canonical_text": "Note: totals include existing uses.",
    }
    blocks.append(note)
    (root / "blocks.jsonl").write_text("\n".join(json.dumps(b) for b in blocks))
    table = {
        "id": "t1",
        "section_id": "s1",
        "document_id": "ex/document/source",
        "cells": [{"text": "Emissions"}, {"text": "10"}],
    }
    (root / "tables.jsonl").write_text(json.dumps(table))
    unit = candidate["citation_unit"]
    section = unit["section_record"]["record"]
    section["ordered_child_ids"] = ["h1", "b1", "t1", "note"]
    (root / "sections.jsonl").write_text(json.dumps(section))
    unit.update(
        citation_label="Table 1. Existing emissions (pp. 1)",
        kind="table",
        table_id="t1",
        section_member_record_ids=section["ordered_child_ids"],
        member_record_ids=["b1", "note", "t1"],
    )

    def anchor(block):
        return {
            "path": "blocks.jsonl",
            "record_id_field": "id",
            "record_id": block["id"],
            "record": block,
            "text_field": "canonical_text",
            "start": 0,
            "end": len(block["canonical_text"]),
            "quote": block["canonical_text"],
        }

    candidate["anchors"] = [anchor(blocks[1]), anchor(note)] + [
        {
            "path": "tables.jsonl",
            "record_id_field": "id",
            "record_id": "t1",
            "record": table,
            "text_field": f"cells.{i}.text",
            "start": 0,
            "end": len(cell["text"]),
            "quote": cell["text"],
        }
        for i, cell in enumerate(table["cells"])
    ]
    if omit == "note":
        candidate["anchors"].pop(1)
        unit["member_record_ids"].remove("note")
    elif omit == "cell":
        candidate["anchors"].pop()
    if omit:
        with pytest.raises(ValueError):
            validate_units([candidate], root)
    else:
        validate_units([candidate], root)


@pytest.fixture
def audited_multi_table(section_candidate):
    """Bind two tables with intervening prose to an immutable explicit receipt."""
    import hashlib

    candidate, root, _ = section_candidate
    blocks = [json.loads(line) for line in (root / "blocks.jsonl").read_text().splitlines()]
    base = blocks[0]
    content = [
        ("h1", "heading", "Operations"),
        ("intro", "paragraph", "Intro"),
        ("c1", "caption", "Table 1"),
        ("n1", "footnote", "Note one"),
        ("middle", "paragraph", "Interpretation between tables"),
        ("c2", "caption", "Table 2"),
        ("n2", "paragraph", "SOURCE: two"),
        ("h2", "heading", "Next section"),
    ]
    blocks = [
        {
            **base,
            "id": i,
            "block_type": k,
            "canonical_text": t,
            "sequence": n,
            "section_id": "s1" if i != "h2" else "s2",
        }
        for n, (i, k, t) in enumerate(content)
    ]
    by_id = {b["id"]: b for b in blocks}
    tables = [
        {
            "id": t,
            "section_id": "s1",
            "document_id": "ex/document/source",
            "cells": [{"text": "Value"}, {"text": "10"}],
        }
        for t in ["t1", "t2"]
    ]
    members = ["h1", "intro", "c1", "t1", "n1", "middle", "c2", "t2", "n2"]
    section = candidate["citation_unit"]["section_record"]["record"]
    section["ordered_child_ids"] = members
    for name, values in [("blocks", blocks), ("tables", tables), ("sections", [section])]:
        (root / (name + ".jsonl")).write_text("\n".join(json.dumps(v) for v in values))
    groups = [
        {"table_id": t, "caption_id": c, "note_record_ids": [n], "member_record_ids": [c, t, n]}
        for t, c, n in [("t1", "c1", "n1"), ("t2", "c2", "n2")]
    ]
    receipt = {
        "schema_version": "er_commons.task07d.table_associations.v1",
        "status": "audited",
        "audit_note": "Synthetic reviewed fixture",
        "heading_block_id": "h1",
        "next_heading_block_id": "h2",
        "source_id": "source",
        "section_id": "s1",
        "section_member_record_ids": members,
        "narrative_record_ids": ["h1", "intro", "middle"],
        "tables": groups,
        "canonical_files": {
            k: {
                "path": k + ".jsonl",
                "sha256": hashlib.sha256((root / (k + ".jsonl")).read_bytes()).hexdigest(),
            }
            for k in ["blocks", "sections", "tables"]
        },
    }
    (root / "association.json").write_text(json.dumps(receipt))
    binding = {
        "path": "association.json",
        "sha256": hashlib.sha256((root / "association.json").read_bytes()).hexdigest(),
    }

    def anchor(identity):
        """Build complete canonical block or cell anchors for the fixture."""
        if identity in by_id:
            b = by_id[identity]
            return [
                {
                    "path": "blocks.jsonl",
                    "record_id_field": "id",
                    "record_id": identity,
                    "record": b,
                    "text_field": "canonical_text",
                    "start": 0,
                    "end": len(b["canonical_text"]),
                    "quote": b["canonical_text"],
                }
            ]
        t = next(t for t in tables if t["id"] == identity)
        return [
            {
                "path": "tables.jsonl",
                "record_id_field": "id",
                "record_id": identity,
                "record": t,
                "text_field": f"cells.{i}.text",
                "start": 0,
                "end": len(c["text"]),
                "quote": c["text"],
            }
            for i, c in enumerate(t["cells"])
        ]

    result = []
    for table_id, ids in [(None, ["h1", "intro", "middle"])] + [
        (g["table_id"], g["member_record_ids"]) for g in groups
    ]:
        c = copy.deepcopy(candidate)
        u = c["citation_unit"]
        u.update(
            schema_version="er_commons.task07d.citation_unit.v2",
            table_association_receipt=binding,
            kind="table" if table_id else "section",
            table_id=table_id,
            section_member_record_ids=members,
            member_record_ids=ids,
            heading_anchor=anchor("h1")[0],
            next_heading_anchor=anchor("h2")[0],
            breadcrumb=[
                {"section_id": "s1", "heading_block_id": "h1", "heading_text": "Operations"}
            ],
            separately_cited_units=[]
            if table_id
            else [
                {
                    "kind": "table",
                    "table_id": g["table_id"],
                    "member_record_ids": g["member_record_ids"],
                }
                for g in groups
            ],
            citation_label=by_id[ids[0]]["canonical_text"] + " (pp. 1)",
        )
        c["anchors"] = [a for identity in ids for a in anchor(identity)]
        result.append(c)
    return result, root


@pytest.mark.parametrize(
    "mutation", [None, "dropped_note", "dropped_prose", "foreign_receipt", "receipt_tamper"]
)
def test_audited_multiple_tables(audited_multi_table, mutation):
    """Require all notes, intervening prose, and the exact source-bound audit receipt."""
    candidates, root = audited_multi_table
    if mutation in {"dropped_note", "dropped_prose"}:
        c = candidates[1 if mutation == "dropped_note" else 0]
        identity = "n1" if mutation == "dropped_note" else "middle"
        c["anchors"] = [a for a in c["anchors"] if a["record_id"] != identity]
        c["citation_unit"]["member_record_ids"].remove(identity)
    elif mutation == "foreign_receipt":
        import hashlib

        p = root / "association.json"
        r = json.loads(p.read_text())
        r["section_id"] = "foreign"
        p.write_text(json.dumps(r))
        for c in candidates:
            c["citation_unit"]["table_association_receipt"]["sha256"] = hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
    elif mutation == "receipt_tamper":
        (root / "association.json").write_text("{}")
    if mutation:
        with pytest.raises(ValueError):
            validate_units(candidates, root)
    else:
        validate_units(candidates, root)
