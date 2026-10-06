"""Invented canonical section/table fixtures; no corpus or historical labels."""

import copy
import json
from pathlib import Path
from typing import Any

from er_commons import pilot_evidence as evidence
from er_commons.group_evidence import VERSION


def prepare_qualification(root: Path) -> list[dict[str, Any]]:
    """Write invented canonical files to a new directory and prepare five UI tasks."""
    root.mkdir(parents=True, exist_ok=False)
    tasks = []
    for number, kind in enumerate(("section", "table", "section", "section", "section"), 1):
        prefix = f"fixture{number}"
        (root / prefix).mkdir()
        source = f"synthetic_{number}"
        document = f"synthetic/document/{source}"
        heading = "1.1 Synthetic fixture"
        blocks: list[dict[str, Any]] = [
            {
                "id": identity,
                "canonical_text": text,
                "block_type": block_kind,
                "sequence": i,
                "section_id": "s1" if i < 2 else "s2",
                "content_layer": "body",
                "document_id": document,
                "extraction_id": "synthetic",
            }
            for i, (identity, text, block_kind) in enumerate(
                [
                    ("h1", heading, "heading"),
                    (
                        "b1",
                        "Table 1. Synthetic measurements"
                        if kind == "table"
                        else "The fictional container holds ten units.",
                        "caption" if kind == "table" else "paragraph",
                    ),
                    ("h2", "1.2 Next fixture", "heading"),
                ]
            )
        ]
        section = {
            "id": "s1",
            "document_id": document,
            "heading_block_id": "h1",
            "ordered_child_ids": ["h1", "b1"],
            "section_path_ids": ["s1"],
        }

        def anchor(
            record: dict[str, Any], field: str = "canonical_text", prefix: str = prefix
        ) -> dict[str, Any]:
            """Bind complete synthetic canonical text or one complete table cell."""
            text = (
                record["cells"][int(field.split(".")[1])]["text"]
                if field.startswith("cells")
                else record[field]
            )
            return {
                "path": f"{prefix}/{'tables' if field.startswith('cells') else 'blocks'}.jsonl",
                "record_id_field": "id",
                "record_id": record["id"],
                "record": record,
                "text_field": field,
                "start": 0,
                "end": len(text),
                "quote": text,
            }

        anchors = [anchor(b) for b in blocks[:2]]
        members = ["h1", "b1"]
        if kind == "table":
            note = {
                **blocks[1],
                "id": "note",
                "sequence": 1.5,
                "block_type": "paragraph",
                "canonical_text": "Note: invented units only.",
            }
            blocks.append(note)
            table = {
                "id": "t1",
                "section_id": "s1",
                "document_id": document,
                "extraction_id": "synthetic",
                "cells": [
                    {"row_index": 0, "column_index": 0, "text": "Units"},
                    {"row_index": 1, "column_index": 0, "text": "10"},
                ],
            }
            (root / f"{prefix}/tables.jsonl").write_text(json.dumps(table))
            section["ordered_child_ids"] = ["h1", "b1", "t1", "note"]
            members = ["b1", "note", "t1"]
            anchors = [
                anchor(blocks[1]),
                anchor(note),
                anchor(table, "cells.0.text"),
                anchor(table, "cells.1.text"),
            ]
        (root / f"{prefix}/blocks.jsonl").write_text("\n".join(json.dumps(b) for b in blocks))
        (root / f"{prefix}/sections.jsonl").write_text(json.dumps(section))
        unit = {
            "schema_version": "er_commons.task07d.citation_unit.v1",
            "kind": kind,
            "boundary_policy": "heading_to_next_heading_exclusive",
            "section_id": "s1",
            "section_record": {
                "path": f"{prefix}/sections.jsonl",
                "record_id_field": "id",
                "record_id": "s1",
                "record": section,
            },
            "heading_anchor": anchor(blocks[0]),
            "next_heading_anchor": anchor(blocks[2]),
            "start_block_id": "h1",
            "breadcrumb": [{"section_id": "s1", "heading_block_id": "h1", "heading_text": heading}],
            "section_member_record_ids": section["ordered_child_ids"],
            "member_record_ids": members,
            "separately_cited_units": [],
            "citation_label": (blocks[1]["canonical_text"] if kind == "table" else heading)
            + " (pp. 1)",
            "table_id": "t1" if kind == "table" else None,
        }
        candidate = {
            "citation_unit": unit,
            "anchors": anchors,
            "quote": "\n\n".join(a["quote"] for a in anchors),
            "source_id": source,
            "source_url": "https://example.invalid/synthetic.pdf",
            "edition": "Draft",
            "physical_pages": [1],
            "printed_labels": ["1"],
            "limitations": ["Synthetic"],
        }
        candidate["candidate_id"] = evidence.candidate_id(candidate)
        case = f"QA-08E-{number}"
        claim = {
            "claim_id": f"{case}-claim",
            "local_id": "C001",
            "text": "The fictional container holds ten units.",
            "relationship": "direct",
            "concern_ids": ["Q1"],
            "supporting_claim_ids": [],
        }
        context = dict.fromkeys(
            ("comment_html", "concerns_html", "response_html"),
            "<p>Entirely synthetic qualification context.</p>",
        )
        packet = {
            "schema_version": "er_commons.task07d.evidence_packet.v2",
            "case_id": case,
            "claims": [claim],
            "context": context,
            "source_bindings": {},
            "candidates": [candidate],
            "discovery_attempts": [],
            "claim_candidates": [
                {
                    "claim_id": claim["claim_id"],
                    "candidate_ids": [candidate["candidate_id"]],
                    "overflow_candidate_ids": [],
                    "search_gap": "Source-free fixture, no actual search.",
                }
            ],
        }
        review = {
            "review_status": "approved",
            "case_label": case,
            "claims": [copy.deepcopy(claim)],
            "evidence_candidate_claim_ids": [claim["claim_id"]],
            "data": {
                "comment_html": context["comment_html"],
                "concerns_html": context["concerns_html"],
                "sources_html": context["response_html"],
            },
        }
        task = evidence.prepare_claim_tasks(packet, data_root=root, approved_review=review)[0]
        task["data"].update(
            qualification_only=True,
            interface_version=VERSION,
            question_version="synthetic.v1",
            upstream_handoff="synthetic-only",
        )
        tasks.append(task)
    return tasks


