"""Semantic section hierarchy and ordered mixed-content policies."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import cast

from er_commons.document_records.document_structure.bundle import (
    DocumentStructureBundleView,
    JsonObject,
)
from er_commons.document_records.document_structure.errors import StructureContractError
from er_commons.document_records.document_structure.section_starts import (
    logical_section_start_id,
)


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


def _section_sort_key(
    view: DocumentStructureBundleView, section: JsonObject
) -> tuple[int, int, int]:
    """Place the two synthetic roots before headings in mixed-content order."""
    root_order = {
        "synthetic_body_root": 0,
        "synthetic_furniture_root": 1,
    }
    if section["section_kind"] in root_order:
        return (0, root_order[section["section_kind"]], 0)
    return (
        1,
        view.global_order_by_id.get(_required_section_anchor(section), -1),
        int(section["semantic_level"]),
    )


def _section_anchor_id(section: JsonObject) -> str | None:
    """Return a heading or explicitly derived start anchor."""
    return logical_section_start_id(section)


def _required_section_anchor(section: JsonObject) -> str:
    """Return a structural anchor or fail for a malformed non-root section."""
    anchor = _section_anchor_id(section)
    if anchor is None:
        raise StructureContractError(f"section lacks a structural anchor: {section['id']}")
    return anchor


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
            if heading_id is not None and heading_id in owned_heading_ids:
                raise StructureContractError(f"heading ownership is not one-to-one: {heading_id}")
            if heading_id is not None:
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
) -> str | None:
    """Validate one accepted heading and return its uniquely owned block ID."""
    section_id = section["id"]
    if section["content_layer"] != "body" or parent is None:
        raise StructureContractError(f"semantic section must be a body descendant: {section_id}")
    if section["section_path_ids"][0] != body_root["id"]:
        raise StructureContractError(
            f"semantic section must descend from the body root: {section_id}"
        )
    if not parent["section_kind"].startswith("synthetic_") and not (
        parent["semantic_level"] < section["semantic_level"]
    ):
        raise StructureContractError(
            f"semantic child level must be greater than parent: {section_id}"
        )

    heading_id = section["heading_block_id"]
    if section["section_kind"] == "derived_chapter":
        start_id = section.get("start_record_id")
        if (
            heading_id is not None
            or not isinstance(start_id, str)
            or start_id not in view.content_by_id
        ):
            raise StructureContractError(
                f"derived chapter lacks a valid start anchor: {section_id}"
            )
        if section.get("heading_component_block_ids") != []:
            raise StructureContractError(
                f"derived chapter fabricates heading components: {section_id}"
            )
        _validate_chapter_scope(view, section, require_descendant_start=True)
        return None
    heading = view.content_by_id.get(heading_id)
    if heading is None:
        raise StructureContractError(f"semantic heading block is missing: {heading_id}")
    if not section["ordered_child_ids"]:
        raise StructureContractError(f"semantic section has no heading child: {section_id}")
    heading_is_owned = _is_owned_heading(heading, section)
    if section["section_kind"] == "composite_semantic":
        heading_position_is_valid = heading["id"] in section["ordered_child_ids"]
    else:
        heading_position_is_valid = section["ordered_child_ids"][0] == heading["id"]
    if not heading_is_owned or not heading_position_is_valid:
        raise StructureContractError(
            f"heading block has invalid direct ownership or position: {heading_id}"
        )
    if heading["stable_item_key"] != section["source_stable_item_key"]:
        raise StructureContractError(f"section heading evidence key differs: {section_id}")
    _validate_heading_components(view, section, cast(str, heading_id))
    if section["section_kind"] == "composite_semantic":
        _validate_chapter_scope(view, section, require_descendant_start=False)
    return cast(str, heading_id)


def _validate_chapter_scope(
    view: DocumentStructureBundleView,
    section: JsonObject,
    *,
    require_descendant_start: bool,
) -> None:
    """Require one exact body interval and a truthful derived descendant start."""
    scope_ids = section.get("chapter_scope_content_ids")
    start_id = section.get("start_record_id")
    boundary_id = section.get("scope_boundary_record_id")
    if not isinstance(scope_ids, list) or not scope_ids or start_id != scope_ids[0]:
        raise StructureContractError(f"chapter scope has an invalid start: {section['id']}")
    try:
        start_index = view.global_order_by_id[start_id]
    except (KeyError, TypeError) as error:
        raise StructureContractError(
            f"chapter scope has an invalid start: {section['id']}"
        ) from error
    if isinstance(boundary_id, str) and boundary_id in view.global_order_by_id:
        boundary_index = view.global_order_by_id[boundary_id]
    elif boundary_id == section["document_id"]:
        boundary_index = len(view.content)
    else:
        raise StructureContractError(f"chapter scope has an invalid boundary: {section['id']}")
    expected = [
        item["id"]
        for item in view.content[start_index:boundary_index]
        if item["content_layer"] == "body"
    ]
    if scope_ids != expected:
        raise StructureContractError(
            f"chapter scope is not the exact body interval: {section['id']}"
        )
    declared_components = section.get("heading_component_block_ids", [])
    scoped_components = [item_id for item_id in scope_ids if item_id in declared_components]
    if section["section_kind"] == "composite_semantic" and scoped_components != (
        declared_components
    ):
        raise StructureContractError(
            f"chapter heading components fall outside its scope: {section['id']}"
        )
    derivation = section.get("derivation_ref")
    if not isinstance(derivation, dict):
        raise StructureContractError(f"chapter scope lacks derivation: {section['id']}")
    descendant_ids = _descendant_section_ids(view, section["id"])
    declared_child_ids = _resolve_declared_chapter_children(
        view, derivation.get("ordered_child_refs")
    )
    if not declared_child_ids or not declared_child_ids <= descendant_ids:
        raise StructureContractError(
            f"chapter selected children differ from its descendants: {section['id']}"
        )
    selected_subtree_ids = set(declared_child_ids)
    for child_id in declared_child_ids:
        selected_subtree_ids.update(_descendant_section_ids(view, child_id))
    selected_child_body_ids = {
        item["id"]
        for item in view.content
        if item["content_layer"] == "body" and item["section_id"] in selected_subtree_ids
    }
    if not selected_child_body_ids <= set(scope_ids):
        raise StructureContractError(
            f"chapter selected child content falls outside its scope: {section['id']}"
        )
    pages = [
        page
        for item in view.content
        if item["id"] in set(scope_ids)
        for page in _content_page_numbers(item)
    ]
    if (
        not isinstance(derivation, dict)
        or not pages
        or [min(pages), max(pages)]
        != [derivation.get("extent_start_page"), derivation.get("extent_end_page")]
    ):
        raise StructureContractError(f"chapter scope differs from its extent: {section['id']}")
    if not require_descendant_start:
        return
    anchors = [
        _required_section_anchor(child) for child in view.sections if child["id"] in descendant_ids
    ]
    anchors.sort(key=view.global_order_by_id.__getitem__)
    if not anchors or start_id != anchors[0]:
        raise StructureContractError(
            f"derived chapter start is not its first descendant anchor: {section['id']}"
        )
    anchor = view.content_by_id[start_id]
    marker = re.match(
        r"^(\d{1,2})\.\d+(?:\.|\s|$)",
        _normalize_structural_marker_text(str(anchor.get("canonical_text", ""))),
    )
    if marker is None or marker.group(1) != section.get("chapter_marker"):
        raise StructureContractError(
            f"derived chapter start marker differs from chapter: {section['id']}"
        )


def _content_page_numbers(item: JsonObject) -> list[int]:
    """Read compact v3 page membership or full-record regions in focused fixtures."""
    compact = item.get("physical_page_numbers")
    if isinstance(compact, list):
        return [int(page) for page in compact]
    return [int(region["page_id"].rsplit("/p", 1)[1]) for region in item.get("regions", [])]


def _normalize_structural_marker_text(value: str) -> str:
    """Mirror stable Unicode and ASCII-space normalization without a v3 import."""
    normalized = unicodedata.normalize("NFC", value).replace("\N{NO-BREAK SPACE}", " ")
    return re.sub(r"[ \t\n\r\f\v]+", " ", normalized).strip().casefold()


def _descendant_section_ids(view: DocumentStructureBundleView, section_id: str) -> set[str]:
    """Return all recursive section descendants of one chapter."""
    result: set[str] = set()
    changed = True
    while changed:
        before = len(result)
        result.update(
            child["id"]
            for child in view.sections
            if child.get("parent_section_id") == section_id
            or child.get("parent_section_id") in result
        )
        changed = len(result) != before
    return result


def _resolve_declared_chapter_children(view: DocumentStructureBundleView, refs: object) -> set[str]:
    """Resolve every frozen child reference uniquely in the candidate namespace."""
    if not isinstance(refs, list) or not refs or not all(isinstance(ref, str) for ref in refs):
        return set()
    resolved: list[str] = []
    for ref in refs:
        matches = [
            section
            for section in view.sections
            if section["id"] == ref
            or section.get("source_stable_item_key") == ref
            or _section_reference_tail(str(section["id"])) == _section_reference_tail(ref)
        ]
        if len(matches) != 1:
            return set()
        resolved.append(str(matches[0]["id"]))
    return set(resolved) if len(set(resolved)) == len(resolved) else set()


def _section_reference_tail(value: str) -> str:
    """Compare a current section ID with an accepted candidate-local reference."""
    marker = "/section/"
    return value.split(marker, maxsplit=1)[1] if marker in value else value


def _validate_heading_components(
    view: DocumentStructureBundleView, section: JsonObject, heading_id: str
) -> None:
    """Require a composite's declared blocks to exactly invert direct heading roles."""
    direct = sorted(
        (
            item
            for item in view.content
            if item["section_id"] == section["id"]
            and item["semantic_placement"] in {"heading_owner", "heading_component"}
        ),
        key=lambda item: view.global_order_by_id[item["id"]],
    )
    if section["section_kind"] != "composite_semantic":
        if any(item["semantic_placement"] == "heading_component" for item in direct):
            raise StructureContractError(
                f"non-composite section owns heading components: {section['id']}"
            )
        return
    declared = section.get("heading_component_block_ids")
    actual_ids = [item["id"] for item in direct]
    actual_roles = [item["semantic_placement"] for item in direct]
    if (
        not isinstance(declared, list)
        or not declared
        or declared[0] != heading_id
        or declared != actual_ids
        or actual_roles != ["heading_owner", *["heading_component"] * (len(direct) - 1)]
    ):
        raise StructureContractError(
            f"composite heading components differ from direct ownership: {section['id']}"
        )


def _is_owned_heading(heading: JsonObject, section: JsonObject) -> bool:
    """Return whether a block is the direct heading owner of one section."""
    return bool(
        heading["record_type"] == "block"
        and heading["section_id"] == section["id"]
        and heading["semantic_placement"] == "heading_owner"
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
        if item["record_type"] != "block" and item["semantic_placement"] in {
            "heading_owner",
            "heading_component",
        }:
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
        if item["semantic_placement"] == "heading_component" and (
            owner["section_kind"] != "composite_semantic"
        ):
            raise StructureContractError(
                f"heading component is orphaned from a composite owner: {item['id']}"
            )


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
        (view.global_order_by_id[_required_section_anchor(child)], child["id"])
        for child in view.sections
        if child["parent_section_id"] == section_id and _section_anchor_id(child) is not None
    )
    return [child_id for _, child_id in sorted(positioned_children)]
