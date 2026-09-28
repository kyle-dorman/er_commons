"""Prepare source-bound evidence cards and normalize explicit human judgments."""

# Keep native XML attributes intact.
# ruff: noqa: E501

import copy
import hashlib
import html
import json
from pathlib import Path
from typing import Any

from er_commons.pilot_citation_units import validate_units
from er_commons.pilot_evidence_forms import (
    CLAIM_FORM_VERSION,
    CONTEXT_CLAIM_FORM_VERSION,
    FORM_VERSION,
    FULLER_CLAIM_FORM_VERSION,
    LAYOUT_CLAIM_FORM_VERSION,
    LEGACY_CLAIM_FORM_VERSION,
    OUTCOMES,
    PAIR_LABELS,
    build_claim_form,
    build_form,
)

# Keep the existing review API while layouts have a separate maintenance home.
__all__ = [
    "CLAIM_FORM_VERSION",
    "CONTEXT_CLAIM_FORM_VERSION",
    "FORM_VERSION",
    "FULLER_CLAIM_FORM_VERSION",
    "LAYOUT_CLAIM_FORM_VERSION",
    "LEGACY_CLAIM_FORM_VERSION",
    "OUTCOMES",
    "PAIR_LABELS",
    "build_claim_form",
    "build_form",
    "SCHEMA",
    "SECTION_SCHEMA",
    "ReviewValidationError",
    "digest",
    "candidate_id",
    "validate_candidates",
    "prepare_task",
    "prepare_claim_tasks",
    "normalize_review",
    "normalize_claim_review",
]

SCHEMA = "er_commons.task07d.evidence_packet.v1"
SECTION_SCHEMA = "er_commons.task07d.evidence_packet.v2"


class ReviewValidationError(ValueError):
    """Expose parsed judgments for explicit audit without accepting an invalid review.

    Structural/native binding failures still raise plain ``ValueError``. This
    exception is only available after trusted input and native controls validate;
    consumers must resolve or explicitly disposition its consistency errors.
    """

    def __init__(self, review: dict[str, Any]) -> None:
        """Retain independent provenance and the original validation message."""
        self.review = copy.deepcopy(review)
        super().__init__("; ".join(review["validation_errors"]))


