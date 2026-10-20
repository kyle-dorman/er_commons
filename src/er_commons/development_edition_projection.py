"""Opt-in offline bibliographic projection; never alters frozen G or Task 10 inputs."""

from __future__ import annotations

import copy
import re
from typing import Any

from er_commons.artifact_io import stable_json_sha256
from er_commons.point_grounding import validate_input
from er_commons.target_generation import validate_record

PROJECTION_VERSION = "task11d2.g.edition_projection.v1"
MAPPING_VERSION = "task11d2.bibliographic_mapping.v1"
FIXED_CASES = frozenset({"C041", "C017", "C019", "C014", "C037", "C056"})
_IDENTITY = {
    "candidate_id",
    "candidate_sha256",
    "request_sha256",
    "run_id",
    "case_id",
    "repeat",
    "attempt",
}
_ITEM_FIELDS = {
    "identity",
    "component",
    "point_id",
    "sample_id",
    "payload_sha256",
    "packet",
    "status",
    "group",
    "error_type",
    "citation_ids",
    "unresolved_citation_ids",
    "supported",
}
_LOCATOR_FIELDS = {"unit_type", "unit_id", "extraction_id", "breadcrumb"}


def _exact_keys(value: Any, keys: set[str], name: str) -> None:
    """Reject unknown fields instead of forwarding arbitrary metadata."""
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"Invalid {name} fields")


def _edition(bibliography: dict[str, Any]) -> str:
    """Render explicitly audited bibliographic fields; never parse curation prose."""
    _exact_keys(bibliography, {"year", "document_kind", "appendix"}, "bibliography")
    year, kind, appendix = (bibliography[k] for k in ("year", "document_kind", "appendix"))
    if type(year) is not int or not 1900 <= year <= 2100:
        raise ValueError("Invalid bibliographic year")
    if kind not in ("Draft EIR", "Final EIR"):
        raise ValueError("Invalid bibliographic document kind")
    if appendix is not None and (
        not isinstance(appendix, str) or re.fullmatch(r"[A-Z](?:\.[A-Z0-9]+)*", appendix) is None
    ):
        raise ValueError("Invalid bibliographic appendix")
    return f"{year} {kind}" + (f" Appendix {appendix}" if appendix else "")


