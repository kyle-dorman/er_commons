"""Validate citable units against parsed hierarchy, independently of support labels."""

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
    source_path,
)


def reviewed_table_associations(
    binding: dict[str, Any],
    *,
    data_root: Path,
    source_id: str,
    section_id: str,
    section_path: str,
    members: list[str],
    blocks: dict[str, Any],
    tables: dict[str, Any],
) -> list[dict[str, Any]]:
    """Read an explicitly audited association receipt, never infer note ownership."""
    receipt = json.loads(bound_bytes(binding, data_root))
    if (
        receipt.get("schema_version") != "er_commons.task07d.table_associations.v1"
        or receipt.get("source_id") != source_id
        or receipt.get("section_id") != section_id
        or receipt.get("section_member_record_ids") != members
        or receipt.get("status") != "audited"
        or not receipt.get("audit_note")
    ):
        raise ValueError("Association receipt differs from citation source")
    directory = Path(section_path).parent
    for kind in ("sections", "blocks", "tables"):
        expected_path = str(directory / (kind + ".jsonl"))
        ref = receipt["canonical_files"][kind]
        if ref["path"] != expected_path:
            raise ValueError("Association canonical binding mismatch")
        bound_bytes(ref, data_root)
    heading = blocks[members[0]]
    following = next_body_heading(blocks, heading)
    if (
        receipt.get("heading_block_id") != heading["id"]
        or not following
        or receipt.get("next_heading_block_id") != following["id"]
    ):
        raise ValueError("Association receipt section boundaries differ from source")
    groups: list[dict[str, Any]] = receipt["tables"]
    expected_tables = [i for i in members if i in tables]
    if [g["table_id"] for g in groups] != expected_tables:
        raise ValueError("Association receipt must account for every section table")
    removed: list[str] = []
    for group in groups:
        ids = group["member_record_ids"]
        table_id = group["table_id"]
        pos = members.index(table_id)
        if (
            pos == 0
            or ids[:2] != [members[pos - 1], table_id]
            or ids[0] not in blocks
            or blocks[ids[0]]["block_type"] != "caption"
            or ids != members[pos - 1 : pos - 1 + len(ids)]
            or any(i not in blocks for i in ids[2:])
            or group.get("caption_id") != ids[0]
            or group.get("note_record_ids") != ids[2:]
        ):
            raise ValueError("Audited table association must preserve caption and ordered notes")
        removed.extend(ids)
    if len(set(removed)) != len(removed) or receipt["narrative_record_ids"] != [
        i for i in members if i not in removed
    ]:
        raise ValueError("Association receipt must account for all intervening narrative")
    return groups


def _validate_full_anchor(anchor: dict[str, Any], actual: dict[str, Any], path: str) -> None:
    """Require the complete canonical block while permitting unrelated anchor metadata."""
    if any(anchor[key] != value for key, value in block_anchor(path, actual).items()):
        raise ValueError("Citation requires the complete canonical block")


def _validate_section_membership(
    unit: dict[str, Any],
    candidates: list[dict[str, Any]],
    associations: list[dict[str, Any]] | None,
    members: list[str],
    actual_members: list[str],
    heading: dict[str, Any],
) -> None:
    """Permit section omissions only for complete, separately displayed table units."""
    if associations is not None and unit["separately_cited_units"] != [
        {
            "kind": "table",
            "table_id": g["table_id"],
            "member_record_ids": g["member_record_ids"],
        }
        for g in associations
    ]:
        raise ValueError("Section exclusions differ from audited associations")
    removed: list[str] = []
    for exclusion in unit["separately_cited_units"]:
        matches = [
            c
            for c in candidates
            if c.get("citation_unit", {}).get("table_id") == exclusion["table_id"]
            and c["citation_unit"]["kind"] == "table"
        ]
        if (
            not matches
            or exclusion["kind"] != "table"
            or any(
                match["citation_unit"]["member_record_ids"] != exclusion["member_record_ids"]
                or match["citation_unit"]["section_record"] != unit["section_record"]
                or canonical_table_binding(match) != canonical_table_binding(matches[0])
                for match in matches
            )
        ):
            raise ValueError("Section omission needs a complete separately cited table")
        removed.extend(exclusion["member_record_ids"])
    if (
        len(removed) != len(set(removed))
        or actual_members != [i for i in members if i not in removed]
        or not actual_members
        or actual_members[0] != heading["id"]
    ):
        raise ValueError("Section citation omits or reorders source records")


