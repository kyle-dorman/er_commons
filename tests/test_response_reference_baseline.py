"""Focused source-free tests for Task 05F exact reference resolution."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.artifact_io import canonical_json_sha256
from er_commons.document_records.document_structure.normalization import normalize_alias
from er_commons.response_inventory.reference_baseline import (
    _indexes,
    _MentionContext,
    _publish_candidate,
    _ResolutionResources,
    _resolve_reference,
    _sha256_small,
    _target_indexes,
    _validate_acceptance,
    map_task04a_usability,
    map_visual_usability,
)

type JsonObject = dict[str, Any]


@dataclass(frozen=True)
class _ResolveOptions:
    """Optional test inputs for one reference-resolution example."""

    source_kind: str = "response"
    catalog_aliases: dict[str, set[str]] = field(default_factory=dict)
    catalog_designators: dict[str, set[str]] = field(default_factory=dict)
    context: _MentionContext = _MentionContext()
    direct_section_children: dict[str, tuple[str, ...]] | None = None


def _id(prefix: str, character: str) -> str:
    return f"{prefix}v1-{character * 64}"


def _mention(label: str, *, domain: str = "draft_eir") -> JsonObject:
    return {
        "mention_id": _id("mention", "a"),
        "mention_span_id": _id("span", "b"),
        "source_unit_id": _id("unit", "c"),
        "raw_text_sha256": "d" * 64,
        "reference_domain": domain,
        "target_labels": [label],
    }


def _source(kind: str = "response") -> JsonObject:
    return {"unit_kind": kind}


def _row(
    label: str,
    source_id: str,
    target_type: str,
    target_character: str,
) -> JsonObject:
    return {
        "lookup_key": normalize_alias(label),
        "source_id": source_id,
        "target_type": target_type,
        "target_id": f"target-{target_character * 64}",
    }


def _activity() -> JsonObject:
    return {
        "activity_id": _id("activity", "e"),
        "input_refs": [
            {"role": "task04a_registry", "identity": "reviewv1-test"},
            {"role": "task04d_handoff", "identity": "handoffv1-test"},
        ],
    }


def _registry(*source_ids: str) -> dict[str, JsonObject]:
    return {
        source_id: {
            "entry_id": f"usabilityv1-{source_id}",
            "source_id": source_id,
            "status": "eligible",
        }
        for source_id in source_ids
    }


def _resolve(
    label: str,
    rows: list[JsonObject],
    *,
    options: _ResolveOptions | None = None,
) -> tuple[JsonObject, JsonObject | None]:
    selected = options or _ResolveOptions()
    return _resolve_reference(
        _mention(label),
        _source(selected.source_kind),
        _ResolutionResources(
            indexes=_target_indexes(rows, selected.direct_section_children),
            catalog_aliases=selected.catalog_aliases,
            catalog_designators=selected.catalog_designators,
            registry=_registry(
                "deir_main",
                "deir_appendix_n1",
                "deir_appendix_n2",
                "deir_appendix_d",
            ),
            activity=_activity(),
        ),
        selected.context,
    )


def test_exact_alias_only_outside_routed_source_is_a_negative_control() -> None:
    outcome, link = _resolve(
        "Draft EIR Chapter 8",
        [_row("Chapter 8", "deir_appendix_e", "section", "1")],
    )
    assert link is None
    assert outcome["terminal_reason"] == "exact_alias_only_outside_routed_source"
    assert outcome["global_candidate_target_ids"]
    assert outcome["source_candidate_target_ids"] == []


def test_unique_leading_chapter_identifier_resolves_only_in_routed_source() -> None:
    intended = _row(
        "Chapter 2 General Environmental and Planning Context",
        "deir_main",
        "section",
        "2",
    )
    unrelated = _row("Chapter 2", "deir_appendix_e", "section", "3")
    numbered_section = _row("2 Project Description", "deir_main", "section", "4")
    outcome, link = _resolve(
        "Draft EIR Chapter 2",
        [unrelated, numbered_section, intended],
    )

    assert link is not None
    assert link["target_id"] == intended["target_id"]
    assert link["resolver_rule"] == "task05f_leading_identifier_exact_v1"
    assert outcome["global_candidate_target_ids"] == [intended["target_id"]]
    assert outcome["source_candidate_target_ids"] == [intended["target_id"]]


def test_leading_chapter_identifier_does_not_substitute_first_subsection() -> None:
    subsection = _row("8.1 Introduction", "deir_main", "section", "1")
    unrelated = _row("Chapter 8", "deir_appendix_e", "section", "2")
    outcome, link = _resolve("Draft EIR Chapter 8", [subsection, unrelated])

    assert link is None
    assert outcome["terminal_reason"] == "exact_alias_only_outside_routed_source"
    assert outcome["compatible_target_ids"] == []


def test_cardinality_deduplicates_alias_rows_by_target_id() -> None:
    row = _row("Chapter 3", "deir_main", "section", "1")
    outcome, link = _resolve("Draft EIR Chapter 3", [row, dict(row)])
    assert link is not None
    assert outcome["outcome"] == "resolved"
    assert outcome["compatible_target_ids"] == [row["target_id"]]


def test_true_collision_and_type_conflict_remain_separate() -> None:
    first = _row("Chapter 3", "deir_main", "section", "1")
    second = _row("Chapter 3", "deir_main", "section", "2")
    collision, collision_link = _resolve("Draft EIR Chapter 3", [second, first, dict(first)])
    assert collision_link is None
    assert collision["terminal_reason"] == "exact_target_collision"
    assert collision["compatible_target_ids"] == sorted({first["target_id"], second["target_id"]})

    conflict, conflict_link = _resolve(
        "Draft EIR Table 3-1",
        [_row("Table 3-1", "deir_main", "section", "3")],
    )
    assert conflict_link is None
    assert conflict["terminal_reason"] == "target_type_incompatible"


def test_appendix_routing_uses_only_catalog_aliases() -> None:
    row = _row("Appendix N1", "deir_appendix_n1", "document", "1")
    aliases = {normalize_alias("Appendix N1"): {"deir_appendix_n1"}}
    options = _ResolveOptions(catalog_aliases=aliases)
    outcome, link = _resolve("Draft EIR Appendix N1", [row], options=options)
    assert link is not None
    assert outcome["routed_source_ids"] == ["deir_appendix_n1"]

    dotted, dotted_link = _resolve("Draft EIR Appendix N.1", [row], options=options)
    assert dotted_link is None
    assert dotted["terminal_reason"] == "appendix_source_route_absent"


def test_structured_appendix_punctuation_normalization_is_unique_and_fail_closed() -> None:
    row = _row(
        "Appendix N2 - Fire Protection Services Plan",
        "deir_appendix_n2",
        "document",
        "2",
    )
    outcome, link = _resolve(
        "Draft EIR Appendix N.2",
        [row],
        options=_ResolveOptions(catalog_designators={"appendix:n:2": {"deir_appendix_n2"}}),
    )
    assert link is not None
    assert outcome["routed_source_ids"] == ["deir_appendix_n2"]

    absent, absent_link = _resolve(
        "Draft EIR Appendix F",
        [],
        options=_ResolveOptions(
            catalog_designators={
                "appendix:f:1": {"deir_appendix_f1"},
                "appendix:f:2": {"deir_appendix_f2"},
            }
        ),
    )
    assert absent_link is None
    assert absent["terminal_reason"] == "appendix_source_route_absent"


def test_leading_identifier_and_attached_title_rules_fail_closed() -> None:
    canonical = _row("4.6 biological resources", "deir_main", "section", "1")
    duplicate = _row("4.6 . biological resources", "deir_main", "section", "2")
    unique, unique_link = _resolve(
        "Draft EIR Section 4.6.1",
        [_row("4.6.1 introduction", "deir_main", "section", "3")],
    )
    assert unique_link is not None
    assert unique_link["resolver_rule"] == "task05f_leading_identifier_exact_v1"

    titled, titled_link = _resolve(
        "Draft EIR Section 4.6",
        [duplicate, canonical],
        options=_ResolveOptions(
            context=_MentionContext(after=", Biological Resources, evaluates impacts")
        ),
    )
    assert titled_link is not None
    assert titled_link["target_id"] == canonical["target_id"]
    assert titled_link["resolver_rule"] == "task05f_attached_title_exact_v1"

    collision, collision_link = _resolve(
        "Draft EIR Section 4.6",
        [duplicate, canonical],
    )
    assert collision_link is None
    assert collision["terminal_reason"] == "exact_target_collision"
    assert collision["compatible_target_ids"] == sorted(
        [canonical["target_id"], duplicate["target_id"]]
    )


def test_hierarchical_subsection_composes_exact_parent_and_direct_child() -> None:
    parent = _row("4.8.3 regulatory context", "deir_main", "section", "1")
    child = _row(
        "d. City of Brisbane Plans, Ordinances, and Regulations",
        "deir_main",
        "section",
        "2",
    )
    unrelated_parent = _row("4.9.3 regulatory context", "deir_main", "section", "3")
    unrelated_child = _row("d. Local regulations", "deir_main", "section", "4")
    children = {
        str(parent["target_id"]): (str(child["target_id"]),),
        str(unrelated_parent["target_id"]): (str(unrelated_child["target_id"]),),
    }

    dotted, dotted_link = _resolve(
        "Draft EIR Section 4.8.3.d",
        [parent, child, unrelated_parent, unrelated_child],
        options=_ResolveOptions(direct_section_children=children),
    )
    assert dotted["outcome"] == "resolved"
    assert dotted_link is not None
    assert dotted_link["target_id"] == child["target_id"]
    assert dotted_link["resolver_rule"] == "task05f_hierarchical_subsection_exact_v1"

    undotted, undotted_link = _resolve(
        "Draft EIR Section 4.8.3d",
        [parent, child],
        options=_ResolveOptions(
            direct_section_children={str(parent["target_id"]): (str(child["target_id"]),)}
        ),
    )
    assert undotted["outcome"] == "resolved"
    assert undotted_link is not None
    assert undotted_link["target_id"] == child["target_id"]


def test_hierarchical_subsection_requires_one_direct_child() -> None:
    parent = _row("4.8.7 project impacts", "deir_main", "section", "1")
    first = _row("a. First child", "deir_main", "section", "2")
    second = _row("a. Second child", "deir_main", "section", "3")

    absent, absent_link = _resolve(
        "Draft EIR Section 4.8.7a",
        [parent, first],
        options=_ResolveOptions(direct_section_children={str(parent["target_id"]): ()}),
    )
    assert absent_link is None
    assert absent["terminal_reason"] == "exact_target_absent"

    collision, collision_link = _resolve(
        "Draft EIR Section 4.8.7a",
        [parent, first, second],
        options=_ResolveOptions(
            direct_section_children={
                str(parent["target_id"]): (
                    str(first["target_id"]),
                    str(second["target_id"]),
                )
            }
        ),
    )
    assert collision_link is None
    assert collision["terminal_reason"] == "exact_target_collision"
    assert collision["compatible_target_ids"] == sorted([first["target_id"], second["target_id"]])


def test_es_identifiers_resolve_uniquely_or_preserve_collisions() -> None:
    unique = _row("ES.5.3 Environmental Impacts", "deir_main", "section", "1")
    outcome, link = _resolve("Draft EIR Section ES.5.3", [unique])
    assert outcome["outcome"] == "resolved"
    assert link is not None
    assert link["resolver_rule"] == "task05f_es_identifier_exact_v1"

    alternatives = [
        _row("ES.6 Alternatives", "deir_main", "section", str(number)) for number in range(1, 8)
    ]
    collision, collision_link = _resolve("Draft EIR Section ES.6", alternatives)
    assert collision_link is None
    assert collision["terminal_reason"] == "exact_target_collision"
    assert len(collision["compatible_target_ids"]) == 7


@pytest.mark.parametrize(
    ("mention_label", "published_label"),
    [
        ("Draft EIR Table 4.3.2", "Table 4.3-2 Regional Plans"),
        ("Draft EIR Table 4.8.11", "Table 4.8-11 Vehicle Miles Traveled"),
    ],
)
def test_table_period_separator_normalizes_only_the_final_separator(
    mention_label: str,
    published_label: str,
) -> None:
    target = _row(published_label, "deir_main", "table", "1")
    outcome, link = _resolve(mention_label, [target])
    assert outcome["outcome"] == "resolved"
    assert link is not None
    assert link["target_id"] == target["target_id"]
    assert link["resolver_rule"] == "task05f_table_separator_normalization_v1"


def test_section_hyphen_separator_preserves_all_normalized_candidates() -> None:
    candidates = [
        _row("4.11 Energy Resources", "deir_main", "section", str(number)) for number in range(1, 4)
    ]
    outcome, link = _resolve("Draft EIR Section 4-11", candidates)
    assert link is None
    assert outcome["terminal_reason"] == "exact_target_collision"
    assert len(outcome["compatible_target_ids"]) == 3


def test_attached_title_prefers_the_longest_complete_candidate_alias() -> None:
    short = _row("4.6 biological", "deir_main", "section", "1")
    long = _row("4.6 biological resources", "deir_main", "section", "2")
    outcome, link = _resolve(
        "Draft EIR Section 4.6",
        [short, long],
        options=_ResolveOptions(
            context=_MentionContext(after=", Biological Resources evaluates impacts")
        ),
    )
    assert outcome["outcome"] == "resolved"
    assert link is not None
    assert link["target_id"] == long["target_id"]


def test_unique_appendix_document_does_not_replace_attached_inner_target() -> None:
    row = _row(
        "Appendix D - Biological Resources Technical Report",
        "deir_appendix_d",
        "document",
        "4",
    )
    aliases = {normalize_alias("Appendix D"): {"deir_appendix_d"}}
    outer, outer_link = _resolve(
        "Draft EIR Appendix D",
        [row],
        options=_ResolveOptions(catalog_aliases=aliases),
    )
    assert outer_link is not None
    assert outer_link["resolver_rule"] == "task05f_unique_appendix_document_v1"

    inner, inner_link = _resolve(
        "Draft EIR Appendix D",
        [row],
        options=_ResolveOptions(
            catalog_aliases=aliases,
            context=_MentionContext(before="Figure 3 of the report (", after=")"),
        ),
    )
    assert inner_link is None
    assert inner["terminal_reason"] == "more_specific_appendix_target_requires_resolution"


def test_comments_are_preserved_without_links_after_exact_accounting() -> None:
    row = _row("Chapter 3", "deir_main", "section", "1")
    outcome, link = _resolve(
        "Draft EIR Chapter 3",
        [row],
        options=_ResolveOptions(source_kind="comment"),
    )
    assert link is None
    assert outcome["terminal_reason"] == ("comment_authored_reference_no_official_response_link")
    assert outcome["compatible_target_ids"] == [row["target_id"]]


def test_appendix_q_and_absent_figures_have_distinct_closures() -> None:
    appendix_q, link = _resolve_reference(
        _mention("Appendix Q", domain="appendix_q"),
        _source(),
        _ResolutionResources(
            indexes=_target_indexes([]),
            catalog_aliases={},
            catalog_designators={},
            registry=_registry("deir_main"),
            activity=_activity(),
        ),
    )
    assert link is None
    assert appendix_q["terminal_reason"] == "appendix_q_verification_required"

    figure, figure_link = _resolve("Draft EIR Figure 2-16", [])
    assert figure_link is None
    assert figure["terminal_reason"] == "exact_figure_target_absent"
    assert figure["visual_evidence_usability"] == "not_applicable"


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("eligible", "usable"),
        ("eligible_with_warning", "usable_with_warning"),
        ("ineligible", "unusable"),
        ("repair_required", "unusable"),
        ("unresolved", "unusable"),
        ("not_evaluated", "not_applicable"),
    ],
)
def test_task04a_dispositions_map_deterministically(status: str, expected: str) -> None:
    assert map_task04a_usability({"status": status}) == expected


def test_visual_usability_is_independent_and_figure_specific() -> None:
    assert map_visual_usability("section", "usable") == "not_applicable"
    assert map_visual_usability("figure", "usable") == "not_reviewed"
    assert map_visual_usability("figure", "usable_with_warning") == "not_reviewed"
    assert map_visual_usability("figure", "unusable") == "unusable"


def test_unrecognized_task04a_disposition_fails_closed() -> None:
    with pytest.raises(ValueError, match="unsupported Task 04A"):
        map_task04a_usability({"status": "mystery"})


def test_outcome_schema_rejects_unexpected_fields() -> None:
    outcome, _link = _resolve("Draft EIR Figure 2-16", [])
    schema_path = (
        Path(__file__).parents[1]
        / "benchmarks/er_bench/schemas/response_inventory/v5/reference_outcome.schema.json"
    )
    validator = Draft202012Validator(json.loads(schema_path.read_text()))
    validator.validate(outcome)
    outcome["invented_match"] = True
    assert list(validator.iter_errors(outcome))


def test_acceptance_binding_rejects_content_substitution() -> None:
    record: JsonObject = {"status": "accepted", "activity_id": "activityv1-test"}
    record["acceptance_id"] = f"acceptancev1-{canonical_json_sha256(record)}"
    _validate_acceptance(record, expected={"status": "accepted"})
    with pytest.raises(ValueError, match="binding mismatch"):
        _validate_acceptance(record, expected={"status": "rejected"})


def test_indexes_are_sorted_and_close_the_link_set() -> None:
    links = [
        {"link_id": "link-b", "target_id": "target-a"},
        {"link_id": "link-a", "target_id": "target-a"},
    ]
    outcomes = [
        {"mention_id": "mention-b", "link_id": "link-b"},
        {"mention_id": "mention-a", "link_id": "link-a"},
        {"mention_id": "mention-c", "link_id": None},
    ]
    forward, reverse = _indexes(outcomes, links)
    assert [item["mention_id"] for item in forward] == [
        "mention-a",
        "mention-b",
        "mention-c",
    ]
    assert reverse == [{"target_id": "target-a", "link_ids": ["link-a", "link-b"]}]


def test_publication_reuses_exact_bytes_and_rejects_partial_state(tmp_path: Path) -> None:
    root = tmp_path / "candidate"
    payloads = {"records/activity.json": b"{}\n"}
    receipt = {"status": "exact"}
    _publish_candidate(root, payloads, receipt)
    _publish_candidate(root, payloads, receipt)
    (tmp_path / "partial").mkdir()
    with pytest.raises(ValueError, match="partial"):
        _publish_candidate(tmp_path / "partial", payloads, receipt)

    (root / "unexpected.txt").write_text("not managed")
    with pytest.raises(ValueError, match="unexpected=.*unexpected.txt"):
        _publish_candidate(root, payloads, receipt)


def test_large_upstream_file_is_never_hashed(tmp_path: Path) -> None:
    path = tmp_path / "large.jsonl"
    path.write_bytes(b"x" * 100_001)
    with pytest.raises(ValueError, match="refusing to hash"):
        _sha256_small(path)
