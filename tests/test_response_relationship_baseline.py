"""Source-free behavior tests for the Task 05E exact-only baseline."""

from __future__ import annotations

from typing import Any

import pytest

from er_commons.response_inventory.relationship_baseline import (
    _build_records,
    _classify_nonmatch,
    _classify_structural_mention,
    _relation_type,
    _ResolutionPolicy,
    _resolve_membership_target,
    _resolve_mention_target,
    _review_views,
    _strongly_connected_components,
)

type JsonObject = dict[str, Any]


def _typed(prefix: str, value: str) -> str:
    return f"{prefix}v1-{value * 64}"


def _marker(value: str, label: str) -> JsonObject:
    return {
        "record_type": "marker_candidate",
        "marker_id": _typed("marker", value),
        "observed_label": label,
    }


def _unit(value: str, kind: str, label: str, marker_value: str) -> JsonObject:
    return {
        "record_type": "source_unit",
        "unit_id": _typed("unit", value),
        "unit_kind": kind,
        "official_label": label,
        "start_marker_id": _typed("marker", marker_value),
        "span_ids": [_typed("span", value)],
    }


def _activity() -> JsonObject:
    return {"activity_id": _typed("activity", "a")}


def test_nonmatch_census_does_not_promote_variants() -> None:
    labels: dict[str, JsonObject] = {
        "Response X-1": {},
        "Response X-2a": {},
        "GENERAL RESPONSE 1": {},
    }
    assert _classify_nonmatch("Response \r\nX-1", labels) == "whitespace_variant"
    assert _classify_nonmatch("Response X-1.", labels) == "punctuation_variant"
    assert _classify_nonmatch("Response X-2", labels) == "parent_subanswer_candidate"
    assert _classify_nonmatch("Response X-1 to X-3", labels) == "range_like"
    assert _classify_nonmatch("response is", labels) == "prose_like"
    assert _classify_nonmatch("General Response 1", labels) == "case_variant"
    assert _classify_nonmatch("General \r\nResponse 1", labels) == "whitespace_case_variant"
    assert _classify_nonmatch("response times", labels) == "other_nonexact"


def test_relation_type_is_closed_to_the_accepted_v1_graph() -> None:
    assert _relation_type("comment", "response") == "comment_response"
    assert _relation_type("response", "response") == "response_response"
    assert _relation_type("response", "general_response") == "response_general_response"
    assert _relation_type("general_response", "comment") == "general_response_membership"
    assert _relation_type("comment", "general_response") is None
    assert _relation_type("general_response", "response") is None
    assert (
        _relation_type("general_response", "response", allow_general_response_response=True)
        == "general_response_response"
    )
    assert (
        _relation_type(
            "general_response",
            "general_response",
            allow_general_response_general_response=True,
        )
        == "general_response_general_response"
    )


