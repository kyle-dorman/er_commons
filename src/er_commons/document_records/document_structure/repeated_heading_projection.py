"""Project accepted repeated-heading decisions onto semantic records."""

from __future__ import annotations

import copy
from dataclasses import dataclass, replace
from typing import Any, Protocol

from er_commons.document_records.document_structure.aliases import AliasSeed
from er_commons.document_records.document_structure.errors import StructureContractError
from er_commons.document_records.document_structure.repeated_heading_policy import (
    HeadingTopology,
    RepeatedHeadingDecision,
    _eligibility_rejections,
    _parse_heading,
)

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class RepeatedHeadingProjection:
    """Projected semantic records plus complete old-to-new target correspondence."""

    sections: list[JsonObject]
    content: list[JsonObject]
    section_target_redirects: dict[str, str]
    heading_target_redirects: dict[str, str]
    source_section_target_correspondence: dict[str, str]


class RepeatedHeadingProjectionView(Protocol):
    """Structural fields needed to seal 06D correspondence after later projections."""

    @property
    def sections(self) -> list[JsonObject]: ...

    @property
    def content(self) -> list[JsonObject]: ...

    @property
    def source_section_target_correspondence(self) -> dict[str, str]: ...


def build_repeated_heading_correspondence(
    decision: RepeatedHeadingDecision,
    projection: RepeatedHeadingProjectionView,
) -> JsonObject:
    """Describe many-to-one targets and exact retained-block/content conservation."""
    if decision.status != "eligible" or len(decision.heading_section_ids) != 2:
        raise StructureContractError("correspondence requires one eligible two-heading decision")
    _validate_decision_extent_before_boundary(decision)
    old_anchor_id, old_absorbed_id = decision.heading_section_ids
    new_target_id = projection.source_section_target_correspondence.get(old_absorbed_id)
    if new_target_id is None:
        raise StructureContractError("projection lacks absorbed-section correspondence")
    retained_by_key = {
        item.get("stable_item_key"): item["id"]
        for item in projection.content
        if item.get("stable_item_key") in decision.heading_stable_keys
    }
    if set(retained_by_key) != set(decision.heading_stable_keys):
        raise StructureContractError("projection did not retain both repeated heading blocks")
    expected_extents = [item for item in decision.source_page_extents if item is not None]
    if len(expected_extents) != 2:
        raise StructureContractError("correspondence requires both source page extents")
    expected_extent = (
        min(item[0] for item in expected_extents),
        max(item[1] for item in expected_extents),
    )
    descendant_sections = {new_target_id}
    changed = True
    while changed:
        previous_count = len(descendant_sections)
        descendant_sections.update(
            item["id"]
            for item in projection.sections
            if item["parent_section_id"] in descendant_sections
        )
        changed = len(descendant_sections) != previous_count
    observed_pages = [
        page
        for item in projection.content
        if item["section_id"] in descendant_sections
        for page in _content_physical_pages(item)
    ]
    if not observed_pages or (min(observed_pages), max(observed_pages)) != expected_extent:
        raise StructureContractError("projected logical chapter extent differs from decision")
    return {
        "schema_version": "er_commons.recovery.stage_correspondence.v1",
        "stage_role": "semantic_sections_and_target_aliases",
        "change_class": "many_to_one_repeated_heading_repair",
        "policy_version": decision.rule_version,
        "extent_basis": decision.extent_basis,
        "old_targets": [
            {"section_id": old_anchor_id, "role": "retained_anchor"},
            {"section_id": old_absorbed_id, "role": "absorbed_duplicate"},
        ],
        "new_target": {"section_id": new_target_id, "state": "projected_candidate_local"},
        "source_heading_block_ids": list(decision.heading_block_ids),
        "retained_heading_block_ids": [
            retained_by_key[key] for key in decision.heading_stable_keys
        ],
        "retained_heading_stable_keys": list(decision.heading_stable_keys),
        "logical_content_page_extent": list(expected_extent),
        "heading_content_orders": list(decision.heading_content_orders),
        "source_content_order_extents": [
            list(item) if item is not None else None
            for item in decision.source_content_order_extents
        ],
        "following_boundary_section_id": decision.following_boundary_section_id,
        "following_boundary_stable_key": decision.following_boundary_stable_key,
        "following_boundary_raw_text": decision.following_boundary_raw_text,
        "following_boundary_page": decision.following_boundary_page,
        "following_boundary_content_order": decision.following_boundary_content_order,
        "content_record_count": len(projection.content),
        "content_record_ids_unique": len({item["id"] for item in projection.content})
        == len(projection.content),
        "affected_descendants": [
            "semantic_sections_and_membership",
            "target_aliases",
            "document_links_and_publication",
            "collection_target_index_resolution_and_handoff",
        ],
    }


