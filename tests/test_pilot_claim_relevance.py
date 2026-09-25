"""Exercise combined relevance semantics, edit provenance, and partial/overflow preservation."""

import copy
import hashlib
import json

import pytest
from test_pilot_claims import packet  # noqa: F401

from er_commons import pilot_claim_relevance as review


@pytest.fixture
def combined(packet, tmp_path):  # noqa: F811
    """Bind a new proposal to the independent original packet fixture."""
    prior_task = review.pilot_claims.build_trial_task(*packet)
    prior = tmp_path / "prior_review.json"
    prior.write_text(
        json.dumps(
            {
                "case_label": "case",
                "review_status": "approved",
                "input_sha256": prior_task["data"]["input_sha256"],
            }
        )
    )
    proposal = {
        "schema_version": "er_commons.task07c1.proposal.v1",
        "proposal_id": "new-proposal",
        "case_label": "case",
        "input_sha256": prior_task["data"]["input_sha256"],
        "packet_manifest_sha256": prior_task["data"]["packet_manifest_sha256"],
        "predecessor_review": {
            "path": str(prior),
            "sha256": hashlib.sha256(prior.read_bytes()).hexdigest(),
        },
        "claims": [
            {
                "claim_id": "durable-one",
                "local_id": "C001",
                "text": "Qualified claim.",
                "relationship": "direct",
                "concern_ids": ["Q1"],
                "supporting_claim_ids": [],
                "rationale": "Addresses the concern.",
                "prior_edit_note": "Fresh proposal.",
                "source_refs": [{"passage_id": "R01-P01", "quote": "May apply"}],
            },
            {
                "claim_id": "durable-two",
                "local_id": "C002",
                "text": "Supporting claim.",
                "relationship": "supporting",
                "concern_ids": [],
                "supporting_claim_ids": ["durable-one"],
                "rationale": "Supplies reasoning.",
                "prior_edit_note": "Fresh proposal.",
                "source_refs": [{"passage_id": "R02-P01", "quote": "Another qualified claim."}],
            },
        ],
        "coverage": [
            {
                "passage_id": "R01-P01",
                "entries": [
                    {"kind": "claim", "claim_ids": ["durable-one"], "note": "Complete argument."}
                ],
            },
            {
                "passage_id": "R02-P01",
                "entries": [
                    {"kind": "claim", "claim_ids": ["durable-two"], "note": "Complete argument."}
                ],
            },
        ],
    }
    path = tmp_path / "combined_proposal.json"
    path.write_text(json.dumps(proposal))
    return (*packet, path)


def annotation(task, status="approved"):
    """Create explicit QA review values without modifying model suggestions."""
    return {
        "id": 42,
        "task": 7,
        "completed_by": 3,
        "result": [
            *copy.deepcopy(task["predictions"][0]["result"]),
            review._result("review_status", status, choices=True),
        ],
    }


def change(saved, name, value, *, choices=False):
    """Replace one native QA field while keeping all others intact."""
    saved["result"] = [r for r in saved["result"] if r["from_name"] != name]
    if value is not None:
        saved["result"].append(review._result(name, value, choices=choices))


def normalize(task, saved):
    """Use an independently held trusted task for normalization."""
    return review.normalize_review(
        {"id": 7, **task}, saved, expected_task=task, export_lineage="qa"
    )


def test_blank_slots_and_explicit_status(combined):
    task = review.build_trial_task(*combined)
    assert task["data"]["slot_count"] == 6
    assert all(not r["from_name"].startswith("s003") for r in task["predictions"][0]["result"])
    assert not any(r["from_name"] == "review_status" for r in task["predictions"][0]["result"])
    result = normalize(task, annotation(task))
    assert len(result["claims"]) == 2
    assert result["whole_case_ready"]
    assert result["evidence_candidate_claim_ids"] == ["durable-one", "durable-two"]


