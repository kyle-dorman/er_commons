"""Guard human decisions and safe retry boundaries independently of the server."""

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.pilot_label_migration import (
    build_import_tasks,
    decision,
    pending_import_tasks,
    verify_backup,
    verify_migration,
)


def _original(comment_id: str = "c1") -> dict[str, Any]:
    """Create a completed Skip annotation with two independent reasons."""
    return {
        "id": 10,
        "project": 1,
        "data": {
            "comment_id": comment_id,
            "comment_html": "unchanged comment",
            "response_html": "direct response",
            "context_html": "old context",
            "context_unit_ids": [comment_id, "r1"],
            "inventory_id": "old-inventory",
            "sample_sha256": "old-sample",
            "form_version": "form-v1",
        },
        "annotations": [
            {
                "id": 20,
                "completed_by": 1,
                "was_cancelled": False,
                "ground_truth": False,
                "lead_time": 12.5,
                "created_at": "2026-09-24T16:00:00Z",
                "updated_at": "2026-09-24T16:01:00Z",
                "result": [
                    {
                        "from_name": "pilot_fit",
                        "to_name": "comment",
                        "type": "choices",
                        "value": {"choices": ["skip_for_pilot"]},
                    },
                    {
                        "from_name": "skip_reasons",
                        "to_name": "comment",
                        "type": "choices",
                        "value": {"choices": ["document_change", "unavailable_evidence"]},
                    },
                ],
            }
        ],
    }


def _prepared() -> list[dict[str, Any]]:
    """Prepare a changed context without modifying the old task."""
    old = _original()
    replacement = {"data": copy.deepcopy(old["data"])}
    replacement["data"].update(inventory_id="new-inventory", context_html="new context")
    return build_import_tasks([old], [replacement], "backup-sha")


def _export(prepared: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Simulate IDs and timestamps assigned by the installed bulk importer."""
    result = copy.deepcopy(prepared)
    for task in result:
        task.update(id=100, project=2)
        task["annotations"][0].update(id=200, created_at="new time", updated_at="new time")
    return result


def test_provenance_survives_server_ids_and_timestamps() -> None:
    """New database timestamps cannot replace original decision provenance."""
    prepared = _prepared()
    mapping = verify_migration(prepared, _export(prepared))
    assert mapping[0]["original_annotation_id"] == 20
    assert mapping[0]["replacement_annotation_id"] == 200
    provenance = mapping[0]["provenance"]
    assert provenance["original_annotation"]["created_at"] == "2026-09-24T16:00:00Z"
    assert provenance["response_context_changed"] is True
    assert prepared[0]["annotations"][0]["result"] == _original()["annotations"][0]["result"]
    assert "predictions" not in prepared[0]


def test_retry_reconciles_by_comment_id_and_stops_on_partial_annotations() -> None:
    """A successful but uncertain POST produces no second import on retry."""
    prepared = _prepared()
    assert pending_import_tasks(prepared, []) == prepared
    exported = _export(prepared)
    assert pending_import_tasks(prepared, exported) == []
    exported[0]["annotations"] = []
    with pytest.raises(ValueError, match="one completed"):
        pending_import_tasks(prepared, exported)
    with pytest.raises(ValueError, match="incomplete"):
        verify_migration(prepared, [])


@pytest.mark.parametrize("field", ["result", "completed_by", "meta", "data"])
def test_changed_labels_reviewer_or_context_stop_retry(field: str) -> None:
    """Do not overwrite either unexpected human decisions or context changes."""
    prepared = _prepared()
    exported = _export(prepared)
    if field == "result":
        exported[0]["annotations"][0]["result"][1]["value"]["choices"] = []
    elif field == "completed_by":
        exported[0]["annotations"][0][field] = 2
    else:
        exported[0][field]["unexpected"] = True
    with pytest.raises(ValueError, match="differs"):
        pending_import_tasks(prepared, exported)


def test_duplicate_identity_or_annotations_are_not_silently_reused() -> None:
    """Duplicate comment rows and multiple human decisions require investigation."""
    prepared = _prepared()
    exported = _export(prepared)
    with pytest.raises(ValueError, match="duplicate"):
        pending_import_tasks(prepared, exported * 2)
    exported[0]["annotations"] *= 2
    with pytest.raises(ValueError, match="one completed"):
        pending_import_tasks(prepared, exported)


def test_population_and_comment_text_must_match() -> None:
    """Never match on order or silently remap a changed comment."""
    old = _original()
    new = {"data": copy.deepcopy(old["data"])}
    new["data"]["comment_id"] = "other"
    with pytest.raises(ValueError, match="exactly"):
        build_import_tasks([old], [new], "sha")
    new["data"]["comment_id"] = "c1"
    new["data"]["comment_html"] = "changed"
    with pytest.raises(ValueError, match="text changed"):
        build_import_tasks([old], [new], "sha")


def test_reason_sets_and_inconsistent_controls() -> None:
    """Portable decisions use reason sets but reject repeated/invalid controls."""
    task = _original()
    expected = decision(task)
    task["annotations"][0]["result"][1]["value"]["choices"].reverse()
    assert decision(task) == expected
    task["annotations"][0]["result"][0]["value"]["choices"] = ["great_fit"]
    with pytest.raises(ValueError, match="inconsistent"):
        decision(task)


def test_backup_checksums_and_portable_provenance(tmp_path: Path) -> None:
    """A byte-level backup change fails before any migration data are built."""
    task = _original()
    annotation = task["annotations"][0]
    portable = {
        "comment_id": "c1",
        "task_id": 10,
        "annotation_id": 20,
        "fit": "skip_for_pilot",
        "skip_reasons": ["document_change", "unavailable_evidence"],
        "reviewer_id": 1,
        "created_at": annotation["created_at"],
        "updated_at": annotation["updated_at"],
        "inventory_id": "old-inventory",
        "sample_sha256": "old-sample",
        "form_version": "form-v1",
    }
    payloads = {
        "label_studio_export.json": json.dumps([task]),
        "decisions.json": json.dumps([portable]),
        "project.json": "{}",
        "label_config.xml": "<View/>",
    }
    seals = {}
    for name, value in payloads.items():
        (tmp_path / name).write_text(value)
        seals[name] = hashlib.sha256(value.encode()).hexdigest()
    manifest = {
        "status": "verified",
        "task_count": 1,
        "rating_counts": {"skip_for_pilot": 1},
        "files": seals,
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    assert verify_backup(tmp_path, expected_count=1) == [task]
    (tmp_path / "decisions.json").write_text("[]")
    with pytest.raises(ValueError, match="checksum"):
        verify_backup(tmp_path, expected_count=1)
