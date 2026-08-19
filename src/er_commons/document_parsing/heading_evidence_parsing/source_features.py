"""Validate Docling source structure and extract persisted item observations."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Literal, cast

from er_commons.document_parsing.heading_evidence_parsing.alignment_projection import (
    AlignmentPage,
)
from er_commons.document_parsing.heading_evidence_parsing.document import stable_text_keys
from er_commons.document_parsing.heading_evidence_parsing.errors import (
    HierarchyInferenceContractError,
)
from er_commons.document_parsing.heading_evidence_parsing.text_evidence import (
    normalize_text,
    parse_numbering,
)
from er_commons.document_parsing.heading_evidence_parsing.types import ObservedItem

JsonObject = dict[str, Any]

_PAGE_OF_FOOTER = re.compile(r"^Page (?P<label>[A-Za-z]?[0-9]+) of [0-9]+$")
_STANDALONE_FOOTER = re.compile(r"^(?:[ivxlcdm]+|[A-Za-z]?[0-9]+)$")


@dataclass(frozen=True)
class TraversedText:
    """One provenance-bearing Docling text in deterministic reading order."""

    pointer: str
    item: JsonObject
    parent_pointer: str
    content_layer: Literal["body", "furniture"]
    picture_caption: bool


def document_index_text_pointers(document: JsonObject) -> frozenset[str]:
    """Return every transitive text descendant of a document-index table."""
    objects = _index_objects(document)
    tables = document.get("tables")
    if not isinstance(tables, list):
        raise HierarchyInferenceContractError("Docling tables collection is invalid")
    descendants: set[str] = set()
    active: set[str] = set()

    def visit(pointer: str) -> None:
        if pointer in active:
            raise HierarchyInferenceContractError(
                f"Docling document-index descendant cycle: {pointer}"
            )
        item = objects.get(pointer)
        if item is None:
            raise HierarchyInferenceContractError(
                f"unknown Docling document-index reference: {pointer}"
            )
        if _pointer_collection(pointer) == "texts":
            descendants.add(pointer)
            return
        active.add(pointer)
        for child in _references(item.get("children", []), f"children: {pointer}"):
            visit(child)
        active.remove(pointer)

    for index, item in enumerate(tables):
        if not isinstance(item, dict):
            raise HierarchyInferenceContractError(f"invalid Docling table: #/tables/{index}")
        if item.get("label") != "document_index":
            continue
        for child in _references(item.get("children", []), f"children: #/tables/{index}"):
            visit(child)
    return frozenset(descendants)


def traverse_provenance_text(document: JsonObject) -> tuple[TraversedText, ...]:
    """Traverse body then furniture while retaining picture-owned text exactly once."""
    objects = _index_objects(document)
    text_items = document.get("texts")
    if not isinstance(text_items, list):
        raise HierarchyInferenceContractError("Docling texts collection is invalid")

    caption_owner = _validated_picture_captions(document, objects)
    ordered: list[TraversedText] = []
    visited_text: set[str] = set()
    active: set[str] = set()

    def visit(pointer: str) -> None:
        if pointer in active:
            raise HierarchyInferenceContractError(f"Docling reading-order cycle: {pointer}")
        item = objects.get(pointer)
        if item is None:
            raise HierarchyInferenceContractError(
                f"unknown Docling reading-order reference: {pointer}"
            )
        collection = _pointer_collection(pointer)
        if collection == "texts":
            if pointer in visited_text:
                raise HierarchyInferenceContractError(
                    f"duplicate Docling text traversal: {pointer}"
                )
            if not item.get("prov"):
                return
            layer = _content_layer(item, pointer)
            parent = _reference(item.get("parent"), f"text parent: {pointer}")
            if parent not in objects and parent not in {"#/body", "#/furniture"}:
                raise HierarchyInferenceContractError(
                    f"unknown Docling text parent: {pointer} -> {parent}"
                )
            visited_text.add(pointer)
            ordered.append(TraversedText(pointer, item, parent, layer, pointer in caption_owner))
            return
        if collection not in {"groups", "tables", "pictures"}:
            raise HierarchyInferenceContractError(
                f"unsupported Docling reading-order object: {pointer}"
            )
        active.add(pointer)
        for child in _references(item.get("children", []), f"children: {pointer}"):
            visit(child)
        if collection == "pictures":
            for caption in _references(item.get("captions", []), f"captions: {pointer}"):
                if caption not in visited_text:
                    visit(caption)
        active.remove(pointer)

    for root_name in ("body", "furniture"):
        root = document.get(root_name)
        if not isinstance(root, dict):
            raise HierarchyInferenceContractError(f"Docling {root_name} root is invalid")
        for pointer in _references(root.get("children", []), f"{root_name} children"):
            visit(pointer)

    for index, raw in enumerate(text_items):
        if not isinstance(raw, dict):
            raise HierarchyInferenceContractError(f"invalid Docling text: #/texts/{index}")
        pointer = f"#/texts/{index}"
        if not raw.get("prov") or pointer in visited_text:
            continue
        if _content_layer(raw, pointer) != "furniture":
            raise HierarchyInferenceContractError(
                f"provenance-bearing body text is absent from reading order: {pointer}"
            )
        visit(pointer)

    expected = sum(isinstance(item, dict) and bool(item.get("prov")) for item in text_items)
    if len(ordered) != expected:
        raise HierarchyInferenceContractError("provenance-bearing text coverage differs")
    keys_by_pointer = dict(
        zip(
            (f"#/texts/{index}" for index in range(len(text_items))),
            stable_text_keys(text_items),
            strict=True,
        )
    )
    keys = [keys_by_pointer[entry.pointer] for entry in ordered]
    if len(keys) != len(set(keys)):
        raise HierarchyInferenceContractError("duplicate stable text key")
    return tuple(ordered)


def extract_item_observations(
    document: JsonObject,
    alignment_pages: dict[int, AlignmentPage],
    *,
    outline_observations: tuple[JsonObject, ...] = (),
    printed_page_labels: dict[int, str] | None = None,
) -> list[ObservedItem]:
    """Build producer-owned feature fields before TOC and regime assignment."""
    pages = alignment_pages
    labels = printed_page_labels or unique_footer_labels(document)
    traversed = traverse_provenance_text(document)
    text_items = document.get("texts")
    if not isinstance(text_items, list):
        raise HierarchyInferenceContractError("Docling texts collection is invalid")
    keys_by_pointer = dict(
        zip(
            (f"#/texts/{index}" for index in range(len(text_items))),
            stable_text_keys(text_items),
            strict=True,
        )
    )
    features: list[ObservedItem] = []
    for order, entry in enumerate(traversed):
        item = entry.item
        provenance = item["prov"][0]
        if not isinstance(provenance, dict):
            raise HierarchyInferenceContractError(f"invalid provenance: {entry.pointer}")
        physical_page = provenance.get("page_no")
        bbox = provenance.get("bbox")
        charspan = provenance.get("charspan")
        if not isinstance(physical_page, int) or physical_page not in pages:
            raise HierarchyInferenceContractError(f"missing conversion page: {entry.pointer}")
        if not isinstance(bbox, dict) or bbox.get("coord_origin") != "BOTTOMLEFT":
            raise HierarchyInferenceContractError(f"invalid source bbox: {entry.pointer}")
        if not isinstance(charspan, list) or len(charspan) != 2:
            raise HierarchyInferenceContractError(f"invalid source charspan: {entry.pointer}")
        text = item.get("text")
        orig = item.get("orig")
        role = item.get("label")
        if not isinstance(text, str) or not isinstance(orig, str) or not isinstance(role, str):
            raise HierarchyInferenceContractError(f"invalid text fields: {entry.pointer}")
        page_record = pages[physical_page]
        layout = page_record.lookup(text)
        numbering = parse_numbering(text, raw_role=role)
        normalized = normalize_text(text)
        features.append(
            cast(
                ObservedItem,
                {
                    "stable_item_key": keys_by_pointer[entry.pointer],
                    "raw_self_ref": entry.pointer,
                    "raw_parent_ref": entry.parent_pointer,
                    "text": text,
                    "orig": orig,
                    "normalized_text": normalized,
                    "reading_order_index": order,
                    "content_layer": entry.content_layer,
                    "raw_role": role,
                    "raw_level": item.get("level") if isinstance(item.get("level"), int) else None,
                    "physical_page": physical_page,
                    "page_width": page_record.width,
                    "page_height": page_record.height,
                    "bbox": bbox,
                    "charspan": charspan,
                    "line_count": layout.line_count,
                    "left_pt": _six_places(bbox.get("l")),
                    "height_pt": _six_places(_number(bbox.get("t")) - _number(bbox.get("b"))),
                    "numbering_kind": numbering.kind,
                    "numbering_token": numbering.token,
                    "numbering_depth": numbering.depth,
                    "outline_state": "absent",
                    "outline_level": None,
                    "layout_state": layout.state,
                    "printed_page_label": labels.get(physical_page),
                },
            )
        )
    return apply_outline_observations(features, outline_observations)


def apply_outline_observations(
    features: list[ObservedItem],
    outline_observations: tuple[JsonObject, ...],
) -> list[ObservedItem]:
    """Apply validated outline matches without rebuilding source feature seeds."""
    by_target: dict[tuple[int, str], list[JsonObject]] = defaultdict(list)
    for observation in outline_observations:
        title = observation.get("normalized_title")
        page = observation.get("physical_page")
        level = observation.get("effective_level")
        if not isinstance(title, str) or not isinstance(page, int):
            raise HierarchyInferenceContractError("outline observation target is invalid")
        if not isinstance(level, int) or not 1 <= level <= 6:
            raise HierarchyInferenceContractError("outline observation level is invalid")
        by_target[(page, title)].append(observation)

    overlaid: list[ObservedItem] = []
    for feature in features:
        matches = by_target[(feature["physical_page"], feature["normalized_text"])]
        updated = dict(feature)
        if len(matches) == 1:
            updated["outline_state"] = "unique_exact"
            updated["outline_level"] = matches[0]["effective_level"]
        elif len(matches) > 1:
            updated["outline_state"] = "ambiguous"
            updated["outline_level"] = None
        overlaid.append(cast(ObservedItem, updated))
    return overlaid


def build_feature_seeds(
    document: JsonObject,
    alignment_pages: dict[int, AlignmentPage],
    *,
    outline_observations: tuple[JsonObject, ...] = (),
    printed_page_labels: dict[int, str] | None = None,
) -> list[ObservedItem]:
    """Return typed parser observations for hierarchy inference."""
    return extract_item_observations(
        document,
        alignment_pages,
        outline_observations=outline_observations,
        printed_page_labels=printed_page_labels,
    )


def unique_footer_labels(document: JsonObject) -> dict[int, str]:
    """Resolve a unique Page-N-of-total token, then a standalone fallback."""
    primary: dict[int, set[str]] = defaultdict(set)
    fallback: dict[int, set[str]] = defaultdict(set)
    texts = document.get("texts", [])
    if not isinstance(texts, list):
        raise HierarchyInferenceContractError("Docling texts collection is invalid")
    for item in texts:
        if not isinstance(item, dict) or item.get("label") != "page_footer":
            continue
        provenance = item.get("prov")
        text = item.get("text")
        if not isinstance(provenance, list) or not provenance or not isinstance(text, str):
            continue
        first = provenance[0]
        if isinstance(first, dict) and isinstance(first.get("page_no"), int):
            token = normalize_text(text, casefold=False)
            match = _PAGE_OF_FOOTER.fullmatch(token)
            if match is not None:
                primary[first["page_no"]].add(match.group("label"))
            elif _STANDALONE_FOOTER.fullmatch(token):
                fallback[first["page_no"]].add(token)
    labels: dict[int, str] = {}
    for page in set(primary) | set(fallback):
        preferred = primary.get(page, set())
        secondary = fallback.get(page, set())
        if len(preferred) == 1:
            labels[page] = next(iter(preferred))
        elif not preferred and len(secondary) == 1:
            labels[page] = next(iter(secondary))
    return labels


def _validated_picture_captions(
    document: JsonObject, objects: dict[str, JsonObject]
) -> dict[str, str]:
    owners: dict[str, str] = {}
    pictures = document.get("pictures", [])
    if not isinstance(pictures, list):
        raise HierarchyInferenceContractError("Docling pictures collection is invalid")
    for index, picture in enumerate(pictures):
        if not isinstance(picture, dict):
            raise HierarchyInferenceContractError(f"invalid Docling picture: #/pictures/{index}")
        pointer = f"#/pictures/{index}"
        captions = _references(picture.get("captions", []), f"captions: {pointer}")
        picture_page = _first_page(picture, pointer) if captions else None
        for caption in captions:
            item = objects.get(caption)
            if item is None or _pointer_collection(caption) != "texts":
                raise HierarchyInferenceContractError(f"invalid picture caption ref: {caption}")
            if item.get("label") != "caption":
                raise HierarchyInferenceContractError(f"picture caption label differs: {caption}")
            if _reference(item.get("parent"), f"caption parent: {caption}") != pointer:
                raise HierarchyInferenceContractError(f"picture caption parent differs: {caption}")
            if _first_page(item, caption) != picture_page:
                raise HierarchyInferenceContractError(f"picture caption page differs: {caption}")
            previous = owners.setdefault(caption, pointer)
            if previous != pointer:
                raise HierarchyInferenceContractError(
                    f"picture caption has multiple owners: {caption}"
                )
    return owners


def _index_objects(document: JsonObject) -> dict[str, JsonObject]:
    objects: dict[str, JsonObject] = {}
    for collection in ("groups", "tables", "pictures", "texts"):
        values = document.get(collection, [])
        if not isinstance(values, list):
            raise HierarchyInferenceContractError(f"Docling {collection} collection is invalid")
        for index, item in enumerate(values):
            if not isinstance(item, dict):
                raise HierarchyInferenceContractError(f"invalid Docling {collection} item: {index}")
            pointer = item.get("self_ref")
            expected = f"#/{collection}/{index}"
            if pointer != expected or pointer in objects:
                raise HierarchyInferenceContractError(f"invalid Docling self reference: {expected}")
            objects[pointer] = item
    return objects


def _references(value: Any, context: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise HierarchyInferenceContractError(f"invalid Docling reference list: {context}")
    return tuple(_reference(item, context) for item in value)


def _reference(value: Any, context: str) -> str:
    if not isinstance(value, dict) or not isinstance(value.get("$ref"), str):
        raise HierarchyInferenceContractError(f"invalid Docling reference: {context}")
    return cast(str, value["$ref"])


def _pointer_collection(pointer: str) -> str:
    parts = pointer.split("/")
    if len(parts) != 3 or parts[0] != "#" or not parts[2].isdigit():
        raise HierarchyInferenceContractError(f"invalid Docling pointer: {pointer}")
    return parts[1]


def _content_layer(item: JsonObject, pointer: str) -> Literal["body", "furniture"]:
    layer = item.get("content_layer")
    if layer not in {"body", "furniture"}:
        raise HierarchyInferenceContractError(f"unknown content layer: {pointer}")
    return cast(Literal["body", "furniture"], layer)


def _first_page(item: JsonObject, pointer: str) -> int:
    provenance = item.get("prov")
    if not isinstance(provenance, list) or not provenance or not isinstance(provenance[0], dict):
        raise HierarchyInferenceContractError(f"missing provenance: {pointer}")
    page = provenance[0].get("page_no")
    if not isinstance(page, int):
        raise HierarchyInferenceContractError(f"invalid provenance page: {pointer}")
    return page


def _number(value: Any) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise HierarchyInferenceContractError("bbox coordinate is invalid")
    return float(value)


def _six_places(value: Any) -> float:
    number = _number(value)
    return float(Decimal(str(number)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN))
