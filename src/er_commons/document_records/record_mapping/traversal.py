"""Flatten preserved Docling pointers without importing or revalidating Docling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

from er_commons.document_records.record_mapping.errors import MappingContractError

EventKind = Literal["text", "table", "figure"]


@dataclass(frozen=True)
class TraversalEvent:
    """One canonical content position derived from declared producer order."""

    kind: EventKind
    pointer: str
    content_layer: Literal["body", "furniture"]
    producer_table_id: str | None = None


@dataclass(frozen=True)
class TraversalResult:
    """Ordered events plus explicit suppression and fallback accounting."""

    events: tuple[TraversalEvent, ...]
    emitted_text_pointers: frozenset[str]
    suppressed_text_pointers: frozenset[str]
    invalid_geometry_text_pointers: frozenset[str]
    suppressed_picture_furniture_pointers: frozenset[str]
    zero_table_pointers: frozenset[str]


class DoclingTraversal:
    """Traverse a saved Docling dictionary using only its JSON-pointer graph."""

    def __init__(
        self,
        document: dict[str, Any],
        mapped_table_ids: dict[str, tuple[str, ...]],
        invalid_geometry_text_pointers: set[str] | frozenset[str] = frozenset(),
        suppressed_table_pointers: set[str] | frozenset[str] = frozenset(),
    ) -> None:
        self._document = document
        self._mapped_table_ids = mapped_table_ids
        self._events: list[TraversalEvent] = []
        self._emitted_text: set[str] = set()
        self._emitted_semantic: set[str] = set()
        self._invalid_geometry_text = set(invalid_geometry_text_pointers)
        self._suppressed_tables = set(suppressed_table_pointers)
        self._suppressed_text: set[str] = set(self._invalid_geometry_text)
        self._suppressed_picture_furniture: set[str] = set()
        self._zero_tables: set[str] = set()
        self._active_groups: set[str] = set()

    def run(self) -> TraversalResult:
        """Return body events followed by producer-pointer ordered furniture."""
        body = self._document.get("body")
        if not isinstance(body, dict):
            raise MappingContractError("saved Docling document has no body object")
        for child in body.get("children", []):
            self._visit(self._child_pointer(child))

        for index, item in enumerate(self._document.get("texts", [])):
            pointer = f"#/texts/{index}"
            if item.get("content_layer") != "furniture":
                continue
            if pointer in self._suppressed_text:
                continue
            if pointer not in self._emitted_text:
                self._emit_text(pointer, "furniture")

        return TraversalResult(
            events=tuple(self._events),
            emitted_text_pointers=frozenset(self._emitted_text),
            suppressed_text_pointers=frozenset(self._suppressed_text),
            invalid_geometry_text_pointers=frozenset(self._invalid_geometry_text),
            suppressed_picture_furniture_pointers=frozenset(self._suppressed_picture_furniture),
            zero_table_pointers=frozenset(self._zero_tables),
        )

    def _visit(self, pointer: str) -> None:
        collection, _index = self._parse_pointer(pointer)
        if collection == "groups":
            self._visit_group(pointer)
        elif collection == "texts":
            item = self._resolve(pointer)
            layer = item.get("content_layer", "body")
            if layer == "furniture":
                return
            self._emit_text(pointer, "body")
        elif collection == "tables":
            self._visit_table(pointer)
        elif collection == "pictures":
            self._visit_picture(pointer)
        else:
            raise MappingContractError(f"unsupported Docling pointer in body graph: {pointer}")

    def _visit_group(self, pointer: str) -> None:
        if pointer in self._active_groups:
            raise MappingContractError(f"Docling group cycle: {pointer}")
        self._active_groups.add(pointer)
        group = self._resolve(pointer)
        for child in group.get("children", []):
            self._visit(self._child_pointer(child))
        self._active_groups.remove(pointer)

    def _visit_table(self, pointer: str) -> None:
        item = self._resolve(pointer)
        table_ids = self._mapped_table_ids.get(pointer, ())
        captions = {self._child_pointer(ref) for ref in item.get("captions", [])}
        if pointer in self._suppressed_tables:
            self._claim_semantic(pointer)
            for caption in captions:
                self._emit_text(caption, self._content_layer(self._resolve(caption)))
            for child in item.get("children", []):
                self._suppress_descendant_text(self._child_pointer(child), captions)
            return
        if table_ids:
            self._claim_semantic(pointer)
            for producer_table_id in table_ids:
                self._events.append(
                    TraversalEvent(
                        kind="table",
                        pointer=pointer,
                        content_layer=self._content_layer(item),
                        producer_table_id=producer_table_id,
                    )
                )
            for caption in captions:
                self._emit_text(caption, self._content_layer(self._resolve(caption)))
            for child in item.get("children", []):
                self._suppress_descendant_text(self._child_pointer(child), captions)
            return

        self._zero_tables.add(pointer)
        for child in item.get("children", []):
            self._visit(self._child_pointer(child))
        for caption in captions:
            if caption not in self._emitted_text:
                self._emit_text(caption, self._content_layer(self._resolve(caption)))

    def _visit_picture(self, pointer: str) -> None:
        item = self._resolve(pointer)
        self._claim_semantic(pointer)
        self._events.append(
            TraversalEvent(
                kind="figure",
                pointer=pointer,
                content_layer=self._content_layer(item),
            )
        )
        captions = {self._child_pointer(ref) for ref in item.get("captions", [])}
        for caption in captions:
            self._emit_text(caption, self._content_layer(self._resolve(caption)))
        for child in item.get("children", []):
            self._suppress_descendant_text(self._child_pointer(child), captions)

    def _suppress_descendant_text(self, pointer: str, exceptions: set[str]) -> None:
        if pointer in exceptions:
            return
        collection, _index = self._parse_pointer(pointer)
        item = self._resolve(pointer)
        if collection == "texts":
            if pointer in self._emitted_text:
                raise MappingContractError(f"cannot suppress already emitted text: {pointer}")
            self._suppressed_text.add(pointer)
            if item.get("content_layer") == "furniture":
                self._suppressed_picture_furniture.add(pointer)
            return
        for child in item.get("children", []):
            self._suppress_descendant_text(self._child_pointer(child), exceptions)

    def _emit_text(self, pointer: str, layer: str) -> None:
        self._resolve(pointer)
        if pointer in self._invalid_geometry_text:
            self._suppressed_text.add(pointer)
            return
        if pointer in self._emitted_text:
            raise MappingContractError(f"duplicate Docling semantic traversal: {pointer}")
        if pointer in self._suppressed_text:
            raise MappingContractError(f"suppressed Docling text was emitted: {pointer}")
        if layer not in {"body", "furniture"}:
            raise MappingContractError(f"unsupported content layer on {pointer}: {layer}")
        content_layer = cast(Literal["body", "furniture"], layer)
        self._claim_semantic(pointer)
        self._emitted_text.add(pointer)
        self._events.append(
            TraversalEvent(
                kind="text",
                pointer=pointer,
                content_layer=content_layer,
            )
        )

    def _claim_semantic(self, pointer: str) -> None:
        if pointer in self._emitted_semantic:
            raise MappingContractError(f"duplicate Docling semantic traversal: {pointer}")
        self._emitted_semantic.add(pointer)

    def _resolve(self, pointer: str) -> dict[str, Any]:
        collection, index = self._parse_pointer(pointer)
        values = self._document.get(collection)
        if not isinstance(values, list) or index >= len(values):
            raise MappingContractError(f"unknown Docling pointer: {pointer}")
        item = values[index]
        if not isinstance(item, dict):
            raise MappingContractError(f"Docling pointer does not resolve to an object: {pointer}")
        return item

    @staticmethod
    def _child_pointer(reference: Any) -> str:
        if not isinstance(reference, dict) or not isinstance(reference.get("$ref"), str):
            raise MappingContractError("Docling child is missing a JSON pointer")
        return str(reference["$ref"])

    @staticmethod
    def _parse_pointer(pointer: str) -> tuple[str, int]:
        parts = pointer.split("/")
        if len(parts) != 3 or parts[0] != "#" or not parts[2].isdigit():
            raise MappingContractError(f"unsupported Docling JSON pointer: {pointer}")
        return parts[1], int(parts[2])

    @staticmethod
    def _content_layer(item: dict[str, Any]) -> Literal["body", "furniture"]:
        layer = item.get("content_layer", "body")
        if layer not in {"body", "furniture"}:
            raise MappingContractError(f"unsupported Docling content layer: {layer}")
        return cast(Literal["body", "furniture"], layer)


def traverse_docling_document(
    document: dict[str, Any],
    mapped_table_ids: dict[str, tuple[str, ...]],
    invalid_geometry_text_pointers: set[str] | frozenset[str] = frozenset(),
    suppressed_table_pointers: set[str] | frozenset[str] = frozenset(),
) -> TraversalResult:
    """Flatten one saved Docling document under the canonical traversal policy."""
    return DoclingTraversal(
        document,
        mapped_table_ids,
        invalid_geometry_text_pointers,
        suppressed_table_pointers,
    ).run()
