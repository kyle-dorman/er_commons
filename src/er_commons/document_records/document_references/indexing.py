"""Build the candidate-owned target index from accepted target-side evidence."""

from __future__ import annotations

import copy
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from er_commons.document_records.document_references.policy import TABLE_LABEL_PATTERN
from er_commons.document_records.document_references.types import JsonObject, TargetIndexEntry


@dataclass(frozen=True)
class TargetIndex:
    """Canonical aliases plus convenient typed lookup rows."""

    aliases: tuple[JsonObject, ...]
    entries: tuple[TargetIndexEntry, ...]
    upstream_alias_count: int

    @property
    def derived_table_alias_count(self) -> int:
        """Count aliases added from verified same-page table labels."""
        return len(self.aliases) - self.upstream_alias_count

    def matching(self, lookup_key: str, target_type: str) -> list[TargetIndexEntry]:
        """Return entries matching one authorized key and target type."""
        return [
            entry
            for entry in self.entries
            if entry.target_type == target_type and lookup_key in entry.structural_lookup_keys()
        ]

    def support_payload(self) -> JsonObject:
        """Serialize the complete target-index support artifact."""
        return {
            "schema_version": "er_commons.cross_reference_target_index.v3",
            "upstream_alias_count": self.upstream_alias_count,
            "derived_table_alias_count": self.derived_table_alias_count,
            "derived_figure_alias_count": 0,
            "entries": [entry.as_json() for entry in self.entries],
        }


class NamespaceRemapper:
    """Remap only exact candidate-scoped IDs and the canonical schema major."""

    def __init__(self, upstream_candidate_id: str, candidate_id: str) -> None:
        self.upstream_candidate_id = upstream_candidate_id
        self.candidate_id = candidate_id

    def value(self, value: Any) -> Any:
        """Return a deep copy with the accepted namespace transformation."""
        if isinstance(value, str):
            remapped = value.replace(self.upstream_candidate_id, self.candidate_id)
            if remapped == "er_commons.canonical_extraction.v2":
                return "er_commons.canonical_extraction.v3"
            return remapped
        if isinstance(value, list):
            return [self.value(item) for item in value]
        if isinstance(value, dict):
            return {key: self.value(item) for key, item in value.items()}
        return copy.deepcopy(value)

    def record_id(self, upstream_record_id: str) -> str:
        """Remap one known upstream record ID."""
        return upstream_record_id.replace(self.upstream_candidate_id, self.candidate_id)


