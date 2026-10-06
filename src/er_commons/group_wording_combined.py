"""Qualify an all-selected v3 closeout as a combined comment-only review queue."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from er_commons import group_selection, group_selection_closeout
from er_commons.group_ranking import checked, digest, encoded
from er_commons.group_wording_input import validate_packet as validate_legacy_packet

VERSION = "task08c.comment_only.v2"


def validate_packet(packet: dict[str, Any]) -> None:
    """Preserve the strict safe-field boundary while permitting a combined queue."""
    if set(packet) != {"schema_version", "records"} or packet["schema_version"] != VERSION:
        raise ValueError("Unsupported combined packet fields or version")
    records = packet["records"]
    if not isinstance(records, list) or not records:
        raise ValueError("Combined packet requires records")
    for position, record in enumerate(records, 1):
        if not isinstance(record, dict) or record.get("neutral_id") != f"C{position:03d}":
            raise ValueError("Combined queue requires sequential neutral IDs")
        validate_legacy_packet(
            {
                "schema_version": "task08c.comment_only.v1",
                "records": [{**record, "neutral_id": "C001"}],
            }
        )


def project_selected(
    handoff: dict[str, Any], tasks: list[dict[str, Any]], decisions: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Check v3 selection identities before projecting only source-safe fields."""
    if (
        handoff.get("schema_version") != "task08b.handoff.v3"
        or handoff.get("process_revision") != group_selection_closeout.PROCESS_REVISION
        or handoff.get("policy") != group_selection_closeout.POLICY
        or handoff.get("status") != "complete"
        or decisions.get("status") != "complete"
    ):
        raise ValueError("Completed v3 closeout required")
    selected = handoff["selected_cases"]
    ids = [row["comment_id"] for row in selected]
    if (
        len(set(ids)) != len(ids)
        or ids != decisions["selected_comment_ids"]
        or ids != decisions["advancing_comment_ids"]
    ):
        raise ValueError("Selected identity closure differs")
    result = {}
    for row in selected:
        index = row["source_task_index"]
        if type(index) is not int or not 0 <= index < len(tasks):
            raise ValueError("Invalid source task index")
        data = tasks[index]["data"]
        original = data["original_comment"]
        if (
            data["comment_id"] != row["comment_id"]
            or original["unit_id"] != row["comment_id"]
            or original["unit_kind"] != "comment"
            or digest(encoded(original)) != row["original_comment_sha256"]
        ):
            raise ValueError("Original comment identity or hash differs")
        result[row["comment_id"]] = {
            "original_comment": original["text"],
            "comment_source_warnings": data["comment_source_warnings"],
            "original_comment_sha256": row["original_comment_sha256"],
            "comment_text_sha256": digest(original["text"].encode()),
        }
    return result