def digest(value: Any) -> str:
    """Bind JSON values without changing their original content."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def candidate_id(candidate: dict[str, Any]) -> str:
    """Identify exact source content and its presentation/provenance version."""
    return "evidence07d-" + digest({k: v for k, v in candidate.items() if k != "candidate_id"})


def _unique(values: list[str]) -> None:
    """Reject duplicate references rather than silently merging them."""
    if len(values) != len(set(values)):
        raise ValueError("Duplicate reference")


def validate_candidates(packet: dict[str, Any], data_root: Path) -> None:
    """Compare each consumed canonical snapshot and quote to its actual source file."""
    if packet["schema_version"] == SECTION_SCHEMA:
        validate_units(packet["candidates"], data_root)
    cache: dict[tuple[str, str], dict[str, Any]] = {}
    _unique([c["candidate_id"] for c in packet["candidates"]])
    for candidate in packet["candidates"]:
        if candidate["candidate_id"] != candidate_id(candidate):
            raise ValueError("Candidate identity mismatch")
        if candidate["source_id"] == "feir_volume_4":
            raise ValueError("Response text cannot be its own evidence")
        if not candidate["anchors"] or not candidate["physical_pages"]:
            raise ValueError("Canonical anchors and physical pages required")
        if any(type(p) is not int or p < 1 for p in candidate["physical_pages"]):
            raise ValueError("Physical pages must be one based")
        quotes = []
        for anchor in candidate["anchors"]:
            path = (data_root / anchor["path"]).resolve()
            if not path.is_relative_to(data_root.resolve()):
                raise ValueError("Canonical path escapes data root")
            key = (str(path), anchor["record_id_field"])
            if key not in cache:
                records = [
                    json.loads(line) for line in path.read_text().splitlines() if line.strip()
                ]
                indexed = {r[anchor["record_id_field"]]: r for r in records}
                if len(indexed) != len(records):
                    raise ValueError("Duplicate canonical record identity")
                cache[key] = indexed
            actual = cache[key].get(anchor["record_id"])
            if actual != anchor["record"]:
                raise ValueError("Canonical record snapshot differs from source")
            if actual.get("source_id", candidate["source_id"]) != candidate["source_id"]:
                raise ValueError("Candidate source differs from canonical source")
            text = actual
            for component in anchor["text_field"].split("."):
                text = text[int(component)] if isinstance(text, list) else text[component]
            start, end = anchor["start"], anchor["end"]
            if not isinstance(text, str) or not (type(start) is int and type(end) is int):
                raise ValueError("Canonical spans require text and integer offsets")
            if not 0 <= start < end <= len(text) or text[start:end] != anchor["quote"]:
                raise ValueError("Candidate quote differs from canonical span")
            quotes.append(anchor["quote"])
        if candidate["quote"] != "\n\n".join(quotes):
            raise ValueError("Candidate quote must preserve ordered canonical spans")


def _table_html(record: dict[str, Any], header_rows: int) -> str:
    """Merge empty header placeholders for display while preserving every body cell."""
    rows: dict[int, list[dict[str, Any]]] = {}
    for cell in record["cells"]:
        rows.setdefault(cell["row_index"], []).append(cell)
    if type(header_rows) is not int or not 0 <= header_rows <= len(rows):
        raise ValueError("Invalid presentation header row count")
    output = [
        '<div style="overflow-x:auto"><table style="border-collapse:collapse;font:13px/1.5 sans-serif;min-width:950px" border="1" cellpadding="6">'
    ]
    for ordinal, (_, cells) in enumerate(sorted(rows.items())):
        ordered = sorted(cells, key=lambda cell: cell["column_index"])
        output.append("<tr>")
        index = 0
        while index < len(ordered):
            cell = ordered[index]
            span = 1
            if ordinal < header_rows and cell["text"].strip():
                while index + span < len(ordered) and not ordered[index + span]["text"].strip():
                    span += 1
            tag = "th" if ordinal < header_rows else "td"
            attribute = f' colspan="{span}"' if span > 1 else ""
            output.append(f"<{tag}{attribute}>" + html.escape(cell["text"]) + f"</{tag}>")
            index += span
        output.append("</tr>")
    output.append("</table></div>")
    return "".join(output)


def _source_content_html(candidate: dict[str, Any], alias: str) -> str:
    """Render citation metadata and source content without curator commentary."""
    esc = html.escape
    table_html = ""
    table_records = {
        a["record_id"]: a["record"] for a in candidate["anchors"] if "cells" in a["record"]
    }
    for record in table_records.values():
        table_html += _table_html(record, candidate.get("presentation_header_rows", 0))
    if table_html:
        table_html += "".join(
            "<pre>" + esc(anchor["quote"]) + "</pre>"
            for anchor in candidate["anchors"]
            if "cells" not in anchor["record"]
        )
    narrative_html = "<pre>" + esc(candidate["quote"]) + "</pre>"
    if candidate.get("display_segments"):
        text_by_id = {a["record_id"]: a["quote"] for a in candidate["anchors"]}
        narrative_html = "".join(
            "<pre>" + esc(text_by_id[segment["record_id"]]) + "</pre>"
            if segment["kind"] == "text"
            else '<p><a target="_blank" href="'
            + esc(segment["pdf_url"], quote=True)
            + '">'
            + esc(segment["label"])
            + "</a></p>"
            for segment in candidate["display_segments"]
        )
    link = candidate.get("pdf_url", candidate["source_url"])
    if not link.startswith(("http://", "https://")):
        raise ValueError("Source links require HTTP URLs")
    unit = candidate.get("citation_unit")
    title = unit["citation_label"] if unit else candidate.get("title", candidate["source_id"])
    breadcrumb = " > ".join(item["heading_text"] for item in unit["breadcrumb"]) if unit else ""
    return (
        f'<p><a href="{esc(link, quote=True)}" target="_blank">Open source PDF</a></p>'
        f"<h3>{alias} · {esc(title)}</h3>"
        + (
            f"<details><summary>Section path</summary><p>{esc(breadcrumb)}</p></details>"
            if breadcrumb
            else ""
        )
        + f"<p>{esc(candidate['edition'])}"
        + (f" · {esc(candidate['source_id'])}" if unit else "")
        + " · PDF pages "
        f"{esc(str(candidate['physical_pages']))} · printed "
        f"{esc(str(candidate['printed_labels']))}</p>"
        + (
            f"{table_html}<details><summary>Exact anchored text</summary><pre>{esc(candidate['quote'])}</pre></details>"
            if table_html
            else narrative_html
        )
    )


def _candidate_html(candidate: dict[str, Any], alias: str) -> str:
    """Preserve historical cards with source content followed by curator notes."""
    esc = html.escape
    return (
        _source_content_html(candidate, alias)
        + "<p>Source limits</p><ul>"
        + "".join("<li>" + esc(limit) + "</li>" for limit in candidate["limitations"])
        + "</ul>"
        + "<details><summary>Exact canonical anchors</summary><pre>"
        + esc(
            "\n".join(
                f"{a['path']} · {a['record_id']} · {a['text_field']}[{a['start']}:{a['end']}]"
                for a in candidate["anchors"]
            )
        )
        + "</pre></details>"
    )


def _source_excerpt_html(candidate: dict[str, Any], alias: str) -> str:
    """Keep only source citation and verbatim content in the citable source pane."""
    source = _source_content_html(candidate, alias)
    return (
        '<section class="source-excerpt">'
        + source.replace("<h3>", "<h3>Source excerpt · ", 1)
        + "</section>"
    )


def _reviewer_notes_html(
    mapping: dict[str, Any], candidates: dict[str, Any], aliases: dict[str, str]
) -> str:
    """Label discovery commentary separately from quotations and human judgments."""
    esc = html.escape
    parts = ['<section class="reviewer-notes"><h3>Reviewer notes — not source text</h3>']
    if mapping["search_gap"].strip():
        parts.append("<p>Search coverage: " + esc(mapping["search_gap"]) + "</p>")
    overflow = mapping["overflow_candidate_ids"]
    if overflow:
        parts.append(
            "<p>Additional candidates: " + esc(", ".join(aliases[e] for e in overflow)) + "</p>"
        )
    for identity in mapping["candidate_ids"]:
        candidate = candidates[identity]
        reason = candidate.get("retrieval_reason")
        if reason is not None:
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("Retrieval reason requires readable text")
            parts.append(
                "<p><strong>"
                + aliases[identity]
                + " — why retrieved:</strong> "
                + esc(reason)
                + "</p>"
            )
        relation = candidate.get("citation_relation")
        if relation:
            kind = str(relation.get("kind", "")) if isinstance(relation, dict) else ""
            if kind == "supplied":
                continue
            label = {"corrected": "corrected citation", "omitted": "additional citation"}.get(
                kind, "citation note"
            )
            note = (
                relation
                if isinstance(relation, str)
                else relation.get("note", relation.get("description", ""))
            )
            if not note:
                raise ValueError("Citation relation requires a readable note")
            parts.append(
                "<p><strong>" + aliases[identity] + " " + label + ":</strong> " + esc(note) + "</p>"
            )
    parts.append("<details><summary>Source provenance and extraction notes</summary>")
    for identity in mapping["candidate_ids"]:
        candidate = candidates[identity]
        parts.append("<h4>" + aliases[identity] + "</h4><ul>")
        parts.extend("<li>" + esc(limit) + "</li>" for limit in candidate["limitations"])
        parts.append(
            "</ul><pre>"
            + esc(
                "\n".join(
                    f"{a['path']} · {a['record_id']} · {a['text_field']}[{a['start']}:{a['end']}]"
                    for a in candidate["anchors"]
                )
            )
            + "</pre>"
        )
    parts.append("</details></section>")
    return "".join(parts)


def prepare_task(
    packet: dict[str, Any], *, data_root: Path, approved_review: dict[str, Any]
) -> dict[str, Any]:
    """Prepare historical case-level cards with their original presentation budget."""
    return _prepare_task(
        packet, data_root=data_root, approved_review=approved_review, max_candidates=3
    )


def _prepare_task(
    packet: dict[str, Any],
    *,
    data_root: Path,
    approved_review: dict[str, Any],
    max_candidates: int | None,
) -> dict[str, Any]:
    """Validate immutable inputs before either bounded historical or full claim display."""
    if (
        packet["schema_version"] not in {SCHEMA, SECTION_SCHEMA}
        or approved_review["review_status"] != "approved"
    ):
        raise ValueError("Approved review and supported packet schema required")
    if packet["case_id"] != approved_review["case_label"]:
        raise ValueError("Foreign case")
    queued = approved_review["evidence_candidate_claim_ids"]
    expected = [c for c in approved_review["claims"] if c["claim_id"] in queued]
    if packet["claims"] != expected or len(expected) != len(queued):
        raise ValueError("Claims differ from immutable reviewed queue")
    expected_context = {
        "comment_html": approved_review["data"]["comment_html"],
        "concerns_html": approved_review["data"]["concerns_html"],
        "response_html": approved_review["data"]["sources_html"],
    }
    if packet["context"] != expected_context:
        raise ValueError("Context differs from trusted approved review")
    validate_candidates(packet, data_root)
    by_id = {c["candidate_id"]: c for c in packet["candidates"]}
    mappings = packet["claim_candidates"]
    if [m["claim_id"] for m in mappings] != [c["claim_id"] for c in expected]:
        raise ValueError("Claim candidate mappings must follow exact queue order")
    esc = html.escape
    data: dict[str, Any] = {
        "form_version": FORM_VERSION,
        "packet": copy.deepcopy(packet),
        "packet_sha256": digest(packet),
        "review_sha256": digest(approved_review),
        "case_label": packet["case_id"],
        "comment_html": packet["context"]["comment_html"],
        "concerns_html": packet["context"]["concerns_html"],
        "response_html": packet["context"]["response_html"],
        "slots": [],
    }
    aliases = {identity: f"E{i:02d}" for i, identity in enumerate(by_id, 1)}
    cards = []
    displayed = {identity for mapping in mappings for identity in mapping["candidate_ids"]}
    for candidate in by_id.values():
        if candidate["candidate_id"] not in displayed:
            continue
        identity = candidate["candidate_id"]
        cards.append(_candidate_html(candidate, aliases[identity]))
    data["evidence_html"] = "".join(cards) or "<p>No candidate evidence found.</p>"
    for index, (claim, mapping) in enumerate(zip(expected, mappings, strict=True), 1):
        shown, overflow = mapping["candidate_ids"], mapping["overflow_candidate_ids"]
        _unique(shown + overflow)
        if (max_candidates is not None and len(shown) > max_candidates) or not set(
            shown + overflow
        ) <= by_id.keys():
            raise ValueError("Unknown candidates or presentation budget exceeded")
        has_presented_candidates = bool(shown or (max_candidates is None and overflow))
        if not has_presented_candidates and not mapping["search_gap"].strip():
            raise ValueError("No candidates requires an explicit search gap")
        slot = f"c{index:03d}"
        data["slots"].append({"slot": slot, "claim_id": claim["claim_id"], "candidate_ids": shown})
        data[f"{slot}_html"] = (
            f"<h3>{esc(claim['local_id'])}</h3><p>{esc(claim['text'])}</p>"
            f"<p>Reviewed relevance: {esc(claim['relationship'])}. "
            "This does not establish evidence support.</p>"
            f"<p>Search gap / limits: {esc(mapping['search_gap'])}</p>"
            f"<p>Overflow: {esc(', '.join(aliases[e] for e in overflow)) or 'none'}</p>"
        )
        for pair_index, identity in enumerate(shown, 1):
            data[f"{slot}_p{pair_index:02d}_title"] = f"Relationship to {aliases[identity]}"
    data["candidate_aliases"] = aliases
    return {"data": data}


def _native_review_fields(
    data: dict[str, Any],
    annotation: dict[str, Any],
    *,
    status_field: str,
    note_field: str,
    simplified: bool,
) -> dict[str, Any]:
    """Parse only controls declared by the trusted task; reject foreign values."""
    allowed = {} if simplified else {status_field: "choices", note_field: "textarea"}
    for binding in data["slots"]:
        slot = binding["slot"]
        allowed.update({slot + "_outcome": "choices", slot + "_note": "textarea"})
        if binding["candidate_ids"] and not simplified:
            allowed[slot + "_set"] = "choices"
        for index, _ in enumerate(binding["candidate_ids"], 1):
            prefix = f"{slot}_p{index:02d}"
            allowed.update({prefix + "_label": "choices", prefix + "_note": "textarea"})
    fields: dict[str, Any] = {}
    for result in annotation["result"]:
        name = result["from_name"]
        if name not in allowed or name in fields or result["to_name"] != "evidence":
            raise ValueError("Unknown, duplicate, or foreign native field")
        if result["type"] != allowed[name]:
            raise ValueError("Wrong native field type")
        values = result["value"]["text" if result["type"] == "textarea" else "choices"]
        if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
            raise ValueError("Native values must be string lists")
        _unique(values)
        if not name.endswith("_set") and len(values) > 1:
            raise ValueError("Single value required")
        fields[name] = values if name.endswith("_set") else (values[0] if values else "")
    return fields


def _normalize_review(
    task: dict[str, Any],
    annotation: dict[str, Any],
    *,
    expected_task: dict[str, Any],
    export_lineage: str,
    claim_level: bool = False,
) -> dict[str, Any]:
    """Retain native provenance and require explicit, non-inferred support outcomes."""
    if task.get("data") != expected_task["data"] or not export_lineage.strip():
        raise ValueError("Trusted task and export lineage required")
    if task.get("id") is None or annotation.get("task") != task["id"]:
        raise ValueError("Foreign or unbound annotation")
    if annotation.get("id") is None or annotation.get("completed_by") is None:
        raise ValueError("Saved annotation and reviewer required")
    if annotation.get("was_cancelled") or annotation.get("skipped"):
        raise ValueError("Canceled annotations cannot become reviews")
    data = task["data"]
    status_field = "claim_status" if claim_level else "case_status"
    note_field = "claim_note" if claim_level else "case_note"
    simplified = claim_level and data["form_version"] == CLAIM_FORM_VERSION
    fields = _native_review_fields(
        data,
        annotation,
        status_field=status_field,
        note_field=note_field,
        simplified=simplified,
    )
    status = fields.get(status_field)
    if not simplified and status not in {"reviewed", "needs_context"}:
        raise ValueError(f"Explicit {status_field} required")
    errors, reviews = [], []
    for binding in data["slots"]:
        slot = binding["slot"]
        pairs = []
        for index, identity in enumerate(binding["candidate_ids"], 1):
            prefix = f"{slot}_p{index:02d}"
            label, note = fields.get(prefix + "_label", ""), fields.get(prefix + "_note", "")
            if label not in PAIR_LABELS:
                errors.append(f"{prefix}: missing relationship")
            if label in {"partial", "contradicts", "unusable"} and not note.strip():
                errors.append(f"{prefix}: explanation required")
            pairs.append({"candidate_id": identity, "relationship": label, "note": note})
        outcome, note = fields.get(slot + "_outcome", ""), fields.get(slot + "_note", "")
        selected = fields.get(slot + "_set", [])
        aliases = {data["candidate_aliases"][e]: e for e in binding["candidate_ids"]}
        if not set(selected) <= aliases.keys():
            raise ValueError("Unknown evidence set member")
        if outcome not in OUTCOMES:
            errors.append(f"{slot}: missing claim outcome")
        if not simplified and outcome in {"supported", "partial", "conflicting"} and not selected:
            errors.append(f"{slot}: evidence set required")
        if (
            outcome in {"partial", "conflicting", "unresolved"}
            or (not simplified and len(selected) > 1)
        ) and not note.strip():
            errors.append(f"{slot}: explanation required")
        selected_labels = [
            p["relationship"]
            for p in pairs
            if simplified or p["candidate_id"] in {aliases[a] for a in selected}
        ]
        if outcome == "supported" and not (
            "supports" in selected_labels or selected_labels.count("partial") >= 2
        ):
            errors.append(
                f"{slot}: supported outcome needs supporting evidence or a reasoned joint partial set"
            )
        if (
            simplified
            and outcome == "supported"
            and "supports" not in selected_labels
            and selected_labels.count("partial") >= 2
            and not note.strip()
        ):
            errors.append(f"{slot}: joint partial support needs an explanation")
        if outcome == "partial" and not set(selected_labels).intersection({"supports", "partial"}):
            errors.append(f"{slot}: partial outcome needs positive evidence")
        if outcome == "conflicting" and "contradicts" not in selected_labels:
            errors.append(f"{slot}: conflicting outcome needs contradictory evidence")
        if (
            outcome == "no_support_found"
            and any(p["relationship"] in {"supports", "partial"} for p in pairs)
            and not note.strip()
        ):
            errors.append(
                f"{slot}: no-support outcome conflicts with positive pair judgments; explain"
            )
        reviews.append(
            {
                "claim_id": binding["claim_id"],
                "pairs": pairs,
                "outcome": outcome,
                **({} if simplified else {"evidence_set": [aliases[a] for a in selected]}),
                "note": note,
            }
        )
    if status == "needs_context" and not fields.get(note_field, "").strip():
        errors.append("Context request needs a note")
    result = {
        "schema_version": (
            "er_commons.task07d.claim_evidence_review.v2"
            if simplified
            else "er_commons.task07d.claim_evidence_review.v1"
            if claim_level
            else "er_commons.task07d.evidence_review.v1"
        ),
        "case_id": data["case_label"],
        "packet_sha256": data["packet_sha256"],
        "task_sha256": digest(data),
        "form_sha256": hashlib.sha256(
            (
                build_claim_form(data["form_version"], max_candidates=data.get("max_candidates", 3))
                if claim_level
                else build_form(expected_task)
            ).encode()
        ).hexdigest(),
        **(
            {"review_complete": not errors}
            if simplified
            else {status_field: status, note_field: fields.get(note_field, "")}
        ),
        "claims": reviews,
        "validation_errors": errors,
        "export_lineage": export_lineage,
        "task_id": task["id"],
        "annotation_id": annotation["id"],
        "reviewer": annotation["completed_by"],
        "created_at": annotation.get("created_at"),
        "updated_at": annotation.get("updated_at"),
        "native_annotation": copy.deepcopy(annotation),
        "annotation_sha256": digest(annotation),
    }
    if (simplified or status == "reviewed") and errors:
        raise ReviewValidationError(result)
    return result


def prepare_claim_tasks(
    packet: dict[str, Any], *, data_root: Path, approved_review: dict[str, Any]
) -> list[dict[str, Any]]:
    """Validate the whole approved case before deriving independently reviewable claims."""
    case = _prepare_task(
        packet, data_root=data_root, approved_review=approved_review, max_candidates=None
    )
    max_candidates = max(
        [1]
        + [
            len(m["candidate_ids"]) + len(m["overflow_candidate_ids"])
            for m in packet["claim_candidates"]
        ]
    )
    by_id = {candidate["candidate_id"]: candidate for candidate in packet["candidates"]}
    tasks = []
    for index, (claim, mapping) in enumerate(
        zip(packet["claims"], packet["claim_candidates"], strict=True), 1
    ):
        data = copy.deepcopy(case["data"])
        for key in list(data):
            if key.startswith("c") and (key.endswith("_html") or key.endswith("_title")):
                if key not in {"comment_html", "concerns_html"}:
                    del data[key]
        shown = mapping["candidate_ids"] + mapping["overflow_candidate_ids"]
        display_mapping = {**mapping, "candidate_ids": shown, "overflow_candidate_ids": []}
        aliases = data["candidate_aliases"]
        data.update(
            form_version=CLAIM_FORM_VERSION,
            max_candidates=max_candidates,
            claim_id=claim["claim_id"],
            claim=copy.deepcopy(claim),
            claim_index=index,
            claim_count=len(packet["claims"]),
            claim_task_id="claimreview07d-"
            + digest(
                {
                    "packet_sha256": data["packet_sha256"],
                    "claim_id": claim["claim_id"],
                    "form_version": CLAIM_FORM_VERSION,
                    "max_candidates": max_candidates,
                }
            ),
            claim_heading=f"{packet['case_id']} · {claim['local_id']} · {index} of {len(packet['claims'])}",
            slots=[
                {
                    "slot": "c001",
                    "claim_id": claim["claim_id"],
                    "candidate_ids": copy.deepcopy(shown),
                }
            ],
            evidence_html="".join(_source_excerpt_html(by_id[e], aliases[e]) for e in shown)
            or "<p>No candidate evidence found in this search.</p>",
            evidence_options=[{"value": aliases[e]} for e in shown],
            claim_html=(
                f'<div class="evidence-count-{len(shown)}"><h2>{html.escape(claim["text"])}</h2></div>'
            ),
            reviewer_notes_html=_reviewer_notes_html(display_mapping, by_id, aliases),
            relevance_html=(
                f"<p>Previously reviewed relevance: {html.escape(claim['relationship'])}. "
                "This does not establish evidence support.</p>"
                "<pre>" + html.escape(json.dumps(claim, ensure_ascii=False, indent=2)) + "</pre>"
            ),
        )
        for pair in range(1, max_candidates + 1):
            data[f"c001_p{pair:02d}_title"] = (
                f"Relationship to {aliases[shown[pair - 1]]}" if pair <= len(shown) else ""
            )
        tasks.append({"data": data})
    return tasks


def normalize_review(
    task: dict[str, Any],
    annotation: dict[str, Any],
    *,
    expected_task: dict[str, Any],
    export_lineage: str,
) -> dict[str, Any]:
    """Normalize the preserved case-level v1 form without accepting claim-task status."""
    if expected_task["data"]["form_version"] != FORM_VERSION:
        raise ValueError("Case-level v1 task required")
    return _normalize_review(
        task, annotation, expected_task=expected_task, export_lineage=export_lineage
    )


def normalize_claim_review(
    task: dict[str, Any],
    annotation: dict[str, Any],
    *,
    expected_task: dict[str, Any],
    export_lineage: str,
) -> dict[str, Any]:
    """Bind one human claim outcome without asserting whole-case completion."""
    data = expected_task["data"]
    if (
        data["form_version"]
        not in {
            CLAIM_FORM_VERSION,
            FULLER_CLAIM_FORM_VERSION,
            CONTEXT_CLAIM_FORM_VERSION,
            LAYOUT_CLAIM_FORM_VERSION,
            LEGACY_CLAIM_FORM_VERSION,
        }
        or len(data["slots"]) != 1
    ):
        raise ValueError("Single-claim task required")
    if data["form_version"] in {CLAIM_FORM_VERSION, FULLER_CLAIM_FORM_VERSION}:
        expected_capacity = max(
            [1]
            + [
                len(m["candidate_ids"]) + len(m["overflow_candidate_ids"])
                for m in data["packet"]["claim_candidates"]
            ]
        )
        if (
            type(data.get("max_candidates")) is not int
            or data["max_candidates"] != expected_capacity
        ):
            raise ValueError("Candidate capacity differs from packet")
    if data["slots"][0]["claim_id"] != data["claim_id"]:
        raise ValueError("Claim binding mismatch")
    try:
        result = _normalize_review(
            task,
            annotation,
            expected_task=expected_task,
            export_lineage=export_lineage,
            claim_level=True,
        )
    except ReviewValidationError as error:
        _bind_claim_review(error.review, data)
        raise
    _bind_claim_review(result, data)
    return result


def _bind_claim_review(result: dict[str, Any], data: dict[str, Any]) -> None:
    """Give successful and rejected claim reviews the same single-claim shape."""
    result["claim_id"] = data["claim_id"]
    result["claim_task_id"] = data["claim_task_id"]
    result["claim_review"] = result.pop("claims")[0]
