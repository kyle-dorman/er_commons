"""The one audited boundary exception must remain complete and source exact."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from er_commons.pilot_citation_boundary_overrides import (
    EXTRACTION,
    SCOPE,
    _block,
    _expected,
    _section,
)
from er_commons.pilot_citation_units import validate_units


@pytest.fixture
def reviewed_candidate(tmp_path: Path):
    """Model the audited split without requiring production artifacts in tests."""
    blocks = []
    for number in range(18656, 18681):
        section = 3324 if number < 18669 else 3325 if number < 18679 else 3326
        blocks.append(
            dict(
                id=_block(number),
                sequence=number,
                canonical_text=f"Exact source {number}",
                block_type="heading" if number in (18656, 18669, 18679, 18680) else "paragraph",
                document_id=f"{EXTRACTION}/document/deir_main",
                section_id=_section(section),
                content_layer="body",
            )
        )
    sections = [
        dict(
            id=_section(n),
            heading_block_id=_block(start),
            ordered_child_ids=[_block(i) for i in range(start, stop)],
            section_path_ids=[_section(n)],
        )
        for n, start, stop in [(3324, 18656, 18669), (3325, 18669, 18679), (3326, 18679, 18680)]
    ]
    sections[1]["ordered_child_ids"].append(_section(3326))

    def write(path, value):
        path.write_text(value)
        return dict(path=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    files = {
        kind: write(tmp_path / f"{kind}.jsonl", "\n".join(json.dumps(r) for r in rows))
        for kind, rows in [("blocks", blocks), ("sections", sections)]
    }
    evidence = write(tmp_path / "source_qa.txt", "Source page checked")
    original = [_block(i) for i in range(18656, 18680)]
    displayed = original[:13] + [_block(18670), _block(18671), _block(18679)] + original[16:23]
    receipt = dict(
        schema_version="er_commons.task07d.boundary_review.v1",
        status="audited",
        scope=SCOPE,
        source_id="deir_main",
        canonical_files=files,
        source_sections=sections,
        affected_blocks=blocks,
        original_member_record_ids=original,
        member_record_ids=displayed,
        excluded_running_header_id=_block(18669),
        next_heading_record_id=_block(18680),
        reorder=dict(
            record_id=_block(18679),
            original_index=23,
            display_index=15,
            before_record_id=_block(18672),
        ),
        audit_note="Reviewed header and inline label",
        evidence=[evidence],
    )
    binding = write(tmp_path / "review.json", json.dumps(receipt))
    return tmp_path, _expected(binding, tmp_path)


def test_valid_audited_boundary_preserves_full_section(reviewed_candidate):
    """Only the running header is removed; the inline label stays in the unit."""
    root, candidate = reviewed_candidate
    validate_units([candidate], root)
    assert len(candidate["anchors"]) == 23
    assert candidate["anchors"][15]["record_id"] == _block(18679)


@pytest.mark.parametrize("change", ["omitted", "changed_text", "wrong_boundary", "reorder"])
def test_rejects_candidate_deviations(reviewed_candidate, change):
    """Changing a displayed source or boundary cannot hide behind a valid receipt."""
    root, original = reviewed_candidate
    candidate = copy.deepcopy(original)
    if change == "omitted":
        candidate["anchors"].pop(2)
        candidate["citation_unit"]["member_record_ids"].pop(2)
    elif change == "changed_text":
        candidate["anchors"][2]["quote"] = "Rewritten source"
    elif change == "wrong_boundary":
        candidate["citation_unit"]["next_heading_anchor"]["record_id"] = _block(18669)
    else:
        candidate["anchors"][14], candidate["anchors"][15] = (
            candidate["anchors"][15],
            candidate["anchors"][14],
        )
    with pytest.raises(ValueError, match="differs"):
        validate_units([candidate], root)


def test_rejects_unstated_reorder_even_with_rehashed_receipt(reviewed_candidate):
    """A self-consistent new receipt cannot broaden the explicitly supported exception."""
    root, candidate = reviewed_candidate
    path = root / "review.json"
    receipt = json.loads(path.read_text())
    receipt["reorder"] = {}
    path.write_text(json.dumps(receipt))
    candidate["citation_unit"]["boundary_review_receipt"]["sha256"] = hashlib.sha256(
        path.read_bytes()
    ).hexdigest()
    with pytest.raises(ValueError, match="reading-order"):
        validate_units([candidate], root)
