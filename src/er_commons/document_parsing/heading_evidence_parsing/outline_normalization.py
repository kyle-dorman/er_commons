"""Repair the bounded raw-object defect in malformed PDF outline folders."""

from __future__ import annotations

from typing import Any

from pypdf.generic import (
    ArrayObject,
    FloatObject,
    IndirectObject,
    NameObject,
    NullObject,
    NumberObject,
)

from er_commons.document_parsing.heading_evidence_parsing.errors import (
    HierarchyInferenceContractError,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_types import RawReferenceKey
from er_commons.document_parsing.heading_evidence_parsing.text_evidence import normalize_text


def normalize_malformed_filename_destinations(reader: Any) -> frozenset[RawReferenceKey]:
    """Make null-page numeric-fit filename containers readable in memory only."""
    try:
        root = _resolve_pdf_object(reader.trailer["/Root"])
        outlines = _resolve_pdf_object(root.get("/Outlines"))
        first = outlines.get("/First")
    except (AttributeError, KeyError, TypeError):
        return frozenset()
    if first is None:
        return frozenset()

    normalized: set[RawReferenceKey] = set()
    visited: set[RawReferenceKey | tuple[str, int]] = set()

    def walk(first_reference: Any) -> None:
        current = first_reference
        while current is not None:
            reference_key = _raw_object_key(current)
            if reference_key in visited:
                raise HierarchyInferenceContractError("source PDF outline contains a cycle")
            visited.add(reference_key)
            node = _resolve_pdf_object(current)
            if not hasattr(node, "get"):
                raise HierarchyInferenceContractError("source PDF outline node is invalid")
            if _is_malformed_filename_destination(
                node.get("/Title"), _resolve_pdf_object(node.get("/Dest")), node.get("/First")
            ):
                node[NameObject("/Dest")] = ArrayObject([NullObject(), NameObject("/Fit")])
                indirect_key = _indirect_reference_key(current)
                if indirect_key is None:
                    raise HierarchyInferenceContractError(
                        "malformed outline filename container is not indirect"
                    )
                normalized.add(indirect_key)
            child = node.get("/First")
            if child is not None:
                walk(child)
            current = node.get("/Next")

    walk(first)
    return frozenset(normalized)


def outline_reference_key(value: Any) -> RawReferenceKey | None:
    """Return the raw reference for one pypdf outline destination wrapper."""
    return _indirect_reference_key(getattr(value, "indirect_reference", None))


def _is_malformed_filename_destination(title: Any, destination: Any, first_child: Any) -> bool:
    """Recognize the bounded null-page/numeric-fit container defect."""
    return (
        isinstance(title, str)
        and normalize_text(title).endswith(".pdf")
        and first_child is not None
        and isinstance(destination, (list, ArrayObject))
        and len(destination) >= 2
        and isinstance(_resolve_pdf_object(destination[0]), NullObject)
        and isinstance(destination[1], (FloatObject, NumberObject))
    )


def _resolve_pdf_object(value: Any) -> Any:
    return value.get_object() if isinstance(value, IndirectObject) else value


def _indirect_reference_key(value: Any) -> RawReferenceKey | None:
    if not isinstance(value, IndirectObject):
        return None
    return (value.idnum, value.generation)


def _raw_object_key(value: Any) -> RawReferenceKey | tuple[str, int]:
    return _indirect_reference_key(value) or ("direct", id(value))
