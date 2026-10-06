"""Citation-first human relationships over immutable Task08E investigation packets."""

# Readable native XML/CSS fragments intentionally retain their complete attributes.
# ruff: noqa: E501

import copy
import hashlib
import html
from pathlib import Path
from typing import Any

from er_commons import group_evidence as shared
from er_commons import group_evidence_live as live
from er_commons import pilot_evidence as evidence
from er_commons.group_evidence_transport import hydrate_tasks

VERSION = "task08e.citation_review.v1"
LABELS = {
    "supports": "Supports",
    "partial": "Partially supports",
    "context": "Context only",
    "not_support": "Does not support",
    "contradicts": "Contradicts",
}
_PROCESS_WARNING = (
    "fresh Task 06H review was a bounded sample; unreviewed repaired-source rows retain "
    "accepted dispositions through matching source/disposition strata"
)


def _display_limitations(limitations: list[str]) -> list[str]:
    """Separate known workflow diagnostics from source-specific interpretation limits."""
    replacements = {
        _PROCESS_WARNING: "",
        "Exact canonical bytes retained. Fresh agent render comparison is not a saved human table-usability or evidence decision.": "",
        "Figure 2 and its canonical placeholder/captions remain part of the unit boundary. Parent must preserve any unavailable-visual limitation; no map-distance or count inference was made.": "Figure 2 is not available as reviewed visual evidence; no map distances or counts were evaluated.",
        "Both tbl 190 and 191 are required. Preserve project thresholds 1.0 HI and 0.3µg/m 3; they are not cumulative 10.0 HI and 0.8µg/m 3.": "Project thresholds are 1.0 HI and 0.3µg/m 3; cumulative thresholds are 10.0 HI and 0.8µg/m 3.",
        "No residential-distance conclusion follows from the school row. Both table-family members 264 and 265 must be rendered and reviewed; a numeric source location is not an enforceable 500-foot setback.": "The school row does not establish residential distances or an enforceable 500-foot setback.",
        "Regional table tbl000173 is separate and not claim-relevant; preserve full narrative and source CO daily wording.": "The regional table is separate from the local analysis; the source states the CO screen in daily units.",
        "The school exposure note and narrative continuation lie in section 1387 and must accompany the table.": "School exposure assumptions are stated in the accompanying note and continued narrative.",
    }
    result = []
    for item in limitations:
        if (
            item.startswith("WARNING: /Volumes/")
            and "Resources is missing or invalid; repairing" in item
        ):
            display = ""
        else:
            display = replacements.get(item, item)
        if display:
            result.append(display)
    return result


def _source_html(candidate: dict[str, Any], alias: str) -> str:
    """Render exact maintained source content and only source-specific visible limitations."""
    esc = html.escape
    limits = _display_limitations(candidate["limitations"])
    return (
        '<section class="overview"><h3>Summary</h3><p>'
        + esc(str(candidate.get("source_summary", "")))
        + "</p><h3>Why retrieved</h3><p>"
        + esc(str(candidate.get("retrieval_reason", "")))
        + '</p></section><hr/><section class="parsed-source"><h3>Parsed source</h3>'
        + evidence._source_content_html(candidate, alias)
        + "</section><hr/>"
        + (
            '<details class="source-limits"><summary>Source limitations</summary><ul>'
            + "".join("<li>" + esc(item) + "</li>" for item in limits)
            + "</ul></details>"
            if limits
            else ""
        )
    )


