"""Synthetic review selection, sparse ledger, and source-faithful cache tests."""

from copy import deepcopy
from types import SimpleNamespace
from typing import Any, cast

import pytest

from er_commons.response_inventory.release_inputs import ReleaseInputs
from er_commons.response_inventory.release_review import (
    QUESTION_VERSION,
    SCHEMA_VERSION,
    build_selection,
    build_view_index,
    validate_decisions,
    warning_profile,
)
from er_commons.response_inventory.release_views import build_review_cache


def inputs() -> ReleaseInputs:
    """A small accepted-shaped graph with one unattached General Response."""
    rows: list[dict[str, Any]] = [
        {"record_type": "page", "page_id": "p", "physical_page": 8, "raw_text": "<x>é🙂"}
    ]
    for index, kind in enumerate(["comment", "response", "general_response"]):
        rows.extend(
            [
                {
                    "record_type": "source_unit",
                    "unit_id": f"u{index}",
                    "unit_kind": kind,
                    "official_label": kind,
                    "span_ids": [f"s{index}"],
                },
                {
                    "record_type": "source_span",
                    "span_id": f"s{index}",
                    "fragments": [{"page_id": "p", "text_start": 0, "text_end": 5}],
                },
            ]
        )
    outcomes = [
        {
            "mention_id": f"m{i}",
            "source_unit_id": "u1",
            "outcome": "resolved",
            "resolver_rule": "exact",
            "final_f1_warning": None,
            "target_annotations": [
                {
                    "target_id": f"t{i}",
                    "target_type": "figure",
                    "text_only_model_eligibility": False,
                }
            ],
        }
        for i in range(3)
    ]
    return cast(
        ReleaseInputs,
        SimpleNamespace(
            source_records=rows,
            edges=[
                {
                    "edge_id": "e",
                    "relation_type": "comment_response",
                    "source_unit_id": "u0",
                    "target_unit_id": "u1",
                    "evidence_ids": [],
                    "evidence_resolutions": [{"resolver_rule": "exact_typed_label_suffix_v1"}],
                }
            ],
            graph_views=[
                {
                    "view_id": "v",
                    "root_unit_id": "u0",
                    "ordered_unit_ids": ["u0", "u1"],
                    "edge_ids": ["e"],
                }
            ],
            graph_diagnostics=[],
            outcomes=outcomes,
            limitations={"coverage": {"sampled_carries_individually_rereviewed": False}},
            dependencies=[],
            semantic_digest="d" * 64,
        ),
    )


def decision(refs: list[str], **changes: Any) -> dict[str, Any]:
    """Supply a human-authored fixture attestation, never a production judgment."""
    row = {
        "decision_id": "d1",
        "schema_version": SCHEMA_VERSION,
        "plan_id": "plan05hv1-" + "a" * 64,
        "subject_refs": refs,
        "question_version": QUESTION_VERSION,
        "coverage_basis": "new_individual",
        "disposition": "confirmed_with_limitation",
        "rationale": "Synthetic fixture review",
        "evidence_refs": [
            {
                "identity": "sealed",
                "path": "records/evidence.json",
                "sha256": "a" * 64,
                "record_id": "record",
            }
        ],
        "reviewer": "Fixture reviewer",
        "reviewed_at": "2026-09-17T20:00:00Z",
        "supersedes": [],
        "action": "none",
        "replacement_refs": [],
        "requires_owner_replay": False,
    }
    row.update(changes)
    return row


def test_selection_order_independent_and_first_last() -> None:
    """Changing input order and target IDs cannot create accidental per-row strata."""
    original = inputs()
    shuffled = deepcopy(original)
    shuffled.source_records.reverse()
    shuffled.outcomes.reverse()
    assert build_selection(original) == build_selection(shuffled)
    strata = [s for s in build_selection(original)["strata"] if s["kind"] == "official_link"]
    assert len(strata) == 1
    assert strata[0]["selected_refs"] == ["m0", "m2"]
    assert "u2" in {o["subject_ref"] for o in build_selection(original)["obligations"]}


def test_navigation_reaches_orphan_without_following_cycle() -> None:
    """Accepted views retain ordering and navigation includes every unattached unit."""
    value = inputs()
    index = build_view_index(value)
    assert index[0]["ordered_unit_ids"] == ["u0", "u1"]
    assert {u for row in index for u in row["ordered_unit_ids"]} == {"u0", "u1", "u2"}


def test_nonlink_cards_split_heterogeneous_resolver_rules() -> None:
    """An equal reason cannot conceal different accepted resolver rules."""
    value = inputs()
    value.outcomes = [
        dict(o, outcome="unresolved", terminal_reason="absent", resolver_rule=f"rule{i % 2}")
        for i, o in enumerate(value.outcomes)
    ]
    cards = [o for o in build_selection(value)["obligations"] if o["coverage_basis"] == "new_rule"]
    assert len(cards) == 2
    assert sum(len(o["member_refs"]) for o in cards) == 3


