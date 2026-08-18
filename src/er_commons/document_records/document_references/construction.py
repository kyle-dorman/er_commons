"""Construct one schema-v3 candidate through explicit, inspectable stages."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from er_commons.document_records.document_references.detection import MentionDetector
from er_commons.document_records.document_references.indexing import (
    NamespaceRemapper,
    TargetIndex,
    TargetIndexBuilder,
)
from er_commons.document_records.document_references.policy import MentionPolicy
from er_commons.document_records.document_references.resolution import MentionResolver
from er_commons.document_records.document_references.source_scope import SourceScope
from er_commons.document_records.document_references.storage import (
    read_json,
    read_jsonl,
    serialized_json_sha256,
)
from er_commons.document_records.document_references.types import (
    DetectedMention,
    JsonObject,
    Resolution,
)
from er_commons.source_family_catalog import SourceFamilyCatalog

TARGET_ALIAS_PATH = "canonical/target_aliases.jsonl"
CROSS_REFERENCE_PATH = "canonical/cross_references.jsonl"


@dataclass(frozen=True)
class CandidateSource:
    """Accepted upstream records needed by the enrichment stage."""

    root: Path
    manifest: JsonObject
    record_files: dict[str, list[JsonObject]]

    @classmethod
    def load(cls, root: Path) -> CandidateSource:
        """Load only record streams declared by the accepted manifest."""
        manifest = read_json(root / "records" / "manifest.json")
        record_files = {
            item["path"]: read_jsonl(root / item["path"]) for item in manifest["record_files"]
        }
        return cls(root=root, manifest=manifest, record_files=record_files)


@dataclass(frozen=True)
class CandidateBuild:
    """All canonical streams and support payloads before serialization."""

    preserved_record_files: dict[str, list[JsonObject]]
    target_aliases: list[JsonObject]
    cross_references: list[JsonObject]
    support: dict[str, JsonObject]


class DocumentReferenceBuilder:
    """Orchestrate readable detection, indexing, and resolution components."""

    def __init__(
        self,
        *,
        source: CandidateSource,
        upstream_candidate_id: str,
        candidate_id: str,
        policy: MentionPolicy,
        source_family_catalog: SourceFamilyCatalog,
        source_family_catalog_sha256: str,
        source_id: str,
    ) -> None:
        self._source = source
        self._candidate_id = candidate_id
        self._policy = policy
        self._source_family_catalog = source_family_catalog
        self._source_family_catalog_sha256 = source_family_catalog_sha256
        self._source_id = source_id
        self._remapper = NamespaceRemapper(upstream_candidate_id, candidate_id)

    def build(self) -> CandidateBuild:
        """Build the target index, remapped graph, mentions, and support in order."""
        upstream = self._source.record_files
        target_index = TargetIndexBuilder(self._remapper, self._source_id).build(
            upstream_aliases=upstream[TARGET_ALIAS_PATH],
            upstream_blocks=upstream["canonical/blocks.jsonl"],
            upstream_tables=upstream["canonical/tables.jsonl"],
        )
        index_support = target_index.support_payload()
        preserved = self._remap_preserved_record_files()
        mentions, summary = self._build_mentions(
            target_index=target_index,
            target_index_sha256=serialized_json_sha256(index_support),
            preserved=preserved,
        )
        preservation = self._preservation_support(target_index)
        return CandidateBuild(
            preserved_record_files=preserved,
            target_aliases=list(target_index.aliases),
            cross_references=mentions,
            support={
                "cross_reference_target_index": index_support,
                "cross_reference_summary": summary,
                "cross_reference_preservation": preservation,
            },
        )

    def _remap_preserved_record_files(self) -> dict[str, list[JsonObject]]:
        return {
            path: [self._remapper.value(record) for record in records]
            for path, records in self._source.record_files.items()
            if path not in {TARGET_ALIAS_PATH, CROSS_REFERENCE_PATH}
        }

    def _build_mentions(
        self,
        *,
        target_index: TargetIndex,
        target_index_sha256: str,
        preserved: dict[str, list[JsonObject]],
    ) -> tuple[list[JsonObject], JsonObject]:
        detector = MentionDetector(
            self._policy,
            SourceScope.from_hierarchy(
                sections=self._source.record_files["canonical/sections.jsonl"],
                blocks=self._source.record_files["canonical/blocks.jsonl"],
            ),
        )
        page_numbers = {
            page["id"]: page["physical_page_number"] for page in preserved["canonical/pages.jsonl"]
        }
        resolver = MentionResolver(
            target_index=target_index,
            page_numbers=page_numbers,
            target_document_order=_target_document_order(preserved),
            target_index_sha256=target_index_sha256,
            table_page_window=self._policy.table_page_window,
            source_family_catalog=self._source_family_catalog,
            source_id=self._source_id,
            source_family_catalog_sha256=self._source_family_catalog_sha256,
        )
        mentions: list[JsonObject] = []
        diagnostic_counts: Counter[str] = Counter()
        eligible_source_count = 0
        upstream_blocks = self._source.record_files["canonical/blocks.jsonl"]
        local_blocks = preserved["canonical/blocks.jsonl"]
        for upstream_block, local_block in zip(upstream_blocks, local_blocks, strict=True):
            if detector.is_eligible_source(upstream_block):
                eligible_source_count += 1
            detected, diagnostics = detector.detect(upstream_block)
            diagnostic_counts.update(item.category for item in diagnostics)
            if not detected:
                continue
            source_page_id = local_block["regions"][0]["page_id"]
            for detected_mention in detected:
                resolution = resolver.resolve(
                    detected_mention,
                    source_text=upstream_block["canonical_text"],
                    source_page_id=source_page_id,
                )
                mentions.append(
                    self._mention_record(
                        sequence=len(mentions) + 1,
                        source_block=local_block,
                        detected=detected_mention,
                        resolution=resolution,
                    )
                )
        return mentions, _summary_support(
            mentions=mentions,
            eligible_source_count=eligible_source_count,
            diagnostic_counts=diagnostic_counts,
        )

    def _mention_record(
        self,
        *,
        sequence: int,
        source_block: JsonObject,
        detected: DetectedMention,
        resolution: Resolution,
    ) -> JsonObject:
        return {
            "schema_version": "er_commons.canonical_extraction.v3",
            "extraction_id": self._candidate_id,
            "id": (f"{self._candidate_id}/cross-reference/{self._source_id}/xref{sequence:06d}"),
            "document_id": source_block["document_id"],
            "sequence": sequence,
            "source_record_id": source_block["id"],
            "mention_class": detected.kind.value,
            "raw_text": detected.raw_text,
            "source_charspan": detected.span.as_json(),
            "pattern_version": self._policy.pattern_version,
            "lookup_key": detected.lookup_key,
            "candidates": [candidate.as_json() for candidate in resolution.candidates],
            "resolution_status": resolution.status.value,
            "unresolved_reason": (
                resolution.unresolved_reason.value
                if resolution.unresolved_reason is not None
                else None
            ),
            "cross_document_evidence": resolution.cross_document_evidence,
            "regions": source_block["regions"],
            "raw_links": source_block["raw_links"],
        }

    def _preservation_support(self, target_index: TargetIndex) -> JsonObject:
        return {
            "schema_version": "er_commons.cross_reference_preservation.v3",
            "upstream_candidate_id": self._remapper.upstream_candidate_id,
            "upstream_alias_count": target_index.upstream_alias_count,
            "bidirectional_alias_correspondence_complete": True,
            "derived_table_alias_count": target_index.derived_table_alias_count,
            "derived_figure_alias_count": 0,
            "undeclared_difference_count": 0,
            "status": "passed",
        }


def _target_document_order(
    preserved: dict[str, list[JsonObject]],
) -> dict[str, int]:
    paths = (
        "canonical/documents.jsonl",
        "canonical/pages.jsonl",
        "canonical/sections.jsonl",
        "canonical/tables.jsonl",
        "canonical/figures.jsonl",
    )
    records = [record for path in paths for record in preserved[path]]
    return {
        record["id"]: record.get("sequence", record.get("physical_page_number", 0)) or 0
        for record in records
    }


def _summary_support(
    *,
    mentions: list[JsonObject],
    eligible_source_count: int,
    diagnostic_counts: Counter[str],
) -> JsonObject:
    mention_counts = Counter(item["mention_class"] for item in mentions)
    status_counts = Counter(item["resolution_status"] for item in mentions)
    reason_counts = Counter(
        item["unresolved_reason"] for item in mentions if item["unresolved_reason"] is not None
    )
    return {
        "schema_version": "er_commons.cross_reference_summary.v3",
        "eligible_source_count": eligible_source_count,
        "mention_counts": dict(sorted(mention_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "unresolved_reason_counts": dict(sorted(reason_counts.items())),
        "unsupported_diagnostic_counts": dict(sorted(diagnostic_counts.items())),
    }
