"""Generic Gate C tests for reusable policy, caller profiles, and R6 aliases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.document_records.document_references.exact_resolution import (
    ExactAliasEvidence,
    ExactResolutionOutcome,
)
from er_commons.document_records.document_references.linking_core import (
    LinkQuery,
    resolve_link_query,
)
from er_commons.document_records.document_references.linking_policy import (
    LinkCaller,
    LinkingPolicyError,
    load_document_linking_policy,
)
from er_commons.document_records.document_references.table_aliases import (
    build_r6_table_aliases,
    normalize_table_caption,
)

ROOT = Path(__file__).parents[1]
POLICY_PATH = ROOT / "configs/linking_policies/document_linking_v1.json"
SCHEMA_PATH = ROOT / "benchmarks/er_bench/schemas/document_linking/v1/linking_policy.schema.json"


def _policy():
    return load_document_linking_policy(POLICY_PATH, schema_path=SCHEMA_PATH)


def _evidence(text: str, *, target_type: str = "section") -> ExactAliasEvidence:
    return ExactAliasEvidence(
        lookup_keys=(text,),
        target_type=target_type,
        alias_id="alias-1",
        target_id=f"{target_type}-1",
        target_page_ids=("page-1",),
    )


def test_strict_policy_loader_maps_complete_caller_profiles() -> None:
    policy = _policy()

    assert policy.machine_reference.section_fallback_rules == ()
    assert [rule.value for rule in policy.effective_navigation.section_fallback_rules] == [
        "terminal_period",
        "standalone_ampersand_and",
        "alphabetic_hyphen_separator",
        "slash_adjacent_whitespace",
        "split_fi_ligature",
        "optional_comma_before_and",
        "apostrophe_and_terminal_period",
        "retained_ascii_hyphen_adjacent_whitespace",
    ]
    assert policy.machine_reference.table_fallback_rules == (
        policy.effective_navigation.table_fallback_rules
    )


def test_policy_loader_rejects_schema_valid_duplicate_rule_ownership(tmp_path: Path) -> None:
    payload = json.loads(POLICY_PATH.read_bytes())
    payload["section_rules"][1]["rule_id"] = "R1"
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(payload))

    with pytest.raises(LinkingPolicyError, match="exactly once"):
        load_document_linking_policy(path, schema_path=SCHEMA_PATH)


def test_navigation_uses_r5_but_machine_section_references_do_not() -> None:
    aliases = (_evidence("4.2 GP-1-18 On-Site Improvements"),)
    machine = resolve_link_query(
        LinkQuery(
            caller=LinkCaller.MACHINE_REFERENCE,
            lookup_text="4.2 GP -1 -18 On -Site Improvements",
            target_type="section",
            aliases=aliases,
        ),
        policy=_policy(),
    )
    navigation = resolve_link_query(
        LinkQuery(
            caller=LinkCaller.EFFECTIVE_NAVIGATION,
            lookup_text="4.2 GP -1 -18 On -Site Improvements",
            target_type="section",
            aliases=aliases,
        ),
        policy=_policy(),
    )

    assert machine.outcome is ExactResolutionOutcome.NO_TEXT_MATCH
    assert navigation.outcome is ExactResolutionOutcome.RESOLVED_UNIQUE
    assert navigation.match_basis == ("retained_ascii_hyphen_adjacent_whitespace",)


@pytest.mark.parametrize("caller", tuple(LinkCaller))
def test_r6a_table_fallback_is_shared_by_both_callers(caller: LinkCaller) -> None:
    decision = resolve_link_query(
        LinkQuery(
            caller=caller,
            lookup_text="Table 8-2, Habitat Benefits",
            target_type="table",
            aliases=(_evidence("Table 8-2 , Habitat Benefits", target_type="table"),),
        ),
        policy=_policy(),
    )

    assert decision.outcome is ExactResolutionOutcome.RESOLVED_UNIQUE
    assert decision.match_basis == ("whitespace_before_comma",)


@pytest.mark.parametrize("caller", tuple(LinkCaller))
def test_r6a_optional_digit_letter_hyphen_handles_a_word(caller: LinkCaller) -> None:
    decision = resolve_link_query(
        LinkQuery(
            caller=caller,
            lookup_text="Table 8-11. Existing 45-acre Habitat",
            target_type="table",
            aliases=(_evidence("Table 8-11. Existing 45acre Habitat", target_type="table"),),
        ),
        policy=_policy(),
    )

    assert decision.outcome is ExactResolutionOutcome.RESOLVED_UNIQUE
    assert decision.match_basis == ("optional_digit_letter_hyphen",)


def test_r1_destination_intersection_remains_fail_closed() -> None:
    decision = resolve_link_query(
        LinkQuery(
            caller=LinkCaller.EFFECTIVE_NAVIGATION,
            lookup_text="4.2 Habitat",
            target_type="section",
            aliases=(_evidence("4.2 Habitat"),),
            destination_page_ids=("page-2",),
        ),
        policy=_policy(),
    )

    assert decision.outcome is ExactResolutionOutcome.DESTINATION_PAGE_MISMATCH


def test_callers_are_equivalent_for_identical_exact_candidates_and_page_scope() -> None:
    aliases = (
        ExactAliasEvidence(
            lookup_keys=("4.2 Habitat",),
            target_type="section",
            alias_id="alias-1",
            target_id="section-1",
            target_page_ids=("page-1",),
        ),
        ExactAliasEvidence(
            lookup_keys=("4.2 Habitat",),
            target_type="section",
            alias_id="alias-2",
            target_id="section-1",
            target_page_ids=("page-1",),
        ),
    )
    decisions = [
        resolve_link_query(
            LinkQuery(
                caller=caller,
                lookup_text="4.2 Habitat",
                target_type="section",
                aliases=aliases,
                destination_page_ids=("page-1",),
            ),
            policy=_policy(),
        )
        for caller in LinkCaller
    ]

    assert decisions[0] == decisions[1]
    assert decisions[0].outcome is ExactResolutionOutcome.RESOLVED_UNIQUE
    assert decisions[0].candidates[0].alias_ids == ("alias-1", "alias-2")


def test_r6_builds_complete_caption_alias_only_for_immediate_body_table() -> None:
    upstream = "exv1-" + "1" * 64
    candidate = "exv1-" + "2" * 64
    page = f"{upstream}/page/report/p000001"
    document = f"{upstream}/document/report"
    caption = _block(
        upstream,
        document,
        page,
        "Table 8-2. Habitat Benefits by Type",
        [10, 80, 90, 90],
        sequence=1,
    )
    table = _table(upstream, document, page, [15, 20, 85, 75])

    aliases = build_r6_table_aliases(
        upstream_candidate_id=upstream,
        candidate_id=candidate,
        source_id="report",
        upstream_blocks=[caption],
        upstream_tables=[table],
        first_sequence=1,
    )

    assert len(aliases) == 1
    assert aliases[0].record["normalized_alias"] == "table 8-2. habitat benefits by type"
    assert aliases[0].record["alias_origin"] == "linking_v1_r6_body_table_caption"
    assert aliases[0].evidence.lookup_keys == ("table 8-2. habitat benefits by type",)


def test_r6_accepts_terminal_letter_table_identifier() -> None:
    upstream = "exv1-" + "1" * 64
    candidate = "exv1-" + "2" * 64
    page = f"{upstream}/page/report/p000001"
    document = f"{upstream}/document/report"
    caption = _block(
        upstream,
        document,
        page,
        "Table 10a Existing Conditions",
        [10, 80, 90, 90],
        sequence=1,
    )
    table = _table(upstream, document, page, [15, 20, 85, 75])

    aliases = build_r6_table_aliases(
        upstream_candidate_id=upstream,
        candidate_id=candidate,
        source_id="report",
        upstream_blocks=[caption],
        upstream_tables=[table],
        first_sequence=1,
    )

    assert len(aliases) == 1
    assert aliases[0].record["normalized_alias"] == "table 10a existing conditions"


def test_r6_compacts_only_the_leading_table_identifier() -> None:
    assert (
        normalize_table_caption("Table 4.5 -2f. On -Site Improvements")
        == "table 4.5-2f. on -site improvements"
    )


@pytest.mark.parametrize(
    "change",
    ["intervening_block", "different_section", "no_overlap", "table_above", "toc_caption"],
)
def test_r6_rejects_any_missing_spatial_or_body_relation(change: str) -> None:
    upstream = "exv1-" + "1" * 64
    candidate = "exv1-" + "2" * 64
    page = f"{upstream}/page/report/p000001"
    document = f"{upstream}/document/report"
    caption = _block(upstream, document, page, "Table 3. Results", [10, 80, 90, 90], 1)
    table = _table(upstream, document, page, [15, 20, 85, 75])
    blocks = [caption]
    if change == "intervening_block":
        blocks.append(_block(upstream, document, page, "Note", [10, 76, 90, 79], 2))
    elif change == "different_section":
        table["section_id"] = "section-2"
    elif change == "no_overlap":
        table["regions"][0]["bbox"] = [100, 20, 120, 75]
    elif change == "table_above":
        table["regions"][0]["bbox"] = [15, 92, 85, 99]
    else:
        caption["is_toc_row"] = True

    aliases = build_r6_table_aliases(
        upstream_candidate_id=upstream,
        candidate_id=candidate,
        source_id="report",
        upstream_blocks=blocks,
        upstream_tables=[table],
        first_sequence=1,
    )

    assert aliases == ()


def _block(
    root: str,
    document: str,
    page: str,
    text: str,
    bbox: list[int],
    sequence: int,
) -> dict[str, object]:
    return {
        "id": f"{root}/block/report/blk{sequence:06d}",
        "document_id": document,
        "sequence": sequence,
        "canonical_text": text,
        "block_type": "caption",
        "content_layer": "body",
        "is_toc_row": False,
        "section_id": "section-1",
        "regions": [{"page_id": page, "bbox": bbox}],
    }


def _table(root: str, document: str, page: str, bbox: list[int]) -> dict[str, object]:
    return {
        "id": f"{root}/table/report/tbl000001",
        "document_id": document,
        "sequence": 1,
        "section_id": "section-1",
        "regions": [{"page_id": page, "bbox": bbox}],
    }
