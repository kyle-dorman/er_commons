"""Separate invented saved-review checks for policy-aware Task08E intake and review."""

import copy
import json

import pytest
from test_group_claims_investigation import chain_fixture
from test_group_evidence import native

from er_commons import group_evidence_live as live
from er_commons.group_evidence_fixtures import prepare_qualification
from er_commons.group_ranking import digest, encoded


@pytest.fixture
def prepared(tmp_path):
    """Bind invented canonical inputs to live controls without dataset decisions."""
    root = tmp_path / "synthetic"
    tasks = prepare_qualification(root)
    for task in tasks:
        task["data"].update(
            interface_version=live.VERSION,
            qualification_only=False,
            upstream_handoff_sha256="f" * 64,
            upstream_case={
                "scope_unresolved": True,
                "question_parts": [{"part_id": "P1", "status": "unanswered"}],
            },
        )
    return tasks, root


def saved(task, **values):
    """Normalize an invented saved annotation preserving actual control bindings."""
    return live.normalize_claim(
        {**task, "id": 21}, native(**values), expected_task=task, export_lineage="fixture-v1"
    )


@pytest.mark.parametrize(
    "outcome,label",
    [("conflicting", "contradicts"), ("unresolved", "context"), ("no_support_found", "context")],
)
def test_non_supporting_evidence_can_reach_human_stop_or_unresolved(prepared, outcome, label):
    tasks, _ = prepared
    task = tasks[0]
    review = saved(
        task,
        c001_outcome=outcome,
        c001_note="Retain the unresolved scope.",
        c001_p01_label=label,
        c001_p01_note="Invented limitation.",
        source_summary="Edited summary",
    )
    assert review["review_complete"]
    gate = live.prepare_eligibility(
        task["data"]["case_label"],
        [review],
        required_table_members=[],
        expected_claim_ids=[review["claim_id"]],
        packet=task["data"]["packet"],
    )
    for disposition in ("stop", "unresolved"):
        result = live.normalize_eligibility(
            {**gate, "id": 21},
            native(
                disposition=disposition,
                table_usability="unresolved",
                reason="Human unresolved case judgment.",
            ),
            expected_task=gate,
            export_lineage="gate-v1",
        )
        assert result["human_decision"]["disposition"] == disposition
        assert result["advancing_claim_ids"] == []
        assert result["allowed_next_stage"] is None


def test_export_queue_capacity_holds_and_exact_bindings(prepared):
    tasks, root = prepared
    tasks = live.bind_project_capacity(tasks)
    exports = [
        {**copy.deepcopy(t), "id": i, "project": 7, "annotations": []}
        for i, t in enumerate(tasks, 1)
    ]
    kwargs = dict(
        expected_tasks=tasks,
        project_id=7,
        actual_form=live.claim_form(1),
        reviewer_id="synthetic-only",
        export_lineage="fixture-v1",
        data_root=root,
    )
    result = live.normalize_export(exports, **kwargs)
    assert result["pending_task_ids"] == list(range(1, 6))
    assert result["eligibility"] == "undecided"
    for mutation in ("project", "queue", "form", "source"):
        changed = copy.deepcopy(exports)
        options = dict(kwargs)
        if mutation == "project":
            changed[0]["project"] = 8
        elif mutation == "queue":
            changed.pop()
        elif mutation == "form":
            options["actual_form"] += "changed"
        else:
            changed[0]["data"]["upstream_case"]["scope_unresolved"] = False
        with pytest.raises(ValueError):
            live.normalize_export(changed, **options)


def test_eligibility_requires_saved_claim_closure_and_exact_evidence(prepared):
    tasks, _ = prepared
    task = tasks[1]
    review = saved(task, c001_outcome="supported", c001_p01_label="supports")
    kwargs = dict(
        required_table_members=["t1"],
        expected_claim_ids=[review["claim_id"]],
        packet=task["data"]["packet"],
    )
    with pytest.raises(ValueError):
        live.prepare_eligibility(review["case_id"], [], **kwargs)
    gate = live.prepare_eligibility(review["case_id"], [review], **kwargs)
    with pytest.raises(ValueError, match="Every required"):
        live.normalize_eligibility(
            {**gate, "id": 21},
            native(
                disposition="advance",
                reason="Explicit human decision",
                table_usability="verified_all_required_family_members",
                render_checks="",
            ),
            expected_task=gate,
            export_lineage="gate",
        )
    gate["data"]["reviews"][0]["source_summary"] = "Tampered"
    with pytest.raises(ValueError, match="bindings"):
        live.normalize_eligibility(
            {**gate, "id": 21},
            native(disposition="unresolved", reason="Hold", table_usability="unresolved"),
            expected_task=gate,
            export_lineage="gate",
        )


