"""Source-bound cards and append-only production Task08D chat decisions.

Human statements are transcribed, never classified automatically. Hash chains
protect replay integrity, not reviewer authenticity; preserve original chat receipts.
"""

from __future__ import annotations

import copy
import fcntl
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError  # type: ignore[import-untyped]

from er_commons.group_claims import digest, encoded
from er_commons.group_claims_input import validate_packet
from er_commons.group_claims_inventory import validate_inventory

VERSION = "task08d.chat_review.v1"
SCHEMA = (
    Path(__file__).resolve().parents[2]
    / "benchmarks/er_bench/schemas/task08d/chat_v1/journal.schema.json"
)


def _sha(value: Any) -> str:
    """Bind exact deterministic JSON content."""
    return digest(encoded(value))


def _index(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    """Reject duplicated identifiers before indexing."""
    result = {row[key]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"Duplicate {key}")
    return result


def _chain(claim: dict[str, Any], claims: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve support to a direct claim, rejecting cycles and dangling links."""
    seen = {claim["claim_id"]}
    result = []
    while claim["relationship"] == "supporting":
        if len(claim["targets"]) != 1:
            raise ValueError("Supporting claim requires exactly one target")
        target = claim["targets"][0]
        if target in seen or target not in claims:
            raise ValueError("Cyclic or dangling support")
        seen.add(target)
        claim = claims[target]
        result.append(claim)
    if result and claim["relationship"] != "direct":
        raise ValueError("Support chain must reach a direct claim")
    return result


def _validate_claims(source: dict[str, Any], case: dict[str, Any]) -> None:
    """Require anchored claims, exact parts, and well-formed relationship graphs."""
    schema_path = SCHEMA.parent.parent / "v1/proposal.schema.json"
    case_schema = json.loads(schema_path.read_bytes())["properties"]["cases"]["items"]
    clean = {
        "case_id": case["case_id"],
        "question_parts": case["question_parts"],
        "claims": [{k: v for k, v in c.items() if k != "version"} for c in case["claims"]],
    }
    try:
        Draft202012Validator(case_schema).validate(clean)
    except ValidationError as exc:
        raise ValueError(exc.message) from exc
    claims = _index(case["claims"], "claim_id")
    parts = _index(case["question_parts"], "part_id")
    passages = _index(source["passages"], "passage_id")
    if not parts:
        raise ValueError("Explicit question parts required")
    for part in parts.values():
        if (
            not part["text"].strip()
            or not part["explanation"].strip()
            or part["status"] not in {"addressed", "unanswered", "unclear"}
            or type(part["essential"]) is not bool
        ):
            raise ValueError("Invalid question scope record")
        if not set(part["claim_ids"]) <= claims.keys():
            raise ValueError("Question part references removed claim")
    for claim in claims.values():
        for key in ("passage_ids", "assertion_ids", "targets"):
            if len(claim[key]) != len(set(claim[key])):
                raise ValueError("Duplicate claim references")
        if not claim["text"].strip() or not claim["rationale"].strip():
            raise ValueError("Blank claim or rationale")
        if not claim["passage_ids"] or not set(claim["passage_ids"]) <= passages.keys():
            raise ValueError("Unanchored claim")
        relation, targets = claim["relationship"], claim["targets"]
        if relation == "direct":
            if not targets or not set(targets) <= parts.keys():
                raise ValueError("Unknown direct question part")
        elif relation == "supporting":
            _chain(claim, claims)
        elif relation not in {"not-relevant", "unclear"} or targets:
            raise ValueError("Invalid relationship or targets")


def _ordered(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep stable input order within direct, dependency, and remaining tiers."""
    indexed = _index(claims, "claim_id")
    return sorted(
        claims,
        key=lambda c: (
            0 if c["relationship"] == "direct" else 1 if c["relationship"] == "supporting" else 2,
            len(_chain(c, indexed)) if c["relationship"] == "supporting" else 0,
        ),
    )


def _quote(text: str) -> str:
    """Quote every original line without normalizing source prose."""
    return "\n".join("> " + line for line in text.split("\n"))


def render_card(
    source: dict[str, Any],
    case: dict[str, Any],
    claim_id: str,
    *,
    case_position: int | None = None,
    case_count: int | None = None,
) -> str:
    """Repeat full question, exact inline target and anchored source on each card."""
    ordered = _ordered(case["claims"])
    indexed = _index(ordered, "claim_id")
    claim = indexed[claim_id]
    number = next(i for i, item in enumerate(ordered, 1) if item["claim_id"] == claim_id)
    relation = claim["relationship"]
    lines = [
        f"Case {case_position or source['case_id']}"
        + (f" of {case_count}" if case_count else "")
        + f" · {source['case_id']} · {source['question'].get('comment_label', '')}"
        + f" · {claim_id} · version {claim.get('version', 1)}",
        "**Approved question**",
        _quote(source["question"]["text"]),
        f"**Claim {number} of {len(ordered)} — {relation} claim**",
        _quote(claim["text"]),
    ]
    if relation == "supporting":
        target = indexed[claim["targets"][0]]
        position = next(i for i, c in enumerate(ordered, 1) if c is target)
        lines += [
            f"**Supports claim {position}:** ({target['claim_id']}, "
            f"version {target.get('version', 1)})",
            _quote(target["text"]),
            claim["rationale"],
        ]
    else:
        lines += [f"**Why {relation.replace('-', ' ')}:** {claim['rationale']}"]
    passages = _index(source["passages"], "passage_id")
    lines += ["**Response passage**", "Exact original text; no normalization."]
    lines += [_quote(passages[pid]["text"]) for pid in claim["passage_ids"]]
    units = {passages[pid]["unit_id"] for pid in claim["passage_ids"]}
    references = [
        r
        for unit in source["responses"]
        if unit["unit_id"] in units
        for r in unit.get("supplied_citations", [])
    ]
    readable = []
    domains = {
        "intra_volume": "Internal comment/response cross-reference",
        "draft_eir": "Draft EIR citation",
        "final_eir": "Final EIR citation",
        "appendix_q": "Appendix Q citation",
        "external": "External reference",
        "unknown": "Unclassified supplied reference",
    }
    for reference in references:
        if isinstance(reference, str):
            readable.append(reference)
        else:
            text = next(
                (reference[k] for k in ("raw_text", "text", "citation_text") if reference.get(k)),
                None,
            )
            if text is None:
                text = "; ".join(reference.get("target_labels", []))
            readable.append(
                domains.get(reference.get("reference_domain"), "Supplied reference") + ": " + text
            )
    if readable:
        lines += ["**Supplied reference:** " + "; ".join(readable)]
        lines += [
            "References indexed for this response unit; any additional references in "
            "the exact passage remain source-supplied. None are evidence-verified."
        ]
    else:
        reference_passages = [
            passages[pid]["text"]
            for pid in claim["passage_ids"]
            if re.search(
                r"Draft EIR|DEIR|Final EIR|Appendix|Table \d|"
                r"Figure \d|Section \d|Guidelines|Public Resources Code|"
                r"Response [A-Z]|MM [A-Z]|BRTR|https?://",
                passages[pid]["text"],
                re.IGNORECASE,
            )
        ]
        if reference_passages:
            lines += [
                "**Supplied reference:** The source index has no separate citation record. "
                "Reference-bearing response text is preserved verbatim below; it is not "
                "evidence-verified."
            ]
            lines += [_quote(text) for text in reference_passages]
        else:
            lines += [
                "**Supplied reference:** None separately indexed. The exact response "
                "passage above retains any unindexed source references."
            ]
    return "\n\n".join(lines) + "\n"


def prepare_queue(
    packet: dict[str, Any],
    inventory: dict[str, Any],
    proposal: dict[str, Any],
    context_notes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prepare a deterministic blank queue with all original source context preserved."""
    validate_packet(packet)
    if any("authorized_context" in case for case in packet["cases"]):
        profile = json.loads((SCHEMA.parent / "input.schema.json").read_bytes())
        Draft202012Validator(profile).validate(packet)
    validate_inventory(packet, inventory, proposal)
    proposed = _index(proposal["cases"], "case_id")
    cards = []
    for position, source in enumerate(packet["cases"], 1):
        case = proposed[source["case_id"]]
        _validate_claims(source, case)
        for claim in _ordered(case["claims"]):
            card = render_card(
                source,
                case,
                claim["claim_id"],
                case_position=position,
                case_count=len(packet["cases"]),
            )
            cards.append(
                {
                    "case_id": source["case_id"],
                    "claim_id": claim["claim_id"],
                    "claim_version": 1,
                    "claim_sha256": _sha(claim),
                    "target_bindings": [
                        {
                            "claim_id": target["claim_id"],
                            "version": 1,
                            "text_sha256": digest(target["text"].encode()),
                        }
                        for target in _chain(claim, _index(case["claims"], "claim_id"))
                    ],
                    "card": card,
                    "card_sha256": digest(card.encode()),
                    "decision": None,
                }
            )
    return {
        "schema_version": VERSION,
        "status": "prepared, awaiting human review",
        "packet": copy.deepcopy(packet),
        "context_notes": copy.deepcopy(context_notes or {}),
        "inventory": copy.deepcopy(inventory),
        "proposal": copy.deepcopy(proposal),
        "cards": cards,
        "packet_sha256": _sha(packet),
        "inventory_sha256": _sha(inventory),
        "proposal_sha256": _sha(proposal),
    }


def new_journal(queue: dict[str, Any]) -> dict[str, Any]:
    """Initialize without importing historical or practice decisions."""
    return {"schema_version": VERSION, "queue_sha256": _sha(queue), "events": []}


def _current_hash(case: dict[str, Any]) -> str:
    """Bind case approval to claims, links, versions, and preserved question gaps."""
    return _sha({"claims": case["claims"], "question_parts": case["question_parts"]})


def replay(queue: dict[str, Any], journal: dict[str, Any]) -> dict[str, Any]:
    """Replay exact displayed decisions; invalidate dependents after any revision."""
    try:
        Draft202012Validator(json.loads(SCHEMA.read_bytes())).validate(journal)
    except ValidationError as exc:
        raise ValueError(exc.message) from exc
    rebuilt = prepare_queue(
        queue["packet"], queue["inventory"], queue["proposal"], queue.get("context_notes")
    )
    if rebuilt != queue or journal["queue_sha256"] != _sha(queue):
        raise ValueError("Prepared queue or source binding changed")
    if journal["schema_version"] != VERSION:
        raise ValueError("Unknown journal version")
    sources = _index(queue["packet"]["cases"], "case_id")
    cases = copy.deepcopy(_index(queue["proposal"]["cases"], "case_id"))
    for case in cases.values():
        for claim in case["claims"]:
            claim["version"] = 1
        case.update(decisions={}, case_decision=None, history=[])
    displayed = None
    previous = journal["queue_sha256"]
    for position, event in enumerate(journal["events"], 1):
        payload = {k: v for k, v in event.items() if k != "event_sha256"}
        if (
            event["sequence"] != position
            or event["previous_sha256"] != previous
            or event["event_sha256"] != _sha(payload)
        ):
            raise ValueError("Broken append-only event chain")
        previous = event["event_sha256"]
        if any(
            not isinstance(event.get(k), str) or not event[k].strip()
            for k in ("actor", "chat_reference", "timestamp")
        ):
            raise ValueError("Event requires actor, chat reference and timestamp")
        if datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00")).tzinfo is None:
            raise ValueError("Timezone-aware event timestamp required")
        case = cases[event["case_id"]]
        claims = _index(case["claims"], "claim_id")
        kind = event["kind"]
        if kind == "display":
            card = render_card(
                sources[event["case_id"]],
                case,
                event["claim_id"],
                case_position=list(sources).index(event["case_id"]) + 1,
                case_count=len(sources),
            )
            if event["card_sha256"] != digest(card.encode()):
                raise ValueError("Display does not bind exact current card")
            displayed = (event["case_id"], event["claim_id"], event["card_sha256"])
        elif kind == "decision":
            expected = (event["case_id"], event["claim_id"], event["card_sha256"])
            if displayed != expected or not event["feedback"].strip():
                raise ValueError("Decision requires the currently displayed card and feedback")
            if event["decision"] not in {"approve", "reject", "defer"}:
                raise ValueError("Unknown human decision")
            if event.get("explicit") is not True:
                raise ValueError("Discussion is not approval")
            claim = claims[event["claim_id"]]
            case["decisions"][claim["claim_id"]] = {**event, "version": claim["version"]}
            case["case_decision"] = None
            displayed = None
        elif kind == "revise":
            removed = set(event["replaces"])
            if not removed or not removed <= claims.keys():
                raise ValueError("Revision needs existing replaced IDs")
            replacements = copy.deepcopy(event["claims"])
            replacement_ids = set(_index(replacements, "claim_id"))
            if replacement_ids & (claims.keys() - removed):
                raise ValueError("Revision overwrites unrelated claim")
            historical_ids = {c["claim_id"] for snapshot in case["history"] for c in snapshot}
            if (replacement_ids - claims.keys()) & historical_ids:
                raise ValueError("Retired stable claim IDs cannot be reused")
            for claim in replacements:
                claim["version"] = claims.get(claim["claim_id"], {}).get("version", 0) + 1
            affected = set(removed)
            while True:
                larger = affected | {
                    c["claim_id"] for c in claims.values() if set(c["targets"]) & affected
                }
                if larger == affected:
                    break
                affected = larger
            case["history"].append(copy.deepcopy(case["claims"]))
            case["claims"] = [
                c for c in case["claims"] if c["claim_id"] not in removed
            ] + replacements
            if "question_parts" in event:
                previous_parts = _index(case["question_parts"], "part_id")
                revised_parts = _index(event["question_parts"], "part_id")
                if previous_parts.keys() != revised_parts.keys() or any(
                    any(p[field] != revised_parts[k][field] for field in ("text", "essential"))
                    for k, p in previous_parts.items()
                ):
                    raise ValueError("Revision cannot silently narrow question scope")
                case["question_parts"] = copy.deepcopy(event["question_parts"])
            # Splits/merges must explicitly refresh every dangling dependent in this same event.
            _validate_claims(sources[event["case_id"]], case)
            inventory_case = _index(queue["inventory"]["cases"], "case_id")[event["case_id"]]
            assertions = _index(inventory_case["assertions"], "assertion_id")
            mapped = set()
            for claim in case["claims"]:
                aids = set(claim["assertion_ids"])
                if not aids or not aids <= assertions.keys():
                    raise ValueError("Revision requires inventoried assertion bindings")
                if not {p for aid in aids for p in assertions[aid]["passage_ids"]} <= set(
                    claim["passage_ids"]
                ):
                    raise ValueError("Revision dropped source qualifications")
                mapped.update(aids)
            if mapped != assertions.keys():
                raise ValueError("Revision silently dropped assertions")
            for cid in affected | replacement_ids:
                case["decisions"].pop(cid, None)
            case["case_decision"] = None
            displayed = None
        elif kind == "case_decision":
            if event["case_sha256"] != _current_hash(case) or not event["feedback"].strip():
                raise ValueError("Case decision must bind current claims and gap summary")
            if event["decision"] not in {"investigate", "hold", "stop"}:
                raise ValueError("Unknown case disposition")
            if event.get("explicit") is not True:
                raise ValueError("Explicit case disposition required")
            case["case_decision"] = copy.deepcopy(event)
            displayed = None
        elif kind != "discussion" or not event["feedback"].strip():
            raise ValueError("Unknown event or empty discussion")
    return {
        "cases": cases,
        "displayed": displayed,
        "journal_sha256": _sha(journal),
        "event_count": len(journal["events"]),
    }


def add_event(
    queue: dict[str, Any], journal: dict[str, Any], event: dict[str, Any]
) -> dict[str, Any]:
    """Return a validated appended journal; prior events are never changed."""
    result = copy.deepcopy(journal)
    previous = result["events"][-1]["event_sha256"] if result["events"] else result["queue_sha256"]
    row = {
        **copy.deepcopy(event),
        "sequence": len(result["events"]) + 1,
        "previous_sha256": previous,
    }
    row["event_sha256"] = _sha(row)
    result["events"].append(row)
    replay(queue, result)
    return result


def append_event(path: Path, queue: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Append one fsynced JSONL event under an exclusive lock; fail on torn records."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        content = stream.read()
        if content and not content.endswith("\n"):
            raise ValueError("Incomplete journal record; preserve before recovery")
        journal = new_journal(queue)
        journal["events"] = [json.loads(line) for line in content.splitlines() if line.strip()]
        updated = add_event(queue, journal, event)
        stream.seek(0, os.SEEK_END)
        stream.write(json.dumps(updated["events"][-1], ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return updated


def export_review(queue: dict[str, Any], journal: dict[str, Any]) -> dict[str, Any]:
    """Export only explicitly approved chains after independent whole-case disposition."""
    state = replay(queue, journal)
    advancing = []
    for cid, case in state["cases"].items():
        disposition = case["case_decision"]
        if disposition is None:
            raise ValueError("Missing whole-case human decision")
        if disposition["decision"] != "investigate":
            continue
        if disposition.get("links_confirmed") is not True or disposition.get("gaps_status") not in {
            "resolved",
            "unresolved",
            "not-applicable",
        }:
            raise ValueError("Explicit current links and unanswered scope required")
        gaps = [part for part in case["question_parts"] if part["status"] != "addressed"]
        if gaps and disposition["gaps_status"] == "not-applicable":
            raise ValueError("Unanswered scope cannot be marked not applicable")
        if (
            gaps
            and disposition["gaps_status"] == "resolved"
            and not disposition.get("gaps_resolution", "").strip()
        ):
            raise ValueError("Resolved gaps require an explicit human explanation")
        claims = _index(case["claims"], "claim_id")
        if claims.keys() != case["decisions"].keys():
            raise ValueError("Missing current claim decisions")
        approved = {k for k, d in case["decisions"].items() if d["decision"] == "approve"}
        if any(d["decision"] == "defer" for d in case["decisions"].values()):
            raise ValueError("Unresolved claim requires case hold")
        usable = [
            c
            for c in case["claims"]
            if c["claim_id"] in approved and c["relationship"] in {"direct", "supporting"}
        ]
        if not any(c["relationship"] == "direct" for c in usable):
            raise ValueError("No usable direct claim; explicit stop or hold required")
        for claim in usable:
            chain = _chain(claim, claims)
            if any(c["claim_id"] not in approved for c in chain):
                raise ValueError("Rejected or unresolved support target")
            advancing.append({"case_id": cid, "claim": claim, "support_chain": chain})
    return {
        "schema_version": VERSION,
        "status": "review complete; investigation only",
        "queue_sha256": _sha(queue),
        "journal_sha256": _sha(journal),
        "cases": state["cases"],
        "advancing": advancing,
        "source_context": queue["packet"],
        "context_notes": queue["context_notes"],
        "eligibility": "not determined",
    }
