"""Focused Task 06E policy, projection, schema, and publication matrix."""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from er_commons.document_records.document_structure.aliases import AliasSeed, build_target_aliases
from er_commons.document_records.document_structure.bundle import DocumentStructureBundleView
from er_commons.document_records.document_structure.comparison import compare_baseline_collections
from er_commons.document_records.document_structure.config import DocumentStructureExpectations
from er_commons.document_records.document_structure.construction import DocumentStructureBuild
from er_commons.document_records.document_structure.missing_chapter_correspondence import (
    CORRESPONDENCE_SCHEMA_RELATIVE_PATH,
    validate_missing_chapter_correspondence,
)
from er_commons.document_records.document_structure.missing_chapter_policy import (
    ChapterBoundaryEvidence,
    ChapterChildEvidence,
    ChapterHeadingComponent,
    ChapterTocEvidence,
    DirectContentEvidence,
    EnclosingSectionEvidence,
    MissingChapterEvidence,
    classify_missing_chapter,
)
from er_commons.document_records.document_structure.missing_chapter_projection import (
    build_missing_chapter_alias_seeds,
    build_missing_chapter_correspondence,
    project_missing_chapter_decisions,
)
from er_commons.document_records.document_structure.missing_chapter_qualification import (
    publish_missing_chapter_qualification,
)
from er_commons.document_records.document_structure.policies.aliases import validate_target_aliases
from er_commons.document_records.document_structure.policies.sections import validate_sections
from er_commons.document_records.document_structure.repeated_heading_projection import (
    RepeatedHeadingProjection,
)
from er_commons.document_records.document_structure.section_starts import (
    logical_section_start_id,
)
from er_commons.document_records.document_structure.support import (
    document_structure_validation_bundle,
)
from er_commons.human_review_support.extraction_review.toc_census import (
    _Section as CensusSection,
)
from er_commons.human_review_support.extraction_review.toc_census import _section_headings

ROOT = Path(__file__).parents[1]
SCHEMA_PATH = (
    ROOT / "benchmarks/er_bench/schemas/task06_recovery/v1/missing_chapter_decision.schema.json"
)
KEYS = ("1" * 64, "2" * 64)


def _evidence(*, components: bool = True) -> MissingChapterEvidence:
    headings = (
        (
            ChapterHeadingComponent(
                "block/main/a",
                KEYS[0],
                "CHAPTER 8",
                10,
                100,
                block_type="page_header",
                content_layer="furniture",
                source_id="main",
                corrected_role="heading",
                reclassification_authorized=True,
                reclassification_authority=(
                    "missing_whole_chapter_v1_observed_heading_reclassification"
                ),
            ),
            ChapterHeadingComponent(
                "block/main/b",
                KEYS[1],
                "ALTERNATIVES",
                10,
                101,
                block_type="page_header",
                content_layer="furniture",
                source_id="main",
                reclassification_authorized=True,
                reclassification_authority=(
                    "missing_whole_chapter_v1_observed_heading_reclassification"
                ),
            ),
        )
        if components
        else ()
    )
    return MissingChapterEvidence(
        source_id="main",
        chapter_marker="8",
        heading_components=headings,
        toc_evidence=(ChapterTocEvidence(("toc8",), "Chapter 8 Alternatives", source_id="main"),),
        ordered_child_refs=("child-key",),
        parent_ref="section/main/sec000001",
        semantic_level=2,
        start_record_ref=KEYS[0] if components else "child-key",
        extent_start_page=10,
        extent_end_page=19,
        following_boundary=ChapterBoundaryEvidence(
            "block/main/boundary",
            "9" * 64,
            "CHAPTER 9",
            20,
            source_id="main",
            content_order=200,
        ),
        child_topology=(
            ChapterChildEvidence(
                "child-key",
                "main",
                102,
                "section/main/sec000001",
                3,
                10,
                19,
                "8.1 INTRODUCTION",
            ),
        ),
        start_content_order=100 if components else 102,
    )


def _reference() -> dict[str, str]:
    return {
        "authority": "accepted_records",
        "relative_path": "06a/evidence.json",
        "identity": "accepted-main",
        "verification_mode": "sealed_packet",
    }


def test_composite_recovery_is_eligible_and_schema_valid() -> None:
    decision = classify_missing_chapter(_evidence())
    assert decision.status == "eligible"
    assert decision.representation == "recovered_composite"
    record = decision.as_record(source_ref=_reference(), new_target_ref=_reference())
    errors = list(Draft202012Validator(json.loads(SCHEMA_PATH.read_text())).iter_errors(record))
    assert errors == []


def test_single_observed_heading_is_supported() -> None:
    evidence = _evidence()
    one = replace(
        evidence,
        heading_components=(
            replace(evidence.heading_components[0], raw_text="CHAPTER 8 ALTERNATIVES"),
        ),
    )
    decision = classify_missing_chapter(one)
    assert decision.status == "eligible"


def test_fallback_requires_exact_accepted_destination() -> None:
    evidence = _evidence(components=False)
    rejected = classify_missing_chapter(evidence)
    assert rejected.reason_codes == ("missing_toc_body_destination",)
    accepted = classify_missing_chapter(
        replace(
            evidence,
            toc_evidence=(replace(evidence.toc_evidence[0], destination_physical_pages=(10,)),),
        )
    )
    assert accepted.status == "eligible"
    assert accepted.representation == "toc_children_fallback"


def test_cross_source_unapproved_and_dotted_marker_evidence_stop() -> None:
    evidence = _evidence()
    unapproved = replace(
        evidence,
        heading_components=(
            replace(evidence.heading_components[0], reclassification_authorized=False),
            evidence.heading_components[1],
        ),
    )
    assert (
        "furniture_reclassification_not_authorized"
        in classify_missing_chapter(unapproved).reason_codes
    )
    body_header = replace(
        evidence,
        heading_components=(
            replace(
                evidence.heading_components[0],
                content_layer="body",
                reclassification_authorized=False,
                reclassification_authority=None,
            ),
            evidence.heading_components[1],
        ),
    )
    assert (
        "furniture_reclassification_not_authorized"
        in classify_missing_chapter(body_header).reason_codes
    )
    dotted = replace(
        evidence,
        toc_evidence=(replace(evidence.toc_evidence[0], raw_title="8.2 Alternatives"),),
    )
    assert classify_missing_chapter(dotted).reason_codes == ("toc_marker_conflict",)


def test_closed_status_matrix_accounts_existing_absent_and_conflicting_evidence() -> None:
    existing = classify_missing_chapter(
        replace(_evidence(), chapter_marker="7", existing_target_id="section/main/chapter7")
    )
    assert existing.status == "already_present"
    absent = classify_missing_chapter(
        replace(
            _evidence(components=False),
            chapter_marker="6",
            toc_evidence=(),
            ordered_child_refs=(),
            child_topology=(),
            parent_ref="",
            start_record_ref="",
            following_boundary=None,
        )
    )
    assert absent.status == "rejected"
    conflicting = classify_missing_chapter(
        replace(
            _evidence(),
            toc_evidence=(
                *_evidence().toc_evidence,
                ChapterTocEvidence(("toc8b",), "Chapter 8 Other", source_id="main"),
            ),
        )
    )
    assert conflicting.status == "review_required"


