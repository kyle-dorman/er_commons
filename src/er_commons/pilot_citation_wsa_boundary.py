"""Source-bound C022 WSA section audit; accepted canonical records remain unchanged."""

import json
from pathlib import Path
from typing import Any

from er_commons.pilot_citation_records import (
    block_anchor,
    bound_bytes,
    index_records,
    section_breadcrumb,
)

SCHEMA = "er_commons.task08f.wsa_section_unit.v1"
RECEIPT_SCHEMA = "er_commons.task08f.wsa_boundary_review.v1"
SCOPE = "C022_deir_appendix_p_section_8"
EXTRACTION = "exv1-35b4b86e1b3249d87d3a04379edae383738dd50c21013c57bbe6619870aa90e9"
PDF_SHA256 = "2dfceac46931a946bc343d52b09104b7b58ed8831bc4f49a03f0b8655e4e6ea1"

CANONICAL_SHA256 = {
    "blocks": "044a0a32cd8005d9162ad5d51094a8546c7d860c6e9b7f93cebf6d75157be0be",
    "sections": "f57a4b22ee77e4491d1fedf2eb6f4373e5f87fa50af480bfe0115fc87aeccdcc",
    "tables": "576914dfc90c171294a459d4013fa0275b40cb373365a0f13eac156cb4cd5447",
}


def _block(number: int) -> str:
    """Return an identity in the one audited WSA extraction."""
    return f"{EXTRACTION}/block/deir_appendix_p/blk{number:06}"


def _section(number: int) -> str:
    """Return a section identity in the one audited WSA extraction."""
    return f"{EXTRACTION}/section/deir_appendix_p/sec{number:06}"


def _read(binding: dict[str, Any], data_root: Path) -> bytes:
    """Read a hash-bound relative artifact without escaping its data root."""
    if Path(binding["path"]).is_absolute():
        raise ValueError("WSA binding must be relative to data root")
    return bound_bytes(binding, data_root)


