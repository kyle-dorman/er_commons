"""Qualify the explicit 2026-10-01 saved-selection closeout amendment."""

import copy
from typing import Any

import pytest
from test_group_selection_export import annotate, fixtures

from er_commons.group_selection_closeout import (
    FINISH_VERSION,
    POLICY,
    PROCESS_REVISION,
    normalize_closeout_export,
)
from er_commons.group_selection_export import VERSION


def confirmation() -> dict[str, Any]:
    """Bind the actual policy authorization to a synthetic export."""
    return {
        "schema_version": FINISH_VERSION,
        "process_revision": PROCESS_REVISION,
        "template_version": VERSION,
        "project_id": 10,
        "group": "fixture",
        "input_sha256": "a" * 64,
        "proposal_sha256": "b" * 64,
        "export_sha256": "c" * 64,
        "finished": True,
        **POLICY,
        "reviewer": "Synthetic reviewer",
        "confirmed_at": "2026-10-01T12:00:00-07:00",
        "chat_reference": "synthetic:closeout",
        "statement": "All groups finished; keep all saved Selected, including more than three.",
    }


def normalize(expected: list[dict[str, Any]], native: list[dict[str, Any]]) -> dict[str, Any]:
    """Normalize under an explicit export-bound policy confirmation."""
    return normalize_closeout_export(
        native, expected, project_id=10, export_sha256="c" * 64, finish_confirmation=confirmation()
    )


def test_more_than_three_saved_selections_preserve_order_without_mutating_inputs() -> None:
    expected, native = fixtures(5)
    for task in native:
        annotate(task)
    before = copy.deepcopy(native)
    output = normalize(expected, list(reversed(native)))
    assert output["status"] == "complete"
    assert (
        output["selected_comment_ids"]
        == output["advancing_comment_ids"]
        == ["c1", "c2", "c3", "c4", "c5"]
    )
    assert output["counts"]["selected"] == 5
    assert native == before


def test_skips_drafts_and_unanswered_preserve_distinct_states_and_do_not_block() -> None:
    expected, native = fixtures(6)
    annotate(native[0])
    annotate(native[1])
    native[1]["annotations"][0]["was_cancelled"] = True
    native[2]["drafts"] = [{"id": 22, "result": []}]
    annotate(native[4], selection="Reviewed skip")
    annotate(native[5], selection="Excluded")
    output = normalize(expected, native)
    assert output["status"] == "complete"
    assert output["selected_comment_ids"] == ["c1"]
    assert [record["state"] for record in output["records"]] == [
        "reviewed",
        "native_skipped",
        "draft_only",
        "unreviewed",
        "reviewed",
        "reviewed",
    ]
    assert output["counts"]["native_skipped"] == 1
    assert output["counts"]["draft_only"] == 1
    assert output["counts"]["reviewed_skips"] == 1
    assert output["counts"]["excluded"] == 1
    assert output["untouched_comment_ids"] == ["c4"]
    assert output["native_tasks"] == native


def test_saved_selected_authoritative_with_draft_and_cancelled_history() -> None:
    expected, native = fixtures(1)
    annotate(native[0])
    cancelled = copy.deepcopy(native[0]["annotations"][0])
    cancelled.update(id=200, was_cancelled=True)
    native[0]["annotations"].insert(0, cancelled)
    native[0]["drafts"] = [{"id": 25, "result": [{"unsaved": "Excluded"}]}]
    output = normalize(expected, native)
    assert output["advancing_comment_ids"] == ["c1"]
    assert output["records"][0]["saved_decision_with_draft"] is True
    assert output["records"][0]["cancelled_annotation_ids"] == [200]
    assert output["records"][0]["provenance"]["annotation_id"] == 101
    native[0]["drafts"].clear()
    assert output["native_tasks"][0]["drafts"]


def test_draft_selected_never_becomes_a_label() -> None:
    expected, native = fixtures(1)
    annotate(native[0])
    native[0]["drafts"] = native[0].pop("annotations")
    native[0]["annotations"] = []
    output = normalize(expected, native)
    assert output["advancing_comment_ids"] == []
    assert output["records"][0]["state"] == "draft_only"
    assert output["records"][0]["decision"] is None


def test_no_confirmation_never_advances() -> None:
    expected, native = fixtures(4)
    for task in native:
        annotate(task)
    output = normalize_closeout_export(native, expected, project_id=10, export_sha256="c" * 64)
    assert output["counts"]["selected"] == 4
    assert output["advancing_comment_ids"] == []
    assert output["status"] == "awaiting_finish_confirmation"


