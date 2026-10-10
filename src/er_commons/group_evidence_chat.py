"""Display-bound Task08E evidence journal; preparation never creates human decisions.

Reuse Task08D's deterministic byte encoding and locked, fsynced append pattern.
Hashes attest replay integrity, not human identity; retain original chat references.
"""

from __future__ import annotations

import copy
import fcntl
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from er_commons.group_claims import digest, encoded

VERSION = "task08e.chat_review.v1"


def sha(value: Any) -> str:
    """Bind exact JSON values with the maintained review encoder."""
    return digest(encoded(value))


def _text(value: Any) -> str:
    """Reject absent provenance without normalizing the original text."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Nonblank text required")
    return value


def _items(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index per-question findings without pooling or merging any citations."""
    rows = packet["claim_findings"] + packet["beyond_claim_findings"]
    result = {_text(row["finding_id"]): row for row in rows}
    if len(result) != len(rows):
        raise ValueError("Duplicate finding identifier")
    return result


def _validate(packet: dict[str, Any]) -> None:
    """Guard display bindings; full canonical-source validation belongs to sealing."""
    if packet["schema_version"] != "task08e.research_packet.v1":
        raise ValueError("Unknown research packet schema")
    if (
        packet["human_decisions"]
        or packet["eligibility"] is not None
        or packet["disposition"] is not None
    ):
        raise ValueError("Research proposals cannot contain human decisions")
    _text(packet["frozen_input"]["case_id"])
    sources = {s["occurrence_id"]: s for s in packet["sources"]}
    if len(sources) != len(packet["sources"]):
        raise ValueError("Source occurrences require distinct identifiers")
    for item in _items(packet).values():
        if "claim" in item:
            if item["claim"] not in packet["frozen_input"]["approved_claims"]:
                raise ValueError("Claim does not bind an exact approved version")
        elif not item["citations"]:
            raise ValueError("Beyond-claim findings require source evidence")
        for citation in item["citations"]:
            if (
                citation["occurrence_id"] not in sources
                or sources[citation["occurrence_id"]]["candidate_id"] != citation["candidate_id"]
            ):
                raise ValueError("Missing source binding")
            if citation["relationship"] not in {
                "Support",
                "Partial",
                "Context",
                "Not support",
                "Contradicts",
            }:
                raise ValueError("Unknown proposed relationship")
            _text(citation["reason"])
            _text(citation["excerpt"])


def new_journal(
    packet: dict[str, Any], *, synthetic: bool = False, phase: str = "preparation"
) -> dict[str, Any]:
    """Create an empty, exact-packet-bound journal outside the preparation seal."""
    _validate(packet)
    if phase not in {"preparation", "review"}:
        raise ValueError("Unknown journal phase")
    return {
        "phase": phase,
        "schema_version": VERSION,
        "packet_sha256": sha(packet),
        "synthetic": synthetic,
        "events": [],
    }


def render_display(packet: dict[str, Any], finding_ids: list[str]) -> dict[str, Any]:
    """Save exact displayed findings, source copies and all frozen context.

    Full source and table-family payloads remain available alongside a readable
    overview. Acceptance is restricted to the explicitly enumerated finding IDs.
    """
    _validate(packet)
    items = _items(packet)
    if not finding_ids or len(finding_ids) != len(set(finding_ids)):
        raise ValueError("A nonempty, unique display scope is required")
    if not set(finding_ids) <= items.keys():
        raise ValueError("Unknown displayed finding")
    selected = [copy.deepcopy(items[fid]) for fid in finding_ids]
    source_ids = {c["occurrence_id"] for item in selected for c in item["citations"]}
    sources = [s for s in packet["sources"] if s["occurrence_id"] in source_ids]
    frozen = packet["frozen_input"]
    question = frozen["question"]
    if isinstance(question, dict):
        question = question.get("reviewed_question", question.get("text"))
    _text(question)
    lines = ["# Evidence review", "## Exact approved question", question]
    context = frozen.get("required_context")
    if context:
        lines += ["Upstream context and holds (Phase A research was separately authorized):"]
        if isinstance(context, dict) and "rules" in context:
            lines += ["- " + rule for rule in context["rules"]]
        else:
            lines += [json.dumps(context, ensure_ascii=False)]
    for part in frozen.get("reviewed_case", {}).get("question_parts", []):
        lines += [f"Question part {part['part_id']}: {part['text']}", part.get("explanation", "")]
    source_index = {s["occurrence_id"]: s for s in sources}
    for item in selected:
        lines += ["## " + item["finding_id"]]
        if "claim" in item:
            lines += ["Exact approved claim:", "> " + item["claim"]["text"]]
        else:
            lines += ["Advisory finding beyond approved claims:", item["summary"]]
        for citation in item["citations"]:
            source = source_index[citation["occurrence_id"]]
            title = source.get("citation_unit", {}).get("citation_label") or source.get(
                "title", source.get("source_id", citation["candidate_id"])
            )
            document = source.get("document_title") or source.get("source_id", "Source").replace(
                "_", " "
            )
            source_url = source.get("pdf_url", source.get("source_url"))
            page_numbers = source.get("physical_pages", [])
            source_link = (
                source_url.split("#")[0] + "#page=" + str(page_numbers[0])
                if source_url and page_numbers
                else None
            )
            source_title = f"{document} — {title}"
            if source_link:
                source_title = f"[{source_title}]({source_link})"
            lines += [
                f"Source occurrence: {citation['occurrence_id']}",
                f"{source_title} "
                f"({source.get('edition', 'edition retained in source binding')}); "
                f"printed pages {source.get('printed_labels', [])}; "
                f"PDF pages {source.get('physical_pages', [])}",
                f"Proposed {citation['relationship']}: {citation['reason']}",
                "Verbatim source excerpt:",
                "> " + citation["excerpt"].replace("\n", "\n> "),
            ]
        if item["limitations"]:
            lines += ["Limitations:"] + ["- " + value for value in item["limitations"]]
        if item.get("remaining_gaps"):
            lines += ["Remaining gaps:"] + ["- " + value for value in item["remaining_gaps"]]
    lines += [
        "## Problems still open",
        *["- " + value for value in packet.get("remaining_gaps", [])],
        *["- " + value for value in packet.get("limitations", [])],
        "No citation found means none was found within the saved search limits; "
        "it does not establish that evidence does not exist.",
        "Full passages, table families and source bindings are retained in the saved packet.",
    ]
    return {
        "packet_sha256": sha(packet),
        "finding_ids": list(finding_ids),
        "frozen_input": copy.deepcopy(frozen),
        "findings": selected,
        "sources": copy.deepcopy(sources),
        "text": "\n\n".join(lines),
    }


