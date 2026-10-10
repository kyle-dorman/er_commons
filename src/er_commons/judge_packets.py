"""Deterministic judge inputs; no prompts, scoring, retrieval or model execution.

Inputs are verified complete source units from the existing citation assemblers.
Only ``payload`` crosses the model boundary; raw identities stay in mappings.
"""

from __future__ import annotations

import copy
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from er_commons.artifact_io import stable_json_sha256
from er_commons.judge_qualification_packets import project_answer, project_target

SCHEMA_VERSION = "task09c.judge_packet.v1"
CONTEXT_TOKENS = 49152
OUTPUT_RESERVE = 1500


class PacketInputError(ValueError):
    """A malformed answer or inconsistent source input, never a rubric score."""


class SourceUnavailableError(PacketInputError):
    """A known source is incomplete; do not mislabel it an invalid citation."""


class StrictModel(BaseModel):
    """Reject unprojected metadata at every model-visible object boundary."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Point(StrictModel):
    """Exact assertion and ordered links, including repeated/joint citations."""

    point_id: str
    text: str
    citation_ids: list[str]
    applies_to: list[str] = Field(default_factory=list)


class Locator(StrictModel):
    """Candidate-provided excerpts are assertions, not replacement evidence."""

    occurrence_id: str
    excerpt: str


class Answer(StrictModel):
    """Preserve every substantive field even when status declares abstention."""

    status: Literal["answered", "abstained"]
    conclusion: Point
    supporting_points: list[Point]
    qualifications: list[Point]
    optional_context: list[Point]
    citation_locators: list[Locator] = Field(default_factory=list)


class Heading(StrictModel):
    """A source heading without its review/provenance envelope."""

    heading_text: str


class Figure(StrictModel):
    """Retain the source locator and inherited text-only interpretation limit."""

    record_id: str
    interpretation: str


class Target(StrictModel):
    """Canonical readable locators, never human evidence classifications."""

    unit_id: str
    kind: str | None = None
    unit_type: str | None = None
    citation_label: str | None = None
    edition: str | None = None
    pages: list[int] | None = None
    breadcrumb: list[Heading] | None = None
    figure_refs: list[Figure] | None = None


class Cell(StrictModel):
    """Grid content and positioning without nested extraction receipts."""

    text: str
    row_index: int
    column_index: int
    row_span: int | None = None
    column_span: int | None = None
    is_header: bool | None = None
    column_header: bool | None = None
    row_header: bool | None = None


class Table(StrictModel):
    """Complete ordered cells and continuation identities; notes remain in full text."""

    cells: list[Cell]
    id: str | None = None
    shape: list[int] | None = None
    caption: str | None = None
    caption_block_ids: list[str] | None = None
    num_rows: int | None = None
    num_cols: int | None = None
    row_count: int | None = None
    column_count: int | None = None
    table_family_id: str | None = None
    continuation_of: str | None = None


class ResolvedEvidence(StrictModel):
    """An actual complete source unit attached to a neutral citation ID."""

    citation_id: str
    resolution: Literal["resolved"]
    source_id: str
    full_source_text: str = Field(min_length=1)
    tables: list[Table]
    title: str | None = None
    edition: str | None = None
    canonical_target: Target | None = None
    physical_pages: list[int] | None = None
    printed_labels: list[str] | None = None


class UnresolvedEvidence(StrictModel):
    """An explicit unknown candidate citation; raw token is retained outside the payload."""

    citation_id: str
    resolution: Literal["unresolved"]


class GroundingPayload(StrictModel):
    """Reference-blind input for an independent grounding call."""

    question: str
    answer: Answer
    evidence: list[ResolvedEvidence | UnresolvedEvidence]


class AdequacyPayload(GroundingPayload):
    """Independent reference-aware input with actual candidate evidence retained."""

    reference_answer: Answer


def points(answer: dict[str, Any]) -> list[dict[str, Any]]:
    """Return every assertion in its saved order, without semantic interpretation."""
    return [
        answer["conclusion"],
        *answer["supporting_points"],
        *answer["qualifications"],
        *answer["optional_context"],
    ]


def citation_ids(answer: dict[str, Any]) -> list[str]:
    """Collect first appearances without dropping repeated links from the answer itself."""
    return list(
        dict.fromkeys(
            [
                *(c for point in points(answer) for c in point["citation_ids"]),
                *(row["occurrence_id"] for row in answer.get("citation_locators", [])),
            ]
        )
    )


def _source_content(source: dict[str, Any]) -> dict[str, Any]:
    """Keep complete text and cell semantics; discard review metadata recursively."""
    if (
        not isinstance(source.get("full_source_text"), str)
        or not source["full_source_text"].strip()
    ):
        raise SourceUnavailableError("Known source lacks complete source text")
    if not isinstance(source.get("tables"), list):
        raise SourceUnavailableError("Known source lacks its table inventory")
    row = {
        key: copy.deepcopy(source[key])
        for key in ResolvedEvidence.model_fields
        if key in source and key not in {"citation_id", "resolution", "tables", "canonical_target"}
    }
    row["tables"] = []
    for table in source["tables"]:
        if not isinstance(table.get("cells"), list) or not table["cells"]:
            raise SourceUnavailableError("Known table lacks its complete cells")
        projected = {
            key: copy.deepcopy(table[key])
            for key in Table.model_fields
            if key in table and key != "cells"
        }
        projected["cells"] = [
            {key: copy.deepcopy(cell[key]) for key in Cell.model_fields if key in cell}
            for cell in table["cells"]
        ]
        row["tables"].append(projected)
    target = source.get("canonical_target")
    if target is not None:
        if target.get("unit_type") == "table" and not row["tables"]:
            raise SourceUnavailableError("Known table unit lacks its table records")
        row["canonical_target"] = project_target(target)
    return row


def _project_source(source: dict[str, Any]) -> dict[str, Any]:
    """Report malformed known evidence as an infrastructure error with its locator."""
    try:
        content = _source_content(source)
        ResolvedEvidence.model_validate({"citation_id": "S1", "resolution": "resolved", **content})
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        raise SourceUnavailableError(
            f"Invalid source {source['occurrence_id']!r}: {error}"
        ) from error
    return content


def _saved_answer(answer: Any, role: str) -> dict[str, Any]:
    """Validate raw substantive types before iteration or ID anonymization.

    Extra metadata is ignored recursively at intake, while serialization remains
    strict. Excluding unset defaults preserves the saved answer's exact shape.
    """
    try:
        return Answer.model_validate(answer, extra="ignore").model_dump(exclude_unset=True)
    except ValueError as error:
        raise PacketInputError(f"Invalid saved {role} answer: {error}") from error


def _source_inventory(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Require an unambiguous source inventory before resolving any candidate ID."""
    rows = packet.get("sources")
    if not isinstance(rows, list):
        raise SourceUnavailableError("Missing source occurrence inventory")
    result: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get("occurrence_id"), str):
            raise SourceUnavailableError(f"Invalid source occurrence at inventory index {index}")
        identity = row["occurrence_id"]
        if identity in result:
            raise PacketInputError(f"Duplicate source occurrence ID: {identity!r}")
        result[identity] = row
    return result