def prepare_extended_qualification(root: Path) -> list[dict[str, Any]]:
    """Prepare separate zero-hit, shared-source and long-context synthetic tasks."""
    base = prepare_qualification(root)
    packets = [copy.deepcopy(base[i]["data"]["packet"]) for i in (0, 2, 3)]
    packets[0]["case_id"] = "QA-08E-ZERO"
    packets[0]["candidates"] = []
    packets[0]["claim_candidates"][0]["candidate_ids"] = []
    packets[0]["claim_candidates"][0]["search_gap"] = "Synthetic zero-hit gap; not corpus absence."
    shared = packets[1]
    shared["case_id"] = "QA-08E-SHARED"
    second = copy.deepcopy(shared["claims"][0])
    second.update(
        claim_id="QA-08E-SHARED-second",
        local_id="C002",
        text="The fictional container is suitable for a different purpose.",
    )
    shared["claims"].append(second)
    shared["claim_candidates"].append(
        {**copy.deepcopy(shared["claim_candidates"][0]), "claim_id": second["claim_id"]}
    )
    packets[2]["case_id"] = "QA-08E-LONG"
    packets[2]["context"] = dict.fromkeys(
        ("comment_html", "concerns_html", "response_html"),
        "<p>" + "Invented long review context with units and scope. " * 140 + "</p>",
    )
    tasks = []
    for packet in packets:
        context = packet["context"]
        approved = {
            "review_status": "approved",
            "case_label": packet["case_id"],
            "claims": copy.deepcopy(packet["claims"]),
            "evidence_candidate_claim_ids": [c["claim_id"] for c in packet["claims"]],
            "data": {
                "comment_html": context["comment_html"],
                "concerns_html": context["concerns_html"],
                "sources_html": context["response_html"],
            },
        }
        for task in evidence.prepare_claim_tasks(packet, data_root=root, approved_review=approved):
            task["data"].update(
                qualification_only=True,
                interface_version=VERSION,
                question_version="synthetic.v1",
                upstream_handoff="synthetic-only",
            )
            tasks.append(task)
    return tasks
