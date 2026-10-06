"""Project verified selection inputs into a strictly comment-only wording packet.

Response-bearing bytes are consumed only by this deterministic boundary. Source
identities and selection provenance are saved separately from model/review input.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any

from er_commons.group_ranking import checked, digest, encoded, indexed, under
from er_commons.group_selection_export import normalize_export

VERSION = "task08c.comment_only.v1"


def validate_packet(packet: dict[str, Any]) -> None:
    """Reject extra fields, changed text, duplicate IDs and non-neutral identities."""
    if not isinstance(packet, dict) or set(packet) != {"schema_version", "records"}:
        raise ValueError("Comment-only packet requires exact fields")
    if packet["schema_version"] != VERSION:
        raise ValueError("Unsupported comment-only schema")
    records = packet["records"]
    if not isinstance(records, list) or not 1 <= len(records) <= 3:
        raise ValueError("Comment-only packet requires one to three records")
    keys = {
        "neutral_id",
        "original_comment",
        "comment_source_warnings",
        "original_comment_sha256",
        "comment_text_sha256",
    }
    for position, record in enumerate(records, 1):
        if not isinstance(record, dict) or set(record) != keys:
            raise ValueError("Comment-only record requires exact fields")
        if record["neutral_id"] != f"C{position:03d}":
            raise ValueError("Comment-only IDs must be sequential neutral IDs")
        text = record["original_comment"]
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Original comment must be nonblank exact text")
        warnings = record["comment_source_warnings"]
        if not isinstance(warnings, list) or any(
            not isinstance(w, str) or not w.strip() for w in warnings
        ):
            raise ValueError("Comment-source warnings must be text strings")
        for key in ("original_comment_sha256", "comment_text_sha256"):
            if not isinstance(record[key], str) or not re.fullmatch(r"[a-f0-9]{64}", record[key]):
                raise ValueError("Source hashes must be SHA-256 digests")
        if record["comment_text_sha256"] != digest(text.encode()):
            raise ValueError("Original comment text checksum differs")


def extract_comments(
    handoff: dict[str, Any],
    trusted_tasks: list[dict[str, Any]],
    decisions: dict[str, Any],
    authorized_comment_ids: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Extract an authorized selected set after independent selection validation.

    The caller verifies file hashes before invoking this pure projection. Neither
    selection reasons nor response fields are returned in the safe packet.
    """
    if (
        handoff.get("schema_version") != "task08b.handoff.v2"
        or handoff.get("process_revision") != "task08.selection_gate.v2"
        or handoff.get("status") != "complete"
        or decisions.get("status") != "complete"
    ):
        raise ValueError("A completed selection-gate v2 handoff is required")
    selected = handoff["selected_cases"]
    ids = [row["comment_id"] for row in selected]
    if (
        not authorized_comment_ids
        or len(set(authorized_comment_ids)) != len(authorized_comment_ids)
        or set(ids) != set(authorized_comment_ids)
        or len(ids) != len(authorized_comment_ids)
        or set(decisions["advancing_comment_ids"]) != set(ids)
        or set(decisions["selected_comment_ids"]) != set(ids)
    ):
        raise ValueError("Selected set differs from explicit authorization")
    tasks = indexed([task["data"] for task in trusted_tasks], "comment_id")
    saved = indexed(decisions["records"], "comment_id")
    selected_by_id = indexed(selected, "comment_id")
    records, mappings = [], []
    # Caller order establishes neutral IDs independently of advisory rank.
    for position, cid in enumerate(authorized_comment_ids, 1):
        data, selection = tasks[cid], selected_by_id[cid]
        decision = saved[cid]
        if (
            decision["state"] != "reviewed"
            or decision["decision"]["selection"] != "Selected"
            or not decision["decision"]["selection_reason"].strip()
        ):
            raise ValueError("Every source requires explicit selection with a reason")
        index = selection["source_task_index"]
        if (
            type(index) is not int
            or not 0 <= index < len(trusted_tasks)
            or trusted_tasks[index]["data"]["comment_id"] != cid
        ):
            raise ValueError("Selected source-task index differs")
        original = data["original_comment"]
        original_hash = digest(encoded(original))
        if (
            original["unit_kind"] != "comment"
            or original["unit_id"] != cid
            or original_hash != selection["original_comment_sha256"]
        ):
            raise ValueError("Selected original comment binding differs")
        record = {
            "neutral_id": f"C{position:03d}",
            "original_comment": original["text"],
            "comment_source_warnings": list(data["comment_source_warnings"]),
            "original_comment_sha256": original_hash,
            "comment_text_sha256": digest(original["text"].encode()),
        }
        records.append(record)
        mappings.append(
            {
                "neutral_id": record["neutral_id"],
                "comment_id": cid,
                "source_task_index": index,
                "original_comment_sha256": original_hash,
                "comment_text_sha256": record["comment_text_sha256"],
                "comment_source_warnings_sha256": digest(
                    encoded(record["comment_source_warnings"])
                ),
            }
        )
    packet = {"schema_version": VERSION, "records": records}
    validate_packet(packet)
    return packet, mappings


