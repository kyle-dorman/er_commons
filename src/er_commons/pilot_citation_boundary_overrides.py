"""One source-audited citation overlay; never alter the accepted canonical records."""

import json
from pathlib import Path
from typing import Any

from er_commons.pilot_citation_records import (
    block_anchor,
    bound_bytes,
    index_records,
    section_breadcrumb,
)

SCHEMA = "er_commons.task07d.citation_unit.v3"
SCOPE = "pc_lm2_deir_main_8_5_2"
EXTRACTION = "exv1-0b398345894de37c9a2bcae4b32b8c80f4b0cb61ecb20c2e435f83561f9009ba"


def _block(number: int) -> str:
    """Identify a block in the single audited extraction."""
    return f"{EXTRACTION}/block/deir_main/blk{number:06}"


def _section(number: int) -> str:
    """Identify a section in the single audited extraction."""
    return f"{EXTRACTION}/section/deir_main/sec{number:06}"


def _bound_bytes(binding: dict[str, Any], data_root: Path) -> bytes:
    """Verify immutable receipt/source bytes before interpreting a boundary."""
    if Path(binding["path"]).is_absolute():
        raise ValueError("Boundary binding escapes data root")
    return bound_bytes(binding, data_root)


def _expected(binding: dict[str, Any], data_root: Path) -> dict[str, Any]:
    """Derive the only permitted overlay from all three original section snapshots."""
    review = json.loads(_bound_bytes(binding, data_root))
    if (
        review.get("schema_version") != "er_commons.task07d.boundary_review.v1"
        or review.get("status") != "audited"
        or review.get("scope") != SCOPE
        or review.get("source_id") != "deir_main"
    ):
        raise ValueError("Unsupported reviewed boundary scope")
    records = {}
    for kind in ("blocks", "sections"):
        records[kind] = index_records(_bound_bytes(review["canonical_files"][kind], data_root))
    blocks, sections = records["blocks"], records["sections"]
    expected_sections = [sections[_section(n)] for n in (3324, 3325, 3326)]
    if review["source_sections"] != expected_sections:
        raise ValueError("Boundary review section snapshots differ from source")
    original = [
        i
        for section in expected_sections
        for i in section["ordered_child_ids"]
        if i not in sections
    ]
    if original != [_block(n) for n in range(18656, 18680)]:
        raise ValueError("Boundary scope must cover all original section records")
    affected = [blocks[_block(n)] for n in range(18656, 18681)]
    if review["affected_blocks"] != affected:
        raise ValueError("Boundary review block snapshots differ from source")
    document = f"{EXTRACTION}/document/deir_main"
    if any(b["document_id"] != document for b in affected):
        raise ValueError("Boundary review differs from accepted extraction")
    expected_order = (
        [_block(n) for n in range(18656, 18669)]
        + [_block(18670), _block(18671), _block(18679)]
        + [_block(n) for n in range(18672, 18679)]
    )
    if (
        review["original_member_record_ids"] != original
        or review["member_record_ids"] != expected_order
        or review["excluded_running_header_id"] != _block(18669)
        or review["next_heading_record_id"] != _block(18680)
        or review["reorder"]
        != {
            "record_id": _block(18679),
            "original_index": 23,
            "display_index": 15,
            "before_record_id": _block(18672),
        }
    ):
        raise ValueError("Boundary exclusions or explicit reading-order correction differ")
    if not review.get("audit_note") or not review.get("evidence"):
        raise ValueError("Boundary override requires source QA evidence")
    for evidence in review["evidence"]:
        _bound_bytes(evidence, data_root)
    heading, following = blocks[_block(18656)], blocks[_block(18680)]
    if (
        heading["block_type"] != "heading"
        or following["block_type"] != "heading"
        or blocks[_block(18669)]["block_type"] != "heading"
        or blocks[_block(18679)]["block_type"] != "heading"
    ):
        raise ValueError("Boundary source classifications changed")
    path = review["canonical_files"]["blocks"]["path"]
    anchors = [block_anchor(path, blocks[i]) for i in expected_order]
    section = expected_sections[0]
    unit = dict(
        schema_version=SCHEMA,
        kind="section",
        section_id=section["id"],
        section_record=dict(
            path=review["canonical_files"]["sections"]["path"],
            record_id=section["id"],
            record_id_field="id",
            record=section,
        ),
        heading_anchor=block_anchor(path, heading),
        next_heading_anchor=block_anchor(path, following),
        breadcrumb=section_breadcrumb(section, sections, blocks),
        start_block_id=heading["id"],
        boundary_policy="source_audited_heading_override",
        section_member_record_ids=original,
        member_record_ids=expected_order,
        separately_cited_units=[],
        table_id=None,
        boundary_review_receipt=binding,
        citation_label=heading["canonical_text"] + " (pp. 8-157, 8-158)",
    )
    return dict(
        source_id="deir_main",
        extraction_id=EXTRACTION,
        anchors=anchors,
        quote="\n\n".join(a["quote"] for a in anchors),
        title=heading["canonical_text"],
        physical_pages=[2011, 2012],
        printed_labels=["8-157", "8-158"],
        citation_unit=unit,
    )


def validate_reviewed_boundary(candidate: dict[str, Any], data_root: Path) -> None:
    """Reject omissions, rewritten text, stale snapshots or unstated reordering."""
    expected = _expected(candidate["citation_unit"]["boundary_review_receipt"], data_root)
    if any(candidate.get(key) != value for key, value in expected.items()):
        raise ValueError("Citation differs from source-audited boundary overlay")


def assemble_reviewed_boundary(
    *, review_binding: dict[str, Any], data_root: Path, metadata: dict[str, Any]
) -> dict[str, Any]:
    """Build the narrowly audited complete 8.5.2 citation without source edits."""
    from er_commons.pilot_evidence import SECTION_SCHEMA, candidate_id, validate_candidates

    candidate = {**metadata, **_expected(review_binding, data_root)}
    if candidate.get("pdf_url"):
        candidate["pdf_url"] = candidate["pdf_url"].split("#")[0] + "#page=2011"
    candidate["candidate_id"] = candidate_id(candidate)
    validate_candidates({"schema_version": SECTION_SCHEMA, "candidates": [candidate]}, data_root)
    return candidate