def project_repeated_heading_decisions(
    sections: list[JsonObject],
    content: list[JsonObject],
    decisions: tuple[RepeatedHeadingDecision, ...],
) -> RepeatedHeadingProjection:
    """Collapse eligible pairs once while preserving every content record and its order."""
    projected_sections = copy.deepcopy(sections)
    projected_content = copy.deepcopy(content)
    original_content_ids = [item["id"] for item in projected_content]
    content_order = {record_id: index for index, record_id in enumerate(original_content_ids)}
    section_target_redirects: dict[str, str] = {}
    heading_target_redirects: dict[str, str] = {}
    source_section_target_correspondence: dict[str, str] = {}
    used_keys: set[str] = set()
    current_topologies = _heading_topologies_from_records(projected_sections, projected_content)
    topology_by_key = {item.stable_item_key: item for item in current_topologies}
    if len(topology_by_key) != len(current_topologies):
        raise StructureContractError("repeated-heading input contains duplicate heading keys")

    for decision in decisions:
        if decision.status != "eligible":
            raise StructureContractError("only eligible repeated-heading decisions may project")
        _validate_decision_extent_before_boundary(decision)
        anchor_key = _required_key(decision.anchor_heading_key, "anchor")
        absorbed_key = _required_key(decision.absorbed_heading_key, "absorbed")
        if anchor_key == absorbed_key or used_keys.intersection({anchor_key, absorbed_key}):
            raise StructureContractError("repeated-heading decisions overlap or reuse one heading")
        used_keys.update({anchor_key, absorbed_key})
        by_key = {
            item.get("source_stable_item_key"): item
            for item in projected_sections
            if item.get("source_stable_item_key") is not None
        }
        if anchor_key not in by_key:
            raise StructureContractError("repeated-heading decision names a missing source heading")
        if absorbed_key not in by_key:
            _accept_already_projected_pair(
                decision,
                anchor=by_key[anchor_key],
                content=projected_content,
                topology_by_key=topology_by_key,
                section_target_redirects=section_target_redirects,
                heading_target_redirects=heading_target_redirects,
                source_section_target_correspondence=source_section_target_correspondence,
            )
            continue
        _validate_frozen_decision(decision, topology_by_key)
        anchor = by_key[anchor_key]
        absorbed = by_key[absorbed_key]
        _validate_projection_pair(anchor, absorbed, projected_content, content_order)

        anchor_id = anchor["id"]
        absorbed_id = absorbed["id"]
        for item in projected_content:
            if item["section_id"] == absorbed_id:
                item["section_id"] = anchor_id
                if item["id"] == absorbed["heading_block_id"]:
                    item["semantic_placement"] = "direct_body"
        for section in projected_sections:
            if section["parent_section_id"] == absorbed_id:
                section["parent_section_id"] = anchor_id
        projected_sections.remove(absorbed)
        section_target_redirects[absorbed_id] = anchor_id
        heading_target_redirects[absorbed_key] = anchor_id
        if len(decision.heading_section_ids) != 2:
            raise StructureContractError(
                "repeated-heading decision lacks old section correspondence"
            )
        source_section_target_correspondence[decision.heading_section_ids[0]] = anchor_id
        source_section_target_correspondence[decision.heading_section_ids[1]] = anchor_id

    _rebuild_section_paths_and_order(
        projected_sections, projected_content, content_order=content_order
    )
    if [item["id"] for item in projected_content] != original_content_ids:
        raise StructureContractError(
            "repeated-heading projection changed content identity or order"
        )
    return RepeatedHeadingProjection(
        sections=projected_sections,
        content=projected_content,
        section_target_redirects=section_target_redirects,
        heading_target_redirects=heading_target_redirects,
        source_section_target_correspondence=source_section_target_correspondence,
    )


