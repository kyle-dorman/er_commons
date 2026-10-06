"""Independent negative export checks for source-free Task08E qualification."""

import copy
from pathlib import Path

import pytest

from er_commons import group_evidence as review
from er_commons import pilot_evidence
from er_commons.group_evidence_fixtures import prepare_qualification


def native(**values):
    """Build separate synthetic annotations using actual native field bindings."""
    result = []
    for name, value in values.items():
        text = name in {"c001_note", "c001_p01_note", "source_summary", "reason", "render_checks"}
        result.append(
            {
                "from_name": name,
                "to_name": "eligibility"
                if name in {"disposition", "table_usability", "reason", "render_checks"}
                else "evidence",
                "type": "textarea" if text else "choices",
                "value": {"text" if text else "choices": [value]},
            }
        )
    return {"id": 11, "task": 21, "completed_by": "synthetic-only", "result": result}


@pytest.fixture
def setup(tmp_path: Path):
    """Prepare ordinary canonical units through maintained current validation."""
    return prepare_qualification(tmp_path / "fixtures"), tmp_path / "fixtures"


def normalize(task, **values):
    """Normalize against the original prepared task."""
    return review.normalize_claim(
        {**task, "id": 21},
        native(**values),
        expected_task=task,
        export_lineage="synthetic-export-1",
    )


def test_current_units_summary_edit_and_no_defaults(setup):
    tasks, root = setup
    assert {t["data"]["packet"]["candidates"][0]["citation_unit"]["kind"] for t in tasks} == {
        "section",
        "table",
    }
    for task in tasks:
        pilot_evidence.validate_candidates(task["data"]["packet"], root)
    saved = normalize(
        tasks[0],
        c001_p01_label="supports",
        c001_outcome="supported",
        source_summary="Edited curator wording",
    )
    assert saved["source_summary"] == "Edited curator wording"
    assert "selected=" not in review.claim_form(1) + review.eligibility_form()
    assert (
        tasks[0]["data"]["packet"]["claims"][0]["text"]
        == "The fictional container holds ten units."
    )


@pytest.mark.parametrize(
    "mutation", ["anchor", "table_cell", "task", "unknown", "empty", "context_support"]
)
def test_independent_export_rejections(setup, mutation):
    tasks, root = setup
    task = copy.deepcopy(tasks[1] if mutation == "table_cell" else tasks[0])
    if mutation in {"anchor", "table_cell"}:
        packet = task["data"]["packet"]
        packet["candidates"][0]["anchors"].pop()
        with pytest.raises(ValueError):
            pilot_evidence.validate_candidates(packet, root)
        return
    values = {"c001_p01_label": "supports", "c001_outcome": "supported"}
    if mutation == "task":
        task["data"]["question_version"] = "tampered"
    elif mutation == "unknown":
        values["foreign"] = "x"
    elif mutation == "empty":
        values = {}
    else:
        values["c001_p01_label"] = "context"
    if mutation in {"empty", "context_support"}:
        held = review.normalize_claim(
            {**task, "id": 21}, native(**values), expected_task=tasks[0], export_lineage="synthetic"
        )
        assert not held["review_complete"] and held["validation_errors"]
        return
    with pytest.raises(ValueError):
        review.normalize_claim(
            {**task, "id": 21}, native(**values), expected_task=tasks[0], export_lineage="synthetic"
        )


def test_eligibility_closure_family_checks_and_qualification_segregation(setup):
    task = setup[0][1]
    saved = normalize(task, c001_p01_label="supports", c001_outcome="supported")
    claim_ids = [saved["claim_id"]]
    with pytest.raises(ValueError, match="queue"):
        review.prepare_eligibility(
            saved["case_id"],
            [saved],
            required_table_members=[],
            expected_claim_ids=claim_ids + ["missing"],
            packet=task["data"]["packet"],
        )
    gate = review.prepare_eligibility(
        saved["case_id"],
        [saved],
        required_table_members=["t1"],
        expected_claim_ids=claim_ids,
        packet=task["data"]["packet"],
    )
    fields = dict(
        disposition="advance",
        table_usability="verified_all_required_family_members",
        reason="Synthetic human gate",
        render_checks="t1",
    )
    exported = review.normalize_eligibility(
        {**gate, "id": 21}, native(**fields), expected_task=gate, export_lineage="synthetic"
    )
    assert exported["synthetic_disposition"] == "advance"
    assert exported["advancing_claim_ids"] == []
    for field, value in [
        ("render_checks", "other"),
        ("reason", ""),
        ("table_usability", "not_required"),
    ]:
        with pytest.raises(ValueError):
            review.normalize_eligibility(
                {**gate, "id": 21},
                native(**{**fields, field: value}),
                expected_task=gate,
                export_lineage="synthetic",
            )


