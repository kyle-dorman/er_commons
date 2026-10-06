"""Prepare and replay strictly comment-only Task08C wording review packets."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

VERSION = "task08c.wording.v1"
ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "benchmarks/er_bench/schemas/task08c/v1"
FORM = ROOT / "configs/label_studio/task08c_wording_v1.xml"
PROMPT = ROOT / "docs/prompts/task08c_wording_v1.md"


def digest(content: bytes) -> str:
    """Hash exact saved bytes."""
    return hashlib.sha256(content).hexdigest()


def encoded(value: Any) -> bytes:
    """Serialize deterministic review artifacts without changing text values."""
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def validate_schema(value: Any, name: str) -> None:
    """Check a closed versioned schema before consuming payload fields."""
    Draft202012Validator(json.loads((SCHEMAS / name).read_bytes())).validate(value)


def _html(text: str) -> str:
    """Escape source-controlled prose for passive display."""
    return '<pre style="white-space:pre-wrap">' + html.escape(text) + "</pre>"


def build_tasks(
    packet: dict[str, Any],
    proposal: dict[str, Any],
    *,
    packet_sha256: str,
    proposal_sha256: str,
    namespace: str,
) -> list[dict[str, Any]]:
    """Project approved input fields only; predictions carry no human decision."""
    from er_commons.group_wording_input import validate_packet

    validate_packet(packet)
    validate_schema(proposal, "proposal.schema.json")
    if proposal["packet_sha256"] != packet_sha256:
        raise ValueError("Proposal is bound to a different packet")
    if len(packet["records"]) != len(proposal["records"]):
        raise ValueError("Proposal must cover the complete packet")
    tasks = []
    for source, proposed in zip(packet["records"], proposal["records"], strict=True):
        for key in ("neutral_id", "comment_text_sha256"):
            if source[key] != proposed[key]:
                raise ValueError("Proposal source binding differs")
        question, stop = proposed["question"], proposed["stop_reason"]
        if question is None:
            if not isinstance(stop, str) or not stop.strip():
                raise ValueError("A stopped proposal requires a reason")
        elif not question.strip() or stop is not None:
            raise ValueError("Propose a nonblank question or stop, never both")
        data = {
            **source,
            "form_version": VERSION,
            "namespace": namespace,
            "packet_sha256": packet_sha256,
            "proposal_sha256": proposal_sha256,
            "proposed_question": question,
            "warnings_html": "".join(_html(w) for w in source["comment_source_warnings"]),
        }
        result = (
            []
            if question is None
            else [
                {
                    "from_name": "question",
                    "to_name": "comment",
                    "type": "textarea",
                    "value": {"text": [question]},
                }
            ]
        )
        tasks.append({"data": data, "predictions": [{"model_version": VERSION, "result": result}]})
    validate_tasks(tasks)
    return tasks


def validate_tasks(tasks: list[dict[str, Any]]) -> None:
    """Reject hidden metadata and verify exact source displays and predictions."""
    validate_schema(tasks, "tasks.schema.json")
    first = tasks[0]["data"]
    seen = set()
    for task in tasks:
        data = task["data"]
        if data["neutral_id"] in seen:
            raise ValueError("Duplicate neutral ID")
        seen.add(data["neutral_id"])
        if any(data[k] != first[k] for k in ("namespace", "packet_sha256", "proposal_sha256")):
            raise ValueError("Mixed task bindings")
        if digest(data["original_comment"].encode()) != data["comment_text_sha256"]:
            raise ValueError("Source text hash differs")
        if data["warnings_html"] != "".join(_html(w) for w in data["comment_source_warnings"]):
            raise ValueError("Source warning display differs")
        question = data["proposed_question"]
        expected = (
            []
            if question is None
            else [
                {
                    "from_name": "question",
                    "to_name": "comment",
                    "type": "textarea",
                    "value": {"text": [question]},
                }
            ]
        )
        if task["predictions"][0]["result"] != expected:
            raise ValueError("Question prediction differs")


def _snapshots() -> dict[str, bytes]:
    """Collect explicit shared interfaces for no-clobber replay qualification."""
    result = {
        "form.xml": FORM.read_bytes(),
        "prompt.md": PROMPT.read_bytes(),
        "preparation.py": Path(__file__).read_bytes(),
        "exporter.py": Path(__file__).with_name("group_wording_export.py").read_bytes(),
        "input_validator.py": Path(__file__).with_name("group_wording_input.py").read_bytes(),
    }
    result["packet.schema.json"] = (SCHEMAS.parent / "packet.schema.json").read_bytes()
    for name in ("proposal", "tasks", "decisions"):
        result[f"{name}.schema.json"] = (SCHEMAS / f"{name}.schema.json").read_bytes()
    return result


def prepare(
    packet_path: Path, proposal_path: Path, output: Path, *, namespace: str
) -> dict[str, Any]:
    """Save self-contained clean inputs and shared interfaces in a new directory."""
    packet_bytes, proposal_bytes = packet_path.read_bytes(), proposal_path.read_bytes()
    tasks = build_tasks(
        json.loads(packet_bytes),
        json.loads(proposal_bytes),
        packet_sha256=digest(packet_bytes),
        proposal_sha256=digest(proposal_bytes),
        namespace=namespace,
    )
    payloads = {
        **_snapshots(),
        "comment_only.json": packet_bytes,
        "proposal.json": proposal_bytes,
        "tasks.json": encoded(tasks),
    }
    manifest = {
        "schema_version": VERSION,
        "namespace": namespace,
        "files": {name: digest(value) for name, value in payloads.items()},
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, value in {**payloads, "manifest.json": encoded(manifest)}.items():
        with (output / name).open("xb") as handle:
            handle.write(value)
    return manifest


def load_prepared(directory: Path) -> list[dict[str, Any]]:
    """Rebuild trusted tasks from sealed clean inputs, never from native exports."""
    manifest = json.loads((directory / "manifest.json").read_bytes())
    snapshots = _snapshots()
    expected_names = set(snapshots) | {"comment_only.json", "proposal.json", "tasks.json"}
    if (
        set(manifest) != {"schema_version", "namespace", "files"}
        or manifest["schema_version"] != VERSION
        or set(manifest["files"]) != expected_names
    ):
        raise ValueError("Prepared manifest closure or version differs")
    contents = {}
    for name in expected_names:
        contents[name] = (directory / name).read_bytes()
        if digest(contents[name]) != manifest["files"][name]:
            raise ValueError(f"Prepared checksum differs: {name}")
        if name in snapshots and contents[name] != snapshots[name]:
            raise ValueError("Shared interface changed; explicit version review required")
    tasks = build_tasks(
        json.loads(contents["comment_only.json"]),
        json.loads(contents["proposal.json"]),
        packet_sha256=digest(contents["comment_only.json"]),
        proposal_sha256=digest(contents["proposal.json"]),
        namespace=manifest["namespace"],
    )
    if encoded(tasks) != contents["tasks.json"]:
        raise ValueError("Prepared tasks differ from clean source rebuild")
    return tasks


def main() -> None:
    """Expose preparation, verified loading and no-clobber native export."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    for arg in ("packet", "proposal", "output"):
        prep.add_argument(f"--{arg}", type=Path, required=True)
    prep.add_argument("--namespace", choices=("dataset", "synthetic"), required=True)
    load = commands.add_parser("load")
    load.add_argument("--prepared", type=Path, required=True)
    export = commands.add_parser("export")
    for arg in ("prepared", "native-export", "output"):
        export.add_argument(f"--{arg}", type=Path, required=True)
    for arg in ("project-id", "reviewer-id"):
        export.add_argument(f"--{arg}", type=int, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.packet, args.proposal, args.output, namespace=args.namespace)
    elif args.command == "load":
        load_prepared(args.prepared)
    else:
        from er_commons.group_wording_export import normalize_export

        raw = args.native_export.read_bytes()
        result = normalize_export(
            json.loads(raw),
            load_prepared(args.prepared),
            project_id=args.project_id,
            reviewer_id=args.reviewer_id,
            export_sha256=digest(raw),
        )
        with args.output.open("xb") as handle:
            handle.write(encoded(result))
    logging.basicConfig(level=logging.INFO)
    logging.info("Task08C %s completed", args.command)


if __name__ == "__main__":
    main()