def _accept_already_projected_pair(
    decision: RepeatedHeadingDecision,
    *,
    anchor: JsonObject,
    content: list[JsonObject],
    topology_by_key: dict[str, HeadingTopology],
    section_target_redirects: dict[str, str],
    heading_target_redirects: dict[str, str],
    source_section_target_correspondence: dict[str, str],
) -> None:
    """Recognize an identical prior projection without scanning for a new pair."""
    _validate_already_projected_decision(decision, content, topology_by_key)
    assert decision.absorbed_heading_key is not None
    absorbed = [
        item for item in content if item.get("stable_item_key") == decision.absorbed_heading_key
    ]
    if len(absorbed) != 1 or absorbed[0]["section_id"] != anchor["id"]:
        raise StructureContractError("repeated-heading decision names a missing source heading")
    if absorbed[0]["semantic_placement"] != "direct_body":
        raise StructureContractError("previous repeated-heading projection has changed placement")
    if len(decision.heading_section_ids) != 2:
        raise StructureContractError("repeated-heading decision lacks old section correspondence")
    section_target_redirects[decision.heading_section_ids[1]] = anchor["id"]
    heading_target_redirects[decision.absorbed_heading_key] = anchor["id"]
    source_section_target_correspondence[decision.heading_section_ids[0]] = anchor["id"]
    source_section_target_correspondence[decision.heading_section_ids[1]] = anchor["id"]


def redirect_repeated_heading_alias_seeds(
    seeds: list[AliasSeed], projection: RepeatedHeadingProjection
) -> list[AliasSeed]:
    """Redirect absorbed heading aliases to the logical section target."""
    anchor_orders = {
        section["id"]: next(
            item["sequence"]
            for item in projection.content
            if item["id"] == section["heading_block_id"]
        )
        for section in projection.sections
        if section["section_kind"] == "semantic"
    }
    redirected = []
    for seed in seeds:
        target_id = projection.section_target_redirects.get(seed.target_id, seed.target_id)
        redirected.append(
            replace(
                seed,
                target_id=target_id,
                target_order=anchor_orders.get(target_id, seed.target_order),
            )
        )
    return redirected


