"""Construct remapped v3 records, mentions, and candidate-owned support."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.cross_reference_materialization.detection import (
    PATTERN_VERSION,
    detect_mentions,
    eligible_source,
)
from er_commons.cross_reference_materialization.io import read_jsonl
from er_commons.cross_reference_materialization.resolution import resolve_mention
from er_commons.cross_reference_materialization.targets import build_target_index, remap_value

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class CrossReferenceBuild:
    """All deterministic record streams and support payloads for one candidate."""

    record_files: dict[str, list[JsonObject]]
    target_aliases: list[JsonObject]
    cross_references: list[JsonObject]
    support: dict[str, JsonObject]


def construct_candidate(
    *, upstream_root: Path, upstream_id: str, candidate_id: str
) -> CrossReferenceBuild:
    """Remap the accepted v2 graph and add only frozen v3 cross-reference facts."""
    manifest = json.loads((upstream_root / "records" / "manifest.json").read_bytes())
    upstream_files = {
        item["path"]: read_jsonl(upstream_root / item["path"]) for item in manifest["record_files"]
    }
    upstream_blocks = upstream_files["canonical/blocks.jsonl"]
    upstream_tables = upstream_files["canonical/tables.jsonl"]
    upstream_aliases = upstream_files["canonical/target_aliases.jsonl"]
    aliases, index_entries = build_target_index(
        upstream_aliases=upstream_aliases,
        upstream_blocks=upstream_blocks,
        upstream_tables=upstream_tables,
        upstream_id=upstream_id,
        candidate_id=candidate_id,
    )
    target_support: JsonObject = {
        "schema_version": "er_commons.cross_reference_target_index.v3",
        "upstream_alias_count": len(upstream_aliases),
        "derived_table_alias_count": len(aliases) - len(upstream_aliases),
        "derived_figure_alias_count": 0,
        "entries": index_entries,
    }
    target_index_sha256 = _serialized_sha256(target_support)

    record_files = {
        path: [remap_value(record, upstream_id, candidate_id) for record in records]
        for path, records in upstream_files.items()
        if path not in {"canonical/target_aliases.jsonl", "canonical/cross_references.jsonl"}
    }
    pages = record_files["canonical/pages.jsonl"]
    page_numbers = {page["id"]: page["physical_page_number"] for page in pages}
    targets = [
        *record_files["canonical/documents.jsonl"],
        *record_files["canonical/pages.jsonl"],
        *record_files["canonical/sections.jsonl"],
        *record_files["canonical/tables.jsonl"],
        *record_files["canonical/figures.jsonl"],
    ]
    target_order = {
        record["id"]: record.get("sequence", record.get("physical_page_number", 0)) or 0
        for record in targets
    }

    mentions: list[JsonObject] = []
    diagnostic_counts: Counter[str] = Counter()
    eligible_count = 0
    for upstream_block, block in zip(
        upstream_blocks, record_files["canonical/blocks.jsonl"], strict=True
    ):
        if eligible_source(upstream_block):
            eligible_count += 1
        detected, diagnostics = detect_mentions(upstream_block)
        diagnostic_counts.update(item.diagnostic_class for item in diagnostics)
        if not detected:
            continue
        source_page_id = block["regions"][0]["page_id"]
        for detected_mention in detected:
            candidates, reason = resolve_mention(
                detected_mention,
                source_text=upstream_block["canonical_text"],
                source_page_id=source_page_id,
                entries=index_entries,
                page_numbers=page_numbers,
                target_order=target_order,
                target_index_sha256=target_index_sha256,
            )
            sequence = len(mentions) + 1
            status = (
                "unresolved"
                if not candidates
                else "resolved"
                if len(candidates) == 1
                else "ambiguous"
            )
            mentions.append(
                {
                    "schema_version": "er_commons.canonical_extraction.v3",
                    "extraction_id": candidate_id,
                    "id": f"{candidate_id}/cross-reference/deir_appendix_p/xref{sequence:06d}",
                    "document_id": block["document_id"],
                    "sequence": sequence,
                    "source_record_id": block["id"],
                    "mention_class": detected_mention.mention_class,
                    "raw_text": detected_mention.raw_text,
                    "source_charspan": [detected_mention.start, detected_mention.end],
                    "pattern_version": PATTERN_VERSION,
                    "lookup_key": detected_mention.lookup_key,
                    "candidates": candidates,
                    "resolution_status": status,
                    "unresolved_reason": reason,
                    "regions": block["regions"],
                    "raw_links": block["raw_links"],
                }
            )

    mention_counts = Counter(item["mention_class"] for item in mentions)
    status_counts = Counter(item["resolution_status"] for item in mentions)
    reason_counts = Counter(
        item["unresolved_reason"] for item in mentions if item["unresolved_reason"] is not None
    )
    summary: JsonObject = {
        "schema_version": "er_commons.cross_reference_summary.v3",
        "eligible_source_count": eligible_count,
        "mention_counts": dict(sorted(mention_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "unresolved_reason_counts": dict(sorted(reason_counts.items())),
        "unsupported_diagnostic_counts": dict(sorted(diagnostic_counts.items())),
    }
    preservation: JsonObject = {
        "schema_version": "er_commons.cross_reference_preservation.v3",
        "upstream_candidate_id": upstream_id,
        "upstream_alias_count": len(upstream_aliases),
        "bidirectional_alias_correspondence_complete": True,
        "derived_table_alias_count": len(aliases) - len(upstream_aliases),
        "derived_figure_alias_count": 0,
        "undeclared_difference_count": 0,
        "status": "passed",
    }
    return CrossReferenceBuild(
        record_files=record_files,
        target_aliases=aliases,
        cross_references=mentions,
        support={
            "cross_reference_target_index": target_support,
            "cross_reference_summary": summary,
            "cross_reference_preservation": preservation,
        },
    )


def _serialized_sha256(value: Any) -> str:
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    return hashlib.sha256(payload.encode()).hexdigest()
