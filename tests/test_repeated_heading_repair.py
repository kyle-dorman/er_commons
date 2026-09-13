"""Source-free policy and projection tests for Task 06D."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from er_commons.document_records.document_structure.aliases import (
    AliasSeed,
    build_appendix_p_alias_seeds,
)
from er_commons.document_records.document_structure.config import DocumentStructureConfig
from er_commons.document_records.document_structure.errors import (
    DocumentStructureInvariantError,
    StructureContractError,
)
from er_commons.document_records.document_structure.inputs import (
    _load_repeated_heading_decisions,
    _verify_repeated_heading_records,
)
from er_commons.document_records.document_structure.parser_evidence import ProducerEvidence
from er_commons.document_records.document_structure.repeated_heading_projection import (
    _heading_topologies_from_records,
)
from er_commons.document_records.document_structure.repeated_heading_qualification import (
    publish_repeated_heading_qualification,
)
from er_commons.document_records.document_structure.repeated_headings import (
    HeadingTopology,
    RepeatedHeadingDecision,
    TocHeadingEvidence,
    build_repeated_heading_correspondence,
    classify_repeated_heading_group,
    project_repeated_heading_decisions,
    redirect_repeated_heading_alias_seeds,
)

REF = {"path": "accepted/decisions.jsonl", "sha256": "a" * 64}
ROOT = Path(__file__).parents[1]
SCHEMA = json.loads(
    (
        ROOT / "benchmarks/er_bench/schemas/task06_recovery/v1/"
        "repeated_heading_decision.schema.json"
    ).read_text()
)
SCHEMA_V2 = json.loads(
    (
        ROOT / "benchmarks/er_bench/schemas/task06_recovery/v1/"
        "repeated_heading_decision_v2.schema.json"
    ).read_text()
)


def _heading(
    suffix: str,
    text: str,
    page: int,
    sequence: int,
    *,
    parent: str = "root",
    level: int = 3,
    children: tuple[str, ...] = (),
    direct: tuple[str, ...] = (),
    extent: tuple[int, int] | None = None,
    layer: str = "body",
    role: str = "heading",
    toc: bool = False,
    sibling_index: int | None = None,
    content_order: int | None = None,
    content_order_extent: tuple[int, int] | None = None,
) -> HeadingTopology:
    resolved_content_order = sequence if content_order is None else content_order
    return HeadingTopology(
        section_id=f"section-{suffix}",
        heading_block_id=f"block-{suffix}",
        stable_item_key=suffix * 64,
        raw_text=text,
        physical_page=page,
        section_sequence=sequence,
        sibling_index=sequence if sibling_index is None else sibling_index,
        parent_section_id=parent,
        semantic_level=level,
        content_layer=layer,
        corrected_role=role,
        is_toc_row=toc,
        direct_content_ids=direct,
        child_section_ids=children,
        descendant_page_extent=extent or (page, page),
        heading_content_order=resolved_content_order,
        descendant_content_order_extent=(
            content_order_extent or (resolved_content_order, resolved_content_order)
        ),
    )


def _observed_group(chapter: str) -> tuple[HeadingTopology, HeadingTopology, HeadingTopology]:
    if chapter == "06":
        return (
            _heading("1", "06 CIRCULATION", 311, 446, sibling_index=0),
            _heading(
                "2",
                "06 | CIRCULATION",
                312,
                447,
                children=tuple(f"section-6-{index}" for index in range(6)),
                extent=(312, 449),
                sibling_index=1,
            ),
            _heading("3", "07 INFRASTRUCTURE", 451, 662, sibling_index=2),
        )
    return (
        _heading("4", "08 PUBLIC FACILITIES FINANCING", 479, 748, sibling_index=0),
        _heading(
            "5",
            "08 | PUBLIC FACILITIES FINANCING",
            480,
            749,
            children=tuple(f"section-8-{index}" for index in range(4)),
            extent=(480, 491),
            sibling_index=1,
        ),
        _heading("6", "09 IMPLEMENTATION", 491, 783, sibling_index=2),
    )


@pytest.mark.parametrize("chapter", ["06", "08"])
def test_observed_shapes_are_one_logical_chapter_without_physical_toc_guess(
    chapter: str,
) -> None:
    divider, opening, following = _observed_group(chapter)
    toc = TocHeadingEvidence(
        evidence_ids=(f"toc-{chapter}",),
        raw_text=opening.raw_text,
        terminal_destination_token="280" if chapter == "06" else "447",
    )

    decision = classify_repeated_heading_group(
        (divider, opening), toc_evidence=(toc,), following_sibling=following
    )

    assert decision.status == "eligible"
    assert decision.anchor_heading_key == divider.stable_item_key
    assert decision.absorbed_heading_key == opening.stable_item_key
    assert decision.destination_physical_pages == ()
    assert decision.extent_start_page == divider.physical_page
    assert decision.following_boundary_page == following.physical_page
    assert decision.following_boundary_stable_key == following.stable_item_key
    assert decision.following_boundary_raw_text == following.raw_text


@pytest.mark.parametrize("extent_end", [452, 500])
def test_complete_descendant_extent_must_end_before_following_boundary(
    extent_end: int,
) -> None:
    divider, opening, following = _observed_group("06")
    decision = classify_repeated_heading_group(
        (divider, replace(opening, descendant_page_extent=(312, extent_end))),
        toc_evidence=(TocHeadingEvidence(("toc",), opening.raw_text),),
        following_sibling=following,
    )
    assert decision.status == "review_required"
    assert "descendant_extent_crosses_following_boundary_page" in decision.reason_codes


def test_destinations_to_either_or_both_retained_pages_do_not_choose_the_anchor() -> None:
    divider, opening, following = _observed_group("06")
    toc = TocHeadingEvidence(("toc",), opening.raw_text, (311, 312), "280")
    decision = classify_repeated_heading_group(
        (divider, opening), toc_evidence=(toc,), following_sibling=following
    )
    assert decision.status == "eligible"
    assert decision.destination_physical_pages == (311, 312)
    assert decision.anchor_heading_key == divider.stable_item_key


def test_sibling_adjacency_is_independent_of_descendant_section_sequence() -> None:
    divider, opening, following = _observed_group("06")
    decision = classify_repeated_heading_group(
        (
            replace(divider, section_sequence=10, sibling_index=2),
            replace(opening, section_sequence=40, sibling_index=3),
        ),
        toc_evidence=(TocHeadingEvidence(("toc",), opening.raw_text),),
        following_sibling=replace(following, sibling_index=4),
    )
    assert decision.status == "eligible"


def test_review_record_retains_matching_and_contradictory_toc_evidence_ids() -> None:
    divider, opening, following = _observed_group("06")
    decision = classify_repeated_heading_group(
        (divider, opening),
        toc_evidence=(
            TocHeadingEvidence(("toc-title", "toc-token"), opening.raw_text),
            TocHeadingEvidence(("toc-conflict",), "06 | TRANSIT"),
        ),
        following_sibling=following,
    )
    assert decision.status == "review_required"
    assert decision.toc_evidence_ids == ("toc-title", "toc-token", "toc-conflict")


def test_decision_record_schema_preserves_unresolved_toc_and_pending_target() -> None:
    divider, opening, following = _observed_group("08")
    decision = classify_repeated_heading_group(
        (divider, opening),
        toc_evidence=(TocHeadingEvidence(("toc-08",), opening.raw_text, (), "447"),),
        following_sibling=following,
    )
    record = decision.as_record(
        source_ref={
            "authority": "task06a_packet",
            "relative_path": "pipelines/recovery/appendix_a_topology.v1.json",
            "identity": "packet-inventory-83c31433",
            "verification_mode": "selected_record_read",
        },
        new_target_ref={
            "authority": "task06d_policy",
            "relative_path": "logical-targets/08",
            "identity": f"logical-chapter-{divider.stable_item_key}",
            "verification_mode": "pending_06g_materialization",
        },
        human_decision_ref={
            "authority": "user_decision",
            "relative_path": "tasks/sprint2/06g_replay_repaired_document_and_collection_stages.md",
            "identity": "user-selected-earlier-boundary-2026-09-12",
            "verification_mode": "recorded_conversation_decision",
        },
    )
    Draft202012Validator.check_schema(SCHEMA_V2)
    Draft202012Validator(SCHEMA_V2).validate(record)
    assert record["unresolved_toc_tokens"] == ["447"]
    assert record["human_decision_ref"]["identity"] == ("user-selected-earlier-boundary-2026-09-12")


def test_v2_same_page_boundary_requires_strict_record_order() -> None:
    divider, opening, following = _observed_group("08")
    toc = (TocHeadingEvidence(("toc-08",), opening.raw_text),)
    accepted = classify_repeated_heading_group(
        (divider, opening), toc_evidence=toc, following_sibling=following
    )
    collision = classify_repeated_heading_group(
        (
            divider,
            replace(
                opening,
                descendant_content_order_extent=(
                    opening.heading_content_order or 0,
                    following.heading_content_order or 0,
                ),
            ),
        ),
        toc_evidence=toc,
        following_sibling=following,
    )
    crossing = classify_repeated_heading_group(
        (divider, replace(opening, descendant_page_extent=(480, 492))),
        toc_evidence=toc,
        following_sibling=following,
    )
    assert accepted.status == "eligible"
    assert accepted.source_page_extents[-1] == (480, 491)
    assert accepted.following_boundary_page == 491
    assert collision.status == "review_required"
    assert "descendant_content_reaches_following_boundary" in collision.reason_codes
    assert crossing.status == "review_required"
    assert "descendant_extent_crosses_following_boundary_page" in crossing.reason_codes


def test_v2_terminal_nonnumeric_boundary_is_eligible() -> None:
    divider = _heading("7", "09 IMPLEMENTATION", 491, 783, sibling_index=0)
    opening = _heading("8", "09 | IMPLEMENTATION", 492, 784, sibling_index=1)
    boundary = _heading("9", "APPENDICES", 501, 798, sibling_index=2)
    decision = classify_repeated_heading_group(
        (divider, opening),
        toc_evidence=(TocHeadingEvidence(("toc-09",), opening.raw_text),),
        following_sibling=boundary,
    )
    assert decision.status == "eligible"
    assert decision.following_boundary_raw_text == "APPENDICES"


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (
            lambda first, second: (first, replace(second, physical_page=313)),
            "nonadjacent_physical_pages",
        ),
        (
            lambda first, second: (first, replace(second, parent_section_id="other")),
            "different_parents",
        ),
        (
            lambda first, second: (first, replace(second, raw_text="09 | CIRCULATION")),
            "chapter_marker_disagreement",
        ),
        (
            lambda first, second: (first, replace(second, raw_text="06 | TRANSIT")),
            "chapter_title_disagreement",
        ),
        (
            lambda first, second: (first, replace(second, raw_text="06 CIRCULATION")),
            "not_divider_then_opening_typography",
        ),
        (
            lambda first, second: (first, replace(second, is_toc_row=True)),
            "toc_or_furniture_ineligible",
        ),
    ],
)
def test_nonqualifying_pairs_remain_distinct(mutation: object, reason: str) -> None:
    divider, opening, following = _observed_group("06")
    changed = mutation(divider, opening)  # type: ignore[operator]
    decision = classify_repeated_heading_group(
        changed,
        toc_evidence=(TocHeadingEvidence(("toc",), opening.raw_text),),
        following_sibling=following,
    )
    assert decision.status == "rejected"
    assert reason in decision.reason_codes


def test_rejected_identical_raw_spellings_remain_schema_valid() -> None:
    divider, opening, following = _observed_group("06")
    decision = classify_repeated_heading_group(
        (divider, replace(opening, raw_text=divider.raw_text)),
        toc_evidence=(TocHeadingEvidence(("toc",), opening.raw_text),),
        following_sibling=following,
    )
    record = decision.as_record(
        source_ref={
            "authority": "task06a_packet",
            "relative_path": "topology.json",
            "identity": "packet-identity",
            "verification_mode": "selected_record_read",
        },
        new_target_ref=None,
    )
    assert decision.status == "rejected"
    assert decision.reason_codes == ("not_divider_then_opening_typography",)
    assert record["heading_raw_texts"] == ["06 CIRCULATION", "06 CIRCULATION"]
    Draft202012Validator(SCHEMA_V2).validate(record)


def test_ambiguous_cardinality_overlap_destination_and_boundary_require_review() -> None:
    divider, opening, following = _observed_group("06")
    toc = TocHeadingEvidence(("toc",), opening.raw_text)
    cardinality = classify_repeated_heading_group(
        (divider, opening, replace(opening, stable_item_key="9" * 64)),
        toc_evidence=(toc,),
        following_sibling=following,
    )
    overlap = classify_repeated_heading_group(
        (
            replace(divider, direct_content_ids=("shared",)),
            replace(opening, direct_content_ids=("shared",)),
        ),
        toc_evidence=(toc,),
        following_sibling=following,
    )
    destination = classify_repeated_heading_group(
        (divider, opening),
        toc_evidence=(replace(toc, destination_physical_pages=(999,)),),
        following_sibling=following,
    )
    no_boundary = classify_repeated_heading_group(
        (divider, opening), toc_evidence=(toc,), following_sibling=None
    )
    no_extent = classify_repeated_heading_group(
        (divider, replace(opening, descendant_page_extent=None)),
        toc_evidence=(toc,),
        following_sibling=following,
    )
    assert cardinality.reason_codes == ("unsupported_cardinality",)
    assert overlap.reason_codes == ("overlapping_child_ownership",)
    assert destination.reason_codes == ("conflicting_toc_destinations",)
    assert no_boundary.reason_codes == ("following_chapter_boundary_absent",)
    assert no_extent.reason_codes == ("descendant_page_extent_absent",)
    assert {cardinality.status, overlap.status, destination.status, no_boundary.status} == {
        "review_required"
    }
    assert no_extent.status == "review_required"


def _section(
    section_id: str,
    key: str | None,
    heading_id: str | None,
    parent: str | None,
    level: int | None,
    sequence: int,
    ordered: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "id": section_id,
        "document_id": "document",
        "sequence": sequence,
        "content_layer": "body",
        "section_kind": "semantic" if key is not None else "synthetic_body_root",
        "semantic_level": level,
        "section_path_ids": [section_id],
        "parent_section_id": parent,
        "heading_block_id": heading_id,
        "ordered_child_ids": list(ordered),
        "inference_method": "accepted_hierarchy_correction" if key is not None else "synthetic",
        "source_stable_item_key": key,
        "evidence_ref": REF if key is not None else None,
    }


def _content(
    record_id: str,
    key: str,
    section_id: str,
    sequence: int,
    placement: str,
    *,
    text: str = "body",
    page: int = 1,
) -> dict[str, object]:
    return {
        "id": record_id,
        "record_type": "block",
        "content_layer": "body",
        "section_id": section_id,
        "sequence": sequence,
        "semantic_placement": placement,
        "is_toc_row": False,
        "stable_item_key": key,
        "canonical_text": text,
        "regions": [{"page_id": f"exv1-test/page/source/p{page:06d}"}],
    }


def test_v2_four_disjoint_pairs_project_once_and_idempotently() -> None:
    headings = (
        ("1", "06 CIRCULATION", 311),
        ("2", "06 | CIRCULATION", 312),
        ("3", "07 INFRASTRUCTURE", 451),
        ("4", "07 | INFRASTRUCTURE", 452),
        ("5", "08 PUBLIC FACILITIES FINANCING", 479),
        ("6", "08 | PUBLIC FACILITIES FINANCING", 480),
        ("7", "09 IMPLEMENTATION", 491),
        ("8", "09 | IMPLEMENTATION", 492),
        ("9", "APPENDICES", 501),
    )
    sections = [_section("root", None, None, None, None, 1)]
    content = []
    for sequence, (suffix, text, page) in enumerate(headings, start=1):
        section_id = f"section-{suffix}"
        block_id = f"block-{suffix}"
        sections.append(
            _section(section_id, suffix * 64, block_id, "root", 3, sequence + 1, (block_id,))
        )
        content.append(
            _content(
                block_id,
                suffix * 64,
                section_id,
                sequence,
                "heading_owner",
                text=text,
                page=page,
            )
        )
    topology = _heading_topologies_from_records(sections, content)
    decisions = tuple(
        classify_repeated_heading_group(
            (topology[index], topology[index + 1]),
            toc_evidence=(TocHeadingEvidence((f"toc-{index}",), topology[index + 1].raw_text),),
            following_sibling=topology[index + 2],
        )
        for index in (0, 2, 4, 6)
    )
    assert [item.status for item in decisions] == ["eligible"] * 4
    once = project_repeated_heading_decisions(sections, content, decisions)
    twice = project_repeated_heading_decisions(once.sections, once.content, decisions)
    assert [item["id"] for item in once.content] == [item["id"] for item in content]
    assert len(once.sections) == len(sections) - 4
    assert twice.sections == once.sections
    assert twice.content == once.content
    tampered = replace(decisions[2], following_boundary_content_order=999)
    with pytest.raises(StructureContractError, match="following boundary changed"):
        project_repeated_heading_decisions(sections, content, (*decisions[:2], tampered))


def _eligible_decision() -> RepeatedHeadingDecision:
    divider, opening, _ = _observed_group("06")
    following = _heading("3", "07 | INFRASTRUCTURE", 452, 663, sibling_index=2)
    decision = classify_repeated_heading_group(
        (divider, opening),
        toc_evidence=(TocHeadingEvidence(("toc",), opening.raw_text),),
        following_sibling=following,
    )
    return replace(
        decision,
        heading_content_orders=(),
        source_content_order_extents=(),
        following_boundary_content_order=None,
        schema_version="er_commons.recovery.chapter_decision.v1",
        rule_version="repeated_chapter_divider_opening_v1",
        extent_basis="anchor_through_before_following_same_level_sibling",
    )


def test_projection_preserves_both_blocks_content_children_paths_and_order() -> None:
    decision = _eligible_decision()
    anchor_key, absorbed_key = decision.heading_stable_keys
    decision = replace(
        decision,
        ordered_child_refs=(
            ("block-1", "divider-body"),
            ("block-2", "opening-body", "child"),
        ),
        source_page_extents=((311, 311), (312, 312)),
    )
    sections = [
        _section("root", None, None, None, None, 1),
        _section(
            "section-1",
            anchor_key,
            "block-1",
            "root",
            3,
            2,
            ("block-1", "divider-body"),
        ),
        _section(
            "section-2",
            absorbed_key,
            "block-2",
            "root",
            3,
            3,
            ("block-2", "opening-body", "child"),
        ),
        _section("child", "c" * 64, "block-child", "section-2", 4, 4, ("block-child",)),
        _section("section-3", "3" * 64, "block-3", "root", 3, 5, ("block-3",)),
    ]
    content = [
        _content(
            "block-1", anchor_key, "section-1", 1, "heading_owner", text="06 CIRCULATION", page=311
        ),
        _content("divider-body", "d" * 64, "section-1", 2, "direct_body", page=311),
        _content(
            "block-2",
            absorbed_key,
            "section-2",
            3,
            "heading_owner",
            text="06 | CIRCULATION",
            page=312,
        ),
        _content("opening-body", "e" * 64, "section-2", 4, "direct_body", page=312),
        _content("block-child", "c" * 64, "child", 5, "heading_owner", page=312),
        _content(
            "block-3",
            "3" * 64,
            "section-3",
            6,
            "heading_owner",
            text="07 | INFRASTRUCTURE",
            page=452,
        ),
    ]

    projected = project_repeated_heading_decisions(sections, content, (decision,))

    assert [item["id"] for item in projected.content] == [item["id"] for item in content]
    assert "section-2" not in {item["id"] for item in projected.sections}
    assert next(item for item in projected.content if item["id"] == "block-2") == {
        **content[2],
        "section_id": "section-1",
        "semantic_placement": "direct_body",
    }
    child = next(item for item in projected.sections if item["id"] == "child")
    assert child["parent_section_id"] == "section-1"
    assert child["section_path_ids"] == ["root", "section-1", "child"]
    anchor = next(item for item in projected.sections if item["id"] == "section-1")
    assert anchor["ordered_child_ids"] == [
        "block-1",
        "divider-body",
        "block-2",
        "opening-body",
        "child",
    ]
    assert projected.section_target_redirects == {"section-2": "section-1"}
    correspondence = build_repeated_heading_correspondence(decision, projected)
    assert correspondence["old_targets"] == [
        {"section_id": "section-1", "role": "retained_anchor"},
        {"section_id": "section-2", "role": "absorbed_duplicate"},
    ]
    assert correspondence["retained_heading_block_ids"] == ["block-1", "block-2"]
    assert correspondence["content_record_ids_unique"] is True


def test_projection_is_idempotent_and_never_cascades_into_a_third_heading() -> None:
    decision = _eligible_decision()
    anchor_key, absorbed_key = decision.heading_stable_keys
    decision = replace(
        decision,
        ordered_child_refs=(("block-1",), ("block-2",)),
        source_page_extents=((311, 311), (312, 312)),
    )
    sections = [
        _section("root", None, None, None, None, 1),
        _section("section-1", anchor_key, "block-1", "root", 3, 2, ("block-1",)),
        _section("section-2", absorbed_key, "block-2", "root", 3, 3, ("block-2",)),
        _section("section-3", "3" * 64, "block-3", "root", 3, 4, ("block-3",)),
    ]
    content = [
        _content(
            "block-1", anchor_key, "section-1", 1, "heading_owner", text="06 CIRCULATION", page=311
        ),
        _content(
            "block-2",
            absorbed_key,
            "section-2",
            2,
            "heading_owner",
            text="06 | CIRCULATION",
            page=312,
        ),
        _content(
            "block-3",
            "3" * 64,
            "section-3",
            3,
            "heading_owner",
            text="07 | INFRASTRUCTURE",
            page=452,
        ),
    ]
    once = project_repeated_heading_decisions(sections, content, (decision,))
    twice = project_repeated_heading_decisions(once.sections, once.content, (decision,))
    assert twice.sections == once.sections
    assert twice.content == once.content
    assert any(item["id"] == "section-3" for item in twice.sections)


@pytest.mark.parametrize(
    ("target", "field", "value", "message"),
    [
        ("content", "canonical_text", "06 | TRANSIT", "frozen evidence"),
        ("content", "semantic_placement", "heading_owner", "frozen evidence"),
        ("boundary", "parent_section_id", "other-root", "following boundary"),
        ("boundary_content", "canonical_text", "07 | TRANSIT", "following boundary"),
    ],
)
def test_reapplication_revalidates_absorbed_heading_and_following_boundary(
    target: str, field: str, value: str, message: str
) -> None:
    decision = replace(
        _eligible_decision(),
        ordered_child_refs=(("block-1",), ("block-2",)),
        source_page_extents=((311, 311), (312, 312)),
    )
    sections = [
        _section("root", None, None, None, None, 1),
        _section(
            "section-1",
            decision.heading_stable_keys[0],
            "block-1",
            "root",
            3,
            2,
            ("block-1",),
        ),
        _section(
            "section-2",
            decision.heading_stable_keys[1],
            "block-2",
            "root",
            3,
            3,
            ("block-2",),
        ),
        _section("section-3", "3" * 64, "block-3", "root", 3, 4, ("block-3",)),
    ]
    content = [
        _content(
            "block-1",
            decision.heading_stable_keys[0],
            "section-1",
            1,
            "heading_owner",
            text="06 CIRCULATION",
            page=311,
        ),
        _content(
            "block-2",
            decision.heading_stable_keys[1],
            "section-2",
            2,
            "heading_owner",
            text="06 | CIRCULATION",
            page=312,
        ),
        _content(
            "block-3",
            "3" * 64,
            "section-3",
            3,
            "heading_owner",
            text="07 | INFRASTRUCTURE",
            page=452,
        ),
    ]
    once = project_repeated_heading_decisions(sections, content, (decision,))
    changed_sections = [dict(item) for item in once.sections]
    changed_content = [dict(item) for item in once.content]
    if target == "content":
        next(item for item in changed_content if item["id"] == "block-2")[field] = value
    elif target == "boundary_content":
        next(item for item in changed_content if item["id"] == "block-3")[field] = value
    else:
        next(item for item in changed_sections if item["id"] == "section-3")[field] = value
    with pytest.raises(StructureContractError, match=message):
        project_repeated_heading_decisions(changed_sections, changed_content, (decision,))


def test_projection_and_correspondence_reject_extent_reaching_boundary() -> None:
    decision = replace(_eligible_decision(), source_page_extents=((311, 311), (312, 500)))
    with pytest.raises(StructureContractError, match="extent reaches"):
        project_repeated_heading_decisions([], [], (decision,))
    empty_projection = project_repeated_heading_decisions([], [], ())
    with pytest.raises(StructureContractError, match="extent reaches"):
        build_repeated_heading_correspondence(decision, empty_projection)


def test_aliases_keep_both_spellings_but_one_logical_target() -> None:
    decision = _eligible_decision()
    anchor_key, absorbed_key = decision.heading_stable_keys
    decision = replace(
        decision,
        ordered_child_refs=(("block-1",), ("block-2",)),
        source_page_extents=((311, 311), (312, 312)),
    )
    sections = [
        _section("root", None, None, None, None, 1),
        _section("section-1", anchor_key, "block-1", "root", 3, 2, ("block-1",)),
        _section("section-2", absorbed_key, "block-2", "root", 3, 3, ("block-2",)),
        _section("section-3", "3" * 64, "block-3", "root", 3, 4, ("block-3",)),
    ]
    content = [
        _content(
            "block-1", anchor_key, "section-1", 1, "heading_owner", text="06 CIRCULATION", page=311
        ),
        _content(
            "block-2",
            absorbed_key,
            "section-2",
            2,
            "heading_owner",
            text="06 | CIRCULATION",
            page=312,
        ),
        _content(
            "block-3",
            "3" * 64,
            "section-3",
            3,
            "heading_owner",
            text="07 | INFRASTRUCTURE",
            page=452,
        ),
    ]
    projection = project_repeated_heading_decisions(sections, content, (decision,))
    seeds = [
        AliasSeed("section", "06 CIRCULATION", "section-1", "section", 1, "heading_text", REF),
        AliasSeed("section", "06 | CIRCULATION", "section-2", "section", 2, "heading_text", REF),
    ]
    redirected = redirect_repeated_heading_alias_seeds(seeds, projection)
    assert [item.raw_value for item in redirected] == ["06 CIRCULATION", "06 | CIRCULATION"]
    assert {item.target_id for item in redirected} == {"section-1"}


def test_exact_toc_alias_to_absorbed_heading_redirects_to_logical_target(
    tmp_path: Path,
) -> None:
    hierarchy_root = tmp_path / "hierarchy"
    baseline_root = tmp_path / "baseline"
    (hierarchy_root / "artifacts").mkdir(parents=True)
    (baseline_root / "canonical").mkdir(parents=True)
    for relative in (
        "artifacts/decisions.jsonl",
        "artifacts/item_features.jsonl",
        "artifacts/toc_reconciliation.jsonl",
    ):
        (hierarchy_root / relative).write_text("")
    (baseline_root / "canonical/documents.jsonl").write_text("")
    anchor_key, absorbed_key = _eligible_decision().heading_stable_keys
    target_id = "candidate/section/chapter-06"
    evidence = ProducerEvidence(
        baseline_document={},
        hierarchy_document={},
        item_features=[
            {"stable_item_key": anchor_key, "text": "06 CIRCULATION"},
            {"stable_item_key": absorbed_key, "text": "06 | CIRCULATION"},
        ],
        decisions=[],
        hierarchy={},
        visible_toc_entries=[
            {"toc_entry_id": "toc-06", "title_with_marker_normalized": "06 Circulation"}
        ],
        toc_reconciliations=[
            {"toc_entry_id": "toc-06", "state": "exact", "target_key": absorbed_key}
        ],
        baseline_key_by_pointer={},
        hierarchy_key_by_pointer={},
    )
    seeds = build_appendix_p_alias_seeds(
        collections={
            "documents": [{"id": "document", "title": "Appendix A"}],
            "blocks": [
                {
                    "stable_item_key": anchor_key,
                    "canonical_text": "06 CIRCULATION",
                    "sequence": 1,
                },
                {
                    "stable_item_key": absorbed_key,
                    "canonical_text": "06 | CIRCULATION",
                    "sequence": 2,
                },
            ],
            "pages": [],
        },
        sections=[
            {
                "source_stable_item_key": anchor_key,
                "section_kind": "semantic",
                "id": target_id,
            }
        ],
        evidence=evidence,
        page_labels=[],
        hierarchy_root=hierarchy_root,
        baseline_root=baseline_root,
        heading_target_redirects={absorbed_key: target_id},
    )
    toc_seed = next(item for item in seeds if item.evidence_kind == "visible_toc_reconciliation")
    assert toc_seed.target_id == target_id


def test_projection_rejects_missing_changed_or_overlapping_decisions() -> None:
    decision = _eligible_decision()
    anchor_key, absorbed_key = decision.heading_stable_keys
    sections = [
        _section("root", None, None, None, None, 1),
        _section("section-1", anchor_key, "block-1", "root", 3, 2, ("block-1",)),
        _section("section-2", absorbed_key, "block-2", "root", 4, 3, ("block-2",)),
        _section("section-3", "3" * 64, "block-3", "root", 3, 4, ("block-3",)),
    ]
    content = [
        _content(
            "block-1", anchor_key, "section-1", 1, "heading_owner", text="06 CIRCULATION", page=311
        ),
        _content(
            "block-2",
            absorbed_key,
            "section-2",
            2,
            "heading_owner",
            text="06 | CIRCULATION",
            page=312,
        ),
        _content(
            "block-3",
            "3" * 64,
            "section-3",
            3,
            "heading_owner",
            text="07 | INFRASTRUCTURE",
            page=452,
        ),
    ]
    with pytest.raises(StructureContractError, match="topology changed"):
        project_repeated_heading_decisions(sections, content, (decision,))
    valid_decision = replace(
        decision,
        ordered_child_refs=(("block-1",), ("block-2",)),
        source_page_extents=((311, 311), (312, 312)),
    )
    with pytest.raises(StructureContractError, match="overlap"):
        project_repeated_heading_decisions(
            [replace_section(item, semantic_level=3) for item in sections],
            content,
            (valid_decision, valid_decision),
        )


def test_projection_correspondence_survives_candidate_namespace_change() -> None:
    decision = replace(
        _eligible_decision(),
        ordered_child_refs=(("block-1",), ("block-2",)),
        source_page_extents=((311, 311), (312, 312)),
    )
    prefix = "exv1-new/"
    sections = [
        _section(f"{prefix}root", None, None, None, None, 1),
        _section(
            f"{prefix}section-1",
            decision.heading_stable_keys[0],
            f"{prefix}block-1",
            f"{prefix}root",
            3,
            2,
            (f"{prefix}block-1",),
        ),
        _section(
            f"{prefix}section-2",
            decision.heading_stable_keys[1],
            f"{prefix}block-2",
            f"{prefix}root",
            3,
            3,
            (f"{prefix}block-2",),
        ),
        _section(
            f"{prefix}section-3",
            "3" * 64,
            f"{prefix}block-3",
            f"{prefix}root",
            3,
            4,
            (f"{prefix}block-3",),
        ),
    ]
    content = [
        _content(
            f"{prefix}block-1",
            decision.heading_stable_keys[0],
            f"{prefix}section-1",
            1,
            "heading_owner",
            text="06 CIRCULATION",
            page=311,
        ),
        _content(
            f"{prefix}block-2",
            decision.heading_stable_keys[1],
            f"{prefix}section-2",
            2,
            "heading_owner",
            text="06 | CIRCULATION",
            page=312,
        ),
        _content(
            f"{prefix}block-3",
            "3" * 64,
            f"{prefix}section-3",
            3,
            "heading_owner",
            text="07 | INFRASTRUCTURE",
            page=452,
        ),
    ]
    projection = project_repeated_heading_decisions(sections, content, (decision,))
    correspondence = build_repeated_heading_correspondence(decision, projection)
    assert correspondence["new_target"]["section_id"] == f"{prefix}section-1"


def test_projection_rejects_changed_frozen_text_and_missing_child_reference() -> None:
    decision = replace(
        _eligible_decision(),
        ordered_child_refs=(("block-1",), ("block-2",)),
        source_page_extents=((311, 311), (312, 312)),
    )
    sections = [
        _section("root", None, None, None, None, 1),
        _section(
            "section-1",
            decision.heading_stable_keys[0],
            "block-1",
            "root",
            3,
            2,
            ("block-1",),
        ),
        _section(
            "section-2",
            decision.heading_stable_keys[1],
            "block-2",
            "root",
            3,
            3,
            ("block-2",),
        ),
        _section("section-3", "3" * 64, "block-3", "root", 3, 4, ("block-3",)),
    ]
    content = [
        _content(
            "block-1",
            decision.heading_stable_keys[0],
            "section-1",
            1,
            "heading_owner",
            text="06 CIRCULATION",
            page=311,
        ),
        _content(
            "block-2",
            decision.heading_stable_keys[1],
            "section-2",
            2,
            "heading_owner",
            text="06 | CIRCULATION",
            page=312,
        ),
        _content(
            "block-3",
            "3" * 64,
            "section-3",
            3,
            "heading_owner",
            text="07 | INFRASTRUCTURE",
            page=452,
        ),
    ]
    changed = [dict(item) for item in content]
    changed[1]["canonical_text"] = "06 | TRANSIT"
    with pytest.raises(StructureContractError, match="topology changed"):
        project_repeated_heading_decisions(sections, changed, (decision,))
    missing = [dict(item) for item in sections]
    missing[2]["ordered_child_ids"] = ["block-2", "missing-child"]
    with pytest.raises(StructureContractError, match="missing or foreign"):
        project_repeated_heading_decisions(missing, content, (decision,))
    changed_boundary = [dict(item) for item in sections]
    changed_boundary[3]["parent_section_id"] = "other-root"
    with pytest.raises(StructureContractError, match="following boundary changed"):
        project_repeated_heading_decisions(changed_boundary, content, (decision,))
    changed_boundary_text = [dict(item) for item in content]
    changed_boundary_text[2]["canonical_text"] = "07 | TRANSIT"
    with pytest.raises(StructureContractError, match="following boundary changed"):
        project_repeated_heading_decisions(sections, changed_boundary_text, (decision,))
    changed_boundary_key = [dict(item) for item in sections]
    changed_boundary_key[3]["source_stable_item_key"] = "4" * 64
    with pytest.raises(StructureContractError, match="following boundary changed"):
        project_repeated_heading_decisions(changed_boundary_key, content, (decision,))
    with pytest.raises(StructureContractError, match="parsed identity changed"):
        project_repeated_heading_decisions(
            sections, content, (replace(decision, chapter_title="transit"),)
        )


def test_qualification_is_completion_last_closed_and_no_clobber(tmp_path: Path) -> None:
    eligible = _eligible_decision()
    divider_08, opening_08, following_09 = _observed_group("08")
    rejected = classify_repeated_heading_group(
        (divider_08, replace(opening_08, raw_text=divider_08.raw_text)),
        toc_evidence=(TocHeadingEvidence(("toc-08",), opening_08.raw_text),),
        following_sibling=following_09,
    )
    rejected = replace(
        rejected,
        heading_content_orders=(),
        source_content_order_extents=(),
        following_boundary_content_order=None,
        schema_version="er_commons.recovery.chapter_decision.v1",
        rule_version="repeated_chapter_divider_opening_v1",
        extent_basis="anchor_through_before_following_same_level_sibling",
    )
    output = tmp_path / "qualification-v1"
    source_ref = {
        "authority": "task06a_packet",
        "relative_path": "pipelines/recovery/appendix_a_topology.v1.json",
        "identity": "packet-inventory-83c31433",
        "verification_mode": "selected_record_read",
    }
    completion = publish_repeated_heading_qualification(
        output,
        decisions=(eligible, rejected),
        source_ref=source_ref,
        policy_ref={"path": "docs/specs/repeated_heading_repair_v1.md", "sha256": "a" * 64},
        schema_ref={
            "path": (
                "benchmarks/er_bench/schemas/task06_recovery/v1/"
                "repeated_heading_decision.schema.json"
            ),
            "sha256": "b" * 64,
        },
        decision_schema=SCHEMA,
        limitations=("physical TOC destination unresolved",),
    )
    assert completion.is_file()
    assert json.loads((output / "qualification.json").read_text())["counts"] == {
        "eligible": 1,
        "rejected": 1,
        "review_required": 0,
    }
    assert len((output / "eligible_decisions.jsonl").read_text().splitlines()) == 1
    all_records = [
        json.loads(line) for line in (output / "all_decisions.jsonl").read_text().splitlines()
    ]
    rejected_record = next(item for item in all_records if item["status"] == "rejected")
    assert rejected_record["heading_raw_texts"] == [
        "08 PUBLIC FACILITIES FINANCING",
        "08 PUBLIC FACILITIES FINANCING",
    ]
    with pytest.raises(FileExistsError, match="already exists"):
        publish_repeated_heading_qualification(
            output,
            decisions=(eligible,),
            source_ref=source_ref,
            policy_ref={},
            schema_ref={},
            decision_schema=SCHEMA,
        )


def test_qualification_loader_verifies_packet_closure_and_seals(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    data_root = tmp_path / "data"
    policy_relative = Path("docs/specs/repeated_heading_repair_v1.md")
    schema_relative = Path(
        "benchmarks/er_bench/schemas/task06_recovery/v1/repeated_heading_decision.schema.json"
    )
    policy_path = project_root / policy_relative
    schema_path = project_root / schema_relative
    policy_path.parent.mkdir(parents=True)
    schema_path.parent.mkdir(parents=True)
    policy_path.write_text("policy\n")
    schema_path.write_text(json.dumps(SCHEMA))
    qualification_relative = Path("pipelines/recovery/06d/qualification")
    config_value = json.loads(
        (ROOT / "configs/brisbane_baylands_2025_deir_task03e4_semantic_v1.json").read_text()
    )
    config_value.update(
        {
            "schema_version": "2.0.0",
            "repeated_heading_policy_relative_path": policy_relative.as_posix(),
            "repeated_heading_qualification_relative_root": qualification_relative.as_posix(),
            "repeated_heading_decision_schema_relative_path": schema_relative.as_posix(),
        }
    )
    config = DocumentStructureConfig.model_validate(config_value)
    source_ref = {
        "authority": "task06a_packet",
        "relative_path": "pipelines/recovery/appendix_a_topology.v1.json",
        "identity": "packet-inventory-83c31433",
        "verification_mode": "selected_record_read",
    }
    publish_repeated_heading_qualification(
        data_root / qualification_relative,
        decisions=(_eligible_decision(),),
        source_ref=source_ref,
        policy_ref={"path": policy_relative.as_posix(), "sha256": _sha256(policy_path)},
        schema_ref={"path": schema_relative.as_posix(), "sha256": _sha256(schema_path)},
        decision_schema=SCHEMA,
    )
    refs, decisions = _load_repeated_heading_decisions(
        data_root=data_root, project_root=project_root, config=config
    )
    assert set(refs) == {"decisions", "completion", "inventory", "qualification"}
    assert len(decisions) == 1
    inventory = data_root / qualification_relative / "inventory.json"
    inventory.write_text(inventory.read_text() + " ")
    with pytest.raises(Exception, match="completion seals its inventory"):
        _load_repeated_heading_decisions(
            data_root=data_root, project_root=project_root, config=config
        )


def test_qualification_consumer_rejects_pending_review_and_subset_drift() -> None:
    source_ref = {
        "authority": "task06a_packet",
        "relative_path": "pipelines/recovery/appendix_a_topology.v1.json",
        "identity": "packet-inventory-83c31433",
        "verification_mode": "selected_record_read",
    }
    eligible = _eligible_decision().as_record(
        source_ref=source_ref,
        new_target_ref={
            "authority": "task06d_policy",
            "relative_path": "logical-targets/06",
            "identity": "logical-chapter-06",
            "verification_mode": "pending_06g_materialization",
        },
    )
    review = {
        **eligible,
        "status": "review_required",
        "anchor_heading_key": None,
        "absorbed_heading_key": None,
        "new_target_ref": None,
    }
    completion = {"eligible_decision_count": 1}
    qualification = {
        "source_ref": source_ref,
        "counts": {"eligible": 1, "rejected": 0, "review_required": 1},
    }
    with pytest.raises(DocumentStructureInvariantError, match="no pending human review"):
        _verify_repeated_heading_records(
            Path("eligible.jsonl"), [eligible], [eligible, review], completion, qualification
        )
    qualification["counts"] = {"eligible": 1, "rejected": 0, "review_required": 0}
    with pytest.raises(DocumentStructureInvariantError, match="counts match"):
        _verify_repeated_heading_records(
            Path("eligible.jsonl"), [eligible], [eligible, review], completion, qualification
        )


def replace_section(section: dict[str, object], **changes: object) -> dict[str, object]:
    """Return a shallow test-only section mutation."""
    return {**section, **changes}


def _sha256(path: Path) -> str:
    """Return a test-only SHA-256 for compact policy inputs."""
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()
