"""Versioned evidence-first cards over unchanged Task08E source packets and controls."""

# Native XML and CSS remain readable as complete fragments.
# ruff: noqa: E501

import copy
import html
import json
import xml.etree.ElementTree as ET
from typing import Any

from er_commons import pilot_evidence as evidence

VERSION = "task08e.evidence_cards.v1"


def prepare_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Derive grouped display fields on fresh expanded tasks, preserving source identity."""
    result = copy.deepcopy(tasks)
    for task in result:
        data = task["data"]
        if "packet" not in data or "layout_revision" in data:
            raise ValueError("Fresh expanded tasks required for evidence cards")
        candidates = {c["candidate_id"]: c for c in data["packet"]["candidates"]}
        shown = data["slots"][0]["candidate_ids"]
        capacity = data.get("project_capacity", data["max_candidates"])
        mapping = next(
            m for m in data["packet"]["claim_candidates"] if m["claim_id"] == data["claim_id"]
        )
        data["layout_revision"] = VERSION
        data["evidence_html"] = "<p>Review each evidence item, then record the overall outcome.</p>"
        data["search_gap_html"] = (
            "<p>" + html.escape(mapping["search_gap"]) + "</p>"
            if mapping["search_gap"].strip()
            else "<p>No additional search gap was recorded.</p>"
        )
        data.pop("reviewer_notes_html", None)
        for index in range(1, capacity + 1):
            data[f"c001_p{index:02d}_card_html"] = (
                _card(candidates[shown[index - 1]], data["candidate_aliases"][shown[index - 1]])
                if index <= len(shown)
                else ""
            )
    return result


def _card(candidate: dict[str, Any], alias: str) -> str:
    """Keep proposals, exact parsed content, warnings and provenance together."""
    esc = html.escape
    limits = "".join("<li>" + esc(limit) + "</li>" for limit in candidate["limitations"])
    relation = candidate.get("citation_relation")
    citation_note = ""
    if relation:
        note = (
            relation
            if isinstance(relation, str)
            else relation.get("note", relation.get("description", ""))
        )
        if note:
            citation_note = "<p><strong>Citation note:</strong> " + esc(str(note)) + "</p>"
    return (
        "<h2>"
        + esc(alias)
        + "</h2><h3>Summary</h3><p>"
        + esc(str(candidate.get("source_summary", "No proposed summary supplied.")))
        + "</p><p><small>Astra proposal; verify against the source below.</small></p>"
        + "<h3>Why retrieved</h3><p>"
        + esc(str(candidate.get("retrieval_reason", "No retrieval explanation supplied.")))
        + "</p>"
        + citation_note
        + "<h3>Parsed source</h3>"
        + evidence._source_content_html(candidate, alias)
        + ("<h4>Warnings and limitations</h4><ul>" + limits + "</ul>" if limits else "")
        + "<details><summary>Exact source provenance</summary><pre>"
        + esc(
            json.dumps(
                {
                    "candidate_id": candidate["candidate_id"],
                    "anchors": [
                        {
                            key: anchor[key]
                            for key in ("path", "record_id", "text_field", "start", "end")
                        }
                        for anchor in candidate["anchors"]
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        + "</pre></details>"
    )


def claim_form(max_candidates: int, legacy_form: str) -> str:
    """Move existing native controls beside their sources without changing their values."""
    if type(max_candidates) is not int or max_candidates < 1:
        raise ValueError("Positive integer candidate capacity required")
    native = ET.fromstring(legacy_form)
    controls = {
        node.attrib["name"]: ET.tostring(node, encoding="unicode")
        for node in native.iter()
        if node.tag in {"Choices", "TextArea"}
    }
    selectors = [
        f".evidence-cards:has(.evidence-count-{count}) .pair-{slot}"
        for count in range(max_candidates)
        for slot in range(count + 1, max_candidates + 1)
    ]
    parts = [
        '<View className="evidence-cards"><Style>',
        ".evidence-cards {font:15px/1.55 -apple-system,BlinkMacSystemFont,sans-serif;max-width:1100px;margin:auto}",
        ".evidence-cards pre {white-space:pre-wrap;font-family:inherit;overflow-wrap:anywhere}",
        ".evidence-cards .evidence-card {border:1px solid #cbd5df;border-radius:8px;padding:20px;margin:24px 0}",
        ".evidence-cards table {border-collapse:collapse;width:100%;font-size:13px}",
        ".evidence-cards td,.evidence-cards th {border:1px solid #cad2da;padding:5px;vertical-align:top}",
        ".evidence-cards details {margin:12px 0}",
        ",".join(selectors) + "{display:none}</Style>",
        '<Header value="$claim_heading" size="4"/>',
        '<HyperText name="claim" value="$claim_html" inline="true" selectionEnabled="false"/>',
        '<HyperText name="evidence" value="$evidence_html" inline="true" selectionEnabled="false"/>',
        '<Collapse><Panel value="Question and original comment">',
        '<HyperText name="concerns" value="$concerns_html" inline="true" selectionEnabled="false"/>',
        '<HyperText name="comment" value="$comment_html" inline="true" selectionEnabled="false"/>',
        '</Panel><Panel value="Approved claim links and unresolved scope">',
        '<HyperText name="relevance" value="$relevance_html" inline="true" selectionEnabled="false"/>',
        '</Panel><Panel value="Response context — search leads">',
        '<HyperText name="response" value="$response_html" inline="true" selectionEnabled="false"/>',
        '</Panel><Panel value="Search coverage and remaining gaps">',
        '<HyperText name="search_gap" value="$search_gap_html" inline="true" selectionEnabled="false"/>',
        "</Panel></Collapse>",
    ]
    for index in range(1, max_candidates + 1):
        prefix = f"c001_p{index:02d}"
        parts.extend(
            [
                f'<View className="evidence-card pair-{index}">',
                f'<HyperText name="{prefix}_card" value="${prefix}_card_html" inline="true" selectionEnabled="false"/>',
                f'<Header value="${prefix}_title" size="4"/>',
                controls.pop(prefix + "_label"),
                controls.pop(prefix + "_note"),
                "</View>",
            ]
        )
    parts.extend(
        [
            '<Header value="Overall outcome for this claim" size="4"/>',
            controls.pop("c001_outcome"),
            controls.pop("c001_note"),
            '<Header value="Optional overall reviewer notes" size="4"/>',
            controls.pop("source_summary"),
            "</View>",
        ]
    )
    if controls:
        raise ValueError("Unplaced native controls")
    return "".join(parts)
