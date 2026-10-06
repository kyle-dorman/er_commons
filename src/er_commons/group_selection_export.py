"""Normalize native Task 08B exports against the exact trusted review inputs.

Human decisions are explicit; drafts, cancellation and unseen tasks never become
negative labels. Native task records remain available as a lossless audit trail.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

VERSION = "task08b.selection.v2"
PROCESS_REVISION = "task08.selection_gate.v2"
CHOICES = {
    "selection": {"Selected", "Reviewed skip", "Excluded", "Unresolved"},
    "selection_reason": {
        "Clear scoped concern",
        "Weaker candidate",
        "Multiple independent asks",
        "Ambiguous concern",
        "Source or eligibility concern",
        "Other",
    },
}


def _positive_id(value: Any, label: str) -> int:
    """Require real positive native identifiers, excluding boolean lookalikes."""
    if type(value) is not int or value < 1:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _timestamp(value: Any) -> None:
    """Require a timezone-bound native saved-decision timestamp."""
    if not isinstance(value, str):
        raise ValueError("Saved decisions require timestamps")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid saved-decision timestamp") from exc
    if stamp.tzinfo is None:
        raise ValueError("Saved-decision timestamps require a timezone")


def _fields(annotation: dict[str, Any]) -> dict[str, str]:
    """Parse only known single-valued native controls and reject contradictions."""
    fields: dict[str, str] = {}
    results = annotation.get("result")
    if not isinstance(results, list):
        raise ValueError("Saved decisions require native result controls")
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("Malformed native result")
        name = result.get("from_name")
        if name not in {*CHOICES, "notes"} or name in fields:
            raise ValueError("Unknown or duplicate native control")
        text_control = name == "notes"
        kind, key = ("textarea", "text") if text_control else ("choices", "choices")
        if result.get("to_name") != "review_context" or result.get("type") != kind:
            raise ValueError("Foreign native control binding")
        value = result.get("value")
        if not isinstance(value, dict) or set(value) != {key}:
            raise ValueError("Malformed native control value")
        values = value[key]
        if not isinstance(values, list) or len(values) != 1 or not isinstance(values[0], str):
            raise ValueError("Native controls require exactly one text value")
        if not text_control and values[0] not in CHOICES[name]:
            raise ValueError(f"Unknown choice for {name}")
        fields[name] = values[0]
    if not set(CHOICES) <= fields.keys():
        raise ValueError("Incomplete saved decision")
    if fields["selection_reason"] == "Other" and not fields.get("notes", "").strip():
        raise ValueError("Other requires nonblank explanatory notes")
    return fields


def _record(task: dict[str, Any]) -> dict[str, Any]:
    """Normalize one candidate while retaining unsaved/cancelled states explicitly."""
    data = task["data"]
    record = {
        key: data[key]
        for key in (
            "comment_id",
            "comment_label",
            "rank",
            "input_sha256",
            "proposal_sha256",
        )
    }
    record.update(task_id=task["id"], state="unreviewed", decision=None, provenance=None)
    annotations = task.get("annotations")
    drafts = task.get("drafts")
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
    _positive_id(annotation.get("id"), "Annotation id")
    if annotation.get("task") != task["id"]:
        raise ValueError("Annotation belongs to a different or unbound task")
    reviewer = annotation.get("completed_by")
    _positive_id(reviewer.get("id") if isinstance(reviewer, dict) else reviewer, "Reviewer id")
    for key in ("created_at", "updated_at"):
        _timestamp(annotation.get(key))
    record["state"] = "reviewed"
    record["decision"] = _fields(annotation)
    record["provenance"] = {
        "annotation_id": annotation["id"],
        "reviewer": copy.deepcopy(reviewer),
        "created_at": annotation["created_at"],
        "updated_at": annotation["updated_at"],
    }
    return record


def _trusted_inputs(expected_tasks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Require one complete, sequential, consistently bound trusted group."""
    if not expected_tasks:
        raise ValueError("Trusted candidate tasks are required")
    expected: dict[str, dict[str, Any]] = {}
    common = ("form_version", "namespace", "group", "input_sha256", "proposal_sha256")
    first = expected_tasks[0]["data"]
    for rank, task in enumerate(expected_tasks, 1):
        data = task["data"]
        if data.get("form_version") != VERSION or data.get("namespace") not in {
            "dataset",
            "synthetic",
        }:
            raise ValueError("Unsupported form or namespace")
        if any(data.get(key) != first.get(key) for key in common):
            raise ValueError("Mixed trusted group or input identities")
        for key in ("input_sha256", "proposal_sha256"):
            if not isinstance(data.get(key), str) or not re.fullmatch(r"[a-f0-9]{64}", data[key]):
                raise ValueError("Invalid trusted input digest")
        for key in ("comment_id", "comment_label", "group"):
            if not isinstance(data.get(key), str) or not data[key].strip():
                raise ValueError("Missing trusted candidate identity")
        if data.get("rank") != rank or data.get("candidate_count") != len(expected_tasks):
            raise ValueError("Trusted tasks must preserve complete sequential advisory order")
        if data["comment_id"] in expected:
            raise ValueError("Duplicate trusted candidate identity")
        if task.get("predictions"):
            raise ValueError("Selection tasks must not contain predictions")
        expected[data["comment_id"]] = data
    return expected