def test_topology_and_source_fail_closed_without_trusting_flags() -> None:
    evidence = _evidence()
    reordered = replace(
        evidence,
        ordered_child_refs=("second", "child-key"),
        child_topology=(
            ChapterChildEvidence(
                "second",
                "main",
                103,
                "section/main/sec000001",
                3,
                11,
                12,
                "8.2 SECOND",
            ),
            evidence.child_topology[0],
        ),
    )
    assert "noncontiguous_children" in classify_missing_chapter(reordered).reason_codes
    cross_source = replace(
        evidence,
        child_topology=(replace(evidence.child_topology[0], source_id="appendix_a"),),
    )
    assert "cross_source_child_evidence" in classify_missing_chapter(cross_source).reason_codes
    direct = DirectContentEvidence(
        "block/main/direct",
        "4" * 64,
        "block",
        "main",
        103,
        (11, 10, 11),
        "section/main/sec000001",
    )
    assert (
        "direct_content_scope_invalid"
        in classify_missing_chapter(
            replace(evidence, direct_content_topology=(direct,))
        ).reason_codes
    )


def test_document_end_boundary_is_explicit_and_eligible() -> None:
    terminal = replace(
        _evidence(),
        following_boundary=ChapterBoundaryEvidence(
            "document/main",
            None,
            "document end",
            19,
            source_id="main",
            content_order=999,
            boundary_kind="document_end",
        ),
    )
    decision = classify_missing_chapter(terminal)
    assert decision.status == "eligible"
    assert (
        decision.as_record(source_ref=_reference(), new_target_ref=_reference())["extent_basis"]
        == "start_through_document_end"
    )


def test_fresh_namespace_parent_and_unnumbered_enclosing_topology_resolve() -> None:
    """Historical IDs resolve structurally and sec002679-like ancestors are explicit."""
    old = "exv1-" + "c" * 64
    new = "exv1-" + "d" * 64
    evidence = replace(
        _evidence(),
        parent_ref=f"{old}/section/main/sec009999",
        ordered_child_refs=(f"{old}/section/main/sec002680",),
        child_topology=(
            ChapterChildEvidence(
                f"{old}/section/main/sec002680",
                "main",
                102,
                f"{old}/section/main/sec002679",
                4,
                10,
                19,
                "8.2 RATIONALE",
            ),
        ),
        enclosing_section_refs=(f"{old}/section/main/sec002679",),
        enclosing_topology=(
            EnclosingSectionEvidence(
                f"{old}/section/main/sec002679",
                "main",
                "4" * 64,
                f"{old}/block/main/enclosing",
                "UNNUMBERED ENCLOSURE",
                101,
                f"{old}/section/main/sec009999",
                3,
            ),
        ),
        direct_content_topology=(
            DirectContentEvidence(
                f"{old}/block/main/enclosing",
                "4" * 64,
                "block",
                "main",
                2,
                (10,),
                f"{old}/section/main/sec002679",
            ),
            DirectContentEvidence(
                f"{old}/block/main/blk017276",
                "5" * 64,
                "block",
                "main",
                4,
                (10,),
                f"{old}/section/main/sec002679",
            ),
        ),
    )
    decision = classify_missing_chapter(evidence)
    numbered = replace(
        evidence,
        enclosing_topology=(replace(evidence.enclosing_topology[0], heading_raw_text="7.2 WRONG"),),
    )
    assert "numbered_enclosing_section" in classify_missing_chapter(numbered).reason_codes
    sections, content = _projection_fixture()
    body = sections[0]
    child = sections[2]
    body["id"] = f"{new}/section/main/sec000001"
    body["document_id"] = f"{new}/document/main"
    enclosure = _section(
        f"{new}/section/main/sec002679",
        3,
        "semantic",
        body["id"],
        f"{new}/block/main/enclosing",
        "enclosing-key",
    )
    enclosure["document_id"] = f"{new}/document/main"
    enclosure["semantic_level"] = 3
    enclosure["source_stable_item_key"] = "4" * 64
    child["id"] = f"{new}/section/main/sec002680"
    child["document_id"] = f"{new}/document/main"
    child["parent_section_id"] = enclosure["id"]
    child["semantic_level"] = 4
    child["heading_block_id"] = f"{new}/block/main/child"
    child["source_stable_item_key"] = "child-key"
    for item in content:
        item["id"] = item["id"].replace("exv1-" + "a" * 64, new)
        item["section_id"] = (
            child["id"]
            if item.get("stable_item_key") in {"child-key", "end-key"}
            else item["section_id"].replace("exv1-" + "a" * 64, new)
        )
        item["regions"][0]["page_id"] = item["regions"][0]["page_id"].replace(
            "exv1-" + "a" * 64, new
        )
    content.append(
        _content(
            f"{new}/block/main/enclosing",
            "4" * 64,
            enclosure["id"],
            101,
            10,
            "heading_owner",
        )
    )
    content[-1]["canonical_text"] = "UNNUMBERED ENCLOSURE"
    content.extend(
        [
            _content(
                f"{new}/block/main/blk017276",
                "5" * 64,
                enclosure["id"],
                103,
                10,
                "direct_body",
            ),
            _content(
                f"{new}/block/main/post-boundary",
                "6" * 64,
                enclosure["id"],
                201,
                20,
                "direct_body",
            ),
        ]
    )
    next(item for item in content if item["stable_item_key"] == "child-key")["canonical_text"] = (
        "8.2 RATIONALE"
    )
    content.sort(key=lambda item: item["sequence"])
    projection = project_missing_chapter_decisions(
        [body, sections[1], enclosure, child],
        content,
        (decision,),
        section_target_redirects={
            f"{old}/section/main/sec009999": str(body["id"]),
        },
        source_section_target_correspondence={
            f"{old}/section/main/sec009999": str(body["id"]),
        },
    )
    assert projection.chapter_target_ids["8"].startswith(new)
    target_id = projection.chapter_target_ids["8"]
    target = next(item for item in projection.sections if item["id"] == target_id)
    current_enclosure = next(item for item in projection.sections if item["id"] == enclosure["id"])
    assert current_enclosure["parent_section_id"] == body["id"]
    assert current_enclosure["heading_block_id"] == f"{new}/block/main/enclosing"
    assert child["id"] in {item["id"] for item in projection.sections}
    assert f"{new}/block/main/blk017276" in target["chapter_scope_content_ids"]
    assert f"{new}/block/main/post-boundary" not in target["chapter_scope_content_ids"]


