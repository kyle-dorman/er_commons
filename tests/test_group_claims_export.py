"""Source-free saved-review qualification for Task 08D's fail-closed exporter."""

import copy
import hashlib

import pytest

from er_commons.group_claims_export import LEGACY_VERSION, VERSION, normalize_export


def fixture():
    """Build a synthetic two-claim review without historical case content."""
    question = {
        "text": "What does the response assert?",
        "question_id": "q1",
        "question_version": "v1",
    }
    question["text_sha256"] = hashlib.sha256(question["text"].encode()).hexdigest()
    data = {
        "form_version": LEGACY_VERSION,
        "case_id": "synthetic",
        "question": question,
        "packet_sha256": "a" * 64,
        "proposal_sha256": "b" * 64,
        "case_input": {
            "passages": [
                {
                    "passage_id": "P1",
                    "text": "The response asserts a qualified result.",
                    "source_version": "fixture-v1",
                    "warnings": ["synthetic"],
                }
            ]
        },
        "proposal": {
            "claims": [{"claim_id": "A001"}, {"claim_id": "A002"}],
            "question_parts": [
                {
                    "part_id": "Q1",
                    "text": question["text"],
                    "status": "addressed",
                    "essential": True,
                }
            ],
        },
        "slot_bindings": [
            {"slot": "s001", "claim_id": "A001", "proposal_claim_id": "A001"},
            {"slot": "s002", "claim_id": "A002", "proposal_claim_id": "A002"},
            {"slot": "s003", "claim_id": "A003", "proposal_claim_id": None},
        ],
    }
    fields = {
        "s001_text": "The response asserts a qualified result.",
        "s001_passages": "P1",
        "s001_relationship": "direct",
        "s001_targets": "Q1",
        "s001_decision": "approve",
        "s002_text": "The response supplies a material reason.",
        "s002_passages": "P1",
        "s002_relationship": "supporting",
        "s002_targets": "A001",
        "s002_rationale": "Explains the condition attached to the direct conclusion.",
        "s002_decision": "approve",
        "case_status": "ready",
        "links_confirmed": "confirmed",
        "gaps_status": "not-applicable",
    }
    native = {
        "id": 1,
        "project": 2,
        "data": copy.deepcopy(data),
        "drafts": [],
        "annotations": [
            {
                "id": 3,
                "task": 1,
                "completed_by": 4,
                "created_at": "2026-09-30T12:00:00Z",
                "updated_at": "2026-09-30T12:01:00Z",
                "result": [],
            }
        ],
    }
    for name, value in fields.items():
        set_field(native, name, value)
    return [{"data": data}], [native]


def set_field(task, name, value):
    """Replace a saved native control to model a human edit."""
    choices = name.endswith(("_decision", "_relationship")) or name in {
        "case_status",
        "links_confirmed",
        "gaps_status",
    }
    key, kind = ("choices", "choices") if choices else ("text", "textarea")
    results = task["annotations"][0]["result"]
    results[:] = [r for r in results if r["from_name"] != name]
    results.append(
        {"from_name": name, "to_name": "response_context", "type": kind, "value": {key: [value]}}
    )


def export(trusted, native):
    """Normalize with fixed synthetic native authority bindings."""
    return normalize_export(native, trusted, project_id=2, reviewer_id=4, export_sha256="c" * 64)


def test_saved_exact_edits_and_target_versions_survive():
    trusted, native = fixture()
    before = export(trusted, native)
    set_field(native[0], "s001_text", "  The response conditionally asserts a revised result.\n")
    after = export(trusted, native)
    direct, support = after["records"][0]["approved_claims"]
    assert direct["text"] == "  The response conditionally asserts a revised result.\n"
    assert support["target_claim_version"] == direct["claim_version"]
    assert (
        support["target_content_sha256"]
        != before["records"][0]["approved_claims"][1]["target_content_sha256"]
    )
    assert direct["source_spans"][0]["warnings"] == ["synthetic"]
    assert after["advancing_case_ids"] == ["synthetic"]


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("s001_relationship", "not-relevant"),
        ("s001_decision", "reject"),
        ("s002_targets", "A003"),
        ("s002_rationale", ""),
        ("s001_targets", "Q9"),
        ("s001_passages", "P999"),
        ("s001_decision", "unresolved"),
        ("gaps_status", ""),
        ("links_confirmed", ""),
    ],
)
def test_invalid_saved_ready_relationships_fail(name, value):
    trusted, native = fixture()
    set_field(native[0], name, value)
    with pytest.raises(ValueError, match="Ready case"):
        export(trusted, native)


