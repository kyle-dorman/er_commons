"""Offline, opt-in Task 11D.6 context envelopes; legacy readers stay unchanged.

Opaque source identifiers and verbatim evidence are preserved. Human-readable
locators are explicitly mapped, with original metadata retained only in provenance.
"""

from __future__ import annotations

import copy
import json
import re
from typing import Any, cast

from er_commons import adequacy_binary, no_answer, point_grounding
from er_commons.artifact_io import stable_json_sha256
from er_commons.target_generation import validate_record

VERSION = "task11d6.context.v1"
MAP_VERSION = "task11d6.locators.v1"
IDENTITY_FIELDS = {
    "candidate_id",
    "candidate_sha256",
    "request_sha256",
    "run_id",
    "case_id",
    "repeat",
    "attempt",
}
ITEM_FIELDS = {
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


def neutral_question(text: str) -> str:
    """Apply the shared mechanical edition-name substitution to authored questions."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Question must be nonblank")
    return re.sub(
        r"(?i)\b(?:(?:(?:19|20)\d{2})\s+)?"
        r"(?:Draft\s+(?:Environmental\s+Impact\s+Report|DEIR|FEIR|EIR)|"
        r"Final\s+(?:Environmental\s+Impact\s+Report|DEIR|FEIR|EIR)|DEIR|FEIR)\b",
        "EIR",
        text,
    )


def _keys(value: Any, expected: set[str], name: str) -> None:
    """Fail closed on unknown fields at the authored metadata boundary."""
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"Unexpected {name} fields")


def _locator(value: dict[str, Any]) -> None:
    """Require explicit document/section labels without editorial edition framing."""
    _keys(value, {"document", "title", "heading_path"}, "neutral locator")
    if not isinstance(value["document"], str) or not re.fullmatch(
        r"EIR main document|EIR Appendix [A-Z](?:\.\d+)?", value["document"]
    ):
        raise ValueError("Expected main document or named appendix")
    if not isinstance(value["heading_path"], list) or not value["heading_path"]:
        raise ValueError("Section information is required")
    for text in [value["title"], *value["heading_path"]]:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Locator text must be nonblank")
        if re.search(
            r"\b(?:Draft|Final)\s+EIR\b|\b[DF]EIR\b|qualified substitute|"
            r"equivalence assumed|curator",
            text,
            re.IGNORECASE,
        ):
            raise ValueError("Authored locator retains edition/curator framing")


def build_locator_map(record: dict[str, Any], labels: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Bind explicitly audited neutral labels to every complete original passage."""
    validate_record(record)
    passages = record["payload"]["passages"]
    if set(labels) != {p["citation_id"] for p in passages}:
        raise ValueError("Mapping must cover every passage exactly")
    entries = []
    for p in passages:
        label = labels[p["citation_id"]]
        _locator(label)
        entries.append(
            {
                "citation_id": p["citation_id"],
                "passage_sha256": stable_json_sha256(p),
                "neutral": copy.deepcopy(label),
                "original_locator": {
                    k: copy.deepcopy(p.get(k))
                    for k in ("source_id", "title", "heading_path", "edition")
                },
            }
        )
    return {
        "version": MAP_VERSION,
        "case_id": record["case_id"],
        "record_sha256": stable_json_sha256(record),
        "entries": entries,
    }


def _mapping(record: dict[str, Any], mapping: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Rebuild the mapping to reject stale source bytes or unbound provenance."""
    _keys(mapping, {"version", "case_id", "record_sha256", "entries"}, "mapping")
    if not isinstance(mapping["entries"], list):
        raise ValueError("Invalid mapping entries")
    labels = {}
    for entry in mapping["entries"]:
        _keys(
            entry, {"citation_id", "passage_sha256", "neutral", "original_locator"}, "mapping entry"
        )
        if entry["citation_id"] in labels:
            raise ValueError("Duplicate mapping entry")
        labels[entry["citation_id"]] = entry["neutral"]
    if mapping != build_locator_map(record, labels):
        raise ValueError("Mapping/source identity changed")
    return labels


def _envelope(
    role: str,
    payload: dict[str, Any],
    summary: str,
    prompt: str,
    parent: dict[str, Any],
    mapping: dict[str, Any],
    provenance: dict[str, Any],
) -> dict[str, Any]:
    """Separate model messages from private provenance and bind both identities."""
    if not isinstance(summary, str) or not summary.strip() or not prompt.strip():
        raise ValueError("Shared summary and prompt must be nonblank")
    prefix = "<project_context>\n" + summary + "\n</project_context>\n\n"
    messages = [
        {"role": "system", "content": prefix + prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False, separators=(",", ":"))},
    ]
    private = {"locator_mapping": copy.deepcopy(mapping), **provenance}
    identity = {
        "version": VERSION,
        "private_provenance_sha256": stable_json_sha256(private),
        "role": role,
        "parent": parent,
        "mapping_sha256": stable_json_sha256(mapping),
        "summary_sha256": stable_json_sha256(summary),
        "prompt_sha256": stable_json_sha256(prompt),
        "payload_sha256": stable_json_sha256(payload),
        "messages_sha256": stable_json_sha256(messages),
    }
    return {
        "version": VERSION,
        "context_id": stable_json_sha256(identity),
        "identity": identity,
        "status": "not_run",
        "messages": messages,
        "payload": payload,
        "private_provenance": private,
    }


def project_target(
    record: dict[str, Any], mapping: dict[str, Any], *, summary: str, prompt: str
) -> dict[str, Any]:
    """Render target-only evidence; never accept a reference or judge label input."""
    labels = _mapping(record, mapping)
    payload = copy.deepcopy(record["payload"])
    payload["question"] = neutral_question(payload["question"])
    for p in payload["passages"]:
        neutral = labels[p["citation_id"]]
        p.pop("edition", None)
        p["title"] = neutral["document"] + ": " + neutral["title"]
        p["heading_path"] = copy.deepcopy(neutral["heading_path"])
    validate_record({**record, "payload": payload})
    return _envelope(
        "target",
        payload,
        summary,
        prompt,
        {"case_id": record["case_id"], "record_sha256": stable_json_sha256(record)},
        mapping,
        {"original_question": record["payload"]["question"]},
    )


def _validate_item(item: dict[str, Any], record: dict[str, Any]) -> None:
    """Verify pending legacy plan identities without transferring saved verdicts."""
    required = {
        "identity",
        "component",
        "point_id",
        "sample_id",
        "payload_sha256",
        "packet",
        "status",
    }
    if not required <= set(item) <= ITEM_FIELDS or item["status"] != "not_run":
        raise ValueError("Expected a pending legacy plan item")
    if (
        item.get("supported") is not None
        or item.get("error_type") is not None
        or item.get("unresolved_citation_ids")
    ):
        raise ValueError("Do not copy verdicts or failed projections")
    identity = item["identity"]
    _keys(identity, IDENTITY_FIELDS, "candidate identity")
    if identity["case_id"] != record["case_id"]:
        raise ValueError("Candidate case differs from source record")
    if any(type(identity[k]) is not int or identity[k] < 1 for k in ("repeat", "attempt")):
        raise ValueError("Invalid repeat/attempt")
    for key in IDENTITY_FIELDS - {"case_id", "repeat", "attempt"}:
        if not isinstance(identity[key], str) or not re.fullmatch("[0-9a-f]{64}", identity[key]):
            raise ValueError("Invalid candidate hash")
    if identity["candidate_id"] != stable_json_sha256(
        {k: v for k, v in identity.items() if k != "candidate_id"}
    ):
        raise ValueError("Candidate identity mismatch")
    if item["sample_id"] != stable_json_sha256(
        {k: item[k] for k in ("identity", "component", "point_id")}
    ):
        raise ValueError("Sample identity mismatch")
    if item["payload_sha256"] != stable_json_sha256(item["packet"]):
        raise ValueError("Legacy payload changed")


def _validate_packet(component: str, packet: dict[str, Any], citations: Any = None) -> None:
    """Reuse frozen component input isolation, without changing judge semantics."""
    if component == "A":
        no_answer.validate_input(packet)
    elif component == "G":
        point_grounding.validate_input(packet, citation_ids=citations)
    elif component in {"S", "C"}:
        adequacy_binary.validate_input(cast(adequacy_binary.Component, component), packet)
    else:
        raise ValueError("Unsupported component")


def _project_grounding_locators(
    packet: dict[str, Any], record: dict[str, Any], labels: dict[str, dict[str, Any]]
) -> None:
    """Neutralize copied G locators only after verifying exact bound evidence."""
    passages = {passage["citation_id"]: passage for passage in record["payload"]["passages"]}
    for evidence in packet["evidence"]:
        citation_id = evidence["occurrence_id"]
        if citation_id not in passages:
            raise ValueError("Unmapped G evidence")
        passage = passages[citation_id]
        for key in (
            "source_id",
            "title",
            "full_source_text",
            "tables",
            "physical_pages",
            "printed_labels",
        ):
            if evidence.get(key) != passage[key]:
                raise ValueError("G evidence differs from bound target passage")
        locator = evidence["canonical_target"]
        if set(locator) - {"unit_type", "unit_id", "extraction_id", "breadcrumb", "edition"}:
            raise ValueError("Unexpected canonical locator fields")
        if locator.get("breadcrumb") != [{"heading_text": h} for h in passage["heading_path"]]:
            raise ValueError("G section differs from bound target")
        locator.pop("edition", None)
        locator["breadcrumb"] = [{"heading_text": h} for h in labels[citation_id]["heading_path"]]
        evidence["title"] = labels[citation_id]["document"] + ": " + labels[citation_id]["title"]


def _project_reference(packet: dict[str, Any], reference: dict[str, Any]) -> None:
    """Replace a copied C reference only when its derivative binds the original."""
    _keys(
        reference,
        {"original_reference_sha256", "reference_conclusion", "publication_sha256"},
        "reference derivative",
    )
    if reference["original_reference_sha256"] != stable_json_sha256(packet["reference_conclusion"]):
        raise ValueError("Reference derivative does not bind original")
    if not isinstance(reference["publication_sha256"], str) or not re.fullmatch(
        "[0-9a-f]{64}", reference["publication_sha256"]
    ):
        raise ValueError("Reference publication hash required")
    packet["reference_conclusion"] = reference["reference_conclusion"]


def project_judge(
    item: dict[str, Any],
    record: dict[str, Any],
    mapping: dict[str, Any],
    *,
    summary: str,
    prompt: str,
    reference: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a new context identity; existing candidate prose is never neutralized.

    Caller verifies the owning plan/publication seals. Only C may consume an
    explicit reference derivative bound to its old text and publication hash.
    """
    labels = _mapping(record, mapping)
    _validate_item(item, record)
    component = item["component"]
    _validate_packet(component, item["packet"], item.get("citation_ids"))
    if reference is not None and component != "C":
        raise ValueError("Reference leakage outside C")
    packet = copy.deepcopy(item["packet"])
    provenance: dict[str, Any] = {
        "original_item_sha256": stable_json_sha256(item),
        "candidate_text_policy": "unchanged historical candidate, not newly generated",
    }
    if "question" in packet:
        if packet["question"] != record["payload"]["question"]:
            raise ValueError("Judge question differs from original target")
        packet["question"] = neutral_question(packet["question"])
    if component == "G":
        _project_grounding_locators(packet, record, labels)
    if reference is not None:
        _project_reference(packet, reference)
        provenance["reference_derivative"] = copy.deepcopy(reference)
    _validate_packet(component, packet, item.get("citation_ids"))
    return _envelope(
        component,
        packet,
        summary,
        prompt,
        {k: copy.deepcopy(item[k]) for k in ("identity", "sample_id", "point_id")},
        mapping,
        provenance,
    )
