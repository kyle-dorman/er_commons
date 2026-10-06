"""Validate append-only chat review snapshots and freeze explicitly approved text.

The journal records human statements without interpreting their language. A
curator must accurately transcribe explicit decisions; structural validation
cannot establish semantic faithfulness or prove a statement was truly approval.
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.group_wording import digest, encoded, validate_schema
from er_commons.group_wording_input import validate_packet

VERSION = "task08c.chat_review.v1"
SCHEMA = (
    Path(__file__).resolve().parents[2]
    / "benchmarks/er_bench/schemas/task08c/chat_v1/journal.schema.json"
)


def new_journal(
    packet: dict[str, Any],
    proposal: dict[str, Any],
    *,
    packet_sha256: str,
    proposal_sha256: str,
    prompt_sha256: str,
    namespace: str = "dataset",
) -> dict[str, Any]:
    """Create an empty pending journal without importing any human dispositions."""
    journal: dict[str, Any] = {
        "schema_version": VERSION,
        "process_revision": VERSION,
        "namespace": namespace,
        "packet_sha256": packet_sha256,
        "proposal_sha256": proposal_sha256,
        "prompt_sha256": prompt_sha256,
        "model": "gpt-6-astra",
        "previous_snapshot_sha256": None,
        "events": [],
    }
    validate_journal(
        journal,
        packet,
        proposal,
        packet_sha256=packet_sha256,
        proposal_sha256=proposal_sha256,
        prompt_sha256=prompt_sha256,
    )
    return journal


def _inputs(packet: dict[str, Any], proposal: dict[str, Any], packet_sha256: str) -> None:
    """Require the unchanged clean source and one bound proposal per comment."""
    validate_packet(packet)
    validate_schema(proposal, "proposal.schema.json")
    if proposal["packet_sha256"] != packet_sha256:
        raise ValueError("Proposal packet binding differs")
    if len(packet["records"]) != len(proposal["records"]):
        raise ValueError("Proposal does not cover the complete packet")
    for source, row in zip(packet["records"], proposal["records"], strict=True):
        if any(source[k] != row[k] for k in ("neutral_id", "comment_text_sha256")):
            raise ValueError("Proposal source identity differs")
        question, stop = row["question"], row["stop_reason"]
        if question is None:
            if not isinstance(stop, str) or not stop.strip():
                raise ValueError("Null proposal needs its preserved model stop reason")
        elif not question.strip() or stop is not None:
            raise ValueError("Proposal must be a nonblank question or a stop")


def _timestamp(value: str) -> None:
    """Reject events with ambiguous timezone-free timestamps."""
    if datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is None:
        raise ValueError("Chat event timestamp requires timezone")


def _display(event: dict[str, Any], record: dict[str, Any], proposal: dict[str, Any]) -> None:
    """Bind the first display to its proposal and revised displays to new versions."""
    displays = record["display_history"]
    expected = f"{event['neutral_id']}-v{len(displays) + 1}"
    if event["display_version"] != expected:
        raise ValueError("Display versions must increment per comment")
    question = event["question"]
    if question is not None and not question.strip():
        raise ValueError("Displayed question must be nonblank or null")
    expected_sha = digest(question.encode()) if question is not None else None
    if event["question_sha256"] != expected_sha:
        raise ValueError("Displayed exact text hash differs")
    if not displays:
        if (
            event["origin"] != "original_proposal"
            or question != proposal["question"]
            or event["support_resolution"] != "none"
        ):
            raise ValueError("First display must preserve the original proposal exactly")
    else:
        if event["origin"] != "revision":
            raise ValueError("Later displays must be explicit revisions")
        if not event["source_support_note"].strip():
            raise ValueError("Revisions require a source support note")
        if record["unsupported_content"] and not event["unsupported_content"]:
            resolution = event["support_resolution"]
            if resolution == "none":
                raise ValueError(
                    "Unsupported content requires an explicit source-grounded resolution"
                )
            if resolution == "declined_unsupported_clarification" and (
                displays[-1]["unsupported_content"] or question != displays[-1]["question"]
            ):
                raise ValueError(
                    "Declining feedback cannot clear flagged or changed displayed wording"
                )
            if resolution == "removed_unsupported_content" and question == displays[-1]["question"]:
                raise ValueError("Removing unsupported content requires changed wording")
        elif event["support_resolution"] != "none":
            raise ValueError("Support resolution requires a previously flagged clarification")
    displays.append(copy.deepcopy(event))
    record.update(
        state="pending",
        latest_display_version=event["display_version"],
        unsupported_content=event["unsupported_content"],
        frozen_question=None,
        disposition=None,
        needs_redisplay=False,
    )


def _disposition(event: dict[str, Any], record: dict[str, Any], journal: dict[str, Any]) -> None:
    """Freeze only an explicit decision naming the latest exact displayed version."""
    if (
        not record["display_history"]
        or event["display_version"] != record["latest_display_version"]
    ):
        raise ValueError("Disposition must reference the latest displayed version")
    display = record["display_history"][-1]
    if not event["actor"].strip() or not event["statement"].strip():
        raise ValueError("Disposition requires verbatim human statement and actor")
    decision = event["decision"]
    if decision == "approve":
        if record["needs_redisplay"]:
            raise ValueError("Feedback requires a fresh display before exact approval")
        if record["unsupported_content"] or display["question"] is None:
            raise ValueError("Unsupported content or null question cannot be approved")
        if (
            event["explicit_approval"] is not True
            or event["approved_question"] != display["question"]
            or event["approved_question_sha256"] != display["question_sha256"]
        ):
            raise ValueError("Approval must explicitly bind exact displayed wording and hash")
        binding = {
            key: journal[key]
            for key in ("packet_sha256", "proposal_sha256", "prompt_sha256", "model")
        }
        version = digest(
            encoded(
                {
                    **binding,
                    "source": record["original_comment_sha256"],
                    "display_version": display["display_version"],
                    "approval": event,
                }
            )
        )
        record["frozen_question"] = {
            "question_id": f"task08c-{record['neutral_id']}-{version}",
            "question_version": version,
            "text": display["question"],
            "text_sha256": display["question_sha256"],
            "display_version": display["display_version"],
            **binding,
            "approval": copy.deepcopy(event),
        }
        record["state"] = "approved"
    else:
        if (
            event["explicit_approval"] is not False
            or event["approved_question"] is not None
            or event["approved_question_sha256"] is not None
        ):
            raise ValueError("Nonapproval cannot carry frozen text or explicit approval")
        record.update(
            state="excluded" if decision == "exclude" else "unresolved", frozen_question=None
        )
    record["disposition"] = copy.deepcopy(event)


def validate_journal(
    journal: dict[str, Any],
    packet: dict[str, Any],
    proposal: dict[str, Any],
    *,
    packet_sha256: str,
    proposal_sha256: str,
    prompt_sha256: str,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Replay every event, preserving versions and invalidating approval on feedback.

    Hash arguments must come from verified saved input bytes. A predecessor hash
    binds canonical encoded journal bytes; callers preserve each snapshot intact.
    """
    Draft202012Validator(json.loads(SCHEMA.read_bytes())).validate(journal)
    _inputs(packet, proposal, packet_sha256)
    for key, expected in (
        ("packet_sha256", packet_sha256),
        ("proposal_sha256", proposal_sha256),
        ("prompt_sha256", prompt_sha256),
    ):
        if journal[key] != expected:
            raise ValueError(f"Journal {key} differs from saved inputs")
    if previous is None:
        if journal["previous_snapshot_sha256"] is not None:
            raise ValueError("Previous snapshot required for append-only validation")
    else:
        Draft202012Validator(json.loads(SCHEMA.read_bytes())).validate(previous)
        if journal["previous_snapshot_sha256"] != digest(encoded(previous)):
            raise ValueError("Previous snapshot hash differs")
        for key in set(journal) - {"events", "previous_snapshot_sha256"}:
            if journal[key] != previous[key]:
                raise ValueError("Journal source/version bindings cannot change")
        if journal["events"][: len(previous["events"])] != previous["events"]:
            raise ValueError("Journal events must preserve an unchanged append-only prefix")
    records = {
        source["neutral_id"]: {
            **copy.deepcopy(source),
            "state": "pending",
            "latest_display_version": None,
            "display_history": [],
            "feedback_history": [],
            "disposition": None,
            "unsupported_content": False,
            "needs_redisplay": False,
            "frozen_question": None,
        }
        for source in packet["records"]
    }
    proposals = {row["neutral_id"]: row for row in proposal["records"]}
    for position, event in enumerate(journal["events"], 1):
        if event["event_id"] != position or event["neutral_id"] not in records:
            raise ValueError("Unknown comment or nonsequential journal event")
        _timestamp(event["timestamp"])
        if not event["chat_reference"].strip():
            raise ValueError("Chat event requires a reference")
        record = records[event["neutral_id"]]
        if event["kind"] == "display":
            _display(event, record, proposals[event["neutral_id"]])
        elif event["kind"] == "feedback":
            if (
                not record["display_history"]
                or event["display_version"] != record["latest_display_version"]
            ):
                raise ValueError("Feedback must reference the latest displayed version")
            if not event["statement"].strip() or not event["actor"].strip():
                raise ValueError("Feedback requires verbatim statement and actor")
            record["feedback_history"].append(copy.deepcopy(event))
            record.update(
                state="pending",
                frozen_question=None,
                disposition=None,
                needs_redisplay=True,
                unsupported_content=record["unsupported_content"] or event["unsupported_content"],
            )
        else:
            _disposition(event, record, journal)
    values = list(records.values())
    return {
        "schema_version": VERSION,
        "process_revision": VERSION,
        "journal_sha256": digest(encoded(journal)),
        "journal": copy.deepcopy(journal),
        "records": values,
        "advancing_neutral_ids": [r["neutral_id"] for r in values if r["state"] == "approved"],
        "status": "complete"
        if all(r["state"] in {"approved", "excluded"} for r in values)
        else "pending",
    }


def main() -> None:
    """Validate saved journals or export into a fresh file without mutating inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "export"))
    for name in ("journal", "packet", "proposal", "prompt"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    packet_bytes, proposal_bytes = args.packet.read_bytes(), args.proposal.read_bytes()
    result = validate_journal(
        json.loads(args.journal.read_bytes()),
        json.loads(packet_bytes),
        json.loads(proposal_bytes),
        packet_sha256=digest(packet_bytes),
        proposal_sha256=digest(proposal_bytes),
        prompt_sha256=digest(args.prompt.read_bytes()),
        previous=json.loads(args.previous.read_bytes()) if args.previous else None,
    )
    if args.command == "export":
        if args.output is None:
            parser.error("export requires --output")
        with args.output.open("xb") as handle:
            handle.write(encoded(result))
    logging.basicConfig(level=logging.INFO)
    logging.info("Task08C chat %s: %s", args.command, result["status"])


if __name__ == "__main__":
    main()