def test_bounded_rules_resolve_case_whitespace_control_separator_and_membership_alias() -> None:
    labels: dict[str, JsonObject] = {
        "GENERAL RESPONSE 1": {"unit_id": "general"},
        "Response X-1": {"unit_id": "response-x"},
        "Response X-2": {"unit_id": "response-x-2"},
        "Response X-3": {"unit_id": "response-x-3"},
        "Response M-OSEC-173": {"unit_id": "response-173"},
        "Response M-OSEC-119": {"unit_id": "response-119"},
        "Comment M-OSEC-106": {"unit_id": "comment-106", "unit_kind": "comment"},
    }
    policy = _ResolutionPolicy(
        name="test",
        normalize_case=True,
        collapse_whitespace=True,
        recover_control_separator=True,
        classify_self_mentions=True,
        allow_general_response_response=True,
        strip_one_terminal_period=True,
        typed_memberships=True,
        membership_aliases={"O-OSEC-106": "M-OSEC-106"},
    )
    mention = {"mention_span_id": "span"}
    spans = {"span": {"fragments": [{"page_id": "page", "text_end": 10}]}}
    pages = {"page": {"raw_text": "Response M\x02OSEC-173"}}

    assert _resolve_mention_target("General Response 1", mention, labels, spans, pages, policy)[
        :2
    ] == ("GENERAL RESPONSE 1", labels["GENERAL RESPONSE 1"])
    assert _resolve_mention_target("Response \r\nX-1", mention, labels, spans, pages, policy)[
        :2
    ] == ("Response X-1", labels["Response X-1"])
    assert _resolve_mention_target("Response M", mention, labels, spans, pages, policy)[:2] == (
        "Response M-OSEC-173",
        labels["Response M-OSEC-173"],
    )
    assert _resolve_mention_target("Response X-2.", mention, labels, spans, pages, policy)[:2] == (
        "Response X-2",
        labels["Response X-2"],
    )
    combined = _resolve_mention_target("response \r\nX-3.", mention, labels, spans, pages, policy)
    assert combined[:2] == ("Response X-3", labels["Response X-3"])
    assert combined[2] == "collapsed_whitespace_one_terminal_period_casefold_v1"
    lower_mention = {"mention_span_id": "lower-span"}
    lower_spans = {"lower-span": {"fragments": [{"page_id": "lower-page", "text_end": 10}]}}
    lower_pages = {"lower-page": {"raw_text": "response M\x02OSEC-119"}}
    assert _resolve_mention_target(
        "response M", lower_mention, labels, lower_spans, lower_pages, policy
    )[:2] == ("Response M-OSEC-119", labels["Response M-OSEC-119"])
    assert _resolve_membership_target("O-OSEC-106", labels, policy)[:2] == (
        "Comment M-OSEC-106",
        labels["Comment M-OSEC-106"],
    )


def test_reviewed_structural_and_ordinary_prose_classifications_are_bounded() -> None:
    running_text = (
        "Chapter 13. Responses to Comments\r\n"
        "13.2. General Responses to Comments Raised in Multiple Letters | "
        "13.2.2. General Response 2: Topic\r\nBody"
    )
    running_start = running_text.index("General Response 2")
    section_text = "b. Response\r\nGreenhouse Gas Mitigation Measures"
    section_start = section_text.index("Response")
    spans = {
        "running-span": {
            "fragments": [
                {
                    "page_id": "running-page",
                    "text_start": running_start,
                    "text_end": running_start + len("General Response 2"),
                }
            ]
        },
        "section-span": {
            "fragments": [
                {
                    "page_id": "section-page",
                    "text_start": section_start,
                    "text_end": section_start + len("Response\r\nGreenhouse"),
                }
            ]
        },
    }
    pages = {
        "running-page": {"raw_text": running_text},
        "section-page": {"raw_text": section_text},
    }
    policy = _ResolutionPolicy(
        name="test",
        classify_running_headers=True,
        classify_response_section_headings=True,
    )

    assert (
        _classify_structural_mention(
            "General Response 2",
            {"mention_span_id": "running-span"},
            spans,
            pages,
            policy,
        )[0]
        == "running_header"
    )
    assert (
        _classify_structural_mention(
            "Response\r\nGreenhouse",
            {"mention_span_id": "section-span"},
            spans,
            pages,
            policy,
        )[0]
        == "response_section_heading"
    )
    assert (
        _classify_nonmatch(
            "response vehicles",
            {},
            classify_ordinary_response_prose=True,
        )
        == "ordinary_prose"
    )
    assert (
        _classify_nonmatch(
            "response M",
            {},
            classify_ordinary_response_prose=True,
        )
        == "other_nonexact"
    )
    assert (
        _classify_nonmatch(
            "Response OSEC-21",
            {},
            terminal_unresolved_labels=frozenset({"Response OSEC-21"}),
        )
        == "reviewed_source_label_typo_unresolved"
    )


