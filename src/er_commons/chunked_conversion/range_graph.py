"""Build the exhaustive document graph used by chunk recomposition."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

COLLECTIONS = (
    "groups",
    "texts",
    "pictures",
    "tables",
    "key_value_items",
    "form_items",
)
ROOT_REFS = frozenset({"#/body", "#/furniture"})


class RangeGraphError(ValueError):
    """A document graph cannot be partitioned without losing evidence."""


@dataclass(frozen=True)
class GraphRecord:
    """One canonical Docling collection record and its page ownership evidence."""

    collection: str
    index: int
    source_ref: str
    value: dict[str, Any]
    pages: tuple[int, ...]


@dataclass(frozen=True)
class DocumentGraph:
    """Validated document roots, pages, collection records, and reference ledger."""

    root: dict[str, Any]
    pages: tuple[tuple[int, dict[str, Any]], ...]
    records: tuple[GraphRecord, ...]
    record_by_ref: Mapping[str, GraphRecord]
    reference_count: int


def build_document_graph(document: dict[str, Any], *, page_count: int) -> DocumentGraph:
    """Validate every canonical pointer and derive one page set per semantic record."""
    root = _document_root(document)
    pages = _validate_pages(document.get("pages"), page_count=page_count)
    values = _collection_values(document)
    known = {
        f"#/{collection}/{index}"
        for collection, records in values.items()
        for index in range(len(records))
    }
    known.update(ROOT_REFS)
    reference_count = _validate_references(document, known)
    pages_by_ref = _derive_record_pages(values, root=root, page_count=page_count)
    records: list[GraphRecord] = []
    for collection in COLLECTIONS:
        for index, value in enumerate(values[collection]):
            source_ref = f"#/{collection}/{index}"
            records.append(
                GraphRecord(
                    collection=collection,
                    index=index,
                    source_ref=source_ref,
                    value=value,
                    pages=pages_by_ref[source_ref],
                )
            )
    by_ref = {record.source_ref: record for record in records}
    _validate_parent_child_reciprocity(root, by_ref)
    return DocumentGraph(root, pages, tuple(records), by_ref, reference_count)


def iter_references(value: Any, *, path: str = "$") -> Iterator[tuple[str, str]]:
    """Yield every JSON reference with a contextual value path."""
    if isinstance(value, dict):
        reference = value.get("$ref")
        if reference is not None:
            if set(value) != {"$ref"} or not isinstance(reference, str):
                raise RangeGraphError(f"malformed reference at {path}")
            yield path, reference
            return
        for key, child in value.items():
            yield from iter_references(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_references(child, path=f"{path}[{index}]")


def rewrite_references(
    value: Any,
    rewrite: Callable[[str, str], str],
    *,
    path: str = "$",
) -> Any:
    """Copy one JSON value while rewriting self and object references."""
    if isinstance(value, dict):
        reference = value.get("$ref")
        if reference is not None:
            if set(value) != {"$ref"} or not isinstance(reference, str):
                raise RangeGraphError(f"malformed reference at {path}")
            return {"$ref": rewrite(reference, path)}
        copied: dict[str, Any] = {}
        for key, child in value.items():
            if key == "self_ref":
                if not isinstance(child, str):
                    raise RangeGraphError(f"invalid self_ref at {path}.self_ref")
                copied[key] = rewrite(child, f"{path}.self_ref")
            else:
                copied[key] = rewrite_references(child, rewrite, path=f"{path}.{key}")
        return copied
    if isinstance(value, list):
        return [
            rewrite_references(child, rewrite, path=f"{path}[{index}]")
            for index, child in enumerate(value)
        ]
    return value


def _document_root(document: dict[str, Any]) -> dict[str, Any]:
    expected = {*COLLECTIONS, "pages"}
    missing = expected - set(document)
    if missing:
        raise RangeGraphError(f"document collections are missing: {sorted(missing)}")
    return {key: value for key, value in document.items() if key not in expected}


def _validate_pages(value: Any, *, page_count: int) -> tuple[tuple[int, dict[str, Any]], ...]:
    if not isinstance(value, dict):
        raise RangeGraphError("document pages are not an object")
    expected = list(range(1, page_count + 1))
    actual: list[int] = []
    pages: list[tuple[int, dict[str, Any]]] = []
    for raw_key, page in value.items():
        if not isinstance(raw_key, str) or not raw_key.isdigit() or not isinstance(page, dict):
            raise RangeGraphError(f"invalid document page record: {raw_key!r}")
        page_no = int(raw_key)
        if page.get("page_no") != page_no:
            raise RangeGraphError(f"page key/value differs: {raw_key}")
        actual.append(page_no)
        pages.append((page_no, page))
    if actual != expected:
        raise RangeGraphError("document page coverage or order differs")
    return tuple(pages)


def _collection_values(document: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for collection in COLLECTIONS:
        raw = document.get(collection)
        if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
            raise RangeGraphError(f"document collection is invalid: {collection}")
        values = list(raw)
        for index, item in enumerate(values):
            expected = f"#/{collection}/{index}"
            if item.get("self_ref") != expected:
                raise RangeGraphError(f"self_ref differs at {expected}")
        result[collection] = values
    return result


def _validate_references(document: dict[str, Any], known: set[str]) -> int:
    count = 0
    for path, reference in iter_references(document):
        count += 1
        if reference not in known:
            raise RangeGraphError(f"unresolved reference at {path}: {reference}")
    return count


def _derive_record_pages(
    values: Mapping[str, Sequence[dict[str, Any]]],
    *,
    root: Mapping[str, Any],
    page_count: int,
) -> dict[str, tuple[int, ...]]:
    direct: dict[str, tuple[int, ...]] = {}
    for collection in COLLECTIONS:
        for index, record in enumerate(values[collection]):
            direct[f"#/{collection}/{index}"] = _direct_provenance_pages(
                record, page_count=page_count
            )

    resolved: dict[str, tuple[int, ...]] = {}
    visiting: set[str] = set()

    def resolve(reference: str) -> tuple[int, ...]:
        if reference in resolved:
            return resolved[reference]
        if reference in visiting:
            raise RangeGraphError(f"page-ownership cycle at {reference}")
        visiting.add(reference)
        pages = set(direct[reference])
        if not pages:
            collection, index = parse_collection_ref(reference)
            record = values[collection][index]
            for _, child in iter_references(record):
                if child in ROOT_REFS or child == reference:
                    continue
                if _is_parent_reference(record, child):
                    continue
                pages.update(resolve(child))
        visiting.remove(reference)
        resolved[reference] = tuple(sorted(pages))
        return resolved[reference]

    for reference in direct:
        resolve(reference)
    return resolved


def _direct_provenance_pages(record: dict[str, Any], *, page_count: int) -> tuple[int, ...]:
    provenance = record.get("prov", [])
    if not isinstance(provenance, list):
        raise RangeGraphError(f"provenance is not a list: {record.get('self_ref')}")
    pages: set[int] = set()
    for index, item in enumerate(provenance):
        if not isinstance(item, dict) or not isinstance(item.get("page_no"), int):
            raise RangeGraphError(f"invalid provenance: {record.get('self_ref')}[{index}]")
        page_no = int(item["page_no"])
        if not 1 <= page_no <= page_count:
            raise RangeGraphError(f"provenance page outside source: {record.get('self_ref')}")
        pages.add(page_no)
    return tuple(sorted(pages))


def _is_parent_reference(record: dict[str, Any], reference: str) -> bool:
    parent = record.get("parent")
    return isinstance(parent, dict) and parent.get("$ref") == reference


def parse_collection_ref(reference: str) -> tuple[str, int]:
    """Parse one canonical indexed collection reference."""
    parts = reference.split("/")
    if len(parts) != 3 or parts[0] != "#" or parts[1] not in COLLECTIONS:
        raise RangeGraphError(f"unsupported collection reference: {reference}")
    try:
        index = int(parts[2])
    except ValueError as error:
        raise RangeGraphError(f"invalid collection reference: {reference}") from error
    if index < 0:
        raise RangeGraphError(f"invalid collection reference: {reference}")
    return parts[1], index


def _validate_parent_child_reciprocity(
    root: Mapping[str, Any], by_ref: Mapping[str, GraphRecord]
) -> None:
    children_by_parent: dict[str, set[str]] = {root_ref: set() for root_ref in ROOT_REFS}
    for root_name in ("body", "furniture"):
        root_value = root.get(root_name)
        if not isinstance(root_value, dict):
            raise RangeGraphError(f"document root is invalid: {root_name}")
        root_children = [
            reference for _, reference in iter_references(root_value.get("children", []))
        ]
        if len(root_children) != len(set(root_children)):
            raise RangeGraphError(f"duplicate child occurrence below #/{root_name}")
        children_by_parent[f"#/{root_name}"] = set(root_children)
    occurrences: dict[str, str] = {}
    for parent_ref, children in tuple(children_by_parent.items()):
        for child_ref in children:
            previous = occurrences.setdefault(child_ref, parent_ref)
            if previous != parent_ref:
                raise RangeGraphError(
                    f"child appears below multiple parents: {child_ref} -> {previous}, {parent_ref}"
                )
    for record in by_ref.values():
        record_children = [
            reference for _, reference in iter_references(record.value.get("children", []))
        ]
        if len(record_children) != len(set(record_children)):
            raise RangeGraphError(f"duplicate child occurrence below {record.source_ref}")
        children_by_parent[record.source_ref] = set(record_children)
        for child_ref in record_children:
            previous = occurrences.setdefault(child_ref, record.source_ref)
            if previous != record.source_ref:
                raise RangeGraphError(
                    f"child appears below multiple parents: {child_ref} -> {previous}, "
                    f"{record.source_ref}"
                )
    for record in by_ref.values():
        parent = record.value.get("parent")
        if not isinstance(parent, dict) or not isinstance(parent.get("$ref"), str):
            raise RangeGraphError(f"record parent is invalid: {record.source_ref}")
        parent_ref = str(parent["$ref"])
        if record.source_ref not in children_by_parent.get(parent_ref, set()):
            raise RangeGraphError(
                f"parent/child relationship differs: {record.source_ref} -> {parent_ref}"
            )
        if occurrences.get(record.source_ref) != parent_ref:
            raise RangeGraphError(
                f"child occurrence parent differs: {record.source_ref} -> {parent_ref}"
            )


__all__ = [
    "COLLECTIONS",
    "DocumentGraph",
    "GraphRecord",
    "ROOT_REFS",
    "RangeGraphError",
    "build_document_graph",
    "iter_references",
    "parse_collection_ref",
    "rewrite_references",
]