def test_child_marker_terminal_boundary_and_redirect_merge_fail_closed() -> None:
    mismatch = replace(
        _evidence(),
        child_topology=(replace(_evidence().child_topology[0], heading_raw_text="7.1 WRONG"),),
    )
    assert "child_chapter_marker_mismatch" in classify_missing_chapter(mismatch).reason_codes
    bad_terminal = replace(
        _evidence(),
        following_boundary=ChapterBoundaryEvidence(
            "document/main",
            None,
            "document end",
            1,
            source_id="main",
            content_order=201,
            boundary_kind="document_end",
        ),
    )
    assert "invalid_document_end_boundary" in classify_missing_chapter(bad_terminal).reason_codes
    partial = replace(
        _evidence(),
        following_boundary=replace(
            _evidence().following_boundary,
            scope_start_record_id="block/main/scope",
        ),
    )
    assert "incomplete_scope_boundary_evidence" in classify_missing_chapter(partial).reason_codes
    decision = classify_missing_chapter(_evidence())
    sections, content = _projection_fixture()
    repeated = RepeatedHeadingProjection(
        sections,
        content,
        {
            "old06d": "new06d",
            str(sections[2]["id"]): "surviving-06d-section",
        },
        {"heading06d": "new06d"},
        {
            "old06d": "new06d",
            str(sections[2]["id"]): "surviving-06d-section",
        },
    )
    projection = project_missing_chapter_decisions(
        repeated.sections,
        repeated.content,
        (decision,),
        section_target_redirects=repeated.section_target_redirects,
        heading_target_redirects=repeated.heading_target_redirects,
        source_section_target_correspondence=(repeated.source_section_target_correspondence),
    )
    assert projection.source_section_target_correspondence["old06d"] == "new06d"
    assert projection.source_section_target_correspondence == (
        repeated.source_section_target_correspondence
    )
    terminal = classify_missing_chapter(
        replace(
            _evidence(),
            following_boundary=ChapterBoundaryEvidence(
                "document/main",
                None,
                "document end",
                19,
                source_id="main",
                content_order=201,
                boundary_kind="document_end",
            ),
        )
    )
    with pytest.raises(Exception, match="document-end boundary changed"):
        project_missing_chapter_decisions(sections, content, (terminal,), page_count=19)


def test_nullable_nontext_scope_boundary_resolves_by_record_ref_and_precedes_heading() -> None:
    sections, content = _projection_fixture()
    prefix = "exv1-" + "a" * 64
    table = _content(
        f"{prefix}/table/main/tbl-boundary",
        None,
        str(sections[0]["id"]),
        1,
        20,
        "inherited_nontext",
    )
    table["record_type"] = "table"
    content.insert(4, table)
    boundary = replace(
        _evidence().following_boundary,
        scope_start_record_id="table/main/tbl-boundary",
        scope_start_stable_key=None,
        scope_start_content_order=4,
    )
    decision = classify_missing_chapter(replace(_evidence(), following_boundary=boundary))
    assert decision.status == "eligible"
    project_missing_chapter_decisions(sections, content, (decision,))
    false_key = replace(decision, following_scope_start_stable_key="8" * 64)
    with pytest.raises(Exception, match="scope boundary changed|scope boundary is absent"):
        project_missing_chapter_decisions(sections, content, (false_key,))
    content.append(
        _content(
            f"{prefix}/block/main/after-boundary",
            "7" * 64,
            str(sections[0]["id"]),
            201,
            20,
            "direct_body",
        )
    )
    post = replace(
        decision,
        following_scope_start_ref="block/main/after-boundary",
        following_scope_start_stable_key="7" * 64,
        following_scope_start_content_order=6,
    )
    with pytest.raises(Exception, match="scope boundary changed"):
        project_missing_chapter_decisions(sections, content, (post,))


def test_reclassification_preservation_is_exactly_decision_bound() -> None:
    old_id, new_id = "exv1-" + "a" * 64, "exv1-" + "b" * 64
    key = "3" * 64
    old = _content(f"{old_id}/block/main/a", key, f"{old_id}/section/main/s", 1, 1, "furniture")
    new = copy.deepcopy(old)
    new["id"] = new["id"].replace(old_id, new_id)
    new["section_id"] = new["section_id"].replace(old_id, new_id)
    new["regions"][0]["page_id"] = new["regions"][0]["page_id"].replace(old_id, new_id)
    new["content_layer"] = "body"
    new["semantic_placement"] = "heading_owner"
    allowed = compare_baseline_collections(
        {"blocks": [old]},
        {"blocks": [new]},
        baseline_candidate_id=old_id,
        new_candidate_id=new_id,
        authorized_heading_component_keys=frozenset({key}),
    )
    denied = compare_baseline_collections(
        {"blocks": [old]}, {"blocks": [new]}, baseline_candidate_id=old_id, new_candidate_id=new_id
    )
    assert allowed["undeclared_difference_count"] == 0
    assert denied["undeclared_difference_count"] == 1
    unchanged = copy.deepcopy(new)
    unchanged["content_layer"] = "body"
    baseline_body = copy.deepcopy(unchanged)
    baseline_body["id"] = baseline_body["id"].replace(new_id, old_id)
    baseline_body["section_id"] = baseline_body["section_id"].replace(new_id, old_id)
    baseline_body["regions"][0]["page_id"] = baseline_body["regions"][0]["page_id"].replace(
        new_id, old_id
    )
    ordinary = compare_baseline_collections(
        {"blocks": [baseline_body]},
        {"blocks": [unchanged]},
        baseline_candidate_id=old_id,
        new_candidate_id=new_id,
        authorized_heading_component_keys=frozenset({key}),
    )
    assert ordinary["undeclared_difference_count"] == 0


def test_projection_preserves_blocks_and_does_not_steal_unrelated_content() -> None:
    direct_key = "4" * 64
    decision = classify_missing_chapter(
        replace(
            _evidence(),
            direct_content_topology=(
                DirectContentEvidence(
                    "block/main/unrelated",
                    direct_key,
                    "block",
                    "main",
                    3,
                    (10,),
                    "section/main/sec000001",
                ),
            ),
        )
    )
    sections, content = _projection_fixture()
    body = str(sections[0]["id"])
    child_id = str(sections[2]["id"])
    prefix = "exv1-" + "a" * 64
    content.insert(
        3,
        _content(f"{prefix}/block/main/unrelated", direct_key, body, 103, 10, "direct_body"),
    )
    projection = project_missing_chapter_decisions(
        sections,
        content,
        (decision,),
        decisions_ref={"path": "06e/eligible_decisions.jsonl", "sha256": "f" * 64},
    )
    target = projection.chapter_target_ids["8"]
    by_key = {item["stable_item_key"]: item for item in projection.content}
    assert by_key[KEYS[0]]["semantic_placement"] == "heading_owner"
    assert by_key[KEYS[1]]["semantic_placement"] == "heading_component"
    assert by_key[direct_key]["section_id"] == body
    target_section = next(item for item in projection.sections if item["id"] == target)
    assert by_key[direct_key]["id"] in target_section["chapter_scope_content_ids"]
    assert (
        projection.direct_content_ownership_correspondence[0]["original_owner_section_id"] == body
    )
    assert (
        next(item for item in projection.sections if item["id"] == child_id)["parent_section_id"]
        == target
    )
    aliases = build_missing_chapter_alias_seeds((decision,), projection)
    assert {item.raw_value for item in aliases} == {"Chapter 8 Alternatives", "Chapter 8"}


def test_direct_scope_rejects_missing_extra_and_unrelated_owner_evidence() -> None:
    sections, content = _projection_fixture()
    body = str(sections[0]["id"])
    prefix = "exv1-" + "a" * 64
    direct_key = "4" * 64
    direct = _content(f"{prefix}/block/main/blk018715", direct_key, body, 103, 10, "direct_body")
    content.insert(3, direct)
    with pytest.raises(Exception, match="topology is incomplete"):
        project_missing_chapter_decisions(
            sections, content, (classify_missing_chapter(_evidence()),)
        )
    fact = DirectContentEvidence(
        "block/main/blk018715",
        direct_key,
        "block",
        "main",
        3,
        (10,),
        "section/main/sec000001",
    )
    complete = classify_missing_chapter(replace(_evidence(), direct_content_topology=(fact,)))
    project_missing_chapter_decisions(sections, content, (complete,))
    with pytest.raises(Exception, match="topology is incomplete"):
        project_missing_chapter_decisions(
            sections,
            _projection_fixture()[1],
            (complete,),
        )
    unrelated_owner = classify_missing_chapter(
        replace(
            _evidence(),
            direct_content_topology=(replace(fact, original_owner_ref="section/main/sec009999"),),
        )
    )
    with pytest.raises(Exception, match="owner is outside"):
        project_missing_chapter_decisions(sections, content, (unrelated_owner,))


