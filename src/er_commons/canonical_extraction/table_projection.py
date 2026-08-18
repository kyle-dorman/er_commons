"""Derive the canonical table view without rewriting sealed producer evidence."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from er_commons.canonical_extraction.errors import ContractError
from er_commons.canonical_extraction.tables import ProducerTableBundle

DOCUMENT_INDEX_UNMAPPED_REASON = "document_index_not_canonical_table"


def _docling_table(document: dict[str, Any], pointer: str) -> dict[str, Any]:
    """Resolve one verified producer table pointer against saved Docling JSON."""
    parts = pointer.split("/")
    if len(parts) != 3 or parts[:2] != ["#", "tables"] or not parts[2].isdigit():
        raise ContractError(f"invalid Docling table pointer in region mapping: {pointer}")
    tables = document.get("tables")
    index = int(parts[2])
    if not isinstance(tables, list) or index >= len(tables):
        raise ContractError(f"unknown Docling table pointer in region mapping: {pointer}")
    table = tables[index]
    if not isinstance(table, dict):
        raise ContractError(f"Docling table pointer is not an object: {pointer}")
    return table


def project_canonical_table_bundle(
    document: dict[str, Any],
    producer_bundle: ProducerTableBundle,
) -> ProducerTableBundle:
    """Exclude document indexes from canonical tables while preserving producer bytes."""
    excluded_table_ids: set[str] = set()
    seen_pointers: set[str] = set()
    projected_mappings = []
    for mapping in producer_bundle.region_mappings:
        if mapping.raw_object_ref in seen_pointers:
            raise ContractError(
                f"duplicate Docling table pointer in region mappings: {mapping.raw_object_ref}"
            )
        seen_pointers.add(mapping.raw_object_ref)
        table = _docling_table(document, mapping.raw_object_ref)
        if table.get("label") != "document_index":
            projected_mappings.append(mapping)
            continue
        excluded_table_ids.update(mapping.clean_table_ids)
        projected_mappings.append(
            replace(
                mapping,
                clean_table_ids=(),
                unmapped_reason=DOCUMENT_INDEX_UNMAPPED_REASON,
            )
        )

    producer_table_ids = {table.table_id for table in producer_bundle.tables}
    if not excluded_table_ids <= producer_table_ids:
        unknown = excluded_table_ids - producer_table_ids
        raise ContractError(
            f"document-index projection references unknown clean tables: {sorted(unknown)}"
        )

    projected_families = []
    for family in producer_bundle.families:
        family_ids = set(family.table_ids)
        overlap = family_ids & excluded_table_ids
        if not overlap:
            projected_families.append(family)
            continue
        if overlap != family_ids:
            raise ContractError(
                "document-index projection would split a mixed table family: "
                f"family={family.family_id} excluded={sorted(overlap)}"
            )

    projected_tables = tuple(
        table for table in producer_bundle.tables if table.table_id not in excluded_table_ids
    )
    projected_family_ids = {family.family_id for family in projected_families}
    if any(table.family_id not in projected_family_ids for table in projected_tables):
        raise ContractError("canonical table projection left a table without a family")

    remaining_mapping_ids = {
        table_id for mapping in projected_mappings for table_id in mapping.clean_table_ids
    }
    remaining_table_ids = {table.table_id for table in projected_tables}
    if remaining_mapping_ids != remaining_table_ids:
        raise ContractError(
            "canonical table projection does not exactly cover retained tables: "
            f"mapped={sorted(remaining_mapping_ids)} retained={sorted(remaining_table_ids)}"
        )

    return ProducerTableBundle(
        tables=projected_tables,
        families=tuple(projected_families),
        region_mappings=tuple(projected_mappings),
    )
