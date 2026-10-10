"""Fresh audited table families for Task08E; canonical records remain unchanged."""

import json
from pathlib import Path
from typing import Any

from er_commons.pilot_citation_records import (
    block_anchor,
    bound_bytes,
    canonical_table_binding,
    index_records,
    next_body_heading,
    section_breadcrumb,
)

VERSION = "er_commons.task08e.table_family_unit.v1"
RECEIPT_VERSION = "er_commons.task08e.table_family_audit.v1"


def _record_pages(record: dict[str, Any], source_id: str, extraction_id: str) -> set[int]:
    """Resolve positive source pages only from canonical extraction-bound regions."""
    if not extraction_id or record.get("extraction_id") != extraction_id:
        raise ValueError("Candidate extraction identity differs from canonical record")
    prefix = f"{extraction_id}/page/{source_id}/p"
    pages = set()
    for region in record.get("regions", []):
        page_id = region.get("page_id", "")
        suffix = page_id.removeprefix(prefix)
        if not page_id.startswith(prefix) or not suffix.isdecimal() or int(suffix) < 1:
            raise ValueError("Canonical region page identity differs")
        pages.add(int(suffix))
    if not pages:
        raise ValueError("Canonical source regions required")
    return pages


def _validate_source_metadata(candidate: dict[str, Any], anchors: list[dict[str, Any]]) -> None:
    """Bind displayed extraction and sorted physical pages to every canonical anchor."""
    pages: set[int] = set()
    for anchor in anchors:
        pages.update(
            _record_pages(
                anchor["record"], candidate["source_id"], candidate.get("extraction_id", "")
            )
        )
    if candidate["physical_pages"] != sorted(pages) or any(
        type(page) is not int for page in candidate["physical_pages"]
    ):
        raise ValueError("Candidate physical pages differ from canonical regions")