def test_intake_replays_version_bound_support_chain_and_rejects_stale_chain(tmp_path, monkeypatch):
    trusted, native_tasks = chain_fixture()
    from test_group_claims_export import set_field

    set_field(native_tasks[0], "gaps_status", "unresolved")
    native_raw = encoded(native_tasks)
    from er_commons.group_claims_export import normalize_export

    decisions = normalize_export(
        native_tasks,
        trusted,
        project_id=2,
        reviewer_id=4,
        export_sha256=digest(native_raw),
        policy_revision="task08d.investigation.v1",
    )
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    (prepared / "manifest.json").write_text("{}")
    monkeypatch.setattr(live.group_claims, "load_prepared", lambda _: trusted)
    approved = [
        {
            **claim,
            "case_id": case["case_id"],
            "question_id": case["question"]["question_id"],
            "question_version": case["question"]["question_version"],
            "question_text_sha256": case["question"]["text_sha256"],
            "packet_sha256": case["packet_sha256"],
            "proposal_sha256": case["proposal_sha256"],
        }
        for case in decisions["records"]
        for claim in case["approved_claims"]
    ]
    auth = {
        "native_export_sha256": digest(native_raw),
        "project_id": 2,
        "policy_revision": "task08d.investigation.v1",
    }
    handoff = {
        "status": "complete",
        "policy_revision": "task08d.investigation.v1",
        "advancement_scope": "08E_investigation_only",
        "eligibility": "undecided",
        "prepared": str(prepared),
        "prepared_manifest_sha256": digest((prepared / "manifest.json").read_bytes()),
        "authorization_sha256": digest(encoded(auth)),
        "project_id": 2,
        "reviewer_id": 4,
        "cases": decisions["records"],
        "advancing_case_ids": decisions["advancing_case_ids"],
        "approved_claims": approved,
    }
    payloads = {
        "handoff.json": encoded(handoff),
        "native_export.json": native_raw,
        "policy_authorization.json": encoded(auth),
        "decisions.json": encoded(decisions),
    }
    for name, raw in payloads.items():
        (tmp_path / name).write_bytes(raw)
    (tmp_path / "completion.json").write_bytes(
        encoded({"files": {name: digest(raw) for name, raw in payloads.items()}})
    )
    loaded = live.load_handoff(tmp_path / "handoff.json", digest(payloads["handoff.json"]))
    assert loaded["approved_claims"][2]["support_chain_versions"][-1]["claim_id"] == "A001"
    assert loaded["cases"][0]["scope_unresolved"]
    # A caller-approved hash cannot make altered chains match saved upstream work.
    handoff["approved_claims"][2]["support_chain_versions"][0]["claim_version"] = "stale"
    raw = encoded(handoff)
    (tmp_path / "handoff.json").write_bytes(raw)
    completion = json.loads((tmp_path / "completion.json").read_bytes())
    completion["files"]["handoff.json"] = digest(raw)
    (tmp_path / "completion.json").write_bytes(encoded(completion))
    with pytest.raises(ValueError, match="cases|claim closure"):
        live.load_handoff(tmp_path / "handoff.json", digest(raw))


def test_global_capacity_does_not_pad_case_candidates_or_accept_inactive_controls(prepared):
    tasks, root = prepared
    packet = copy.deepcopy(tasks[1]["data"]["packet"])
    extra = copy.deepcopy(tasks[0]["data"]["packet"]["candidates"][0])
    packet["candidates"].append(extra)
    packet["claim_candidates"][0]["candidate_ids"].append(extra["candidate_id"])
    context = packet["context"]
    wide = live.evidence.prepare_claim_tasks(
        packet,
        data_root=root,
        approved_review={
            "review_status": "approved",
            "case_label": packet["case_id"],
            "claims": packet["claims"],
            "evidence_candidate_claim_ids": [c["claim_id"] for c in packet["claims"]],
            "data": {
                "comment_html": context["comment_html"],
                "concerns_html": context["concerns_html"],
                "sources_html": context["response_html"],
            },
        },
    )[0]
    wide["data"].update(
        {
            key: tasks[1]["data"][key]
            for key in (
                "qualification_only",
                "interface_version",
                "upstream_case",
                "upstream_handoff_sha256",
            )
        }
    )
    mixed = live.bind_project_capacity([tasks[0], wide])
    assert [t["data"]["max_candidates"] for t in mixed] == [1, 2]
    assert [t["data"]["project_capacity"] for t in mixed] == [2, 2]
    assert mixed[0]["data"]["packet"] == tasks[0]["data"]["packet"]
    result = saved(mixed[0], c001_p01_label="supports", c001_outcome="supported")
    assert result["review_complete"]
    with pytest.raises(ValueError):
        saved(
            mixed[0], c001_p01_label="supports", c001_p02_label="supports", c001_outcome="supported"
        )


