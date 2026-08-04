"""Deterministic local resolution with uncertainty kept visible."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Collection, Mapping

from er_commons.cross_reference_enrichment.indexing import TargetIndex
from er_commons.cross_reference_enrichment.policy import is_qualified_external_table_reference
from er_commons.cross_reference_enrichment.types import (
    DetectedMention,
    JsonObject,
    MentionKind,
    Resolution,
    TargetIndexEntry,
    UnresolvedReason,
)

TARGET_TYPE_FOR_MENTION = {
    MentionKind.SECTION: "section",
    MentionKind.APPENDIX: "section",
    MentionKind.TABLE: "table",
    MentionKind.FIGURE: "figure",
    MentionKind.PRINTED_PAGE: "page",
    MentionKind.DOCUMENT: "document",
}
TARGET_TYPE_ORDER = {"document": 0, "page": 1, "section": 2, "table": 3, "figure": 4}


class MentionResolver:
    """Resolve one mention only through the candidate-owned target index."""

    def __init__(
        self,
        *,
        target_index: TargetIndex,
        page_numbers: Mapping[str, int],
        target_document_order: Mapping[str, int],
        target_index_sha256: str,
        table_page_window: int,
        corpus_document_keys: Collection[str],
    ) -> None:
        self._target_index = target_index
        self._page_numbers = page_numbers
        self._target_document_order = target_document_order
        self._target_index_sha256 = target_index_sha256
        self._table_page_window = table_page_window
        self._corpus_document_keys = frozenset(corpus_document_keys)

    def resolve(
        self,
        mention: DetectedMention,
        *,
        source_text: str,
        source_page_id: str,
    ) -> Resolution:
        """Return ordered local candidates or one explicit unresolved reason."""
        if mention.kind is MentionKind.FIGURE:
            return Resolution((), UnresolvedReason.TARGET_TYPE_UNAVAILABLE)
        if mention.kind is MentionKind.TABLE and is_qualified_external_table_reference(
            source_text[mention.span.end :]
        ):
            return Resolution((), UnresolvedReason.QUALIFIED_EXTERNAL_TABLE)

        target_type = TARGET_TYPE_FOR_MENTION[mention.kind]
        matching = self._target_index.matching(mention.lookup_key, target_type)
        unfiltered_table_match = mention.kind is MentionKind.TABLE and bool(matching)
        if mention.kind is MentionKind.TABLE:
            matching = self._within_table_window(matching, source_page_id)

        candidates = self._group_candidates(matching, source_page_id)
        if candidates:
            return Resolution(tuple(candidates), None)
        if unfiltered_table_match:
            return Resolution((), UnresolvedReason.OUTSIDE_TABLE_WINDOW)
        if mention.kind is MentionKind.DOCUMENT:
            reason = (
                UnresolvedReason.DEFERRED_CROSS_DOCUMENT
                if mention.lookup_key in self._corpus_document_keys
                else UnresolvedReason.EXTERNAL_DOCUMENT
            )
            return Resolution((), reason)
        return Resolution((), UnresolvedReason.NO_LOCAL_ALIAS)

    def _within_table_window(
        self, entries: list[TargetIndexEntry], source_page_id: str
    ) -> list[TargetIndexEntry]:
        source_page = self._page_numbers[source_page_id]
        return [
            entry
            for entry in entries
            if entry.evidence_page_id is not None
            and abs(self._page_numbers[entry.evidence_page_id] - source_page)
            <= self._table_page_window
        ]

    def _group_candidates(
        self, entries: list[TargetIndexEntry], source_page_id: str
    ) -> list[JsonObject]:
        by_target: dict[str, list[TargetIndexEntry]] = defaultdict(list)
        for entry in entries:
            by_target[entry.target_record_id].append(entry)
        candidates = [self._candidate(group, source_page_id) for group in by_target.values()]
        candidates.sort(
            key=lambda candidate: (
                TARGET_TYPE_ORDER[candidate["target_type"]],
                self._target_document_order.get(candidate["target_record_id"], 10**9),
                candidate["target_record_id"],
            )
        )
        return candidates

    def _candidate(self, entries: list[TargetIndexEntry], source_page_id: str) -> JsonObject:
        ordered = sorted(entries, key=lambda entry: entry.alias_record_id)
        first = ordered[0]
        if len({entry.alias_origin for entry in ordered}) != 1:
            raise ValueError("one target candidate cannot mix alias origins")
        candidate: JsonObject = {
            "target_type": first.target_type,
            "alias_origin": first.alias_origin,
            "alias_record_ids": [entry.alias_record_id for entry in ordered],
            "target_record_id": first.target_record_id,
            "upstream_alias_record_ids": [
                entry.upstream_alias_record_id
                for entry in ordered
                if entry.upstream_alias_record_id is not None
            ],
            "upstream_target_record_id": first.upstream_target_record_id,
            "evidence": [
                {
                    "kind": _candidate_evidence_kind(first),
                    "refs": [
                        {
                            "path": "support/cross_reference_target_index.json",
                            "sha256": self._target_index_sha256,
                        }
                    ],
                }
            ],
        }
        if first.alias_origin == "v3_verified_table_label":
            if first.evidence_page_id is None:
                raise ValueError("verified table alias is missing its evidence page")
            candidate["page_distance"] = abs(
                self._page_numbers[first.evidence_page_id] - self._page_numbers[source_page_id]
            )
        return candidate


def _candidate_evidence_kind(entry: TargetIndexEntry) -> str:
    if entry.alias_origin == "v3_verified_table_label":
        return "verified_same_page_table_label"
    if entry.target_type == "section" and _numeric_lookup(entry.lookup_key):
        return "section_numeric_prefix"
    if entry.target_type == "section" and entry.lookup_key.startswith("appendix "):
        return "appendix_key_exact"
    if entry.target_type == "page":
        return "resolved_printed_page_exact"
    return "accepted_alias_exact"


def _numeric_lookup(value: str) -> bool:
    first = value[:1]
    return bool(first and first in "0123456789")