def build_mapping(
    target_record: dict[str, Any], annotations: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Bind every fixed-case passage to an explicit bibliography/curation separation.

    Each annotation has bibliography={year, document_kind, appendix} and
    curation_qualification=None or the exact parenthetical qualification. The
    supplied fields must reconstruct the original edition exactly. This validates
    an audited declaration; it does not establish documentary truth or approval.
    """
    validate_record(target_record)
    if target_record["case_id"] not in FIXED_CASES:
        raise ValueError("Only the fixed six cases are permitted")
    passages = target_record["payload"]["passages"]
    ids = [passage["citation_id"] for passage in passages]
    if len(ids) != len(set(ids)) or set(annotations) != set(ids):
        raise ValueError("Mapping must cover every passage exactly once")
    entries = []
    for passage in passages:
        annotation = annotations[passage["citation_id"]]
        _exact_keys(annotation, {"bibliography", "curation_qualification"}, "annotation")
        label = _edition(annotation["bibliography"])
        qualification = annotation["curation_qualification"]
        if qualification is not None and (
            not isinstance(qualification, str) or not qualification.strip()
        ):
            raise ValueError("Invalid curation qualification")
        original = label + (f" ({qualification})" if qualification is not None else "")
        if passage.get("edition") != original:
            raise ValueError("Audited separation differs from original edition")
        entries.append(
            {
                "citation_id": passage["citation_id"],
                "passage_sha256": stable_json_sha256(passage),
                "bibliography": copy.deepcopy(annotation["bibliography"]),
                "curation_qualification": qualification,
            }
        )
    return {
        "schema_version": MAPPING_VERSION,
        "case_id": target_record["case_id"],
        "target_record_sha256": stable_json_sha256(target_record),
        "entries": entries,
    }


def _validated_mapping(target_record: dict[str, Any], mapping: dict[str, Any]) -> dict[str, str]:
    """Rebuild the explicit mapping to verify hashes, membership and all fields."""
    _exact_keys(
        mapping, {"schema_version", "case_id", "target_record_sha256", "entries"}, "mapping"
    )
    if not isinstance(mapping["entries"], list):
        raise ValueError("Invalid mapping entries")
    annotations = {}
    for entry in mapping["entries"]:
        _exact_keys(
            entry,
            {"citation_id", "passage_sha256", "bibliography", "curation_qualification"},
            "mapping entry",
        )
        citation = entry["citation_id"]
        if not isinstance(citation, str) or citation in annotations:
            raise ValueError("Duplicate or invalid mapping citation")
        annotations[citation] = {
            key: entry[key] for key in ("bibliography", "curation_qualification")
        }
    rebuilt = build_mapping(target_record, annotations)
    if mapping != rebuilt:
        raise ValueError("Mapping binding or ordering changed")
    return {entry["citation_id"]: _edition(entry["bibliography"]) for entry in mapping["entries"]}


def _validate_item(item: dict[str, Any], case_id: str) -> None:
    """Require an unmodified legacy G plan item and its exact candidate/sample joins."""
    required = {
        "identity",
        "component",
        "point_id",
        "sample_id",
        "payload_sha256",
        "packet",
        "status",
    }
    if not isinstance(item, dict) or not required <= set(item) <= _ITEM_FIELDS:
        raise ValueError("Invalid legacy item fields")
    identity = item["identity"]
    _exact_keys(identity, _IDENTITY, "candidate identity")
    if identity["case_id"] != case_id or item["component"] != "G" or item["status"] != "not_run":
        raise ValueError("Expected a fixed-case pending G projection")
    if any(type(identity[k]) is not int or identity[k] < 1 for k in ("attempt", "repeat")):
        raise ValueError("Invalid attempt/repeat identity")
    for key in _IDENTITY - {"case_id", "attempt", "repeat"}:
        if (
            not isinstance(identity[key], str)
            or re.fullmatch(r"[0-9a-f]{64}", identity[key]) is None
        ):
            raise ValueError("Invalid identity hash")
    if identity["candidate_id"] != stable_json_sha256(
        {k: v for k, v in identity.items() if k != "candidate_id"}
    ):
        raise ValueError("Candidate identity mismatch")
    if not isinstance(item["point_id"], str) or not item["point_id"].strip():
        raise ValueError("Invalid point identity")
    sample_key = {k: item[k] for k in ("identity", "component", "point_id")}
    if item["sample_id"] != stable_json_sha256(sample_key) or item[
        "payload_sha256"
    ] != stable_json_sha256(item["packet"]):
        raise ValueError("Legacy item hash mismatch")
    validate_input(item["packet"])
    if (
        item.get("supported") is not None
        or item.get("error_type") is not None
        or item.get("unresolved_citation_ids")
    ):
        raise ValueError("Legacy item contains a verdict or failure")
    if "group" in item and item["group"] not in ("supporting_points", "qualifications"):
        raise ValueError("Invalid point group")
    if "citation_ids" in item and (
        not isinstance(item["citation_ids"], (list, tuple))
        or list(item["citation_ids"]) != [s["occurrence_id"] for s in item["packet"]["evidence"]]
    ):
        raise ValueError("Citation ownership mismatch")


def project_item(
    item: dict[str, Any], target_record: dict[str, Any], mapping: dict[str, Any]
) -> dict[str, Any]:
    """Add bibliographic locator edition offline with a distinct evaluation identity.

    No dispatcher imports this adapter. Callers must verify the saved plan/run
    seal before supplying an item: these local hashes do not authenticate that
    point_text came from candidate bytes. Callers retain the original sealed item;
    mappings and curator qualifications remain audit metadata outside the packet.
    """
    editions = _validated_mapping(target_record, mapping)
    _validate_item(item, target_record["case_id"])
    passages = {p["citation_id"]: p for p in target_record["payload"]["passages"]}
    packet = copy.deepcopy(item["packet"])
    if packet["question"] != target_record["payload"]["question"]:
        raise ValueError("Question differs from Task 10")
    for source in packet["evidence"]:
        citation = source["occurrence_id"]
        if citation not in passages:
            raise ValueError("Unmapped citation")
        passage = passages[citation]
        _exact_keys(source["canonical_target"], _LOCATOR_FIELDS, "legacy locator")
        if source["canonical_target"]["breadcrumb"] != [
            {"heading_text": h} for h in passage["heading_path"]
        ]:
            raise ValueError("Source headings differ from Task 10")
        for key in (
            "source_id",
            "title",
            "full_source_text",
            "tables",
            "physical_pages",
            "printed_labels",
        ):
            if source.get(key) != passage[key]:
                raise ValueError(f"Source {key} differs from Task 10")
        for key in ("unit_type", "unit_id", "extraction_id"):
            if (
                not isinstance(source["canonical_target"][key], str)
                or not source["canonical_target"][key].strip()
            ):
                raise ValueError("Invalid source locator")
        source["canonical_target"]["edition"] = editions[citation]
    validate_input(packet, citation_ids=[s["occurrence_id"] for s in item["packet"]["evidence"]])
    projection = {
        "version": PROJECTION_VERSION,
        "mapping_sha256": stable_json_sha256(mapping),
        "original_item_sha256": stable_json_sha256(item),
        "original_sample_id": item["sample_id"],
        "original_payload_sha256": item["payload_sha256"],
        "target_record_sha256": stable_json_sha256(target_record),
    }
    payload_hash = stable_json_sha256(packet)
    sample_id = stable_json_sha256(
        {
            "identity": item["identity"],
            "component": "G",
            "point_id": item["point_id"],
            "projection": projection,
            "payload_sha256": payload_hash,
        }
    )
    return {
        **copy.deepcopy(item),
        "sample_id": sample_id,
        "payload_sha256": payload_hash,
        "packet": packet,
        "projection": projection,
        "status": "not_run",
    }