def test_edit_add_remove_preserve_identity_and_original(combined):
    task = review.build_trial_task(*combined)
    saved = annotation(task)
    change(saved, "s001_text", "Edited wording with qualification.")
    change(saved, "s002_remove", "remove", choices=True)
    change(saved, "s003_text", "New unrelated assertion.")
    change(saved, "s003_passages", "R02-P01")
    change(saved, "s003_relationship", "not_relevant", choices=True)
    result = normalize(task, saved)
    assert result["claims"][0]["claim_id"] == "durable-one"
    assert result["removed_claims"][0]["saved_fields"]["text"] == "Supporting claim."
    assert len(result["added_claim_ids"]) == 1
    assert result["data"]["original_proposal"]["claims"][0]["text"] == "Qualified claim."
    assert result["evidence_candidate_claim_ids"] == ["durable-one"]
    assert result["native_annotation"] == saved


@pytest.mark.parametrize("target", ["C002", "C999", "C003"])
def test_dangling_self_and_empty_targets_fail(combined, target):
    task = review.build_trial_task(*combined)
    saved = annotation(task)
    change(saved, "s002_targets", target)
    with pytest.raises(ValueError):
        normalize(task, saved)


def test_removed_target_invalidates_supporting_claim(combined):
    task = review.build_trial_task(*combined)
    saved = annotation(task)
    change(saved, "s001_remove", "remove", choices=True)
    with pytest.raises(ValueError, match="supporting path"):
        normalize(task, saved)


def test_cycle_and_chain(combined):
    task = review.build_trial_task(*combined)
    saved = annotation(task)
    change(saved, "s003_text", "Indirect supporting assertion.")
    change(saved, "s003_passages", "R02-P01")
    change(saved, "s003_relationship", "supporting", choices=True)
    change(saved, "s003_targets", "C002")
    assert len(normalize(task, saved)["claims"]) == 3
    change(saved, "s001_relationship", "supporting", choices=True)
    change(saved, "s001_targets", "C003")
    with pytest.raises(ValueError, match="circular"):
        normalize(task, saved)


def test_unclear_claim_can_be_approved_but_is_held(combined):
    task = review.build_trial_task(*combined)
    saved = annotation(task)
    change(saved, "s002_relationship", "unclear", choices=True)
    change(saved, "s002_targets", None)
    result = normalize(task, saved)
    assert result["review_status"] == "approved"
    assert result["held_claim_ids"] == ["durable-two"]
    assert result["evidence_candidate_claim_ids"] == ["durable-one"]
    assert not result["whole_case_ready"]


def test_partial_retains_valid_claim_and_invalid_raw_work(combined):
    task = review.build_trial_task(*combined)
    saved = annotation(task, "needs_context")
    change(saved, "s002_relationship", None)
    result = normalize(task, saved)
    assert len(result["claims"]) == 1
    assert result["validation_errors"]
    assert result["native_annotation"] == saved
    assert not result["evidence_candidate_claim_ids"]
    change(saved, "review_status", "approved", choices=True)
    with pytest.raises(ValueError, match="missing relationship"):
        normalize(task, saved)


def test_empty_approval_rejected(combined):
    task = review.build_trial_task(*combined)
    saved = annotation(task)
    for slot in ("s001", "s002"):
        change(saved, f"{slot}_remove", "remove", choices=True)
    with pytest.raises(ValueError, match="at least one"):
        normalize(task, saved)


@pytest.mark.parametrize("mutation", ["quote", "coverage", "prior_hash", "input_hash", "cycle"])
def test_proposal_integrity(combined, mutation):
    path = combined[2]
    proposal = json.loads(path.read_text())
    if mutation == "quote":
        proposal["claims"][0]["source_refs"][0]["quote"] = "Invented words"
    elif mutation == "coverage":
        proposal["coverage"].pop()
    elif mutation == "prior_hash":
        proposal["predecessor_review"]["sha256"] = "bad"
    elif mutation == "input_hash":
        proposal["input_sha256"] = "bad"
    else:
        proposal["claims"][0].update(
            relationship="supporting", concern_ids=[], supporting_claim_ids=["durable-two"]
        )
    path.write_text(json.dumps(proposal))
    with pytest.raises(ValueError):
        review.build_trial_task(*combined)


