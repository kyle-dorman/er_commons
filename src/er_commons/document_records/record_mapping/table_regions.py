"""Reconcile Docling layout regions with clean producer table artifacts."""

from __future__ import annotations

from pathlib import Path

from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.table_records import (
    ProducerTable,
    RegionTableMapping,
    parse_bbox,
    read_json_object,
    read_jsonl_objects,
)


def load_region_crosswalk(
    producer_root: Path,
    tables: tuple[ProducerTable, ...],
) -> tuple[RegionTableMapping, ...]:
    """Load the exact region-to-clean-table crosswalk for all routed pages."""
    table_root = producer_root / "tables"
    routes = read_jsonl_objects(producer_root / "routing" / "page_routes.jsonl")
    tables_by_page_region: dict[tuple[int, str], list[str]] = {}
    for table in tables:
        if table.region_id is not None:
            tables_by_page_region.setdefault((table.physical_pdf_page, table.region_id), []).append(
                table.table_id
            )
    mappings: list[RegionTableMapping] = []
    seen_clean_tables: set[str] = set()
    for route in routes:
        page = route.get("physical_pdf_page")
        page_route = route.get("route")
        observations = route.get("layout_table_observations")
        if (
            not isinstance(page, int)
            or isinstance(page, bool)
            or not isinstance(observations, list)
            or not all(isinstance(item, dict) for item in observations)
        ):
            raise MappingContractError("invalid routing table observations")
        if not observations:
            continue
        result = read_json_object(table_root / f"pages/page_{page:05d}/result.json")
        evidence = result.get("parser_evidence")
        result_tables = result.get("tables")
        if not isinstance(evidence, dict) or not isinstance(result_tables, list):
            raise MappingContractError(f"invalid page table result for page {page}")
        if page_route == "full_page_numeric":
            _validate_full_page_result(page, result_tables, tables)
            mappings.extend(_unmapped_full_page_regions(page=page, observations=observations))
            continue
        page_mappings, page_table_ids = _layout_page_mappings(
            page=page,
            observations=observations,
            evidence=evidence,
            result_tables=result_tables,
            tables=tables,
            tables_by_page_region=tables_by_page_region,
        )
        mappings.extend(page_mappings)
        seen_clean_tables.update(page_table_ids)
    expected_tables = {table.table_id for table in tables if table.region_id is not None}
    if seen_clean_tables != expected_tables:
        raise MappingContractError("region mappings do not exactly cover clean tables")
    return tuple(mappings)


def _layout_page_mappings(
    *,
    page: int,
    observations: list[object],
    evidence: dict[object, object],
    result_tables: list[object],
    tables: tuple[ProducerTable, ...],
    tables_by_page_region: dict[tuple[int, str], list[str]],
) -> tuple[list[RegionTableMapping], set[str]]:
    """Validate and map all layout regions for one routed page."""
    result_pairs = {
        (item.get("table_id"), item.get("region_id"))
        for item in result_tables
        if isinstance(item, dict)
    }
    if len(result_pairs) != len(result_tables) or not all(
        isinstance(table_id, str) and isinstance(region_id, str)
        for table_id, region_id in result_pairs
    ):
        raise MappingContractError(f"invalid result table references for page {page}")
    expected_pairs = {
        (table.table_id, table.region_id)
        for table in tables
        if table.physical_pdf_page == page and table.region_id is not None
    }
    if result_pairs != expected_pairs:
        raise MappingContractError(f"page result differs from tables.jsonl for page {page}")
    region_matches = evidence.get("region_matches")
    if not isinstance(region_matches, list) or not all(
        isinstance(item, dict) for item in region_matches
    ):
        raise MappingContractError(f"invalid region matches for page {page}")
    match_by_region = {item.get("region_id"): item.get("matched") for item in region_matches}
    mappings: list[RegionTableMapping] = []
    seen: set[str] = set()
    for region_index, observation in enumerate(observations, start=1):
        assert isinstance(observation, dict)
        region_id = f"layout_{region_index:03d}"
        raw_object_ref, provenance_index = _raw_region_identity(observation, page=page)
        clean_table_ids = tuple(tables_by_page_region.get((page, region_id), []))
        if len(clean_table_ids) > 1:
            raise MappingContractError(
                f"region maps to multiple clean tables: page {page} {region_id}"
            )
        matched = match_by_region.get(region_id)
        if not isinstance(matched, bool) or matched != bool(clean_table_ids):
            raise MappingContractError(
                f"region match differs from clean tables: page {page} {region_id}"
            )
        seen.update(clean_table_ids)
        mappings.append(
            RegionTableMapping(
                physical_pdf_page=page,
                region_id=region_id,
                raw_object_ref=raw_object_ref,
                provenance_index=provenance_index,
                bbox_pdf_points_bottom_left=parse_bbox(
                    observation.get("bbox_pdf_points_bottom_left"),
                    owner=f"page {page} {region_id}",
                ),
                clean_table_ids=clean_table_ids,
                unmapped_reason=None if clean_table_ids else "no_clean_table_match",
            )
        )
    return mappings, seen


def _validate_full_page_result(
    page: int,
    result_tables: list[object],
    tables: tuple[ProducerTable, ...],
) -> None:
    result_ids = {item.get("table_id") for item in result_tables if isinstance(item, dict)}
    expected_ids = {
        table.table_id
        for table in tables
        if table.physical_pdf_page == page and table.region_id is None
    }
    if (
        len(result_ids) != len(result_tables)
        or not all(isinstance(table_id, str) for table_id in result_ids)
        or any(
            item.get("region_id") is not None for item in result_tables if isinstance(item, dict)
        )
        or result_ids != expected_ids
    ):
        raise MappingContractError(f"full-page result differs from tables.jsonl for page {page}")


def _raw_region_identity(observation: dict[object, object], *, page: int) -> tuple[str, int]:
    raw_object_ref = observation.get("raw_object_ref")
    provenance_index = observation.get("provenance_index")
    if (
        not isinstance(raw_object_ref, str)
        or not isinstance(provenance_index, int)
        or isinstance(provenance_index, bool)
    ):
        raise MappingContractError(f"invalid raw table observation on page {page}")
    return raw_object_ref, provenance_index


def _unmapped_full_page_regions(
    *,
    page: int,
    observations: list[object],
) -> list[RegionTableMapping]:
    mappings: list[RegionTableMapping] = []
    for region_index, observation in enumerate(observations, start=1):
        assert isinstance(observation, dict)
        region_id = f"layout_{region_index:03d}"
        raw_object_ref, provenance_index = _raw_region_identity(observation, page=page)
        mappings.append(
            RegionTableMapping(
                physical_pdf_page=page,
                region_id=region_id,
                raw_object_ref=raw_object_ref,
                provenance_index=provenance_index,
                bbox_pdf_points_bottom_left=parse_bbox(
                    observation.get("bbox_pdf_points_bottom_left"),
                    owner=f"page {page} {region_id}",
                ),
                clean_table_ids=(),
                unmapped_reason="full_page_numeric_route",
            )
        )
    return mappings
