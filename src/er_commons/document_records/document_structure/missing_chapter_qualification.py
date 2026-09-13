"""Completion-last publication for compact missing-chapter qualification."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.document_records.document_structure.missing_chapters import (
    MissingChapterDecision,
)

JsonObject = dict[str, Any]


def verify_compact_qualification_packet(root: Path, *, expected_completion_sha256: str) -> None:
    """Verify completion-last inventory closure before consuming a qualification packet."""
    completion_path = root / "completion.json"
    inventory_path = root / "inventory.json"
    _verify_file(completion_path, expected_completion_sha256)
    completion = _read_json(completion_path)
    if completion.get("status") != "complete":
        raise ValueError(f"qualification packet is not complete: {root}")
    inventory_sha256 = completion.get("inventory_sha256")
    if not isinstance(inventory_sha256, str):
        raise ValueError(f"qualification completion lacks inventory seal: {root}")
    _verify_file(inventory_path, inventory_sha256)
    inventory = _read_json(inventory_path)
    files = inventory.get("files")
    if not isinstance(files, list):
        raise ValueError(f"qualification inventory lacks files: {root}")
    if completion.get("managed_file_count") != len(files):
        raise ValueError(f"qualification managed-file count differs: {root}")
    listed_paths: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            raise ValueError(f"qualification inventory entry differs: {root}")
        relative = Path(str(item.get("path")))
        relative_key = relative.as_posix()
        if relative.is_absolute() or ".." in relative.parts or relative_key in listed_paths:
            raise ValueError(f"qualification inventory path differs: {relative}")
        listed_paths.add(relative_key)
        path = root / relative
        _verify_file(path, str(item.get("sha256")))
        if path.stat().st_size != item.get("byte_size"):
            raise ValueError(f"qualification inventory size differs: {path}")
    observed_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name not in {"completion.json", "inventory.json"}
    }
    if observed_paths != listed_paths:
        raise ValueError(f"qualification managed-file closure differs: {root}")


def publish_missing_chapter_qualification(
    output_root: Path,
    *,
    decisions: tuple[MissingChapterDecision, ...],
    source_ref: JsonObject,
    policy_ref: JsonObject,
    schema_ref: JsonObject,
    decision_schema: JsonObject,
    limitations: tuple[str, ...] = (),
    amendment_ref: JsonObject | None = None,
) -> Path:
    """Publish one fresh source-free five-file packet without clobbering evidence."""
    if output_root.exists():
        raise FileExistsError(f"missing-chapter qualification already exists: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}-", dir=output_root.parent))
    try:
        ordered = tuple(
            sorted(decisions, key=lambda item: (item.source_id, item.chapter_marker or ""))
        )
        keys = [(item.source_id, item.chapter_marker) for item in ordered]
        if len(set(keys)) != len(keys):
            raise ValueError("missing-chapter qualification contains a duplicate chapter")
        records = [_decision_record(item, source_ref) for item in ordered]
        validator = Draft202012Validator(decision_schema)
        for record in records:
            errors = sorted(validator.iter_errors(record), key=lambda item: list(item.path))
            if errors:
                raise ValueError(f"invalid missing-chapter decision: {errors[0].message}")
        eligible = [record for record in records if record["status"] == "eligible"]
        status = (
            "review_required"
            if any(item.status == "review_required" for item in ordered)
            else "complete"
        )
        _write_jsonl(staging / "all_decisions.jsonl", records)
        _write_jsonl(staging / "eligible_decisions.jsonl", eligible)
        qualification = {
            "schema_version": "er_commons.recovery.missing_chapter_qualification.v1",
            "status": status,
            "source_ref": source_ref,
            "policy_ref": policy_ref,
            "decision_schema_ref": schema_ref,
            "counts": {
                name: sum(item.status == name for item in ordered)
                for name in (
                    "eligible",
                    "already_present",
                    "rejected",
                    "review_required",
                )
            },
            "limitations": list(limitations),
            "production_replay_status": "not_executed_task06g_owned",
            "task06e_acceptance_status": "pending_separate_astra_review",
            "terminal_replacement_review_status": "pending_task06h",
        }
        if amendment_ref is not None:
            qualification["amendment_ref"] = amendment_ref
        _write_json(staging / "qualification.json", qualification)
        managed = ["all_decisions.jsonl", "eligible_decisions.jsonl", "qualification.json"]
        files = [_file_entry(staging / relative, relative) for relative in managed]
        _write_json(
            staging / "inventory.json",
            {
                "schema_version": "er_commons.recovery.compact_inventory.v1",
                "files": files,
                "total_bytes": sum(int(item["byte_size"]) for item in files),
            },
        )
        _write_json(
            staging / "completion.json",
            {
                "schema_version": "er_commons.recovery.missing_chapter_completion.v1",
                "status": status,
                "inventory_sha256": _sha256(staging / "inventory.json"),
                "managed_file_count": len(managed),
                "decision_count": len(records),
                "decision_counts": {
                    name: sum(item.status == name for item in ordered)
                    for name in (
                        "eligible",
                        "already_present",
                        "rejected",
                        "review_required",
                    )
                },
                "eligible_decision_count": len(eligible),
            },
        )
        os.replace(staging, output_root)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_root / "completion.json"


def _decision_record(decision: MissingChapterDecision, source_ref: JsonObject) -> JsonObject:
    target = None
    if decision.status == "eligible" and decision.chapter_marker is not None:
        target = {
            "authority": "task06e_policy",
            "relative_path": (
                f"logical-targets/{decision.source_id}/chapter-{decision.chapter_marker}"
            ),
            "identity": f"logical-chapter-{decision.source_id}-{decision.chapter_marker}",
            "verification_mode": "pending_06g_materialization",
        }
    return decision.as_record(source_ref=source_ref, new_target_ref=target)


def _write_json(path: Path, value: JsonObject) -> None:
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def _write_jsonl(path: Path, values: list[JsonObject]) -> None:
    path.write_text(
        "".join(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n" for value in values)
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> JsonObject:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _verify_file(path: Path, expected_sha256: str) -> None:
    if not path.is_file() or _sha256(path) != expected_sha256:
        raise ValueError(f"checksum mismatch: {path}")


def _file_entry(path: Path, relative: str) -> JsonObject:
    return {"path": relative, "sha256": _sha256(path), "byte_size": path.stat().st_size}