@pytest.mark.parametrize("disposition", ["stop", "unresolved"])
def test_unresolved_preserved_without_advancement(setup, disposition):
    task = setup[0][2]
    saved = normalize(
        task,
        c001_p01_label="context",
        c001_outcome="unresolved",
        c001_note="Synthetic unresolved condition",
    )
    gate = review.prepare_eligibility(
        saved["case_id"],
        [saved],
        required_table_members=[],
        expected_claim_ids=[saved["claim_id"]],
        packet=task["data"]["packet"],
    )
    fields = dict(disposition=disposition, table_usability="unresolved", reason="Needs human work")
    result = review.normalize_eligibility(
        {**gate, "id": 21}, native(**fields), expected_task=gate, export_lineage="synthetic"
    )
    assert result["advancing_claim_ids"] == []
    with pytest.raises(ValueError, match="unsupported"):
        review.normalize_eligibility(
            {**gate, "id": 21},
            native(**{**fields, "disposition": "advance"}),
            expected_task=gate,
            export_lineage="synthetic",
        )


def test_native_export_exact_queue_project_form_reviewer_and_holds(setup):
    tasks, _ = setup
    exported = [
        {**task, "id": 21 + i, "project": 81, "annotations": []} for i, task in enumerate(tasks)
    ]
    exported[0]["annotations"] = [native(c001_p01_label="supports", c001_outcome="supported")]
    kwargs = dict(
        data_root=setup[1],
        expected_tasks=tasks,
        project_id=81,
        actual_form=review.claim_form(1),
        reviewer_id="synthetic-only",
        export_lineage="synthetic",
    )
    result = review.normalize_export(exported, **kwargs)
    assert result["pending_task_ids"] == [22, 23, 24, 25]
    assert result["advancing_claim_ids"] == []
    for field, value in [("project_id", 82), ("actual_form", "tampered"), ("reviewer_id", "other")]:
        with pytest.raises(ValueError):
            review.normalize_export(exported, **{**kwargs, field: value})
    with pytest.raises(ValueError, match="Missing"):
        review.normalize_export(exported[:-1], **kwargs)
    held = normalize(tasks[0])
    gate = review.prepare_eligibility(
        held["case_id"],
        [held],
        required_table_members=[],
        expected_claim_ids=[held["claim_id"]],
        packet=tasks[0]["data"]["packet"],
    )
    result = review.normalize_eligibility(
        {**gate, "id": 21},
        native(disposition="unresolved", reason="Incomplete fixture", table_usability="unresolved"),
        expected_task=gate,
        export_lineage="synthetic",
    )
    assert result["advancing_claim_ids"] == []


def test_extended_zero_shared_roles_aggregation_and_long_edit(tmp_path):
    from er_commons.group_evidence_fixtures import prepare_extended_qualification
    from er_commons.pilot_case_citations import aggregate_case_citations

    tasks = prepare_extended_qualification(tmp_path / "extended")
    assert len(tasks) == 4
    zero = normalize(tasks[0], c001_outcome="unresolved", c001_note="No hits within budget")
    assert zero["review_complete"] and zero["claim_review"]["pairs"] == []
    support = normalize(tasks[1], c001_p01_label="supports", c001_outcome="supported")
    context = normalize(
        tasks[2],
        c001_p01_label="context",
        c001_outcome="unresolved",
        c001_note="Context alone cannot support this claim",
    )
    aggregated = aggregate_case_citations(tasks[1]["data"]["packet"], [support, context])
    assert len(aggregated["citations"]) == 1
    assert aggregated["citations"][0]["level"] == "support"
    assert len(aggregated["audit"]["citation_decisions"][0]["judgments"]) == 2
    long_edit = "Edited synthetic summary with explicit limits. " * 150
    edited = normalize(
        tasks[3], c001_p01_label="supports", c001_outcome="supported", source_summary=long_edit
    )
    assert edited["source_summary"] == long_edit
    partial = normalize(
        tasks[1],
        c001_p01_label="partial",
        c001_p01_note="Some units; gap remains",
        c001_outcome="partial",
        c001_note="Some units; gap remains",
    )
    with pytest.raises(ValueError, match="Partial-only"):
        aggregate_case_citations(tasks[1]["data"]["packet"], [partial, context])


def test_canonical_bytes_revalidated_at_export(setup):
    tasks, root = setup
    expected = [tasks[0]]
    exported = [{**tasks[0], "id": 21, "project": 81, "annotations": []}]
    canonical = root / "fixture1/blocks.jsonl"
    canonical.write_text(canonical.read_text().replace("ten units", "eleven units"))
    with pytest.raises(ValueError):
        review.normalize_export(
            exported,
            expected_tasks=expected,
            project_id=81,
            actual_form=review.claim_form(1),
            reviewer_id="synthetic-only",
            export_lineage="synthetic",
            data_root=root,
        )
