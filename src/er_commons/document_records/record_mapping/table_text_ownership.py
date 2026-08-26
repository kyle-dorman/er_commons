"""Assign duplicate native text to validated full-page producer tables."""

from __future__ import annotations

from collections.abc import Mapping, Set
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Literal, cast

from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.provenance import ProvenanceProjection
from er_commons.document_records.record_mapping.tables import BoundingBox, ProducerTable

TABLE_TEXT_OWNERSHIP_REASON: Final = "single_full_page_table_contains_all_text_regions"
TableTextOwnershipReason = Literal["single_full_page_table_contains_all_text_regions"]


@dataclass(frozen=True)
class ProjectedTextRegion:
    """Typed page and geometry needed for one table-ownership decision."""

    page_id: str
    bbox: BoundingBox

    def as_json(self) -> dict[str, object]:
        """Return stable page-local geometry for published diagnostics."""
        return {
            "page_id": self.page_id,
            "bbox_pdf_points_bottom_left": list(self.bbox),
        }


@dataclass(frozen=True)
class TableTextOwnershipDecision:
    """Evidence explaining one native-text suppression by one clean table."""

    text_pointer: str
    producer_table_id: str
    physical_pdf_page: int
    table_bbox_pdf_points_bottom_left: BoundingBox
    text_regions: tuple[ProjectedTextRegion, ...]
    reason: TableTextOwnershipReason

    def as_json(self) -> dict[str, object]:
        """Return the versioned published diagnostic representation."""
        return {
            "schema_version": "er_commons.table_text_ownership_observation.v1",
            "text_pointer": self.text_pointer,
            "producer_table_id": self.producer_table_id,
            "physical_pdf_page": self.physical_pdf_page,
            "table_bbox_pdf_points_bottom_left": list(self.table_bbox_pdf_points_bottom_left),
            "text_regions": [region.as_json() for region in self.text_regions],
            "reason": self.reason,
        }


@dataclass(frozen=True)
class TableTextOwnership:
    """Exact native-text pointers claimed by validated producer tables."""

    decisions: tuple[TableTextOwnershipDecision, ...]

    @property
    def table_id_by_text_pointer(self) -> Mapping[str, str]:
        """Return the immutable traversal suppression index."""
        return MappingProxyType(
            {decision.text_pointer: decision.producer_table_id for decision in self.decisions}
        )


def assign_table_text_ownership(
    *,
    document: Mapping[str, Any],
    tables: tuple[ProducerTable, ...],
    projections: Mapping[str, ProvenanceProjection],
    page_ids: Mapping[int, str],
    document_index_descendants: Set[str],
) -> TableTextOwnership:
    """Assign text only when one full-page table contains every valid region.

    Producer tables have already passed clean-grid and CSV validation. This
    policy adds the canonical ownership decision: body text is claimed only
    when its provenance is entirely valid and exactly one full-page table
    contains every projected region. Ambiguous or partial coverage remains
    canonical text.
    """
    eligible_tables = tuple(table for table in tables if table.route == "full_page_numeric")
    if not eligible_tables:
        return TableTextOwnership(())

    page_id_by_table = _table_page_ids(eligible_tables, page_ids)
    texts = document.get("texts")
    if not isinstance(texts, list):
        raise MappingContractError("saved Docling document has no text collection")

    decisions: list[TableTextOwnershipDecision] = []
    for pointer, projection in projections.items():
        item = _text_item(texts, pointer)
        if not _may_be_table_owned(
            pointer=pointer,
            item=item,
            projection=projection,
            document_index_descendants=document_index_descendants,
        ):
            continue
        regions = tuple(
            _projected_region(pointer, index, region)
            for index, region in enumerate(projection.regions)
        )
        owners = [
            table
            for table in eligible_tables
            if _table_contains_every_region(table, page_id_by_table[table.table_id], regions)
        ]
        if len(owners) == 1:
            owner = owners[0]
            decisions.append(
                TableTextOwnershipDecision(
                    text_pointer=pointer,
                    producer_table_id=owner.table_id,
                    physical_pdf_page=owner.physical_pdf_page,
                    table_bbox_pdf_points_bottom_left=owner.bbox_pdf_points_bottom_left,
                    text_regions=regions,
                    reason=TABLE_TEXT_OWNERSHIP_REASON,
                )
            )

    return TableTextOwnership(tuple(sorted(decisions, key=lambda item: item.text_pointer)))


def _table_page_ids(
    tables: tuple[ProducerTable, ...], page_ids: Mapping[int, str]
) -> dict[str, str]:
    """Resolve every eligible table to a canonical page with useful errors."""
    resolved: dict[str, str] = {}
    for table in tables:
        page_id = page_ids.get(table.physical_pdf_page)
        if page_id is None:
            raise MappingContractError(
                "full-page table has no canonical page: "
                f"table_id={table.table_id} physical_pdf_page={table.physical_pdf_page}"
            )
        resolved[table.table_id] = page_id
    return resolved


def _text_item(texts: list[Any], pointer: str) -> Mapping[str, Any]:
    """Resolve one projected text pointer with contextual contract errors."""
    prefix = "#/texts/"
    raw_index = pointer.removeprefix(prefix)
    if not pointer.startswith(prefix) or not raw_index.isdigit():
        raise MappingContractError(f"invalid projected text pointer: {pointer}")
    index = int(raw_index)
    if index >= len(texts):
        raise MappingContractError(f"projected text pointer is unresolved: {pointer}")
    item = texts[index]
    if not isinstance(item, dict):
        raise MappingContractError(f"projected text pointer is unresolved: {pointer}")
    return cast(Mapping[str, Any], item)


def _may_be_table_owned(
    *,
    pointer: str,
    item: Mapping[str, Any],
    projection: ProvenanceProjection,
    document_index_descendants: Set[str],
) -> bool:
    """Apply non-geometric exclusions before attempting table ownership."""
    return (
        pointer not in document_index_descendants
        and item.get("content_layer") == "body"
        and not projection.rejected
        and bool(projection.regions)
    )


def _projected_region(pointer: str, index: int, region: Mapping[str, Any]) -> ProjectedTextRegion:
    """Read the typed subset of one already validated provenance projection."""
    page_id = region.get("page_id")
    bbox = region.get("bbox")
    if (
        not isinstance(page_id, str)
        or not isinstance(bbox, list)
        or len(bbox) != 4
        or not all(isinstance(value, float) for value in bbox)
    ):
        raise MappingContractError(
            f"invalid projected text region: pointer={pointer} provenance_index={index}"
        )
    return ProjectedTextRegion(
        page_id=page_id,
        bbox=(bbox[0], bbox[1], bbox[2], bbox[3]),
    )


def _table_contains_every_region(
    table: ProducerTable,
    table_page_id: str,
    regions: tuple[ProjectedTextRegion, ...],
) -> bool:
    """Require one table to own every region of a native text item."""
    return all(
        region.page_id == table_page_id
        and _bbox_contains(table.bbox_pdf_points_bottom_left, region.bbox)
        for region in regions
    )


def _bbox_contains(container: BoundingBox, candidate: BoundingBox) -> bool:
    """Return whether candidate geometry is fully inside container geometry."""
    return (
        container[0] <= candidate[0]
        and container[1] <= candidate[1]
        and candidate[2] <= container[2]
        and candidate[3] <= container[3]
    )


__all__ = [
    "TABLE_TEXT_OWNERSHIP_REASON",
    "TableTextOwnership",
    "TableTextOwnershipDecision",
    "assign_table_text_ownership",
]
