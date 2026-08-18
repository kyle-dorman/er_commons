"""Owner-level tests for the human-owned Task 03E.5 implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.document_records.document_references.construction import CandidateBuild
from er_commons.document_records.document_references.detection import MentionDetector
from er_commons.document_records.document_references.indexing import (
    NamespaceRemapper,
    TargetIndex,
    TargetIndexBuilder,
)
from er_commons.document_records.document_references.policy import default_mention_policy
from er_commons.document_records.document_references.publication import (
    preserve_failed_attempt,
    write_failed_build_snapshot,
)
from er_commons.document_records.document_references.resolution import MentionResolver
from er_commons.document_records.document_references.source_scope import SourceScope
from er_commons.document_records.document_references.types import (
    MentionKind,
    TargetIndexEntry,
    UnresolvedReason,
)
from er_commons.source_family_catalog import SourceFamilyCatalog

ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "benchmarks/er_bench/fixtures/canonical_extraction/v3"


def _source_family_catalog(
    *, target_alias: str | None = None, second_target_alias: str | None = None
) -> SourceFamilyCatalog:
    sources = [
        {
            "source": {"source_id": "alpha", "sha256": "a" * 64, "pdf_page_count": 1},
            "family_root_source_id": "alpha",
            "document_role": "root_report",
            "parent_source_id": None,
            "reference_aliases": ["report alpha"],
        }
    ]
    if target_alias is not None:
        sources.append(
            {
                "source": {"source_id": "beta", "sha256": "b" * 64, "pdf_page_count": 1},
                "family_root_source_id": "alpha",
                "document_role": "top_level_appendix",
                "parent_source_id": "alpha",
                "reference_aliases": [target_alias],
            }
        )
    if second_target_alias is not None:
        sources.append(
            {
                "source": {"source_id": "gamma", "sha256": "c" * 64, "pdf_page_count": 1},
                "family_root_source_id": "alpha",
                "document_role": "top_level_appendix",
                "parent_source_id": "alpha",
                "reference_aliases": [second_target_alias],
            }
        )
    return SourceFamilyCatalog.from_bytes(
        json.dumps(
            {
                "schema_version": "er_commons.source_family_catalog.v1",
                "catalog_version": "fixture-v1",
                "source_family_id": "fixture-family",
                "sources": sources,
            }
        ).encode()
    )


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
        source_family_catalog=_source_family_catalog(),
        source_id="alpha",
        source_family_catalog_sha256="c" * 64,
    )
    resolution = resolver.resolve(mentions[0], source_text=source_text, source_page_id=source_page)
    assert resolution.unresolved_reason is None
    assert resolution.candidates[0].page_distance == 1


def test_structural_section_lookup_resolves_through_index_entry_keys() -> None:
    upstream = "exv1-" + "1" * 64
    candidate = "exv1-" + "2" * 64
    index = TargetIndexBuilder(NamespaceRemapper(upstream, candidate), "doc").build(
        upstream_aliases=[
            {
                "id": f"{upstream}/target-alias/doc/alias000001",
                "normalized_alias": "3.1 existing conditions",
                "targets": [
                    {
                        "target_id": f"{upstream}/section/doc/sec000001",
                        "target_type": "section",
                    }
                ],
            }
        ],
        upstream_blocks=[],
        upstream_tables=[],
    )
    source_page = f"{candidate}/page/doc/p000001"
    mention = MentionDetector(default_mention_policy()).detect(
        {
            "canonical_text": "See Section 3.1.",
            "content_layer": "body",
            "is_toc_row": False,
            "block_type": "paragraph",
        }
    )[0][0]
    resolver = MentionResolver(
        target_index=index,
        page_numbers={source_page: 1},
        target_document_order={},
        target_index_sha256="0" * 64,
        table_page_window=5,
        source_family_catalog=_source_family_catalog(),
        source_id="alpha",
        source_family_catalog_sha256="c" * 64,
    )

    result = resolver.resolve(mention, source_text="See Section 3.1.", source_page_id=source_page)

    assert result.unresolved_reason is None
    assert result.candidates[0].target_record_id.endswith("/section/doc/sec000001")


def test_table_window_boundary_and_case_insensitive_external_qualification() -> None:
    candidate = "exv1-" + "2" * 64
    source_near = f"{candidate}/page/doc/p000001"
    source_six = f"{candidate}/page/doc/p000012"
    source_ten = f"{candidate}/page/doc/p000016"
    source_far = f"{candidate}/page/doc/p000017"
    evidence_page = f"{candidate}/page/doc/p000006"
    entry = TargetIndexEntry(
        lookup_key="table 1",
        target_type="table",
        alias_origin="v3_verified_table_label",
        alias_record_id=f"{candidate}/target-alias/doc/alias000001",
        target_record_id=f"{candidate}/table/doc/tbl000001",
        upstream_alias_record_id=None,
        upstream_target_record_id="upstream-table",
        evidence_kind="verified_same_page_table_label",
        evidence_source_record_id=f"{candidate}/block/doc/blk000001",
        evidence_page_id=evidence_page,
    )
    resolver = MentionResolver(
        target_index=TargetIndex((), (entry,), 0),
        page_numbers={
            source_near: 1,
            source_six: 12,
            source_ten: 16,
            source_far: 17,
            evidence_page: 6,
        },
        target_document_order={},
        target_index_sha256="0" * 64,
        table_page_window=10,
        source_family_catalog=_source_family_catalog(),
        source_id="alpha",
        source_family_catalog_sha256="c" * 64,
    )
    detector = MentionDetector(default_mention_policy())
    local_text = "See Table 1."
    local = detector.detect(
        {
            "canonical_text": local_text,
            "content_layer": "body",
            "is_toc_row": False,
            "block_type": "paragraph",
        }
    )[0][0]

    boundary = resolver.resolve(local, source_text=local_text, source_page_id=source_near)
    distance_six = resolver.resolve(local, source_text=local_text, source_page_id=source_six)
    distance_ten = resolver.resolve(local, source_text=local_text, source_page_id=source_ten)
    outside = resolver.resolve(local, source_text=local_text, source_page_id=source_far)
    qualified_text = "See Table 1 from rEfErEnCe 2."
    qualified = detector.detect(
        {
            "canonical_text": qualified_text,
            "content_layer": "body",
            "is_toc_row": False,
            "block_type": "paragraph",
        }
    )[0][0]
    external = resolver.resolve(qualified, source_text=qualified_text, source_page_id=source_near)
    missing_text = "See Table 2."
    missing = detector.detect(
        {
            "canonical_text": missing_text,
            "content_layer": "body",
            "is_toc_row": False,
            "block_type": "paragraph",
        }
    )[0][0]
    no_alias = resolver.resolve(missing, source_text=missing_text, source_page_id=source_near)

    assert boundary.candidates[0].page_distance == 5
    assert distance_six.candidates[0].page_distance == 6
    assert distance_ten.candidates[0].page_distance == 10
    assert outside.unresolved_reason is UnresolvedReason.OUTSIDE_TABLE_WINDOW
    assert external.unresolved_reason is UnresolvedReason.QUALIFIED_EXTERNAL_TABLE
    assert no_alias.unresolved_reason is UnresolvedReason.NO_LOCAL_ALIAS


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
        source_family_catalog=_source_family_catalog(target_alias=mention.lookup_key),
        source_id="alpha",
        source_family_catalog_sha256="c" * 64,
    )
    deferred = resolver.resolve(mention, source_text=text, source_page_id=page)
    assert deferred.unresolved_reason is UnresolvedReason.DEFERRED_CROSS_DOCUMENT


def test_source_family_catalog_preserves_reviewed_aliases_and_roles() -> None:
    catalog = _source_family_catalog(target_alias="appendix d", second_target_alias="appendix p")
    assert [source.source_id for source in catalog.alias_lookup["appendix d"]] == ["beta"]
    match = catalog.cross_document_match(
        source_id="alpha",
        mention_class="appendix",
        lookup_key="appendix d",
        source_text="See Appendix D.",
        mention_start=4,
        mention_end=14,
    )
    assert match is not None
    assert match.intended_target_source_ids == ("beta",)

    unqualified = catalog.cross_document_match(
        source_id="beta",
        mention_class="appendix",
        lookup_key="appendix p",
        source_text="See Appendix P.",
        mention_start=4,
        mention_end=14,
    )
    qualified_text = "See Appendix P of the Draft Environmental Impact Report."
    qualified = catalog.cross_document_match(
        source_id="beta",
        mention_class="appendix",
        lookup_key="appendix p",
        source_text=qualified_text,
        mention_start=4,
        mention_end=14,
    )
    assert unqualified is None
    assert qualified is not None
    assert qualified.intended_target_source_ids == ("gamma",)
    assert qualified.traversal_rule == "qualified_nested_to_top_level_appendix"


def test_human_owned_failed_attempt_has_no_completion(tmp_path: Path) -> None:
    staging = tmp_path / ".tmp" / "candidate.token"
    completion = staging / "records/completion_record.json"
    completion.parent.mkdir(parents=True)
    completion.write_text("{}")
    (staging / "diagnostic.txt").write_text("inspectable failure")
    write_failed_build_snapshot(
        staging,
        build=CandidateBuild(
            preserved_record_files={},
            target_aliases=[{"id": "bad-alias"}],
            cross_references=[{"id": "bad-mention"}],
            support={"cross_reference_summary": {"status": "rejected"}},
        ),
        identity={"extraction_id": "exv1-rejected"},
        error=ValueError("candidate correspondence matches target index"),
    )
    retained = preserve_failed_attempt(tmp_path, staging)
    assert (retained / "diagnostic.txt").read_text() == "inspectable failure"
    assert not (retained / "records/completion_record.json").exists()
    context = json.loads((retained / "diagnostics/validation_build/context.json").read_text())
    assert context["error_type"] == "ValueError"
    assert context["error_message"] == "candidate correspondence matches target index"
    assert (retained / "diagnostics/validation_build/cross_references.jsonl").is_file()