def validate_table_family(candidate: dict[str, Any], data_root: Path) -> None:
    """Verify an audited caption/continuation association and every unchanged cell.

    Receipt audit status records curator source inspection, never human evidence
    or eligibility approval. Render checks remain visible for later human review.
    """
    unit = candidate["citation_unit"]
    receipt = json.loads(bound_bytes(unit["receipt_ref"], data_root))
    if (
        unit["schema_version"] != VERSION
        or unit["kind"] != "table"
        or receipt.get("schema_version") != RECEIPT_VERSION
        or receipt.get("status") != "audited"
        or not receipt.get("audit_note", "").strip()
        or receipt.get("source_id") != candidate["source_id"]
        or receipt.get("section_id") != unit["section_id"]
    ):
        raise ValueError("Fresh audited table-family receipt required")
    files = receipt["canonical_files"]
    if set(files) != {"sections", "blocks", "tables"}:
        raise ValueError("Exact canonical file bindings required")
    directory = Path(unit["section_record"]["path"]).parent
    if any(files[kind]["path"] != str(directory / (kind + ".jsonl")) for kind in files):
        raise ValueError("Canonical family directory differs")
    sources = {kind: index_records(bound_bytes(ref, data_root)) for kind, ref in files.items()}
    sections, blocks, tables = sources["sections"], sources["blocks"], sources["tables"]
    section = sections[unit["section_id"]]
    reference = unit["section_record"]
    if reference != {
        "path": files["sections"]["path"],
        "record_id_field": "id",
        "record_id": section["id"],
        "record": section,
    }:
        raise ValueError("Canonical section snapshot differs")
    heading = blocks[section["heading_block_id"]]
    if "start_block_id" in unit and unit["start_block_id"] != heading["id"]:
        raise ValueError("Legacy start boundary differs from canonical heading")
    for field, record in (
        ("heading_anchor", heading),
        ("next_heading_anchor", next_body_heading(blocks, heading)),
    ):
        if field in unit and (
            record is None
            or any(
                unit[field].get(key) != value
                for key, value in block_anchor(files["blocks"]["path"], record).items()
            )
        ):
            raise ValueError("Legacy heading anchor differs from canonical boundary")
    if unit.get("boundary_policy") != "audited_table_family":
        raise ValueError("Explicit audited table-family boundary policy required")
    members = [identity for identity in section["ordered_child_ids"] if identity not in sections]
    table_ids = receipt["table_ids"]
    if not table_ids or len(set(table_ids)) != len(table_ids) or unit["table_id"] != table_ids[0]:
        raise ValueError("Ordered unique table-family identities required")
    if [identity for identity in members if identity in table_ids] != table_ids:
        raise ValueError("Table family differs from parsed section order")
    selected_families = {tables[identity].get("table_family_id") for identity in table_ids} - {
        None,
        "",
    }
    family_closure = {
        identity
        for identity, table in tables.items()
        if table.get("table_family_id") in selected_families
    }
    if not family_closure <= set(table_ids):
        raise ValueError("Every canonical continuation family member is required")
    caption_id = receipt["caption_id"]
    notes = receipt["note_record_ids"]
    included = receipt["member_record_ids"]
    context_ids = receipt.get("context_record_ids", [])
    note_sections = receipt.get("additional_note_section_ids", [])
    if len(set(note_sections)) != len(note_sections) or section["id"] in note_sections:
        raise ValueError("Distinct explicitly audited note sections required")
    extra_members = [
        identity
        for section_id in note_sections
        for identity in sections[section_id]["ordered_child_ids"]
        if identity not in sections
    ]
    for identity in notes:
        if identity not in blocks:
            raise ValueError("Audited note must be a canonical block")
        owner = blocks[identity]["section_id"]
        if (
            owner not in {section["id"], *note_sections}
            or identity not in sections[owner]["ordered_child_ids"]
        ):
            raise ValueError("Audited note ownership differs from canonical section")
    if [blocks[identity]["sequence"] for identity in notes] != sorted(
        blocks[identity]["sequence"] for identity in notes
    ):
        raise ValueError("Audited notes must preserve canonical sequence")
    if any(identity not in members or identity not in blocks for identity in context_ids):
        raise ValueError("Context blocks must belong to the bound primary section")
    family_members = members + extra_members
    selected = {caption_id, *table_ids, *notes, *context_ids}
    if (
        receipt["section_member_record_ids"] != members
        or unit["section_member_record_ids"] != members
        or unit["member_record_ids"] != included
        or included != [identity for identity in family_members if identity in selected]
        or len(set(included)) != len(included)
        or set(included) != selected
        or blocks[caption_id]["block_type"] not in {"heading", "caption"}
        or any(identity not in blocks for identity in notes)
        or any(tables[identity]["section_id"] != section["id"] for identity in table_ids)
    ):
        raise ValueError("Audited caption/table/note family membership differs")
    comparisons = receipt["render_comparisons"]
    if {row["table_id"] for row in comparisons} != set(table_ids) or not comparisons:
        raise ValueError("Every family member needs a render comparison")
    for row in comparisons:
        if (
            type(row["physical_page"]) is not int
            or row["physical_page"] < 1
            or not row.get("comparison_note", "").strip()
        ):
            raise ValueError("Render page and comparison explanation required")
        if row["physical_page"] not in _record_pages(
            tables[row["table_id"]], candidate["source_id"], candidate.get("extraction_id", "")
        ):
            raise ValueError("Table render page differs from canonical table regions")
        bound_bytes(row["render"], data_root)
    for table_id in table_ids:
        if {
            row["physical_page"] for row in comparisons if row["table_id"] == table_id
        } != _record_pages(
            tables[table_id], candidate["source_id"], candidate.get("extraction_id", "")
        ):
            raise ValueError("Every canonical table page needs a render comparison")
    if set(candidate["physical_pages"]) != {row["physical_page"] for row in comparisons}:
        raise ValueError("Rendered page coverage differs from candidate")
    expected_anchors = []
    for identity in included:
        if identity in blocks:
            expected_anchors.append(block_anchor(files["blocks"]["path"], blocks[identity]))
        else:
            table = tables[identity]
            for index, cell in enumerate(table["cells"]):
                text = cell["text"]
                if text:
                    expected_anchors.append(
                        {
                            "path": files["tables"]["path"],
                            "record_id_field": "id",
                            "record_id": identity,
                            "record": table,
                            "text_field": f"cells.{index}.text",
                            "start": 0,
                            "end": len(text),
                            "quote": text,
                        }
                    )
    if len(candidate["anchors"]) != len(expected_anchors) or any(
        any(actual.get(key) != value for key, value in expected.items())
        for actual, expected in zip(candidate["anchors"], expected_anchors, strict=True)
    ):
        raise ValueError("Family must preserve every canonical block and nonempty cell")
    if any(
        not anchor["record"].get("document_id", "").endswith("/document/" + candidate["source_id"])
        for anchor in expected_anchors
    ):
        raise ValueError("Family source document differs")
    _validate_source_metadata(candidate, expected_anchors)
    if unit["breadcrumb"] != section_breadcrumb(section, sections, blocks):
        raise ValueError("Table-family breadcrumb differs")
    expected_label = (
        blocks[caption_id]["canonical_text"]
        + " (pp. "
        + ", ".join(candidate["printed_labels"])
        + ")"
    )
    if unit["citation_label"] != expected_label:
        raise ValueError("Table-family label differs from unchanged canonical caption")


