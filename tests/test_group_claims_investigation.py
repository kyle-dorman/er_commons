"""Source-free qualification of explicitly authorized investigation-only policy."""

import copy

import pytest
from test_group_claims_export import fixture, set_field

from er_commons.group_claims_export import INVESTIGATION_POLICY, normalize_export


def investigation(trusted, native, policy=INVESTIGATION_POLICY):
    """Export a synthetic review under an explicit policy choice."""
    return normalize_export(
        native,
        trusted,
        project_id=2,
        reviewer_id=4,
        export_sha256="c" * 64,
        policy_revision=policy,
    )


def chain_fixture():
    """Add a third approved claim supporting another supporting claim."""
    trusted, native = fixture()
    for field, value in {
        "text": "The response qualifies that material reason.",
        "passages": "P1",
        "relationship": "supporting",
        "targets": "A002",
        "rationale": "Bounds the reason underlying the direct conclusion.",
        "decision": "approve",
    }.items():
        set_field(native[0], f"s003_{field}", value)
    return trusted, native


def test_unresolved_scope_is_preserved_and_only_investigation_advances():
    trusted, native = chain_fixture()
    for task in (trusted[0], native[0]):
        task["data"]["proposal"]["question_parts"][0]["status"] = "unanswered"
    set_field(native[0], "gaps_status", "unresolved")
    result = investigation(trusted, native)
    record = result["records"][0]
    assert record["state"] == "ready"
    assert record["scope_unresolved"] is True
    assert record["investigation_only"] is True
    assert record["unresolved_question_parts"] == trusted[0]["data"]["proposal"]["question_parts"]
    assert result["advancement_scope"] == record["advancement_scope"] == "08E_investigation_only"
    assert result["eligibility"] == record["eligibility"] == "undecided"
    assert result["native_tasks"] == native
    assert "gaps_resolution" not in record["fields"]
    with pytest.raises(ValueError, match="Ready case"):
        investigation(trusted, native, None)


def test_full_support_chain_binds_exact_ancestor_content_and_versions():
    trusted, native = chain_fixture()
    before = investigation(trusted, native)["records"][0]["approved_claims"]
    set_field(native[0], "s001_text", "  Revised qualified result.\n")
    after = investigation(trusted, native)["records"][0]["approved_claims"]
    direct, support, leaf = after
    assert leaf["target_claim_version"] == support["claim_version"]
    assert [b["claim_id"] for b in leaf["support_chain_versions"]] == ["A002", "A001"]
    assert leaf["support_chain_versions"][-1]["claim_version"] == direct["claim_version"]
    assert leaf["support_chain_sha256"] != before[2]["support_chain_sha256"]
    assert leaf["claim_version"] != before[2]["claim_version"]
    assert direct["text"] == "  Revised qualified result.\n"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("s002_targets", "A003"),  # Cycle.
        ("s003_targets", "A003"),  # Self-edge.
        ("s002_targets", "A999"),  # Missing ancestor.
        ("s002_decision", "reject"),
        ("s002_decision", "unresolved"),
        ("s002_decision", ""),
        ("s002_relationship", "unclear"),
        ("s002_rationale", ""),
        ("s001_targets", "missing-part"),
        ("s001_passages", "missing-span"),
        ("s003_targets", "A001,A002"),
        ("links_confirmed", ""),
        ("gaps_status", ""),
    ],
)
def test_invalid_ancestor_or_saved_decision_still_blocks(field, value):
    trusted, native = chain_fixture()
    set_field(native[0], field, value)
    with pytest.raises(ValueError, match="Ready case"):
        investigation(trusted, native)


@pytest.mark.parametrize("status", ["stop", "unresolved"])
def test_whole_case_holds_and_stops_never_release_claims(status):
    trusted, native = chain_fixture()
    set_field(native[0], "case_status", status)
    set_field(native[0], "case_note", "Hold the whole case for review.")
    set_field(native[0], "gaps_status", "unresolved")
    result = investigation(trusted, native)
    assert result["advancing_case_ids"] == []
    assert result["records"][0]["approved_claims"] == []
    assert result["records"][0]["advancement_scope"] is None


def test_graph_validation_is_independent_of_slot_order():
    trusted, native = chain_fixture()
    for task in (trusted[0], native[0]):
        task["data"]["slot_bindings"].reverse()
    result = investigation(trusted, native)
    claims = result["records"][0]["approved_claims"]
    assert claims[0]["relationship"] == "direct"
    assert (
        next(c for c in claims if c["claim_id"] == "A003")["support_chain"][-1]["claim_id"]
        == "A001"
    )


def test_policy_is_explicit_and_default_does_not_add_fields():
    trusted, native = fixture()
    strict = investigation(trusted, native, None)
    assert "policy_revision" not in strict
    assert "investigation_only" not in strict["records"][0]
    assert "support_chain" not in strict["records"][0]["approved_claims"][1]
    with pytest.raises(ValueError, match="policy revision"):
        investigation(trusted, native, "unknown-policy")
    original = copy.deepcopy(native)
    investigation(trusted, native)
    assert original == native


def test_v2_chains_keep_trusted_source_anchors_and_exact_rationale():
    """Current form chains never require invented or reviewer-entered anchors."""
    from er_commons.group_claims_export import VERSION

    trusted, native = chain_fixture()
    for task in (trusted[0], native[0]):
        data = task["data"]
        data["form_version"] = VERSION
        data["slot_bindings"][2]["proposal_claim_id"] = "A003"
        data["proposal"]["claims"].append({"claim_id": "A003"})
        for claim in data["proposal"]["claims"]:
            claim["passage_ids"] = ["P1"]
    results = native[0]["annotations"][0]["result"]
    results[:] = [r for r in results if not r["from_name"].endswith("_passages")]
    set_field(native[0], "s002_rationale", "  A qualified material contribution.\n")
    leaf = investigation(trusted, native)["records"][0]["approved_claims"][2]
    assert leaf["source_binding_origin"] == "trusted_proposal"
    assert leaf["passage_ids"] == ["P1"]
    before = leaf["support_chain_sha256"]
    set_field(native[0], "s002_rationale", "A qualified material contribution.")
    leaf = investigation(trusted, native)["records"][0]["approved_claims"][2]
    assert leaf["support_chain_sha256"] != before