def test_warning_profile_ignores_identity_and_free_text() -> None:
    """Profile bins bind categorical coverage, not individual target identities."""
    assert warning_profile({"target_id": "a", "warning": "prose", "coverage_kind": "sampled"}) == [
        "coverage_kind:sampled"
    ]


def test_decisions_require_every_obligation_and_no_hidden_override() -> None:
    """Missing and conflicting decisions cannot pass; explicit later review can."""
    selection = build_selection(inputs())
    refs = [o["subject_ref"] for o in selection["obligations"]]
    with pytest.raises(ValueError, match="pending"):
        validate_decisions(selection, [], "plan05hv1-" + "a" * 64)
    first = decision(refs)
    assert (
        validate_decisions(selection, [first, first], "plan05hv1-" + "a" * 64)["pending_count"] == 0
    )
    second = decision(refs, decision_id="d2", reviewed_at="2026-09-18T20:00:00Z")
    with pytest.raises(ValueError, match="conflicting"):
        validate_decisions(selection, [first, second], "plan05hv1-" + "a" * 64)
    second["supersedes"] = ["d1"]
    assert set(
        validate_decisions(selection, [second, first], "plan05hv1-" + "a" * 64)[
            "decision_refs"
        ].values()
    ) == {"d2"}


@pytest.mark.parametrize(
    "changes",
    [
        {"disposition": "correction_required"},
        {"requires_owner_replay": True},
        {"action": "owner_finding"},
        {"replacement_refs": ["replacement"]},
        {"evidence_refs": []},
        {"plan_id": "wrong"},
        {"coverage_basis": "inherited_sampled_stratum"},
    ],
)
def test_unsafe_or_unattested_decisions_stop(changes: dict[str, Any]) -> None:
    """Review closure cannot promote owner changes, unbound claims or inherited samples."""
    selection = build_selection(inputs())
    refs = [o["subject_ref"] for o in selection["obligations"]]
    with pytest.raises(ValueError):
        validate_decisions(selection, [decision(refs, **changes)], "plan05hv1-" + "a" * 64)


def test_cache_is_lazy_escaped_and_preserves_limitations() -> None:
    """Only requested text is rendered with raw Unicode anchors and truthful exclusions."""
    value = inputs()
    index = build_view_index(value)
    assert set(build_review_cache(value, index)) == {"index.html"}
    cache = build_review_cache(value, index, ["u0"])
    card = next(v.decode() for k, v in cache.items() if k != "index.html")
    assert "&lt;x&gt;é🙂" in card
    assert "raw Unicode [0, 5)" in card
    assert "text_only_model_eligibility" in card and "false" in card
    assert "sampled_carries_individually_rereviewed" in card
    assert "<script" not in card


def test_cache_indexes_primary_ids_only_when_records_shuffled() -> None:
    """A marker's page foreign key must never replace the source-page record."""
    value = inputs()
    value.source_records.insert(
        0, {"record_type": "marker_candidate", "marker_id": "marker", "page_id": "p"}
    )
    cache = build_review_cache(value, build_view_index(value), ["u0"])
    assert any("&lt;x&gt;é🙂" in content.decode() for content in cache.values())


def test_provenance_strata_retain_distinct_coverage_claims() -> None:
    """Proved correspondence and sampled carries receive separate display obligations."""
    value = inputs()
    value.limitations["decision_provenance"] = [
        {"entry_id": "proved", "decision_origin": "accepted_task04_proved_correspondence"},
        {
            "entry_id": "sampled",
            "decision_origin": "accepted_task04_repaired_source_sample_confirmed",
        },
    ]
    strata = [
        s for s in build_selection(value)["strata"] if s["kind"] == "inherited_provenance_display"
    ]
    assert len(strata) == 2
    assert {tuple(s["member_refs"]) for s in strata} == {("proved",), ("sampled",)}


def test_forged_or_unrelated_sealed_evidence_rejected() -> None:
    """A real receipt is insufficient when the cited member belongs to another subject."""
    from er_commons.response_inventory.release_review import validate_decision_evidence

    value = inputs()
    value.components = []
    value.dependencies = [
        {
            "role": "task05d_completion",
            "identity": "sealed",
            "path": "records/evidence.json",
            "sha256": "a" * 64,
        }
    ]
    selection = build_selection(value)
    valid = decision(["u0"])
    valid["evidence_refs"][0]["record_id"] = "u0"
    validate_decision_evidence(value, selection, [valid])
    forged = deepcopy(valid)
    forged["evidence_refs"][0]["sha256"] = "b" * 64
    with pytest.raises(ValueError, match="not a retained"):
        validate_decision_evidence(value, selection, [forged])
    unrelated = deepcopy(valid)
    unrelated["evidence_refs"][0]["record_id"] = "u1"
    with pytest.raises(ValueError, match="unrelated"):
        validate_decision_evidence(value, selection, [unrelated])


