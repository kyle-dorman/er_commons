"""Qualify the narrowly source-bound WSA callout exception without production data."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from er_commons import pilot_citation_wsa_boundary as wsa
from er_commons.pilot_citation_units import validate_units


@pytest.fixture
def reviewed_candidate(tmp_path: Path, monkeypatch):
    """Build an isolated immutable record family and a checksummed audit receipt."""

    def write(name, value):
        raw = value if isinstance(value, bytes) else value.encode()
        (tmp_path / name).write_bytes(raw)
        return dict(path=name, sha256=hashlib.sha256(raw).hexdigest())

    pdf = write("source.pdf", b"%PDF-test fixture")
    monkeypatch.setattr(wsa, "PDF_SHA256", pdf["sha256"])
    headings = {
        1122: "8 COMPARISON OF SUPPLY AND DEMAND",
        1123: "\uf0fe CWC § 10910",
        1125: "\uf0fe CWC § 10911",
        1130: "\uf0fe CWC § 10911",
        1147: "9 CONCLUSIONS",
    }
    blocks = [
        dict(
            id=wsa._block(n),
            sequence=n,
            canonical_text=headings.get(n, f"Exact paragraph {n}"),
            block_type="heading" if n in headings else "paragraph",
            content_layer="body",
            document_id=f"{wsa.EXTRACTION}/document/deir_appendix_p",
            extraction_id=wsa.EXTRACTION,
            section_id=wsa._section(184 if n < 1147 else 185),
        )
        for n in range(1122, 1148)
    ]
    for block in blocks:
        number = block["sequence"]
        block["semantic_placement"] = "direct_body"
        page = 96 if number == 1147 else 92 + min((number - 1122) // 6, 3)
        block["regions"] = [dict(page_id=f"{wsa.EXTRACTION}/page/deir_appendix_p/p{page:06}")]
    sections = [
        dict(
            id=wsa._section(n),
            heading_block_id=wsa._block(start),
            ordered_child_ids=[wsa._block(i) for i in range(start, stop)],
            parent_section_id=wsa._section(3),
            section_path_ids=[wsa._section(n)],
        )
        for n, start, stop in [(184, 1122, 1147), (185, 1147, 1148)]
    ]
    files = {
        k: write(f"{k}.jsonl", "\n".join(json.dumps(x) for x in rows))
        for k, rows in [("blocks", blocks), ("sections", sections), ("tables", [])]
    }
    monkeypatch.setattr(wsa, "CANONICAL_SHA256", {k: v["sha256"] for k, v in files.items()})
    review = dict(
        schema_version=wsa.RECEIPT_SCHEMA,
        status="audited",
        scope=wsa.SCOPE,
        source_id="deir_appendix_p",
        extraction_id=wsa.EXTRACTION,
        section_id=wsa._section(184),
        canonical_files=files,
        source_pdf=pdf,
        member_record_ids=[wsa._block(n) for n in range(1122, 1147)],
        internal_heading_block_ids=[wsa._block(n) for n in (1123, 1125, 1130)],
        next_heading_block_id=wsa._block(1147),
        audit_note="Callouts visually verified",
        rendered_pages=[
            dict(physical_page=n, **write(f"page-{n}.png", b"\x89PNG\r\n\x1a\n"))
            for n in range(92, 97)
        ],
    )
    binding = write("review.json", json.dumps(review))
    return tmp_path, wsa._expected(binding, tmp_path)


def test_full_section_keeps_internal_headings(reviewed_candidate):
    """The override retains all text and labels, with the real next section boundary."""
    root, candidate = reviewed_candidate
    validate_units([candidate], root)
    assert len(candidate["anchors"]) == 25
    assert candidate["citation_unit"]["next_heading_anchor"]["record_id"] == wsa._block(1147)


@pytest.mark.parametrize("change", ["omitted", "text", "boundary", "source"])
def test_rejects_candidate_mutation(reviewed_candidate, change):
    """A valid receipt never permits selective quotations or changed source identity."""
    root, original = reviewed_candidate
    candidate = copy.deepcopy(original)
    if change == "omitted":
        candidate["anchors"].pop()
    elif change == "text":
        candidate["anchors"][-1]["quote"] = "Different commitment"
    elif change == "boundary":
        candidate["citation_unit"]["next_heading_anchor"]["record_id"] = wsa._block(1123)
    else:
        candidate["source_id"] = "deir_main"
    with pytest.raises(ValueError, match="differs"):
        validate_units([candidate], root)


@pytest.mark.parametrize("change", ["omitted", "boundary", "source", "rendering", "scope"])
def test_rejects_rehashed_receipt_broadening(reviewed_candidate, change):
    """Self-consistent receipts cannot expand the bounded exception or omit visual proof."""
    root, candidate = reviewed_candidate
    path = root / "review.json"
    review = json.loads(path.read_text())
    if change == "omitted":
        review["member_record_ids"].pop()
    elif change == "boundary":
        review["next_heading_block_id"] = wsa._block(1123)
    elif change == "source":
        review["source_pdf"]["sha256"] = "0" * 64
    elif change == "rendering":
        review["rendered_pages"].pop()
    else:
        review["scope"] = "another_section"
    path.write_text(json.dumps(review))
    candidate["citation_unit"]["boundary_review_receipt"]["sha256"] = hashlib.sha256(
        path.read_bytes()
    ).hexdigest()
    with pytest.raises(ValueError):
        validate_units([candidate], root)


@pytest.mark.parametrize("file", ["blocks.jsonl", "sections.jsonl", "tables.jsonl", "page-95.png"])
def test_rejects_mutated_bound_files(reviewed_candidate, file):
    """The receipt binds exact canonical bytes and visual review material."""
    root, candidate = reviewed_candidate
    path = root / file
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        validate_units([candidate], root)


def test_rehashed_canonical_content_cannot_change_commitment(reviewed_candidate):
    """Even a replacement receipt cannot authorize revised source text."""
    root, candidate = reviewed_candidate
    blocks_path = root / "blocks.jsonl"
    blocks = [json.loads(line) for line in blocks_path.read_text().splitlines()]
    blocks[-2]["canonical_text"] = "Unconditional binding promise"
    blocks_path.write_text("\n".join(json.dumps(block) for block in blocks))
    review_path = root / "review.json"
    receipt = json.loads(review_path.read_text())
    receipt["canonical_files"]["blocks"]["sha256"] = hashlib.sha256(
        blocks_path.read_bytes()
    ).hexdigest()
    review_path.write_text(json.dumps(receipt))
    candidate["citation_unit"]["boundary_review_receipt"]["sha256"] = hashlib.sha256(
        review_path.read_bytes()
    ).hexdigest()
    with pytest.raises(ValueError, match="audited extraction bytes"):
        validate_units([candidate], root)