def _validate_table_membership(
    candidate: dict[str, Any],
    unit: dict[str, Any],
    section: dict[str, Any],
    table: dict[str, Any],
    blocks: dict[str, Any],
    members: list[str],
    actual_members: list[str],
    associations: list[dict[str, Any]] | None,
) -> str:
    """Validate a complete table and its notes; return its canonical caption text."""
    if table["section_id"] != section["id"] or unit["table_id"] not in actual_members:
        raise ValueError("Table citation differs from parsed section")
    # Version 1 requires the whole section tail because parsed tables lack note
    # ownership. Version 2 may use an audited association receipt instead.
    table_position = members.index(table["id"])
    caption_position = table_position - 1
    if associations is not None:
        group = next(g for g in associations if g["table_id"] == table["id"])
        if actual_members != group["member_record_ids"]:
            raise ValueError("Table membership differs from audited caption and notes")
    elif (
        caption_position < 0
        or members[caption_position] not in blocks
        or blocks[members[caption_position]]["block_type"] != "caption"
        or any(i not in blocks for i in members[table_position + 1 :])
        or set(actual_members) != set(members[caption_position:])
        or [i for i in actual_members if i in blocks]
        != [i for i in members[caption_position:] if i in blocks]
    ):
        raise ValueError("Table unit requires its caption and complete section tail")
    table_anchors = [a for a in candidate["anchors"] if a["record_id"] == table["id"]]
    expected_fields = [f"cells.{i}.text" for i, cell in enumerate(table["cells"]) if cell["text"]]
    if [a["text_field"] for a in table_anchors] != expected_fields or any(
        a["record"] != table or a["start"] != 0 or a["end"] != len(a["quote"])
        for a in table_anchors
    ):
        raise ValueError("Table citation must preserve all nonempty cells")
    if not any(blocks[i]["block_type"] == "caption" for i in actual_members if i in blocks):
        raise ValueError("Table citation requires its caption")
    caption_text: str = blocks[members[caption_position]]["canonical_text"]
    return caption_text