def _heading_topologies_from_records(
    sections: list[JsonObject], content: list[JsonObject]
) -> tuple[HeadingTopology, ...]:
    """Derive a namespace-local topology snapshot before any repair is applied."""
    content_by_id = {item["id"]: item for item in content}
    if len(content_by_id) != len(content):
        raise StructureContractError("repeated-heading input contains duplicate content IDs")
    content_order = {item["id"]: index for index, item in enumerate(content)}
    semantic = [item for item in sections if item["section_kind"] == "semantic"]
    section_by_id = {item["id"]: item for item in sections}
    if len(section_by_id) != len(sections):
        raise StructureContractError("repeated-heading input contains duplicate section IDs")
    siblings: dict[str, list[JsonObject]] = {}
    for section in semantic:
        siblings.setdefault(section["parent_section_id"], []).append(section)
    for values in siblings.values():
        values.sort(key=lambda item: content_order[item["heading_block_id"]])

    def descendant_ids(section_id: str) -> set[str]:
        result = {section_id}
        pending = [section_id]
        while pending:
            parent = pending.pop()
            children = [item["id"] for item in semantic if item["parent_section_id"] == parent]
            if result.intersection(children):
                raise StructureContractError("repeated-heading input contains a section cycle")
            result.update(children)
            pending.extend(children)
        return result

    result = []
    for section in semantic:
        heading = content_by_id.get(section["heading_block_id"])
        if heading is None:
            raise StructureContractError("repeated-heading input is missing a semantic heading")
        direct = tuple(item["id"] for item in content if item["section_id"] == section["id"])
        children = tuple(item["id"] for item in siblings.get(section["id"], []))
        mixed_children = [*direct, *children]
        if len(set(section["ordered_child_ids"])) != len(section["ordered_child_ids"]):
            raise StructureContractError(
                "repeated-heading input contains duplicate ordered child references"
            )
        if set(section["ordered_child_ids"]) != set(mixed_children):
            raise StructureContractError(
                "repeated-heading input has missing or foreign ordered child references"
            )
        expected_order = tuple(
            sorted(
                mixed_children,
                key=lambda item_id: content_order[
                    content_by_id[item_id]["id"]
                    if item_id in content_by_id
                    else section_by_id[item_id]["heading_block_id"]
                ],
            )
        )
        if tuple(section["ordered_child_ids"]) != expected_order:
            raise StructureContractError(
                "repeated-heading input ordered child references differ from source order"
            )
        subtree = descendant_ids(section["id"])
        pages = [
            page
            for item in content
            if item["section_id"] in subtree
            for page in _content_physical_pages(item)
        ]
        if not pages:
            raise StructureContractError("repeated-heading input lacks heading page provenance")
        subtree_content_order = [
            content_order[item["id"]] for item in content if item["section_id"] in subtree
        ]
        if not subtree_content_order:
            raise StructureContractError("repeated-heading input lacks content-order provenance")
        sibling_values = siblings[section["parent_section_id"]]
        result.append(
            HeadingTopology(
                section_id=section["id"],
                heading_block_id=section["heading_block_id"],
                stable_item_key=section["source_stable_item_key"],
                raw_text=heading["canonical_text"],
                physical_page=_content_physical_pages(heading)[0],
                section_sequence=section["sequence"],
                sibling_index=sibling_values.index(section),
                parent_section_id=section["parent_section_id"],
                semantic_level=section["semantic_level"],
                content_layer=section["content_layer"],
                corrected_role="heading",
                is_toc_row=heading["is_toc_row"],
                direct_content_ids=direct,
                child_section_ids=children,
                ordered_child_ids=tuple(section["ordered_child_ids"]),
                descendant_page_extent=(min(pages), max(pages)),
                heading_content_order=content_order[heading["id"]],
                descendant_content_order_extent=(
                    min(subtree_content_order),
                    max(subtree_content_order),
                ),
            )
        )
    return tuple(result)


def _content_physical_pages(item: JsonObject) -> tuple[int, ...]:
    pages = []
    for region in item.get("regions", []):
        page_id = region.get("page_id")
        if isinstance(page_id, str) and "/p" in page_id:
            try:
                pages.append(int(page_id.rsplit("/p", 1)[1]))
            except ValueError as error:
                raise StructureContractError("invalid repeated-heading page ID") from error
    return tuple(sorted(set(pages)))