NARRATIVE_VERSION = "er_commons.task08e.audited_section_unit.v1"


def _anchors(
    members: list[str], sources: dict[str, Any], files: dict[str, Any]
) -> list[dict[str, Any]]:
    """Assemble full immutable blocks/cells in supplied validated canonical order."""
    anchors = []
    for identity in members:
        if identity in sources["blocks"]:
            anchors.append(block_anchor(files["blocks"]["path"], sources["blocks"][identity]))
        else:
            table = sources["tables"][identity]
            for index, cell in enumerate(table["cells"]):
                text = cell["text"]
                if text:
                    anchors.append(
                        {
                            "path": files["tables"]["path"],
                            "record_id_field": "id",
                            "record_id": identity,
                            "record": table,
                            "text_field": f"cells.{index}.text",
                            "start": 0,
                            "end": len(text),
                            "quote": text,
                        }
                    )
    return anchors


def build_candidate(
    receipt_ref: dict[str, str], *, data_root: Path, metadata: dict[str, Any]
) -> dict[str, Any]:
    """Assemble a fresh audited family/section from receipt-bound canonical bytes.

    Metadata supplies edition, source URL, physical/printed pages and discovery
    provenance. It cannot replace the canonical anchors, quote, identity or unit.
    """
    from er_commons.pilot_evidence import candidate_id

    receipt = json.loads(bound_bytes(receipt_ref, data_root))
    files = receipt["canonical_files"]
    sources = {kind: index_records(bound_bytes(ref, data_root)) for kind, ref in files.items()}
    section = sources["sections"][receipt["section_id"]]
    narrative = receipt["schema_version"] == "er_commons.task08e.section_audit.v1"
    label_id = section["heading_block_id"] if narrative else receipt["caption_id"]
    unit = {
        "schema_version": NARRATIVE_VERSION if narrative else VERSION,
        "kind": "section" if narrative else "table",
        "boundary_policy": "audited_full_section" if narrative else "audited_table_family",
        "receipt_ref": receipt_ref,
        "section_id": section["id"],
        "section_record": {
            "path": files["sections"]["path"],
            "record_id_field": "id",
            "record_id": section["id"],
            "record": section,
        },
        "section_member_record_ids": receipt["section_member_record_ids"],
        "member_record_ids": receipt["member_record_ids"],
        "table_id": None if narrative else receipt["table_ids"][0],
        "separately_cited_units": [],
        "breadcrumb": section_breadcrumb(section, sources["sections"], sources["blocks"]),
        "citation_label": sources["blocks"][label_id]["canonical_text"]
        + " (pp. "
        + ", ".join(metadata["printed_labels"])
        + ")",
    }
    anchors = _anchors(receipt["member_record_ids"], sources, files)
    result = {
        **metadata,
        "source_id": receipt["source_id"],
        "anchors": anchors,
        "quote": "\n\n".join(anchor["quote"] for anchor in anchors),
        "citation_unit": unit,
    }
    result["candidate_id"] = candidate_id(result)
    if not narrative:
        validate_table_family(result, data_root)
    return result


