"""Regenerable, read-only text cards; never an authoritative source-text store."""

from __future__ import annotations

import html
import json
from typing import TYPE_CHECKING, Any

from er_commons.artifact_io import canonical_json_sha256
from er_commons.response_inventory.release_review import build_selection, primary_id

if TYPE_CHECKING:
    from er_commons.response_inventory.release_inputs import ReleaseInputs

type JsonObject = dict[str, Any]


def build_review_cache(
    inputs: ReleaseInputs,
    view_index: list[JsonObject],
    subject_ids: list[str] | None = None,
) -> dict[str, bytes]:
    """Return an index and only explicitly requested cards; no I/O or recursive graph walk."""
    selection = build_selection(inputs)
    obligations = {obligation["subject_ref"]: obligation for obligation in selection["obligations"]}
    requested = set(subject_ids or [])
    if requested - obligations.keys():
        raise ValueError("05H cache request contains unknown obligation IDs")
    records = _record_index(inputs)
    payloads: dict[str, bytes] = {}
    links = []
    for subject_ref, obligation in obligations.items():
        name = f"cards/{canonical_json_sha256(subject_ref)}.html"
        label = html.escape(subject_ref + " — " + "; ".join(obligation["reasons"]))
        links.append(
            f'<li><a href="{name}">{label}</a></li>'
            if subject_ref in requested
            else f"<li>{label} (not materialized; request this subject ID)</li>"
        )
        if subject_ref not in requested:
            continue
        payloads[name] = _render_card(inputs, records, view_index, obligation)
    payloads["index.html"] = _document(
        "<h1>Task 05H curator review</h1><p>Read-only, regenerable cache. "
        "Record judgments explicitly in the sealed review ledger; this cache records none. "
        "Only requested cards contain text.</p><ul>"
        + "".join(links)
        + "</ul>"
        + '<h2 id="limitations">Shared inherited limitations</h2>'
        + _pre(_coverage_summary(inputs))
        + "<h2>Retained accepted records (references only)</h2>"
        + _pre(inputs.dependencies)
    )
    return payloads


def _render_card(
    inputs: ReleaseInputs,
    records: dict[str, JsonObject],
    view_index: list[JsonObject],
    obligation: JsonObject,
) -> bytes:
    """Render one bounded context with its accepted graph evidence and caveats."""
    evidence_records, context_unit_ids, span_refs = _card_context(
        inputs, records, view_index, obligation
    )
    pieces = [
        "<h1>Curator composition review</h1>",
        "<p>New display review only. Inherited coverage is unchanged. "
        "Target identity does not establish evidence eligibility.</p>",
        _pre(obligation),
    ]

    def source_order(unit_id: str) -> tuple[int, int, str]:
        """Preserve physical source ordering without merging any unit boundaries."""
        first = records[records[unit_id]["span_ids"][0]]["fragments"][0]
        return records[first["page_id"]]["physical_page"], first["text_start"], unit_id

    for unit_id in sorted(context_unit_ids, key=source_order):
        pieces.append(_unit_html(inputs, records, unit_id))
    related_edges = [
        edge
        for edge in inputs.edges
        if edge["source_unit_id"] in context_unit_ids or edge["target_unit_id"] in context_unit_ids
    ]
    pieces.extend(
        ["<h2>Directed graph evidence (no recursive traversal)</h2>", _pre(related_edges)]
    )
    related_subjects = set(context_unit_ids)
    related_subjects.update(
        outcome["mention_id"]
        for outcome in inputs.outcomes
        if outcome["source_unit_id"] in context_unit_ids
    )
    related_diagnostics = [
        row
        for row in inputs.graph_diagnostics
        if related_subjects.intersection(row.get("subject_ids", []))
    ]
    pieces.extend(["<h2>Accepted graph warnings and exceptions</h2>", _pre(related_diagnostics)])
    # Placement exceptions can refer only to spans, without an in-scope source unit.
    for span_id in sorted(span_refs):
        pieces.append(_span_html(records, span_id))
    pieces.extend(
        [
            "<h2>Exact accepted evidence</h2>",
            _pre(evidence_records),
            "<h2>Inherited limitations and coverage</h2>",
            _pre(_coverage_summary(inputs)),
            '<p><a href="../index.html#limitations">'
            "Shared limitations and accepted dependency bindings</a></p>",
        ]
    )
    return _document("".join(pieces))