@pytest.mark.parametrize(
    "change", ["source", "missing", "duplicate", "task", "project", "predictions"]
)
def test_full_inventory_and_source_binding_fail_closed(change: str) -> None:
    expected, native = fixtures(2)
    if change == "source":
        native[0]["data"]["complete_source"] = "Truncated"
    elif change == "missing":
        native.pop()
    elif change == "duplicate":
        native.append(copy.deepcopy(native[0]))
    elif change == "task":
        native[1]["id"] = native[0]["id"]
    elif change == "project":
        native[0]["project"] = 11
    else:
        native[0]["predictions"] = [{"result": []}]
    with pytest.raises(ValueError):
        normalize(expected, native)


@pytest.mark.parametrize(
    "change",
    ["multiple_saved", "no_reason", "task", "reviewer", "timestamp", "flag", "duplicate_id"],
)
def test_saved_decisions_remain_strict(change: str) -> None:
    expected, native = fixtures(1)
    annotate(native[0])
    annotation = native[0]["annotations"][0]
    if change == "multiple_saved":
        native[0]["annotations"].append({**annotation, "id": 300})
    elif change == "no_reason":
        annotation["result"].pop()
    elif change == "task":
        annotation["task"] = 200
    elif change == "reviewer":
        annotation["completed_by"] = None
    elif change == "timestamp":
        annotation["updated_at"] = "2026-10-01"
    elif change == "flag":
        annotation["was_cancelled"] = "false"
    else:
        native[0]["annotations"].append({**annotation, "was_cancelled": True})
    with pytest.raises(ValueError):
        normalize(expected, native)


@pytest.mark.parametrize(
    "key,value",
    [
        ("export_sha256", "d" * 64),
        ("group", "foreign"),
        ("selection_limit", 3),
        ("saved_selected_authoritative", False),
        ("native_skips_close_review", False),
        ("process_revision", "task08.selection_gate.v2"),
        ("finished", False),
        ("statement", ""),
        ("confirmed_at", "2026-10-01"),
        ("extra", True),
    ],
)
def test_exact_export_and_policy_authorization(key: str, value: Any) -> None:
    expected, native = fixtures(1)
    finish = confirmation()
    finish[key] = value
    with pytest.raises(ValueError):
        normalize_closeout_export(
            native, expected, project_id=10, export_sha256="c" * 64, finish_confirmation=finish
        )


@pytest.mark.parametrize("selection", ["Excluded", "Reviewed skip", "Unresolved"])
@pytest.mark.parametrize("notes", [None, " "])
def test_nonselected_other_missing_notes_are_preserved_with_diagnostic(
    selection: str, notes: str | None
) -> None:
    """Observed native nonselected decisions remain exportable without fake notes."""
    expected, native = fixtures(1)
    annotate(native[0], selection=selection, selection_reason="Other")
    if notes is not None:
        annotate(native[0], selection=selection, selection_reason="Other", notes=notes)
    before = copy.deepcopy(native)
    output = normalize(expected, native)
    record = output["records"][0]
    assert output["status"] == "complete"
    assert output["selected_comment_ids"] == []
    assert record["decision"]["selection"] == selection
    assert record["decision"]["selection_reason"] == "Other"
    assert record["decision"].get("notes") == notes
    assert record["validation_notes"] == ["nonselected_other_reason_without_explanatory_notes"]
    assert output["native_tasks"] == before == native


@pytest.mark.parametrize("selection", ["Selected", "Excluded", "Reviewed skip"])
def test_other_never_bypasses_controls_or_reviewer_validation(selection: str) -> None:
    """Diagnostic acceptance cannot mask malformed controls or reviewer provenance."""
    expected, native = fixtures(1)
    annotate(native[0], selection=selection, selection_reason="Other")
    native[0]["annotations"][0]["completed_by"] = None
    with pytest.raises(ValueError, match="Reviewer id"):
        normalize(expected, native)
    native[0]["annotations"][0]["completed_by"] = 2
    native[0]["annotations"][0]["result"][0]["to_name"] = "foreign"
    with pytest.raises(ValueError, match="Foreign native control"):
        normalize(expected, native)


def test_selected_other_without_notes_still_fails() -> None:
    """Only complete valid Selected decisions may advance."""
    expected, native = fixtures(1)
    annotate(native[0], selection_reason="Other")
    with pytest.raises(ValueError, match="Other requires nonblank"):
        normalize(expected, native)
