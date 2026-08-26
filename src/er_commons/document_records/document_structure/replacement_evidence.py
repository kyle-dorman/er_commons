"""Explain producer text replaced by canonical tables, figures, or invalid geometry."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from er_commons.document_records.document_structure.errors import (
    DocumentStructureInvariantError,
)
from er_commons.document_records.record_mapping.provenance import (
    ProvenanceProjection,
    descendant_text_pointers,
    project_regions,
)
from er_commons.document_records.record_mapping.table_projection import (
    project_canonical_table_bundle,
)
from er_commons.document_records.record_mapping.table_text_ownership import (
    assign_table_text_ownership,
)
from er_commons.document_records.record_mapping.tables import (
    ProducerTable,
    load_producer_table_bundle,
)

JsonObject = dict[str, Any]


def hierarchy_relevant_keys(hierarchy: JsonObject, blocks: list[JsonObject]) -> set[str]:
    """Return every correction-controlled key plus retained furniture keys."""
    keys = set(hierarchy["roots"])
    keys.update(edge["child_key"] for edge in hierarchy["edges"])
    keys.update(item["item_key"] for item in hierarchy["direct_membership"])
    keys.update(hierarchy["unassigned_content"])
    keys.update(
        item["stable_item_key"] for item in blocks if item["semantic_placement"] == "furniture"
    )
    return keys


def replacement_dispositions(
    *,
    baseline_document: JsonObject,
    producer_root: Path,
    key_by_pointer: dict[str, str],
    relevant_keys: set[str],
) -> dict[str, str]:
    """Explain text hidden beneath canonical table and figure replacements."""
    table_bundle = project_canonical_table_bundle(
        baseline_document, load_producer_table_bundle(producer_root)
    )
    page_sizes = _page_sizes(baseline_document)
    page_ids = {page: str(page) for page in page_sizes}
    text_projections = _text_projections(baseline_document, page_ids, page_sizes)
    replaced_table_refs = {
        mapping.raw_object_ref
        for mapping in table_bundle.region_mappings
        if (mapping.clean_table_ids or mapping.unmapped_reason == "full_page_numeric_route")
        and mapping.raw_object_ref is not None
    }
    table_pointers = _replacement_text_pointers(
        baseline_document,
        (
            baseline_document["tables"][int(ref.rsplit("/", 1)[-1])]
            for ref in sorted(replaced_table_refs)
        ),
    )
    picture_pointers = _replacement_text_pointers(
        baseline_document, iter(baseline_document["pictures"])
    )
    dispositions = _dispositions_for_pointers(
        table_pointers,
        key_by_pointer,
        relevant_keys,
        "canonical_table_replacement_descendant",
    )
    dispositions.update(
        _dispositions_for_pointers(
            picture_pointers,
            key_by_pointer,
            relevant_keys,
            "canonical_figure_suppressed_descendant",
        )
    )
    dispositions.update(
        _dispositions_for_pointers(
            set(
                _geometry_owned_text_by_pointer(
                    baseline_document=baseline_document,
                    tables=table_bundle.tables,
                    projections=text_projections,
                    page_ids=page_ids,
                )
            ),
            key_by_pointer,
            relevant_keys,
            "canonical_table_geometry_owned_text",
        )
    )
    for pointer in _invalid_geometry_text_pointers(text_projections):
        key = key_by_pointer[pointer]
        if key in relevant_keys:
            dispositions.setdefault(key, "canonical_invalid_provenance_suppressed")
    return dispositions


def _geometry_owned_text_by_pointer(
    *,
    baseline_document: JsonObject,
    tables: tuple[ProducerTable, ...],
    projections: dict[str, ProvenanceProjection],
    page_ids: dict[int, str],
) -> dict[str, str]:
    """Reuse canonical table ownership policy for downstream bridge evidence."""
    return dict(
        assign_table_text_ownership(
            document=baseline_document,
            tables=tables,
            projections=projections,
            page_ids=page_ids,
            document_index_descendants=_document_index_descendants(baseline_document),
        ).table_id_by_text_pointer
    )


def _text_projections(
    document: JsonObject,
    page_ids: dict[int, str],
    page_sizes: dict[int, tuple[float, float]],
) -> dict[str, ProvenanceProjection]:
    """Project all baseline text once for the shared ownership classifier."""
    projections: dict[str, ProvenanceProjection] = {}
    for index, item in enumerate(document.get("texts", [])):
        pointer = f"#/texts/{index}"
        projections[pointer] = project_regions(
            item=item,
            pointer=pointer,
            page_ids=page_ids,
            page_sizes=page_sizes,
        )
    return projections


def _document_index_descendants(document: JsonObject) -> set[str]:
    """Identify index text excluded from geometry-based table ownership."""
    pointers: set[str] = set()
    for table in document.get("tables", []):
        if table.get("label") == "document_index":
            pointers.update(descendant_text_pointers(document, table.get("children", [])))
    return pointers


def _replacement_text_pointers(document: JsonObject, owners: Iterable[JsonObject]) -> set[str]:
    pointers: set[str] = set()
    for owner in owners:
        captions = {item["$ref"] for item in owner.get("captions", [])}
        roots = [item for item in owner["children"] if item["$ref"] not in captions]
        pointers.update(descendant_text_pointers(document, roots))
    return pointers


def _dispositions_for_pointers(
    pointers: set[str],
    key_by_pointer: dict[str, str],
    relevant_keys: set[str],
    disposition: str,
) -> dict[str, str]:
    return {
        key_by_pointer[pointer]: disposition
        for pointer in pointers
        if key_by_pointer[pointer] in relevant_keys
    }


def _invalid_geometry_text_pointers(
    projections: dict[str, ProvenanceProjection],
) -> set[str]:
    """Return text with no valid canonical region from shared projections."""
    return {pointer for pointer, projection in projections.items() if not projection.regions}


def _page_sizes(document: JsonObject) -> dict[int, tuple[float, float]]:
    pages = document.get("pages")
    if not isinstance(pages, dict):
        raise DocumentStructureInvariantError(
            stage="producer evidence",
            invariant="producer pages support geometry projection",
            expected="page mapping",
            observed=type(pages).__name__,
            subject="baseline producer document",
        )
    try:
        return {
            int(page): (float(item["size"]["width"]), float(item["size"]["height"]))
            for page, item in pages.items()
        }
    except (KeyError, TypeError, ValueError) as error:
        raise DocumentStructureInvariantError(
            stage="producer evidence",
            invariant="producer page sizes are valid",
            expected="positive numeric dimensions",
            observed="invalid page size",
            subject="baseline producer document",
        ) from error