def validate_units(candidates: list[dict[str, Any]], data_root: Path) -> None:
    """Require complete heading-bounded sections or separately named complete tables."""
    cache: dict[Path, dict[str, Any]] = {}

    def records(relative: str) -> dict[str, Any]:
        """Read canonical IDs once, rejecting paths outside the configured root."""
        path = source_path(data_root, relative)
        if path not in cache:
            cache[path] = index_records(path.read_bytes())
        return cache[path]

    for candidate in candidates:
        unit = candidate.get("citation_unit")
        if (
            isinstance(unit, dict)
            and unit.get("schema_version") == "er_commons.task08e.mixed_section_unit.v1"
        ):
            from er_commons.group_evidence_mixed import validate_mixed_section

            validate_mixed_section(candidate, data_root)
            continue
        if (
            isinstance(unit, dict)
            and unit.get("schema_version") == "er_commons.task08e.audited_section_unit.v1"
        ):
            from er_commons.group_evidence_units import validate_audited_section

            validate_audited_section(candidate, candidates, data_root)
            continue
        if (
            isinstance(unit, dict)
            and unit.get("schema_version") == "er_commons.task08e.table_family_unit.v1"
        ):
            from er_commons.group_evidence_units import validate_table_family

            validate_table_family(candidate, data_root)
            continue
        if (
            isinstance(unit, dict)
            and unit.get("schema_version") == "er_commons.task07d.citation_unit.v4"
        ):
            from er_commons.pilot_citation_visual_sections import validate_visual_units

            validate_visual_units([candidate], data_root)
            continue
        if (
            isinstance(unit, dict)
            and unit.get("schema_version") == "er_commons.task07d.citation_unit.v3"
        ):
            from er_commons.pilot_citation_boundary_overrides import validate_reviewed_boundary

            validate_reviewed_boundary(candidate, data_root)
            continue
        if (
            isinstance(unit, dict)
            and unit.get("schema_version") == "er_commons.task08f.wsa_section_unit.v1"
        ):
            from er_commons.pilot_citation_wsa_boundary import validate_wsa_boundary

            validate_wsa_boundary(candidate, data_root)
            continue
        if not isinstance(unit, dict) or unit.get("schema_version") not in {
            "er_commons.task07d.citation_unit.v1",
            "er_commons.task07d.citation_unit.v2",
        }:
            raise ValueError("Packet v2 requires a supported citation unit")
        if (
            unit["kind"] not in {"section", "table"}
            or unit["boundary_policy"] != "heading_to_next_heading_exclusive"
        ):
            raise ValueError("Unsupported citation unit boundary")
        reference = unit["section_record"]
        sections = records(reference["path"])
        section = sections[unit["section_id"]]
        if (
            reference["record_id_field"] != "id"
            or reference["record_id"] != section["id"]
            or reference["record"] != section
        ):
            raise ValueError("Citation section snapshot differs from source")
        directory = Path(reference["path"]).parent
        block_path = str(directory / "blocks.jsonl")
        blocks = records(block_path)
        heading = blocks[section["heading_block_id"]]
        _validate_full_anchor(unit["heading_anchor"], heading, block_path)
        if unit["start_block_id"] != heading["id"] or heading["block_type"] != "heading":
            raise ValueError("Citation must begin at its section heading")
        next_heading = next_body_heading(blocks, heading)
        if next_heading is None:
            raise ValueError("Citation needs an explicit next heading boundary")
        _validate_full_anchor(unit["next_heading_anchor"], next_heading, block_path)
        expected_breadcrumb = section_breadcrumb(section, sections, blocks)
        if unit["breadcrumb"] != expected_breadcrumb:
            raise ValueError("Citation breadcrumb differs from parsed hierarchy")
        members = [i for i in section["ordered_child_ids"] if i not in sections]
        if unit["section_member_record_ids"] != members:
            raise ValueError("Citation membership differs from parsed section")
        for identity in members:
            if identity in blocks:
                block = blocks[identity]
                if (
                    block["section_id"] != section["id"]
                    or not heading["sequence"] <= block["sequence"] < next_heading["sequence"]
                ):
                    raise ValueError("Citation crosses the next section heading")
        associations = None
        if unit["schema_version"] == "er_commons.task07d.citation_unit.v2":
            associations = reviewed_table_associations(
                unit["table_association_receipt"],
                data_root=data_root,
                source_id=candidate["source_id"],
                section_id=section["id"],
                section_path=reference["path"],
                members=members,
                blocks=blocks,
                tables=records(str(directory / "tables.jsonl")),
            )
        actual_members = list(dict.fromkeys(a["record_id"] for a in candidate["anchors"]))
        if unit["member_record_ids"] != actual_members or not set(actual_members) <= set(members):
            raise ValueError("Displayed records differ from citation membership")
        for anchor in candidate["anchors"]:
            if anchor["record_id"] in blocks:
                _validate_full_anchor(anchor, blocks[anchor["record_id"]], block_path)
        source_records = [section, heading, next_heading] + [
            a["record"] for a in candidate["anchors"]
        ]
        if any(
            not record.get("document_id", "").endswith("/document/" + candidate["source_id"])
            for record in source_records
        ):
            raise ValueError("Citation document differs from candidate source")
        citation_text = heading["canonical_text"]
        if unit["kind"] == "section":
            _validate_section_membership(
                unit, candidates, associations, members, actual_members, heading
            )
        else:
            table = records(str(directory / "tables.jsonl"))[unit["table_id"]]
            citation_text = _validate_table_membership(
                candidate, unit, section, table, blocks, members, actual_members, associations
            )

        expected_label = citation_text + " (pp. " + ", ".join(candidate["printed_labels"]) + ")"
        if unit["citation_label"] != expected_label:
            raise ValueError("Citation label must use the canonical heading or caption")