def test_global_mixed_start_index_supports_interleaved_multi_page_nontext() -> None:
    sections, content = _projection_fixture()
    body = str(sections[0]["id"])
    prefix = "exv1-" + "a" * 64
    key = None
    table = _content(f"{prefix}/table/main/tbl000001", key, body, 1, 10, "inherited_nontext")
    table["record_type"] = "table"
    table["regions"].append({"page_id": f"{prefix}/page/main/p000011"})
    content.insert(0, table)
    decision = classify_missing_chapter(
        replace(
            _evidence(),
            direct_content_topology=(
                DirectContentEvidence(
                    "table/main/tbl000001",
                    key,
                    "table",
                    "main",
                    0,
                    (10, 11),
                    "section/main/sec000001",
                ),
            ),
            start_record_ref="table/main/tbl000001",
            start_content_order=0,
        )
    )
    assert decision.status == "eligible"
    assert (
        "start_anchor_mismatch"
        in classify_missing_chapter(
            replace(
                _evidence(),
                direct_content_topology=decision.direct_content_topology,
                start_record_ref="table/main/tbl000001",
                start_content_order=1,
            )
        ).reason_codes
    )
    decision_ref = {"path": "06e/eligible_decisions.jsonl", "sha256": "f" * 64}
    projection = project_missing_chapter_decisions(
        sections, content, (decision,), decisions_ref=decision_ref
    )
    assert projection.direct_content_ownership_correspondence[0]["content_record_id"].endswith(
        "/table/main/tbl000001"
    )
    record = build_missing_chapter_correspondence(decision, projection)
    validate_missing_chapter_correspondence(
        {
            "schema_version": "er_commons.recovery.missing_chapter_correspondence.v1",
            "records": [record],
        },
        schema_path=ROOT / CORRESPONDENCE_SCHEMA_RELATIVE_PATH,
        sections=projection.sections,
        content=projection.content,
        content_record_count=len(projection.content),
        expected_decision_ref=decision_ref,
    )


def test_source_shaped_chapter9_enclosure_owned_blk018715_is_in_scope() -> None:
    """The accepted Chapter 9 omission shape is explicit without changing direct ownership."""
    sections, content = _projection_fixture()
    body = str(sections[0]["id"])
    prefix = "exv1-" + "a" * 64
    key = "4" * 64
    enclosure_key = "5" * 64
    enclosure = _section(
        f"{prefix}/section/main/sec003330",
        3,
        "semantic",
        body,
        f"{prefix}/block/main/enclosure9",
        enclosure_key,
    )
    child = sections[2]
    child["sequence"] = 4
    child["semantic_level"] = 4
    child["parent_section_id"] = enclosure["id"]
    sections.insert(2, enclosure)
    content.insert(
        0,
        _content(
            f"{prefix}/block/main/enclosure9",
            enclosure_key,
            enclosure["id"],
            90,
            9,
            "heading_owner",
        ),
    )
    content[0]["canonical_text"] = "UNNUMBERED CHAPTER GROUP"
    content.insert(
        4,
        _content(
            f"{prefix}/block/main/blk018715",
            key,
            enclosure["id"],
            103,
            10,
            "direct_body",
        ),
    )
    next(item for item in content if item["stable_item_key"] == KEYS[0])["canonical_text"] = (
        "CHAPTER 9"
    )
    next(item for item in content if item["stable_item_key"] == KEYS[1])["canonical_text"] = (
        "SUBSEQUENT EIR ANALYSIS AND FINDINGS"
    )
    next(item for item in content if item["stable_item_key"] == "child-key")["canonical_text"] = (
        "9.1 INTRODUCTION"
    )
    next(item for item in content if item["stable_item_key"] == "9" * 64)["canonical_text"] = (
        "CHAPTER 10"
    )
    base = _evidence()
    evidence = replace(
        base,
        chapter_marker="9",
        heading_components=(
            replace(base.heading_components[0], raw_text="CHAPTER 9"),
            replace(
                base.heading_components[1],
                raw_text="SUBSEQUENT EIR ANALYSIS AND FINDINGS",
            ),
        ),
        toc_evidence=(
            ChapterTocEvidence(
                ("toc9",),
                "Chapter 9 Subsequent EIR Analysis and Findings",
                source_id="main",
            ),
        ),
        child_topology=(
            replace(
                base.child_topology[0],
                parent_ref=str(enclosure["id"]),
                semantic_level=4,
                heading_raw_text="9.1 INTRODUCTION",
            ),
        ),
        enclosing_section_refs=(enclosure_key,),
        enclosing_topology=(
            EnclosingSectionEvidence(
                enclosure_key,
                "main",
                enclosure_key,
                str(enclosure["heading_block_id"]),
                "UNNUMBERED CHAPTER GROUP",
                90,
                body,
                3,
            ),
        ),
        following_boundary=replace(base.following_boundary, raw_text="CHAPTER 10"),
        direct_content_topology=(
            DirectContentEvidence(
                "block/main/blk018715",
                key,
                "block",
                "main",
                4,
                (10,),
                "section/main/sec003330",
            ),
        ),
    )
    decision = classify_missing_chapter(evidence)
    assert decision.status == "eligible"
    projection = project_missing_chapter_decisions(sections, content, (decision,))
    target = next(
        item for item in projection.sections if item["id"] == projection.chapter_target_ids["9"]
    )
    assert f"{prefix}/block/main/blk018715" in target["chapter_scope_content_ids"]
    assert (
        next(item for item in projection.content if item["stable_item_key"] == key)["section_id"]
        == enclosure["id"]
    )
    projected_enclosure = next(
        item for item in projection.sections if item["id"] == enclosure["id"]
    )
    assert projected_enclosure["parent_section_id"] == body
    assert projected_enclosure["heading_block_id"] == enclosure["heading_block_id"]


@pytest.mark.parametrize(
    ("marker", "opening_ids", "direct_id", "component_ids"),
    (
        (
            "8",
            ("blk017273", "blk017274", "blk017275"),
            "blk017276",
            ("blk029572", "blk029573"),
        ),
        (
            "9",
            tuple(f"blk{number:06d}" for number in range(18692, 18703)),
            "blk018703",
            ("blk030330", "blk030331"),
        ),
    ),
)
def test_source_shaped_child_opening_precedes_recovered_heading(
    marker: str,
    opening_ids: tuple[str, ...],
    direct_id: str,
    component_ids: tuple[str, str],
) -> None:
    """Chapters 8 and 9 retain opening subsection content before a late heading."""
    evidence, sections, content = _late_heading_source_fixture(
        marker, opening_ids, direct_id, component_ids
    )
    decision = classify_missing_chapter(evidence)
    assert decision.status == "eligible"
    projection = project_missing_chapter_decisions(sections, content, (decision,))
    target_id = projection.chapter_target_ids[marker]
    target = next(item for item in projection.sections if item["id"] == target_id)
    opening_record_ids = [f"exv1-{'a' * 64}/block/main/{record_id}" for record_id in opening_ids]
    assert target["start_record_id"] == opening_record_ids[0]
    assert target["chapter_scope_content_ids"][: len(opening_ids)] == opening_record_ids
    assert target["ordered_child_ids"][0].endswith("/section/main/sec000003")
    assert target["ordered_child_ids"].index(target["heading_block_id"]) > 0
    validate_sections(_projection_view(projection.sections, projection.content))


