"""Complete mixed sections: immutable text/tables and explicitly unreviewed figures."""

from pathlib import Path
from typing import Any

from er_commons.group_evidence_units import _anchors, _record_pages
from er_commons.pilot_citation_records import block_anchor, next_body_heading, section_breadcrumb
from er_commons.pilot_citation_visual_sections import FIGURE_LABEL, _load

SCHEMA = "er_commons.task08e.mixed_section_unit.v1"


def assemble_mixed_section(
    *,
    source: dict[str, Any],
    section_id: str,
    data_root: Path,
    printed_labels_by_page: dict[int, str],
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    """Preserve every direct canonical member without interpreting figure contents.

    Tables retain all cells and continuation members. The full section is a table
    review unit so existing packet gates require renders of every covered page.
    """
    from er_commons.pilot_evidence import candidate_id

    records = _load(source, data_root)
    blocks, sections, tables, figures = (
        records[k] for k in ("blocks", "sections", "tables", "figures")
    )
    section = sections[section_id]
    heading = blocks[section["heading_block_id"]]
    following = next_body_heading(blocks, heading)
    members = [i for i in section["ordered_child_ids"] if i not in sections]
    if (
        heading["block_type"] != "heading"
        or heading.get("content_layer") != "body"
        or following is None
        or not members
        or members[0] != heading["id"]
        or len(members) != len(set(members))
    ):
        raise ValueError("Mixed section needs exact body-heading boundaries and membership")
    table_ids = [i for i in members if i in tables]
    figure_ids = [i for i in members if i in figures]
    if not table_ids or not figure_ids or not metadata.get("pdf_url"):
        raise ValueError("Mixed section requires tables, figures and original PDF link")
    families = {tables[i].get("table_family_id") for i in table_ids} - {None, ""}
    if any(i not in table_ids for i, t in tables.items() if t.get("table_family_id") in families):
        raise ValueError("Mixed section omits continuation table family")
    pages: set[int] = set()
    segments, refs = [], []
    for identity in members:
        record = blocks.get(identity) or tables.get(identity) or figures.get(identity)
        if (
            record is None
            or record.get("section_id") != section_id
            or not record.get("document_id", "").endswith("/document/" + source["source_id"])
        ):
            raise ValueError("Mixed section has foreign or unknown member")
        record_pages = _record_pages(record, source["source_id"], source["extraction_id"])
        pages.update(record_pages)
        if identity in blocks:
            if (
                not heading["sequence"] <= record["sequence"] < following["sequence"]
                or not record["canonical_text"]
            ):
                raise ValueError("Mixed section crosses next heading or has empty text")
            segments.append({"kind": "text", "record_id": identity})
        elif identity in tables:
            segments.append({"kind": "table", "record_id": identity})
        else:
            refs.append(
                {
                    "path": source["files"]["figures"]["path"],
                    "file_sha256": source["files"]["figures"]["sha256"],
                    "record_id_field": "id",
                    "record_id": identity,
                    "record": record,
                    "interpretation": "not_evaluated_as_text_evidence",
                }
            )
            segments.append(
                {
                    "kind": "figure",
                    "record_id": identity,
                    "label": FIGURE_LABEL,
                    "pdf_url": metadata["pdf_url"].split("#")[0]
                    + "#page="
                    + str(min(record_pages)),
                }
            )
    text_members = [i for i in members if i not in figures]
    anchors = _anchors(text_members, records, source["files"])
    labels = [printed_labels_by_page[p] for p in sorted(pages)]
    unit = {
        "schema_version": SCHEMA,
        "kind": "table",
        "boundary_policy": "complete_mixed_heading_section",
        "section_id": section_id,
        "section_record": {
            "path": source["files"]["sections"]["path"],
            "record_id_field": "id",
            "record_id": section_id,
            "record": section,
        },
        "source_binding": source,
        "section_member_record_ids": members,
        "member_record_ids": text_members,
        "table_id": table_ids[0],
        "table_ids": table_ids,
        "figure_refs": refs,
        "heading_anchor": block_anchor(source["files"]["blocks"]["path"], heading),
        "next_heading_anchor": block_anchor(source["files"]["blocks"]["path"], following),
        "breadcrumb": section_breadcrumb(section, sections, blocks),
        "separately_cited_units": [],
        "citation_label": heading["canonical_text"] + " (pp. " + ", ".join(labels) + ")",
    }
    candidate = {
        **metadata,
        "source_id": source["source_id"],
        "extraction_id": source["extraction_id"],
        "anchors": anchors,
        "quote": "\n\n".join(a["quote"] for a in anchors),
        "title": heading["canonical_text"],
        "physical_pages": sorted(pages),
        "printed_labels": labels,
        "citation_unit": unit,
        "display_segments": segments,
    }
    candidate["candidate_id"] = candidate_id(candidate)
    return [candidate]


def validate_mixed_section(candidate: dict[str, Any], data_root: Path) -> None:
    """Reconstruct exact mixed closure; reject omitted cells, figures, context or pages."""
    unit = candidate["citation_unit"]
    if unit.get("schema_version") != SCHEMA or len(candidate["physical_pages"]) != len(
        candidate["printed_labels"]
    ):
        raise ValueError("Mixed section schema/page labels differ")
    expected = assemble_mixed_section(
        source=unit["source_binding"],
        section_id=unit["section_id"],
        data_root=data_root,
        printed_labels_by_page=dict(
            zip(candidate["physical_pages"], candidate["printed_labels"], strict=True)
        ),
        metadata={"pdf_url": candidate["pdf_url"]},
    )[0]
    for key in (
        "source_id",
        "extraction_id",
        "anchors",
        "quote",
        "title",
        "physical_pages",
        "citation_unit",
        "display_segments",
    ):
        if candidate.get(key) != expected[key]:
            raise ValueError("Mixed section differs from complete canonical source: " + key)
