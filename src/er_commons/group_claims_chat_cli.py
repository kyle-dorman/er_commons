"""Resume Task08D human review through exact cards and a durable decision journal."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from er_commons.group_claims import digest, encoded
from er_commons.group_claims_batch import read_reference, write_new
from er_commons.group_claims_chat import (
    append_event,
    export_review,
    new_journal,
    render_card,
    replay,
)


def load_journal(path: Path, queue: dict[str, Any]) -> dict[str, Any]:
    """Load only complete saved events; malformed partial writes fail closed."""
    journal = new_journal(queue)
    if path.exists():
        content = path.read_bytes()
        if content and not content.endswith(b"\n"):
            raise ValueError("Incomplete journal record; preserve and repair before resuming")
        journal["events"] = [json.loads(line) for line in content.splitlines() if line.strip()]
    return journal


def next_review(queue: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Find the first undecided claim or separate case disposition in saved order."""
    for position, source in enumerate(queue["packet"]["cases"], 1):
        cid = source["case_id"]
        case = state["cases"][cid]
        if case["case_decision"] is not None and (
            case["case_decision"]["decision"] in {"hold", "stop"}
            or {c["claim_id"] for c in case["claims"]} == set(case["decisions"])
        ):
            continue
        # Card display order is computed for current versions after any revisions.
        from er_commons.group_claims_chat import _ordered

        for claim in _ordered(case["claims"]):
            if claim["claim_id"] not in case["decisions"]:
                if not case["history"]:
                    card = next(
                        c["card"]
                        for c in queue["cards"]
                        if c["case_id"] == cid and c["claim_id"] == claim["claim_id"]
                    )
                else:
                    card = render_card(
                        source,
                        case,
                        claim["claim_id"],
                        case_position=position,
                        case_count=len(state["cases"]),
                    )
                return {
                    "kind": "claim",
                    "case_id": cid,
                    "claim_id": claim["claim_id"],
                    "card": card,
                    "card_sha256": digest(card.encode()),
                }
        return {
            "kind": "case_summary",
            "case_id": cid,
            "question": source["question"]["text"],
            "question_parts": case["question_parts"],
            "decisions": case["decisions"],
            "claims": case["claims"],
            "case_sha256": digest(
                encoded({"claims": case["claims"], "question_parts": case["question_parts"]})
            ),
            "instruction": (
                "Request an explicit whole-case disposition and current-link "
                "confirmation; preserve unresolved question scope."
            ),
        }
    return {
        "kind": "complete",
        "instruction": "Validate export; starting 08E requires a separate request.",
    }


def main() -> None:
    """Read precomputed preparation or persist an explicit review event and export."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["validate", "next", "record", "export"])
    parser.add_argument(
        "--queue-reference",
        type=Path,
        required=True,
        help="JSON containing the exact queue path and sha256",
    )
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--event", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    queue = read_reference(json.loads(args.queue_reference.read_bytes()))
    journal = load_journal(args.journal, queue)
    state = replay(queue, journal)
    if args.action == "record":
        if args.event is None:
            parser.error("record requires --event")
        journal = append_event(args.journal, queue, json.loads(args.event.read_bytes()))
        result = {
            "saved_events": len(journal["events"]),
            "journal_sha256": digest(encoded(journal)),
        }
    elif args.action == "next":
        result = next_review(queue, state)
    elif args.action == "export":
        if args.output is None:
            parser.error("export requires --output")
        result = export_review(queue, journal)
        write_new(args.output, result)
    else:
        result = {
            "valid": True,
            "saved_events": state["event_count"],
            "queue_sha256": journal["queue_sha256"],
        }
    sys.stdout.write(encoded(result).decode())


if __name__ == "__main__":
    main()