def prepare(result_path: Path, health_path: Path, data_root: Path, output: Path) -> dict[str, Any]:
    """Replay every saved group and write a new no-clobber, hash-bound intake."""
    references: list[dict[str, str]] = []

    def read(ref: dict[str, str]) -> bytes:
        """Verify each pinned reference without exposing its potentially restricted text."""
        path = Path(ref["path"])
        if not path.is_absolute():
            path = data_root / path
        content = checked(path, ref["sha256"])
        references.append({"path": str(path), "sha256": ref["sha256"]})
        return content

    result_bytes = checked(result_path)
    result = json.loads(result_bytes)
    if (
        result.get("status") != "complete"
        or result.get("schema_version") != "task08b.all_groups_export_result.v1"
        or result.get("handoff_version") != "task08b.handoff.v3"
    ):
        raise ValueError("Completed authoritative v3 result required")
    for ref in result["artifacts"].values():
        read(ref)
    summary = json.loads(read(result["artifacts"]["summary"]))
    csv_rows = list(
        csv.DictReader(io.StringIO(read(result["artifacts"]["selected_candidates"]).decode()))
    )
    if summary.get("status") != "complete":
        raise ValueError("Completed summary required")
    if [
        {key: str(value) for key, value in row.items()} for row in summary["selected_cases"]
    ] != csv_rows:
        raise ValueError("Summary and CSV saved order differ")
    if len({group["group"] for group in summary["groups"]}) != 42:
        raise ValueError("42 unique groups required")
    if len(csv_rows) != 57 or len({r["comment_id"] for r in csv_rows}) != 57:
        raise ValueError("Exactly 57 unique saved selections required")
    if summary["counts"] != result["counts"] or len(summary["groups"]) != 42:
        raise ValueError("All-group summary closure differs")
    if (
        read(result["artifacts"]["normalizer"])
        != Path(group_selection_closeout.__file__).read_bytes()
    ):
        raise ValueError("Maintained closeout normalizer differs from saved revision")
    sources: dict[str, dict[str, Any]] = {}
    provenance: dict[str, dict[str, Any]] = {}
    totals = dict.fromkeys(summary["counts"], 0)
    for group in summary["groups"]:
        completion = json.loads(read(group["completion"]))
        handoff = json.loads(read(group["handoff"]))
        if completion["status"] != "complete" or completion["handoff"] != group["handoff"]:
            raise ValueError("Group completion differs")
        manifest = json.loads(read(completion["manifest"]))
        for ref in manifest["files"].values():
            read(ref)
        read(manifest["normalizer"])
        read(manifest["upstream_prepared"])
        read(handoff["prepared_manifest"])
        tasks = group_selection.load_prepared(Path(handoff["prepared_manifest"]["path"]).parent)
        native = read(handoff["full_native_export"])
        decisions = json.loads(read(handoff["decisions"]))
        finish = json.loads(read(handoff["finish_confirmation"]))
        replay = group_selection_closeout.normalize_closeout_export(
            json.loads(native),
            tasks,
            project_id=handoff["project_id"],
            export_sha256=digest(native),
            finish_confirmation=finish,
        )
        if (
            replay != decisions
            or replay["counts"] != group["counts"]
            or replay["counts"] != handoff["counts"]
        ):
            raise ValueError("Saved decisions or counts do not replay")
        for key in ("group", "project_id", "input_sha256", "proposal_sha256", "process_revision"):
            if replay[key] != handoff[key]:
                raise ValueError("Handoff identity differs from replay")
        if handoff["group"] != group["group"] or handoff["project_id"] != group["project_id"]:
            raise ValueError("Summary group identity differs")
        for key, value in replay["counts"].items():
            totals[key] += value
        projected = project_selected(handoff, tasks, replay)
        if sources.keys() & projected.keys():
            raise ValueError("Duplicate comment across groups")
        sources.update(projected)
        for row in handoff["selected_cases"]:
            provenance[row["comment_id"]] = {
                **row,
                "group": group["group"],
                "project_id": group["project_id"],
                "handoff": group["handoff"],
            }
    if totals != summary["counts"] or set(sources) != {r["comment_id"] for r in csv_rows}:
        raise ValueError("Global candidate reconciliation differs")
    records, mappings = [], []
    for position, row in enumerate(csv_rows, 1):
        cid = row["comment_id"]
        mapping = provenance[cid]
        for key, value in row.items():
            if str(mapping[key]) != value:
                raise ValueError("Saved CSV identity or order source differs")
        neutral = f"C{position:03d}"
        records.append({"neutral_id": neutral, **sources[cid]})
        mappings.append({"neutral_id": neutral, "queue_position": position, **mapping})
    packet = {"schema_version": VERSION, "records": records}
    validate_packet(packet)
    health_bytes = checked(health_path)
    health = json.loads(health_bytes)
    for ref in health["artifacts"].values():
        read(ref)
    for name in ("completion", "manifest", "coordination_handoff"):
        read(health[name])
    historical = json.loads(read(health["artifacts"]["approved_questions"]))
    if (
        len(historical["questions"]) != 2
        or len({q["comment_id"] for q in historical["questions"]}) != 2
        or {q["comment_label"] for q in historical["questions"]} != set(health["selected_comments"])
    ):
        raise ValueError("Two historical health questions required")
    for question in historical["questions"]:
        source = sources[question["comment_id"]]
        if any(
            question[key] != source[key]
            for key in ("original_comment_sha256", "comment_text_sha256")
        ):
            raise ValueError("Historical question source differs")
        if digest(question["text"].encode()) != question["text_sha256"]:
            raise ValueError("Historical question text differs")
    files = {
        "comment_only.json": encoded(packet),
        "restricted_provenance.json": encoded(
            {
                "schema_version": "task08c.combined_provenance.v1",
                "not_for_wording_model": True,
                "mappings": mappings,
                "verified_references": references,
            }
        ),
        "historical_health_questions.json": encoded(
            {
                "schema_version": "task08c.historical_questions.v1",
                "new_pass_approvals": 0,
                "source": health["artifacts"]["approved_questions"],
                "questions": historical["questions"],
            }
        ),
        "intake_validator.py": Path(__file__).read_bytes(),
        "qualification.json": encoded(
            {
                "schema_version": "task08c.combined_intake_qualification.v1",
                "status": "passed",
                "groups_replayed": 42,
                "selected_unique": 57,
                "saved_csv_order_preserved": True,
                "similarity_filter_applied": False,
                "historical_health_revisited": 2,
                "new_pass_approvals": 0,
                "counts": totals,
                "verified_references": len(references),
                "mutable_historical_batch_register": (
                    "Not used as immutable input; historical hash remains in authoritative result."
                ),
            }
        ),
    }
    completion = {
        "schema_version": "task08c.input_completion.v2",
        "records": 57,
        "inputs": {
            "all_groups_result": {"path": str(result_path), "sha256": digest(result_bytes)},
            "health_result": {"path": str(health_path), "sha256": digest(health_bytes)},
        },
        "files": {name: digest(content) for name, content in files.items()},
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, content in files.items():
        (output / name).write_bytes(content)
    (output / "completion.json").write_bytes(encoded(completion))
    return completion
