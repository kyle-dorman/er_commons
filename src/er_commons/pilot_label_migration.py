"""Pure, fail-closed label transfer helpers; callers own isolated API operations.

Import is append-only in Label Studio, so never blindly retry a POST. Export the
project, reconcile it with ``pending_import_tasks``, and submit only missing
comment IDs. A partial task or changed decision requires investigation.
"""

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

_FITS = {"great_fit", "ok_fit", "skip_for_pilot"}
_REASONS = {
    "document_change",
    "not_useful_question",
    "external_document_unavailable",
    "unavailable_evidence",
    "requires_visual_interpretation",
    "too_complex",
    "other",
}


def _index(tasks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index only stable comment IDs, refusing duplicates and missing identities."""
    result: dict[str, dict[str, Any]] = {}
    for task in tasks:
        comment_id = task["data"]["comment_id"]
        if not isinstance(comment_id, str) or not comment_id or comment_id in result:
            raise ValueError(f"Missing or duplicate comment identity: {comment_id}")
        result[comment_id] = task
    return result


def _annotation(task: dict[str, Any]) -> dict[str, Any]:
    """Require exactly one completed human annotation and no pending drafts."""
    annotations = task.get("annotations", [])
    if len(annotations) != 1 or task.get("drafts"):
        raise ValueError(f"Expected one completed annotation: {task['data']['comment_id']}")
    annotation: dict[str, Any] = annotations[0]
    if annotation.get("was_cancelled") or not annotation.get("result"):
        raise ValueError("Cancelled or empty annotation cannot be migrated")
    return annotation


def decision(task: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    """Validate rating/reason semantics and return an order-independent reason set."""
    choices: dict[str, list[str]] = {}
    for result in _annotation(task)["result"]:
        name = result["from_name"]
        if name not in {"pilot_fit", "skip_reasons"} or name in choices:
            raise ValueError(f"Unexpected or duplicate decision field: {name}")
        if result["type"] != "choices" or result["to_name"] != "comment":
            raise ValueError("Unexpected annotation control")
        values = result["value"]["choices"]
        if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
            raise ValueError("Invalid choice values")
        if len(values) != len(set(values)):
            raise ValueError("Duplicate choice values")
        choices[name] = values
    fits = choices.get("pilot_fit", [])
    reasons = choices.get("skip_reasons", [])
    if len(fits) != 1 or fits[0] not in _FITS:
        raise ValueError("Missing or invalid pilot rating")
    if set(reasons) - _REASONS or (reasons and fits[0] != "skip_for_pilot"):
        raise ValueError("Invalid or inconsistent skip reasons")
    return fits[0], tuple(sorted(reasons))


def _reviewer(annotation: dict[str, Any]) -> int:
    """Normalize export and expanded task-read reviewer representations."""
    reviewer = annotation["completed_by"]
    return int(reviewer["id"] if isinstance(reviewer, dict) else reviewer)


def verify_backup(root: Path, expected_count: int = 50) -> list[dict[str, Any]]:
    """Verify every protected file and cross-check portable and native decisions."""
    manifest = json.loads((root / "manifest.json").read_bytes())
    required = {"label_studio_export.json", "decisions.json", "project.json", "label_config.xml"}
    if manifest["status"] != "verified" or not required <= manifest["files"].keys():
        raise ValueError("Incomplete protected backup manifest")
    for name, digest in manifest["files"].items():
        path = root / name
        if path.resolve().parent != root.resolve():
            raise ValueError("Backup filename escapes its directory")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Protected backup checksum mismatch: {name}")
    tasks: list[dict[str, Any]] = json.loads((root / "label_studio_export.json").read_bytes())
    indexed = _index(tasks)
    portable = json.loads((root / "decisions.json").read_bytes())
    decisions = {row["comment_id"]: row for row in portable}
    if len(indexed) != expected_count or len(decisions) != len(portable):
        raise ValueError("Backup count or portable identity mismatch")
    if indexed.keys() != decisions.keys() or manifest["task_count"] != len(indexed):
        raise ValueError("Backup population mismatch")
    ratings: Counter[str] = Counter()
    for comment_id, task in indexed.items():
        fit, reasons = decision(task)
        row = decisions[comment_id]
        annotation = _annotation(task)
        if (fit, reasons) != (row["fit"], tuple(sorted(row["skip_reasons"]))):
            raise ValueError(f"Native/portable decisions differ: {comment_id}")
        bindings = {
            "task_id": task["id"],
            "annotation_id": annotation["id"],
            "reviewer_id": _reviewer(annotation),
            "created_at": annotation["created_at"],
            "updated_at": annotation["updated_at"],
            "inventory_id": task["data"]["inventory_id"],
            "sample_sha256": task["data"]["sample_sha256"],
            "form_version": task["data"]["form_version"],
        }
        if any(row[key] != value for key, value in bindings.items()):
            raise ValueError(f"Native/portable provenance differs: {comment_id}")
        ratings[fit] += 1
    if dict(ratings) != manifest["rating_counts"]:
        raise ValueError("Backup rating totals mismatch")
    return tasks


def build_import_tasks(
    original: list[dict[str, Any]],
    replacements: list[dict[str, Any]],
    backup_manifest_sha256: str,
) -> list[dict[str, Any]]:
    """Join replacement context to original decisions without changing either input."""
    old = _index(original)
    new = _index(replacements)
    if old.keys() != new.keys():
        raise ValueError("Replacement must contain exactly the original comment IDs")
    prepared = []
    for comment_id, task in new.items():
        before = old[comment_id]
        decision(before)
        if task.get("annotations") or task.get("predictions"):
            raise ValueError("Replacement must be unrated")
        if before["data"]["comment_html"] != task["data"]["comment_html"]:
            raise ValueError(f"Comment text changed: {comment_id}")
        annotation = _annotation(before)
        data = copy.deepcopy(task["data"])
        provenance = {
            "schema": "task07a1.label_migration.v1",
            "backup_manifest_sha256": backup_manifest_sha256,
            "original_project_id": before["project"],
            "original_task_id": before["id"],
            "original_annotation": copy.deepcopy(annotation),
            "original_inventory_id": before["data"]["inventory_id"],
            "replacement_inventory_id": data["inventory_id"],
            "original_sample_sha256": before["data"]["sample_sha256"],
            "original_context_unit_ids": before["data"]["context_unit_ids"],
            "response_context_changed": any(
                before["data"][key] != data[key]
                for key in ("response_html", "context_html", "context_unit_ids")
            ),
        }
        prepared.append(
            {
                "data": data,
                "meta": {"label_migration": provenance},
                "annotations": [
                    {
                        "id": annotation["id"],
                        "result": copy.deepcopy(annotation["result"]),
                        "completed_by": _reviewer(annotation),
                        "was_cancelled": False,
                        "ground_truth": annotation.get("ground_truth", False),
                        "lead_time": annotation.get("lead_time"),
                    }
                ],
            }
        )
    return prepared


def pending_import_tasks(
    prepared: list[dict[str, Any]], existing: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Reconcile before each append; reject duplicates, partial writes, or drift.

    Call after any uncertain import outcome, with a fresh complete export. This
    is a single-writer protocol; concurrent imports into this project are unsafe.
    """
    wanted = _index(prepared)
    present = _index(existing)
    if present.keys() - wanted.keys():
        raise ValueError("Replacement project contains unexpected comments")
    for comment_id, task in present.items():
        expected = wanted[comment_id]
        if task["data"] != expected["data"] or task.get("meta") != expected["meta"]:
            raise ValueError(f"Imported context or provenance differs: {comment_id}")
        actual_annotation = _annotation(task)
        expected_annotation = _annotation(expected)
        if decision(task) != decision(expected):
            raise ValueError(f"Imported decision differs: {comment_id}")
        for field in ("result", "ground_truth", "lead_time"):
            if actual_annotation.get(field) != expected_annotation.get(field):
                raise ValueError(f"Imported annotation {field} differs: {comment_id}")
        if _reviewer(actual_annotation) != _reviewer(expected_annotation):
            raise ValueError(f"Imported reviewer differs: {comment_id}")
    return [task for key, task in wanted.items() if key not in present]


def verify_migration(
    prepared: list[dict[str, Any]], exported: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Verify complete population and return original/new identity mapping."""
    if pending_import_tasks(prepared, exported):
        raise ValueError("Replacement export is incomplete")
    mapping = []
    for task in exported:
        provenance = task["meta"]["label_migration"]
        fit, reasons = decision(task)
        mapping.append(
            {
                "comment_id": task["data"]["comment_id"],
                "original_task_id": provenance["original_task_id"],
                "original_annotation_id": provenance["original_annotation"]["id"],
                "replacement_task_id": task["id"],
                "replacement_annotation_id": _annotation(task)["id"],
                "replacement_project_id": task["project"],
                "fit": fit,
                "skip_reasons": list(reasons),
                "provenance": provenance,
            }
        )
    return sorted(mapping, key=lambda row: row["comment_id"])