def render_case_display(packet: dict[str, Any], decisions: dict[str, Any]) -> dict[str, Any]:
    """Bind explicit case closeout to all evidence, decisions and remaining gaps."""
    return {
        "packet": copy.deepcopy(packet),
        "decisions": copy.deepcopy(decisions),
        "notice": "Review remaining gaps and limits; evidence approval is not answer adequacy.",
    }


def replay(packet: dict[str, Any], journal: dict[str, Any]) -> dict[str, Any]:
    """Rebuild state, rejecting hidden approvals, stale displays and torn chains."""
    _validate(packet)
    if journal["schema_version"] != VERSION or journal["packet_sha256"] != sha(packet):
        raise ValueError("Journal does not bind the exact initial packet")
    current = copy.deepcopy(packet)
    decisions: dict[str, Any] = {}
    displayed = None
    searches: dict[str, Any] = {}
    case_display = None
    case_decision = None
    previous = sha({k: v for k, v in journal.items() if k != "events"})
    for number, saved in enumerate(journal["events"], 1):
        event = copy.deepcopy(saved)
        event_hash = event.pop("event_sha256")
        if (
            event["sequence"] != number
            or event["previous_sha256"] != previous
            or sha(event) != event_hash
        ):
            raise ValueError("Broken event chain")
        previous = event_hash
        for key in ("actor", "chat_reference", "timestamp"):
            _text(event[key])
        if datetime.fromisoformat(event["timestamp"]).tzinfo is None:
            raise ValueError("Timezone-bearing timestamp required")
        kind = event["kind"]
        if journal["phase"] != "review":
            raise ValueError("Phase A preparation forbids human review events")
        if kind == "display":
            expected = render_display(current, event["display"]["finding_ids"])
            if event["display"] != expected:
                raise ValueError("Display must preserve exact current findings and sources")
            displayed = expected
        elif kind == "decision":
            if (
                displayed is None
                or event["display_sha256"] != sha(displayed)
                or event.get("explicit") is not True
            ):
                raise ValueError("Explicit decision must bind the current display")
            ids = event["finding_ids"]
            if (
                not ids
                or len(ids) != len(set(ids))
                or not set(ids) <= set(displayed["finding_ids"])
            ):
                raise ValueError("Decision exceeds displayed scope")
            if event["decision"] not in {"accept", "reject", "defer"}:
                raise ValueError("Unknown evidence decision")
            _text(event["feedback"])
            for fid in ids:
                decisions[fid] = copy.deepcopy(saved)
            case_display = None
            case_decision = None
        elif kind == "feedback":
            _text(event["feedback"])
        elif kind == "follow_up_plan":
            sid = _text(event["search_id"])
            if sid in searches:
                raise ValueError("Duplicate follow-up search")
            for key in ("purpose", "scope", "effort_budget"):
                _text(event[key])
            if event["packet_sha256"] != sha(current):
                raise ValueError("Follow-up must bind current packet")
            searches[sid] = {"plan": copy.deepcopy(saved), "receipt": None}
            case_display = None
            case_decision = None
        elif kind == "follow_up_result":
            sid = event["search_id"]
            if sid not in searches or searches[sid]["receipt"] is not None:
                raise ValueError("Follow-up requires a prior unused purpose and scope")
            if not isinstance(event["receipts"], list) or not event["receipts"]:
                raise ValueError("Exact query receipts required")
            _text(event["remaining_limits"])
            searches[sid]["receipt"] = copy.deepcopy(saved)
            case_display = None
            case_decision = None
        elif kind == "revise":
            revised = event["packet"]
            _validate(revised)
            _text(event["feedback"])
            if event["replaces_sha256"] != sha(current):
                raise ValueError("Revision does not bind preceding packet")
            if revised["frozen_input"] != current["frozen_input"]:
                raise ValueError("Frozen question, claims and context cannot change")
            # Conservative reopening also protects links whose source context changed.
            current = copy.deepcopy(revised)
            decisions = {}
            displayed = None
            case_display = None
            case_decision = None
        elif kind == "case_display":
            expected_case = render_case_display(current, decisions)
            if event["display"] != expected_case:
                raise ValueError("Case display must bind complete current evidence and decisions")
            case_display = expected_case
        elif kind == "case_decision":
            if (
                case_display is None
                or event["display_sha256"] != sha(case_display)
                or event.get("explicit") is not True
            ):
                raise ValueError("Case disposition requires explicit current case display")
            choice = event["decision"]
            if choice not in {"advance_to_08f", "hold", "stop"}:
                raise ValueError("Unknown case disposition")
            _text(event["feedback"])
            eligibility = event["eligibility"]
            _text(eligibility["reasons"])
            if eligibility["eligible"] is not None and type(eligibility["eligible"]) is not bool:
                raise ValueError(
                    "Eligibility requires an explicit human boolean or unresolved null"
                )
            if choice == "advance_to_08f" and (
                eligibility["eligible"] is not True
                or set(decisions) != set(_items(current))
                or any(d["decision"] == "defer" for d in decisions.values())
                or any(v["receipt"] is None for v in searches.values())
            ):
                raise ValueError("Advancement requires complete reviewed evidence and eligibility")
            case_decision = copy.deepcopy(saved)
        else:
            raise ValueError("Unknown event; eligibility and case disposition are not authorized")
    pending = [fid for fid in _items(current) if fid not in decisions]
    return {
        "packet": current,
        "decisions": decisions,
        "displayed": displayed,
        "follow_up_searches": searches,
        "pending_finding_ids": pending,
        "resume_finding_id": pending[0] if pending else None,
        "case_decision": case_decision,
        "event_count": len(journal["events"]),
        "journal_sha256": sha(journal),
    }