def test_relationship_edit_to_direct_uses_current_part_targets():
    trusted, native = fixture()
    set_field(native[0], "s002_relationship", "direct")
    set_field(native[0], "s002_targets", "Q1")
    claims = export(trusted, native)["records"][0]["approved_claims"]
    assert [c["relationship"] for c in claims] == ["direct", "direct"]
    assert all("target_claim_version" not in c for c in claims)


@pytest.mark.parametrize("state", ["stop", "unresolved"])
def test_holds_preserve_invalid_claims_and_never_advance(state):
    trusted, native = fixture()
    set_field(native[0], "case_status", state)
    set_field(native[0], "case_note", "The complete question remains unresolved.")
    set_field(native[0], "s001_decision", "unresolved")
    result = export(trusted, native)
    assert result["advancing_case_ids"] == []
    record = result["records"][0]
    assert len(record["claims"]) == 2
    assert record["errors"]
    assert record["approved_claims"] == []
    assert result["native_tasks"] == native


def test_essential_question_gap_requires_resolution():
    trusted, native = fixture()
    for task in (trusted[0], native[0]):
        task["data"]["proposal"]["question_parts"][0]["status"] = "unanswered"
    with pytest.raises(ValueError, match="question parts"):
        export(trusted, native)
    set_field(native[0], "gaps_status", "resolved")
    set_field(
        native[0], "gaps_resolution", "Reviewed exact source addresses this part through A001."
    )
    assert export(trusted, native)["advancing_case_ids"]


@pytest.mark.parametrize(
    "mutation", ["source", "question", "project", "reviewer", "task", "multiple", "missing"]
)
def test_tampered_or_ambiguous_native_bindings_fail(mutation):
    trusted, native = fixture()
    task = native[0]
    if mutation == "source":
        task["data"]["case_input"]["passages"][0]["source_version"] = "foreign"
    elif mutation == "question":
        task["data"]["question"]["text"] = "Rewritten?"
    elif mutation == "project":
        task["project"] = 10
    elif mutation == "reviewer":
        task["annotations"][0]["completed_by"] = 10
    elif mutation == "task":
        task["annotations"][0]["task"] = 10
    elif mutation == "multiple":
        task["annotations"].append(copy.deepcopy(task["annotations"][0]))
    else:
        native.clear()
    with pytest.raises(ValueError):
        export(trusted, native)


def test_drafts_and_untouched_never_read_predictions_as_decisions():
    trusted, native = fixture()
    native[0]["predictions"] = copy.deepcopy(native[0]["annotations"])
    native[0]["annotations"] = []
    assert export(trusted, native)["records"][0]["state"] == "unreviewed"
    native[0]["drafts"] = [{"result": []}]
    assert export(trusted, native)["records"][0]["state"] == "pending_draft"


def test_new_claim_uses_same_explicit_decision_and_source_gate():
    trusted, native = fixture()
    for field, value in {
        "text": "The response adds a distinct assertion.",
        "passages": "P1",
        "relationship": "direct",
        "targets": "Q1",
    }.items():
        set_field(native[0], f"s003_{field}", value)
    with pytest.raises(ValueError, match="explicit claim disposition"):
        export(trusted, native)
    set_field(native[0], "s003_decision", "approve")
    claims = export(trusted, native)["records"][0]["approved_claims"]
    assert len(claims) == 3
    assert next(c for c in claims if c["claim_id"] == "A003")["proposal_claim_id"] is None


def test_nonrelevant_and_rejected_dispositions_are_retained_only():
    trusted, native = fixture()
    set_field(native[0], "s002_relationship", "not-relevant")
    set_field(native[0], "s002_targets", "")
    result = export(trusted, native)["records"][0]
    assert len(result["claims"]) == 2
    assert len(result["approved_claims"]) == 1
    assert result["claims"][1]["decision"] == "approve"
    set_field(native[0], "s002_decision", "reject")
    result = export(trusted, native)["records"][0]
    assert result["claims"][1]["decision"] == "reject"
    assert len(result["approved_claims"]) == 1


