"""Qualify supplemental aliases from existing canonical records without changing them."""

from __future__ import annotations

import re
from collections import defaultdict
from itertools import pairwise
from typing import Any

from er_commons.artifact_io import canonical_json_sha256
from er_commons.document_records.document_references import table_aliases
from er_commons.document_records.document_references.policy import TABLE_LABEL_BLOCK_TYPES

type JsonObject = dict[str, Any]

_TABLE_CAPTION = re.compile(
    r"table\s+(?:[1-9][0-9]*[a-z]?(?:[.-][a-z0-9]+)*|[a-z]-[1-9][0-9]*(?:[.-][a-z0-9]+)*)"
    r"(?:\s*[.:–—-]?\s+\S.*)?",
    re.IGNORECASE,
)
_APPENDIX_HEADING = re.compile(r"appendix\s+([a-z](?:\.[0-9]+)*)(?=\s|:\s|\.\s|$)", re.IGNORECASE)
_PAGE_LABEL = re.compile(r"(?:[0-9]+(?:[.-][0-9]+)*|[ivxlcdm]+)", re.IGNORECASE)


def qualify_supplemental_aliases(
    *,
    source_id: str,
    source_ordinal: int,
    candidate_id: str,
    blocks: list[JsonObject],
    tables: list[JsonObject],
    pages: list[JsonObject],
    sections: list[JsonObject] | None = None,
) -> list[JsonObject]:
    """Return qualified aliases and exact evidence anchors for an already verified candidate.

    The caller verifies the selected candidate inventory before providing complete
    canonical streams. These records never grant fresh review or model eligibility.
    Table geometry is the accepted R6 rule, with letter-prefixed identifiers added.
    Footer labels must agree with canonical labels and be unique across the source.
    """
    by_page = {str(page["id"]): page for page in pages}
    if len(by_page) != len(pages):
        raise ValueError("duplicate canonical page record")
    by_section = {str(section["id"]): section for section in sections or []}
    by_block = {str(block["id"]): block for block in blocks}
    if len(by_block) != len(blocks) or len(by_section) != len(sections or []):
        raise ValueError("duplicate canonical evidence record")
    proposed: list[JsonObject] = []

    def add(
        key: str,
        kind: str,
        target: str,
        page: str,
        evidence: list[str],
        rule: str,
        section_id: str | None = None,
    ) -> None:
        """Retain candidate provenance in a deterministic derived alias identity."""
        row = {
            "lookup_key": key,
            "target_type": kind,
            "source_id": source_id,
            "source_ordinal": source_ordinal,
            "target_id": target,
            "candidate_id": candidate_id,
            "evidence_record_ids": evidence,
            "page_id": page,
            "rule": rule,
        }
        if section_id is not None:
            identifier, ancestry = _appendix_ancestor(
                section_id, by_section, by_block, by_page[page].get("document_id")
            )
            if identifier is not None:
                row["inner_appendix_identifier"] = identifier
                row["evidence_record_ids"] = evidence + ancestry
        proposed.append({**row, "alias_id": "supplementalaliasv1-" + canonical_json_sha256(row)})

    for page_id, items in table_aliases._canonical_page_items(blocks, tables).items():
        if page_id not in by_page:
            continue
        for caption, table in pairwise(items):
            normalized = table_aliases.normalize_table_caption(
                str(caption.get("canonical_text", ""))
            )
            if (
                caption.get("_record_kind") == "block"
                and caption.get("content_layer") == "body"
                and caption.get("is_toc_row") is False
                and caption.get("block_type") in TABLE_LABEL_BLOCK_TYPES
                and _TABLE_CAPTION.fullmatch(normalized)
                and table.get("_record_kind") == "table"
                and table.get("content_layer") == "body"
                and table.get("is_toc_row") is False
                and caption.get("document_id")
                == table.get("document_id")
                == by_page[page_id].get("document_id")
                and table_aliases._satisfies_spatial_relations(caption, table)
            ):
                add(
                    normalized,
                    "table",
                    str(table["id"]),
                    page_id,
                    [str(caption["id"]), str(table["id"])],
                    "strict_adjacent_table_caption_v1",
                    str(table["section_id"]),
                )

    footers: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for block in blocks:
        regions = block.get("regions", [])
        label = str(block.get("canonical_text", "")).strip().casefold()
        if (
            block.get("block_type") == "page_footer"
            and block.get("content_layer") == "furniture"
            and block.get("is_toc_row") is False
            and len(regions) == 1
            and _PAGE_LABEL.fullmatch(label)
        ):
            page_id = str(regions[0]["page_id"])
            if page_id in by_page and block.get("document_id") == by_page[page_id].get(
                "document_id"
            ):
                footers[page_id].append((label, str(block["id"])))
    for page_id, observations in footers.items():
        labels = {label for label, _ in observations}
        if len(labels) != 1:
            continue
        label = next(iter(labels))
        existing = by_page[page_id].get("printed_page_label")
        if existing is not None and str(existing).strip().casefold() != label:
            continue
        # Include canonical labels on every other page in the collision check.
        conflicting_pages = {
            other
            for other, page in by_page.items()
            if str(page.get("printed_page_label", "")).strip().casefold() == label
        } | {
            other for other, values in footers.items() if any(value == label for value, _ in values)
        }
        if conflicting_pages - {page_id}:
            continue
        add(
            "page " + label,
            "page",
            page_id,
            page_id,
            sorted(record_id for _, record_id in observations),
            "unique_canonical_footer_label_v1",
        )

    # Keep contradictory table aliases: dropping them could make an older alias
    # falsely unique when the consumer merges old and supplemental evidence.
    return sorted(
        proposed,
        key=lambda row: (row["lookup_key"], row["target_id"], row["alias_id"]),
    )


def _appendix_ancestor(
    section_id: str,
    sections: dict[str, JsonObject],
    blocks: dict[str, JsonObject],
    document_id: str | None,
) -> tuple[str | None, list[str]]:
    """Read nearest explicit appendix heading through canonical parent relations."""
    visited: set[str] = set()
    evidence: list[str] = []
    current: str | None = section_id
    while current is not None:
        if current in visited:
            raise ValueError("cycle in canonical section ancestry")
        visited.add(current)
        section = sections.get(current)
        if section is None:
            return None, []
        if section.get("document_id") != document_id:
            raise ValueError("cross-document canonical section ancestry")
        evidence.append(current)
        heading = blocks.get(str(section.get("heading_block_id")))
        if heading is not None:
            if heading.get("document_id") != document_id:
                raise ValueError("cross-document appendix heading")
            match = _APPENDIX_HEADING.match(str(heading.get("canonical_text", "")).strip())
            if (
                match
                and heading.get("content_layer") == "body"
                and heading.get("is_toc_row") is False
            ):
                return match.group(1).casefold(), evidence + [str(heading["id"])]
        current = section.get("parent_section_id")
    return None, []