def _finish_confirmation(
    confirmation: dict[str, Any] | None,
    first: dict[str, Any],
    project_id: int,
    export_sha256: str,
) -> dict[str, Any] | None:
    """Bind a separate chat confirmation to this exact saved review export."""
    if confirmation is None:
        return None
    bindings = {
        "schema_version": "task08b.finish.v2",
        "process_revision": PROCESS_REVISION,
        "template_version": VERSION,
        "project_id": project_id,
        "input_sha256": first["input_sha256"],
        "proposal_sha256": first["proposal_sha256"],
        "export_sha256": export_sha256,
        "finished": True,
    }
    text_fields = {"reviewer", "confirmed_at", "chat_reference", "statement"}
    if not isinstance(confirmation, dict) or set(confirmation) != set(bindings) | text_fields:
        raise ValueError("Finish confirmation requires exact fields")
    for key, value in bindings.items():
        if type(confirmation[key]) is not type(value) or confirmation[key] != value:
            raise ValueError(f"Finish confirmation has invalid or stale {key}")
    for key in text_fields:
        if not isinstance(confirmation[key], str) or not confirmation[key].strip():
            raise ValueError(f"Finish confirmation requires nonblank {key}")
    _timestamp(confirmation["confirmed_at"])
    return copy.deepcopy(confirmation)


def normalize_export(
    native_tasks: list[dict[str, Any]],
    expected_tasks: list[dict[str, Any]],
    *,
    project_id: int,
    export_sha256: str,
    finish_confirmation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a complete native export without inferring selection from rank.

    The caller must supply independently verified prepared tasks and the digest
    of the saved native export bytes. Only explicit saved selections advance,
    after chat confirmation closes the review and all native drafts are resolved.
    """
    _positive_id(project_id, "Project id")
    if not re.fullmatch(r"[a-f0-9]{64}", export_sha256):
        raise ValueError("Native export SHA-256 is required")
    expected = _trusted_inputs(expected_tasks)
    seen: set[str] = set()
    task_ids: set[int] = set()
    annotation_ids: set[int] = set()
    records = []
    for task in native_tasks:
        data = task.get("data", {})
        candidate = data.get("comment_id")
        if candidate not in expected or candidate in seen:
            raise ValueError("Unknown or duplicate exported candidate")
        if data != expected[candidate]:
            raise ValueError("Exported task data differs from trusted review inputs")
        if task.get("predictions"):
            raise ValueError("Selection tasks must not contain predictions")
        task_id = _positive_id(task.get("id"), "Task id")
        if task_id in task_ids:
            raise ValueError("Duplicate native task id")
        if task.get("project") != project_id:
            raise ValueError("Foreign project binding")
        record = _record(task)
        for annotation in task["annotations"]:
            if isinstance(annotation, dict) and annotation.get("id") is not None:
                annotation_id = _positive_id(annotation["id"], "Annotation id")
                if annotation_id in annotation_ids:
                    raise ValueError("Duplicate native annotation id")
                annotation_ids.add(annotation_id)
        seen.add(candidate)
        task_ids.add(task_id)
        records.append(record)
    if seen != expected.keys():
        raise ValueError("Native export omits candidates, including untouched tasks")
    records.sort(key=lambda record: record["rank"])
    reviewed = [record for record in records if record["state"] == "reviewed"]
    selected = [record for record in reviewed if record["decision"]["selection"] == "Selected"]
    if len(selected) > 3:
        raise ValueError("At most three candidates may be selected")
    first = expected_tasks[0]["data"]
    confirmation = _finish_confirmation(finish_confirmation, first, project_id, export_sha256)
    pending = any(record["state"].startswith("pending") for record in records)
    status = (
        "awaiting_finish_confirmation"
        if confirmation is None
        else "pending_saved_review"
        if pending
        else "complete"
    )
    advancing = [record["comment_id"] for record in selected] if status == "complete" else []
    output = {
        "schema_version": VERSION,
        "process_revision": PROCESS_REVISION,
        "template_version": VERSION,
        "finish_confirmation": confirmation,
        "namespace": first["namespace"],
        "group": first["group"],
        "input_sha256": first["input_sha256"],
        "proposal_sha256": first["proposal_sha256"],
        "project_id": project_id,
        "export_sha256": export_sha256,
        "status": status,
        "records": records,
        "native_tasks": copy.deepcopy(native_tasks),
        "selected_comment_ids": [r["comment_id"] for r in selected],
        "advancing_comment_ids": advancing,
        "reviewed_ranks": [r["rank"] for r in reviewed],
        "last_reviewed_position": reviewed[-1]["rank"] if reviewed else None,
        "untouched_comment_ids": [r["comment_id"] for r in records if r["state"] == "unreviewed"],
        "counts": {
            "candidates": len(records),
            "reviewed": len(reviewed),
            "selected": len(selected),
            "advancing": len(advancing),
            "reviewed_skips": sum(r["decision"]["selection"] == "Reviewed skip" for r in reviewed),
            "excluded": sum(r["decision"]["selection"] == "Excluded" for r in reviewed),
            "unresolved": sum(r["decision"]["selection"] == "Unresolved" for r in reviewed),
            "unreviewed": sum(r["state"] == "unreviewed" for r in records),
            "pending": sum(r["state"].startswith("pending") for r in records),
        },
    }
    schema_path = (
        Path(__file__).resolve().parents[2]
        / "benchmarks/er_bench/schemas/task08b/v2/decisions.schema.json"
    )
    Draft202012Validator(json.loads(schema_path.read_text())).validate(output)
    return output
