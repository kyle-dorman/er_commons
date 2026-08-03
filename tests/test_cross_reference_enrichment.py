"""Owner-level tests for the human-owned Task 03E.5 implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.cross_reference_enrichment.catalog import CorpusDocumentCatalog
from er_commons.cross_reference_enrichment.comparison import compare_to_behavioral_reference
from er_commons.cross_reference_enrichment.detection import MentionDetector
from er_commons.cross_reference_enrichment.indexing import (
    NamespaceRemapper,
    TargetIndexBuilder,
)
from er_commons.cross_reference_enrichment.policy import default_mention_policy
from er_commons.cross_reference_enrichment.publication import preserve_failed_attempt
from er_commons.cross_reference_enrichment.resolution import MentionResolver
from er_commons.cross_reference_enrichment.source_scope import SourceScope
from er_commons.cross_reference_enrichment.storage import write_json, write_jsonl
from er_commons.cross_reference_enrichment.types import (
    MentionKind,
    UnresolvedReason,
)

ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "benchmarks/er_bench/fixtures/canonical_extraction/v3"


def _fixture_inventories() -> list[dict[str, Any]]:
    return [
        json.loads((FIXTURES / name).read_bytes())
        for name in ("development_cases.json", "frozen_review_cases.json")
    ]


def test_detector_reproduces_frozen_spans_without_fixture_specific_document_text() -> None:
    detector = MentionDetector(default_mention_policy())
    for inventory in _fixture_inventories():
        for case in inventory["cases"]:
            source = case["source"]
            block = {
                "canonical_text": source["canonical_text"],
                "content_layer": source["content_layer"],
                "is_toc_row": source["is_toc_row"],
                "block_type": source["block_type"],
            }
            mentions, diagnostics = detector.detect(block)
            assert [
                (item.kind.value, item.raw_text, item.span.as_json(), item.lookup_key)
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
            assert [item.category for item in diagnostics] == [
                item["diagnostic_class"] for item in case["expected_diagnostics"]
            ]


def test_named_environmental_document_rule_generalizes_to_a_new_title() -> None:
    detector = MentionDetector(default_mention_policy())
    text = (
        "The estimate follows the Final EIR for the Harbor Resilience Master Plan "
        "(Example Agency, 2026)."
    )
    mentions, diagnostics = detector.detect(
        {
            "canonical_text": text,
            "content_layer": "body",
            "is_toc_row": False,
            "block_type": "paragraph",
        }
    )
    assert diagnostics == []
    assert len(mentions) == 1
    assert mentions[0].kind is MentionKind.DOCUMENT
    assert mentions[0].raw_text == "Final EIR for the Harbor Resilience Master Plan"
    assert mentions[0].lookup_key == mentions[0].raw_text.casefold()


def test_reference_section_scope_excludes_every_descendant_block() -> None:
    root = "exv1-" + "1" * 64
    heading_id = f"{root}/block/doc/blk000001"
    reference_id = f"{root}/section/doc/sec000001"
    child_id = f"{root}/section/doc/sec000002"
    blocks = [
        {"id": heading_id, "canonical_text": "10 REFERENCES"},
        {
            "id": f"{root}/block/doc/blk000002",
            "canonical_text": "See Section 3.",
            "content_layer": "body",
            "is_toc_row": False,
            "block_type": "list_item",
            "section_id": child_id,
        },
    ]
    scope = SourceScope.from_hierarchy(
        sections=[
            {"id": reference_id, "heading_block_id": heading_id},
            {"id": child_id, "heading_block_id": None, "parent_section_id": reference_id},
        ],
        blocks=blocks,
    )
    mentions, diagnostics = MentionDetector(default_mention_policy(), scope).detect(blocks[1])
    assert mentions == []
    assert [item.category for item in diagnostics] == ["reference_section"]


def test_bibliography_entry_outside_reference_section_is_excluded() -> None:
    text = (
        "Brown and Caldwell, 2022. Section 3: Water Demand Estimates by Land Use. "
        "In Bayland Water Balance Technical Memorandum, March 2022."
    )
    mentions, diagnostics = MentionDetector(default_mention_policy()).detect(
        {
            "canonical_text": text,
            "content_layer": "body",
            "is_toc_row": False,
            "block_type": "list_item",
        }
    )
    assert mentions == []
    assert [item.category for item in diagnostics] == ["bibliography"]


def test_external_section_qualifiers_do_not_enter_local_resolution() -> None:
    detector = MentionDetector(default_mention_policy())
    cases = {
        "See Section 8 of the SFPUC 2020 UWMP.": "qualified_external_section",
        "Pursuant to Section 7.02 of the 1984 Agreement, the allocation changed.": (
            "qualified_external_section"
        ),
        "They were co-grantees within the meaning of Section 8 of the Act.": "statutory",
    }
    for text, expected_category in cases.items():
        mentions, diagnostics = detector.detect(
            {
                "canonical_text": text,
                "content_layer": "body",
                "is_toc_row": False,
                "block_type": "paragraph",
            }
        )
        assert mentions == []
        assert [item.category for item in diagnostics] == [expected_category]


def test_current_agreement_section_qualifier_remains_local() -> None:
    text = "Costs are allocated under Section 5.04 of this Agreement."
    mentions, diagnostics = MentionDetector(default_mention_policy()).detect(
        {
            "canonical_text": text,
            "content_layer": "body",
            "is_toc_row": False,
            "block_type": "paragraph",
        }
    )
    assert diagnostics == []
    assert [item.lookup_key for item in mentions] == ["5.04"]


def test_target_index_and_table_window_are_separate_responsibilities() -> None:
    upstream = "exv1-" + "1" * 64
    candidate = "exv1-" + "2" * 64
    document = f"{upstream}/document/doc"
    table_page = f"{upstream}/page/doc/p000002"
    label = {
        "id": f"{upstream}/block/doc/blk000001",
        "document_id": document,
        "canonical_text": "Table 1",
        "content_layer": "body",
        "is_toc_row": False,
        "regions": [{"page_id": table_page}],
    }
    table = {
        "id": f"{upstream}/table/doc/tbl000001",
        "document_id": document,
        "regions": [{"page_id": table_page}],
    }
    index = TargetIndexBuilder(NamespaceRemapper(upstream, candidate)).build(
        upstream_aliases=[], upstream_blocks=[label], upstream_tables=[table]
    )
    assert index.derived_table_alias_count == 1

    detector = MentionDetector(default_mention_policy())
    source_text = "See Table 1."
    mentions, _ = detector.detect(
        {
            "canonical_text": source_text,
            "content_layer": "body",
            "is_toc_row": False,
            "block_type": "paragraph",
        }
    )
    source_page = f"{candidate}/page/doc/p000001"
    local_table_page = table_page.replace(upstream, candidate)
    resolver = MentionResolver(
        target_index=index,
        page_numbers={source_page: 1, local_table_page: 2},
        target_document_order={},
        target_index_sha256="0" * 64,
        table_page_window=5,
        corpus_document_keys=(),
    )
    resolution = resolver.resolve(mentions[0], source_text=source_text, source_page_id=source_page)
    assert resolution.unresolved_reason is None
    assert resolution.candidates[0]["page_distance"] == 1


def test_document_disposition_uses_catalog_membership_not_literal_special_cases() -> None:
    detector = MentionDetector(default_mention_policy())
    text = "See the Draft EIR for the Harbor Resilience Master Plan (Agency, 2026)."
    mention = detector.detect(
        {
            "canonical_text": text,
            "content_layer": "body",
            "is_toc_row": False,
            "block_type": "paragraph",
        }
    )[0][0]
    page = "exv1-" + "2" * 64 + "/page/doc/p000001"
    resolver = MentionResolver(
        target_index=TargetIndexBuilder(
            NamespaceRemapper("exv1-" + "1" * 64, "exv1-" + "2" * 64)
        ).build(upstream_aliases=[], upstream_blocks=[], upstream_tables=[]),
        page_numbers={page: 1},
        target_document_order={},
        target_index_sha256="0" * 64,
        table_page_window=5,
        corpus_document_keys={mention.lookup_key},
    )
    deferred = resolver.resolve(mention, source_text=text, source_page_id=page)
    assert deferred.unresolved_reason is UnresolvedReason.DEFERRED_CROSS_DOCUMENT


def test_corpus_catalog_derives_document_keys_from_sealed_titles(tmp_path: Path) -> None:
    manifest = tmp_path / "source_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "deir_main",
                        "source_role": "model_corpus",
                        "official_title": "Complete Harbor Resilience Master Plan DEIR (PDF)",
                    },
                    {
                        "source_id": "outside_reference",
                        "source_role": "supporting_reference",
                        "official_title": "Outside Report (PDF)",
                    },
                ]
            }
        )
    )
    catalog = CorpusDocumentCatalog.from_source_manifest(manifest)
    assert "draft eir for the harbor resilience master plan" in catalog.lookup_keys
    assert "outside report" not in catalog.lookup_keys


def test_comparison_normalizes_only_candidate_namespace(tmp_path: Path) -> None:
    reference_id = "exv1-" + "1" * 64
    candidate_id = "exv1-" + "2" * 64
    reference = tmp_path / "reference"
    candidate = tmp_path / "candidate"
    record_path = "canonical/documents.jsonl"
    write_json(
        reference / "records/manifest.json",
        {"record_files": [{"path": record_path}]},
    )
    reference_record = {"id": f"{reference_id}/document/doc", "title": "Example"}
    candidate_record = {"id": f"{candidate_id}/document/doc", "title": "Example"}
    write_jsonl(reference / record_path, [reference_record])
    write_jsonl(candidate / record_path, [candidate_record])
    for support_path in (
        "support/cross_reference_target_index.json",
        "support/cross_reference_summary.json",
        "support/cross_reference_preservation.json",
    ):
        write_json(reference / support_path, {"candidate": reference_id})
        write_json(candidate / support_path, {"candidate": candidate_id})

    result = compare_to_behavioral_reference(
        reference_root=reference,
        candidate_root=candidate,
        reference_id=reference_id,
        candidate_id=candidate_id,
    )
    assert result.status == "equivalent"
    assert result.mismatched_paths == ()


def test_human_owned_failed_attempt_has_no_completion(tmp_path: Path) -> None:
    staging = tmp_path / ".tmp" / "candidate.token"
    completion = staging / "records/completion_record.json"
    completion.parent.mkdir(parents=True)
    completion.write_text("{}")
    (staging / "diagnostic.txt").write_text("inspectable failure")
    retained = preserve_failed_attempt(tmp_path, staging)
    assert (retained / "diagnostic.txt").read_text() == "inspectable failure"
    assert not (retained / "records/completion_record.json").exists()