def test_late_heading_scope_rejects_omitted_child_content_and_invalid_start() -> None:
    """A later observed heading cannot truncate or replace the logical child start."""
    evidence, sections, content = _late_heading_source_fixture(
        "8",
        ("blk017273", "blk017274", "blk017275"),
        "blk017276",
        ("blk029572", "blk029573"),
    )
    invalid = replace(evidence, start_record_ref="not-the-first-child")
    assert "start_anchor_mismatch" in classify_missing_chapter(invalid).reason_codes
    late_start = replace(
        evidence,
        start_record_ref=evidence.heading_components[0].stable_item_key,
        start_content_order=evidence.heading_components[0].sequence,
    )
    late_decision = classify_missing_chapter(late_start)
    assert late_decision.status == "eligible"
    with pytest.raises(Exception, match="selected child content falls outside scope"):
        project_missing_chapter_decisions(sections, content, (late_decision,))

    projection = project_missing_chapter_decisions(
        sections, content, (classify_missing_chapter(evidence),)
    )
    changed_content = copy.deepcopy(projection.content)
    selected_child = next(
        item for item in projection.sections if item.get("source_stable_item_key") == "child-key"
    )
    escaped = copy.deepcopy(changed_content[-1])
    escaped["id"] = str(escaped["id"]) + "-selected-child"
    escaped["section_id"] = selected_child["id"]
    changed_content.append(escaped)
    with pytest.raises(Exception, match="selected child content falls outside its scope"):
        validate_sections(_projection_view(projection.sections, changed_content))

    changed_sections = copy.deepcopy(projection.sections)
    chapter_id = projection.chapter_target_ids["8"]
    changed_child = next(
        item for item in changed_sections if item.get("source_stable_item_key") == "child-key"
    )
    changed_child["parent_section_id"] = changed_sections[0]["id"]
    changed_child["section_path_ids"] = [changed_sections[0]["id"], changed_child["id"]]
    with pytest.raises(Exception, match="selected children differ from its descendants"):
        validate_sections(_projection_view(changed_sections, projection.content))
    assert chapter_id != changed_child["parent_section_id"]


def test_composite_components_exactly_invert_direct_heading_ownership() -> None:
    """Omitted, reordered, or unrelated component declarations fail closed."""
    decision = classify_missing_chapter(_evidence())
    sections, content = _projection_fixture()
    projection = project_missing_chapter_decisions(
        sections,
        content,
        (decision,),
        decisions_ref={"path": "06e/eligible_decisions.jsonl", "sha256": "f" * 64},
    )

    def view(projected_sections: list[dict[str, object]]) -> DocumentStructureBundleView:
        return DocumentStructureBundleView(
            {
                "document_id": projected_sections[0]["document_id"],
                "global_content_order_ids": [item["id"] for item in projection.content],
                "sections": projected_sections,
                "content": projection.content,
                "page_label_observations": [],
                "target_aliases": [],
                "bridge_entries": [],
            }
        )

    validate_sections(view(projection.sections))
    target_id = projection.chapter_target_ids["8"]
    for mutation in ("omitted", "reordered", "unrelated"):
        changed = copy.deepcopy(projection.sections)
        target = next(item for item in changed if item["id"] == target_id)
        component_ids = list(target["heading_component_block_ids"])
        if mutation == "omitted":
            target["heading_component_block_ids"] = component_ids[:-1]
        elif mutation == "reordered":
            target["heading_component_block_ids"] = list(reversed(component_ids))
        else:
            target["heading_component_block_ids"] = [
                *component_ids,
                projection.content[-1]["id"],
            ]
        with pytest.raises(Exception, match="composite heading components differ"):
            validate_sections(view(changed))
    orphaned = copy.deepcopy(projection.content)
    orphan = copy.deepcopy(orphaned[-1])
    orphan["id"] = str(orphan["id"]) + "-orphan"
    orphan["section_id"] = str(projection.sections[0]["id"])
    orphan["semantic_placement"] = "heading_component"
    orphaned.append(orphan)
    with pytest.raises(Exception, match="orphaned from a composite owner"):
        validate_sections(
            DocumentStructureBundleView(
                {
                    "document_id": projection.sections[0]["document_id"],
                    "global_content_order_ids": [item["id"] for item in orphaned],
                    "sections": projection.sections,
                    "content": orphaned,
                    "page_label_observations": [],
                    "target_aliases": [],
                    "bridge_entries": [],
                }
            )
        )


def test_chapter_aliases_are_bound_to_whole_chapter_identity() -> None:
    decision = classify_missing_chapter(_evidence())
    sections, content = _projection_fixture()
    projection = project_missing_chapter_decisions(
        sections,
        content,
        (decision,),
        decisions_ref={"path": "06e/eligible_decisions.jsonl", "sha256": "f" * 64},
    )
    extraction_id = projection.sections[0]["id"].split("/section/", 1)[0]
    aliases = build_target_aliases(
        build_missing_chapter_alias_seeds((decision,), projection),
        extraction_id=extraction_id,
        document_id=str(projection.sections[0]["document_id"]),
        source_id="main",
    )
    bundle = {
        "document_id": projection.sections[0]["document_id"],
        "global_content_order_ids": [item["id"] for item in projection.content],
        "sections": projection.sections,
        "content": projection.content,
        "page_label_observations": [],
        "target_aliases": aliases,
        "bridge_entries": [],
    }
    validate_target_aliases(DocumentStructureBundleView(bundle))
    child = next(item for item in sections if item["section_kind"] == "semantic")
    mixed_seeds = [
        *build_missing_chapter_alias_seeds((decision,), projection),
        AliasSeed.canonical_target(
            alias_kind="section",
            raw_value="Chapter 8 Alternatives",
            target_id=str(child["id"]),
            target_type="section",
            target_order=102,
            evidence_kind="heading_text",
            evidence_ref={"path": "06a/decisions.jsonl", "sha256": "a" * 64},
        ),
    ]
    mixed = copy.deepcopy(bundle)
    mixed["target_aliases"] = build_target_aliases(
        mixed_seeds,
        extraction_id=extraction_id,
        document_id=str(projection.sections[0]["document_id"]),
        source_id="main",
    )
    assert any(item["resolution_status"] == "ambiguous" for item in mixed["target_aliases"])
    validate_target_aliases(DocumentStructureBundleView(mixed))
    unrelated = copy.deepcopy(bundle)
    unrelated["target_aliases"][0]["targets"][0]["evidence_ref"]["sha256"] = "0" * 64
    with pytest.raises(Exception, match="projected chapter"):
        validate_target_aliases(DocumentStructureBundleView(unrelated))
    bad = copy.deepcopy(bundle)
    bad["target_aliases"] = [bad["target_aliases"][0]]
    bad["target_aliases"][0]["sequence"] = 1
    bad["target_aliases"][0]["targets"][0]["target_id"] = next(
        item["id"] for item in sections if item["section_kind"] == "semantic"
    )
    with pytest.raises(Exception, match="projected chapter"):
        validate_target_aliases(DocumentStructureBundleView(bad))


