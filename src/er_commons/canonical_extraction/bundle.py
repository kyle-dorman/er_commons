"""A readable indexed view over a schema-valid extraction bundle."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import Any

from er_commons.canonical_extraction.layout import RECORD_COLLECTIONS

Record = dict[str, Any]
Bundle = dict[str, Any]

SINGLE_REFERENCE_FIELDS = {
    "document_id": {"document"},
    "section_id": {"section"},
    "parent_section_id": {"section"},
    "heading_block_id": {"block"},
    "routing_observation_id": {"routing-observation"},
    "table_family_id": {"table-family"},
    "asset_id": {"asset"},
    "source_record_id": {"block", "table", "figure"},
    "page_id": {"page"},
    "raw_document_asset_id": {"asset"},
    "canonical_record_id": {
        "section",
        "block",
        "table",
        "table-family",
        "figure",
        "image",
    },
}
LIST_REFERENCE_FIELDS = {
    "page_ids": {"page"},
    "conversion_observation_ids": {"conversion-observation"},
    "ordered_content_ids": {"block", "table", "figure"},
    "table_stage_observation_ids": {"table-stage-observation"},
    "ordered_child_ids": {"section", "block", "table", "figure"},
    "member_table_ids": {"table"},
    "caption_block_ids": {"block"},
    "image_ids": {"image"},
    "target_record_ids": {"section", "block", "table", "figure"},
    "canonical_table_ids": {"table"},
}


@dataclass(frozen=True)
class BundleView:
    """Cache indexes used by several independent contract checks."""

    bundle: Bundle
    records: tuple[Record, ...] = field(init=False)
    records_by_id: dict[str, Record] = field(init=False)
    documents_by_id: dict[str, Record] = field(init=False)
    pages_by_id: dict[str, Record] = field(init=False)
    page_document_by_id: dict[str, str] = field(init=False)

    def __post_init__(self) -> None:
        records = tuple(
            record
            for collection in RECORD_COLLECTIONS
            for record in self.bundle[collection.bundle_key]
        )
        documents_by_id = {document["id"]: document for document in self.bundle["documents"]}
        pages_by_id = {page["id"]: page for page in self.bundle["pages"]}
        object.__setattr__(self, "records", records)
        object.__setattr__(
            self,
            "records_by_id",
            {record["id"]: record for record in records},
        )
        object.__setattr__(self, "documents_by_id", documents_by_id)
        object.__setattr__(self, "pages_by_id", pages_by_id)
        object.__setattr__(
            self,
            "page_document_by_id",
            {page_id: page["document_id"] for page_id, page in pages_by_id.items()},
        )

    def from_collections(self, *bundle_keys: str) -> Iterator[Record]:
        """Yield records from selected bundle collections in the given order."""
        for bundle_key in bundle_keys:
            yield from self.bundle[bundle_key]


def references(record: Record) -> Iterator[str]:
    """Yield every canonical record ID referenced by one record."""
    for field_name in SINGLE_REFERENCE_FIELDS:
        value = record.get(field_name)
        if isinstance(value, str):
            yield value
    for field_name in LIST_REFERENCE_FIELDS:
        yield from record.get(field_name, [])
    for region in regions(record):
        yield region["page_id"]
    for raw_link in raw_links(record):
        yield raw_link["asset_id"]


def typed_references(record: Record) -> Iterator[tuple[str, set[str]]]:
    """Yield each canonical reference with its permitted target record types."""
    for field_name, allowed_types in SINGLE_REFERENCE_FIELDS.items():
        value = record.get(field_name)
        if isinstance(value, str):
            yield value, allowed_types
    for field_name, allowed_types in LIST_REFERENCE_FIELDS.items():
        for value in record.get(field_name, []):
            yield value, allowed_types
    for region in regions(record):
        yield region["page_id"], {"page"}
    for raw_link in raw_links(record):
        yield raw_link["asset_id"], {"asset"}


def regions(record: Record) -> Iterator[Record]:
    """Yield direct regions and table-cell regions owned by a record."""
    yield from record.get("regions", [])
    for cell in record.get("cells", []):
        yield cell["region"]


def raw_links(record: Record) -> Iterator[Record]:
    """Yield all supported shapes of producer-to-canonical links."""
    yield from record.get("raw_links", [])
    yield from record.get("docling_table_region_raw_links", [])
    source_region = record.get("source_region_raw_link")
    if source_region is not None:
        yield source_region


def find_key(value: Any, forbidden_keys: set[str], path: str = "$") -> str | None:
    """Return the first nested forbidden key path, if one exists."""
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in forbidden_keys:
                return child_path
            found = find_key(child, forbidden_keys, child_path)
            if found is not None:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = find_key(child, forbidden_keys, f"{path}[{index}]")
            if found is not None:
                return found
    return None


def ids(records: Iterable[Record]) -> list[str]:
    """Return record IDs while preserving serialization order."""
    return [record["id"] for record in records]