def prepare_tasks(
    expanded_claim_tasks: list[dict[str, Any]],
    *,
    data_root: Path,
    case_names: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Transpose exact approved claim queues into blank citation-by-claim review tasks.

    Saved annotations are never migrated. Full packets retain every search gap,
    warning, approved chain and unresolved upstream part, outside the focused UI.
    """
    cases: dict[str, list[dict[str, Any]]] = {}
    for task in expanded_claim_tasks:
        data = task["data"]
        if (
            data.get("interface_version") != live.VERSION
            or data.get("qualification_only") is not False
        ):
            raise ValueError("Current live investigation tasks required")
        cases.setdefault(data["case_label"], []).append(data)
    result = []
    for case_id, rows in cases.items():
        first = rows[0]
        packet = first["packet"]
        if evidence.digest(packet) != first["packet_sha256"]:
            raise ValueError("Packet identity differs")
        evidence.validate_candidates(packet, data_root)
        claims = packet["claims"]
        claim_ids = [claim["claim_id"] for claim in claims]
        if len(set(claim_ids)) != len(claim_ids) or sorted(
            row["claim_id"] for row in rows
        ) != sorted(claim_ids):
            raise ValueError("Exact approved claim queue required")
        for row in rows:
            if any(
                row[key] != first[key]
                for key in (
                    "packet",
                    "packet_sha256",
                    "upstream_case",
                    "upstream_handoff_sha256",
                    "candidate_aliases",
                )
            ):
                raise ValueError("Mixed case or source bindings")
            if row["claim"] != next(c for c in claims if c["claim_id"] == row["claim_id"]):
                raise ValueError("Approved claim differs")
        mappings = packet["claim_candidates"]
        if sorted(m["claim_id"] for m in mappings) != sorted(claim_ids):
            raise ValueError("Exact proposal claim mappings required")
        for candidate in packet["candidates"]:
            identity = candidate["candidate_id"]
            proposed = {
                m["claim_id"]
                for m in mappings
                if identity in m["candidate_ids"] + m.get("overflow_candidate_ids", [])
            }
            slots = []
            fields: dict[str, Any] = {}
            for group, selected in (("p", True), ("o", False)):
                grouped = [claim for claim in claims if (claim["claim_id"] in proposed) == selected]
                fields[group + "_count"] = len(grouped)
                for index, claim in enumerate(grouped, 1):
                    prefix = f"{group}{index:03d}"
                    slots.append(
                        {"prefix": prefix, "claim": copy.deepcopy(claim), "proposed": selected}
                    )
                    fields[prefix + "_html"] = (
                        "<h3>"
                        + html.escape(claim["claim_id"])
                        + "</h3><p>"
                        + html.escape(claim["text"])
                        + "</p>"
                    )
            alias = first["candidate_aliases"][identity]
            result.append(
                {
                    "data": {
                        "interface_version": VERSION,
                        "qualification_only": False,
                        "case_label": case_id,
                        "candidate_id": identity,
                        "citation_alias": alias,
                        "heading": (case_names or {}).get(case_id, case_id) + " · " + alias,
                        "packet": copy.deepcopy(packet),
                        "packet_sha256": first["packet_sha256"],
                        "upstream_case": copy.deepcopy(first["upstream_case"]),
                        "upstream_handoff_sha256": first["upstream_handoff_sha256"],
                        "slots": slots,
                        "max_claims": len(claims),
                        "evidence_html": _source_html(candidate, alias),
                        "visibility_html": f'<span class="p-count-{fields["p_count"]} o-count-{fields["o_count"]}"></span>',
                        **fields,
                    }
                }
            )
    if not result:
        raise ValueError("At least one citation required")
    return bind_project_capacity(result)


def bind_project_capacity(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Bind one shared native form and fill inactive display fields without fake claims."""
    result = copy.deepcopy(tasks)
    capacity = max(task["data"]["max_claims"] for task in result)
    for task in result:
        data = task["data"]
        data["project_capacity"] = capacity
        for group in ("p", "o"):
            for index in range(1, capacity + 1):
                data.setdefault(f"{group}{index:03d}_html", "")
    return result


def citation_form(max_claims: int) -> str:
    """Show one complete citation followed by independent optional claim relationships."""
    if type(max_claims) is not int or max_claims < 1:
        raise ValueError("Positive integer claim capacity required")
    hidden = [
        f".citation-review:has(.{group}-count-{count}) .{group}-slot-{slot}"
        for group in ("p", "o")
        for count in range(max_claims)
        for slot in range(count + 1, max_claims + 1)
    ]
    parts = [
        '<View className="citation-review"><Style>',
        ".citation-review{max-width:1050px;margin:auto;font:16px/1.65 sans-serif}",
        ".citation-review h3{margin:24px 0 12px!important;font-size:19px!important}",
        ".citation-review p{margin:14px 0 24px!important;line-height:1.65!important}",
        ".citation-review pre{white-space:pre-wrap;overflow-wrap:anywhere;font:16px/1.8 sans-serif!important;margin:28px 0!important}",
        ".citation-review hr{border:0;border-top:2px solid #b8c2cc;margin:34px 0!important}",
        ".citation-review .parsed-source{padding:12px 24px;background:#f8fafc}",
        ".citation-review .claim-link{padding:20px 4px 28px;border-bottom:1px solid #cbd5e1;margin:16px 0 28px}",
        ".citation-review table{border-collapse:collapse!important;font-size:15px!important;line-height:1.5!important}",
        ".citation-review th,.citation-review td{border:1px solid #cbd5e1!important;padding:8px!important;font-size:15px!important;line-height:1.5!important;vertical-align:top}",
        ".citation-review details{margin:20px 0}",
        ",".join(hidden) + "{display:none}",
        '</Style><Header value="$heading" size="2"/>',
        '<HyperText name="visibility" value="$visibility_html" inline="true" selectionEnabled="false"/>',
        '<HyperText name="evidence" value="$evidence_html" inline="true" selectionEnabled="false"/>',
        '<Header value="Relationships to claims" size="3"/>',
    ]
    for group in ("p", "o"):
        if group == "o":
            parts.append('<Collapse><Panel value="Link another claim">')
        for index in range(1, max_claims + 1):
            prefix = f"{group}{index:03d}"
            parts.extend(
                [
                    f'<View className="claim-link {group}-slot-{index}">',
                    f'<HyperText name="{prefix}_claim" value="${prefix}_html" inline="true" selectionEnabled="false"/>',
                    f'<Choices name="{prefix}_label" toName="evidence" choice="single-radio" showInLine="false">',
                    "".join(
                        f'<Choice value="{prefix}_label_{key}" html="{value}" alias="{key}"/>'
                        for key, value in LABELS.items()
                    ),
                    "</Choices>",
                    f'<TextArea name="{prefix}_note" toName="evidence" rows="2" editable="true" maxSubmissions="1" showSubmitButton="false" placeholder="Optional note"/>',
                    "</View>",
                ]
            )
        if group == "o":
            parts.append("</Panel></Collapse>")
    return "".join(parts) + "</View>"


def normalize_export(
    exported_tasks: list[dict[str, Any]],
    *,
    expected_tasks: list[dict[str, Any]],
    project_id: int,
    actual_form: str,
    reviewer_id: int | str,
    export_lineage: str,
    data_root: Path,
) -> dict[str, Any]:
    """Validate saved native bindings and preserve undecided links without aggregate votes."""
    if not expected_tasks or not export_lineage.strip():
        raise ValueError("Expected queue and export lineage required")
    capacities = {t["data"].get("project_capacity") for t in expected_tasks}
    if len(capacities) != 1 or actual_form != citation_form(next(iter(capacities))):
        raise ValueError("Exact homogeneous citation form required")
    expected = {evidence.digest(t["data"]): t for t in expected_tasks}
    if len(expected) != len(expected_tasks):
        raise ValueError("Duplicate expected tasks")
    seen: set[str] = set()
    native_ids: set[int] = set()
    for task in exported_tasks:
        binding = evidence.digest(task["data"])
        if binding not in expected or binding in seen or task.get("id") in native_ids:
            raise ValueError("Unexpected or duplicate queue task")
        if (
            type(task.get("id")) is not int
            or task["id"] < 1
            or task.get("project") != project_id
            or expected[binding].get("id", task["id"]) != task["id"]
        ):
            raise ValueError("Native project/task identity differs")
        annotations = task.get("annotations", [])
        if annotations and (
            len(annotations) != 1 or annotations[0].get("completed_by") != reviewer_id
        ):
            raise ValueError("One saved annotation by configured reviewer required")
        seen.add(binding)
        native_ids.add(task["id"])
    if seen != set(expected):
        raise ValueError("Missing queue tasks")
    hydrated = hydrate_tasks(expected_tasks, data_root=data_root)
    expanded = {
        evidence.digest(t["data"]): e for t, e in zip(expected_tasks, hydrated, strict=True)
    }
    validated = set()
    for task in hydrated:
        data = task["data"]
        if data.get("interface_version") != VERSION or data.get("qualification_only") is not False:
            raise ValueError("Current citation interface required")
        if evidence.digest(data["packet"]) != data["packet_sha256"]:
            raise ValueError("Packet identity differs")
        if data["packet_sha256"] not in validated:
            evidence.validate_candidates(data["packet"], data_root)
            validated.add(data["packet_sha256"])
    records, pending = [], []
    for task in exported_tasks:
        binding = evidence.digest(task["data"])
        data = expanded[binding]["data"]
        annotations = task.get("annotations", [])
        if not annotations:
            pending.append(task["id"])
            continue
        annotation = annotations[0]
        controls = {
            slot["prefix"] + suffix: (kind, "evidence")
            for slot in data["slots"]
            for suffix, kind in (("_label", "choices"), ("_note", "textarea"))
        }
        fields = shared._native_fields(
            {**task, "data": data}, annotation, expanded[binding], controls
        )
        relationships = []
        for slot in data["slots"]:
            label = fields.get(slot["prefix"] + "_label")
            if label is not None and label not in LABELS:
                raise ValueError("Unknown relationship label")
            relationships.append(
                {
                    "claim": copy.deepcopy(slot["claim"]),
                    "proposed": slot["proposed"],
                    "relationship": label if label is not None else "unreviewed",
                    "note": fields.get(slot["prefix"] + "_note", ""),
                }
            )
        records.append(
            {
                "case_id": data["case_label"],
                "candidate_id": data["candidate_id"],
                "citation_alias": data["citation_alias"],
                "relationships": relationships,
                "source_candidate": copy.deepcopy(
                    next(
                        c
                        for c in data["packet"]["candidates"]
                        if c["candidate_id"] == data["candidate_id"]
                    )
                ),
                "search_gaps": copy.deepcopy(
                    data["packet"].get("all_search_gaps", data["packet"]["claim_candidates"])
                ),
                "packet_sha256": data["packet_sha256"],
                "packet_ref": copy.deepcopy(task["data"].get("packet_ref")),
                "upstream_case": copy.deepcopy(data["upstream_case"]),
                "upstream_handoff_sha256": data["upstream_handoff_sha256"],
                "native_task_id": task["id"],
                "native_task_sha256": binding,
                "native_annotation": copy.deepcopy(annotation),
                "annotation_sha256": evidence.digest(annotation),
            }
        )
    return {
        "schema_version": "er_commons.task08e.citation_export.v1",
        "interface_version": VERSION,
        "qualification_only": False,
        "project_id": project_id,
        "reviewer_id": reviewer_id,
        "form_sha256": hashlib.sha256(actual_form.encode()).hexdigest(),
        "export_lineage": export_lineage,
        "native_export_sha256": evidence.digest(exported_tasks),
        "records": records,
        "pending_task_ids": pending,
        "advancing_case_ids": [],
        "advancing_claim_ids": [],
        "allowed_next_stage": None,
        "eligibility": "undecided",
    }
