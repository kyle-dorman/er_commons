"""Exercise human-decision preservation and fail-closed selection export checks."""

import copy
from typing import Any

import pytest

from er_commons.group_selection_export import PROCESS_REVISION, VERSION, normalize_export


def fixtures(count: int = 4) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Construct trusted synthetic tasks separately from their native exports."""
    expected = [
        {
            "data": {
                "form_version": VERSION,
                "namespace": "synthetic",
                "group": "fixture",
                "rank": rank,
                "candidate_count": count,
                "comment_id": f"c{rank}",
                "comment_label": f"C-{rank}",
                "input_sha256": "a" * 64,
                "proposal_sha256": "b" * 64,
                "complete_source": "Unaltered full response.",
            }
        }
        for rank in range(1, count + 1)
    ]
    native = [
        {**copy.deepcopy(task), "id": rank, "project": 10, "annotations": [], "drafts": []}
        for rank, task in enumerate(expected, 1)
    ]
    return expected, native


def annotate(task: dict[str, Any], **overrides: str) -> None:
    """Save a complete synthetic annotation with explicit independent decisions."""
    fields = {
        "selection": "Selected",
        "selection_reason": "Clear scoped concern",
        **overrides,
    }
    task["annotations"] = [
        {
            "id": task["id"] + 100,
            "task": task["id"],
            "completed_by": 2,
            "created_at": "2026-09-30T10:00:00Z",
            "updated_at": "2026-09-30T10:01:00Z",
            "result": [
                {
                    "from_name": name,
                    "to_name": "review_context",
                    "type": "textarea" if name == "notes" else "choices",
                    "value": {"text" if name == "notes" else "choices": [value]},
                }
                for name, value in fields.items()
            ],
        }
    ]


def confirmation() -> dict[str, Any]:
    """Represent an explicit chat close bound to a specific synthetic export."""
    return {
        "schema_version": "task08b.finish.v2",
        "process_revision": PROCESS_REVISION,
        "template_version": VERSION,
        "project_id": 10,
        "input_sha256": "a" * 64,
        "proposal_sha256": "b" * 64,
        "export_sha256": "c" * 64,
        "finished": True,
        "reviewer": "Synthetic reviewer",
        "confirmed_at": "2026-09-30T11:00:00Z",
        "chat_reference": "synthetic:qualification",
        "statement": "I have finished this synthetic review.",
    }


def normalize(expected: list[dict[str, Any]], native: list[dict[str, Any]]) -> dict[str, Any]:
    """Supply an independently bound explicit completion confirmation."""
    return normalize_export(
        native,
        expected,
        project_id=10,
        export_sha256="c" * 64,
        finish_confirmation=confirmation(),
    )


def test_noncontiguous_review_preserves_inventory_and_advances_only_selected() -> None:
    expected, native = fixtures(5)
    annotate(native[0])
    annotate(native[2], selection="Reviewed skip", selection_reason="Weaker candidate")
    annotate(native[3], selection="Unresolved", selection_reason="Ambiguous concern")
    result = normalize(expected, list(reversed(native)))
    assert result["status"] == "complete"
    assert result["selected_comment_ids"] == result["advancing_comment_ids"] == ["c1"]
    assert result["untouched_comment_ids"] == ["c2", "c5"]
    assert result["reviewed_ranks"] == [1, 3, 4]
    assert result["last_reviewed_position"] == 4
    assert result["counts"]["reviewed_skips"] == result["counts"]["unresolved"] == 1
    assert result["native_tasks"] == list(reversed(native))
    assert result["finish_confirmation"] == confirmation()
    assert result["template_version"] == VERSION
    assert result["process_revision"] == PROCESS_REVISION
    assert "stopping_point" not in result
    assert set(result["records"][0]["decision"]) == {"selection", "selection_reason"}


@pytest.mark.parametrize("selected_count", [0, 1, 3])
def test_no_confirmation_never_advances_even_on_exhaustion(selected_count: int) -> None:
    expected, native = fixtures(3)
    for index, task in enumerate(native):
        annotate(task, selection="Selected" if index < selected_count else "Reviewed skip")
    result = normalize_export(native, expected, project_id=10, export_sha256="c" * 64)
    assert result["status"] == "awaiting_finish_confirmation"
    assert len(result["selected_comment_ids"]) == selected_count
    assert result["advancing_comment_ids"] == []
    assert result["counts"]["advancing"] == 0
    assert result["finish_confirmation"] is None


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", "task08b.finish.v1"),
        ("process_revision", "old"),
        ("template_version", "task08b.selection.v1"),
        ("project_id", 11),
        ("project_id", True),
        ("input_sha256", "d" * 64),
        ("proposal_sha256", "d" * 64),
        ("export_sha256", "d" * 64),
        ("finished", False),
        ("finished", 1),
        ("reviewer", " "),
        ("confirmed_at", "2026-09-30"),
        ("chat_reference", ""),
        ("statement", " "),
    ],
)
def test_rejects_invalid_confirmation(key: str, value: Any) -> None:
    expected, native = fixtures()
    finish = confirmation()
    finish[key] = value
    with pytest.raises(ValueError):
        normalize_export(
            native, expected, project_id=10, export_sha256="c" * 64, finish_confirmation=finish
        )


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_confirmation_has_exact_keys(mutation: str) -> None:
    expected, native = fixtures()
    finish = confirmation()
    if mutation == "missing":
        finish.pop("statement")
    else:
        finish["extra"] = True
    with pytest.raises(ValueError, match="exact fields"):
        normalize_export(
            native, expected, project_id=10, export_sha256="c" * 64, finish_confirmation=finish
        )


def test_empty_drafts_and_cancelled_are_not_negative_labels() -> None:
    expected, native = fixtures()
    annotate(native[0])
    native[1]["drafts"] = [{"result": [], "id": 4}]
    native[2]["annotations"] = [{"id": 8, "was_cancelled": True, "result": []}]
    result = normalize(expected, native)
    assert [r["state"] for r in result["records"]] == [
        "reviewed",
        "pending_draft",
        "pending_cancelled",
        "unreviewed",
    ]
    assert result["counts"]["excluded"] == 0
    assert result["selected_comment_ids"] == ["c1"]
    assert result["advancing_comment_ids"] == []
    assert result["status"] == "pending_saved_review"


@pytest.mark.parametrize(
    "change", ["data", "duplicate_candidate", "duplicate_task", "missing", "prediction", "project"]
)
def test_rejects_untrusted_or_incomplete_export(change: str) -> None:
    expected, native = fixtures()
    if change == "data":
        native[0]["data"]["complete_source"] = "Truncated."
    elif change == "duplicate_candidate":
        native[1] = copy.deepcopy(native[0])
    elif change == "duplicate_task":
        native[1]["id"] = native[0]["id"]
    elif change == "missing":
        native.pop()
    elif change == "prediction":
        native[0]["predictions"] = [{"result": []}]
    else:
        native[0]["project"] = 11
    with pytest.raises(ValueError):
        normalize(expected, native)


@pytest.mark.parametrize(
    "change",
    ["unknown", "duplicate", "multiple", "reviewer", "time", "task", "reason", "other", "binding"],
)
def test_rejects_invalid_saved_decisions(change: str) -> None:
    expected, native = fixtures()
    annotate(native[0])
    annotation = native[0]["annotations"][0]
    if change == "unknown":
        annotation["result"][0]["from_name"] = "model_selection"
    elif change == "duplicate":
        annotation["result"].append(copy.deepcopy(annotation["result"][0]))
    elif change == "multiple":
        native[0]["annotations"].append(copy.deepcopy(annotation))
    elif change == "reviewer":
        annotation.pop("completed_by")
    elif change == "time":
        annotation["updated_at"] = "2026-09-30"
    elif change == "task":
        annotation["task"] = 12
    elif change == "reason":
        annotate(native[0], selection_reason="Invalid reason")
    elif change == "other":
        annotate(native[0], selection_reason="Other", notes=" ")
    else:
        annotation["result"][0]["to_name"] = "other_source"
    with pytest.raises(ValueError):
        normalize(expected, native)


def test_other_reason_with_note() -> None:
    expected, native = fixtures(1)
    annotate(native[0], selection_reason="Other", notes="Specific bounded exception.")
    result = normalize(expected, native)
    assert result["status"] == "complete"
    assert result["advancing_comment_ids"] == ["c1"]


def test_three_selections_allow_later_review_but_overflow_is_rejected() -> None:
    expected, native = fixtures()
    for task in native:
        annotate(task)
    with pytest.raises(ValueError, match="At most three"):
        normalize(expected, native)
    annotate(native[3], selection="Reviewed skip")
    result = normalize(expected, native)
    assert result["status"] == "complete"
    assert result["advancing_comment_ids"] == ["c1", "c2", "c3"]
    assert result["reviewed_ranks"] == [1, 2, 3, 4]


def test_zero_selection_pass_can_close_without_reviewing_every_candidate() -> None:
    expected, native = fixtures(2)
    annotate(native[1], selection="Excluded", selection_reason="Source or eligibility concern")
    result = normalize(expected, native)
    assert result["status"] == "complete"
    assert result["counts"]["excluded"] == 1
    assert result["untouched_comment_ids"] == ["c1"]
    assert result["advancing_comment_ids"] == []


def test_saved_revision_with_draft_is_pending_and_lossless() -> None:
    """An unsaved edit cannot silently be promoted or erase its saved history."""
    expected, native = fixtures(1)
    annotate(native[0])
    native[0]["drafts"] = [{"id": 12, "result": [{"unsaved": "value"}]}]
    result = normalize(expected, native)
    assert result["records"][0]["state"] == "pending_draft"
    assert result["status"] == "pending_saved_review"
    assert result["advancing_comment_ids"] == []
    assert result["native_tasks"] == native
    native[0]["drafts"][0]["id"] = 99
    assert result["native_tasks"][0]["drafts"][0]["id"] == 12


@pytest.mark.parametrize(
    "legacy", ["eligibility", "eligibility_reason", "review_progress", "stop_reason"]
)
def test_legacy_controls_are_rejected(legacy: str) -> None:
    expected, native = fixtures(1)
    annotate(native[0], **{legacy: "Old value"})
    with pytest.raises(ValueError, match="Unknown or duplicate native control"):
        normalize(expected, native)


@pytest.mark.parametrize("field", ["selection", "selection_reason"])
def test_required_decisions_cannot_be_omitted(field: str) -> None:
    expected, native = fixtures(1)
    annotate(native[0])
    result = native[0]["annotations"][0]["result"]
    result[:] = [item for item in result if item["from_name"] != field]
    with pytest.raises(ValueError, match="Incomplete saved decision"):
        normalize(expected, native)


def test_duplicate_annotation_identity_across_candidates_is_rejected() -> None:
    """Native annotation IDs identify one saved decision, never two candidates."""
    expected, native = fixtures(2)
    for task in native:
        annotate(task)
    native[1]["annotations"][0]["id"] = native[0]["annotations"][0]["id"]
    with pytest.raises(ValueError, match="Duplicate native annotation"):
        normalize(expected, native)


@pytest.mark.parametrize("missing_key", ["annotations", "drafts", "project"])
def test_native_export_requires_explicit_review_state_and_project(missing_key: str) -> None:
    """An omitted drafts field must never make a stale saved decision advance."""
    expected, native = fixtures(1)
    annotate(native[0])
    del native[0][missing_key]
    with pytest.raises(ValueError):
        normalize(expected, native)


@pytest.mark.parametrize("key", ["annotations", "drafts"])
@pytest.mark.parametrize("bad_value", [None, {}, "", False])
def test_native_review_collections_must_be_lists(key: str, bad_value: Any) -> None:
    """Malformed collection fields cannot masquerade as empty review histories."""
    expected, native = fixtures(1)
    annotate(native[0])
    native[0][key] = bad_value
    with pytest.raises(ValueError, match="must be lists"):
        normalize(expected, native)
