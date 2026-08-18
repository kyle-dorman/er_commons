"""Project accepted corrected hierarchy onto canonical mixed content."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from er_commons.semantic_structure.errors import SemanticContractError

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class _SectionNode:
    key: str
    record: JsonObject
    heading_order: int


def build_semantic_sections(
    content: list[JsonObject],
    *,
    document_id: str,
    extraction_id: str,
    source_id: str,
    features: list[JsonObject],
    decisions: list[JsonObject],
    hierarchy: JsonObject,
    evidence_ref: JsonObject,
    replacement_keys: set[str] | frozenset[str] = frozenset(),
) -> tuple[list[JsonObject], list[JsonObject]]:
    """Return semantic sections and copied content with exact direct membership.

    The caller supplies candidate-ID-remapped content in canonical global mixed
    order. Blocks must carry their independently bridged ``stable_item_key``.
    Tables and figures inherit the deepest active accepted section at their
    existing mixed-order positions.
    """
    copied = copy.deepcopy(content)
    order_by_id = {item["id"]: index for index, item in enumerate(copied)}
    if len(order_by_id) != len(copied):
        raise SemanticContractError("semantic construction received duplicate content IDs")
    content_by_key = {
        item["stable_item_key"]: item for item in copied if item.get("stable_item_key") is not None
    }
    feature_by_key = _unique_index(features, "stable_item_key", "features")
    decision_by_key = _unique_index(decisions, "stable_item_key", "decisions")
    heading_keys = [
        feature["stable_item_key"]
        for feature in features
        if decision_by_key[feature["stable_item_key"]]["corrected_role"] == "heading"
        and feature["stable_item_key"] not in replacement_keys
    ]
    missing_headings = [key for key in heading_keys if key not in content_by_key]
    if missing_headings:
        raise SemanticContractError(f"accepted headings lack canonical blocks: {missing_headings}")

    body_root_id = f"{extraction_id}/section/{source_id}/sec000001"
    furniture_root_id = f"{extraction_id}/section/{source_id}/sec000002"
    roots = [
        _synthetic_root(body_root_id, document_id, 1, "body", "synthetic_body_root"),
        _synthetic_root(
            furniture_root_id,
            document_id,
            2,
            "furniture",
            "synthetic_furniture_root",
        ),
    ]
    parent_by_key = _parent_index(hierarchy, heading_keys, replacement_keys)
    nodes: dict[str, _SectionNode] = {}
    for sequence, key in enumerate(
        sorted(heading_keys, key=lambda item: order_by_id[content_by_key[item]["id"]]),
        start=3,
    ):
        heading = content_by_key[key]
        section_id = f"{extraction_id}/section/{source_id}/sec{sequence:06d}"
        nodes[key] = _SectionNode(
            key=key,
            heading_order=order_by_id[heading["id"]],
            record={
                "id": section_id,
                "document_id": document_id,
                "sequence": sequence,
                "content_layer": "body",
                "section_kind": "semantic",
                "semantic_level": decision_by_key[key]["corrected_level"],
                "section_path_ids": [],
                "parent_section_id": None,
                "heading_block_id": heading["id"],
                "ordered_child_ids": [],
                "inference_method": "accepted_hierarchy_correction",
                "source_stable_item_key": key,
                "evidence_ref": evidence_ref,
            },
        )

    for key, node in nodes.items():
        parent_key = parent_by_key.get(key)
        parent_id = body_root_id if parent_key is None else nodes[parent_key].record["id"]
        node.record["parent_section_id"] = parent_id
        node.record["section_path_ids"] = _section_path(key, nodes, parent_by_key, body_root_id)

    member_owner = _membership_index(hierarchy, set(heading_keys), replacement_keys)
    unassigned = set(hierarchy.get("unassigned_content", []))
    for item in copied:
        layer = item["content_layer"]
        key = item.get("stable_item_key")
        if layer == "furniture":
            _place(item, furniture_root_id, "furniture")
        elif key in nodes:
            _place(item, nodes[key].record["id"], "heading_owner")
        elif key is not None and feature_by_key[key].get("toc_region"):
            _place(item, body_root_id, "toc_content", is_toc=True)
        elif key in unassigned:
            _place(item, body_root_id, "pre_root")
        elif key in member_owner:
            owner_key = member_owner[key]
            _place(
                item,
                body_root_id if owner_key is None else nodes[owner_key].record["id"],
                "direct_body",
            )
        elif item["record_type"] in {"table", "figure"}:
            owner = _most_recent_preceding_heading(nodes, order_by_id[item["id"]])
            _place(item, body_root_id if owner is None else owner.record["id"], "inherited_nontext")
        else:
            raise SemanticContractError(
                f"canonical content has no accepted semantic placement: {item['id']}"
            )

    ordered_nodes = sorted(nodes.values(), key=lambda item: item.heading_order)
    sections = [*roots, *(node.record for node in ordered_nodes)]
    section_by_id = {section["id"]: section for section in sections}
    for section in sections:
        direct: list[tuple[int, str]] = [
            (order_by_id[item["id"]], item["id"])
            for item in copied
            if item["section_id"] == section["id"]
        ]
        direct.extend(
            (node.heading_order, node.record["id"])
            for node in nodes.values()
            if node.record["parent_section_id"] == section["id"]
        )
        section["ordered_child_ids"] = [record_id for _, record_id in sorted(direct)]
        heading_is_not_first = (
            section["section_kind"] == "semantic"
            and section["ordered_child_ids"][0] != section["heading_block_id"]
        )
        if heading_is_not_first:
            raise SemanticContractError(f"heading is not the first direct child: {section['id']}")
    if len(section_by_id) != len(sections):
        raise SemanticContractError("semantic construction allocated duplicate section IDs")
    return sections, copied


def _unique_index(records: list[JsonObject], field: str, label: str) -> dict[str, JsonObject]:
    index = {record[field]: record for record in records}
    if len(index) != len(records):
        raise SemanticContractError(f"semantic {label} contain duplicate {field} values")
    return index


def _parent_index(
    hierarchy: JsonObject,
    headings: list[str],
    replacement_keys: set[str] | frozenset[str],
) -> dict[str, str]:
    heading_set = set(headings)
    original_roots = set(hierarchy["roots"])
    original_parents = {edge["child_key"]: edge["parent_key"] for edge in hierarchy["edges"]}
    original_headings = original_roots | set(original_parents)
    if heading_set != original_headings - set(replacement_keys):
        raise SemanticContractError("accepted hierarchy replacement projection differs")
    parent_by_key: dict[str, str] = {}
    for child in headings:
        parent = original_parents.get(child)
        seen = {child}
        while parent is not None and parent not in heading_set:
            if parent in seen:
                raise SemanticContractError(f"accepted hierarchy contains a cycle: {child}")
            seen.add(parent)
            parent = original_parents.get(parent)
        if parent is not None:
            parent_by_key[child] = parent
    return parent_by_key


def _membership_index(
    hierarchy: JsonObject,
    retained_headings: set[str],
    replacement_keys: set[str] | frozenset[str],
) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    parent_by_heading = {edge["child_key"]: edge["parent_key"] for edge in hierarchy["edges"]}
    for membership in hierarchy["direct_membership"]:
        key = membership["item_key"]
        if key in replacement_keys:
            continue
        if key in result:
            raise SemanticContractError(f"accepted direct member has two owners: {key}")
        owner = membership["heading_key"]
        while owner not in retained_headings:
            owner = parent_by_heading.get(owner)
            if owner is None:
                break
        result[key] = owner
    return result


def _section_path(
    key: str,
    nodes: dict[str, _SectionNode],
    parent_by_key: dict[str, str],
    body_root_id: str,
) -> list[str]:
    keys = [key]
    seen = {key}
    while keys[-1] in parent_by_key:
        parent = parent_by_key[keys[-1]]
        if parent in seen:
            raise SemanticContractError(f"accepted hierarchy contains a cycle: {key}")
        seen.add(parent)
        keys.append(parent)
    return [body_root_id, *(nodes[item].record["id"] for item in reversed(keys))]


def _most_recent_preceding_heading(
    nodes: dict[str, _SectionNode], order: int
) -> _SectionNode | None:
    """Return the heading owning a non-text item at its mixed-order position."""
    preceding = [node for node in nodes.values() if node.heading_order < order]
    if not preceding:
        return None
    return max(preceding, key=lambda node: node.heading_order)


def _place(item: JsonObject, section_id: str, placement: str, *, is_toc: bool = False) -> None:
    item["section_id"] = section_id
    item["semantic_placement"] = placement
    item["is_toc_row"] = is_toc
    item.setdefault("stable_item_key", None)


def _synthetic_root(
    section_id: str,
    document_id: str,
    sequence: int,
    layer: str,
    kind: str,
) -> JsonObject:
    return {
        "id": section_id,
        "document_id": document_id,
        "sequence": sequence,
        "content_layer": layer,
        "section_kind": kind,
        "semantic_level": None,
        "section_path_ids": [section_id],
        "parent_section_id": None,
        "heading_block_id": None,
        "ordered_child_ids": [],
        "inference_method": "synthetic",
        "source_stable_item_key": None,
        "evidence_ref": None,
    }