def _expected(binding: dict[str, Any], data_root: Path) -> dict[str, Any]:
    """Derive the full unchanged section, permitting only three audited callout labels."""
    review = json.loads(_read(binding, data_root))
    members = [_block(n) for n in range(1122, 1147)]
    internal = [_block(n) for n in (1123, 1125, 1130)]
    if (
        review.get("schema_version") != RECEIPT_SCHEMA
        or review.get("status") != "audited"
        or review.get("scope") != SCOPE
        or review.get("source_id") != "deir_appendix_p"
        or review.get("extraction_id") != EXTRACTION
        or review.get("section_id") != _section(184)
        or review.get("member_record_ids") != members
        or review.get("internal_heading_block_ids") != internal
        or review.get("next_heading_block_id") != _block(1147)
        or not review.get("audit_note", "").strip()
    ):
        raise ValueError("Unsupported WSA boundary receipt scope or membership")
    files = review["canonical_files"]
    if set(files) != {"blocks", "sections", "tables"}:
        raise ValueError("WSA audit requires all canonical files")
    if any(files[k]["sha256"] != CANONICAL_SHA256[k] for k in files):
        raise ValueError("WSA canonical source differs from audited extraction bytes")
    directory = Path(files["sections"]["path"]).parent
    if any(files[k]["path"] != str(directory / f"{k}.jsonl") for k in files):
        raise ValueError("WSA canonical file directories differ")
    records = {k: index_records(_read(v, data_root)) for k, v in files.items()}
    if review["source_pdf"]["sha256"] != PDF_SHA256:
        raise ValueError("WSA source PDF differs from accepted edition")
    _read(review["source_pdf"], data_root)
    renderings = review.get("rendered_pages", [])
    if [r.get("physical_page") for r in renderings] != list(range(92, 97)):
        raise ValueError("WSA audit requires rendered pages 92 through 96")
    for rendering in renderings:
        if not _read(rendering, data_root).startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("WSA page evidence must be rendered PNG")
    blocks, sections = records["blocks"], records["sections"]
    section, following_section = sections[_section(184)], sections[_section(185)]
    if (
        section["ordered_child_ids"] != members
        or section["heading_block_id"] != _block(1122)
        or following_section["heading_block_id"] != _block(1147)
        or following_section["parent_section_id"] != section["parent_section_id"]
    ):
        raise ValueError("WSA canonical section boundary or membership differs")
    section_heads = {s.get("heading_block_id") for s in sections.values()}
    if set(internal) & section_heads:
        raise ValueError("WSA internal callout is a canonical section heading")
    expected_headings = {
        1122: "8 COMPARISON OF SUPPLY AND DEMAND",
        1123: "\uf0fe CWC § 10910",
        1125: "\uf0fe CWC § 10911",
        1130: "\uf0fe CWC § 10911",
        1147: "9 CONCLUSIONS",
    }
    for number in range(1122, 1148):
        block = blocks[_block(number)]
        if (
            block["sequence"] != number
            or block["document_id"] != f"{EXTRACTION}/document/deir_appendix_p"
            or block["extraction_id"] != EXTRACTION
            or block["section_id"] != _section(184 if number < 1147 else 185)
            or block.get("content_layer") != "body"
            or (block["block_type"] == "heading") != (number in expected_headings)
        ):
            raise ValueError("WSA source block classification or identity differs")
        if number in expected_headings and block["canonical_text"] != expected_headings[number]:
            raise ValueError("WSA audited heading text differs")
    if any(blocks[i].get("semantic_placement") != "direct_body" for i in internal):
        raise ValueError("WSA callout semantic placement differs")
    pages = set()
    prefix = f"{EXTRACTION}/page/deir_appendix_p/p"
    for identity in members + [_block(1147)]:
        regions = blocks[identity].get("regions", [])
        if not regions:
            raise ValueError("WSA source block has no page regions")
        for region in regions:
            page_id = region["page_id"]
            if not page_id.startswith(prefix) or not page_id[len(prefix) :].isdigit():
                raise ValueError("WSA source page identity differs")
            page = int(page_id[len(prefix) :])
            if identity == _block(1147):
                if page != 96:
                    raise ValueError("WSA next section page differs")
            elif page not in range(92, 96):
                raise ValueError("WSA source page outside complete section")
            else:
                pages.add(page)
    if pages != {92, 93, 94, 95}:
        raise ValueError("WSA section page coverage differs")
    heading, following = blocks[_block(1122)], blocks[_block(1147)]
    path = files["blocks"]["path"]
    anchors = [block_anchor(path, blocks[i]) for i in members]
    unit = dict(
        schema_version=SCHEMA,
        kind="section",
        section_id=section["id"],
        section_record=dict(
            path=files["sections"]["path"],
            record_id=section["id"],
            record_id_field="id",
            record=section,
        ),
        heading_anchor=block_anchor(path, heading),
        next_heading_anchor=block_anchor(path, following),
        breadcrumb=section_breadcrumb(section, sections, blocks),
        start_block_id=heading["id"],
        boundary_policy="source_audited_wsa_internal_headings",
        section_member_record_ids=members,
        member_record_ids=members,
        separately_cited_units=[],
        table_id=None,
        boundary_review_receipt=binding,
        citation_label=heading["canonical_text"] + " (pp. 89–92)",
    )
    return dict(
        source_id="deir_appendix_p",
        extraction_id=EXTRACTION,
        source_pdf_path=review["source_pdf"]["path"],
        source_sha256=PDF_SHA256,
        anchors=anchors,
        quote="\n\n".join(a["quote"] for a in anchors),
        title=heading["canonical_text"],
        physical_pages=[92, 93, 94, 95],
        printed_labels=["89", "90", "91", "92"],
        citation_unit=unit,
    )


def validate_wsa_boundary(candidate: dict[str, Any], data_root: Path) -> None:
    """Reject omitted, rewritten, reclassified or foreign WSA source material."""
    expected = _expected(candidate["citation_unit"]["boundary_review_receipt"], data_root)
    if any(candidate.get(key) != value for key, value in expected.items()):
        raise ValueError("Citation differs from audited complete WSA section")


def assemble_wsa_boundary(
    *, review_binding: dict[str, Any], data_root: Path, metadata: dict[str, Any]
) -> dict[str, Any]:
    """Assemble the audited WSA section with no source edits or approval inference."""
    from er_commons.pilot_evidence import SECTION_SCHEMA, candidate_id, validate_candidates

    candidate = {**metadata, **_expected(review_binding, data_root)}
    if candidate.get("pdf_url"):
        candidate["pdf_url"] = candidate["pdf_url"].split("#")[0] + "#page=92"
    candidate["candidate_id"] = candidate_id(candidate)
    validate_candidates({"schema_version": SECTION_SCHEMA, "candidates": [candidate]}, data_root)
    return candidate
