"""Names and ordering of the files that make up an extraction bundle."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecordCollection:
    """Connect one record type in an ID to its plural bundle collection."""

    record_type: str
    bundle_key: str


# This order is part of the v1 serialization contract. It matches the order of
# ``manifest.record_files`` and therefore must not be alphabetized.
RECORD_COLLECTIONS = (
    RecordCollection("document", "documents"),
    RecordCollection("page", "pages"),
    RecordCollection("section", "sections"),
    RecordCollection("block", "blocks"),
    RecordCollection("table", "tables"),
    RecordCollection("table-family", "table_families"),
    RecordCollection("figure", "figures"),
    RecordCollection("image", "images"),
    RecordCollection("asset", "assets"),
    RecordCollection("cross-reference", "cross_references"),
    RecordCollection("routing-observation", "routing_observations"),
    RecordCollection("table-stage-observation", "table_stage_observations"),
    RecordCollection("conversion-observation", "conversion_observations"),
)

RECORD_TYPES = frozenset(item.record_type for item in RECORD_COLLECTIONS)
COLLECTION_BY_RECORD_TYPE = {item.record_type: item.bundle_key for item in RECORD_COLLECTIONS}
