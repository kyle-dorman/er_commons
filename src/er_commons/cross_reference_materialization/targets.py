"""Candidate-owned target-index construction from independent target evidence."""

from __future__ import annotations

import copy
import re
from collections import defaultdict
from typing import Any

JsonObject = dict[str, Any]
_TABLE_LABEL = re.compile(r"Table\s+([1-9][0-9]*(?:[.-][A-Za-z0-9]+)*)")
_SECTION_PREFIX = re.compile(r"^([1-9][0-9]*(?:\.[0-9]+)*)\b")


def remap_value(value: Any, upstream_id: str, candidate_id: str) -> Any:
    """Deep-copy a JSON value while remapping only the exact candidate namespace."""
    if isinstance(value, str):
        remapped = value.replace(upstream_id, candidate_id)
        if remapped == "er_commons.canonical_extraction.v2":
            return "er_commons.canonical_extraction.v3"
        return remapped
    if isinstance(value, list):
        return [remap_value(item, upstream_id, candidate_id) for item in value]
    if isinstance(value, dict):
        return {key: remap_value(item, upstream_id, candidate_id) for key, item in value.items()}
    return copy.deepcopy(value)


def build_target_index(
    *,
    upstream_aliases: list[JsonObject],
    upstream_blocks: list[JsonObject],
    upstream_tables: list[JsonObject],
    upstream_id: str,
    candidate_id: str,
) -> tuple[list[JsonObject], list[JsonObject]]:
    """Remap accepted aliases and append only strictly verified table aliases."""
    aliases: list[JsonObject] = []
    entries: list[JsonObject] = []
    for upstream_alias in upstream_aliases:
        alias = remap_value(upstream_alias, upstream_id, candidate_id)
        alias["alias_origin"] = "upstream_v2"
        alias["upstream_alias_id"] = upstream_alias["id"]
        converted_targets = []
        for old_target, target in zip(upstream_alias["targets"], alias["targets"], strict=True):
            converted_targets.append(
                {
                    "target_id": target["target_id"],
                    "target_type": target["target_type"],
                    "upstream_target_id": old_target["target_id"],
                    "evidence_kind": "accepted_v2_alias",
                    "evidence_source_record_id": None,
                    "evidence_page_id": None,
                }
            )
            entries.append(
                {
                    "lookup_key": alias["normalized_alias"],
                    "target_type": target["target_type"],
                    "alias_origin": "upstream_v2",
                    "alias_record_id": alias["id"],
                    "target_record_id": target["target_id"],
                    "upstream_alias_record_id": upstream_alias["id"],
                    "upstream_target_record_id": old_target["target_id"],
                    "evidence_kind": "accepted_v2_alias",
                    "evidence_source_record_id": None,
                    "evidence_page_id": None,
                }
            )
        alias["targets"] = converted_targets
        aliases.append(alias)

    page_tables: dict[str, list[JsonObject]] = defaultdict(list)
    for table in upstream_tables:
        for region in table["regions"]:
            page_tables[region["page_id"]].append(table)
    page_labels: dict[str, list[JsonObject]] = defaultdict(list)
    for block in upstream_blocks:
        match = _TABLE_LABEL.fullmatch(block.get("canonical_text", "").strip())
        if (
            match
            and block.get("content_layer") == "body"
            and block.get("is_toc_row") is False
            and len(block.get("regions", [])) == 1
        ):
            page_labels[block["regions"][0]["page_id"]].append(block)

    for page_id in sorted(page_labels):
        labels = page_labels[page_id]
        tables = page_tables.get(page_id, [])
        if len(labels) != 1 or len(tables) != 1:
            continue
        block = labels[0]
        table = tables[0]
        normalized = block["canonical_text"].strip().casefold()
        sequence = len(aliases) + 1
        alias_id = f"{candidate_id}/target-alias/deir_appendix_p/alias{sequence:06d}"
        target_id = table["id"].replace(upstream_id, candidate_id)
        evidence_block_id = block["id"].replace(upstream_id, candidate_id)
        evidence_page_id = page_id.replace(upstream_id, candidate_id)
        alias = {
            "id": alias_id,
            "document_id": table["document_id"].replace(upstream_id, candidate_id),
            "sequence": sequence,
            "alias_kind": "table",
            "raw_values": [block["canonical_text"].strip()],
            "normalized_alias": normalized,
            "normalization_policy": "nfc_nbsp_ascii_whitespace_casefold_v1",
            "resolution_status": "unique",
            "alias_origin": "v3_verified_table_label",
            "upstream_alias_id": None,
            "targets": [
                {
                    "target_id": target_id,
                    "target_type": "table",
                    "upstream_target_id": table["id"],
                    "evidence_kind": "verified_same_page_table_label",
                    "evidence_source_record_id": evidence_block_id,
                    "evidence_page_id": evidence_page_id,
                }
            ],
        }
        aliases.append(alias)
        entries.append(
            {
                "lookup_key": normalized,
                "target_type": "table",
                "alias_origin": "v3_verified_table_label",
                "alias_record_id": alias_id,
                "target_record_id": target_id,
                "upstream_alias_record_id": None,
                "upstream_target_record_id": table["id"],
                "evidence_kind": "verified_same_page_table_label",
                "evidence_source_record_id": evidence_block_id,
                "evidence_page_id": evidence_page_id,
            }
        )
    return aliases, sorted(entries, key=_entry_order)


def lookup_keys(entry: JsonObject) -> set[str]:
    """Return exact and structural lookup keys authorized by one index entry."""
    keys = {entry["lookup_key"]}
    if entry["target_type"] == "section":
        match = _SECTION_PREFIX.match(entry["lookup_key"])
        if match:
            keys.add(match.group(1))
    if entry["target_type"] == "page" and entry["lookup_key"].startswith("page "):
        keys.add(entry["lookup_key"].removeprefix("page "))
    return keys


def _entry_order(entry: JsonObject) -> tuple[str, str, str]:
    return entry["lookup_key"], entry["target_record_id"], entry["alias_record_id"]
