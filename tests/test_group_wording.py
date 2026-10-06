"""Source-free Task08C preparation and exact saved-text regression tests."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from er_commons.group_wording import build_tasks, digest, encoded, load_prepared, prepare
from er_commons.group_wording_export import normalize_export


def packet_proposal() -> tuple[dict[str, Any], dict[str, Any]]:
    """Use invented comments only, keeping no historical case content."""
    text = "Could the project affect the fictional community garden?"
    packet = {
        "schema_version": "task08c.comment_only.v1",
        "records": [
            {
                "neutral_id": "C001",
                "original_comment": text,
                "comment_source_warnings": [],
                "original_comment_sha256": "a" * 64,
                "comment_text_sha256": digest(text.encode()),
            }
        ],
    }
    proposal = {
        "schema_version": "task08c.proposal.v1",
        "model": "gpt-6-astra",
        "prompt_version": "task08c.wording.v1",
        "packet_sha256": digest(encoded(packet)),
        "records": [
            {
                "neutral_id": "C001",
                "comment_text_sha256": digest(text.encode()),
                "question": text,
                "rewrite_reason": "Already suitable.",
                "stop_reason": None,
            }
        ],
    }
    return packet, proposal


def tasks() -> list[dict[str, Any]]:
    """Build independently trusted source-free review inputs."""
    packet, proposal = packet_proposal()
    return build_tasks(
        packet,
        proposal,
        packet_sha256=digest(encoded(packet)),
        proposal_sha256=digest(encoded(proposal)),
        namespace="synthetic",
    )


def control(name: str, value: str) -> dict[str, Any]:
    """Represent one native saved form control."""
    kind, key = ("choices", "choices") if name == "decision" else ("textarea", "text")
    return {"from_name": name, "to_name": "comment", "type": kind, "value": {key: [value]}}


def native(
    decision: str = "Approve exact wording", text: str = "Exact saved question?"
) -> list[dict[str, Any]]:
    """Construct a saved annotation without deriving it from predictions."""
    value = copy.deepcopy(tasks())
    value[0].update(
        id=1,
        project=9,
        drafts=[],
        annotations=[
            {
                "id": 10,
                "task": 1,
                "completed_by": 7,
                "created_at": "2026-09-30T10:00:00Z",
                "updated_at": "2026-09-30T11:00:00Z",
                "was_cancelled": False,
                "result": [
                    control("question", text),
                    control("decision", decision),
                    control("note", "Reason"),
                ],
            }
        ],
    )
    return value


def normalize(value: list[dict[str, Any]]) -> dict[str, Any]:
    """Bind regression exports to the trusted reviewer and project."""
    return normalize_export(
        value, tasks(), project_id=9, reviewer_id=7, export_sha256=digest(encoded(value))
    )


def test_exact_saved_text_and_stable_reexport() -> None:
    text = "  Is the café garden affected?\nKeep its qualification.  "
    value = native(text=text)
    first = normalize(value)
    frozen = first["records"][0]["frozen_question"]
    assert frozen["text"] == text
    assert frozen["text_sha256"] == digest(text.encode())
    value[0]["exported_at"] = "changed export metadata"
    assert normalize(value)["records"][0]["frozen_question"] == frozen
    assert first["advancing_neutral_ids"] == ["C001"]


@pytest.mark.parametrize("text", ["", " \n "])
def test_blank_approval_rejected(text: str) -> None:
    with pytest.raises(ValueError, match="nonblank saved"):
        normalize(native(text=text))


def test_missing_saved_text_never_falls_back() -> None:
    value = native()
    value[0]["annotations"][0]["result"].pop(0)
    with pytest.raises(ValueError, match="fallback"):
        normalize(value)


@pytest.mark.parametrize("decision,state", [("Reject", "rejected"), ("Unresolved", "unresolved")])
def test_stops_retained_without_advancement(decision: str, state: str) -> None:
    value = native(decision)
    result = normalize(value)
    assert result["records"][0]["state"] == state
    assert result["records"][0]["frozen_question"] is None
    assert result["advancing_neutral_ids"] == []
    assert result["native_tasks"] == value
    value[0]["annotations"][0]["result"].pop()
    with pytest.raises(ValueError, match="stop reason"):
        normalize(value)


def test_drafts_and_cancellation_never_advance() -> None:
    value = native()
    value[0]["drafts"] = [{"result": [control("question", "Unsubmitted edit")]}]
    assert normalize(value)["records"][0]["state"] == "pending_draft"
    assert normalize(value)["advancing_neutral_ids"] == []
    value[0]["drafts"] = []
    value[0]["annotations"][0]["was_cancelled"] = True
    assert normalize(value)["records"][0]["state"] == "pending_cancelled"
    value[0]["annotations"] = []
    assert normalize(value)["records"][0]["state"] == "unreviewed"
    del value[0]["drafts"]
    with pytest.raises(ValueError, match="drafts must be lists"):
        normalize(value)


@pytest.mark.parametrize(
    "kind", ["project", "reviewer", "source", "missing", "duplicate", "control"]
)
def test_foreign_or_incomplete_exports_fail(kind: str) -> None:
    value = native()
    if kind == "project":
        value[0]["project"] = 8
    elif kind == "reviewer":
        value[0]["annotations"][0]["completed_by"] = 8
    elif kind == "source":
        value[0]["data"]["original_comment"] += " changed"
    elif kind == "missing":
        value = []
    elif kind == "duplicate":
        value += copy.deepcopy(value)
    elif kind == "control":
        value[0]["annotations"][0]["result"].append(control("question", "Other?"))
    with pytest.raises(ValueError):
        normalize(value)


def test_clean_projection_and_stopped_proposal() -> None:
    packet, proposal = packet_proposal()
    proposal["records"][0].update(question=None, stop_reason="Multiple independent asks.")
    result = build_tasks(
        packet,
        proposal,
        packet_sha256=digest(encoded(packet)),
        proposal_sha256=digest(encoded(proposal)),
        namespace="synthetic",
    )
    assert result[0]["predictions"][0]["result"] == []
    assert "rewrite_reason" not in result[0]["data"]
    assert "stop_reason" not in result[0]["data"]
    assert result[0]["data"]["warnings_html"] == ""
    packet["records"][0]["response"] = "Forbidden hidden field"
    with pytest.raises(ValueError):
        build_tasks(
            packet,
            proposal,
            packet_sha256=digest(encoded(packet)),
            proposal_sha256=digest(encoded(proposal)),
            namespace="synthetic",
        )


def test_wrong_model_or_added_proposal_fields_fail() -> None:
    packet, proposal = packet_proposal()
    proposal["model"] = "wrong-model"
    with pytest.raises(ValidationError):
        build_tasks(
            packet,
            proposal,
            packet_sha256=digest(encoded(packet)),
            proposal_sha256=digest(encoded(proposal)),
            namespace="synthetic",
        )


def test_prepared_snapshots_replay_no_clobber(tmp_path: Path) -> None:
    packet, proposal = packet_proposal()
    p, q = tmp_path / "packet.json", tmp_path / "proposal.json"
    p.write_bytes(encoded(packet))
    q.write_bytes(encoded(proposal))
    output = tmp_path / "prepared"
    prepare(p, q, output, namespace="synthetic")
    assert load_prepared(output) == tasks()
    with pytest.raises(FileExistsError):
        prepare(p, q, output, namespace="synthetic")
    value = json.loads((output / "tasks.json").read_bytes())
    value[0]["data"]["proposed_question"] = "Changed?"
    (output / "tasks.json").write_bytes(encoded(value))
    with pytest.raises(ValueError, match="checksum"):
        load_prepared(output)
