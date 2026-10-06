"""Source-free isolation tests for the Task08C preparation boundary."""

import copy

import pytest

from er_commons.group_ranking import digest, encoded
from er_commons.group_wording_input import extract_comments, validate_packet


def fixture():
    """Build synthetic source data with visible forbidden-field sentinels."""
    original = {
        "unit_id": "source-1",
        "unit_kind": "comment",
        "text": "  Preserve this concern.\n",
        "official_label": "Source 1",
        "source_pages": [1],
        "span_ids": ["span-1"],
    }
    tasks = [
        {
            "data": {
                "comment_id": "source-1",
                "original_comment": original,
                "comment_source_warnings": ["Synthetic source warning"],
                "response_context": "FORBIDDEN_RESPONSE",
                "advisory": "FORBIDDEN_RANKING",
            }
        }
    ]
    handoff = {
        "schema_version": "task08b.handoff.v2",
        "process_revision": "task08.selection_gate.v2",
        "status": "complete",
        "selected_cases": [
            {
                "comment_id": "source-1",
                "source_task_index": 0,
                "original_comment_sha256": digest(encoded(original)),
            }
        ],
    }
    decisions = {
        "status": "complete",
        "selected_comment_ids": ["source-1"],
        "advancing_comment_ids": ["source-1"],
        "records": [
            {
                "comment_id": "source-1",
                "state": "reviewed",
                "decision": {
                    "selection": "Selected",
                    "selection_reason": "FORBIDDEN_SELECTION_REASON",
                },
            }
        ],
    }
    return handoff, tasks, decisions


def test_projection_retains_exact_text_and_isolates_sources():
    """Only allowlisted original text and warnings reach the wording model."""
    handoff, tasks, decisions = fixture()
    packet, mapping = extract_comments(handoff, tasks, decisions, ["source-1"])
    assert packet["records"][0]["original_comment"] == "  Preserve this concern.\n"
    assert packet["records"][0]["neutral_id"] == "C001"
    assert mapping[0]["comment_id"] == "source-1"
    assert b"FORBIDDEN" not in encoded(packet)
    assert b"source-1" not in encoded(packet)
    assert packet["records"][0]["comment_source_warnings"] == ["Synthetic source warning"]


@pytest.mark.parametrize("change", ["hash", "index", "unauthorized", "reason", "gate", "pending"])
def test_projection_rejects_broken_source_or_selection(change):
    """Source and authorization failures stop before any safe packet is emitted."""
    handoff, tasks, decisions = fixture()
    authorized = ["source-1"]
    if change == "hash":
        tasks[0]["data"]["original_comment"]["text"] += "changed"
    elif change == "index":
        handoff["selected_cases"][0]["source_task_index"] = -1
    elif change == "unauthorized":
        authorized = ["foreign"]
    elif change == "reason":
        decisions["records"][0]["decision"]["selection_reason"] = " "
    elif change == "gate":
        handoff["process_revision"] = "task08.selection_gate.v1"
    else:
        decisions["status"] = "pending_saved_review"
    with pytest.raises(ValueError):
        extract_comments(handoff, tasks, decisions, authorized)


@pytest.mark.parametrize("change", ["extra", "nested", "text", "id", "duplicate", "warning"])
def test_packet_validator_rejects_leakage_and_corruption(change):
    """The consumer boundary rejects unrecognized content and corrupted bindings."""
    packet, _ = extract_comments(*fixture(), ["source-1"])
    record = packet["records"][0]
    if change == "extra":
        packet["response"] = "forbidden"
    elif change == "nested":
        record["response"] = "forbidden"
    elif change == "text":
        record["original_comment"] += "changed"
    elif change == "id":
        record["neutral_id"] = "source-1"
    elif change == "duplicate":
        packet["records"].append(copy.deepcopy(record))
    else:
        record["comment_source_warnings"] = [{"response": "forbidden"}]
    with pytest.raises(ValueError):
        validate_packet(packet)


def test_response_and_selection_reason_cannot_affect_projection():
    """Changing forbidden material leaves the exact safe packet unchanged."""
    handoff, tasks, decisions = fixture()
    before, _ = extract_comments(handoff, tasks, decisions, ["source-1"])
    tasks[0]["data"]["response_context"] = "OTHER_RESPONSE"
    tasks[0]["data"]["advisory"] = "OTHER_RANKING"
    decisions["records"][0]["decision"]["selection_reason"] = "OTHER_REASON"
    after, _ = extract_comments(handoff, tasks, decisions, ["source-1"])
    assert encoded(before) == encoded(after)
