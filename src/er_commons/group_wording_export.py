"""Freeze only explicitly approved exact saved wording; preserve every other state."""

from __future__ import annotations

import copy
import re
from datetime import datetime
from typing import Any

from er_commons.group_wording import VERSION, digest, encoded, validate_schema, validate_tasks

DECISIONS = {"Approve exact wording", "Reject", "Unresolved"}


def _positive(value: Any, label: str) -> int:
    """Require native positive integer IDs without boolean coercion."""
    if type(value) is not int or value < 1:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _timestamp(value: Any) -> None:
    """Require timezone-bound saved-review timestamps."""
    if not isinstance(value, str):
        raise ValueError("Saved review requires timestamps")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("Saved review timestamp requires timezone")


def _fields(annotation: dict[str, Any]) -> dict[str, str]:
    """Parse one exact saved value per known control; never consult predictions."""
    results = annotation.get("result")
    if not isinstance(results, list):
        raise ValueError("Saved review requires native results")
    fields: dict[str, str] = {}
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("Malformed native result")
        name = result.get("from_name")
        if name not in {"question", "decision", "note"} or name in fields:
            raise ValueError("Unknown or duplicate native control")
        kind, key = ("choices", "choices") if name == "decision" else ("textarea", "text")
        if result.get("to_name") != "comment" or result.get("type") != kind:
            raise ValueError("Foreign native control binding")
        value = result.get("value")
        if not isinstance(value, dict) or set(value) != {key}:
            raise ValueError("Malformed native control value")
        values = value[key]
        if not isinstance(values, list) or len(values) != 1 or not isinstance(values[0], str):
            raise ValueError("Native control requires exactly one text value")
        fields[name] = values[0]
    if fields.get("decision") not in DECISIONS:
        raise ValueError("Explicit saved decision required")
    if fields["decision"] == "Approve exact wording" and not fields.get("question", "").strip():
        raise ValueError(
            "Approval requires nonblank saved question; proposals are not fallback text"
        )
    return fields


def _record(task: dict[str, Any], reviewer_id: int) -> dict[str, Any]:
    """Retain drafts/cancellations while requiring source-bound explicit approval."""
    data = task["data"]
    record: dict[str, Any] = {
        key: data[key]
        for key in (
            "neutral_id",
            "original_comment_sha256",
            "comment_text_sha256",
            "packet_sha256",
            "proposal_sha256",
            "form_version",
        )
    }
    record.update(
        task_id=task["id"],
        state="unreviewed",
        decision=None,
        saved_question=None,
        note=None,
        provenance=None,
        frozen_question=None,
    )
    annotations, drafts = task.get("annotations"), task.get("drafts")
    if not isinstance(annotations, list) or not isinstance(drafts, list):
        raise ValueError("Native annotations and drafts must be lists")
    if len(annotations) > 1:
        raise ValueError("Multiple annotations require explicit reconciliation")
    if drafts:
        record["state"] = "pending_draft"
        return record
    if not annotations:
        return record
    annotation = annotations[0]
    if not isinstance(annotation, dict):
        raise ValueError("Malformed native annotation")
    if annotation.get("was_cancelled") or annotation.get("skipped"):
        record["state"] = "pending_cancelled"
        return record
    annotation_id = _positive(annotation.get("id"), "Annotation ID")
    if type(annotation.get("task")) is not int or annotation["task"] != task["id"]:
        raise ValueError("Annotation task binding differs")
    reviewer = annotation.get("completed_by")
    actual_reviewer = reviewer.get("id") if isinstance(reviewer, dict) else reviewer
    if _positive(actual_reviewer, "Reviewer ID") != reviewer_id:
        raise ValueError("Unexpected reviewer binding")
    for key in ("created_at", "updated_at"):
        _timestamp(annotation.get(key))
    fields = _fields(annotation)
    if fields["decision"] != "Approve exact wording" and not fields.get("note", "").strip():
        raise ValueError("Rejected or unresolved wording requires a stop reason")
    record.update(
        state={
            "Approve exact wording": "approved",
            "Reject": "rejected",
            "Unresolved": "unresolved",
        }[fields["decision"]],
        decision=fields["decision"],
        saved_question=fields.get("question"),
        note=fields.get("note"),
        provenance={
            "annotation_id": annotation_id,
            "reviewer": copy.deepcopy(reviewer),
            "created_at": annotation["created_at"],
            "updated_at": annotation["updated_at"],
        },
    )
    if record["state"] == "approved":
        text = fields["question"]
        text_sha = digest(text.encode("utf-8"))
        version = digest(
            encoded(
                {
                    "source": data["original_comment_sha256"],
                    "packet": data["packet_sha256"],
                    "proposal": data["proposal_sha256"],
                    "annotation_id": annotation_id,
                    "project_id": task["project"],
                    "updated_at": annotation["updated_at"],
                    "reviewer_id": reviewer_id,
                    "text_sha256": text_sha,
                }
            )
        )
        record["frozen_question"] = {
            "question_id": f"task08c-{data['neutral_id']}-{version}",
            "question_version": version,
            "text": text,
            "text_sha256": text_sha,
        }
    return record