def validate_audited_section(
    candidate: dict[str, Any], candidates: list[dict[str, Any]], data_root: Path
) -> None:
    """Permit a parsed section's unchanged paragraph heading with full source closure."""
    unit = candidate["citation_unit"]
    receipt = json.loads(bound_bytes(unit["receipt_ref"], data_root))
    if (
        receipt.get("schema_version") != "er_commons.task08e.section_audit.v1"
        or receipt.get("status") != "audited"
        or not receipt.get("audit_note", "").strip()
        or receipt.get("source_id") != candidate["source_id"]
        or unit.get("boundary_policy") != "audited_full_section"
        or unit.get("kind") != "section"
    ):
        raise ValueError("Fresh audited full-section receipt required")
    files = receipt["canonical_files"]
    directory = Path(unit["section_record"]["path"]).parent
    if set(files) != {"sections", "blocks", "tables"} or any(
        files[kind]["path"] != str(directory / (kind + ".jsonl")) for kind in files
    ):
        raise ValueError("Canonical audited-section directory differs")
    sources = {kind: index_records(bound_bytes(ref, data_root)) for kind, ref in files.items()}
    section = sources["sections"][receipt["section_id"]]
    if unit["section_id"] != section["id"] or unit["section_record"] != {
        "path": files["sections"]["path"],
        "record_id_field": "id",
        "record_id": section["id"],
        "record": section,
    }:
        raise ValueError("Audited section snapshot differs")
    members = [
        identity for identity in section["ordered_child_ids"] if identity not in sources["sections"]
    ]
    omitted: set[str] = set()
    for ref in receipt.get("excluded_table_family_receipts", []):
        matches = [
            c
            for c in candidates
            if c.get("citation_unit", {}).get("schema_version") == VERSION
            and c["citation_unit"]["receipt_ref"] == ref
        ]
        if not matches:
            raise ValueError("Narrative exclusion requires a separately displayed audited family")
        for match in matches:
            validate_table_family(match, data_root)
            if (
                match["source_id"] != candidate["source_id"]
                or match["citation_unit"]["section_id"] != section["id"]
            ):
                raise ValueError("Foreign table-family exclusion")
            if canonical_table_binding(match) != canonical_table_binding(matches[0]):
                raise ValueError("Conflicting repeated audited table-family binding")
        removed = set(matches[0]["citation_unit"]["member_record_ids"]) & set(members)
        if omitted & removed:
            raise ValueError("Overlapping table exclusions")
        omitted.update(removed)
    expected = [identity for identity in members if identity not in omitted]
    heading = sources["blocks"][section["heading_block_id"]]
    following = next_body_heading(sources["blocks"], heading)
    if (
        not expected
        or expected[0] != heading["id"]
        or following is None
        or receipt["next_heading_block_id"] != following["id"]
    ):
        raise ValueError("Audited section requires exact next canonical heading boundary")
    if any(
        identity in sources["blocks"]
        and not heading["sequence"]
        <= sources["blocks"][identity]["sequence"]
        < following["sequence"]
        for identity in expected
    ):
        raise ValueError("Audited section crosses next heading")
    if (
        receipt["section_member_record_ids"] != members
        or unit["section_member_record_ids"] != members
        or receipt["member_record_ids"] != expected
        or unit["member_record_ids"] != expected
    ):
        raise ValueError("Full audited narrative membership differs")
    expected_anchors = _anchors(expected, sources, files)
    _validate_source_metadata(candidate, expected_anchors)
    if candidate["anchors"] != expected_anchors or unit["breadcrumb"] != section_breadcrumb(
        section, sources["sections"], sources["blocks"]
    ):
        raise ValueError("Audited narrative anchors/breadcrumb differ")
    expected_label = (
        heading["canonical_text"] + " (pp. " + ", ".join(candidate["printed_labels"]) + ")"
    )
    if unit["citation_label"] != expected_label or any(
        not anchor["record"].get("document_id", "").endswith("/document/" + candidate["source_id"])
        for anchor in expected_anchors
    ):
        raise ValueError("Audited narrative source/label differs")
    if any(key in unit for key in ("heading_anchor", "next_heading_anchor", "start_block_id")):
        raise ValueError("Audited narrative uses receipt boundary, not legacy metadata")