def test_overflow_preserves_every_old_identity_and_human_field(combined):
    task = review.build_trial_task(*combined)
    saved = annotation(task, "needs_context")
    change(saved, "s001_text", "Preserve this edit verbatim.\nSecond paragraph.")
    before = copy.deepcopy(task)
    expanded = review.expand_task({"id": 7, **task}, 10, saved)
    assert task == before
    assert expanded["data"]["slot_bindings"][:6] == task["data"]["slot_bindings"]
    for key, value in task["data"].items():
        if key not in {"slot_count", "slot_bindings"}:
            assert expanded["data"][key] == value
    assert expanded["migration"]["native_annotation"] == saved
    assert expanded["predictions"] == task["predictions"]
    assert "id" not in expanded
    assert len({b["claim_id"] for b in expanded["data"]["slot_bindings"]}) == 10


@pytest.mark.parametrize(
    "mutation", ["field", "duplicate", "binding", "task", "reviewer", "tamper"]
)
def test_foreign_annotation_boundaries(combined, mutation):
    task = review.build_trial_task(*combined)
    saved = annotation(task)
    if mutation == "field":
        saved["result"].append(review._result("untrusted", "value"))
    elif mutation == "duplicate":
        saved["result"].append(saved["result"][0])
    elif mutation == "binding":
        saved["result"][0]["to_name"] = "foreign"
    elif mutation == "task":
        saved["task"] = 99
    elif mutation == "reviewer":
        del saved["completed_by"]
    else:
        exported = copy.deepcopy(task)
        exported["data"]["case_label"] = "foreign"
        with pytest.raises(ValueError, match="differs"):
            review.normalize_review(
                {"id": 7, **exported}, saved, expected_task=task, export_lineage="qa"
            )
        return
    with pytest.raises(ValueError):
        normalize(task, saved)


def test_multiple_distinct_quotes_in_same_passage(combined):
    path = combined[2]
    proposal = json.loads(path.read_text())
    proposal["claims"][0]["source_refs"].append({"passage_id": "R01-P01", "quote": "only here."})
    proposal["warnings"] = ["Preserve <qualified> uncertainty."]
    path.write_text(json.dumps(proposal))
    task = review.build_trial_task(*combined)
    refs = [r for r in task["predictions"][0]["result"] if r["from_name"] == "s001_passages"]
    assert refs[0]["value"]["text"] == ["R01-P01"]
    assert "Preserve &lt;qualified&gt; uncertainty." in task["data"]["warnings_html"]
    assert normalize(task, annotation(task))["whole_case_ready"]


def test_predecessor_list_and_foreign_migration(combined):
    path = combined[2]
    proposal = json.loads(path.read_text())
    prior = review.Path(proposal["predecessor_review"]["path"])
    old = json.loads(prior.read_text())
    prior.write_text(json.dumps([old, {"case_label": "other"}]))
    proposal["predecessor_review"]["sha256"] = hashlib.sha256(prior.read_bytes()).hexdigest()
    path.write_text(json.dumps(proposal))
    task = review.build_trial_task(*combined)
    saved = annotation(task)
    saved["task"] = 99
    with pytest.raises(ValueError, match="Foreign migration"):
        review.expand_task({"id": 7, **task}, 10, saved)


@pytest.mark.parametrize("mutation", ["foreign", "absent"])
def test_proposal_case_identity_required(combined, mutation):
    path = combined[2]
    proposal = json.loads(path.read_text())
    if mutation == "foreign":
        proposal["case_label"] = "other-case"
    else:
        del proposal["case_label"]
    path.write_text(json.dumps(proposal))
    with pytest.raises(ValueError, match="Proposal case identity"):
        review.build_trial_task(*combined)


