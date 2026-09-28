"""Aggregate reviewed citation units without reinterpreting claim relevance or outcomes."""

import copy
import hashlib
import json
from typing import Any

from er_commons.pilot_evidence import PAIR_LABELS

Identity = tuple[str, str, str, str]
_BINDING_FIELDS = (
    "source_id",
    "extraction_id",
    "source_sha256",
    "source_manifest",
    "source_release_version",
    "edition",
    "anchors",
    "citation_unit",
    "quote",
)
_CITATION_FIELDS = _BINDING_FIELDS + (
    "title",
    "source_url",
    "pdf_url",
    "physical_pages",
    "printed_labels",
    "printed_label_provenance",
    "display_segments",
    "limitations",
)


def _extraction_id(candidate: dict[str, Any]) -> str:
    """Recover legacy extraction identity from canonical anchors and reject mixtures."""
    records = [anchor["record"] for anchor in candidate["anchors"] if "record" in anchor]
    extractions = {record["extraction_id"] for record in records}
    documents = {record["document_id"] for record in records}
    supplied = candidate.get("extraction_id")
    if supplied:
        extractions.add(supplied)
    if len(extractions) != 1 or len(documents) > 1:
        raise ValueError("Conflicting or missing anchor extraction/document identity")
    extraction = next(iter(extractions))
    if not isinstance(extraction, str) or not extraction:
        raise ValueError("Missing extraction identity")
    if documents and documents != {f"{extraction}/document/{candidate['source_id']}"}:
        raise ValueError("Anchor document does not match source/extraction identity")
    return extraction


def _identity(candidate: dict[str, Any]) -> Identity:
    """Identify a source unit independently of display labels and retrieval routes."""
    unit = candidate["citation_unit"]
    kind = unit["kind"]
    if kind not in {"section", "table"}:
        raise ValueError(f"Unsupported citation kind: {kind}")
    values = (candidate["source_id"], _extraction_id(candidate), kind, unit[kind + "_id"])
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError("Missing citation identity component")
    return values


def _binding(candidate: dict[str, Any]) -> dict[str, Any]:
    """Compare source structure while allowing the verified display label to vary."""
    binding = {key: candidate.get(key) for key in _BINDING_FIELDS}
    binding["extraction_id"] = _extraction_id(candidate)
    binding["citation_unit"] = {
        key: value for key, value in candidate["citation_unit"].items() if key != "citation_label"
    }
    return binding


def _unique(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    """Reject duplicate identities rather than silently overwrite an input row."""
    result = {row[field]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"Duplicate {field}")
    return result


def aggregate_case_citations(
    packet: dict[str, Any], reviews: list[dict[str, Any]]
) -> dict[str, Any]:
    """Return separate claims/citations and lossless audit for a fully reviewed case.

    Callers validate canonical bindings and apply explicitly authorized dispositions
    before calling. This pure adapter checks exact claim/pair coverage and binding
    consistency; overall outcomes and relevance never establish citation support.
    """
    claims = _unique(packet["claims"], "claim_id")
    candidates = _unique(packet["candidates"], "candidate_id")
    mappings = _unique(packet["claim_candidates"], "claim_id")
    by_claim = _unique(reviews, "claim_id")
    if not claims or claims.keys() != mappings.keys() or claims.keys() != by_claim.keys():
        raise ValueError("Missing or unexpected claim reviews/mappings")
    groups: dict[Identity, list[dict[str, Any]]] = {}
    uses: dict[Identity, list[dict[str, Any]]] = {}
    for candidate in candidates.values():
        identity = _identity(candidate)
        group = groups.setdefault(identity, [])
        if group and _binding(candidate) != _binding(group[0]):
            raise ValueError(f"Conflicting source/anchor bindings: {identity}")
        group.append(candidate)
        uses.setdefault(identity, [])
    for claim_id in sorted(claims):
        review = by_claim[claim_id]
        detail = review["claim_review"]
        if review["case_id"] != packet["case_id"] or detail["claim_id"] != claim_id:
            raise ValueError("Review case/claim binding mismatch")
        mapping = mappings[claim_id]
        expected = mapping["candidate_ids"] + mapping.get("overflow_candidate_ids", [])
        if len(expected) != len(set(expected)) or not set(expected) <= candidates.keys():
            raise ValueError("Duplicate or unknown candidate in claim mapping")
        pairs = _unique(detail["pairs"], "candidate_id")
        if pairs.keys() != set(expected):
            raise ValueError("Missing or unknown candidate judgments")
        for candidate_id, pair in sorted(pairs.items()):
            if pair["relationship"] not in PAIR_LABELS:
                raise ValueError("Unknown evidence relationship")
            identity = _identity(candidates[candidate_id])
            uses[identity].append(
                {
                    "claim_id": claim_id,
                    "task_id": review.get("task_id"),
                    "annotation_id": review.get("annotation_id"),
                    "pair": copy.deepcopy(pair),
                }
            )
    citations = []
    decisions = []
    for identity, group in sorted(groups.items()):
        relationships = {use["pair"]["relationship"] for use in uses[identity]}
        if "partial" in relationships and "supports" not in relationships:
            raise ValueError(f"Partial-only citation requires explicit disposition: {identity}")
        level = (
            "support"
            if "supports" in relationships
            else "context"
            if "context" in relationships
            else None
        )
        citation_id = (
            "citation07d-"
            + hashlib.sha256(
                json.dumps(identity, ensure_ascii=False, separators=(",", ":")).encode()
            ).hexdigest()
        )
        # A deterministic presentation represents equivalent candidates; every
        # original presentation and retrieval record remains intact in the audit.
        representative = min(group, key=lambda candidate: candidate["candidate_id"])
        if level:
            citations.append(
                {
                    "citation_id": citation_id,
                    "level": level,
                    "extraction_id": identity[1],
                    **{
                        key: copy.deepcopy(representative[key])
                        for key in _CITATION_FIELDS
                        if key in representative and key != "extraction_id"
                    },
                }
            )
        decisions.append(
            {
                "semantic_identity": list(identity),
                "citation_id": citation_id if level else None,
                "level": level,
                "candidate_ids": sorted(c["candidate_id"] for c in group),
                "judgments": uses[identity],
                "disposition": "included" if level else "excluded_no_approved_support_or_context",
            }
        )
    return {
        "schema_version": "er_commons.task07d.case_citations.v1",
        "case_id": packet["case_id"],
        "claims": [copy.deepcopy(claims[key]) for key in sorted(claims)],
        "citations": citations,
        "audit": {
            "reviews": [copy.deepcopy(by_claim[key]) for key in sorted(by_claim)],
            "candidates": [copy.deepcopy(candidates[key]) for key in sorted(candidates)],
            "claim_candidates": [copy.deepcopy(mappings[key]) for key in sorted(mappings)],
            "citation_decisions": decisions,
        },
    }
