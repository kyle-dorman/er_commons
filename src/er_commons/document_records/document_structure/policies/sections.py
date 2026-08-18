"""Semantic section hierarchy and ordered mixed-content policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from er_commons.document_records.document_structure.bundle import (
    DocumentStructureBundleView,
    JsonObject,
)
from er_commons.document_records.document_structure.errors import StructureContractError


@dataclass(frozen=True)
class SyntheticRoots:
    """The body and furniture anchors required by a complete document."""

    body: JsonObject
    furniture: JsonObject


def validate_sections(view: DocumentStructureBundleView) -> None:
    """Validate semantic ancestry and exact mixed-content containment."""
    _require_unique_record_ids(view)
    _validate_section_order(view)
    _validate_document_scope(view)
    roots = _find_synthetic_roots(view)
    _validate_section_records(view, roots)
    _reject_section_cycles(view)
    _validate_content_placement(view, roots)
    _validate_global_content_order(view)
    _validate_ordered_children(view)


def _validate_section_order(view: DocumentStructureBundleView) -> None:
    """Require roots first, then semantic sections in heading document order."""
    expected_sequences = list(range(1, len(view.sections) + 1))
    actual_sequences = [section["sequence"] for section in view.sections]
    if actual_sequences != expected_sequences:
        raise StructureContractError("sections are not in contiguous sequence")

    expected_order = sorted(view.sections, key=lambda section: _section_sort_key(view, section))
    if view.sections != expected_order:
        raise StructureContractError("sections are not in deterministic document order")


def _section_sort_key(view: DocumentStructureBundleView, section: JsonObject) -> tuple[int, int]:
    """Place the two synthetic roots before headings in mixed-content order."""
    root_order = {
        "synthetic_body_root": 0,
        "synthetic_furniture_root": 1,
    }
    if section["section_kind"] in root_order:
        return (0, root_order[section["section_kind"]])
    heading_id = section["heading_block_id"]
    return (1, view.global_order_by_id.get(heading_id, -1))


def _require_unique_record_ids(view: DocumentStructureBundleView) -> None:
    """Reject duplicate section or mixed-content record identifiers."""
    if len(view.sections_by_id) != len(view.sections):
        raise StructureContractError("duplicate section IDs")
    if len(view.content_by_id) != len(view.content):
        raise StructureContractError("duplicate content IDs")


def _validate_document_scope(view: DocumentStructureBundleView) -> None:
    """Keep every section and mixed-content ID inside one document namespace."""
    document_id = view.bundle["document_id"]
    for section in view.sections:
        if section["document_id"] != document_id or not view.belongs_to_document(section["id"]):
            raise StructureContractError(f"section escaped document scope: {section['id']}")
    for item in view.content:
        if not view.belongs_to_document(item["id"]):
            raise StructureContractError(f"content escaped document scope: {item['id']}")


def _find_synthetic_roots(view: DocumentStructureBundleView) -> SyntheticRoots:
    """Return the document's one body root and one furniture root."""
    body_roots = [
        section for section in view.sections if section["section_kind"] == "synthetic_body_root"
    ]
    furniture_roots = [
        section
        for section in view.sections
        if section["section_kind"] == "synthetic_furniture_root"
    ]
    if len(body_roots) != 1 or len(furniture_roots) != 1:
        raise StructureContractError("exactly one body and furniture synthetic root are required")
    return SyntheticRoots(body=body_roots[0], furniture=furniture_roots[0])


