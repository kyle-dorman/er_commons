"""Responsibility-level tests for the Task 03E.5 production implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.cross_reference_materialization.detection import detect_mentions
from er_commons.cross_reference_materialization.publication import preserve_failed_attempt
from er_commons.cross_reference_materialization.resolution import resolve_mention
from er_commons.cross_reference_materialization.targets import build_target_index

ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "benchmarks/er_bench/fixtures/canonical_extraction/v3"


def _inventories() -> list[dict[str, Any]]:
    return [
        json.loads((FIXTURES / name).read_bytes())
        for name in ("development_cases.json", "frozen_review_cases.json")
    ]


def test_detector_reproduces_every_frozen_span_and_negative_class() -> None:
    for inventory in _inventories():
        for case in inventory["cases"]:
            source = case["source"]
            block = {
                "canonical_text": source["canonical_text"],
                "content_layer": source["content_layer"],
                "is_toc_row": source["is_toc_row"],
                "block_type": source["block_type"],
            }
            mentions, diagnostics = detect_mentions(block)
            assert [
                (item.mention_class, item.raw_text, [item.start, item.end], item.lookup_key)
                for item in mentions
            ] == [
                (
                    item["mention_class"],
                    item["raw_text"],
                    item["source_charspan"],
                    item["lookup_key"],
                )
                for item in case["expected_mentions"]
            ]
            assert [item.diagnostic_class for item in diagnostics] == [
                item["diagnostic_class"] for item in case["expected_diagnostics"]
            ]


def test_target_builder_requires_one_label_and_one_table_on_the_page() -> None:
    upstream = "exv1-" + "1" * 64
    candidate = "exv1-" + "2" * 64
    page = f"{upstream}/page/doc/p000001"
    document = f"{upstream}/document/doc"
    block = {
        "id": f"{upstream}/block/doc/blk000001",
        "document_id": document,
        "canonical_text": "Table 1",
        "content_layer": "body",
        "is_toc_row": False,
        "regions": [{"page_id": page}],
    }
    table = {
        "id": f"{upstream}/table/doc/tbl000001",
        "document_id": document,
        "regions": [{"page_id": page}],
    }
    aliases, entries = build_target_index(
        upstream_aliases=[],
        upstream_blocks=[block],
        upstream_tables=[table],
        upstream_id=upstream,
        candidate_id=candidate,
    )
    assert [item["normalized_alias"] for item in aliases] == ["table 1"]
    assert entries[0]["upstream_alias_record_id"] is None
    assert entries[0]["upstream_target_record_id"] == table["id"]

    aliases, entries = build_target_index(
        upstream_aliases=[],
        upstream_blocks=[block],
        upstream_tables=[table, {**table, "id": table["id"] + "x"}],
        upstream_id=upstream,
        candidate_id=candidate,
    )
    assert aliases == entries == []


def test_deed_recordation_pages_are_diagnostic_only() -> None:
    block = {
        "canonical_text": (
            "The deed was recorded on May 24, 1884, in Book 37 of Deeds at page 356, "
            "Records of San Mateo County."
        ),
        "content_layer": "body",
        "is_toc_row": False,
        "block_type": "paragraph",
    }
    mentions, diagnostics = detect_mentions(block)
    assert mentions == []
    assert [item.diagnostic_class for item in diagnostics] == ["deed_recordation"]


def test_resolution_keeps_figure_unresolved_and_table_window_fail_closed() -> None:
    source = {
        "canonical_text": "See Figure 1 and Table 1.",
        "content_layer": "body",
        "is_toc_row": False,
        "block_type": "paragraph",
    }
    mentions, _ = detect_mentions(source)
    figure, table = mentions
    page1 = "exv1-" + "2" * 64 + "/page/doc/p000001"
    page8 = "exv1-" + "2" * 64 + "/page/doc/p000008"
    entry = {
        "lookup_key": "table 1",
        "target_type": "table",
        "alias_origin": "v3_verified_table_label",
        "alias_record_id": "exv1-" + "2" * 64 + "/target-alias/doc/alias000001",
        "target_record_id": "exv1-" + "2" * 64 + "/table/doc/tbl000001",
        "upstream_alias_record_id": None,
        "upstream_target_record_id": "exv1-" + "1" * 64 + "/table/doc/tbl000001",
        "evidence_kind": "verified_same_page_table_label",
        "evidence_source_record_id": "exv1-" + "2" * 64 + "/block/doc/blk000001",
        "evidence_page_id": page8,
    }
    candidates, reason = resolve_mention(
        figure,
        source_text=source["canonical_text"],
        source_page_id=page1,
        entries=[entry],
        page_numbers={page1: 1, page8: 8},
        target_order={},
        target_index_sha256="0" * 64,
    )
    assert candidates == []
    assert reason == "accepted_target_type_unavailable"
    candidates, reason = resolve_mention(
        table,
        source_text=source["canonical_text"],
        source_page_id=page1,
        entries=[entry],
        page_numbers={page1: 1, page8: 8},
        target_order={},
        target_index_sha256="0" * 64,
    )
    assert candidates == []
    assert reason == "outside_table_page_window"


def test_failed_attempt_is_retained_without_completion(tmp_path: Path) -> None:
    staging = tmp_path / ".tmp" / "candidate.token"
    completion = staging / "records" / "completion_record.json"
    completion.parent.mkdir(parents=True)
    completion.write_text("{}")
    (staging / "diagnostic.txt").write_text("failure evidence")

    retained = preserve_failed_attempt(tmp_path, staging)

    assert retained == tmp_path / "attempts" / "candidate.token"
    assert (retained / "diagnostic.txt").read_text() == "failure evidence"
    assert not (retained / "records" / "completion_record.json").exists()
