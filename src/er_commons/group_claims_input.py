"""Prepare source-only claim inputs from pinned approved questions and inventory."""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any

from er_commons.group_ranking import (
    checked,
    digest,
    encoded,
    indexed,
    rows,
    under,
    validate_closure,
    validate_supplements,
)
from er_commons.group_wording_input import extract_comments
from er_commons.pilot_context_repair import refresh_cases

VERSION = "task08d.input.v1"


def passages(unit: dict[str, Any]) -> list[dict[str, Any]]:
    """Index exact sentence-sized passages without normalizing source characters."""
    text = unit["text"]
    result: list[dict[str, Any]] = []
    # Split only at sentence-ending punctuation followed by whitespace or at a
    # blank line. Wrapped lines, decimals, and URL interiors remain untouched.
    boundaries = list(re.finditer(r"(?<=[.!?])[ \t\r\n]+|(?:\r?\n)[ \t]*(?:\r?\n)", text))
    start = 0
    for boundary in [*boundaries, None]:
        end = boundary.start() if boundary is not None else len(text)
        while start < end and text[start].isspace():
            start += 1
        if start < end:
            result.append(
                {
                    "passage_id": f"{unit['unit_id']}:p{len(result) + 1:03d}",
                    "unit_id": unit["unit_id"],
                    "start": start,
                    "end": end,
                    "text": text[start:end],
                }
            )
        start = boundary.end() if boundary is not None else len(text)
    return result


def validate_packet(packet: dict[str, Any]) -> None:
    """Check exact frozen text, complete response membership and passage coverage."""
    if packet["schema_version"] != VERSION or not packet["cases"]:
        raise ValueError("Invalid claim input schema or empty cases")
    indexed(packet["cases"], "case_id")
    for case in packet["cases"]:
        question = case["question"]
        approval = question["approval"]
        if (
            question["neutral_id"] != case["case_id"]
            or digest(question["text"].encode()) != question["text_sha256"]
            or approval["approved_question"] != question["text"]
            or approval["approved_question_sha256"] != question["text_sha256"]
            or approval["decision"] != "approve"
            or approval["explicit_approval"] is not True
            or approval["display_version"] != question["display_version"]
        ):
            raise ValueError("Frozen question approval or exact text differs")
        original = case["original_comment"]
        if (
            original["unit_id"] != question["comment_id"]
            or digest(encoded(original)) != question["original_comment_sha256"]
            or digest(original["text"].encode()) != question["comment_text_sha256"]
        ):
            raise ValueError("Frozen original comment binding differs")
        responses = indexed(case["responses"], "unit_id")
        expected = set(case["closure"]["context_unit_ids"]) - {question["comment_id"]}
        if set(responses) != expected or any(
            u["unit_kind"] not in {"response", "general_response"} for u in responses.values()
        ):
            raise ValueError("Response closure membership differs")
        if case["passages"] != [p for unit in case["responses"] for p in passages(unit)]:
            raise ValueError("Exact source spans or passage coverage differ")