@pytest.mark.parametrize("identity", ["task_id", "annotation_id", "reviewer"])
def test_declared_predecessor_identity_checked(combined, identity):
    path = combined[2]
    proposal = json.loads(path.read_text())
    prior_path = review.Path(proposal["predecessor_review"]["path"])
    prior = json.loads(prior_path.read_text())
    prior[identity] = 123
    prior_path.write_text(json.dumps(prior))
    proposal["predecessor_review"]["sha256"] = hashlib.sha256(prior_path.read_bytes()).hexdigest()
    proposal["predecessor_review"][identity] = 123
    path.write_text(json.dumps(proposal))
    review.build_trial_task(*combined)
    proposal["predecessor_review"][identity] = 456
    path.write_text(json.dumps(proposal))
    with pytest.raises(ValueError, match=f"{identity} identity mismatch"):
        review.build_trial_task(*combined)


@pytest.mark.parametrize("mutation", ["unaccounted", "foreign_passage"])
def test_inventory_claim_and_passage_accounting(combined, mutation):
    path = combined[2]
    proposal = json.loads(path.read_text())
    entry = proposal["coverage"][1]["entries"][0]
    if mutation == "unaccounted":
        entry.update(kind="non_substantive", claim_ids=[], note="Incorrect exclusion.")
        message = "every proposal claim"
    else:
        entry["claim_ids"] = ["durable-one", "durable-two"]
        message = "not bound to this passage"
    path.write_text(json.dumps(proposal))
    with pytest.raises(ValueError, match=message):
        review.build_trial_task(*combined)


def test_readable_coverage_preserves_raw_identity_inventory(combined):
    path = combined[2]
    proposal = json.loads(path.read_text())
    proposal["coverage"][1]["entries"][0]["kind"] = "repetition"
    proposal["coverage"][1]["entries"].append(
        {"kind": "non_substantive", "claim_ids": [], "note": "Header <context>."}
    )
    path.write_text(json.dumps(proposal))
    task = review.build_trial_task(*combined)
    displayed = task["data"]["coverage_html"]
    assert "R01-P01" in displayed and "C001" in displayed
    assert "Repeated argument" in displayed and "Source context" in displayed
    assert "Header &lt;context&gt;." in displayed
    assert "durable-one" not in displayed
    assert task["data"]["original_proposal"]["coverage"] == proposal["coverage"]


def test_historical_relevance_policy_hidden_only_from_display(combined, monkeypatch):
    original_builder = review.pilot_claims.build_trial_task
    warning = "Read the full text but extract only relevant claims and necessary context."

    def source_with_warning(*args):
        task = original_builder(*args)
        task["data"]["claim_input"]["warnings"].append(warning)
        task["data"]["warnings_html"] += f"<li>{warning}</li>"
        return task

    monkeypatch.setattr(review.pilot_claims, "build_trial_task", source_with_warning)
    task = review.build_trial_task(*combined)
    assert warning in task["data"]["claim_input"]["warnings"]
    assert warning not in task["data"]["warnings_html"]
    assert "Not facts." in task["data"]["warnings_html"]
    assert "Retain all substantive response claims" in task["data"]["warnings_html"]


def test_removal_on_unused_slot_does_not_invent_deleted_claim(combined):
    """Preserve a blank-slot removal click separately from substantive deletions."""
    task = review.build_trial_task(*combined)
    saved = annotation(task)
    change(saved, "s003_remove", "remove", choices=True)
    change(saved, "s003_relationship", "not_relevant", choices=True)
    result = normalize(task, saved)
    assert len(result["claims"]) == 2
    assert not result["removed_claims"]
    assert not result["added_claim_ids"]
    assert result["unused_slot_removals"][0]["local_id"] == "C003"
    assert result["native_annotation"] == saved
    change(saved, "s003_text", "An added claim subsequently removed.")
    result = normalize(task, saved)
    assert not result["unused_slot_removals"]
    assert result["removed_claims"][0]["saved_fields"]["text"] == (
        "An added claim subsequently removed."
    )
