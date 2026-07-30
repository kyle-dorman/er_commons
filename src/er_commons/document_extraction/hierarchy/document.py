"""Index and normalize Docling documents for semantic hierarchy comparison."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from typing import Any

JsonObject = dict[str, Any]


def canonical_bytes(value: Any) -> bytes:
    """Serialize one JSON-compatible value deterministically."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def stable_text_key(item: JsonObject) -> str:
    """Identify one text item without depending on Docling collection indices."""
    provenance = item.get("prov")
    if not isinstance(provenance, list) or not provenance:
        raise ValueError("text item has no provenance")
    first = provenance[0]
    if not isinstance(first, dict):
        raise ValueError("text item has invalid provenance")
    identity = {
        "text": item.get("text"),
        "orig": item.get("orig"),
        "page_no": first.get("page_no"),
        "bbox": first.get("bbox"),
        "charspan": first.get("charspan"),
    }
    return hashlib.sha256(canonical_bytes(identity)).hexdigest()


@dataclass(frozen=True)
class DocumentIndex:
    """Stable text lookup, semantic reference map, and source collection order."""

    text_items: dict[str, JsonObject]
    references: dict[str, str]
    text_order: tuple[str, ...]

    @classmethod
    def build(cls, document: JsonObject) -> DocumentIndex:
        """Validate and index all references needed by hierarchy comparison."""
        texts = document.get("texts")
        if not isinstance(texts, list):
            raise ValueError("Docling document texts collection is invalid")

        items: dict[str, JsonObject] = {}
        references = {"#/body": "root:body", "#/furniture": "root:furniture"}
        order: list[str] = []
        for raw in texts:
            if not isinstance(raw, dict):
                raise ValueError("Docling text item is invalid")
            key = stable_text_key(raw)
            if key in items:
                raise ValueError(f"duplicate stable text key: {key}")
            self_ref = raw.get("self_ref")
            if not isinstance(self_ref, str):
                raise ValueError(f"text item has invalid self reference: {key}")
            items[key] = raw
            references[self_ref] = f"text:{key}"
            order.append(key)

        for collection in (
            "groups",
            "tables",
            "pictures",
            "key_value_items",
            "form_items",
        ):
            values = document.get(collection, [])
            if not isinstance(values, list):
                raise ValueError(f"Docling {collection} collection is invalid")
            singular = collection.removesuffix("s")
            for index, value in enumerate(values):
                if not isinstance(value, dict) or not isinstance(value.get("self_ref"), str):
                    raise ValueError(f"invalid Docling {collection} item at index {index}")
                references[value["self_ref"]] = f"{singular}:{index}"

        return cls(text_items=items, references=references, text_order=tuple(order))

    def reading_order(self, document: JsonObject) -> list[str]:
        """Resolve body and furniture trees to stable semantic references."""
        objects: dict[str, JsonObject] = {}
        for collection in ("groups", "tables", "pictures", "texts"):
            for item in document.get(collection, []):
                if isinstance(item, dict) and isinstance(item.get("self_ref"), str):
                    objects[item["self_ref"]] = item

        ordered: list[str] = []
        active: set[str] = set()

        def visit(raw_ref: str) -> None:
            if raw_ref in active:
                raise ValueError(f"Docling reading-order cycle: {raw_ref}")
            semantic = self.references.get(raw_ref)
            if semantic is None:
                raise ValueError(f"unknown Docling reading-order reference: {raw_ref}")
            item = objects.get(raw_ref)
            if item is None or not item.get("children"):
                ordered.append(semantic)
                return
            active.add(raw_ref)
            for child in item["children"]:
                if not isinstance(child, dict) or not isinstance(child.get("$ref"), str):
                    raise ValueError(f"invalid Docling reading-order child: {raw_ref}")
                visit(child["$ref"])
            active.remove(raw_ref)

        for root_name in ("body", "furniture"):
            root = document.get(root_name)
            if not isinstance(root, dict):
                raise ValueError(f"Docling document has invalid {root_name} root")
            for child in root.get("children", []):
                if not isinstance(child, dict) or not isinstance(child.get("$ref"), str):
                    raise ValueError(f"invalid Docling {root_name} child")
                visit(child["$ref"])
        return ordered


def _image_digest(uri: str) -> str:
    if not uri.startswith("data:") or "," not in uri:
        return uri
    metadata, encoded = uri.split(",", 1)
    if ";base64" not in metadata:
        return uri
    digest = hashlib.sha256(base64.b64decode(encoded)).hexdigest()
    return f"<DATA_URI_SHA256:{digest}>"


def normalize_references(value: Any, references: dict[str, str]) -> Any:
    """Replace collection-index references with stable semantic references."""
    if isinstance(value, list):
        return [normalize_references(item, references) for item in value]
    if not isinstance(value, dict):
        return value
    if set(value) == {"$ref"}:
        target = value["$ref"]
        if not isinstance(target, str) or target not in references:
            raise ValueError(f"unknown Docling reference: {target}")
        return {"$semantic_ref": references[target]}
    normalized: JsonObject = {}
    for key, item in value.items():
        if key == "self_ref":
            continue
        if key == "uri" and isinstance(item, str):
            normalized[key] = _image_digest(item)
        else:
            normalized[key] = normalize_references(item, references)
    return normalized


def normalized_text_item(
    item: JsonObject,
    references: dict[str, str],
    *,
    remove_level: bool,
    project_promotion_source: bool,
) -> JsonObject:
    """Project one text item onto the Task 03E permitted-change surface."""
    normalized = normalize_references(item, references)
    if not isinstance(normalized, dict):
        raise TypeError("normalized text item is not an object")
    if remove_level:
        normalized.pop("level", None)
    if project_promotion_source:
        normalized["label"] = "section_header"
        normalized.pop("enumerated", None)
        normalized.pop("marker", None)
    return normalized