def _unit_html(inputs: ReleaseInputs, records: dict[str, JsonObject], unit_id: str) -> str:
    """Keep each unit's boundary, raw spans and official outcomes together."""
    pieces: list[str] = []
    unit = records[unit_id]
    pieces.append("<h2>" + html.escape(unit.get("official_label", unit_id)) + "</h2>" + _pre(unit))
    for span_id in unit["span_ids"]:
        pieces.append(_span_html(records, span_id))
    for outcome in inputs.outcomes:
        if outcome["source_unit_id"] == unit_id:
            pieces.append("<h3>Accepted reference outcome and warnings</h3>" + _pre(outcome))
    return "".join(pieces)


def _span_html(records: dict[str, JsonObject], span_id: str) -> str:
    """Show exact source intervals; share this path for units and placement exceptions."""
    pieces: list[str] = []
    for fragment in records[span_id]["fragments"]:
        page = records[fragment["page_id"]]
        start, end = fragment["text_start"], fragment["text_end"]
        pieces.append(
            f"<h3>Physical page {page['physical_page']}; raw Unicode [{start}, {end})</h3>"
        )
        pieces.append(_pre(page["raw_text"][start:end]))
    return "".join(pieces)


def _pre(value: Any) -> str:
    """Escape source content as inert text without changing raw Unicode intervals."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
    return '<pre style="white-space:pre-wrap">' + html.escape(text) + "</pre>"


def _document(body: str) -> bytes:
    """Use a static local document without scripts, remote resources or mutation controls."""
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Task 05H review</title>'
        '<meta http-equiv="Content-Security-Policy" '
        "content=\"default-src 'none'; style-src 'unsafe-inline'\">"
        "<body>" + body + "</body></html>"
    ).encode("utf-8")


def _record_index(inputs: ReleaseInputs) -> dict[str, JsonObject]:
    """Index accepted objects by reference without copying their source text."""
    records: dict[str, JsonObject] = {}
    for rows in (inputs.source_records, inputs.edges, inputs.graph_diagnostics, inputs.outcomes):
        for row in rows:
            record_id = primary_id(row)
            if record_id is not None:
                records[record_id] = row
    for row in inputs.limitations.get("decision_provenance", []):
        records[row["entry_id"]] = row
    return records


def _coverage_summary(inputs: ReleaseInputs) -> JsonObject:
    """Keep the universal caveats readable; individual evidence stays on its own card."""
    binding = inputs.limitations.get("final_f1_warning_binding", {})
    return {
        "coverage": inputs.limitations.get("coverage", {}),
        "final_f1": {
            "general_warning": binding.get("general_warning"),
            "other_mentions_not_proven_draft_final_equivalent": binding.get(
                "other_mentions_not_proven_draft_final_equivalent", 64
            ),
            "draft_final_equivalence_proven": False,
        },
        "figure_rule": "All 178 caption-backed targets remain unavailable as text-only evidence.",
        "review_scope": "Assembled-view confirmation does not upgrade inherited sampled coverage.",
    }


def _card_context(
    inputs: ReleaseInputs,
    records: dict[str, JsonObject],
    view_index: list[JsonObject],
    obligation: JsonObject,
) -> tuple[list[JsonObject], set[str], set[str]]:
    """Choose the subject's direct view, never every comment sharing an answer target."""
    members = obligation["member_refs"]
    evidence_records = [
        records[member_id]
        for member_id in sorted({members[0], members[-1]})
        if member_id in records
    ]
    unit_ids: set[str] = set()
    for row in evidence_records:
        if row.get("record_type") == "source_unit":
            unit_ids.add(row["unit_id"])
        unit_ids.update(
            row[field]
            for field in ("source_unit_id", "target_unit_id", "general_response_unit_id")
            if field in row
        )
        for subject in row.get("subject_ids", []):
            subject_row = records.get(subject, {})
            if subject_row.get("record_type") == "source_unit":
                unit_ids.add(subject)
            elif subject_row.get("source_unit_id"):
                unit_ids.add(subject_row["source_unit_id"])
    roots = {unit_id for unit_id in unit_ids if records[unit_id]["unit_kind"] == "comment"}
    # Only direct comment-response ownership selects a comment-rooted context.
    roots.update(
        edge["source_unit_id"]
        for edge in inputs.edges
        if edge["relation_type"] == "comment_response" and edge["target_unit_id"] in unit_ids
    )
    context_unit_ids = set(unit_ids)
    for view in view_index:
        if view["root_unit_id"] in roots:
            context_unit_ids.update(view["ordered_unit_ids"])
    span_refs = {
        record_id
        for row in evidence_records
        for record_id in [*row.get("evidence_ids", []), row.get("mention_span_id")]
        if records.get(record_id, {}).get("record_type") == "source_span"
    }
    return evidence_records, context_unit_ids, span_refs