def _validate_section_records(view: DocumentStructureBundleView, roots: SyntheticRoots) -> None:
    """Validate each section's parent, path, level, and heading ownership."""
    non_block_heading = next(
        (
            item
            for item in view.content
            if item["semantic_placement"] == "heading_owner" and item["record_type"] != "block"
        ),
        None,
    )
    if non_block_heading is not None:
        raise StructureContractError(
            f"tables and figures cannot own semantic headings: {non_block_heading['id']}"
        )

    owned_heading_ids: set[str] = set()
    for section in view.sections:
        parent = _parent_section(view, section)
        _validate_section_path(section, parent)
        if section["section_kind"].startswith("synthetic_"):
            _validate_synthetic_section(section)
        else:
            heading_id = _validate_semantic_section(view, section, parent, roots.body)
            if heading_id in owned_heading_ids:
                raise StructureContractError(f"heading ownership is not one-to-one: {heading_id}")
            owned_heading_ids.add(heading_id)

    declared_heading_ids = {
        item["id"] for item in view.content if item["semantic_placement"] == "heading_owner"
    }
    if declared_heading_ids != owned_heading_ids:
        unowned = sorted(declared_heading_ids - owned_heading_ids)
        missing = sorted(owned_heading_ids - declared_heading_ids)
        raise StructureContractError(
            f"heading ownership is not one-to-one: unowned={unowned}, missing={missing}"
        )


def _parent_section(view: DocumentStructureBundleView, section: JsonObject) -> JsonObject | None:
    """Resolve one parent, rejecting a dangling section relationship."""
    parent_id = section["parent_section_id"]
    if parent_id is None:
        return None
    parent = view.sections_by_id.get(parent_id)
    if parent is None:
        raise StructureContractError(f"unknown section parent: {parent_id}")
    return parent


def _validate_section_path(section: JsonObject, parent: JsonObject | None) -> None:
    """Require the stored path to be the exact root-to-self ancestry."""
    expected_path = (
        [section["id"]] if parent is None else [*parent["section_path_ids"], section["id"]]
    )
    if section["section_path_ids"] != expected_path:
        raise StructureContractError(f"section path differs for {section['id']}")


def _validate_synthetic_section(section: JsonObject) -> None:
    """Keep parser-derived hierarchy evidence off synthetic roots."""
    semantic_fields = ("semantic_level", "heading_block_id", "source_stable_item_key")
    carries_semantic_value = any(section[field] is not None for field in semantic_fields)
    if (
        carries_semantic_value
        or section["inference_method"] != "synthetic"
        or section["parent_section_id"] is not None
    ):
        raise StructureContractError(
            f"synthetic section carries semantic heading fields: {section['id']}"
        )


def _validate_semantic_section(
    view: DocumentStructureBundleView,
    section: JsonObject,
    parent: JsonObject | None,
    body_root: JsonObject,
) -> str:
    """Validate one accepted heading and return its uniquely owned block ID."""
    section_id = section["id"]
    if section["content_layer"] != "body" or parent is None:
        raise StructureContractError(f"semantic section must be a body descendant: {section_id}")
    if section["section_path_ids"][0] != body_root["id"]:
        raise StructureContractError(
            f"semantic section must descend from the body root: {section_id}"
        )
    if parent["section_kind"] == "semantic" and not (
        parent["semantic_level"] < section["semantic_level"]
    ):
        raise StructureContractError(
            f"semantic child level must be greater than parent: {section_id}"
        )

    heading_id = section["heading_block_id"]
    heading = view.content_by_id.get(heading_id)
    if heading is None:
        raise StructureContractError(f"semantic heading block is missing: {heading_id}")
    if not section["ordered_child_ids"]:
        raise StructureContractError(f"semantic section has no heading child: {section_id}")
    if not _is_owned_heading(heading, section, section["ordered_child_ids"][0]):
        raise StructureContractError(
            f"heading block must be its section's first direct child: {heading_id}"
        )
    if heading["stable_item_key"] != section["source_stable_item_key"]:
        raise StructureContractError(f"section heading evidence key differs: {section_id}")
    return cast(str, heading_id)


def _is_owned_heading(heading: JsonObject, section: JsonObject, first_child_id: str) -> bool:
    """Return whether a block is the first direct heading of one section."""
    return bool(
        heading["record_type"] == "block"
        and heading["section_id"] == section["id"]
        and heading["semantic_placement"] == "heading_owner"
        and first_child_id == heading["id"]
    )