def test_graph_rules_and_nonmatch_classes_use_accepted_census() -> None:
    """Policy labels and absent inline evidence must not invent resolver provenance."""
    value = inputs()
    value.edges[0].pop("evidence_resolutions")
    value.limitations["graph_review_census"] = {
        "mention_outcomes": [
            {
                "edge_id": "e",
                "outcome": "resolved",
                "input_id": "m0",
                "rule": "exact_official_label_v1",
            },
            {
                "outcome": "terminal_nonmatch",
                "input_id": "nonmatch",
                "rule": "running_header_mention_classification_v1",
                "reason": "running_header",
            },
        ]
    }
    selection = build_selection(value)
    graph = next(s for s in selection["strata"] if s["kind"] == "graph")
    assert "exact_official_label_v1" in graph["key"]
    assert "exact_typed_label_suffix_v1" not in graph["key"]
    card = next(o for o in selection["obligations"] if o["coverage_basis"] == "new_rule")
    assert card["member_refs"] == ["nonmatch"]
    assert card["reasons"] == [
        "intra_volume_nonmatch:running_header:running_header_mention_classification_v1"
    ]


def test_response_selected_card_retains_paired_comment() -> None:
    """Starting from a response or its reference still exposes the accepted paired comment."""
    value = inputs()
    cache = build_review_cache(value, build_view_index(value), ["m0"])
    card = next(content.decode() for name, content in cache.items() if name != "index.html")
    assert "<h2>comment</h2>" in card
    assert "<h2>response</h2>" in card


def test_decision_cannot_claim_rule_review_for_individual_obligation() -> None:
    selection = build_selection(inputs())
    with pytest.raises(ValueError, match="coverage basis"):
        validate_decisions(
            selection, [decision(["u0"], coverage_basis="new_rule")], "plan05hv1-" + "a" * 64
        )


@pytest.mark.parametrize("invalid", ["", " ", 42, None])
def test_decision_id_requires_nonempty_string(invalid: Any) -> None:
    selection = build_selection(inputs())
    with pytest.raises(ValueError, match="decision ID"):
        validate_decisions(
            selection, [decision(["u0"], decision_id=invalid)], "plan05hv1-" + "a" * 64
        )


def test_supersession_cannot_hide_a_stratum_mismatch() -> None:
    """A mismatch requires a new approved plan, not another same-plan confirmation."""
    selection = build_selection(inputs())
    mismatch = decision(["u0"], disposition="correction_required")
    replacement = decision(
        ["u0"], decision_id="d2", supersedes=["d1"], reviewed_at="2026-09-18T20:00:00Z"
    )
    with pytest.raises(ValueError, match="affected strata pending"):
        validate_decisions(selection, [mismatch, replacement], "plan05hv1-" + "a" * 64)


def test_general_response_card_does_not_expand_every_incoming_comment() -> None:
    """Shared General Response membership is navigation, not a command to flatten views."""
    value = inputs()
    value.graph_views[0]["ordered_unit_ids"].append("u2")
    value.source_records[1]["official_label"] = "UNRELATED COMMENT CONTEXT"
    index = build_view_index(value)
    cache = build_review_cache(value, index, ["u2"])
    card = next(data.decode() for name, data in cache.items() if name.startswith("cards/"))
    assert "UNRELATED COMMENT CONTEXT" not in card
    assert "general_response" in card
    response_cache = build_review_cache(value, index, ["u1"])
    response_card = next(
        data.decode() for name, data in response_cache.items() if name.startswith("cards/")
    )
    assert "UNRELATED COMMENT CONTEXT" in response_card


def test_cards_keep_only_relevant_limitations_and_shared_sealed_references() -> None:
    """The full inherited registry is never repeated on each focused card."""
    value = inputs()
    value.limitations["registry"] = {"entries": [{"unrelated": "UNRELATED REGISTRY ROW"}]}
    value.dependencies = [{"path": "records/accepted_registry.json", "sha256": "a" * 64}]
    cache = build_review_cache(value, build_view_index(value), ["u0"])
    card = next(data.decode() for name, data in cache.items() if name.startswith("cards/"))
    assert "UNRELATED REGISTRY ROW" not in card
    assert "accepted_registry.json" not in card
    assert "accepted_registry.json" in cache["index.html"].decode()
    assert "#limitations" in card
    assert "other_mentions_not_proven_draft_final_equivalent" in card


def test_estimate_bounds_cache_without_rendering(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admission estimates use the same bounded contexts but no HTML production path."""
    from er_commons.response_inventory import release_views

    value = inputs()
    index = build_view_index(value)
    subjects = [row["subject_ref"] for row in build_selection(value)["obligations"]]
    actual = sum(len(data) for data in build_review_cache(value, index, subjects).values())

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("estimate rendered review material")

    monkeypatch.setattr(release_views, "build_review_cache", forbidden)
    monkeypatch.setattr(release_views, "_pre", forbidden)
    monkeypatch.setattr(release_views, "_document", forbidden)
    assert release_views.estimate_review_cache_bytes(value, index, subjects) >= actual