def _project_answer(answer: dict[str, Any], citations: dict[str, str]) -> dict[str, Any]:
    """Use 09B's exact text/attachment projection and reject malformed point links."""
    try:
        result = project_answer(answer, citations)
        Answer.model_validate(result)
    except (KeyError, TypeError, ValueError) as error:
        raise PacketInputError(f"Invalid saved answer: {error}") from error
    return result


def validate_payload(payload: dict[str, Any], dimension: str) -> None:
    """Check the exact serialized model boundary, including nested forbidden fields."""
    model: type[GroundingPayload]
    if dimension == "grounding":
        model = GroundingPayload
    elif dimension == "adequacy":
        model = AdequacyPayload
    else:
        raise PacketInputError("Unknown judge dimension")
    try:
        model.model_validate(payload)
    except ValueError as error:
        raise PacketInputError(f"Invalid {dimension} payload: {error}") from error
    ids = [source["citation_id"] for source in payload["evidence"]]
    if len(ids) != len(set(ids)):
        raise PacketInputError("Duplicate projected citation ID")
    if dimension == "grounding" and set(ids) != set(citation_ids(payload["answer"])):
        raise PacketInputError("Grounding evidence must contain only actual candidate citations")
    for key in ("answer", "reference_answer"):
        if key not in payload:
            continue
        answer = payload[key]
        point_ids = [p["point_id"] for p in points(answer)]
        if len(point_ids) != len(set(point_ids)) or not set(citation_ids(answer)) <= set(ids):
            raise PacketInputError("Inconsistent projected point/citation links")
        if any(not set(p.get("applies_to", [])) <= set(point_ids) for p in points(answer)):
            raise PacketInputError("Dangling qualification attachment")