def _validate_frozen_decision(
    decision: RepeatedHeadingDecision,
    topology_by_key: dict[str, HeadingTopology],
) -> None:
    """Reject a decision when any frozen topology fact changed before projection."""
    _validate_decision_extent_before_boundary(decision)
    if len(decision.heading_stable_keys) != 2:
        raise StructureContractError(
            "eligible repeated-heading decision does not name two headings"
        )
    try:
        current = tuple(topology_by_key[key] for key in decision.heading_stable_keys)
    except KeyError as error:
        raise StructureContractError(
            "repeated-heading decision names a missing source heading"
        ) from error
    first, second = current
    parsed = tuple(_parse_heading(item.raw_text) for item in current)
    if _eligibility_rejections(first, second, parsed):
        raise StructureContractError("repeated-heading eligibility topology changed after decision")
    if (
        parsed[0] is None
        or parsed[0][0] != decision.chapter_marker
        or parsed[0][2] != decision.chapter_title
    ):
        raise StructureContractError("repeated-heading parsed identity changed after decision")
    observed = {
        "heading_section_ids": tuple(_entity_tail(item.section_id) for item in current),
        "heading_block_ids": tuple(_entity_tail(item.heading_block_id) for item in current),
        "heading_raw_texts": tuple(item.raw_text for item in current),
        "heading_physical_pages": tuple(item.physical_page for item in current),
        "parent_section_id": _entity_tail(first.parent_section_id),
        "semantic_level": first.semantic_level,
        "ordered_child_refs": tuple(
            tuple(_entity_tail(item_id) for item_id in item.ordered_child_ids) for item in current
        ),
        "source_page_extents": tuple(item.descendant_page_extent for item in current),
    }
    expected = {
        "heading_section_ids": tuple(_entity_tail(item) for item in decision.heading_section_ids),
        "heading_block_ids": tuple(_entity_tail(item) for item in decision.heading_block_ids),
        "heading_raw_texts": decision.heading_raw_texts,
        "heading_physical_pages": decision.heading_physical_pages,
        "parent_section_id": (
            _entity_tail(decision.parent_section_id)
            if decision.parent_section_id is not None
            else None
        ),
        "semantic_level": decision.semantic_level,
        "ordered_child_refs": tuple(
            tuple(_entity_tail(item_id) for item_id in items)
            for items in decision.ordered_child_refs
        ),
        "source_page_extents": decision.source_page_extents,
    }
    if decision.rule_version == "repeated_chapter_divider_opening_v2":
        observed["heading_content_orders"] = tuple(item.heading_content_order for item in current)
        observed["source_content_order_extents"] = tuple(
            item.descendant_content_order_extent for item in current
        )
        expected["heading_content_orders"] = decision.heading_content_orders
        expected["source_content_order_extents"] = decision.source_content_order_extents
    changed = [field for field in expected if observed[field] != expected[field]]
    if changed:
        raise StructureContractError(
            f"repeated-heading frozen evidence changed after decision: {changed}"
        )
    following = (
        topology_by_key.get(decision.following_boundary_stable_key)
        if decision.following_boundary_stable_key is not None
        else None
    )
    following_parsed = _parse_heading(following.raw_text) if following is not None else None
    if (
        following is None
        or decision.following_boundary_section_id is None
        or _entity_tail(following.section_id)
        != _entity_tail(decision.following_boundary_section_id)
        or following.stable_item_key != decision.following_boundary_stable_key
        or following.raw_text != decision.following_boundary_raw_text
        or following.physical_page != decision.following_boundary_page
        or following.parent_section_id != first.parent_section_id
        or following.semantic_level != first.semantic_level
        or following.sibling_index != second.sibling_index + 1
        or following.physical_page <= second.physical_page
        or (following_parsed is not None and following_parsed[0] == decision.chapter_marker)
        or (
            decision.rule_version == "repeated_chapter_divider_opening_v1"
            and following_parsed is None
        )
        or (
            decision.rule_version == "repeated_chapter_divider_opening_v2"
            and following.heading_content_order != decision.following_boundary_content_order
        )
    ):
        raise StructureContractError("repeated-heading following boundary changed after decision")
    _validate_content_order_before_boundary(current, following, decision)


