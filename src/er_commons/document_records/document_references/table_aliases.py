"""Construct strict R6 table aliases from independent body-side evidence."""

from __future__ import annotations

import re
from collections import defaultdict
from itertools import pairwise

from er_commons.document_records.document_references.exact_resolution import (
    ExactAliasEvidence,
    normalize_exact_text,
)
from er_commons.document_records.document_references.indexing import NamespaceRemapper
from er_commons.document_records.document_references.linking_core import DerivedTargetAlias
from er_commons.document_records.document_references.policy import TABLE_LABEL_BLOCK_TYPES
from er_commons.document_records.document_references.types import JsonObject

_COMPLETE_TABLE_CAPTION = re.compile(
    r"table [1-9][0-9]*[a-z]?(?:[.-][a-z0-9]+)*(?:\s*(?:[.:\-–—]\s*)?\S.*)?",
    re.IGNORECASE,
)
_TABLE_NUMBER_PREFIX = re.compile(
    r"^(table\s+[1-9][0-9]*[a-z]?(?:[.-][a-z0-9]+)*)\b", re.IGNORECASE
)
_SPACED_TABLE_SUFFIX = re.compile(
    r"^(?P<prefix>table\s+[1-9][0-9]*[a-z]?(?:\.[0-9]+)*)\s*-\s*(?P<suffix>[a-z0-9]+)\b",
    re.IGNORECASE,
)


def build_r6_table_aliases(
    *,
    upstream_candidate_id: str,
    candidate_id: str,
    source_id: str,
    upstream_blocks: list[JsonObject],
    upstream_tables: list[JsonObject],
    first_sequence: int,
) -> tuple[DerivedTargetAlias, ...]:
    """Return aliases only for captions satisfying every accepted R6 relation."""
    remapper = NamespaceRemapper(upstream_candidate_id, candidate_id)
    eligible_ids = {block["id"] for block in _eligible_captions(upstream_blocks)}
    derived: list[DerivedTargetAlias] = []
    for page_id, ordered_items in sorted(
        _canonical_page_items(upstream_blocks, upstream_tables).items()
    ):
        for caption, table in pairwise(ordered_items):
            if caption.get("id") not in eligible_ids or table.get("_record_kind") != "table":
                continue
            if not _satisfies_spatial_relations(caption, table):
                continue
            derived.append(
                _derived_alias(
                    remapper=remapper,
                    source_id=source_id,
                    caption=caption,
                    table=table,
                    page_id=page_id,
                    sequence=first_sequence + len(derived),
                )
            )
    return tuple(derived)


def _derived_alias(
    *,
    remapper: NamespaceRemapper,
    source_id: str,
    caption: JsonObject,
    table: JsonObject,
    page_id: str,
    sequence: int,
) -> DerivedTargetAlias:
    """Build one canonical alias and its equivalent in-memory evidence edge."""
    raw_caption = str(caption["canonical_text"]).strip()
    normalized_caption = normalize_table_caption(raw_caption)
    if _TABLE_NUMBER_PREFIX.match(normalized_caption) is None:  # guarded by eligibility
        raise ValueError(
            f"R6 caption lost its required table identifier: {caption.get('id', '<unknown>')}"
        )
    # The marker is validated but deliberately not exposed as a lookup key.
    # R6 accepted only complete-caption aliases because marker-only keys collide.
    alias_id = f"{remapper.candidate_id}/target-alias/{source_id}/alias{sequence:06d}"
    target_id = remapper.record_id(str(table["id"]))
    local_caption_id = remapper.record_id(str(caption["id"]))
    local_page_id = remapper.record_id(page_id)
    record: JsonObject = {
        "id": alias_id,
        "document_id": remapper.record_id(str(table["document_id"])),
        "sequence": sequence,
        "alias_kind": "table",
        "raw_values": [raw_caption],
        "normalized_alias": normalized_caption,
        "normalization_policy": "nfc_nbsp_ascii_whitespace_casefold_v1",
        "resolution_status": "unique",
        "alias_origin": "linking_v1_r6_body_table_caption",
        "upstream_alias_id": None,
        "targets": [
            {
                "target_id": target_id,
                "target_type": "table",
                "upstream_target_id": table["id"],
                "evidence_kind": "r6_body_table_caption",
                "evidence_source_record_id": local_caption_id,
                "evidence_page_id": local_page_id,
            }
        ],
    }
    return DerivedTargetAlias(
        record=record,
        evidence=ExactAliasEvidence(
            lookup_keys=(normalized_caption,),
            target_type="table",
            alias_id=alias_id,
            target_id=target_id,
            target_page_ids=(local_page_id,),
        ),
        rule_id="R6",
    )


def normalize_table_caption(value: str) -> str:
    """Normalize only spacing inside a leading table identifier.

    Task 04D accepts this as structural parsing of identifiers such as
    ``Table 4.5 -2f``. Hyphens in caption prose remain untouched and can be
    compared only through the separately authorized, exact-first R6a rules.
    """
    normalized = normalize_exact_text(value)
    match = _SPACED_TABLE_SUFFIX.match(normalized)
    if match is None:
        return normalized
    compact = f"{match.group('prefix')}-{match.group('suffix')}"
    return f"{compact}{normalized[match.end() :]}"


def _eligible_captions(blocks: list[JsonObject]) -> list[JsonObject]:
    """Select complete, single-region body captions eligible for R6."""
    return [
        block
        for block in blocks
        if (
            block.get("content_layer") == "body"
            and block.get("is_toc_row") is False
            and block.get("block_type") in TABLE_LABEL_BLOCK_TYPES
            and len(block.get("regions", [])) == 1
            and _COMPLETE_TABLE_CAPTION.fullmatch(
                normalize_table_caption(str(block.get("canonical_text", "")).strip())
            )
        )
    ]


def _canonical_page_items(
    blocks: list[JsonObject], tables: list[JsonObject]
) -> dict[str, list[JsonObject]]:
    """Order all bounded block/table records top-to-bottom, then left-to-right."""
    by_page: dict[str, list[JsonObject]] = defaultdict(list)
    for kind, records in (("block", blocks), ("table", tables)):
        for record in records:
            regions = record.get("regions", [])
            if len(regions) != 1 or not _valid_bbox(regions[0].get("bbox")):
                continue
            item = dict(record)
            item["_record_kind"] = kind
            by_page[str(regions[0]["page_id"])].append(item)
    for items in by_page.values():
        items.sort(key=_page_item_order)
    return by_page


def _valid_bbox(value: object) -> bool:
    """Accept four numeric coordinates while rejecting booleans."""
    return (
        isinstance(value, list)
        and len(value) == 4
        and all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value)
    )


def _page_item_order(record: JsonObject) -> tuple[float, float, str]:
    """Return deterministic top-to-bottom, left-to-right record order."""
    left, _lower, _right, upper = record["regions"][0]["bbox"]
    return -float(upper), float(left), str(record["id"])


def _satisfies_spatial_relations(caption: JsonObject, table: JsonObject) -> bool:
    """Require same-section placement, vertical adjacency, and horizontal overlap."""
    section_id = caption.get("section_id")
    if section_id is None or table.get("section_id") != section_id:
        return False
    caption_left, caption_lower, caption_right, _ = caption["regions"][0]["bbox"]
    table_left, _, table_right, table_upper = table["regions"][0]["bbox"]
    return bool(
        float(table_upper) <= float(caption_lower)
        and min(float(caption_right), float(table_right))
        > max(float(caption_left), float(table_left))
    )


__all__ = ["build_r6_table_aliases", "normalize_table_caption"]
