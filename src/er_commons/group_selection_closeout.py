"""Close all Task 08B groups under Kyle's explicit 2026-10-01 amendment.

This separate policy retains every saved Selected decision without a group cap.
Native skips, drafts and untouched tasks remain distinct, never negative labels.
Historical selection exporters and their sealed outputs remain unchanged.
"""

from __future__ import annotations

import copy
import re
from typing import Any

from er_commons.group_selection_export import (
    CHOICES,
    VERSION,
    _positive_id,
    _record,
    _timestamp,
    _trusted_inputs,
)

PROCESS_REVISION = "task08.selection_closeout.v1"
SCHEMA_VERSION = "task08b.closeout.v1"
FINISH_VERSION = "task08b.closeout_finish.v1"
POLICY = {
    "selection_limit": None,
    "saved_selected_authoritative": True,
    "native_skips_close_review": True,
}


def _confirmation(
    value: dict[str, Any] | None,
    first: dict[str, Any],
    project_id: int,
    export_sha256: str,
) -> dict[str, Any] | None:
    """Require exact export-bound authorization for this amended policy."""
    if value is None:
        return None
    bindings = {
        "schema_version": FINISH_VERSION,
        "process_revision": PROCESS_REVISION,
        "template_version": VERSION,
        "project_id": project_id,
        "group": first["group"],
        "input_sha256": first["input_sha256"],
        "proposal_sha256": first["proposal_sha256"],
        "export_sha256": export_sha256,
        "finished": True,
        **POLICY,
    }
    text_fields = {"reviewer", "confirmed_at", "chat_reference", "statement"}
    if not isinstance(value, dict) or set(value) != set(bindings) | text_fields:
        raise ValueError("Closeout confirmation requires exact fields")
    for key, expected in bindings.items():
        if type(value[key]) is not type(expected) or value[key] != expected:
            raise ValueError(f"Closeout confirmation has invalid or stale {key}")
    for key in text_fields:
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError(f"Closeout confirmation requires nonblank {key}")
    _timestamp(value["confirmed_at"])
    return copy.deepcopy(value)


