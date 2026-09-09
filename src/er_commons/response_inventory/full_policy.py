"""Deterministic Task 05D review and structural-accounting policy."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from er_commons.artifact_io import canonical_json_sha256
from er_commons.response_inventory.observations import PageObservation
from er_commons.response_inventory.task05d_policy import (
    TASK05D_ALLOWED_WARNING_CODES,
    TASK05D_RANGE,
)

type JsonObject = dict[str, Any]

TASK05D_CONTROL_PAGES: Final[frozenset[int]] = frozenset(
    {
        1,
        2,
        4,
        38,
        39,
        83,
        84,
        *range(368, 373),
        *range(551, 556),
        *range(668, 672),
        721,
        722,
        TASK05D_RANGE[1],
    }
)

_STRUCTURAL_DIAGNOSTIC_CODES: Final = frozenset(
    {
        "page_unclassified",
        "marker_ambiguous",
        "span_gap",
        *TASK05D_ALLOWED_WARNING_CODES,
        "unit_boundary_ambiguous",
        "geometry_text_mismatch",
    }
)
_TRAILING_NUMBER_RE: Final = re.compile(r"^(?P<prefix>.*?)(?P<number>[0-9]+)$")


@dataclass(frozen=True)
class StructuralSignatureEvidence:
    """Observation-derived booleans used by the shared signature builder."""

    title: bool
    revision: bool
    blank: bool
    geometry_valid: bool


def build_structural_signature(
    record: Mapping[str, Any],
    marker_pairs: Sequence[str],
    submission_kinds: Sequence[str],
    *,
    continuation_in: bool,
    continuation_out: bool,
    evidence: StructuralSignatureEvidence,
) -> JsonObject:
    """Build the canonical structural signature for pilot and fresh evidence."""
    state = str(record["page_state"])
    return {
        "primary_page_state": state,
        "marker_pairs": sorted(marker_pairs),
        "submission_kinds": sorted(submission_kinds),
        "continuation_in": continuation_in,
        "continuation_out": continuation_out,
        "title": evidence.title,
        "revision": evidence.revision,
        "blank": evidence.blank,
        "geometry_valid": evidence.geometry_valid,
        "layout": state == "layout_exception",
    }


def pilot_signature_evidence(
    record: Mapping[str, Any], qualification_row: Mapping[str, Any], *, ambiguous: bool
) -> StructuralSignatureEvidence:
    """Adapt pilot qualification evidence without inventing PDF observations."""
    state = str(record["page_state"])
    low_score = float(qualification_row["pdfium_poppler_token_multiset_f1"]) < 0.98
    explained = low_score or state in {"layout_exception", "revision_markup"} or ambiguous
    return StructuralSignatureEvidence(
        title=state == "layout_exception",
        revision=state == "revision_markup",
        blank=not str(record["raw_text"]).strip(),
        geometry_valid=not (qualification_row.get("flagged_for_review") is True and not explained),
    )


def lower_median[T](items: Sequence[T]) -> T:
    """Return the contract's lower median from an already sorted sequence."""
    if not items:
        raise ValueError("lower median requires at least one item")
    return items[(len(items) - 1) // 2]


def build_structural_accounting(records: Sequence[JsonObject]) -> JsonObject:
    """Derive exact structural counts and conservative label-sequence findings."""
    pages = _records(records, "page")
    markers = _records(records, "marker_candidate")
    units = _records(records, "source_unit")
    diagnostics = _records(records, "diagnostic")
    label_findings = _label_findings(units, records)
    suspected = [item for item in label_findings if item["finding_kind"] == "sequence_gap"]
    page_by_id = {str(record["page_id"]): int(record["physical_page"]) for record in pages}
    by_id = _records_by_id(records)
    diagnostic_instances = [
        {
            "diagnostic_id": row["diagnostic_id"],
            "code": row["code"],
            "subject_ids": row["subject_ids"],
            "evidence_ids": row["evidence_ids"],
            "physical_pages": sorted(
                _resolve_subject_pages(
                    [*row["subject_ids"], *row["evidence_ids"]], by_id, page_by_id
                )
            ),
        }
        for row in sorted(diagnostics, key=lambda item: str(item["diagnostic_id"]))
    ]
    report: JsonObject = {
        "schema_version": "er_commons.response_inventory.structural_accounting.v2",
        "primary_page_states": dict(sorted(Counter(row["page_state"] for row in pages).items())),
        "marker_dispositions": _nested_counts(markers, "marker_kind", "disposition"),
        "unit_kinds": dict(sorted(Counter(row["unit_kind"] for row in units).items())),
        "diagnostic_codes": dict(sorted(Counter(row["code"] for row in diagnostics).items())),
        "diagnostic_instances": diagnostic_instances,
        "label_findings": label_findings,
        "suspected_omissions": suspected,
        "counts": {
            "pages": len(pages),
            "markers": len(markers),
            "units": len(units),
            "diagnostics": len(diagnostics),
            "label_findings": len(label_findings),
            "suspected_omissions": len(suspected),
        },
    }
    report["report_digest"] = canonical_json_sha256(report)
    return report


def select_full_review_population(
    qualification: JsonObject,
    records: Sequence[JsonObject],
    observations: Sequence[PageObservation],
    *,
    accepted_signature_digests: frozenset[str],
) -> JsonObject:
    """Freeze the exact deterministic 05D review population and its reasons."""
    page_rows = _qualification_rows(qualification)
    pages = {int(row["physical_page"]): row for row in _records(records, "page")}
    observation_by_page = {item.physical_page: item for item in observations}
    if set(page_rows) != set(pages) or set(page_rows) != set(observation_by_page):
        raise ValueError(
            "review selection requires identical page, observation, and report coverage"
        )

    reasons: dict[int, set[str]] = defaultdict(set)
    for page, row in page_rows.items():
        for reason in row.get("review_reasons", []):
            if not isinstance(reason, str) or not reason:
                raise ValueError("qualification review reasons must be nonempty strings")
            reasons[page].add(reason)
    for page in TASK05D_CONTROL_PAGES:
        reasons[page].add("fixed_high_risk_or_boundary_control")

    _select_page_state_sample(reasons, pages)
    _select_general_response_endpoints(reasons, records, pages)
    _select_continuation_sample(reasons, records, pages)
    _select_record_triggers(reasons, records, pages)
    signatures = _select_signature_triggers(
        reasons,
        records,
        observation_by_page,
        pages,
        accepted_signature_digests,
    )
    structural = build_structural_accounting(records)
    for finding in structural["label_findings"]:
        for page in finding["physical_pages"]:
            reasons[int(page)].add(f"label_{finding['finding_kind']}")

    selected_rows = []
    for page, row in sorted(page_rows.items()):
        row_reasons = sorted(reasons.get(page, set()))
        row["review_reasons"] = row_reasons
        row["fixed_review_page"] = bool(row_reasons)
        row["flagged_for_review"] = bool(row_reasons)
        selected_rows.append(
            {
                "physical_page": page,
                "page_id": pages[page]["page_id"],
                "reasons": row_reasons,
            }
        )
    population = [row for row in selected_rows if row["reasons"]]
    qualification["review_page_count"] = len(population)
    qualification["review_population"] = population
    qualification["review_population_digest"] = canonical_json_sha256(population)
    qualification["structural_signatures"] = signatures
    qualification["structural_accounting_digest"] = structural["report_digest"]
    return qualification


def accepted_signature_digests_from_pilot(
    records: Sequence[JsonObject], qualification: JsonObject
) -> frozenset[str]:
    """Reconstruct the accepted pilot signature baseline without PDF observations."""
    pages = {int(row["physical_page"]): row for row in _records(records, "page")}
    page_rows = _qualification_rows(qualification)
    markers_by_page: dict[str, list[JsonObject]] = defaultdict(list)
    submissions_by_page: dict[str, list[JsonObject]] = defaultdict(list)
    incoming: set[str] = set()
    outgoing: set[str] = set()
    for marker in _records(records, "marker_candidate"):
        markers_by_page[str(marker["page_id"])].append(marker)
    spans = {str(row["span_id"]): row for row in _records(records, "source_span")}
    for submission in _records(records, "submission"):
        span = spans[str(submission["opener_span_id"])]
        submissions_by_page[str(span["fragments"][0]["page_id"])].append(submission)
    for continuation in _records(records, "page_continuation"):
        outgoing.add(str(continuation["from_page_id"]))
        incoming.add(str(continuation["to_page_id"]))
    ambiguous_pages = {
        str(marker["page_id"])
        for marker in _records(records, "marker_candidate")
        if marker["disposition"] == "needs_review"
    }
    digests: set[str] = set()
    for page, record in pages.items():
        row = page_rows[page]
        page_id = str(record["page_id"])
        signature = build_structural_signature(
            record,
            [f"{item['marker_kind']}:{item['disposition']}" for item in markers_by_page[page_id]],
            [str(item["submission_kind"]) for item in submissions_by_page[page_id]],
            continuation_in=page_id in incoming,
            continuation_out=page_id in outgoing,
            evidence=pilot_signature_evidence(record, row, ambiguous=page_id in ambiguous_pages),
        )
        digests.add(canonical_json_sha256(signature))
    return frozenset(digests)


def _select_page_state_sample(
    reasons: dict[int, set[str]], pages: Mapping[int, JsonObject]
) -> None:
    grouped: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for page, record in pages.items():
        grouped[str(record["page_state"])].append((page, str(record["page_id"])))
    for state, items in grouped.items():
        ordered = sorted(items)
        for page, _identity in {ordered[0], lower_median(ordered), ordered[-1]}:
            reasons[page].add(f"page_state_sample:{state}")


def _select_general_response_endpoints(
    reasons: dict[int, set[str]], records: Sequence[JsonObject], pages: Mapping[int, JsonObject]
) -> None:
    page_by_id = {str(record["page_id"]): page for page, record in pages.items()}
    spans = {str(row["span_id"]): row for row in _records(records, "source_span")}
    for unit in _records(records, "source_unit"):
        if unit["unit_kind"] != "general_response":
            continue
        unit_pages = sorted(
            {
                page_by_id[str(fragment["page_id"])]
                for span_id in unit["span_ids"]
                for fragment in spans[str(span_id)]["fragments"]
            }
        )
        if not unit_pages:
            raise ValueError("General Response unit has no resolvable page")
        label = str(unit["official_label"]).casefold().replace(" ", "_")
        reasons[unit_pages[0]].add(f"general_response_start:{label}")
        reasons[unit_pages[-1]].add(f"general_response_end:{label}")


def _select_continuation_sample(
    reasons: dict[int, set[str]], records: Sequence[JsonObject], pages: Mapping[int, JsonObject]
) -> None:
    page_by_id = {str(record["page_id"]): page for page, record in pages.items()}
    continuations = sorted(
        (
            page_by_id[str(row["from_page_id"])],
            page_by_id[str(row["to_page_id"])],
            str(row["continuation_id"]),
        )
        for row in _records(records, "page_continuation")
    )
    if not continuations:
        return
    for left, right, _identity in {
        continuations[0],
        lower_median(continuations),
        continuations[-1],
    }:
        reasons[left].add("cross_page_continuation_sample")
        reasons[right].add("cross_page_continuation_sample")


def _select_record_triggers(
    reasons: dict[int, set[str]], records: Sequence[JsonObject], pages: Mapping[int, JsonObject]
) -> None:
    page_by_id = {str(record["page_id"]): page for page, record in pages.items()}
    by_id = _records_by_id(records)
    for page, record in pages.items():
        if record["page_state"] in {"mixed_markers", "layout_exception"}:
            reasons[page].add(f"page_state_trigger:{record['page_state']}")
    for marker in _records(records, "marker_candidate"):
        if marker["disposition"] == "needs_review":
            reasons[page_by_id[str(marker["page_id"])]].add("ambiguous_marker")
    for diagnostic in _records(records, "diagnostic"):
        if diagnostic["code"] not in _STRUCTURAL_DIAGNOSTIC_CODES:
            continue
        implicated = _resolve_subject_pages(
            [*diagnostic["subject_ids"], *diagnostic["evidence_ids"]], by_id, page_by_id
        )
        if not implicated:
            raise ValueError("structural diagnostic does not resolve to a physical page")
        for page in implicated:
            reasons[page].add(f"structural_diagnostic:{diagnostic['code']}")


def _select_signature_triggers(
    reasons: dict[int, set[str]],
    records: Sequence[JsonObject],
    observations: Mapping[int, PageObservation],
    pages: Mapping[int, JsonObject],
    accepted: frozenset[str],
) -> list[JsonObject]:
    markers_by_page: dict[str, list[JsonObject]] = defaultdict(list)
    submissions_by_page: dict[str, list[JsonObject]] = defaultdict(list)
    incoming: set[str] = set()
    outgoing: set[str] = set()
    for marker in _records(records, "marker_candidate"):
        markers_by_page[str(marker["page_id"])].append(marker)
    spans = {str(row["span_id"]): row for row in _records(records, "source_span")}
    for submission in _records(records, "submission"):
        span = spans[str(submission["opener_span_id"])]
        submissions_by_page[str(span["fragments"][0]["page_id"])].append(submission)
    for continuation in _records(records, "page_continuation"):
        outgoing.add(str(continuation["from_page_id"]))
        incoming.add(str(continuation["to_page_id"]))

    signatures = []
    for page, record in sorted(pages.items()):
        page_id = str(record["page_id"])
        observation = observations[page]
        signature = build_structural_signature(
            record,
            [f"{row['marker_kind']}:{row['disposition']}" for row in markers_by_page[page_id]],
            [str(row["submission_kind"]) for row in submissions_by_page[page_id]],
            continuation_in=page_id in incoming,
            continuation_out=page_id in outgoing,
            evidence=StructuralSignatureEvidence(
                title=observation.title_page,
                revision=observation.revision_markup,
                blank=not observation.raw_text.strip(),
                geometry_valid=_geometry_is_valid(observation),
            ),
        )
        digest = canonical_json_sha256(signature)
        if digest not in accepted:
            reasons[page].add("new_structural_signature")
        signatures.append(
            {"physical_page": page, "signature": signature, "signature_digest": digest}
        )
    return signatures


def _geometry_is_valid(observation: PageObservation) -> bool:
    for line in observation.lines:
        text = observation.raw_text[line.text_start : line.text_end]
        if not text.strip():
            continue
        if (
            line.character_slot_start is None
            or line.character_slot_end is None
            or line.character_slot_start < 0
            or line.character_slot_end <= line.character_slot_start
            or line.character_slot_end > observation.character_slot_count
        ):
            return False
        left, bottom, right, top = line.bbox
        if not (
            all(math.isfinite(value) for value in line.bbox)
            and 0 <= left <= right <= observation.width_points
            and 0 <= bottom <= top <= observation.height_points
        ):
            return False
    return True


def _label_findings(units: Sequence[JsonObject], records: Sequence[JsonObject]) -> list[JsonObject]:
    pages = {str(row["page_id"]): int(row["physical_page"]) for row in _records(records, "page")}
    spans = {str(row["span_id"]): row for row in _records(records, "source_span")}
    anchors: dict[str, list[int]] = {}
    grouped: dict[tuple[str, str], list[tuple[int, str, int]]] = defaultdict(list)
    for unit in units:
        unit_id = str(unit["unit_id"])
        unit_pages = sorted(
            pages[str(fragment["page_id"])]
            for span_id in unit["span_ids"]
            for fragment in spans[str(span_id)]["fragments"]
        )
        anchors[unit_id] = unit_pages
        normalized = " ".join(str(unit["official_label"]).casefold().split())
        match = _TRAILING_NUMBER_RE.fullmatch(normalized)
        if match is not None:
            grouped[(str(unit["unit_kind"]), match.group("prefix"))].append(
                (int(match.group("number")), unit_id, unit_pages[0])
            )

    findings: list[JsonObject] = []
    by_label: dict[tuple[str, str], list[str]] = defaultdict(list)
    for unit in units:
        key = (str(unit["unit_kind"]), " ".join(str(unit["official_label"]).casefold().split()))
        by_label[key].append(str(unit["unit_id"]))
    for (kind, label), unit_ids in sorted(by_label.items()):
        if len(unit_ids) > 1:
            findings.append(
                {
                    "finding_kind": "duplicate_label",
                    "unit_kind": kind,
                    "label_key": label,
                    "unit_ids": sorted(unit_ids),
                    "physical_pages": sorted({page for uid in unit_ids for page in anchors[uid]}),
                    "missing_numbers": [],
                }
            )
    for (kind, prefix), entries in sorted(grouped.items()):
        ordered = sorted(entries)
        numbers = sorted({number for number, _unit_id, _page in ordered})
        if len(numbers) < 2:
            continue
        missing = sorted(set(range(numbers[0], numbers[-1] + 1)) - set(numbers))
        if missing:
            findings.append(
                {
                    "finding_kind": "sequence_gap",
                    "unit_kind": kind,
                    "label_key": prefix,
                    "unit_ids": sorted(unit_id for _number, unit_id, _page in ordered),
                    "physical_pages": sorted({page for _number, _unit_id, page in ordered}),
                    "missing_numbers": missing,
                }
            )
    return sorted(
        findings,
        key=lambda row: (row["finding_kind"], row["unit_kind"], row["label_key"]),
    )


def _resolve_subject_pages(
    subject_ids: Sequence[str], by_id: Mapping[str, JsonObject], page_by_id: Mapping[str, int]
) -> set[int]:
    pending = list(subject_ids)
    seen: set[str] = set()
    found: set[int] = set()
    while pending:
        identity = pending.pop()
        if identity in seen:
            continue
        seen.add(identity)
        if identity in page_by_id:
            found.add(page_by_id[identity])
            continue
        record = by_id.get(identity)
        if record is None:
            continue
        for field in ("page_id", "from_page_id", "to_page_id", "start_marker_id"):
            value = record.get(field)
            if isinstance(value, str):
                pending.append(value)
        for field in ("span_ids", "evidence_ids"):
            value = record.get(field)
            if isinstance(value, list):
                pending.extend(str(item) for item in value)
        fragments = record.get("fragments")
        if isinstance(fragments, list):
            pending.extend(str(item["page_id"]) for item in fragments if isinstance(item, dict))
    return found


def _records(records: Sequence[JsonObject], record_type: str) -> list[JsonObject]:
    return [record for record in records if record.get("record_type") == record_type]


def _records_by_id(records: Sequence[JsonObject]) -> dict[str, JsonObject]:
    result: dict[str, JsonObject] = {}
    identity_fields = {
        "activity": "activity_id",
        "page": "page_id",
        "page_continuation": "continuation_id",
        "marker_candidate": "marker_id",
        "source_span": "span_id",
        "commenter": "commenter_id",
        "submission": "submission_id",
        "source_unit": "unit_id",
        "membership_claim": "membership_id",
        "reference_mention": "mention_id",
        "diagnostic": "diagnostic_id",
        "source_placement_exception": "exception_id",
    }
    for record in records:
        identity = record.get(identity_fields.get(str(record.get("record_type")), ""))
        if isinstance(identity, str):
            result[identity] = record
    return result


def _qualification_rows(report: JsonObject) -> dict[int, JsonObject]:
    rows = report.get("pages")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("qualification report lacks page rows")
    result = {int(row["physical_page"]): row for row in rows}
    if len(result) != len(rows):
        raise ValueError("qualification report contains duplicate pages")
    return result


def _nested_counts(records: Sequence[JsonObject], left: str, right: str) -> JsonObject:
    counts = Counter((str(row[left]), str(row[right])) for row in records)
    nested: dict[str, dict[str, int]] = defaultdict(dict)
    for (left_value, right_value), count in sorted(counts.items()):
        nested[left_value][right_value] = count
    return dict(nested)


__all__ = [
    "StructuralSignatureEvidence",
    "TASK05D_CONTROL_PAGES",
    "TASK05D_RANGE",
    "accepted_signature_digests_from_pilot",
    "build_structural_accounting",
    "build_structural_signature",
    "lower_median",
    "pilot_signature_evidence",
    "select_full_review_population",
]