def test_correspondence_schema_and_section_inverse_fail_closed() -> None:
    """Construction validates both the closed record and its projected-section inverse."""
    decision = classify_missing_chapter(_evidence())
    sections, content = _projection_fixture()
    projection = project_missing_chapter_decisions(
        sections,
        content,
        (decision,),
        decisions_ref={"path": "06e/eligible_decisions.jsonl", "sha256": "f" * 64},
    )
    record = build_missing_chapter_correspondence(decision, projection)
    payload = {
        "schema_version": "er_commons.recovery.missing_chapter_correspondence.v1",
        "records": [record],
    }
    validate_missing_chapter_correspondence(
        payload,
        schema_path=ROOT / CORRESPONDENCE_SCHEMA_RELATIVE_PATH,
        sections=projection.sections,
        content=projection.content,
        content_record_count=len(projection.content),
        expected_decision_ref={"path": "06e/eligible_decisions.jsonl", "sha256": "f" * 64},
    )
    malformed = copy.deepcopy(payload)
    del malformed["records"][0]["new_target"]
    with pytest.raises(Exception, match="schema violation"):
        validate_missing_chapter_correspondence(
            malformed, schema_path=ROOT / CORRESPONDENCE_SCHEMA_RELATIVE_PATH
        )
    mismatched = copy.deepcopy(payload)
    mismatched["records"][0]["ordered_child_refs"] = ["wrong-child"]
    with pytest.raises(Exception, match="differs from section field ordered_child_refs") as error:
        validate_missing_chapter_correspondence(
            mismatched,
            schema_path=ROOT / CORRESPONDENCE_SCHEMA_RELATIVE_PATH,
            sections=projection.sections,
            content_record_count=len(projection.content),
        )
    for coordinate in ("chapter='8'", "record=", "field=", "expected=", "observed="):
        assert coordinate in str(error.value)
    wrong_candidate = copy.deepcopy(payload)
    wrong_candidate["records"][0]["new_target"]["section_id"] = (
        "exv1-" + "e" * 64 + "/section/main/sec000999"
    )
    with pytest.raises(Exception, match="semantic binding failed"):
        validate_missing_chapter_correspondence(
            wrong_candidate,
            schema_path=ROOT / CORRESPONDENCE_SCHEMA_RELATIVE_PATH,
            candidate_id="exv1-" + "a" * 64,
        )
    for records in ([payload["records"][0], payload["records"][0]],):
        duplicate = copy.deepcopy(payload)
        duplicate["records"] = records
        with pytest.raises(Exception, match="schema violation"):
            validate_missing_chapter_correspondence(
                duplicate, schema_path=ROOT / CORRESPONDENCE_SCHEMA_RELATIVE_PATH
            )
    second = copy.deepcopy(payload["records"][0])
    second["chapter_marker"] = "9"
    second["new_target"]["section_id"] = second["new_target"]["section_id"].replace(
        "sec000004", "sec000005"
    )
    second["logical_content_page_extent"] = [20, 29]
    reversed_payload = copy.deepcopy(payload)
    reversed_payload["records"] = [second, payload["records"][0]]
    with pytest.raises(Exception, match="semantic binding failed"):
        validate_missing_chapter_correspondence(
            reversed_payload, schema_path=ROOT / CORRESPONDENCE_SCHEMA_RELATIVE_PATH
        )
    substituted = copy.deepcopy(payload)
    substituted["records"][0]["decision_ref"]["sha256"] = "0" * 64
    with pytest.raises(Exception, match="unexpected decision artifact"):
        validate_missing_chapter_correspondence(
            substituted,
            schema_path=ROOT / CORRESPONDENCE_SCHEMA_RELATIVE_PATH,
            expected_decision_ref={
                "path": "06e/eligible_decisions.jsonl",
                "sha256": "f" * 64,
            },
        )
    foreign_component = copy.deepcopy(payload)
    foreign_component["records"][0]["retained_heading_block_ids"][0] = (
        "exv1-" + "e" * 64 + "/block/main/blk000008"
    )
    with pytest.raises(Exception, match="semantic binding failed"):
        validate_missing_chapter_correspondence(
            foreign_component, schema_path=ROOT / CORRESPONDENCE_SCHEMA_RELATIVE_PATH
        )
    foreign_boundary = copy.deepcopy(payload)
    foreign_boundary["records"][0]["following_boundary_record_id"] = (
        "exv1-" + "e" * 64 + "/block/main/blk000009"
    )
    with pytest.raises(Exception, match="semantic binding failed"):
        validate_missing_chapter_correspondence(
            foreign_boundary, schema_path=ROOT / CORRESPONDENCE_SCHEMA_RELATIVE_PATH
        )


def test_toc_census_distinguishes_recovered_and_derived_titles() -> None:
    sections = {
        "recovered": CensusSection(None, None, "composite_semantic", "Chapter 8"),
        "fallback": CensusSection(None, None, "derived_chapter", "Chapter 9"),
    }
    assert "recovered title: Chapter 8" in _section_headings("recovered", sections, {})
    assert "derived title: Chapter 9" in _section_headings("fallback", sections, {})


def test_projection_rejects_topology_drift_overlap_and_unpinned_aliases() -> None:
    decision = classify_missing_chapter(_evidence())
    sections, content = _projection_fixture()
    changed = [dict(item) for item in sections]
    next(item for item in changed if item.get("source_stable_item_key") == "child-key")[
        "semantic_level"
    ] = 4
    with pytest.raises(Exception, match="frozen child topology changed") as error:
        project_missing_chapter_decisions(changed, content, (decision,))
    for coordinate in (
        "chapter='8'",
        "record=",
        "field='semantic_level'",
        "expected=3",
        "observed=4",
    ):
        assert coordinate in str(error.value)
    with pytest.raises(Exception, match="extents overlap"):
        project_missing_chapter_decisions(
            sections, content, (decision, replace(decision, chapter_marker="9"))
        )
    starts_after_heading = replace(
        decision,
        start_record_ref="child-key",
        start_content_order=102,
    )
    with pytest.raises(Exception, match="heading components fall outside scope"):
        project_missing_chapter_decisions(sections, content, (starts_after_heading,))
    projection = project_missing_chapter_decisions(sections, content, (decision,))
    with pytest.raises(Exception, match="checksum-pinned"):
        build_missing_chapter_alias_seeds((decision,), projection)


def test_logical_section_start_prefers_restored_scope_start_only() -> None:
    """The shared consumer helper leaves ordinary heading semantics unchanged."""
    ordinary = {
        "section_kind": "semantic",
        "heading_block_id": "block-heading",
        "start_record_id": "legacy-start",
    }
    recovered = {
        "section_kind": "composite_semantic",
        "heading_block_id": "late-heading",
        "start_record_id": "first-child-anchor",
    }
    fallback = {
        "section_kind": "derived_chapter",
        "heading_block_id": None,
        "start_record_id": "first-child-anchor",
    }
    assert logical_section_start_id(ordinary) == "block-heading"
    assert logical_section_start_id(recovered) == "first-child-anchor"
    assert logical_section_start_id(fallback) == "first-child-anchor"


