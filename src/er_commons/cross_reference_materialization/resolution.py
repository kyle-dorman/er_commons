"""Deterministic local candidate generation and uncertainty preservation."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from er_commons.cross_reference_materialization.detection import DetectedMention
from er_commons.cross_reference_materialization.targets import lookup_keys

JsonObject = dict[str, Any]
_TARGET_ORDER = {"document": 0, "page": 1, "section": 2, "table": 3, "figure": 4}


def resolve_mention(
    mention: DetectedMention,
    *,
    source_text: str,
    source_page_id: str,
    entries: list[JsonObject],
    page_numbers: dict[str, int],
    target_order: dict[str, int],
    target_index_sha256: str,
) -> tuple[list[JsonObject], str | None]:
    """Return ordered candidates or one closed-vocabulary unresolved reason."""
    if mention.mention_class == "figure":
        return [], "accepted_target_type_unavailable"
    if mention.mention_class == "document":
        return [], "external_document_outside_corpus"
    if mention.mention_class == "table" and _is_qualified_external(source_text[mention.end :]):
        return [], "qualified_external_table_reference"

    matching = [entry for entry in entries if mention.lookup_key in lookup_keys(entry)]
    matching = [entry for entry in matching if _type_matches(mention.mention_class, entry)]
    had_table_alias = bool(matching) if mention.mention_class == "table" else False
    if mention.mention_class == "table":
        source_page = page_numbers[source_page_id]
        matching = [
            entry
            for entry in matching
            if entry["evidence_page_id"] is not None
            and abs(page_numbers[entry["evidence_page_id"]] - source_page) <= 5
        ]

    grouped: dict[str, list[JsonObject]] = defaultdict(list)
    for entry in matching:
        grouped[entry["target_record_id"]].append(entry)
    candidates = [
        _candidate(
            group,
            source_page_id=source_page_id,
            page_numbers=page_numbers,
            target_index_sha256=target_index_sha256,
        )
        for group in grouped.values()
    ]
    candidates.sort(
        key=lambda candidate: (
            _TARGET_ORDER[candidate["target_type"]],
            target_order.get(candidate["target_record_id"], 10**9),
            candidate["target_record_id"],
        )
    )
    if candidates:
        return candidates, None
    if mention.mention_class == "table" and had_table_alias:
        return [], "outside_table_page_window"
    if mention.mention_class in {"figure"}:
        return [], "accepted_target_type_unavailable"
    return [], "no_local_alias"


def _candidate(
    entries: list[JsonObject],
    *,
    source_page_id: str,
    page_numbers: dict[str, int],
    target_index_sha256: str = "0" * 64,
) -> JsonObject:
    ordered = sorted(entries, key=lambda entry: entry["alias_record_id"])
    first = ordered[0]
    origins = {entry["alias_origin"] for entry in ordered}
    if len(origins) != 1:
        raise ValueError("one target candidate cannot mix alias origins")
    evidence_kind = (
        "verified_same_page_table_label"
        if first["alias_origin"] == "v3_verified_table_label"
        else _upstream_evidence_kind(first)
    )
    refs = [
        {
            "path": "support/cross_reference_target_index.json",
            "sha256": target_index_sha256,
        }
    ]
    result: JsonObject = {
        "target_type": first["target_type"],
        "alias_origin": first["alias_origin"],
        "alias_record_ids": [entry["alias_record_id"] for entry in ordered],
        "target_record_id": first["target_record_id"],
        "upstream_alias_record_ids": [
            entry["upstream_alias_record_id"]
            for entry in ordered
            if entry["upstream_alias_record_id"] is not None
        ],
        "upstream_target_record_id": first["upstream_target_record_id"],
        "evidence": [{"kind": evidence_kind, "refs": refs}],
    }
    if first["alias_origin"] == "v3_verified_table_label":
        result["page_distance"] = abs(
            page_numbers[first["evidence_page_id"]] - page_numbers[source_page_id]
        )
    return result


def _upstream_evidence_kind(entry: JsonObject) -> str:
    if entry["target_type"] == "section" and _looks_numeric(entry["lookup_key"]):
        return "section_numeric_prefix"
    if entry["target_type"] == "section" and entry["lookup_key"].startswith("appendix "):
        return "appendix_key_exact"
    if entry["target_type"] == "page":
        return "resolved_printed_page_exact"
    return "accepted_alias_exact"


def _looks_numeric(value: str) -> bool:
    return value.startswith(tuple("0123456789"))


def _type_matches(mention_class: str, entry: JsonObject) -> bool:
    expected = {"appendix": "section", "printed_page": "page"}.get(mention_class, mention_class)
    target_type = entry.get("target_type")
    return isinstance(target_type, str) and target_type == expected


def _is_qualified_external(suffix: str) -> bool:
    import re

    return bool(re.match(r"^\s+(?:in|from|of)\s+Reference\s+[1-9][0-9]*\b", suffix))