def normalize_export(
    native_tasks: list[dict[str, Any]],
    expected_tasks: list[dict[str, Any]],
    *,
    project_id: int,
    reviewer_id: int,
    export_sha256: str,
) -> dict[str, Any]:
    """Bind a complete native export to independently loaded prepared inputs.

    Exact approved text is never stripped, reformatted or replaced by a proposal.
    Nonapproved records and full native annotation/draft histories stay preserved.
    """
    _positive(project_id, "Project ID")
    _positive(reviewer_id, "Reviewer ID")
    if not isinstance(export_sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", export_sha256):
        raise ValueError("Native export digest required")
    validate_tasks(expected_tasks)
    expected = {task["data"]["neutral_id"]: task for task in expected_tasks}
    seen: set[str] = set()
    task_ids: set[int] = set()
    annotation_ids: set[int] = set()
    records = []
    for task in native_tasks:
        if not isinstance(task, dict) or not isinstance(task.get("data"), dict):
            raise ValueError("Malformed native task")
        neutral_id = task["data"].get("neutral_id")
        if neutral_id not in expected or neutral_id in seen:
            raise ValueError("Unknown or duplicate exported comment")
        if task["data"] != expected[neutral_id]["data"]:
            raise ValueError("Native task differs from trusted comment-only inputs")
        task_id = _positive(task.get("id"), "Task ID")
        if task_id in task_ids:
            raise ValueError("Duplicate native task ID")
        if type(task.get("project")) is not int or task["project"] != project_id:
            raise ValueError("Foreign project binding")
        record = _record(task, reviewer_id)
        for annotation in task["annotations"]:
            if isinstance(annotation, dict) and annotation.get("id") is not None:
                annotation_id = _positive(annotation["id"], "Annotation ID")
                if annotation_id in annotation_ids:
                    raise ValueError("Duplicate annotation ID")
                annotation_ids.add(annotation_id)
        seen.add(neutral_id)
        task_ids.add(task_id)
        records.append(record)
    if seen != expected.keys():
        raise ValueError("Native export must include every comment, even untouched ones")
    positions = {key: position for position, key in enumerate(expected)}
    records.sort(key=lambda record: positions[record["neutral_id"]])
    first = expected_tasks[0]["data"]
    result = {
        "schema_version": VERSION,
        "namespace": first["namespace"],
        "packet_sha256": first["packet_sha256"],
        "proposal_sha256": first["proposal_sha256"],
        "project_id": project_id,
        "reviewer_id": reviewer_id,
        "export_sha256": export_sha256,
        "records": records,
        "native_tasks": copy.deepcopy(native_tasks),
        "advancing_neutral_ids": [r["neutral_id"] for r in records if r["state"] == "approved"],
        "status": "complete"
        if all(r["state"] in {"approved", "rejected"} for r in records)
        else "incomplete",
    }
    validate_schema(result, "decisions.schema.json")
    return result