def test_reviewed_unpaired_source_form_remains_terminal_without_an_edge() -> None:
    records = [
        _marker("1", "Comment SA-Caltrans-48"),
        _marker("2", "Response SA-Caltrans-48a"),
        _unit("1", "comment", "Comment SA-Caltrans-48", "1"),
        _unit("2", "response", "Response SA-Caltrans-48a", "2"),
    ]
    policy = _ResolutionPolicy(
        name="test",
        terminal_unpaired_source_labels=frozenset(
            {"Comment SA-Caltrans-48", "Response SA-Caltrans-48a"}
        ),
    )

    built = _build_records(records, _activity(), policy=policy)

    assert built["edges"] == []
    assert {item["reason"] for item in built["direct_pair_outcomes"]} == {
        "reviewed_non_pair_source_form"
    }


def test_bounded_policy_classifies_case_normalized_self_mentions_without_edges() -> None:
    records = [
        _marker("1", "GENERAL RESPONSE 1"),
        _unit("1", "general_response", "GENERAL RESPONSE 1", "1"),
        {
            "record_type": "reference_mention",
            "mention_id": _typed("mention", "2"),
            "source_unit_id": _typed("unit", "1"),
            "mention_span_id": _typed("span", "2"),
            "target_labels": ["General Response 1"],
            "reference_domain": "intra_volume",
        },
    ]
    policy = _ResolutionPolicy(name="test", normalize_case=True, classify_self_mentions=True)

    built = _build_records(records, _activity(), policy=policy)

    assert built["edges"] == []
    assert built["mention_outcomes"][0]["reason"] == "self_mention"


def test_exact_builder_preserves_prose_and_parent_subanswer_nonmatches() -> None:
    records = [
        _marker("1", "Comment X-1"),
        _marker("2", "Response X-1"),
        _marker("3", "Comment X-2"),
        _marker("4", "Response X-2a"),
        _marker("5", "General Response 1"),
        _unit("1", "comment", "Comment X-1", "1"),
        _unit("2", "response", "Response X-1", "2"),
        _unit("3", "comment", "Comment X-2", "3"),
        _unit("4", "response", "Response X-2a", "4"),
        _unit("5", "general_response", "General Response 1", "5"),
        {
            "record_type": "reference_mention",
            "mention_id": _typed("mention", "6"),
            "source_unit_id": _typed("unit", "2"),
            "mention_span_id": _typed("span", "6"),
            "target_labels": ["General Response 1"],
            "reference_domain": "intra_volume",
        },
        {
            "record_type": "reference_mention",
            "mention_id": _typed("mention", "7"),
            "source_unit_id": _typed("unit", "2"),
            "mention_span_id": _typed("span", "7"),
            "target_labels": ["response is"],
            "reference_domain": "intra_volume",
        },
        {
            "record_type": "reference_mention",
            "mention_id": _typed("mention", "0"),
            "source_unit_id": _typed("unit", "2"),
            "mention_span_id": _typed("span", "0"),
            "target_labels": ["General Response 1"],
            "reference_domain": "intra_volume",
        },
        {
            "record_type": "membership_claim",
            "membership_id": _typed("membership", "8"),
            "general_response_unit_id": _typed("unit", "5"),
            "mention_span_id": _typed("span", "8"),
            "target_label": "Comment X-1",
        },
        {
            "record_type": "membership_claim",
            "membership_id": _typed("membership", "9"),
            "general_response_unit_id": _typed("unit", "5"),
            "mention_span_id": _typed("span", "9"),
            "target_label": "X-1",
        },
    ]
    built = _build_records(records, _activity())
    edges = built["edges"]
    assert {edge["relation_type"] for edge in edges} == {
        "comment_response",
        "response_general_response",
        "general_response_membership",
    }
    mention_outcomes = built["mention_outcomes"]
    assert [item["outcome"] for item in mention_outcomes].count("resolved") == 2
    assert any(item.get("reason") == "prose_like" for item in mention_outcomes)
    general_edge = next(
        edge for edge in edges if edge["relation_type"] == "response_general_response"
    )
    assert len(general_edge["evidence_ids"]) == 2
    direct_failures = {
        item["official_label"]
        for item in built["direct_pair_outcomes"]
        if item["outcome"] == "unresolved"
    }
    assert direct_failures == {"Comment X-2", "Response X-2a"}
    membership_outcomes = built["membership_outcomes"]
    assert [item["outcome"] for item in membership_outcomes].count("resolved") == 1
    assert any(item.get("reason") == "exact_comment_target_absent" for item in membership_outcomes)
    assert all(
        view["rendering_recipe"] == "source_text_with_accepted_overlays" for view in built["views"]
    )