def test_projection_uses_composite_child_logical_start_before_its_late_heading() -> None:
    """Nested recovered targets are ordered by scope start, not a later heading block."""
    decision = classify_missing_chapter(_evidence())
    sections, content = _projection_fixture()
    child = next(item for item in sections if item.get("source_stable_item_key") == "child-key")
    start_id = str(child["heading_block_id"])
    late_heading_id = "exv1-" + "a" * 64 + "/block/main/late-child-heading"
    child["section_kind"] = "composite_semantic"
    child["start_record_id"] = start_id
    child["heading_block_id"] = late_heading_id
    late_heading = _content(
        late_heading_id,
        "8" * 64,
        str(child["id"]),
        103,
        10,
        "heading_owner",
    )
    late_heading["canonical_text"] = "RECOVERED 8.1 HEADING"
    content.insert(3, late_heading)

    projection = project_missing_chapter_decisions(sections, content, (decision,))
    target_id = projection.chapter_target_ids["8"]
    projected_child = next(item for item in projection.sections if item["id"] == child["id"])
    assert logical_section_start_id(projected_child) == start_id
    assert projected_child["parent_section_id"] == target_id


def test_fallback_target_is_distinct_from_first_child_and_matches_v3_schema() -> None:
    evidence = _evidence(components=False)
    decision = classify_missing_chapter(
        replace(
            evidence,
            toc_evidence=(replace(evidence.toc_evidence[0], destination_physical_pages=(10,)),),
        )
    )
    sections, content = _projection_fixture(include_components=False)
    projection = project_missing_chapter_decisions(
        sections,
        content,
        (decision,),
        decisions_ref={"path": "06e/eligible_decisions.jsonl", "sha256": "f" * 64},
    )
    target_id = projection.chapter_target_ids["8"]
    child_id = next(
        item["id"] for item in sections if item.get("source_stable_item_key") == "child-key"
    )
    assert target_id != child_id
    target = next(item for item in projection.sections if item["id"] == target_id)
    assert target["heading_block_id"] is None
    schema = json.loads(
        (
            ROOT
            / "benchmarks/er_bench/schemas/canonical_extraction/v3/semantic_structure.schema.json"
        ).read_text()
    )
    Draft202012Validator({"$ref": "#/$defs/semantic_section", "$defs": schema["$defs"]}).validate(
        target
    )
    changed = copy.deepcopy(projection.sections)
    changed_target = next(item for item in changed if item["id"] == target_id)
    changed_target["start_record_id"] = projection.content[-1]["id"]
    with pytest.raises(
        Exception, match="invalid start|first descendant|deterministic document order"
    ):
        validate_sections(
            DocumentStructureBundleView(
                {
                    "document_id": projection.sections[0]["document_id"],
                    "global_content_order_ids": [item["id"] for item in projection.content],
                    "sections": changed,
                    "content": projection.content,
                    "page_label_observations": [],
                    "target_aliases": [],
                    "bridge_entries": [],
                }
            )
        )


def test_fallback_validates_through_the_compact_v3_bundle() -> None:
    """V3 compact support retains the page and marker evidence used by validation."""
    evidence = _evidence(components=False)
    decision = classify_missing_chapter(
        replace(
            evidence,
            toc_evidence=(replace(evidence.toc_evidence[0], destination_physical_pages=(10,)),),
        )
    )
    sections, content = _projection_fixture(include_components=False)
    projection = project_missing_chapter_decisions(
        sections,
        content,
        (decision,),
        decisions_ref={"path": "06e/eligible_decisions.jsonl", "sha256": "f" * 64},
    )
    projection.content[0]["canonical_text"] = "\N{NO-BREAK SPACE}  8.1 INTRODUCTION"
    page_records = []
    for page_number in (10, 19, 20):
        page_records.append(
            {
                "physical_page_number": page_number,
                "ordered_content_ids": [
                    item["id"]
                    for item in projection.content
                    if any(
                        region["page_id"].endswith(f"p{page_number:06d}")
                        for region in item["regions"]
                    )
                ],
            }
        )
    build = DocumentStructureBuild(
        collections={
            "documents": [{"id": projection.sections[0]["document_id"]}],
            "pages": page_records,
            "sections": projection.sections,
            "blocks": projection.content,
            "tables": [],
            "figures": [],
            "cross_references": [],
        },
        page_label_observations=[],
        target_aliases=[],
        bridge_entries=[],
        bridge_evidence={},
        repeated_heading_correspondence=[],
        missing_chapter_correspondence=[build_missing_chapter_correspondence(decision, projection)],
        observed_expectations=DocumentStructureExpectations(
            section_count=len(projection.sections),
            bridge_entry_count=0,
            canonical_block_count=len(projection.content),
            heading_count=sum(
                not str(section["section_kind"]).startswith("synthetic_")
                for section in projection.sections
            ),
            direct_membership_count=0,
            mapped_block_count=sum(
                item["semantic_placement"] == "direct_body" for item in projection.content
            ),
            table_replacement_count=0,
            figure_suppression_count=0,
        ),
    )
    bundle = document_structure_validation_bundle(
        build=build,
        control={},
        correspondence={},
        baseline_producer_run_id="prv1-" + "1" * 64,
        hierarchy_producer_run_id="prv1-" + "2" * 64,
    )
    assert bundle["content"][0]["physical_page_numbers"] == [10]
    assert bundle["content"][0]["canonical_text"] == "\N{NO-BREAK SPACE}  8.1 INTRODUCTION"
    validate_sections(DocumentStructureBundleView(bundle))


def test_compact_publication_is_no_clobber(tmp_path: Path) -> None:
    decision = classify_missing_chapter(_evidence())
    existing = classify_missing_chapter(
        replace(_evidence(), chapter_marker="7", existing_target_id="section/main/chapter7")
    )
    rejected = classify_missing_chapter(
        replace(_evidence(components=False), chapter_marker="6", toc_evidence=())
    )
    output = tmp_path / "qualification_v1"
    schema = json.loads(SCHEMA_PATH.read_text())
    publish_missing_chapter_qualification(
        output,
        decisions=(rejected, existing, decision),
        source_ref=_reference(),
        policy_ref={"path": "docs/specs/missing_chapter_repair_v1.md", "sha256": "a" * 64},
        schema_ref={"path": SCHEMA_PATH.relative_to(ROOT).as_posix(), "sha256": "b" * 64},
        decision_schema=schema,
    )
    assert {item.name for item in output.iterdir()} == {
        "all_decisions.jsonl",
        "eligible_decisions.jsonl",
        "qualification.json",
        "inventory.json",
        "completion.json",
    }
    qualification = json.loads((output / "qualification.json").read_text())
    assert qualification["counts"] == {
        "eligible": 1,
        "already_present": 1,
        "rejected": 1,
        "review_required": 0,
    }
    completion = json.loads((output / "completion.json").read_text())
    assert completion["decision_count"] == 3
    assert completion["decision_counts"] == qualification["counts"]
    with pytest.raises(FileExistsError):
        publish_missing_chapter_qualification(
            output,
            decisions=(decision,),
            source_ref=_reference(),
            policy_ref={"path": "p", "sha256": "a" * 64},
            schema_ref={"path": "s", "sha256": "b" * 64},
            decision_schema=schema,
        )


