"""Completion-last publication for compact repeated-heading qualification."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.document_records.document_structure.repeated_headings import (
    RepeatedHeadingDecision,
)

JsonObject = dict[str, Any]


def publish_repeated_heading_qualification(
    output_root: Path,
    *,
    decisions: tuple[RepeatedHeadingDecision, ...],
    source_ref: JsonObject,
    policy_ref: JsonObject,
    schema_ref: JsonObject,
    decision_schema: JsonObject,
    generator_ref: JsonObject | None = None,
    human_decision_ref: JsonObject | None = None,
    limitations: tuple[str, ...] = (),
) -> Path:
    """Publish one fresh compact qualification directory without clobbering evidence."""
    if output_root.exists():
        raise FileExistsError(f"repeated-heading qualification already exists: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}-", dir=output_root.parent))
    try:
        ordered_decisions = tuple(
            sorted(decisions, key=lambda item: (item.heading_stable_keys, item.status))
        )
        group_keys = [item.heading_stable_keys for item in ordered_decisions]
        if len(set(group_keys)) != len(group_keys):
            raise ValueError("repeated-heading qualification contains a duplicate group")
        records = [
            _decision_record(item, source_ref, human_decision_ref) for item in ordered_decisions
        ]
        validator = Draft202012Validator(decision_schema)
        for record in records:
            errors = sorted(validator.iter_errors(record), key=lambda item: list(item.path))
            if errors:
                raise ValueError(f"invalid repeated-heading decision: {errors[0].message}")
        eligible = [record for record in records if record["status"] == "eligible"]
        qualification_status = (
            "review_required"
            if any(item.status == "review_required" for item in ordered_decisions)
            else "complete"
        )
        _write_jsonl(staging / "all_decisions.jsonl", records)
        _write_jsonl(staging / "eligible_decisions.jsonl", eligible)
        _write_json(
            staging / "qualification.json",
            {
                "schema_version": "er_commons.recovery.repeated_heading_qualification.v1",
                "status": qualification_status,
                "source_ref": source_ref,
                "policy_ref": policy_ref,
                "decision_schema_ref": schema_ref,
                "generator_ref": generator_ref,
                "counts": {
                    status: sum(item.status == status for item in ordered_decisions)
                    for status in ("eligible", "rejected", "review_required")
                },
                "limitations": list(limitations),
                "production_replay_status": "not_executed_task06g_owned",
                "task06d_acceptance_status": "pending_separate_astra_review",
                "terminal_replacement_review_status": "pending_task06h",
            },
        )
        managed = ["all_decisions.jsonl", "eligible_decisions.jsonl", "qualification.json"]
        files: list[JsonObject] = [
            _file_entry(staging / relative, relative) for relative in managed
        ]
        inventory: JsonObject = {
            "schema_version": "er_commons.recovery.compact_inventory.v1",
            "files": files,
            "total_bytes": sum(int(item["byte_size"]) for item in files),
        }
        _write_json(staging / "inventory.json", inventory)
        _write_json(
            staging / "completion.json",
            {
                "schema_version": "er_commons.recovery.repeated_heading_completion.v1",
                "status": qualification_status,
                "inventory_sha256": _sha256(staging / "inventory.json"),
                "managed_file_count": len(managed),
                "eligible_decision_count": len(eligible),
            },
        )
        os.replace(staging, output_root)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_root / "completion.json"


def _decision_record(
    decision: RepeatedHeadingDecision,
    source_ref: JsonObject,
    human_decision_ref: JsonObject | None,
) -> JsonObject:
    marker = decision.chapter_marker
    anchor = decision.anchor_heading_key
    new_target_ref = None
    if decision.status == "eligible" and marker is not None and anchor is not None:
        new_target_ref = {
            "authority": "task06d_policy",
            "relative_path": f"logical-targets/{marker}-{anchor}",
            "identity": f"logical-chapter-{marker}-{anchor}",
            "verification_mode": "pending_06g_materialization",
        }
    return decision.as_record(
        source_ref=source_ref,
        new_target_ref=new_target_ref,
        human_decision_ref=human_decision_ref,
    )


def _write_json(path: Path, value: JsonObject) -> None:
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def _write_jsonl(path: Path, values: list[JsonObject]) -> None:
    path.write_text(
        "".join(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n" for value in values)
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_entry(path: Path, relative: str) -> JsonObject:
    return {"path": relative, "sha256": _sha256(path), "byte_size": path.stat().st_size}