def add_event(
    packet: dict[str, Any], journal: dict[str, Any], event: dict[str, Any]
) -> dict[str, Any]:
    """Validate an appended copy, preserving every preceding version and feedback."""
    result = copy.deepcopy(journal)
    previous = (
        result["events"][-1]["event_sha256"]
        if result["events"]
        else sha({k: v for k, v in result.items() if k != "events"})
    )
    row = {
        **copy.deepcopy(event),
        "sequence": len(result["events"]) + 1,
        "previous_sha256": previous,
    }
    row["event_sha256"] = sha(row)
    result["events"].append(row)
    replay(packet, result)
    return result


def load_journal(
    path: Path, packet: dict[str, Any], *, synthetic: bool = False, phase: str = "preparation"
) -> dict[str, Any]:
    """Reload durable JSONL and fail closed on a partially written final event."""
    journal = new_journal(packet, synthetic=synthetic, phase=phase)
    content = path.read_text() if path.exists() else ""
    if content and not content.endswith("\n"):
        raise ValueError("Incomplete journal record; preserve before recovery")
    journal["events"] = [json.loads(line) for line in content.splitlines()]
    replay(packet, journal)
    return journal


def append_event(
    path: Path,
    packet: dict[str, Any],
    event: dict[str, Any],
    *,
    synthetic: bool = False,
    phase: str = "preparation",
) -> dict[str, Any]:
    """Append a validated event under an exclusive lock, then flush it to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        journal = load_journal(path, packet, synthetic=synthetic, phase=phase)
        updated = add_event(packet, journal, event)
        stream.seek(0, os.SEEK_END)
        stream.write(json.dumps(updated["events"][-1], ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return updated


def export_review(
    packet: dict[str, Any], journal: dict[str, Any], *, preparation: bool = True
) -> dict[str, Any]:
    """Export complete history; Phase A requires zero human interactions."""
    state = replay(packet, journal)
    if preparation and (journal["events"] or journal["phase"] != "preparation"):
        raise ValueError("Preparation export requires a blank human journal")
    return {
        "schema_version": VERSION,
        "status": "prepared, awaiting human review" if preparation else "review checkpoint",
        "synthetic": journal["synthetic"],
        "packet_sha256": sha(packet),
        "journal": copy.deepcopy(journal),
        "state": state,
        "human_decisions": copy.deepcopy(state["decisions"]),
        "eligibility": state["case_decision"]["eligibility"] if state["case_decision"] else None,
        "disposition": state["case_decision"]["decision"] if state["case_decision"] else None,
        "next_stage": None,
    }