def _closeout_fields(annotation: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    """Validate unchanged controls, recording incomplete nonselected Other reasons.

    This policy-specific parser keeps the historical parser immutable. Missing
    Other notes are diagnostic only for nonselected records; Selected remains
    subject to the original strict reason requirement.
    """
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
        kind, key = ("textarea", "text") if name == "notes" else ("choices", "choices")
        if result.get("to_name") != "review_context" or result.get("type") != kind:
            raise ValueError("Foreign native control binding")
        value = result.get("value")
        if not isinstance(value, dict) or set(value) != {key}:
            raise ValueError("Malformed native control value")
        values = value[key]
        if not isinstance(values, list) or len(values) != 1 or not isinstance(values[0], str):
            raise ValueError("Native controls require exactly one text value")
        if name != "notes" and values[0] not in CHOICES[name]:
            raise ValueError(f"Unknown choice for {name}")
        fields[name] = values[0]
    if not set(CHOICES) <= fields.keys():
        raise ValueError("Incomplete saved decision")
    diagnostics = []
    if fields["selection_reason"] == "Other" and not fields.get("notes", "").strip():
        if fields["selection"] == "Selected":
            raise ValueError("Other requires nonblank explanatory notes for Selected")
        diagnostics.append("nonselected_other_reason_without_explanatory_notes")
    return fields, diagnostics


def _closeout_record(task: dict[str, Any], annotation_ids: set[int]) -> dict[str, Any]:
    """Read saved decisions separately from native cancellation and draft history."""
    annotations, drafts = task.get("annotations"), task.get("drafts")
    if not isinstance(annotations, list) or not isinstance(drafts, list):
        raise ValueError("Native annotations and drafts must be lists")
    if any(not isinstance(draft, dict) for draft in drafts):
        raise ValueError("Malformed native draft")
    saved: list[dict[str, Any]] = []
    cancelled: list[dict[str, Any]] = []
    for annotation in annotations:
        if not isinstance(annotation, dict):
            raise ValueError("Malformed native annotation")
        annotation_id = _positive_id(annotation.get("id"), "Annotation id")
        if annotation_id in annotation_ids:
            raise ValueError("Duplicate native annotation id")
        annotation_ids.add(annotation_id)
        if annotation.get("task") != task["id"]:
            raise ValueError("Annotation belongs to a different or unbound task")
        for flag in ("was_cancelled", "skipped"):
            if flag in annotation and type(annotation[flag]) is not bool:
                raise ValueError("Native cancellation flags must be booleans")
        destination = (
            cancelled if annotation.get("was_cancelled") or annotation.get("skipped") else saved
        )
        destination.append(annotation)
    if len(saved) > 1:
        raise ValueError("Multiple saved annotations require explicit reconciliation")
    record = _record({**task, "annotations": [], "drafts": []})
    if saved:
        annotation = saved[0]
        reviewer = annotation.get("completed_by")
        _positive_id(reviewer.get("id") if isinstance(reviewer, dict) else reviewer, "Reviewer id")
        for key in ("created_at", "updated_at"):
            _timestamp(annotation.get(key))
        fields, diagnostics = _closeout_fields(annotation)
        record.update(
            state="reviewed",
            decision=fields,
            provenance={
                "annotation_id": annotation["id"],
                "reviewer": copy.deepcopy(reviewer),
                "created_at": annotation["created_at"],
                "updated_at": annotation["updated_at"],
            },
        )
        if diagnostics:
            record["validation_notes"] = diagnostics
    else:
        record["state"] = (
            "native_skipped" if cancelled else "draft_only" if drafts else "unreviewed"
        )
    record["has_drafts"] = bool(drafts)
    record["draft_count"] = len(drafts)
    record["cancelled_annotation_ids"] = [item["id"] for item in cancelled]
    record["saved_decision_with_draft"] = bool(saved and drafts)
    return record


def normalize_closeout_export(
    native_tasks: list[dict[str, Any]],
    expected_tasks: list[dict[str, Any]],
    *,
    project_id: int,
    export_sha256: str,
    finish_confirmation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate full inventory and preserve every saved Selected under the amendment.

    Callers verify prepared inputs independently and hash the exact saved native
    export bytes. Completion requires the actual human statement bound to those
    bytes and this policy; no count, skip, draft or queue position implies it.
    """
    _positive_id(project_id, "Project id")
    if not isinstance(export_sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", export_sha256):
        raise ValueError("Native export SHA-256 is required")
    expected = _trusted_inputs(expected_tasks)
    seen: set[str] = set()
    task_ids: set[int] = set()
    annotation_ids: set[int] = set()
    records = []
    for task in native_tasks:
        if not isinstance(task, dict) or not isinstance(task.get("data"), dict):
            raise ValueError("Malformed native task")
        data = task["data"]
        candidate = data.get("comment_id")
        if not isinstance(candidate, str) or candidate not in expected or candidate in seen:
            raise ValueError("Unknown or duplicate exported candidate")
        if data != expected[candidate]:
            raise ValueError("Exported task data differs from trusted review inputs")
        if task.get("predictions"):
            raise ValueError("Selection tasks must not contain predictions")
        task_id = _positive_id(task.get("id"), "Task id")
        if task_id in task_ids:
            raise ValueError("Duplicate native task id")
        if type(task.get("project")) is not int or task["project"] != project_id:
            raise ValueError("Foreign project binding")
        records.append(_closeout_record(task, annotation_ids))
        seen.add(candidate)
        task_ids.add(task_id)
    if seen != expected.keys():
        raise ValueError("Native export omits candidates, including untouched tasks")
    records.sort(key=lambda record: record["rank"])
    reviewed = [record for record in records if record["state"] == "reviewed"]
    selected = [
        record["comment_id"] for record in reviewed if record["decision"]["selection"] == "Selected"
    ]
    first = expected_tasks[0]["data"]
    confirmation = _confirmation(finish_confirmation, first, project_id, export_sha256)
    advancing = selected.copy() if confirmation is not None else []
    return {
        "schema_version": SCHEMA_VERSION,
        "process_revision": PROCESS_REVISION,
        "template_version": VERSION,
        "policy": copy.deepcopy(POLICY),
        "finish_confirmation": confirmation,
        "namespace": first["namespace"],
        "group": first["group"],
        "input_sha256": first["input_sha256"],
        "proposal_sha256": first["proposal_sha256"],
        "project_id": project_id,
        "export_sha256": export_sha256,
        "status": "complete" if confirmation is not None else "awaiting_finish_confirmation",
        "records": records,
        "native_tasks": copy.deepcopy(native_tasks),
        "selected_comment_ids": selected,
        "advancing_comment_ids": advancing,
        "reviewed_ranks": [record["rank"] for record in reviewed],
        "last_reviewed_position": reviewed[-1]["rank"] if reviewed else None,
        "untouched_comment_ids": [
            record["comment_id"] for record in records if record["state"] == "unreviewed"
        ],
        "counts": {
            "candidates": len(records),
            "reviewed": len(reviewed),
            "selected": len(selected),
            "advancing": len(advancing),
            "reviewed_skips": sum(
                record["decision"]["selection"] == "Reviewed skip" for record in reviewed
            ),
            "excluded": sum(record["decision"]["selection"] == "Excluded" for record in reviewed),
            "unresolved": sum(
                record["decision"]["selection"] == "Unresolved" for record in reviewed
            ),
            "unreviewed": sum(record["state"] == "unreviewed" for record in records),
            "native_skipped": sum(record["state"] == "native_skipped" for record in records),
            "draft_only": sum(record["state"] == "draft_only" for record in records),
            "tasks_with_drafts": sum(record["has_drafts"] for record in records),
            "saved_decisions_with_drafts": sum(
                record["saved_decision_with_draft"] for record in records
            ),
            "cancelled_annotations": sum(
                len(record["cancelled_annotation_ids"]) for record in records
            ),
        },
    }