def build_packet(packet: dict[str, Any], answer: dict[str, Any], dimension: str) -> dict[str, Any]:
    """Project verified assembled inputs, preserving wrong and unknown citations as given.

    ``sources`` is a verified complete occurrence inventory, not search results.
    The publisher verifies its seal before this pure function is called. Future
    callers must supply complete assembled units from the same maintained boundary.
    """
    if dimension not in {"grounding", "adequacy"}:
        raise PacketInputError("Unknown judge dimension")
    answer = _saved_answer(answer, "candidate")
    candidate_ids = citation_ids(answer)
    reference = (
        _saved_answer(packet.get("reference_answer"), "reference")
        if dimension == "adequacy"
        else None
    )
    sources = _source_inventory(packet)
    if reference is not None and not set(citation_ids(reference)) <= sources.keys():
        raise SourceUnavailableError("Approved reference citation missing from source inventory")
    # Candidate-first order is stable and does not encode gold roles or synthetic labels.
    selected_ids = list(dict.fromkeys(candidate_ids + (list(sources) if reference else [])))
    citations: dict[str, str] = {}
    evidence: list[dict[str, Any]] = []
    canonical: dict[str, str] = {}
    for raw_id in selected_ids:
        source = sources.get(raw_id)
        if source is None:
            neutral = f"S{len(evidence) + 1}"
            evidence.append({"citation_id": neutral, "resolution": "unresolved"})
        else:
            row = _project_source(source)
            identity = stable_json_sha256(row)
            neutral = canonical.get(identity, f"S{len(evidence) + 1}")
            if identity not in canonical:
                evidence.append({"citation_id": neutral, "resolution": "resolved", **row})
                canonical[identity] = neutral
        citations[raw_id] = neutral
    payload = {
        "question": packet["question"],
        "answer": _project_answer(answer, citations),
        "evidence": evidence,
    }
    if reference is not None:
        payload["reference_answer"] = _project_answer(reference, citations)
    content = serialize_payload(payload, dimension)
    return {
        "schema_version": SCHEMA_VERSION,
        "dimension": dimension,
        "payload": payload,
        "diagnostics": {
            "status": "constructed",
            "context_status": "context_unverified",
            "context_tokens": CONTEXT_TOKENS,
            "output_reserve": OUTPUT_RESERVE,
            "payload_utf8_bytes": len(content.encode()),
            "payload_sha256": stable_json_sha256(payload),
            "unresolved_citations": [
                row["citation_id"] for row in evidence if row["resolution"] == "unresolved"
            ],
            "evidence_policy": "complete_assembled_units_no_truncation_or_repair",
            "inherited_limitations": copy.deepcopy(packet.get("limitations", [])),
        },
        "mappings": {
            "citations": citations,
            "candidate_points": {p["point_id"]: f"P{i + 1}" for i, p in enumerate(points(answer))},
            "reference_points": (
                {p["point_id"]: f"P{i + 1}" for i, p in enumerate(points(reference))}
                if reference is not None
                else {}
            ),
        },
    }


def serialize_payload(payload: dict[str, Any], dimension: str) -> str:
    """Serialize only validated model input; never envelope metadata or raw ID mappings."""
    validate_payload(payload, dimension)
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def payload_schema(dimension: str) -> dict[str, Any]:
    """Expose the versioned strict schema without maintaining a second hand-written copy."""
    if dimension not in {"grounding", "adequacy"}:
        raise PacketInputError("Unknown judge dimension")
    model = GroundingPayload if dimension == "grounding" else AdequacyPayload
    return {"$id": f"{SCHEMA_VERSION}.{dimension}", **model.model_json_schema()}