def _validate_already_projected_decision(
    decision: RepeatedHeadingDecision,
    content: list[JsonObject],
    topology_by_key: dict[str, HeadingTopology],
) -> None:
    """Validate the complete frozen pair and boundary after an earlier projection."""
    _validate_decision_extent_before_boundary(decision)
    if len(decision.heading_stable_keys) != 2:
        raise StructureContractError(
            "eligible repeated-heading decision does not name two headings"
        )
    anchor = topology_by_key.get(decision.heading_stable_keys[0])
    following = (
        topology_by_key.get(decision.following_boundary_stable_key)
        if decision.following_boundary_stable_key is not None
        else None
    )
    retained = [
        item for item in content if item.get("stable_item_key") in decision.heading_stable_keys
    ]
    retained_by_key = {item.get("stable_item_key"): item for item in retained}
    if anchor is None or len(retained) != 2 or len(retained_by_key) != 2:
        raise StructureContractError("previous repeated-heading projection changed frozen headings")
    absorbed = retained_by_key.get(decision.heading_stable_keys[1])
    if absorbed is None:
        raise StructureContractError("previous repeated-heading projection changed frozen headings")

    anchor_observed = (
        _entity_tail(anchor.section_id),
        _entity_tail(anchor.heading_block_id),
        anchor.raw_text,
        anchor.physical_page,
        _entity_tail(anchor.parent_section_id),
        anchor.semantic_level,
    )
    anchor_expected = (
        _entity_tail(decision.heading_section_ids[0]),
        _entity_tail(decision.heading_block_ids[0]),
        decision.heading_raw_texts[0],
        decision.heading_physical_pages[0],
        _entity_tail(decision.parent_section_id) if decision.parent_section_id else None,
        decision.semantic_level,
    )
    absorbed_pages = _content_physical_pages(absorbed)
    absorbed_observed = (
        _entity_tail(absorbed["id"]),
        absorbed.get("canonical_text"),
        absorbed_pages[0] if absorbed_pages else None,
        absorbed.get("section_id"),
        absorbed.get("semantic_placement"),
    )
    absorbed_expected = (
        _entity_tail(decision.heading_block_ids[1]),
        decision.heading_raw_texts[1],
        decision.heading_physical_pages[1],
        anchor.section_id,
        "direct_body",
    )
    expected_children = tuple(
        _entity_tail(item_id) for group in decision.ordered_child_refs for item_id in group
    )
    observed_children = tuple(_entity_tail(item_id) for item_id in anchor.ordered_child_ids)
    source_extents = [item for item in decision.source_page_extents if item is not None]
    expected_extent = (
        (min(item[0] for item in source_extents), max(item[1] for item in source_extents))
        if len(source_extents) == 2
        else None
    )
    if (
        anchor_observed != anchor_expected
        or absorbed_observed != absorbed_expected
        or observed_children != expected_children
        or anchor.descendant_page_extent != expected_extent
    ):
        raise StructureContractError("previous repeated-heading projection changed frozen evidence")

    following_parsed = _parse_heading(following.raw_text) if following is not None else None
    if (
        following is None
        or decision.following_boundary_section_id is None
        or _entity_tail(following.section_id)
        != _entity_tail(decision.following_boundary_section_id)
        or following.stable_item_key != decision.following_boundary_stable_key
        or following.raw_text != decision.following_boundary_raw_text
        or following.physical_page != decision.following_boundary_page
        or following.parent_section_id != anchor.parent_section_id
        or following.semantic_level != anchor.semantic_level
        or following.sibling_index != anchor.sibling_index + 1
        or (following_parsed is not None and following_parsed[0] == decision.chapter_marker)
        or (
            decision.rule_version == "repeated_chapter_divider_opening_v1"
            and following_parsed is None
        )
        or (
            decision.rule_version == "repeated_chapter_divider_opening_v2"
            and following.heading_content_order != decision.following_boundary_content_order
        )
    ):
        raise StructureContractError("repeated-heading following boundary changed after decision")
    _validate_content_order_before_boundary((anchor,), following, decision)


def _validate_content_order_before_boundary(
    headings: tuple[HeadingTopology, ...],
    following: HeadingTopology,
    decision: RepeatedHeadingDecision,
) -> None:
    """Prove same-page chapter transitions from exact record order, never page guesses."""
    if decision.rule_version == "repeated_chapter_divider_opening_v1":
        return
    if len(decision.heading_content_orders) != 2 or len(decision.source_content_order_extents) != 2:
        raise StructureContractError(
            "repeated-heading decision lacks complete content-order evidence"
        )
    if following.heading_content_order != decision.following_boundary_content_order:
        raise StructureContractError(
            "repeated-heading following boundary content order changed after decision"
        )
    extents = [item.descendant_content_order_extent for item in headings]
    if following.heading_content_order is None or any(item is None for item in extents):
        raise StructureContractError("repeated-heading content-order boundary evidence is absent")
    if max(item[1] for item in extents if item is not None) >= following.heading_content_order:
        raise StructureContractError(
            "repeated-heading descendant content reaches following boundary"
        )