class TargetIndexBuilder:
    """Preserve accepted aliases and add only verified table-label aliases."""

    def __init__(self, remapper: NamespaceRemapper, source_id: str | None = None) -> None:
        self._remapper = remapper
        self._source_id = source_id

    def build(
        self,
        *,
        upstream_aliases: list[JsonObject],
        upstream_blocks: list[JsonObject],
        upstream_tables: list[JsonObject],
    ) -> TargetIndex:
        """Construct the full index in two explicit evidence phases."""
        if self._source_id is None:
            self._source_id = _source_id_from_records(upstream_blocks, upstream_tables)
        aliases, entries = self._preserve_upstream_aliases(upstream_aliases)
        derived_aliases, derived_entries = self._verified_table_aliases(
            upstream_blocks=upstream_blocks,
            upstream_tables=upstream_tables,
            first_sequence=len(aliases) + 1,
        )
        aliases.extend(derived_aliases)
        entries.extend(derived_entries)
        entries.sort(key=_entry_order)
        return TargetIndex(tuple(aliases), tuple(entries), len(upstream_aliases))

    def _preserve_upstream_aliases(
        self, upstream_aliases: list[JsonObject]
    ) -> tuple[list[JsonObject], list[TargetIndexEntry]]:
        aliases: list[JsonObject] = []
        entries: list[TargetIndexEntry] = []
        for upstream_alias in upstream_aliases:
            alias = self._remapper.value(upstream_alias)
            alias["alias_origin"] = "upstream_v2"
            alias["upstream_alias_id"] = upstream_alias["id"]
            alias["targets"] = []
            for upstream_target in upstream_alias["targets"]:
                local_target_id = self._remapper.record_id(upstream_target["target_id"])
                alias["targets"].append(
                    {
                        "target_id": local_target_id,
                        "target_type": upstream_target["target_type"],
                        "upstream_target_id": upstream_target["target_id"],
                        "evidence_kind": "accepted_v2_alias",
                        "evidence_source_record_id": None,
                        "evidence_page_id": None,
                    }
                )
                entries.append(
                    TargetIndexEntry(
                        lookup_key=alias["normalized_alias"],
                        target_type=upstream_target["target_type"],
                        alias_origin="upstream_v2",
                        alias_record_id=alias["id"],
                        target_record_id=local_target_id,
                        upstream_alias_record_id=upstream_alias["id"],
                        upstream_target_record_id=upstream_target["target_id"],
                        evidence_kind="accepted_v2_alias",
                        evidence_source_record_id=None,
                        evidence_page_id=None,
                    )
                )
            aliases.append(alias)
        return aliases, entries

    def _verified_table_aliases(
        self,
        *,
        upstream_blocks: list[JsonObject],
        upstream_tables: list[JsonObject],
        first_sequence: int,
    ) -> tuple[list[JsonObject], list[TargetIndexEntry]]:
        tables_by_page = _records_by_page(upstream_tables)
        labels_by_page = _eligible_table_labels_by_page(upstream_blocks)
        aliases: list[JsonObject] = []
        entries: list[TargetIndexEntry] = []
        for page_id in sorted(labels_by_page):
            labels = labels_by_page[page_id]
            tables = tables_by_page.get(page_id, [])
            if len(labels) != 1 or len(tables) != 1:
                continue
            alias, entry = self._table_alias(
                block=labels[0],
                table=tables[0],
                page_id=page_id,
                sequence=first_sequence + len(aliases),
            )
            aliases.append(alias)
            entries.append(entry)
        return aliases, entries

    def _table_alias(
        self, *, block: JsonObject, table: JsonObject, page_id: str, sequence: int
    ) -> tuple[JsonObject, TargetIndexEntry]:
        raw_label = block["canonical_text"].strip()
        lookup_key = raw_label.casefold()
        alias_id = (
            f"{self._remapper.candidate_id}/target-alias/{self._source_id}/alias{sequence:06d}"
        )
        local_target_id = self._remapper.record_id(table["id"])
        local_block_id = self._remapper.record_id(block["id"])
        local_page_id = self._remapper.record_id(page_id)
        alias = {
            "id": alias_id,
            "document_id": self._remapper.record_id(table["document_id"]),
            "sequence": sequence,
            "alias_kind": "table",
            "raw_values": [raw_label],
            "normalized_alias": lookup_key,
            "normalization_policy": "nfc_nbsp_ascii_whitespace_casefold_v1",
            "resolution_status": "unique",
            "alias_origin": "v3_verified_table_label",
            "upstream_alias_id": None,
            "targets": [
                {
                    "target_id": local_target_id,
                    "target_type": "table",
                    "upstream_target_id": table["id"],
                    "evidence_kind": "verified_same_page_table_label",
                    "evidence_source_record_id": local_block_id,
                    "evidence_page_id": local_page_id,
                }
            ],
        }
        entry = TargetIndexEntry(
            lookup_key=lookup_key,
            target_type="table",
            alias_origin="v3_verified_table_label",
            alias_record_id=alias_id,
            target_record_id=local_target_id,
            upstream_alias_record_id=None,
            upstream_target_record_id=table["id"],
            evidence_kind="verified_same_page_table_label",
            evidence_source_record_id=local_block_id,
            evidence_page_id=local_page_id,
        )
        return alias, entry


def _records_by_page(records: list[JsonObject]) -> dict[str, list[JsonObject]]:
    by_page: dict[str, list[JsonObject]] = defaultdict(list)
    for record in records:
        for region in record["regions"]:
            by_page[region["page_id"]].append(record)
    return by_page


def _source_id_from_records(blocks: list[JsonObject], tables: list[JsonObject]) -> str:
    """Recover the verified source namespace for legacy direct builder callers."""
    records = tables or blocks
    if not records:
        return "unresolved_source"
    document_id = records[0].get("document_id")
    marker = "/document/"
    if not isinstance(document_id, str) or marker not in document_id:
        raise ValueError("target-index records do not expose a source document namespace")
    suffix = document_id.split(marker, 1)[1]
    source_id = suffix.split("/", 1)[0]
    if not source_id:
        raise ValueError("target-index source namespace is empty")
    return source_id


def _eligible_table_labels_by_page(
    blocks: list[JsonObject],
) -> dict[str, list[JsonObject]]:
    by_page: dict[str, list[JsonObject]] = defaultdict(list)
    for block in blocks:
        regions = block.get("regions", [])
        if (
            block.get("content_layer") == "body"
            and block.get("is_toc_row") is False
            and len(regions) == 1
            and TABLE_LABEL_PATTERN.fullmatch(block.get("canonical_text", "").strip())
        ):
            by_page[regions[0]["page_id"]].append(block)
    return by_page


def _entry_order(entry: TargetIndexEntry) -> tuple[str, str, str]:
    return entry.lookup_key, entry.target_record_id, entry.alias_record_id