def prepare(
    handoff_path: Path,
    data_root: Path,
    output: Path,
    expected_handoff_sha256: str,
    authorized_labels: list[str],
) -> dict[str, Any]:
    """Verify pinned source bindings and publish a fresh completion-last packet."""
    references = []

    def read(path: Path, sha: str) -> Any:
        """Read only a checksummed input and retain its identity separately."""
        content = checked(path, sha)
        references.append({"path": str(path), "sha256": sha})
        return json.loads(content)

    def ref(record: dict[str, Any]) -> Any:
        """Resolve a pinned reference under the explicit artifact root."""
        return read(under(data_root, record["path"]), record["sha256"])

    handoff = read(handoff_path, expected_handoff_sha256)
    if (
        handoff["schema_version"] != "task08c.handoff.v1"
        or handoff["status"] != "complete"
        or handoff["process_revision"] != "task08c.chat_review.v1"
        or handoff["selected_comments"] != authorized_labels
        or handoff["excluded"]
        or handoff["unresolved"]
    ):
        raise ValueError("Completed authorized frozen-question handoff required")
    artifacts = handoff["artifacts"]
    approved = ref(artifacts["approved_questions"])
    decisions = ref(artifacts["decisions"])
    original_packet = ref(artifacts["original_packet"])
    restricted = ref(artifacts["restricted_provenance"])
    journal = ref(artifacts["journal"])
    questions = handoff["questions"]
    if (
        approved["questions"] != questions
        or decisions["journal"] != journal
        or decisions["status"] != "complete"
        or [q["comment_label"] for q in questions] != authorized_labels
        or decisions["advancing_neutral_ids"] != [q["neutral_id"] for q in questions]
    ):
        raise ValueError("Frozen question export differs from saved decisions")
    journal_events = indexed(journal["events"], "event_id")
    for q in questions:
        if (
            journal_events[q["approval"]["event_id"]] != q["approval"]
            or q["packet_sha256"] != artifacts["original_packet"]["sha256"]
            or q["prompt_sha256"] != artifacts["prompt"]["sha256"]
            or q["proposal_sha256"] != artifacts["original_proposal"]["sha256"]
        ):
            raise ValueError("Frozen question approval or drafting provenance differs")
    upstream = ref(artifacts["upstream_08b_handoff"])
    manifest = ref(upstream["prepared_manifest"])
    selection = ref(upstream["decisions"])
    tasks = ref(restricted["prepared_tasks"])
    projected, mappings = extract_comments(
        upstream, tasks, selection, [q["comment_id"] for q in questions]
    )
    if projected != original_packet or mappings != restricted["mappings"]:
        raise ValueError("08B to 08C source projection differs")
    ranking = read(Path(manifest["ranking_root"]) / "input.json", manifest["input_sha256"])
    component_refs = [
        r for r in ranking["input_bindings"] if r["path"].endswith("/inventory/components.json")
    ]
    if len(component_refs) != 1:
        raise ValueError("Exactly one accepted inventory component binding required")
    components = indexed(read(Path(component_refs[0]["path"]), component_refs[0]["sha256"]), "role")
    for binding in ranking["input_bindings"]:
        if "/task_05_response_inventory/" in binding["path"] and binding not in component_refs:
            checked(Path(binding["path"]), binding["sha256"])
            references.append(binding)
    consumed = {}
    for name in ("source_records", "edges", "outcomes"):
        component = components[name]
        path = under(data_root, component["path"])
        content = checked(path, component["sha256"])
        references.append({"path": str(path), "sha256": component["sha256"]})
        consumed[name] = rows(content)
    # Reconstruct from the complete graph, not the bounded ranking view.
    ids = {q["comment_id"] for q in questions}
    seeds, views = [], []
    for q in questions:
        direct_edges = [
            e
            for e in consumed["edges"]
            if e["relation_type"] == "comment_response" and e["source_unit_id"] == q["comment_id"]
        ]
        direct = [e["target_unit_id"] for e in direct_edges]
        seed = {
            "comment_id": q["comment_id"],
            "comment_label": q["comment_label"],
            "direct_response_ids": direct,
            "context_unit_ids": [q["comment_id"], *direct],
            "relationship_ids": [e["edge_id"] for e in direct_edges],
        }
        seeds.append(seed)
        views.append(
            {
                "root_unit_id": q["comment_id"],
                "view_id": "task08d-directed-rebuild",
                "ordered_unit_ids": seed["context_unit_ids"],
                "edge_ids": seed["relationship_ids"],
            }
        )
    closures, context, _ = refresh_cases(
        seeds, consumed["source_records"], consumed["edges"], consumed["outcomes"], views
    )
    units = indexed(context, "unit_id")
    ranking_cases = indexed(
        [c for c in ranking["candidates"] if c["comment_id"] in ids], "comment_id"
    )
    sources = consumed["source_records"]
    spans = indexed([r for r in sources if r["record_type"] == "source_span"], "span_id")
    pages = indexed([r for r in sources if r["record_type"] == "page"], "page_id")
    task_data = indexed([t["data"] for t in tasks], "comment_id")
    cases = []
    for q, closure in zip(questions, closures, strict=True):
        validate_closure(closure, consumed["edges"])
        for field in (
            "context_unit_ids",
            "relationship_ids",
            "reference_outcome_ids",
            "reference_mention_ids",
        ):
            if set(closure[field]) != set(ranking_cases[q["comment_id"]][field]):
                raise ValueError(f"Accepted ranking closure differs: {field}")
        original = units[q["comment_id"]]
        if original != task_data[q["comment_id"]]["original_comment"]:
            raise ValueError("08B original source changed")
        unit_ids = set(closure["context_unit_ids"])
        supplements = [s for s in ranking["source_supplements"] if s["unit_id"] in unit_ids]
        validate_supplements(supplements, context, pages)
        responses = []
        for uid in closure["context_unit_ids"]:
            if uid == q["comment_id"]:
                continue
            unit = units[uid]
            responses.append(
                {
                    **unit,
                    "source_spans": [spans[s] for s in unit["span_ids"]],
                    "supplied_citations": [
                        r
                        for r in sources
                        if r["record_type"] == "reference_mention" and r["source_unit_id"] == uid
                    ],
                }
            )
        closure.pop("review_state")
        cases.append(
            {
                "case_id": q["neutral_id"],
                "question": q,
                "original_comment": original,
                "responses": responses,
                "supplements": supplements,
                "outcomes": [r for r in consumed["outcomes"] if r["source_unit_id"] in unit_ids],
                "warnings": {
                    "inherited_limitations": ranking["limitations"],
                    "source_flags": closure["challenge_signals"],
                    "comment_source_warnings": task_data[q["comment_id"]][
                        "comment_source_warnings"
                    ],
                },
                "closure": {
                    **closure,
                    "edges": [
                        e for e in consumed["edges"] if e["edge_id"] in closure["relationship_ids"]
                    ],
                },
                "passages": [p for u in responses for p in passages(u)],
            }
        )
    packet = {
        "schema_version": VERSION,
        "cases": cases,
        "inventory_id": ranking["inventory_id"],
        "limitations": ranking["limitations"],
        "historical_task06g_commit_pin_failures": 3,
    }
    validate_packet(packet)
    validation = {
        "valid": True,
        "cases": [
            {
                "case_id": c["case_id"],
                "responses": len(c["responses"]),
                "passages": len(c["passages"]),
                "supplements": len(c["supplements"]),
                "outcomes": len(c["outcomes"]),
                "closure_independently_reconciled": True,
            }
            for c in cases
        ],
    }
    provenance = {
        "schema_version": "task08d.input_manifest.v1",
        "references": references,
        "upstream_handoff_sha256": expected_handoff_sha256,
        "restricted_selection_warnings": {
            q["comment_id"]: task_data[q["comment_id"]]["source_warnings"] for q in questions
        },
        "packet_sha256": digest(encoded(packet)),
        "policy": "Source-only proposal input; no historical case claims, labels or answers.",
        "source_terms": "Inherited from pinned accepted source inventory and release.",
        "command": "python -m er_commons.group_claims_input",
        "split_policy": "No split assigned",
    }
    output.mkdir(parents=True, exist_ok=False)
    payloads = {
        "packet.json": encoded(packet),
        "manifest.json": encoded(provenance),
        "validation.json": encoded(validation),
        "preparation.py": Path(__file__).read_bytes(),
    }
    for name, content in payloads.items():
        (output / name).write_bytes(content)
    completion = {
        "schema_version": "task08d.input_completion.v1",
        "files": {n: digest(b) for n, b in payloads.items()},
        "valid": True,
    }
    (output / "completion.json").write_bytes(encoded(completion))
    return completion


def main() -> None:
    """Publish only explicitly authorized comment IDs into a new input namespace."""
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("handoff", "data-root", "output"):
        parser.add_argument(f"--{key}", type=Path, required=True)
    parser.add_argument("--expected-handoff-sha256", required=True)
    parser.add_argument("--comment-label", action="append", required=True)
    args = parser.parse_args()
    prepare(
        args.handoff, args.data_root, args.output, args.expected_handoff_sha256, args.comment_label
    )
    logging.basicConfig(level=logging.INFO)
    logging.info("Verified source-only claim packet: %s", args.output)


if __name__ == "__main__":
    main()