def estimate_review_cache_bytes(
    inputs: ReleaseInputs,
    view_index: list[JsonObject],
    subject_ids: list[str] | None = None,
) -> int:
    """Conservatively bound HTML bytes without rendering or slicing source text.

    HTML escaping uses at most six bytes per Unicode character. JSON formatting
    is measured only for selected metadata; source fragments use interval lengths.
    Per-card and per-unit reserves cover fixed markup and headings.
    """
    selection = build_selection(inputs)
    obligations = {row["subject_ref"]: row for row in selection["obligations"]}
    requested = set(subject_ids or [])
    if requested - obligations.keys():
        raise ValueError("05H cache estimate contains unknown obligation IDs")
    records = _record_index(inputs)

    def metadata_size(value: Any) -> int:
        """Bound escaped UTF-8 JSON metadata without creating any rendered output."""
        return len(json.dumps(value, ensure_ascii=False, indent=2)) * 6 + 256

    total = 65536 + metadata_size(inputs.dependencies) + metadata_size(_coverage_summary(inputs))
    total += sum(2048 + metadata_size(row) for row in obligations.values())
    for subject_ref in requested:
        obligation = obligations[subject_ref]
        evidence_records, units, span_refs = _card_context(inputs, records, view_index, obligation)
        total += 65536 + metadata_size(obligation) + metadata_size(evidence_records)
        total += metadata_size(_coverage_summary(inputs))
        related_subjects = set(units)
        for unit_id in units:
            unit = records[unit_id]
            total += 2048 + metadata_size(unit)
            # The renderer displays repeated span references repeatedly, so count each.
            for span_id in unit["span_ids"]:
                for fragment in records[span_id]["fragments"]:
                    total += 1024 + 6 * (fragment["text_end"] - fragment["text_start"])
            for outcome in inputs.outcomes:
                if outcome["source_unit_id"] == unit_id:
                    related_subjects.add(outcome["mention_id"])
                    total += 256 + metadata_size(outcome)
        total += metadata_size(
            [
                edge
                for edge in inputs.edges
                if edge["source_unit_id"] in units or edge["target_unit_id"] in units
            ]
        )
        total += metadata_size(
            [
                row
                for row in inputs.graph_diagnostics
                if related_subjects.intersection(row.get("subject_ids", []))
            ]
        )
        for span_id in span_refs:
            for fragment in records[span_id]["fragments"]:
                total += 1024 + 6 * (fragment["text_end"] - fragment["text_start"])
    return total
