"""Named internal boundaries for canonical record construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from er_commons.canonical_extraction.layout import RECORD_COLLECTIONS

JsonRecord = dict[str, Any]


@dataclass(frozen=True)
class MappedRecord:
    """One canonical record and its explicit raw-lineage classification."""

    record_id: str
    mapping_role: str
    raw_links: tuple[JsonRecord, ...]


@dataclass(frozen=True)
class ContentRecordSet:
    """Canonical content records plus indexes needed by support records."""

    blocks: tuple[JsonRecord, ...]
    tables: tuple[JsonRecord, ...]
    table_families: tuple[JsonRecord, ...]
    figures: tuple[JsonRecord, ...]
    images: tuple[JsonRecord, ...]
    sections: tuple[JsonRecord, ...]
    page_content: dict[int, tuple[str, ...]]
    invalid_provenance: tuple[JsonRecord, ...]
    mapped_records: tuple[MappedRecord, ...]


@dataclass(frozen=True)
class SupportRecordSet:
    """Document, page, observation, and lineage records."""

    documents: tuple[JsonRecord, ...]
    pages: tuple[JsonRecord, ...]
    routing_observations: tuple[JsonRecord, ...]
    table_stage_observations: tuple[JsonRecord, ...]
    conversion_observations: tuple[JsonRecord, ...]
    raw_mappings: tuple[JsonRecord, ...]


@dataclass(frozen=True)
class CanonicalRecordSet:
    """Every schema-owned record collection in serialization order."""

    documents: tuple[JsonRecord, ...]
    pages: tuple[JsonRecord, ...]
    sections: tuple[JsonRecord, ...]
    blocks: tuple[JsonRecord, ...]
    tables: tuple[JsonRecord, ...]
    table_families: tuple[JsonRecord, ...]
    figures: tuple[JsonRecord, ...]
    images: tuple[JsonRecord, ...]
    assets: tuple[JsonRecord, ...]
    cross_references: tuple[JsonRecord, ...]
    routing_observations: tuple[JsonRecord, ...]
    table_stage_observations: tuple[JsonRecord, ...]
    conversion_observations: tuple[JsonRecord, ...]
    raw_mappings: tuple[JsonRecord, ...]

    @classmethod
    def assemble(
        cls,
        *,
        content: ContentRecordSet,
        support: SupportRecordSet,
        assets: tuple[JsonRecord, ...],
    ) -> CanonicalRecordSet:
        """Combine independently built record families without rediscovery."""
        return cls(
            documents=support.documents,
            pages=support.pages,
            sections=content.sections,
            blocks=content.blocks,
            tables=content.tables,
            table_families=content.table_families,
            figures=content.figures,
            images=content.images,
            assets=assets,
            cross_references=(),
            routing_observations=support.routing_observations,
            table_stage_observations=support.table_stage_observations,
            conversion_observations=support.conversion_observations,
            raw_mappings=support.raw_mappings,
        )

    def as_bundle_collections(self) -> dict[str, list[JsonRecord]]:
        """Return mutable JSON lists only at the schema-validation boundary."""
        return {
            collection.bundle_key: list(getattr(self, collection.bundle_key))
            for collection in RECORD_COLLECTIONS
        }

    def counts(self) -> dict[str, int]:
        """Return record counts keyed by the published bundle collection names."""
        return {
            collection.bundle_key: len(getattr(self, collection.bundle_key))
            for collection in RECORD_COLLECTIONS
        }


@dataclass(frozen=True)
class MaterializationReport:
    """Accounting facts collected while projecting producer evidence."""

    invalid_provenance: tuple[JsonRecord, ...]
    document_index_descendant_count: int
    producer_text_count: int
    emitted_text_count: int
    suppressed_text_count: int
    producer_furniture_count: int
    emitted_furniture_count: int
    suppressed_picture_furniture_pointers: tuple[str, ...]