def _validate_decision_extent_before_boundary(decision: RepeatedHeadingDecision) -> None:
    """Reject page extents that cross the frozen next-chapter boundary."""
    if decision.rule_version not in {
        "repeated_chapter_divider_opening_v1",
        "repeated_chapter_divider_opening_v2",
    }:
        raise StructureContractError("unsupported repeated-heading decision rule version")
    extents = [item for item in decision.source_page_extents if item is not None]
    if len(extents) != 2 or decision.following_boundary_page is None:
        raise StructureContractError("repeated-heading descendant extent lacks following boundary")
    extent_end = max(item[1] for item in extents)
    crosses_boundary = (
        extent_end >= decision.following_boundary_page
        if decision.rule_version == "repeated_chapter_divider_opening_v1"
        else extent_end > decision.following_boundary_page
    )
    if crosses_boundary:
        raise StructureContractError(
            "repeated-heading descendant extent reaches following boundary"
        )
    if decision.rule_version == "repeated_chapter_divider_opening_v2":
        order_extents = [item for item in decision.source_content_order_extents if item is not None]
        if (
            len(decision.heading_content_orders) != 2
            or len(order_extents) != 2
            or decision.following_boundary_content_order is None
            or any(item[0] > item[1] for item in order_extents)
            or tuple(item[0] for item in order_extents) != decision.heading_content_orders
            or order_extents[0][1] >= order_extents[1][0]
            or order_extents[1][1] >= decision.following_boundary_content_order
        ):
            raise StructureContractError(
                "repeated-heading decision has invalid content-order boundary evidence"
            )


def _entity_tail(record_id: str) -> str:
    """Compare accepted and candidate-local record IDs without equating namespaces."""
    parts = record_id.split("/", maxsplit=1)
    return parts[1] if len(parts) == 2 and parts[0].startswith("exv1-") else record_id


def _required_key(value: str | None, label: str) -> str:
    if value is None:
        raise StructureContractError(f"eligible repeated-heading decision lacks {label} key")
    return value


def _validate_projection_pair(
    anchor: JsonObject,
    absorbed: JsonObject,
    content: list[JsonObject],
    content_order: dict[str, int],
) -> None:
    if (
        anchor["parent_section_id"] != absorbed["parent_section_id"]
        or anchor["semantic_level"] != absorbed["semantic_level"]
    ):
        raise StructureContractError("repeated-heading projection topology changed after decision")
    heading_ids = (anchor["heading_block_id"], absorbed["heading_block_id"])
    by_id = {item["id"]: item for item in content}
    if any(heading_id not in by_id for heading_id in heading_ids):
        raise StructureContractError("repeated-heading projection is missing a heading block")
    if content_order[heading_ids[0]] >= content_order[heading_ids[1]]:
        raise StructureContractError("repeated-heading anchor is not first in source order")


def _rebuild_section_paths_and_order(
    sections: list[JsonObject],
    content: list[JsonObject],
    *,
    content_order: dict[str, int],
) -> None:
    by_id = {section["id"]: section for section in sections}
    if len(by_id) != len(sections):
        raise StructureContractError("repeated-heading projection produced duplicate section IDs")

    def path_for(section: JsonObject, seen: frozenset[str] = frozenset()) -> list[str]:
        section_id = section["id"]
        if section_id in seen:
            raise StructureContractError("repeated-heading projection produced a section cycle")
        parent_id = section["parent_section_id"]
        if parent_id is None:
            return [section_id]
        if parent_id not in by_id:
            raise StructureContractError("repeated-heading projection produced a dangling parent")
        return [*path_for(by_id[parent_id], seen | {section_id}), section_id]

    semantic = [item for item in sections if item["section_kind"] == "semantic"]
    semantic.sort(key=lambda item: content_order[item["heading_block_id"]])
    roots = [item for item in sections if item["section_kind"] != "semantic"]
    roots.sort(key=lambda item: item["sequence"])
    sections[:] = [*roots, *semantic]
    for sequence, section in enumerate(sections, start=1):
        section["sequence"] = sequence
        section["section_path_ids"] = path_for(section)
        positioned = [
            (content_order[item["id"]], item["id"])
            for item in content
            if item["section_id"] == section["id"]
        ]
        positioned.extend(
            (content_order[child["heading_block_id"]], child["id"])
            for child in semantic
            if child["parent_section_id"] == section["id"]
        )
        section["ordered_child_ids"] = [item_id for _, item_id in sorted(positioned)]
