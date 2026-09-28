"""Preserve figure locations in complete sections without interpreting figure content."""

from pathlib import Path
from typing import Any

from er_commons.pilot_citation_records import (
    block_anchor,
    bound_bytes,
    index_records,
    next_body_heading,
    section_breadcrumb,
)

SCHEMA = "er_commons.task07d.citation_unit.v4"
FIGURE_LABEL = "Figure — open original PDF"


def _load(source: dict[str, Any], root: Path) -> dict[str, dict[str, Any]]:
    """Load only hash-bound canonical neighbors; reject foreign paths and duplicate IDs."""
    result = {}
    directory = Path(source["files"]["sections"]["path"]).parent
    for kind in ("blocks", "sections", "tables", "figures"):
        ref = source["files"][kind]
        if ref["path"] != str(directory / (kind + ".jsonl")):
            raise ValueError("Visual section canonical files must be neighbors")
        result[kind] = index_records(bound_bytes(ref, root))
    return result


def _parts(source: dict[str, Any], section_id: str, root: Path) -> dict[str, Any]:
    """Derive exact text/figure membership and exclusive real parsed heading boundary."""
    records = _load(source, root)
    blocks, sections, figures = (records[k] for k in ("blocks", "sections", "figures"))
    section = sections[section_id]
    heading = blocks[section["heading_block_id"]]
    if heading["block_type"] != "heading" or heading.get("content_layer") != "body":
        raise ValueError("Visual section must start at a body heading")
    next_heading = next_body_heading(blocks, heading)
    if next_heading is None:
        raise ValueError("Visual section needs explicit next heading")
    members = [i for i in section["ordered_child_ids"] if i not in sections]
    if not members or members[0] != heading["id"] or len(set(members)) != len(members):
        raise ValueError("Visual section membership must start at heading without duplicates")
    if not any(i in figures for i in members):
        raise ValueError("Visual section rule requires at least one figure")
    text_ids, figure_refs = [], []
    for identity in members:
        record = blocks.get(identity) or figures.get(identity)
        if record is None:
            raise ValueError("Visual section rule supports text and figures only, not tables")
        if record.get("section_id") != section_id or not record.get("document_id", "").endswith(
            "/document/" + source["source_id"]
        ):
            raise ValueError("Visual section record belongs to another section or source")
        if identity in blocks:
            if not heading["sequence"] <= record["sequence"] < next_heading["sequence"]:
                raise ValueError("Visual section crosses next heading")
            if not record["canonical_text"]:
                raise ValueError("Empty canonical anchor")
            text_ids.append(identity)
        else:
            figure_refs.append(
                {
                    "path": source["files"]["figures"]["path"],
                    "file_sha256": source["files"]["figures"]["sha256"],
                    "record_id_field": "id",
                    "record_id": identity,
                    "record": record,
                    "interpretation": "not_evaluated_as_text_evidence",
                }
            )
    block_path = source["files"]["blocks"]["path"]
    anchors = [block_anchor(block_path, blocks[i]) for i in text_ids]
    pages = sorted(
        {
            int(region["page_id"].rsplit("/p", 1)[-1])
            for i in members
            for region in (blocks.get(i) or figures[i])["regions"]
        }
    )
    unit = dict(
        schema_version=SCHEMA,
        kind="section",
        section_id=section_id,
        section_record={
            "path": source["files"]["sections"]["path"],
            "record_id_field": "id",
            "record_id": section_id,
            "record": section,
        },
        source_binding=source,
        heading_anchor=block_anchor(block_path, heading),
        next_heading_anchor=block_anchor(block_path, next_heading),
        start_block_id=heading["id"],
        boundary_policy="heading_to_next_heading_exclusive",
        section_member_record_ids=members,
        member_record_ids=text_ids,
        figure_refs=figure_refs,
        separately_cited_units=[],
        table_id=None,
        breadcrumb=section_breadcrumb(section, sections, blocks),
    )
    return {"unit": unit, "anchors": anchors, "pages": pages, "heading": heading}


def _segments(unit: dict[str, Any], pdf_url: str) -> list[dict[str, Any]]:
    """Keep placeholders separate from verbatim text and at their canonical locations."""
    refs = {f["record_id"]: f for f in unit["figure_refs"]}
    result = []
    for identity in unit["section_member_record_ids"]:
        if identity in refs:
            pages = sorted(
                {int(r["page_id"].rsplit("/p", 1)[-1]) for r in refs[identity]["record"]["regions"]}
            )
            result.append(
                dict(
                    kind="figure",
                    record_id=identity,
                    label=FIGURE_LABEL,
                    pdf_url=pdf_url.split("#")[0] + "#page=" + str(pages[0]),
                )
            )
        else:
            result.append(dict(kind="text", record_id=identity))
    return result


def assemble_visual_section(
    *,
    source: dict[str, Any],
    section_id: str,
    data_root: Path,
    printed_labels_by_page: dict[int, str],
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    """Assemble one figure-containing section with full text and explicit unreviewed visuals."""
    from er_commons.pilot_evidence import candidate_id

    parts = _parts(source, section_id, data_root)
    if not metadata.get("pdf_url"):
        raise ValueError("Visual section requires its original source PDF link")
    labels = [printed_labels_by_page[p] for p in parts["pages"]]
    unit = parts["unit"]
    unit["citation_label"] = parts["heading"]["canonical_text"] + " (pp. " + ", ".join(labels) + ")"
    candidate = {
        **metadata,
        "source_id": source["source_id"],
        "extraction_id": source["extraction_id"],
        "anchors": parts["anchors"],
        "quote": "\n\n".join(a["quote"] for a in parts["anchors"]),
        "title": parts["heading"]["canonical_text"],
        "physical_pages": parts["pages"],
        "printed_labels": labels,
        "citation_unit": unit,
        "display_segments": _segments(unit, metadata["pdf_url"]),
    }
    candidate["limitations"] = list(candidate.get("limitations", [])) + [
        "Figures are preserved as original-PDF locators, not evaluated as text evidence."
    ]
    candidate["candidate_id"] = candidate_id(candidate)
    validate_visual_units([candidate], data_root)
    return [candidate]


def validate_visual_units(candidates: list[dict[str, Any]], data_root: Path) -> None:
    """Reject omitted figures, altered text, foreign snapshots, or invented visual content."""
    for candidate in candidates:
        unit = candidate["citation_unit"]
        if unit.get("schema_version") != SCHEMA:
            raise ValueError("Unsupported visual section version")
        source = unit["source_binding"]
        if (
            candidate["source_id"] != source["source_id"]
            or candidate["extraction_id"] != source["extraction_id"]
        ):
            raise ValueError("Visual section source identity mismatch")
        parts = _parts(source, unit["section_id"], data_root)
        expected = parts["unit"]
        expected["citation_label"] = (
            parts["heading"]["canonical_text"]
            + " (pp. "
            + ", ".join(candidate["printed_labels"])
            + ")"
        )
        if unit != expected or candidate["anchors"] != parts["anchors"]:
            raise ValueError(
                "Visual section text or figure membership differs from canonical source"
            )
        if candidate["physical_pages"] != parts["pages"] or len(candidate["printed_labels"]) != len(
            parts["pages"]
        ):
            raise ValueError("Visual section pages do not cover all text and figures")
        if candidate["quote"] != "\n\n".join(a["quote"] for a in parts["anchors"]):
            raise ValueError("Visual section quote mixes commentary or omits source text")
        if not candidate.get("pdf_url") or candidate.get("display_segments") != _segments(
            unit, candidate["pdf_url"]
        ):
            raise ValueError("Visual section requires ordered source PDF figure placeholders")
