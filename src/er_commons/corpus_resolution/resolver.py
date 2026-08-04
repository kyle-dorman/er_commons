"""Reason-specific resolution against one sealed corpus target index."""

from __future__ import annotations

from er_commons.corpus_extraction.outcomes import DocumentTerminalEvidence
from er_commons.corpus_extraction_contract_v1_1.accounting import unavailable_source_digest
from er_commons.corpus_extraction_contract_v1_1.model import JsonObject
from er_commons.corpus_resolution.mentions import DerivedMention


class CorpusMentionResolver:
    """Resolve derived mentions and retain source-specific negative evidence."""

    def __init__(
        self,
        *,
        index: JsonObject,
        evidence: tuple[DocumentTerminalEvidence, ...],
        catalog_lookup: dict[str, tuple[JsonObject, ...]],
        catalog_ref: JsonObject,
        scope_id: str,
    ) -> None:
        self._index = index
        self._evidence = evidence
        self._catalog_lookup = catalog_lookup
        self._catalog_ref = catalog_ref
        self._scope_id = scope_id
        self._by_source = {str(item.source["source_id"]): item for item in evidence}
        self._unavailable = {
            str(row["source"]["source_id"]): row for row in index["unavailable_sources"]
        }

    def resolve_all(self, mentions: tuple[DerivedMention, ...]) -> list[JsonObject]:
        """Return exactly one ordered resolution for every derived mention."""
        return [self.resolve(mention) for mention in mentions]

    def resolve(self, mention: DerivedMention) -> JsonObject:
        """Resolve one mention without changing its stage-one candidate."""
        source = self._source_evidence(mention.source_candidate_id)
        matching = self._matching_targets(mention.record)
        base = self._base_record(mention.record, source, matching)
        if matching:
            return {
                **base,
                "status": "resolved" if len(matching) == 1 else "ambiguous",
                "unresolved_reason": None,
                "reason_evidence": None,
            }
        reason, evidence = self._unresolved_evidence(mention.record)
        return {
            **base,
            "status": "unresolved",
            "unresolved_reason": reason,
            "reason_evidence": evidence,
        }

    def _matching_targets(self, mention: JsonObject) -> list[JsonObject]:
        return [
            {
                "target_id": entry["target_id"],
                "target_source_id": entry["source_id"],
                "target_type": entry["target_type"],
            }
            for entry in self._index["entries"]
            if entry["lookup_key"] == mention["lookup_key"]
            and entry["target_type"] == "document"
            and entry["source_id"] in mention["intended_target_source_ids"]
        ]

    @staticmethod
    def _base_record(
        mention: JsonObject,
        source: DocumentTerminalEvidence,
        matching: list[JsonObject],
    ) -> JsonObject:
        return {
            "mention_id": mention["mention_id"],
            "source_candidate_id": source.candidate_id,
            "candidate_local_sequence": mention["candidate_local_sequence"],
            "lookup_key": mention["lookup_key"],
            "target_type": "document",
            "intended_target_source_ids": mention["intended_target_source_ids"],
            "source_inventory_before_ref": source.candidate_inventory_ref,
            "source_inventory_after_ref": source.candidate_inventory_ref,
            "candidate_targets": matching,
        }

    def _unresolved_evidence(self, mention: JsonObject) -> tuple[str, JsonObject]:
        intended = mention["intended_target_source_ids"]
        successful = [
            source_id
            for source_id in intended
            if source_id in self._by_source and self._by_source[source_id].candidate_id is not None
        ]
        failed = [source_id for source_id in intended if source_id in self._unavailable]
        if successful:
            source_id = successful[0]
            target = self._by_source[source_id]
            return "target_unavailable", {
                "reason": "target_unavailable",
                "target_source_id": source_id,
                "target_candidate_id": target.candidate_id,
                "index_id": self._index["index_id"],
                "entries_sha256": self._index["entries_ref"]["sha256"],
            }
        if failed:
            source_id = failed[0]
            return "target_source_failed", {
                "reason": "target_source_failed",
                "target_source_id": source_id,
                "unavailable_source_sha256": unavailable_source_digest(
                    self._unavailable[source_id]
                ),
            }
        source_record = self._catalog_source(mention)
        return "target_not_in_scope", {
            "reason": "target_not_in_scope",
            "target_source": source_record,
            "production_manifest_ref": self._catalog_ref,
            "scope_id": self._scope_id,
        }

    def _catalog_source(self, mention: JsonObject) -> JsonObject:
        return next(
            source
            for source_id in mention["intended_target_source_ids"]
            for source in self._catalog_lookup[str(mention["lookup_key"])]
            if source["source_id"] == source_id
        )

    def _source_evidence(self, candidate_id: str) -> DocumentTerminalEvidence:
        for item in self._evidence:
            if item.candidate_id == candidate_id:
                return item
        raise ValueError("mention ID is outside successful candidate namespaces")