def test_question_part_losing_direct_coverage_is_not_silently_removed():
    trusted, native = fixture()
    for task in (trusted[0], native[0]):
        task["data"]["proposal"]["question_parts"].append(
            {
                "part_id": "Q2",
                "text": "A second essential subquestion?",
                "status": "addressed",
                "essential": True,
            }
        )
    with pytest.raises(ValueError, match="question parts"):
        export(trusted, native)
    set_field(native[0], "s001_targets", "Q1,Q2")
    assert export(trusted, native)["advancing_case_ids"] == ["synthetic"]


def v2_fixture():
    """Use trusted proposal anchors and no editable passage controls in v2."""
    trusted, native = fixture()
    for task in (trusted[0], native[0]):
        task["data"]["form_version"] = VERSION
        for claim in task["data"]["proposal"]["claims"]:
            claim["passage_ids"] = ["P1"]
    results = native[0]["annotations"][0]["result"]
    results[:] = [result for result in results if not result["from_name"].endswith("_passages")]
    return trusted, native


def test_v2_saved_edits_preserve_trusted_exact_source_spans():
    trusted, native = v2_fixture()
    set_field(native[0], "s001_text", "  The response conditionally asserts a revised result.\n")
    set_field(native[0], "s002_rationale", "The revised condition explains this direct claim.")
    result = export(trusted, native)
    direct, support = result["records"][0]["approved_claims"]
    assert result["schema_version"] == VERSION
    assert direct["text"] == "  The response conditionally asserts a revised result.\n"
    assert direct["passage_ids"] == ["P1"]
    assert direct["source_spans"] == trusted[0]["data"]["case_input"]["passages"]
    assert direct["source_binding_origin"] == "trusted_proposal"
    assert support["target_claim_version"] == direct["claim_version"]
    assert "passages" not in direct
    assert not any(name.endswith("_passages") for name in result["records"][0]["fields"])


@pytest.mark.parametrize("anchors", ["P1", "P999", ""])
def test_v2_injected_removed_passage_controls_are_rejected(anchors):
    trusted, native = v2_fixture()
    set_field(native[0], "s001_passages", anchors)
    with pytest.raises(ValueError, match="Unknown or duplicate native control"):
        export(trusted, native)


@pytest.mark.parametrize("state", ["unresolved", "stop"])
def test_v2_unbound_addition_cannot_advance_but_survives_holds(state):
    trusted, native = v2_fixture()
    for field, value in {
        "text": "An additional assertion needs source binding.",
        "relationship": "direct",
        "targets": "Q1",
        "decision": "approve",
    }.items():
        set_field(native[0], f"s003_{field}", value)
    with pytest.raises(ValueError, match="source-bound re-review"):
        export(trusted, native)
    set_field(native[0], "s003_decision", "unresolved")
    set_field(native[0], "case_status", state)
    set_field(native[0], "case_note", "New assertion requires source-bound re-review.")
    result = export(trusted, native)
    assert not result["advancing_case_ids"]
    addition = result["records"][0]["claims"][2]
    assert addition["decision"] == "unresolved"
    assert addition["source_binding_origin"] == "unbound_addition"
    assert addition["passage_ids"] == addition["source_spans"] == []


def test_mixed_form_versions_require_separate_exports():
    trusted, native = fixture()
    new_trusted, new_native = v2_fixture()
    new_trusted[0]["data"]["case_id"] = "second-synthetic"
    new_native[0]["data"]["case_id"] = "second-synthetic"
    with pytest.raises(ValueError, match="Mixed claim form versions"):
        export(trusted + new_trusted, native + new_native)
    assert export(trusted, native)["schema_version"] == LEGACY_VERSION


@pytest.mark.parametrize("anchors", [[], ["P999"], ["P1", "P1"], "P1", [None]])
def test_v2_invalid_trusted_anchors_fail_before_reading_decisions(anchors):
    trusted, native = v2_fixture()
    trusted[0]["data"]["proposal"]["claims"][0]["passage_ids"] = anchors
    with pytest.raises(ValueError, match="Invalid trusted proposal source passage anchors"):
        export(trusted, native)