def _reject_section_cycles(view: DocumentStructureBundleView) -> None:
    """Walk each parent chain and reject the first repeated section."""
    for section_id in view.sections_by_id:
        seen = {section_id}
        parent_id = view.sections_by_id[section_id]["parent_section_id"]
        while parent_id is not None:
            if parent_id in seen:
                raise StructureContractError(f"section hierarchy cycle at {section_id}")
            seen.add(parent_id)
            parent_id = view.sections_by_id[parent_id]["parent_section_id"]


def _validate_content_placement(view: DocumentStructureBundleView, roots: SyntheticRoots) -> None:
    """Keep body, TOC, pre-root, furniture, table, and figure roles distinct."""
    for item in view.content:
        owner = view.sections_by_id.get(item["section_id"])
        if owner is None:
            raise StructureContractError(f"content has unknown section: {item['id']}")
        if item["content_layer"] == "furniture" and owner["id"] != roots.furniture["id"]:
            raise StructureContractError(f"furniture escaped the furniture root: {item['id']}")
        if item["content_layer"] == "furniture" and item["semantic_placement"] != "furniture":
            raise StructureContractError(f"furniture content has a body placement: {item['id']}")
        if item["content_layer"] == "body" and owner["content_layer"] != "body":
            raise StructureContractError(f"body content escaped the body hierarchy: {item['id']}")
        if item["content_layer"] == "body" and item["semantic_placement"] == "furniture":
            raise StructureContractError(f"body content has a furniture placement: {item['id']}")
        if item["is_toc_row"] and not _is_body_root_toc(item, owner, roots.body):
            raise StructureContractError(
                f"visible TOC content cannot induce a section: {item['id']}"
            )
        if item["semantic_placement"] == "toc_content" and not item["is_toc_row"]:
            raise StructureContractError(f"non-TOC content has a TOC placement: {item['id']}")
        if item["semantic_placement"] == "pre_root" and owner["id"] != roots.body["id"]:
            raise StructureContractError(
                f"pre-root content must remain under the body root: {item['id']}"
            )
        if item["record_type"] != "block" and item["semantic_placement"] == "heading_owner":
            raise StructureContractError(
                f"tables and figures cannot own semantic headings: {item['id']}"
            )
        if (
            item["record_type"] in {"table", "figure"}
            and item["semantic_placement"] != "inherited_nontext"
        ):
            raise StructureContractError(f"table or figure has a text placement: {item['id']}")
        if item["record_type"] == "block" and item["semantic_placement"] == "inherited_nontext":
            raise StructureContractError(f"block has a nontext placement: {item['id']}")


def _is_body_root_toc(item: JsonObject, owner: JsonObject, body_root: JsonObject) -> bool:
    """Return whether a visible TOC block remains ordinary body-root content."""
    return bool(owner["id"] == body_root["id"] and item["semantic_placement"] == "toc_content")


def _validate_global_content_order(view: DocumentStructureBundleView) -> None:
    """Require the global order to contain every mixed-content record once."""
    persisted_order = view.bundle["global_content_order_ids"]
    if set(persisted_order) != set(view.content_by_id) or len(persisted_order) != len(
        view.content_by_id
    ):
        raise StructureContractError("global mixed-content order is incomplete")


def _validate_ordered_children(view: DocumentStructureBundleView) -> None:
    """Require ordered children to invert direct membership in document order."""
    for section in view.sections:
        expected_children = _expected_direct_children(view, section["id"])
        if section["ordered_child_ids"] != expected_children:
            raise StructureContractError(f"ordered section children differ for {section['id']}")


def _expected_direct_children(view: DocumentStructureBundleView, section_id: str) -> list[str]:
    """Project direct content and child sections into one mixed-order list."""
    positioned_children = [
        (view.global_order_by_id[item["id"]], item["id"])
        for item in view.content
        if item["section_id"] == section_id
    ]
    positioned_children.extend(
        (view.global_order_by_id[child["heading_block_id"]], child["id"])
        for child in view.sections
        if child["parent_section_id"] == section_id and child["heading_block_id"] is not None
    )
    return [child_id for _, child_id in sorted(positioned_children)]