def test_exact_eligibility_project_export_does_not_advance(prepared):
    tasks, root = prepared
    task = tasks[0]
    review = saved(
        task, c001_outcome="unresolved", c001_note="No determination", c001_p01_label="context"
    )
    gate = live.prepare_eligibility(
        review["case_id"],
        [review],
        required_table_members=[],
        expected_claim_ids=[review["claim_id"]],
        packet=task["data"]["packet"],
    )
    expected = {**gate, "id": 21}
    annotation = native(
        disposition="unresolved", reason="Human unresolved judgment", table_usability="unresolved"
    )
    exported = [{**copy.deepcopy(gate), "id": 21, "project": 8, "annotations": [annotation]}]
    kwargs = dict(
        expected_tasks=[expected],
        project_id=8,
        actual_form=live.eligibility_form(),
        reviewer_id="synthetic-only",
        export_lineage="gate-v1",
        data_root=root,
        eligibility=True,
    )
    result = live.normalize_export(exported, **kwargs)
    assert result["eligibility"] == "human_review"
    assert result["records"][0]["human_decision"]["disposition"] == "unresolved"
    assert result["advancing_case_ids"] == [] and result["allowed_next_stage"] is None
    for mutation in ("project", "reviewer", "task", "form", "queue"):
        changed, options = copy.deepcopy(exported), dict(kwargs)
        if mutation == "project":
            changed[0]["project"] = 9
        elif mutation == "reviewer":
            changed[0]["annotations"][0]["completed_by"] = "another"
        elif mutation == "task":
            changed[0]["id"] = 22
        elif mutation == "form":
            options["actual_form"] = live.claim_form(1)
        else:
            changed = []
        with pytest.raises(ValueError):
            live.normalize_export(changed, **options)


def test_live_tasks_show_escaped_advisory_summaries_separately_from_source(prepared, monkeypatch):
    tasks, root = prepared
    packet = copy.deepcopy(tasks[0]["data"]["packet"])
    packet["candidates"][0]["source_summary"] = "Astra proposal <not a source quote>"
    packet["candidates"][0]["candidate_id"] = live.evidence.candidate_id(packet["candidates"][0])
    packet["claim_candidates"][0]["candidate_ids"] = [packet["candidates"][0]["candidate_id"]]
    case = {
        "case_id": packet["case_id"],
        "unresolved_question_parts": [{"part_id": "Q1", "status": "unanswered"}],
    }
    monkeypatch.setattr(
        live, "case_inputs", lambda handoff, case_id: (packet["claims"], packet["context"])
    )
    prepared_tasks = live.prepare_claim_tasks(packet, data_root=root, handoff={"cases": [case]})
    data = prepared_tasks[0]["data"]
    assert "Astra proposal &lt;not a source quote&gt;" in data["reviewer_notes_html"]
    assert "summaries — Astra, advisory" in data["reviewer_notes_html"]
    assert "Astra proposal" not in data["evidence_html"]
    assert "selected=" not in live.claim_form(data["max_candidates"])


def test_caller_cannot_omit_canonical_tables_from_human_render_gate(prepared):
    tasks, _ = prepared
    task = tasks[1]
    review = saved(task, c001_outcome="supported", c001_p01_label="supports")
    kwargs = dict(expected_claim_ids=[review["claim_id"]], packet=task["data"]["packet"])
    with pytest.raises(ValueError, match="Required table members"):
        live.prepare_eligibility(review["case_id"], [review], required_table_members=[], **kwargs)
    gate = live.prepare_eligibility(
        review["case_id"], [review], required_table_members=["t1"], **kwargs
    )
    gate["data"]["required_table_members"] = []
    with pytest.raises(ValueError, match="Required table members"):
        live.normalize_eligibility(
            {**gate, "id": 21},
            native(
                disposition="advance",
                reason="Explicit human decision",
                table_usability="not_required",
            ),
            expected_task=gate,
            export_lineage="gate-v1",
        )


def test_export_validates_each_distinct_packet_once_per_call(prepared, monkeypatch):
    tasks, root = prepared
    first = copy.deepcopy(tasks[0])
    repeat = copy.deepcopy(first)
    repeat["data"]["claim_task_id"] += "-second-claim"
    second = copy.deepcopy(tasks[1])
    expected = live.bind_project_capacity([first, repeat, second])
    exported = [
        {**copy.deepcopy(t), "id": i, "project": 7, "annotations": []}
        for i, t in enumerate(expected, 1)
    ]
    calls = []
    validator = live.evidence.validate_candidates

    def checked(packet, data_root):
        """Record real source validation without bypassing any canonical check."""
        calls.append(live.evidence.digest(packet))
        validator(packet, data_root)

    monkeypatch.setattr(live.evidence, "validate_candidates", checked)
    kwargs = dict(
        expected_tasks=expected,
        project_id=7,
        actual_form=live.claim_form(1),
        reviewer_id="synthetic-only",
        export_lineage="fixture-v1",
        data_root=root,
    )
    live.normalize_export(exported, **kwargs)
    assert len(calls) == 2 and len(set(calls)) == 2
    live.normalize_export(exported, **kwargs)
    assert len(calls) == 4  # No cache survives a later export.
    changed = copy.deepcopy(expected)
    changed[1]["data"]["packet"]["candidates"][0]["anchors"][0]["record"]["canonical_text"] = (
        "tampered"
    )
    kwargs["expected_tasks"] = changed
    exported[1]["data"] = copy.deepcopy(changed[1]["data"])
    with pytest.raises(ValueError):
        live.normalize_export(exported, **kwargs)
    assert len(calls) == 6  # Distinct altered packet reaches canonical validation.
