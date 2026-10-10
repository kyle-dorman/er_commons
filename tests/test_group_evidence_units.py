"""Invented heading-caption and continuation families never change canonical records."""

import copy
import hashlib
import json

import pytest

from er_commons import group_evidence_units as units
from er_commons import pilot_evidence as evidence
from er_commons.group_evidence_fixtures import prepare_qualification


@pytest.fixture
def family(tmp_path):
    """Create independent two-table family and an explicit audited render receipt."""
    root = tmp_path / "fixture"
    tasks = prepare_qualification(root)
    candidate = copy.deepcopy(tasks[1]["data"]["packet"]["candidates"][0])
    directory = root / "fixture2"
    blocks = [json.loads(line) for line in (directory / "blocks.jsonl").read_text().splitlines()]
    candidate["extraction_id"] = "synthetic"
    region = {"page_id": "synthetic/page/synthetic_2/p000001"}
    for block in blocks:
        block["regions"] = [region]
        if block["id"] == "b1":
            block["block_type"] = "heading"
    (directory / "blocks.jsonl").write_text("\n".join(json.dumps(b) for b in blocks))
    table = json.loads((directory / "tables.jsonl").read_text())
    table["regions"] = [region]
    table["table_family_id"] = "synthetic-family"
    continuation = {**copy.deepcopy(table), "id": "t2"}
    continuation["cells"][1]["text"] = "20"
    (directory / "tables.jsonl").write_text(json.dumps(table) + "\n" + json.dumps(continuation))
    section = json.loads((directory / "sections.jsonl").read_text())
    section["ordered_child_ids"] = ["h1", "b1", "t1", "t2", "note"]
    (directory / "sections.jsonl").write_text(json.dumps(section))
    from er_commons.pilot_citation_records import block_anchor

    by_id = {b["id"]: b for b in blocks}
    anchors = [block_anchor("fixture2/blocks.jsonl", by_id["b1"])]
    for record in (table, continuation):
        for i, cell in enumerate(record["cells"]):
            anchors.append(
                {
                    "path": "fixture2/tables.jsonl",
                    "record_id_field": "id",
                    "record_id": record["id"],
                    "record": record,
                    "text_field": f"cells.{i}.text",
                    "start": 0,
                    "end": len(cell["text"]),
                    "quote": cell["text"],
                }
            )
    anchors.append(block_anchor("fixture2/blocks.jsonl", by_id["note"]))
    render = directory / "invented-render.png"
    render.write_bytes(b"synthetic-render-no-live-source")
    receipt = {
        "schema_version": units.RECEIPT_VERSION,
        "status": "audited",
        "audit_note": "Invented fixture continuation and heading-caption association.",
        "source_id": candidate["source_id"],
        "section_id": "s1",
        "canonical_files": {
            kind: {
                "path": f"fixture2/{kind}.jsonl",
                "sha256": hashlib.sha256((directory / f"{kind}.jsonl").read_bytes()).hexdigest(),
            }
            for kind in ("sections", "blocks", "tables")
        },
        "table_ids": ["t1", "t2"],
        "caption_id": "b1",
        "note_record_ids": ["note"],
        "member_record_ids": ["b1", "t1", "t2", "note"],
        "section_member_record_ids": section["ordered_child_ids"],
        "render_comparisons": [
            {
                "table_id": identity,
                "physical_page": 1,
                "comparison_note": "Invented cell values retained.",
                "render": {
                    "path": "fixture2/invented-render.png",
                    "sha256": hashlib.sha256(render.read_bytes()).hexdigest(),
                },
            }
            for identity in ("t1", "t2")
        ],
    }
    receipt_path = directory / "receipt.json"
    receipt_path.write_text(json.dumps(receipt))
    candidate["citation_unit"].update(
        schema_version=units.VERSION,
        boundary_policy="audited_table_family",
        section_record={
            "path": "fixture2/sections.jsonl",
            "record_id_field": "id",
            "record_id": "s1",
            "record": section,
        },
        section_member_record_ids=section["ordered_child_ids"],
        member_record_ids=receipt["member_record_ids"],
        receipt_ref={
            "path": "fixture2/receipt.json",
            "sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        },
    )
    for legacy in ("heading_anchor", "next_heading_anchor", "start_block_id"):
        candidate["citation_unit"].pop(legacy, None)
    candidate["anchors"] = anchors
    candidate["quote"] = "\n\n".join(a["quote"] for a in anchors)
    candidate["candidate_id"] = evidence.candidate_id(candidate)
    return candidate, root


def test_heading_caption_continuation_keeps_all_cells(family):
    candidate, root = family
    units.validate_table_family(candidate, root)
    evidence.validate_candidates(
        {"schema_version": evidence.SECTION_SCHEMA, "candidates": [candidate]}, root
    )
    assert candidate["anchors"][0]["record"]["block_type"] == "heading"


@pytest.mark.parametrize(
    "mutation", ["cell", "caption", "order", "render", "receipt", "label", "source", "boundary"]
)
def test_audited_family_rejects_incomplete_or_changed_sources(family, mutation):
    candidate, root = family
    if mutation == "cell":
        candidate["anchors"].pop(2)
    elif mutation == "caption":
        candidate["anchors"][0]["record"]["block_type"] = "caption"
    elif mutation == "order":
        candidate["anchors"][1], candidate["anchors"][3] = (
            candidate["anchors"][3],
            candidate["anchors"][1],
        )
    elif mutation == "render":
        (root / "fixture2/invented-render.png").write_bytes(b"changed")
    elif mutation == "receipt":
        (root / "fixture2/receipt.json").write_text("{}")
    elif mutation == "label":
        candidate["citation_unit"]["citation_label"] = "Different caption"
    elif mutation == "boundary":
        candidate["citation_unit"]["start_block_id"] = "stale"
    else:
        candidate["source_id"] = "other_document"
    with pytest.raises(ValueError):
        units.validate_table_family(candidate, root)


def test_explicit_cross_section_notes_and_source_ownership(family):
    candidate, root = family
    directory = root / "fixture2"
    blocks = [json.loads(line) for line in (directory / "blocks.jsonl").read_text().splitlines()]
    for block in blocks:
        if block["id"] == "note":
            block["section_id"] = "s3"
    section = json.loads((directory / "sections.jsonl").read_text())
    section["ordered_child_ids"].remove("note")
    note_section = {**section, "id": "s3", "ordered_child_ids": ["note"]}
    (directory / "sections.jsonl").write_text(json.dumps(section) + "\n" + json.dumps(note_section))
    (directory / "blocks.jsonl").write_text("\n".join(json.dumps(b) for b in blocks))
    receipt = json.loads((directory / "receipt.json").read_text())
    receipt["additional_note_section_ids"] = ["s3"]
    receipt["section_member_record_ids"] = section["ordered_child_ids"]
    for kind in ("sections", "blocks"):
        receipt["canonical_files"][kind]["sha256"] = hashlib.sha256(
            (directory / f"{kind}.jsonl").read_bytes()
        ).hexdigest()
    (directory / "receipt.json").write_text(json.dumps(receipt))
    ref = {
        "path": "fixture2/receipt.json",
        "sha256": hashlib.sha256((directory / "receipt.json").read_bytes()).hexdigest(),
    }
    result = units.build_candidate(ref, data_root=root, metadata=candidate)
    units.validate_table_family(result, root)
    assert result["anchors"][-1]["record"]["section_id"] == "s3"
    receipt["additional_note_section_ids"] = []
    (directory / "receipt.json").write_text(json.dumps(receipt))
    ref["sha256"] = hashlib.sha256((directory / "receipt.json").read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="ownership"):
        units.build_candidate(ref, data_root=root, metadata=candidate)


@pytest.fixture
def audited_section_family(family):
    candidate, root = family
    directory = root / "fixture2"
    blocks = [json.loads(line) for line in (directory / "blocks.jsonl").read_text().splitlines()]
    for block in blocks:
        if block["id"] == "h1":
            block["block_type"] = "paragraph"
    (directory / "blocks.jsonl").write_text("\n".join(json.dumps(b) for b in blocks))
    receipt = json.loads((directory / "receipt.json").read_text())
    receipt["canonical_files"]["blocks"]["sha256"] = hashlib.sha256(
        (directory / "blocks.jsonl").read_bytes()
    ).hexdigest()
    (directory / "receipt.json").write_text(json.dumps(receipt))
    ref = {
        "path": "fixture2/receipt.json",
        "sha256": hashlib.sha256((directory / "receipt.json").read_bytes()).hexdigest(),
    }
    table_candidate = units.build_candidate(ref, data_root=root, metadata=candidate)
    narrative = {
        "schema_version": "er_commons.task08e.section_audit.v1",
        "status": "audited",
        "audit_note": "Invented parsed heading remains a paragraph.",
        "source_id": candidate["source_id"],
        "section_id": "s1",
        "canonical_files": receipt["canonical_files"],
        "section_member_record_ids": receipt["section_member_record_ids"],
        "member_record_ids": ["h1"],
        "next_heading_block_id": "b1",
        "excluded_table_family_receipts": [ref],
    }
    (directory / "narrative.json").write_text(json.dumps(narrative))
    narrative_ref = {
        "path": "fixture2/narrative.json",
        "sha256": hashlib.sha256((directory / "narrative.json").read_bytes()).hexdigest(),
    }
    result = units.build_candidate(narrative_ref, data_root=root, metadata=candidate)
    return result, table_candidate, root


def test_audited_paragraph_heading_retains_narrative_and_requires_excluded_family(
    audited_section_family,
):
    result, table_candidate, root = audited_section_family
    units.validate_audited_section(result, [result, table_candidate], root)
    assert result["anchors"][0]["record"]["block_type"] == "paragraph"
    for field, value in (("extraction_id", "wrong-extraction"), ("physical_pages", [999])):
        changed = copy.deepcopy(result)
        changed[field] = value
        changed["candidate_id"] = evidence.candidate_id(changed)
        with pytest.raises(ValueError, match="extraction|physical pages"):
            evidence.validate_candidates(
                {
                    "schema_version": evidence.SECTION_SCHEMA,
                    "candidates": [changed, table_candidate],
                },
                root,
            )
    with pytest.raises(ValueError, match="separately displayed"):
        units.validate_audited_section(result, [result], root)
    result["anchors"][0]["quote"] = "Changed narrative"
    with pytest.raises(ValueError, match="anchors"):
        units.validate_audited_section(result, [result, table_candidate], root)


@pytest.mark.parametrize(
    "mutation", ["extraction", "physical_pages", "render_pages", "family_sibling"]
)
def test_canonical_metadata_and_family_closure_cannot_be_redefined_by_receipt(family, mutation):
    candidate, root = family
    receipt_path = root / "fixture2/receipt.json"
    receipt = json.loads(receipt_path.read_text())
    if mutation == "extraction":
        candidate["extraction_id"] = "wrong-extraction"
    elif mutation == "physical_pages":
        candidate["physical_pages"] = [1, 1]
    elif mutation == "render_pages":
        candidate["physical_pages"] = [999]
        for row in receipt["render_comparisons"]:
            row["physical_page"] = 999
    else:
        receipt["table_ids"] = ["t1"]
        receipt["member_record_ids"].remove("t2")
        receipt["render_comparisons"] = receipt["render_comparisons"][:1]
        candidate["citation_unit"]["member_record_ids"] = receipt["member_record_ids"]
        candidate["anchors"] = [a for a in candidate["anchors"] if a["record_id"] != "t2"]
        candidate["quote"] = "\n\n".join(a["quote"] for a in candidate["anchors"])
    receipt_path.write_text(json.dumps(receipt))
    candidate["citation_unit"]["receipt_ref"]["sha256"] = hashlib.sha256(
        receipt_path.read_bytes()
    ).hexdigest()
    candidate["candidate_id"] = evidence.candidate_id(candidate)
    with pytest.raises(
        ValueError, match="extraction|physical pages|render page|continuation family"
    ):
        evidence.validate_candidates(
            {"schema_version": evidence.SECTION_SCHEMA, "candidates": [candidate]}, root
        )


def test_audited_section_accepts_independent_repeated_complete_families(audited_section_family):
    """Repeated displays retain all occurrences and the same canonical source binding."""
    section, family, root = audited_section_family
    repeated = copy.deepcopy(family)
    repeated["occurrence_id"] = "another-finding"
    repeated["title"] = "Separate display title"
    repeated["anchors"][0]["display_note"] = "Independent occurrence"
    candidates = [section, family, repeated]
    before = copy.deepcopy(candidates)
    units.validate_audited_section(section, candidates, root)
    assert candidates == before


@pytest.mark.parametrize(
    "mutation", ["source_pdf", "source_sha", "edition", "unit", "anchor", "cell"]
)
def test_audited_section_rejects_conflicting_repeated_family(audited_section_family, mutation):
    """One valid occurrence cannot conceal a conflicting second family occurrence."""
    section, family, root = audited_section_family
    repeated = copy.deepcopy(family)
    if mutation == "source_pdf":
        repeated["source_pdf_path"] = "different.pdf"
    elif mutation == "source_sha":
        repeated["source_sha256"] = "0" * 64
    elif mutation == "edition":
        repeated["edition"] = "conflicting edition"
    elif mutation == "unit":
        repeated["citation_unit"]["member_record_ids"] = ["b1", "t1", "note"]
    elif mutation == "anchor":
        repeated["anchors"][0]["path"] = "foreign/blocks.jsonl"
    else:
        repeated["anchors"][1]["record"]["cells"][0]["text"] = "changed"
    with pytest.raises(ValueError):
        units.validate_audited_section(section, [section, family, repeated], root)
