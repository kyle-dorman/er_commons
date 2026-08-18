"""Independent derivation of eligible cross-document mention inputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.collection_processing.contract import JsonObject, canonical_sha256
from er_commons.collection_processing.storage import read_jsonl
from er_commons.document_publication.published_document import DocumentTerminalEvidence
from er_commons.source_family_catalog import SourceFamilyCatalog, normalize_reference_alias


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

    def as_record(self, *, index_id: str, source_family_catalog_ref: JsonObject) -> JsonObject:
        """Serialize the closed manifest without private runtime ownership fields."""
        records = [mention.record for mention in self.mentions]
        return {
            "schema_version": "er_commons.cross_document_mention_manifest.v2",
            "index_id": index_id,
            "source_family_catalog_ref": source_family_catalog_ref,
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
        catalog: SourceFamilyCatalog,
        catalog_sha256: str,
    ) -> None:
        self._extraction_root = extraction_root
        self._catalog = catalog
        self._catalog_sha256 = catalog_sha256

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
            self._eligible_record(row, source_id=str(item.source["source_id"]))
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

    def _eligible_record(self, row: JsonObject, *, source_id: str) -> JsonObject:
        evidence = row.get("cross_document_evidence")
        if not isinstance(evidence, dict):
            raise ValueError("deferred mention lacks explicit catalog evidence")
        if evidence.get("catalog_sha256") != self._catalog_sha256:
            raise ValueError("deferred mention catalog checksum differs")
        alias = normalize_reference_alias(str(row["lookup_key"]))
        if evidence.get("matched_alias") != alias:
            raise ValueError("deferred mention matched alias differs")
        origin = self._catalog.by_source_id.get(source_id)
        if origin is None:
            raise ValueError("deferred mention source is absent from catalog")
        sources = tuple(
            target
            for target in self._catalog.alias_lookup.get(alias, ())
            if target.source_id != source_id
            and target.family_root_source_id == origin.family_root_source_id
        )
        intended = [source.source_id for source in sources]
        if evidence.get("intended_target_source_ids") != intended:
            raise ValueError("deferred mention intended sources differ from catalog")
        mention_class = str(row["mention_class"])
        if mention_class not in {"appendix", "document"}:
            raise ValueError("deferred mention class is not cross-document eligible")
        return {
            "mention_id": row["id"],
            "candidate_local_sequence": row["sequence"],
            "document_id": row["document_id"],
            "mention_class": mention_class,
            "lookup_key": row["lookup_key"],
            "cross_document_evidence": evidence,
            "intended_target_source_ids": intended,
        }
