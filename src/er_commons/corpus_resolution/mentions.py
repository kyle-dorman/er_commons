"""Independent derivation of eligible cross-document mention inputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_extraction.outcomes import DocumentTerminalEvidence
from er_commons.corpus_extraction_contract_v1_1.checks import canonical_sha256
from er_commons.corpus_extraction_contract_v1_1.model import JsonObject
from er_commons.corpus_resolution.storage import read_jsonl


@dataclass(frozen=True)
class DerivedMention:
    """One persisted eligible mention plus its private source ownership."""

    record: JsonObject
    source_candidate_id: str


@dataclass(frozen=True)
class MentionManifest:
    """Exact candidate coverage and ordered eligible mentions."""

    candidates: list[JsonObject]
    mentions: tuple[DerivedMention, ...]

    def as_record(self, *, index_id: str, catalog_ref: JsonObject) -> JsonObject:
        """Serialize the closed manifest without private runtime ownership fields."""
        records = [mention.record for mention in self.mentions]
        return {
            "schema_version": "er_commons.corpus_mention_input_manifest.v1_1",
            "index_id": index_id,
            "corpus_catalog_ref": catalog_ref,
            "candidate_count": len(self.candidates),
            "candidates": self.candidates,
            "eligible_mention_count": len(records),
            "eligible_mentions_sha256": canonical_sha256(records),
        }


class MentionManifestBuilder:
    """Enumerate eligible mentions directly from successful candidate bytes."""

    def __init__(
        self,
        extraction_root: Path,
        catalog_lookup: dict[str, tuple[JsonObject, ...]],
    ) -> None:
        self._extraction_root = extraction_root
        self._catalog_lookup = catalog_lookup

    def build(self, evidence: tuple[DocumentTerminalEvidence, ...]) -> MentionManifest:
        """Cover every successful candidate, including zero-mention candidates."""
        candidates: list[JsonObject] = []
        mentions: list[DerivedMention] = []
        for item in evidence:
            if item.candidate_id is None:
                continue
            candidate, derived = self._candidate(item)
            candidates.append(candidate)
            mentions.extend(derived)
        return MentionManifest(candidates, tuple(mentions))

    def _candidate(self, item: DocumentTerminalEvidence) -> tuple[JsonObject, list[DerivedMention]]:
        if (
            item.cross_references_ref is None
            or item.document_completion_ref is None
            or item.candidate_inventory_ref is None
            or item.candidate_id is None
        ):
            raise ValueError("successful evidence lacks mention inputs")
        path = self._extraction_root / str(item.cross_references_ref["path"])
        eligible = [
            self._eligible_record(row)
            for row in read_jsonl(path)
            if row.get("resolution_status") == "unresolved"
            and row.get("unresolved_reason") == "deferred_cross_document"
        ]
        eligible.sort(key=lambda row: (row["candidate_local_sequence"], row["mention_id"]))
        candidate: JsonObject = {
            "source_id": item.source["source_id"],
            "source_ordinal": item.source_ordinal,
            "candidate_id": item.candidate_id,
            "document_completion_ref": item.document_completion_ref,
            "candidate_inventory_ref": item.candidate_inventory_ref,
            "cross_references_ref": item.cross_references_ref,
            "eligible_mention_count": len(eligible),
            "eligible_mentions": eligible,
        }
        return candidate, [DerivedMention(record, item.candidate_id) for record in eligible]

    def _eligible_record(self, row: JsonObject) -> JsonObject:
        sources = self._catalog_lookup.get(str(row["lookup_key"]))
        if not sources:
            raise ValueError("deferred mention lacks sealed catalog ownership")
        return {
            "mention_id": row["id"],
            "candidate_local_sequence": row["sequence"],
            "document_id": row["document_id"],
            "mention_class": "document",
            "lookup_key": row["lookup_key"],
            "intended_target_source_ids": [source["source_id"] for source in sources],
        }
