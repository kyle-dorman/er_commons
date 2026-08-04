"""Focused invariant-transfer tests for the maintained v3 validator."""

from __future__ import annotations

from pathlib import Path

import pytest

from er_commons.cross_reference_enrichment.construction import CandidateBuild
from er_commons.cross_reference_enrichment.storage import write_jsonl
from er_commons.cross_reference_enrichment.validation import (
    _validate_alias_correspondence,
    _validate_cross_reference_policy,
    _validate_target_index,
)

CANDIDATE_ID = "exv1-" + "a" * 64
UPSTREAM_ID = "exv1-" + "b" * 64


def test_alias_correspondence_derives_expected_count_from_upstream(tmp_path: Path) -> None:
    """Zero, small, and future corpora are not coupled to Appendix P's count 323."""
    upstream_aliases = [
        {"id": f"{UPSTREAM_ID}/target-alias/doc/alias{index:06d}"} for index in range(1, 3)
    ]
    write_jsonl(tmp_path / "canonical/target_aliases.jsonl", upstream_aliases)
    build = CandidateBuild(
        preserved_record_files={},
        target_aliases=[
            {
                "id": alias["id"].replace(UPSTREAM_ID, CANDIDATE_ID),
                "alias_origin": "upstream_v2",
                "upstream_alias_id": alias["id"],
            }
            for alias in upstream_aliases
        ],
        cross_references=[],
        support={},
    )

    _validate_alias_correspondence(build, tmp_path)


def test_resolution_status_and_candidate_count_are_revalidated() -> None:
    """Serialized status cannot disagree with the candidate evidence count."""
    page_id = f"{CANDIDATE_ID}/page/doc/p000001"
    block_id = f"{CANDIDATE_ID}/block/doc/blk000001"
    section_id = f"{CANDIDATE_ID}/section/doc/sec000001"
    alias_id = f"{CANDIDATE_ID}/target-alias/doc/alias000001"
    block = {
        "id": block_id,
        "document_id": f"{CANDIDATE_ID}/document/doc",
        "sequence": 1,
        "canonical_text": "See Section 1.",
        "content_layer": "body",
        "is_toc_row": False,
        "block_type": "paragraph",
        "regions": [{"page_id": page_id}],
        "raw_links": [],
    }
    candidate = {
        "target_type": "section",
        "alias_origin": "upstream_v2",
        "alias_record_ids": [alias_id],
        "target_record_id": section_id,
        "upstream_alias_record_ids": [f"{UPSTREAM_ID}/target-alias/doc/alias000001"],
        "upstream_target_record_id": f"{UPSTREAM_ID}/section/doc/sec000001",
        "evidence": [],
    }
    mention = {
        "extraction_id": CANDIDATE_ID,
        "sequence": 1,
        "source_record_id": block_id,
        "source_charspan": [4, 13],
        "raw_text": "Section 1",
        "regions": block["regions"],
        "raw_links": [],
        "lookup_key": "1",
        "mention_class": "section",
        "candidates": [candidate],
        "resolution_status": "ambiguous",
        "unresolved_reason": None,
    }
    build = CandidateBuild(
        preserved_record_files={
            "canonical/blocks.jsonl": [block],
            "canonical/documents.jsonl": [],
            "canonical/pages.jsonl": [{"id": page_id, "physical_page_number": 1}],
            "canonical/sections.jsonl": [{"id": section_id}],
            "canonical/tables.jsonl": [],
            "canonical/figures.jsonl": [],
        },
        target_aliases=[{"id": alias_id, "alias_origin": "upstream_v2"}],
        cross_references=[mention],
        support={
            "cross_reference_target_index": {
                "entries": [
                    {
                        "lookup_key": "1",
                        "target_type": "section",
                        "alias_origin": "upstream_v2",
                        "alias_record_id": alias_id,
                        "target_record_id": section_id,
                        "upstream_alias_record_id": candidate["upstream_alias_record_ids"][0],
                        "upstream_target_record_id": candidate["upstream_target_record_id"],
                        "evidence_kind": "accepted_v2_alias",
                        "evidence_source_record_id": None,
                        "evidence_page_id": None,
                    }
                ]
            }
        },
    )

    with pytest.raises(ValueError, match="mention status matches candidates"):
        _validate_cross_reference_policy(build)


def test_target_index_allows_one_alias_to_name_multiple_targets(tmp_path: Path) -> None:
    """Ambiguous upstream aliases retain one index row for every target."""
    upstream_alias_id = f"{UPSTREAM_ID}/target-alias/doc/alias000001"
    upstream_targets = [
        f"{UPSTREAM_ID}/section/doc/sec000001",
        f"{UPSTREAM_ID}/section/doc/sec000002",
    ]
    alias_id = upstream_alias_id.replace(UPSTREAM_ID, CANDIDATE_ID)
    target_ids = [target.replace(UPSTREAM_ID, CANDIDATE_ID) for target in upstream_targets]
    upstream_alias = {
        "id": upstream_alias_id,
        "normalized_alias": "section 1",
        "targets": [
            {"target_id": target_id, "target_type": "section"} for target_id in upstream_targets
        ],
    }
    write_jsonl(tmp_path / "canonical/target_aliases.jsonl", [upstream_alias])
    alias = {
        "id": alias_id,
        "normalized_alias": "section 1",
        "alias_origin": "upstream_v2",
        "upstream_alias_id": upstream_alias_id,
        "targets": [
            {
                "target_id": target_id,
                "target_type": "section",
                "upstream_target_id": upstream_target_id,
            }
            for target_id, upstream_target_id in zip(target_ids, upstream_targets, strict=True)
        ],
    }
    entries = [
        {
            "lookup_key": "section 1",
            "target_type": "section",
            "alias_origin": "upstream_v2",
            "alias_record_id": alias_id,
            "target_record_id": target_id,
            "upstream_alias_record_id": upstream_alias_id,
            "upstream_target_record_id": upstream_target_id,
        }
        for target_id, upstream_target_id in zip(target_ids, upstream_targets, strict=True)
    ]
    build = CandidateBuild(
        preserved_record_files={},
        target_aliases=[alias],
        cross_references=[],
        support={"cross_reference_target_index": {"entries": entries}},
    )

    _validate_target_index(build, tmp_path, UPSTREAM_ID, CANDIDATE_ID)

    build.support["cross_reference_target_index"]["entries"].append(entries[0].copy())
    with pytest.raises(ValueError, match="duplicate exact alias-target rows"):
        _validate_target_index(build, tmp_path, UPSTREAM_ID, CANDIDATE_ID)