def _projection_view(
    sections: list[dict[str, object]], content: list[dict[str, object]]
) -> DocumentStructureBundleView:
    return DocumentStructureBundleView(
        {
            "document_id": sections[0]["document_id"],
            "global_content_order_ids": [item["id"] for item in content],
            "sections": sections,
            "content": content,
            "page_label_observations": [],
            "target_aliases": [],
            "bridge_entries": [],
        }
    )


def _late_heading_source_fixture(
    marker: str,
    opening_ids: tuple[str, ...],
    direct_id: str,
    component_ids: tuple[str, str],
) -> tuple[
    MissingChapterEvidence,
    list[dict[str, object]],
    list[dict[str, object]],
]:
    """Build the accepted mixed-order shape where subsection content precedes a header."""
    prefix = "exv1-" + "a" * 64
    body = f"{prefix}/section/main/sec000001"
    furniture = f"{prefix}/section/main/sec000002"
    child_id = f"{prefix}/section/main/sec000003"
    sections = [
        _section(body, 1, "synthetic_body_root", None, None, None),
        _section(furniture, 2, "synthetic_furniture_root", None, None, None),
        _section(
            child_id,
            3,
            "semantic",
            body,
            f"{prefix}/block/main/{opening_ids[0]}",
            "child-key",
        ),
    ]
    child_sequence = 17273 if marker == "8" else 18692
    content = [
        _content(
            f"{prefix}/block/main/{record_id}",
            "child-key" if index == 0 else format(index + 10, "064x"),
            child_id,
            child_sequence + index,
            10,
            "heading_owner" if index == 0 else "direct_body",
        )
        for index, record_id in enumerate(opening_ids)
    ]
    content[0]["canonical_text"] = f"{marker}.1 INTRODUCTION"
    direct_key = "7" * 64
    content.append(
        _content(
            f"{prefix}/block/main/{direct_id}",
            direct_key,
            body,
            child_sequence + len(opening_ids),
            10,
            "direct_body",
        )
    )
    component_texts = (
        ("CHAPTER 8", "ALTERNATIVES")
        if marker == "8"
        else ("CHAPTER 9", "SUBSEQUENT EIR ANALYSIS AND FINDINGS")
    )
    component_sequences = (29572, 29573) if marker == "8" else (30330, 30331)
    for record_id, key, text_value, sequence in zip(
        component_ids, KEYS, component_texts, component_sequences, strict=True
    ):
        component = _content(
            f"{prefix}/block/main/{record_id}",
            key,
            furniture,
            sequence,
            10,
            "furniture",
        )
        component["canonical_text"] = text_value
        content.append(component)
    boundary = _content(
        f"{prefix}/block/main/boundary-{marker}",
        "9" * 64,
        body,
        40000,
        11,
        "direct_body",
    )
    boundary["canonical_text"] = f"CHAPTER {int(marker) + 1}"
    content.append(boundary)
    headings = tuple(
        ChapterHeadingComponent(
            block_id=f"{prefix}/block/main/{record_id}",
            stable_item_key=key,
            raw_text=text_value,
            physical_page=10,
            sequence=sequence,
            block_type="page_header",
            content_layer="furniture",
            source_id="main",
            corrected_role="heading" if index == 0 else "heading_component",
            reclassification_authorized=True,
            reclassification_authority=(
                "missing_whole_chapter_v1_observed_heading_reclassification"
            ),
        )
        for index, (record_id, key, text_value, sequence) in enumerate(
            zip(component_ids, KEYS, component_texts, component_sequences, strict=True)
        )
    )
    title = f"Chapter {marker} " + component_texts[1].title()
    evidence = MissingChapterEvidence(
        source_id="main",
        chapter_marker=marker,
        heading_components=headings,
        toc_evidence=(ChapterTocEvidence((f"toc{marker}",), title, source_id="main"),),
        ordered_child_refs=("child-key",),
        parent_ref=body,
        semantic_level=2,
        start_record_ref="child-key",
        extent_start_page=10,
        extent_end_page=10,
        following_boundary=ChapterBoundaryEvidence(
            str(boundary["id"]),
            str(boundary["stable_item_key"]),
            str(boundary["canonical_text"]),
            11,
            source_id="main",
            content_order=40000,
        ),
        child_topology=(
            ChapterChildEvidence(
                "child-key",
                "main",
                child_sequence,
                body,
                3,
                10,
                10,
                f"{marker}.1 INTRODUCTION",
            ),
        ),
        direct_content_topology=(
            DirectContentEvidence(
                f"block/main/{direct_id}",
                direct_key,
                "block",
                "main",
                len(opening_ids),
                (10,),
                body,
            ),
        ),
        start_content_order=child_sequence,
    )
    return evidence, sections, content


def _section(
    section_id: str,
    sequence: int,
    kind: str,
    parent: str | None,
    heading: str | None,
    key: str | None,
) -> dict[str, object]:
    return {
        "id": section_id,
        "document_id": section_id.split("/section/")[0] + "/document/main",
        "sequence": sequence,
        "content_layer": "body" if sequence != 2 else "furniture",
        "section_kind": kind,
        "semantic_level": 3 if kind == "semantic" else None,
        "section_path_ids": [section_id],
        "parent_section_id": parent,
        "heading_block_id": heading,
        "ordered_child_ids": [],
        "inference_method": "accepted_hierarchy_correction" if kind == "semantic" else "synthetic",
        "source_stable_item_key": key,
        "evidence_ref": None,
    }


def _projection_fixture(
    *, include_components: bool = True
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    body = "exv1-" + "a" * 64 + "/section/main/sec000001"
    furniture = "exv1-" + "a" * 64 + "/section/main/sec000002"
    child_id = "exv1-" + "a" * 64 + "/section/main/sec000003"
    prefix = "exv1-" + "a" * 64
    sections = [
        _section(body, 1, "synthetic_body_root", None, None, None),
        _section(furniture, 2, "synthetic_furniture_root", None, None, None),
        _section(child_id, 3, "semantic", body, f"{prefix}/block/main/child", "child-key"),
    ]
    content = [
        _content(f"{prefix}/block/main/child", "child-key", child_id, 102, 10, "heading_owner"),
        _content(f"{prefix}/block/main/end", "end-key", child_id, 104, 19, "direct_body"),
        _content(
            f"{prefix}/block/main/boundary",
            "9" * 64,
            body,
            200,
            20,
            "direct_body",
        ),
    ]
    if include_components:
        content[0:0] = [
            _content(f"{prefix}/block/main/a", KEYS[0], furniture, 100, 10, "furniture"),
            _content(f"{prefix}/block/main/b", KEYS[1], furniture, 101, 10, "furniture"),
        ]
    return sections, content


def _content(
    record_id: str, key: str | None, section_id: str, sequence: int, page: int, placement: str
) -> dict[str, object]:
    text = {
        KEYS[0]: "CHAPTER 8",
        KEYS[1]: "ALTERNATIVES",
        "child-key": "8.1 INTRODUCTION",
        "9" * 64: "CHAPTER 9",
    }.get(key, "body")
    return {
        "id": record_id,
        "record_type": "block",
        "content_layer": "furniture" if placement == "furniture" else "body",
        "section_id": section_id,
        "sequence": sequence,
        "semantic_placement": placement,
        "is_toc_row": False,
        "stable_item_key": key,
        "canonical_text": text,
        "block_type": "page_header" if key in {*KEYS, "9" * 64} else "paragraph",
        "regions": [{"page_id": record_id.split("/block/")[0] + f"/page/main/p{page:06d}"}],
    }
