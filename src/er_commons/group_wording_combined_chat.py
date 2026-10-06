"""Replay a single combined queue with lazy proposals and explicit human decisions.

Hashes bind saved bytes supplied by the caller. Validation proves structural
provenance, not semantic faithfulness or truthful transcription of human speech.
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from er_commons.group_wording import digest, encoded
from er_commons.group_wording_combined import validate_packet

VERSION = "task08c.combined_chat_review.v1"


def _fields(value: dict[str, Any], fields: str) -> None:
    """Require exact fields so unrecognized content cannot enter review records."""
    if not isinstance(value, dict) or set(value) != set(fields.split()):
        raise ValueError("Unexpected or missing fields")


def _hash(value: str) -> None:
    """Require a lowercase SHA-256 digest."""
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise ValueError("Expected SHA-256 digest")


def _text(value: str) -> None:
    """Reject missing or blank attribution and explanatory text."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected nonblank text")


def new_journal(
    packet: dict[str, Any], *, packet_sha256: str, prompt_sha256: str, namespace: str
) -> dict[str, Any]:
    """Create an empty queue; historical approvals do not populate dispositions."""
    journal: dict[str, Any] = {
        "schema_version": VERSION,
        "namespace": namespace,
        "packet_sha256": packet_sha256,
        "prompt_sha256": prompt_sha256,
        "previous_snapshot_sha256": None,
        "events": [],
    }
    validate_journal(journal, packet, packet_sha256=packet_sha256, prompt_sha256=prompt_sha256)
    return journal


