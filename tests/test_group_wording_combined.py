"""Source-free combined intake checks preserve strict isolation and legacy limits."""

from copy import deepcopy
from typing import Any

import pytest

from er_commons.group_ranking import digest, encoded
from er_commons.group_selection_closeout import POLICY, PROCESS_REVISION
from er_commons.group_wording_combined import VERSION, project_selected, validate_packet
from er_commons.group_wording_input import validate_packet as legacy_validate


def packet() -> dict[str, Any]:
    """Create a full combined queue without real source payloads."""
    return {
        "schema_version": VERSION,
        "records": [
            {
                "neutral_id": f"C{i:03d}",
                "original_comment": "Example source",
                "comment_source_warnings": [],
                "original_comment_sha256": "a" * 64,
                "comment_text_sha256": digest(b"Example source"),
            }
            for i in range(1, 58)
        ],
    }


def test_combined_accepts_57_and_legacy_stays_limited() -> None:
    """Expanded presentation is a named revision, not a silent legacy mutation."""
    value = packet()
    validate_packet(value)
    with pytest.raises(ValueError):
        legacy_validate({**value, "schema_version": "task08c.comment_only.v1"})


@pytest.mark.parametrize("change", ["extra", "text", "order", "warnings", "empty"])
def test_combined_rejects_contamination_and_source_changes(change: str) -> None:
    """No response field or unbound text can enter the safe combined packet."""
    value = packet()
    if change == "extra":
        value["records"][0]["response"] = "restricted"
    elif change == "text":
        value["records"][0]["original_comment"] += " altered"
    elif change == "order":
        value["records"][0]["neutral_id"] = "C002"
    elif change == "warnings":
        value["records"][0]["comment_source_warnings"] = [None]
    else:
        value["records"] = []
    with pytest.raises(ValueError):
        validate_packet(value)


def fixture() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Supply four saved selections above the historical group cap."""
    originals = [
        {"unit_kind": "comment", "unit_id": f"source{i}", "text": f"Original {i}"} for i in range(4)
    ]
    tasks = [
        {
            "data": {
                "comment_id": x["unit_id"],
                "original_comment": x,
                "comment_source_warnings": [],
                "response": "FORBIDDEN",
            }
        }
        for x in originals
    ]
    cases = [
        {
            "comment_id": x["unit_id"],
            "source_task_index": i,
            "original_comment_sha256": digest(encoded(x)),
        }
        for i, x in enumerate(originals)
    ]
    handoff = {
        "schema_version": "task08b.handoff.v3",
        "process_revision": PROCESS_REVISION,
        "policy": deepcopy(POLICY),
        "status": "complete",
        "selected_cases": cases,
    }
    decisions = {
        "status": "complete",
        "selected_comment_ids": [x["unit_id"] for x in originals],
        "advancing_comment_ids": [x["unit_id"] for x in originals],
    }
    return handoff, tasks, decisions


def test_projection_accepts_larger_group_and_removes_restricted_fields() -> None:
    """Only original text, warnings and source hashes survive projection."""
    projected = project_selected(*fixture())
    assert len(projected) == 4
    assert "FORBIDDEN" not in str(projected)


@pytest.mark.parametrize("change", ["hash", "id", "index", "selected", "policy", "legacy"])
def test_projection_rejects_binding_changes(change: str) -> None:
    """No changed v3 identity, selected closure or policy can qualify."""
    handoff, tasks, decisions = fixture()
    if change == "hash":
        handoff["selected_cases"][0]["original_comment_sha256"] = "b" * 64
    elif change == "id":
        tasks[0]["data"]["original_comment"]["unit_id"] = "wrong"
    elif change == "index":
        handoff["selected_cases"][0]["source_task_index"] = 1
    elif change == "selected":
        decisions["advancing_comment_ids"].pop()
    elif change == "policy":
        handoff["policy"]["selection_limit"] = 3
    else:
        handoff["schema_version"] = "task08b.handoff.v2"
    with pytest.raises(ValueError):
        project_selected(handoff, tasks, decisions)
