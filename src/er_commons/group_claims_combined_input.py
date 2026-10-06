"""Prepare restartable source-only 08D packets from the complete combined 08C seal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from er_commons.group_claims_input import VERSION, passages, validate_packet
from er_commons.group_ranking import (
    checked,
    digest,
    encoded,
    indexed,
    rows,
    validate_closure,
    validate_supplements,
)
from er_commons.group_wording_combined_chat import validate_journal
from er_commons.pilot_context_repair import refresh_cases

DEFERRED = ["C013", "C023", "C038", "C057"]


def write_once(path: Path, value: Any) -> dict[str, str]:
    """Resume identical checkpoints, rejecting changed bytes at any saved path."""
    content = encoded(value)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f"Existing checkpoint differs: {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return {"path": str(path), "sha256": digest(content)}


def verify_decisions(result: dict[str, Any], decisions: dict[str, Any]) -> None:
    """Require the exact complete saved order and authorized four deferrals."""
    records = decisions["records"]
    if (
        result["status"] != "review_pass_complete"
        or result["approved"] != 53
        or result["deferred"] != 4
        or result["pending"] != 0
        or result["selected"] != 57
        or result["excluded"] != 0
        or decisions["status"] != "review_pass_complete"
        or [r["neutral_id"] for r in records] != [f"C{i:03d}" for i in range(1, 58)]
        or decisions["deferred_neutral_ids"] != DEFERRED
    ):
        raise ValueError("Completed 57-case combined decisions required")
    approved = []
    for record in records:
        cid = record["neutral_id"]
        if cid in DEFERRED:
            if record["state"] != "deferred":
                raise ValueError("Deferred case unexpectedly advances")
            continue
        q, approval = record["frozen_question"], record["disposition"]
        if (
            record["state"] != "approved"
            or approval["decision"] != "approve"
            or approval["explicit_approval"] is not True
            or approval["approved_question"] != q["text"]
            or approval["approved_question_sha256"] != q["text_sha256"]
            or digest(q["text"].encode()) != q["text_sha256"]
            or approval["display_version"] != q["display_version"]
        ):
            raise ValueError("Exact frozen question approval differs")
        approved.append(cid)
    if approved != decisions["advancing_neutral_ids"] or len(approved) != 53:
        raise ValueError("Approved membership/order differs")


def prepare(result_path: Path, data_root: Path, output: Path) -> dict[str, Any]:
    """Pin all upstream records and reconstruct each full directed response closure."""
    references: dict[str, dict[str, str]] = {}

    def read(ref: dict[str, Any]) -> bytes:
        """Verify bytes before parsing while retaining a deduplicated audit identity."""
        path = Path(ref["path"])
        if not path.is_absolute():
            path = data_root / path
        content = checked(path, ref["sha256"])
        references[str(path)] = {"path": str(path), "sha256": digest(content)}
        return content

    def load(ref: dict[str, Any]) -> Any:
        """Decode a verified JSON reference."""
        return json.loads(read(ref))

    source = result_path.read_bytes()
    result_ref = {"path": str(result_path.resolve()), "sha256": digest(source)}
    result = load(result_ref)
    for ref in result["artifacts"].values():
        read(ref)
    read(result["checkpoint"])
    artifacts = result["artifacts"]
    original_packet = load(artifacts["packet"])
    previous = None
    replay = None
    for ref in result["journal_chain"]:
        journal = load(ref)
        replay = validate_journal(
            journal,
            original_packet,
            packet_sha256=artifacts["packet"]["sha256"],
            prompt_sha256=artifacts["prompt"]["sha256"],
            previous=previous,
        )
        previous = journal
    decisions = load(artifacts["final_decisions_export"])
    if replay != decisions or result["journal_chain"][-1] != artifacts["current_journal"]:
        raise ValueError("Final decisions do not replay from immutable journal chain")
    verify_decisions(result, decisions)
    restricted = load(artifacts["restricted_provenance"])
    mappings = restricted["mappings"]
    if [m["neutral_id"] for m in mappings] != [r["neutral_id"] for r in decisions["records"]]:
        raise ValueError("08B mapping saved order differs")
    # Reverify pinned 08B source references without including selection reasons in packets.
    for ref in restricted["verified_references"]:
        read(ref)
    rankings: dict[str, Any] = {}
    tasks_by_comment: dict[str, Any] = {}
    selected_by_comment: dict[str, Any] = {}
    for mapping in mappings:
        key = mapping["handoff"]["path"]
        if key in rankings:
            continue
        handoff = load(mapping["handoff"])
        manifest = load(handoff["prepared_manifest"])
        ranking = load(
            {
                "path": str(Path(manifest["ranking_root"]) / "input.json"),
                "sha256": manifest["input_sha256"],
            }
        )
        rankings[key] = ranking
        tasks = load(
            {
                "path": str(Path(handoff["prepared_manifest"]["path"]).parent / "tasks.json"),
                "sha256": manifest["files"]["tasks.json"],
            }
        )
        tasks_by_comment.update({t["data"]["comment_id"]: t["data"] for t in tasks})
        selected_by_comment.update({c["comment_id"]: c for c in handoff["selected_cases"]})
    component_refs = {
        r["path"]: r
        for ranking in rankings.values()
        for r in ranking["input_bindings"]
        if r["path"].endswith("/inventory/components.json")
    }
    if len(component_refs) != 1:
        raise ValueError("Single accepted inventory required")
    components = indexed(load(next(iter(component_refs.values()))), "role")
    consumed = {
        name: rows(read(components[name])) for name in ("source_records", "edges", "outcomes")
    }
    sources, edges, outcomes = consumed["source_records"], consumed["edges"], consumed["outcomes"]
    units = indexed([r for r in sources if r["record_type"] == "source_unit"], "unit_id")
    labels = {r["official_label"]: r["unit_id"] for r in units.values()}
    spans = indexed([r for r in sources if r["record_type"] == "source_span"], "span_id")
    pages = indexed([r for r in sources if r["record_type"] == "page"], "page_id")
    extra_ids = {
        "C017": [labels[f"Comment M-OSEC-{i}"] for i in range(272, 275)],
        "C045": [labels[f"Comment PC-MS-{i}"] for i in range(1, 9)],
    }
    roots = list(
        dict.fromkeys(
            [m["comment_id"] for m in mappings if m["neutral_id"] not in DEFERRED]
            + [uid for values in extra_ids.values() for uid in values]
        )
    )
    seeds, views = [], []
    for uid in roots:
        direct_edges = [
            e
            for e in edges
            if e["relation_type"] == "comment_response" and e["source_unit_id"] == uid
        ]
        direct = [e["target_unit_id"] for e in direct_edges]
        if not direct:
            raise ValueError(f"Missing official response: {uid}")
        seed = {
            "comment_id": uid,
            "comment_label": units[uid]["official_label"],
            "direct_response_ids": direct,
            "context_unit_ids": [uid, *direct],
            "relationship_ids": [e["edge_id"] for e in direct_edges],
        }
        seeds.append(seed)
        views.append(
            {
                "root_unit_id": uid,
                "view_id": "task08d-combined-directed-rebuild",
                "ordered_unit_ids": seed["context_unit_ids"],
                "edge_ids": seed["relationship_ids"],
            }
        )
    closures, context, _ = refresh_cases(seeds, sources, edges, outcomes, views)
    for closure in closures:
        validate_closure(closure, edges)
        closure.pop("review_state")
    closure_index, context_index = indexed(closures, "comment_id"), indexed(context, "unit_id")
    supplements = list(
        {
            digest(encoded(s)): s
            for ranking in rankings.values()
            for s in ranking["source_supplements"]
        }.values()
    )
    # Only source content, not the assessment fields, enters the authorized context.
    c017 = load(artifacts["C017_expanded_context"])
    extra_comments = load(c017["expanded_comments"])
    extra_responses = load(c017["responses_for_next_step"])
    c045 = load(artifacts["C045_supplemental_PCMS_context"])
    read(c045["source"])
    notes = {
        name: {"binding": ref, "content": load(ref)}
        for name, ref in artifacts.items()
        if name.startswith("C")
        or name
        in {
            "reconciliation_hold",
            "downstream_bindings",
            "report_context_amendment",
            "appendix_c_feasibility",
        }
    }
    cases, checkpoints, validation_cases = [], [], []
    for record, mapping in zip(decisions["records"], mappings, strict=True):
        cid, uid = record["neutral_id"], mapping["comment_id"]
        if cid in DEFERRED:
            continue
        if (
            uid not in selected_by_comment
            or mapping["original_comment_sha256"] != record["original_comment_sha256"]
        ):
            raise ValueError("08B selection/source binding differs")
        original = context_index[uid]
        if (
            original != tasks_by_comment[uid]["original_comment"]
            or digest(encoded(original)) != record["original_comment_sha256"]
        ):
            raise ValueError("Original comment source changed")
        ranking = rankings[mapping["handoff"]["path"]]
        ranking_case = indexed(ranking["candidates"], "comment_id")[uid]
        closure = closure_index[uid]
        for field in (
            "context_unit_ids",
            "relationship_ids",
            "reference_outcome_ids",
            "reference_mention_ids",
        ):
            expected = set(ranking_case[field])
            if field == "relationship_ids":
                expected -= {
                    e["edge_id"]
                    for e in edges
                    if e["relation_type"] == "general_response_membership"
                }
            if set(closure[field]) != expected:
                raise ValueError(f"Accepted source closure differs: {cid} {field}")
        supplemental = [closure_index[x] for x in extra_ids.get(cid, []) if x != uid]
        response_ids = list(
            dict.fromkeys(
                x
                for c in [closure, *supplemental]
                for x in c["context_unit_ids"]
                if x != c["comment_id"]
            )
        )
        response_units = [
            {
                **context_index[x],
                "source_spans": [spans[s] for s in context_index[x]["span_ids"]],
                "supplied_citations": [
                    r
                    for r in sources
                    if r["record_type"] == "reference_mention" and r["source_unit_id"] == x
                ],
            }
            for x in response_ids
        ]
        all_ids = {uid, *response_ids, *extra_ids.get(cid, [])}
        case_supplements = [s for s in supplements if s["unit_id"] in all_ids]
        validate_supplements(case_supplements, context, pages)
        q = {
            **record["frozen_question"],
            "neutral_id": cid,
            "comment_id": uid,
            "comment_label": mapping["comment_label"],
            "approval": record["disposition"],
            "original_comment_sha256": record["original_comment_sha256"],
            "comment_text_sha256": record["comment_text_sha256"],
        }
        authorized: dict[str, Any] = {
            "comments": [context_index[x] for x in extra_ids.get(cid, [])]
        }
        if cid == "C017":
            authorized.update(
                expanded_comments=extra_comments, verified_response_context=extra_responses
            )
        if cid == "C045":
            authorized.update(
                full_PCMS_text=c045["text"],
                physical_pages=c045["physical_pages"],
                source=c045["source"],
            )
        case = {
            "case_id": cid,
            "question": q,
            "original_comment": original,
            "responses": response_units,
            "supplements": case_supplements,
            "outcomes": [r for r in outcomes if r["source_unit_id"] in all_ids],
            "warnings": {
                "inherited_limitations": ranking["limitations"],
                "source_flags": closure["challenge_signals"],
                "comment_source_warnings": record["comment_source_warnings"],
            },
            "closure": {
                **closure,
                "context_unit_ids": [uid, *response_ids],
                "edges": [e for e in edges if e["edge_id"] in closure["relationship_ids"]],
            },
            "selected_response_closure": closure,
            "supplemental_closures": supplemental,
            "authorized_context": authorized,
            "passages": [p for u in response_units for p in passages(u)],
        }
        packet = {
            "schema_version": VERSION,
            "cases": [case],
            "inventory_id": ranking["inventory_id"],
            "limitations": ranking["limitations"],
            "historical_task06g_commit_pin_failures": 3,
        }
        validate_packet(packet)
        checkpoint = write_once(output / "cases" / cid / "packet.json", packet)
        note_ref = write_once(
            output / "cases" / cid / "context_notes.json",
            {
                "not_for_proposal_model": True,
                "case_id": cid,
                "selection_provenance": mapping,
                "notes": {
                    k: v
                    for k, v in notes.items()
                    if k.startswith(cid + "_")
                    or (cid == "C002" and k in {"reconciliation_hold", "downstream_bindings"})
                },
            },
        )
        checkpoints.append({"case_id": cid, "packet": checkpoint, "context_notes": note_ref})
        cases.append(case)
        validation_cases.append(
            {
                "case_id": cid,
                "responses": len(response_units),
                "passages": len(case["passages"]),
                "supplements": len(case_supplements),
                "closure_independently_reconciled": True,
                "supplemental_closures": len(supplemental),
            }
        )
    packet = {
        "schema_version": VERSION,
        "cases": cases,
        "inventory_id": next(iter(rankings.values()))["inventory_id"],
        "limitations": next(iter(rankings.values()))["limitations"],
        "historical_task06g_commit_pin_failures": 3,
    }
    validate_packet(packet)
    packet_ref = write_once(output / "packet.json", packet)
    notes_ref = write_once(
        output / "context_notes.json",
        {
            "not_for_proposal_model": True,
            "notes": notes,
            "all_57_decisions": decisions,
            "deferred_ids": DEFERRED,
        },
    )
    validation_ref = write_once(
        output / "validation.json",
        {
            "valid": True,
            "cases": validation_cases,
            "journal_replay": True,
            "frozen_question_count": len(cases),
            "deferred_ids": DEFERRED,
        },
    )
    manifest = {
        "schema_version": "task08d.combined_input_manifest.v1",
        "result": result_ref,
        "references": list(references.values()),
        "packet": packet_ref,
        "context_notes": notes_ref,
        "case_checkpoints": checkpoints,
        "validation": validation_ref,
        "policy": (
            "Source-only Astra packets. No historical claims, labels, answers, "
            "selection reasons or evidence judgments."
        ),
        "source_terms": "Inherited pinned accepted source inventory; no split assigned.",
    }
    manifest_ref = write_once(output / "manifest.json", manifest)
    return write_once(
        output / "completion.json",
        {
            "schema_version": "task08d.combined_input_completion.v1",
            "valid": True,
            "case_count": len(cases),
            "manifest": manifest_ref,
            "packet": packet_ref,
            "validation": validation_ref,
        },
    )


def main() -> None:
    """Prepare or verify identical restart checkpoints in the authorized namespace."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("result", "data-root", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.result, args.data_root, args.output)


if __name__ == "__main__":
    main()
