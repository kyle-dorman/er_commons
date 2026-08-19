"""Stable table-handoff imports and bundle-level orchestration."""

from pathlib import Path

from er_commons.document_records.record_mapping.table_artifacts import load_producer_tables
from er_commons.document_records.record_mapping.table_cleanup import clean_table_cells
from er_commons.document_records.record_mapping.table_families import load_table_families
from er_commons.document_records.record_mapping.table_records import (
    BoundingBox,
    CleanTableCell,
    FamilyEvidence,
    JsonObject,
    ProducerTable,
    ProducerTableBundle,
    ProducerTableFamily,
    RegionTableMapping,
    TableCleanupEvidence,
    TableParser,
)
from er_commons.document_records.record_mapping.table_regions import load_region_crosswalk


def load_producer_table_bundle(producer_root: Path) -> ProducerTableBundle:
    """Load the verified producer's complete table handoff from plain JSON."""
    table_root = producer_root / "tables"
    families, assignments = load_table_families(table_root)
    tables = load_producer_tables(table_root, assignments)
    mappings = load_region_crosswalk(producer_root, tables)
    return ProducerTableBundle(tables=tables, families=families, region_mappings=mappings)


__all__ = [
    "BoundingBox",
    "CleanTableCell",
    "FamilyEvidence",
    "JsonObject",
    "ProducerTable",
    "ProducerTableBundle",
    "ProducerTableFamily",
    "RegionTableMapping",
    "TableCleanupEvidence",
    "TableParser",
    "clean_table_cells",
    "load_producer_table_bundle",
]