def prepare_comment_only(
    handoff_path: Path,
    data_root: Path,
    output: Path,
    authorized_comment_ids: list[str],
    expected_handoff_sha256: str,
) -> dict[str, Any]:
    """Verify upstream bytes and publish a fresh, no-clobber safe input directory."""
    if not re.fullmatch(r"[a-f0-9]{64}", expected_handoff_sha256):
        raise ValueError("An explicitly pinned handoff checksum is required")
    handoff = json.loads(checked(handoff_path, expected_handoff_sha256))
    references: dict[str, dict[str, str]] = {}

    def read_ref(name: str) -> Any:
        """Load one pinned reference while retaining only its identity for audit."""
        ref = handoff[name]
        path = under(data_root, ref["path"])
        content = checked(path, ref["sha256"])
        references[name] = {"path": ref["path"], "sha256": ref["sha256"]}
        return json.loads(content)

    manifest = read_ref("prepared_manifest")
    decisions = read_ref("decisions")
    finish = read_ref("finish_confirmation")
    restricted = read_ref("restricted_provenance")
    native_ref = restricted["native_export"]
    native_bytes = checked(under(data_root, native_ref["path"]), native_ref["sha256"])
    if (
        digest(native_bytes) != decisions["export_sha256"]
        or json.loads(native_bytes) != decisions["native_tasks"]
    ):
        raise ValueError("Saved native selection export differs")
    prepared_path = under(data_root, handoff["prepared_manifest"]["path"]).parent
    task_bytes = checked(prepared_path / "tasks.json", manifest["files"]["tasks.json"])
    tasks = json.loads(task_bytes)
    for key in ("group", "input_sha256", "proposal_sha256", "process_revision"):
        if manifest[key] != handoff[key] or decisions[key] != handoff[key]:
            raise ValueError("Upstream selection bindings differ")
    if decisions["project_id"] != handoff["project_id"]:
        raise ValueError("Selection project binding differs")
    rebuilt = normalize_export(
        decisions["native_tasks"],
        tasks,
        project_id=handoff["project_id"],
        export_sha256=decisions["export_sha256"],
        finish_confirmation=finish,
    )
    if rebuilt != decisions:
        raise ValueError("Selection decisions do not reproduce from saved native state")
    packet, mappings = extract_comments(handoff, tasks, rebuilt, authorized_comment_ids)
    packet_bytes = encoded(packet)
    provenance = {
        "schema_version": "task08c.restricted_input.v1",
        "not_for_wording_model": True,
        "handoff": {"path": str(handoff_path), "sha256": expected_handoff_sha256},
        "upstream_references": references,
        "prepared_tasks": {"path": str(prepared_path / "tasks.json"), "sha256": digest(task_bytes)},
        "comment_only_sha256": digest(packet_bytes),
        "mappings": mappings,
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "comment_only.json").write_bytes(packet_bytes)
    (output / "restricted_provenance.json").write_bytes(encoded(provenance))
    snapshots = {
        "preparation.py": Path(__file__).read_bytes(),
        "packet.schema.json": (
            Path(__file__).resolve().parents[2]
            / "benchmarks/er_bench/schemas/task08c/packet.schema.json"
        ).read_bytes(),
    }
    for name, content in snapshots.items():
        (output / name).write_bytes(content)
    completion = {
        "schema_version": "task08c.input_completion.v1",
        "records": len(mappings),
        "files": {
            "comment_only.json": digest(packet_bytes),
            "restricted_provenance.json": digest(encoded(provenance)),
            **{name: digest(content) for name, content in snapshots.items()},
        },
    }
    (output / "completion.json").write_bytes(encoded(completion))
    return completion


def main() -> None:
    """Expose deterministic projection without displaying response-bearing records."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("handoff", "data-root", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--expected-handoff-sha256", required=True)
    parser.add_argument("--comment-id", action="append", required=True)
    args = parser.parse_args()
    prepare_comment_only(
        args.handoff, args.data_root, args.output, args.comment_id, args.expected_handoff_sha256
    )
    logging.basicConfig(level=logging.INFO)
    logging.info("Comment-only input published: %s", args.output)


if __name__ == "__main__":
    main()