def append_event(previous: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Return a detached successor; validate it before no-clobber publication."""
    journal = copy.deepcopy(previous)
    journal["previous_snapshot_sha256"] = digest(encoded(previous))
    journal["events"].append(copy.deepcopy(event))
    return journal


def _proposal(proposal: dict[str, Any], source: dict[str, Any], journal: dict[str, Any]) -> None:
    """Bind one lazy source-only proposal or preserved historical wording."""
    _fields(
        proposal,
        "neutral_id packet_sha256 prompt_sha256 original_comment_sha256 "
        "comment_text_sha256 question stop_reason origin model source_artifact_sha256",
    )
    for key in ("packet_sha256", "prompt_sha256"):
        if proposal[key] != journal[key]:
            raise ValueError("Proposal input binding differs")
    for key in ("neutral_id", "original_comment_sha256", "comment_text_sha256"):
        if proposal[key] != source[key]:
            raise ValueError("Proposal source binding differs")
    question = proposal["question"]
    if question is None:
        _text(proposal["stop_reason"])
    else:
        _text(question)
        if proposal["stop_reason"] is not None:
            raise ValueError("Question cannot also carry a model stop")
    if proposal["origin"] == "astra":
        if proposal["model"] != "gpt-6-astra" or proposal["source_artifact_sha256"] is not None:
            raise ValueError("Astra proposal provenance differs")
    elif proposal["origin"] == "historical_approved_wording":
        _hash(proposal["source_artifact_sha256"])
        if question is None or proposal["model"] is not None:
            raise ValueError("Historical wording requires exact nonnull text")
    else:
        raise ValueError("Unsupported proposal origin")


def _display(event: dict[str, Any], record: dict[str, Any], journal: dict[str, Any]) -> None:
    """Retain exact source/display bytes and increment every displayed version."""
    _fields(
        event,
        "event_id timestamp chat_reference neutral_id kind display_version question "
        "question_sha256 unsupported_content source_support_note support_resolution "
        "proposal proposal_sha256",
    )
    history = record["display_history"]
    if event["display_version"] != f"{event['neutral_id']}-v{len(history) + 1}":
        raise ValueError("Display version must increment")
    if type(event["unsupported_content"]) is not bool:
        raise ValueError("Source-support flag must be boolean")
    _text(event["source_support_note"])
    resolution = event["support_resolution"]
    if record["unsupported_content"] and not event["unsupported_content"]:
        if resolution == "removed_unsupported_content":
            if event["question"] == history[-1]["question"]:
                raise ValueError("Removing unsupported content requires changed wording")
        elif resolution == "declined_unsupported_clarification":
            if history[-1]["unsupported_content"] or event["question"] != history[-1]["question"]:
                raise ValueError("Declining unsupported feedback must preserve supported wording")
        else:
            raise ValueError("Clearing unsupported content requires explicit source resolution")
    elif resolution != "none":
        raise ValueError("Source resolution requires a previously flagged issue")
    _proposal(event["proposal"], record, journal)
    if digest(encoded(event["proposal"])) != event["proposal_sha256"]:
        raise ValueError("Proposal checksum differs")
    if event["question"] != event["proposal"]["question"]:
        raise ValueError("Displayed wording differs from proposal")
    question = event["question"]
    expected = digest(question.encode()) if question is not None else None
    if event["question_sha256"] != expected:
        raise ValueError("Displayed question checksum differs")
    history.append(copy.deepcopy(event))
    record.update(
        state="pending", needs_redisplay=False, unsupported_content=event["unsupported_content"]
    )


def _decision(event: dict[str, Any], record: dict[str, Any], journal: dict[str, Any]) -> None:
    """Freeze only explicit approval of the current supported exact wording."""
    _fields(
        event,
        "event_id timestamp chat_reference neutral_id kind display_version actor statement "
        "decision explicit_approval approved_question approved_question_sha256",
    )
    _text(event["actor"])
    _text(event["statement"])
    decision = event["decision"]
    if decision not in {"approve", "exclude", "defer"}:
        raise ValueError("Human decision must approve, exclude or defer")
    display = record["display_history"][-1]
    if decision == "approve":
        if (
            record["needs_redisplay"]
            or record["unsupported_content"]
            or display["question"] is None
        ):
            raise ValueError("Approval requires redisplayed, supported nonnull wording")
        if (
            event["explicit_approval"] is not True
            or event["approved_question"] != display["question"]
            or event["approved_question_sha256"] != display["question_sha256"]
        ):
            raise ValueError("Approval must bind exact displayed wording")
        version = digest(
            encoded({"display": display, "approval": event, "packet": journal["packet_sha256"]})
        )
        record["frozen_question"] = {
            "question_id": f"task08c-{journal['namespace']}-{record['neutral_id']}-{version}",
            "question_version": version,
            "text": display["question"],
            "text_sha256": display["question_sha256"],
            "display_version": display["display_version"],
        }
    elif (
        event["explicit_approval"] is not False
        or event["approved_question"] is not None
        or event["approved_question_sha256"] is not None
    ):
        raise ValueError("Nonapproval cannot freeze text")
    record.update(
        state={"approve": "approved", "exclude": "excluded", "defer": "deferred"}[decision],
        disposition=copy.deepcopy(event),
    )


def validate_journal(
    journal: dict[str, Any],
    packet: dict[str, Any],
    *,
    packet_sha256: str,
    prompt_sha256: str,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Replay the saved queue and reject jumps, stale approvals and edited prefixes.

    Each continuation must receive its immediate predecessor. Full-chain replay
    remains the caller's responsibility when loading multiple saved snapshots.
    """
    validate_packet(packet)
    if digest(encoded(packet)) != packet_sha256:
        raise ValueError("Canonical packet checksum differs")
    _fields(
        journal,
        "schema_version namespace packet_sha256 prompt_sha256 previous_snapshot_sha256 events",
    )
    if journal["schema_version"] != VERSION:
        raise ValueError("Unsupported combined review version")
    _text(journal["namespace"])
    for key, expected in (("packet_sha256", packet_sha256), ("prompt_sha256", prompt_sha256)):
        _hash(expected)
        if journal[key] != expected:
            raise ValueError("Journal input binding differs")
    if not isinstance(journal["events"], list):
        raise ValueError("Events must be a list")
    if previous is None:
        if journal["previous_snapshot_sha256"] is not None:
            raise ValueError("Previous snapshot required")
    else:
        if journal["previous_snapshot_sha256"] != digest(encoded(previous)):
            raise ValueError("Previous snapshot checksum differs")
        for key in ("schema_version", "namespace", "packet_sha256", "prompt_sha256"):
            if journal[key] != previous[key]:
                raise ValueError("Snapshot input bindings changed")
        count = len(previous["events"])
        if journal["events"][:count] != previous["events"] or len(journal["events"]) <= count:
            raise ValueError("Snapshot must strictly append an unchanged prefix")
    records = [
        {
            **copy.deepcopy(row),
            "state": "pending",
            "display_history": [],
            "feedback_history": [],
            "disposition": None,
            "frozen_question": None,
            "needs_redisplay": False,
            "unsupported_content": False,
        }
        for row in packet["records"]
    ]
    current = 0
    for number, event in enumerate(journal["events"], 1):
        if type(event.get("event_id")) is not int or event["event_id"] != number:
            raise ValueError("Event IDs must be sequential")
        if current >= len(records) or event.get("neutral_id") != records[current]["neutral_id"]:
            raise ValueError("Only the current queue question can be reviewed")
        _text(event["chat_reference"])
        if datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00")).tzinfo is None:
            raise ValueError("Event timestamp requires timezone")
        record = records[current]
        if event["kind"] == "display":
            _display(event, record, journal)
            continue
        history = record["display_history"]
        if not history or event.get("display_version") != history[-1]["display_version"]:
            raise ValueError("Decision or feedback requires latest displayed version")
        if event["kind"] == "feedback":
            _fields(
                event,
                "event_id timestamp chat_reference neutral_id kind display_version actor "
                "statement unsupported_content",
            )
            _text(event["actor"])
            _text(event["statement"])
            if type(event["unsupported_content"]) is not bool:
                raise ValueError("Source-support flag must be boolean")
            record["feedback_history"].append(copy.deepcopy(event))
            record["needs_redisplay"] = True
            record["unsupported_content"] |= event["unsupported_content"]
        elif event["kind"] == "disposition":
            _decision(event, record, journal)
            current += 1
        else:
            raise ValueError("Unknown event kind")
    return {
        "schema_version": VERSION,
        "journal_sha256": digest(encoded(journal)),
        "records": records,
        "current_position": current + 1 if current < len(records) else None,
        "total": len(records),
        "status": "review_pass_complete" if current == len(records) else "pending",
        "advancing_neutral_ids": [r["neutral_id"] for r in records if r["state"] == "approved"],
        "deferred_neutral_ids": [r["neutral_id"] for r in records if r["state"] == "deferred"],
    }


def main() -> None:
    """Verify saved input bytes and the full snapshot chain; export no-clobber."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "export"))
    for name in ("journal", "packet", "prompt"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument(
        "--previous",
        type=Path,
        action="append",
        default=[],
        help="All predecessors in oldest-to-newest order; repeat per snapshot",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    packet_bytes = args.packet.read_bytes()
    bindings = {
        "packet_sha256": digest(packet_bytes),
        "prompt_sha256": digest(args.prompt.read_bytes()),
    }
    packet = json.loads(packet_bytes)
    previous = None
    result: dict[str, Any] = {}
    for path in [*args.previous, args.journal]:
        raw = path.read_bytes()
        journal = json.loads(raw)
        if raw != encoded(journal):
            raise ValueError("Snapshots must preserve canonical encoded journal bytes")
        result = validate_journal(journal, packet, **bindings, previous=previous)
        previous = journal
    if args.command == "export":
        if args.output is None:
            parser.error("export requires --output")
        with args.output.open("xb") as handle:
            handle.write(encoded(result))
    logging.basicConfig(level=logging.INFO)
    logging.info(
        "Combined review %s: position %s / %s",
        result["status"],
        result["current_position"],
        result["total"],
    )


if __name__ == "__main__":
    main()