def test_cycle_detection_is_deterministic() -> None:
    units: dict[str, JsonObject] = {
        _typed("unit", "1"): {},
        _typed("unit", "2"): {},
        _typed("unit", "3"): {},
    }
    adjacency = {
        _typed("unit", "1"): [_typed("unit", "2")],
        _typed("unit", "2"): [_typed("unit", "1")],
    }
    assert _strongly_connected_components(units, adjacency) == [
        [_typed("unit", "1"), _typed("unit", "2")],
        [_typed("unit", "3")],
    ]


def test_review_view_traverses_general_response_relationships() -> None:
    comment_id = _typed("unit", "1")
    response_id = _typed("unit", "2")
    general_id = _typed("unit", "3")
    linked_general_id = _typed("unit", "4")
    units = {
        comment_id: _unit("1", "comment", "Comment X-1", "1"),
        response_id: _unit("2", "response", "Response X-1", "2"),
        general_id: _unit("3", "general_response", "GENERAL RESPONSE 1", "3"),
        linked_general_id: _unit("4", "general_response", "GENERAL RESPONSE 2", "4"),
    }
    edges = [
        {
            "edge_id": _typed("edge", "1"),
            "relation_type": "comment_response",
            "source_unit_id": comment_id,
            "target_unit_id": response_id,
        },
        {
            "edge_id": _typed("edge", "2"),
            "relation_type": "general_response_membership",
            "source_unit_id": general_id,
            "target_unit_id": comment_id,
        },
        {
            "edge_id": _typed("edge", "3"),
            "relation_type": "general_response_general_response",
            "source_unit_id": general_id,
            "target_unit_id": linked_general_id,
        },
    ]

    view = _review_views(units, edges, _activity())[0]

    assert linked_general_id in view["ordered_unit_ids"]
    assert _typed("edge", "3") in view["edge_ids"]


def test_exact_builder_rejects_multi_target_mentions() -> None:
    records = [
        _marker("1", "Comment X-1"),
        _marker("2", "Response X-1"),
        _unit("1", "comment", "Comment X-1", "1"),
        _unit("2", "response", "Response X-1", "2"),
        {
            "record_type": "reference_mention",
            "mention_id": _typed("mention", "3"),
            "source_unit_id": _typed("unit", "2"),
            "mention_span_id": _typed("span", "3"),
            "target_labels": ["Response X-1", "Response X-2"],
            "reference_domain": "intra_volume",
        },
    ]
    with pytest.raises(ValueError, match="exactly one target occurrence"):
        _build_records(records, _activity())


def test_exact_builder_rejects_duplicate_or_marker_divergent_labels() -> None:
    duplicate = [
        _marker("1", "Comment X-1"),
        _marker("2", "Comment X-1"),
        _unit("1", "comment", "Comment X-1", "1"),
        _unit("2", "comment", "Comment X-1", "2"),
    ]
    with pytest.raises(ValueError, match="official label is not unique"):
        _build_records(duplicate, _activity())

    divergent = [
        _marker("1", "Comment X-2"),
        _unit("1", "comment", "Comment X-1", "1"),
    ]
    with pytest.raises(ValueError, match="differs from its start marker"):
        _build_records(divergent, _activity())
