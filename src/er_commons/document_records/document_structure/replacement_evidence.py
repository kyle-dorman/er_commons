"""Explain producer text replaced by canonical tables, figures, or invalid geometry."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from er_commons.document_records.document_structure.errors import (
    DocumentStructureInvariantError,
)
from er_commons.document_records.record_mapping.provenance import (
    descendant_text_pointers,
    project_regions,
)
from er_commons.document_records.record_mapping.table_projection import (
    project_canonical_table_bundle,
)
from er_commons.document_records.record_mapping.tables import load_producer_table_bundle

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
    mapped_table_refs = {
        mapping.raw_object_ref
        for mapping in table_bundle.region_mappings
        if mapping.clean_table_ids
    }
    table_pointers = _replacement_text_pointers(
        baseline_document,
        (
            baseline_document["tables"][int(ref.rsplit("/", 1)[-1])]
            for ref in sorted(mapped_table_refs)
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
    for pointer in _invalid_geometry_text_pointers(baseline_document):
        key = key_by_pointer[pointer]
        if key in relevant_keys:
            dispositions.setdefault(key, "canonical_invalid_provenance_suppressed")
    return dispositions


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


def _invalid_geometry_text_pointers(document: JsonObject) -> set[str]:
    page_sizes = _page_sizes(document)
    page_ids = {page: str(page) for page in page_sizes}
    invalid: set[str] = set()
    for index, item in enumerate(document.get("texts", [])):
        pointer = f"#/texts/{index}"
        projection = project_regions(
            item=item, pointer=pointer, page_ids=page_ids, page_sizes=page_sizes
        )
        if not projection.regions:
            invalid.add(pointer)
    return invalid


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
