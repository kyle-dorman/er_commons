"""Project accepted missing-chapter decisions without inventing source blocks."""

from __future__ import annotations

import copy
from dataclasses import dataclass, replace
from typing import Any, cast

from er_commons.document_records.document_structure.aliases import AliasSeed
from er_commons.document_records.document_structure.errors import StructureContractError
from er_commons.document_records.document_structure.missing_chapter_policy import (
    MissingChapterDecision,
    StartOrderBasis,
)
from er_commons.document_records.document_structure.normalization import normalize_alias
from er_commons.document_records.document_structure.section_starts import (
    logical_section_start_id,
)

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class MissingChapterProjection:
    """Projected records and exact decision-to-target correspondence."""

    sections: list[JsonObject]
    content: list[JsonObject]
    section_target_redirects: dict[str, str]
    heading_target_redirects: dict[str, str]
    chapter_target_ids: dict[str, str]
    source_section_target_correspondence: dict[str, str]
    direct_content_ownership_correspondence: list[JsonObject]
    decisions_ref: JsonObject | None


@dataclass(frozen=True)
class _ResolvedLogicalStart:
    """Current start record plus the ordering domain used by the published value."""

    record: JsonObject
    observed_content_order: int
    order_basis: StartOrderBasis


def project_missing_chapter_decisions(
    sections: list[JsonObject],
    content: list[JsonObject],
    decisions: tuple[MissingChapterDecision, ...],
    *,
    section_target_redirects: dict[str, str] | None = None,
    heading_target_redirects: dict[str, str] | None = None,
    source_section_target_correspondence: dict[str, str] | None = None,
    decisions_ref: JsonObject | None = None,
    page_count: int | None = None,
) -> MissingChapterProjection:
    """Insert distinct chapter targets around frozen contiguous child subtrees."""
    projected_sections = copy.deepcopy(sections)
    projected_content = copy.deepcopy(content)
    original_ids = [item["id"] for item in projected_content]
    order = {record_id: index for index, record_id in enumerate(original_ids)}
    chapter_targets: dict[str, str] = {}
    correspondence: dict[str, str] = dict(source_section_target_correspondence or {})
    used_sections: set[str] = set()
    used_component_keys: set[str] = set()
    used_extents: list[tuple[int, int]] = []
    ownership_correspondence: list[JsonObject] = []

    for decision in sorted(decisions, key=lambda item: item.extent_start_page or -1):
        if decision.status != "eligible" or decision.representation is None:
            raise StructureContractError("only eligible missing-chapter decisions may project")
        if decision.chapter_marker is None or decision.chapter_title is None:
            raise StructureContractError("eligible missing-chapter decision lacks identity")
        if decision.chapter_marker in chapter_targets:
            raise StructureContractError("missing-chapter decisions repeat one marker")
        extent = _required_extent(decision)
        if any(extent[0] <= prior[1] and prior[0] <= extent[1] for prior in used_extents):
            raise StructureContractError("missing-chapter decision extents overlap")
        used_extents.append(extent)
        _validate_frozen_components_and_boundary(decision, projected_content, page_count)
        if used_component_keys.intersection(decision.heading_stable_keys):
            raise StructureContractError("missing-chapter decisions reuse a heading component")
        used_component_keys.update(decision.heading_stable_keys)
        children = _resolve_child_run(projected_sections, decision.ordered_child_refs)
        _validate_frozen_child_topology(decision, children, projected_sections, projected_content)
        _validate_complete_enclosing_topology(
            decision,
            children,
            projected_sections,
            projected_content,
            correspondence,
        )
        top_children = _topmost_selected_children(children, projected_sections)
        subtree_ids = _descendants({item["id"] for item in top_children}, projected_sections)
        if not top_children or used_sections.intersection(subtree_ids):
            raise StructureContractError("missing-chapter decisions overlap or lack a child run")
        used_sections.update(subtree_ids)
        scope_content, direct_content = _validate_complete_content_scope(
            decision,
            subtree_ids,
            projected_sections,
            projected_content,
            correspondence,
        )
        _validate_frozen_extent(decision, scope_content)
        parent = _resolve_section_with_redirect(
            projected_sections, decision.parent_ref, correspondence
        )
        if parent is None or _record_source_id(parent["id"], "section") != decision.source_id:
            raise StructureContractError("missing-chapter parent is absent")
        resolved_start = _resolve_logical_start(projected_content, decision)
        start = resolved_start.record
        if resolved_start.observed_content_order != decision.start_content_order:
            raise _field_mismatch(
                "missing-chapter start record order changed",
                decision,
                str(start["id"]),
                f"start_content_order[{resolved_start.order_basis}]",
                decision.start_content_order,
                resolved_start.observed_content_order,
            )
        sequence = max(int(item["sequence"]) for item in projected_sections) + 1
        target_id = _allocate_section_id(projected_sections, sequence)
        component_ids = _resolve_component_ids(projected_content, decision)
        boundary_id = _resolved_boundary_id(
            decision, projected_sections, projected_content, correspondence
        )
        scope_boundary_id = _resolved_scope_boundary_id(decision, projected_content, boundary_id)
        heading_id = component_ids[0] if component_ids else None
        section = {
            "id": target_id,
            "document_id": parent["document_id"],
            "sequence": sequence,
            "content_layer": "body",
            "section_kind": (
                "composite_semantic"
                if decision.representation == "recovered_composite"
                else "derived_chapter"
            ),
            "semantic_level": decision.semantic_level,
            "section_path_ids": [],
            "parent_section_id": parent["id"],
            "heading_block_id": heading_id,
            "ordered_child_ids": [],
            "inference_method": (
                "accepted_composite_heading_recovery"
                if component_ids
                else "accepted_toc_children_derivation"
            ),
            "source_stable_item_key": (decision.heading_stable_keys[0] if component_ids else None),
            "evidence_ref": decisions_ref,
            "chapter_marker": decision.chapter_marker,
            "structural_title": decision.chapter_title,
            "chapter_representation": decision.representation,
            "heading_component_block_ids": list(component_ids),
            "title_evidence_ids": list(decision.toc_evidence_ids),
            "start_record_id": start["id"],
            "following_boundary_record_id": boundary_id,
            "scope_boundary_record_id": scope_boundary_id,
            "chapter_scope_content_ids": [item["id"] for item in scope_content],
            "derivation_ref": {
                "policy_version": "missing_whole_chapter_v1",
                "extent_start_page": decision.extent_start_page,
                "extent_end_page": decision.extent_end_page,
                "ordered_child_refs": list(decision.ordered_child_refs),
                "enclosing_section_refs": list(decision.enclosing_section_refs),
                "direct_content_record_refs": [
                    item.record_id for item in decision.direct_content_topology
                ],
            },
        }
        projected_sections.append(section)
        for child in top_children:
            child["parent_section_id"] = target_id
        for index, component_id in enumerate(component_ids):
            component = next(item for item in projected_content if item["id"] == component_id)
            component["content_layer"] = "body"
            component["section_id"] = target_id
            component["semantic_placement"] = "heading_owner" if index == 0 else "heading_component"
            component["is_toc_row"] = False
        ownership_correspondence.extend(
            {
                "content_record_id": item["id"],
                "source_stable_item_key": item["stable_item_key"],
                "original_owner_section_id": item["section_id"],
                "current_owner_section_id": item["section_id"],
                "chapter_scope_section_id": target_id,
            }
            for item in direct_content
        )
        chapter_targets[decision.chapter_marker] = target_id

    _rebuild(projected_sections, projected_content, order)
    if [item["id"] for item in projected_content] != original_ids:
        raise StructureContractError("missing-chapter projection changed content identity or order")
    return MissingChapterProjection(
        sections=projected_sections,
        content=projected_content,
        section_target_redirects=dict(section_target_redirects or {}),
        heading_target_redirects=dict(heading_target_redirects or {}),
        chapter_target_ids=chapter_targets,
        source_section_target_correspondence=correspondence,
        direct_content_ownership_correspondence=ownership_correspondence,
        decisions_ref=copy.deepcopy(decisions_ref),
    )


def build_missing_chapter_alias_seeds(
    decisions: tuple[MissingChapterDecision, ...], projection: MissingChapterProjection
) -> list[AliasSeed]:
    """Emit full-title and bare chapter aliases with decision provenance."""
    by_id = {item["id"]: item for item in projection.sections}
    seeds: list[AliasSeed] = []
    for decision in decisions:
        if decision.chapter_marker is None or decision.chapter_title is None:
            continue
        target_id = projection.chapter_target_ids[decision.chapter_marker]
        section = by_id[target_id]
        evidence = projection.decisions_ref
        if not isinstance(evidence, dict) or set(evidence) != {"path", "sha256"}:
            raise StructureContractError(
                "missing-chapter aliases require a checksum-pinned decision artifact"
            )
        for raw_value in (decision.chapter_title, f"Chapter {decision.chapter_marker}"):
            seeds.append(
                AliasSeed.canonical_target(
                    alias_kind="section",
                    raw_value=raw_value,
                    target_id=target_id,
                    target_type="section",
                    target_order=_section_start_order(section, projection.content),
                    evidence_kind="chapter_decision",
                    evidence_ref=copy.deepcopy(evidence),
                )
            )
    return seeds


def prefer_missing_chapter_alias_evidence(seeds: list[AliasSeed]) -> list[AliasSeed]:
    """Use the chapter decision for restored-target aliases emitted by multiple owners."""
    preferred = {
        (seed.alias_kind, normalize_alias(seed.raw_value), seed.target_id): seed
        for seed in seeds
        if seed.evidence_kind == "chapter_decision"
    }
    return [
        replace(
            seed,
            target_order=chosen.target_order,
            evidence_kind=chosen.evidence_kind,
            evidence_ref=copy.deepcopy(chosen.evidence_ref),
            toc_reconciliation_ref=chosen.toc_reconciliation_ref,
        )
        if (
            chosen := preferred.get(
                (seed.alias_kind, normalize_alias(seed.raw_value), seed.target_id)
            )
        )
        else seed
        for seed in seeds
    ]


def build_missing_chapter_correspondence(
    decision: MissingChapterDecision, projection: MissingChapterProjection
) -> JsonObject:
    """Describe the distinct target, retained components, and frozen subtree extent."""
    assert decision.chapter_marker is not None
    target_id = projection.chapter_target_ids[decision.chapter_marker]
    retained = [
        item["id"]
        for item in projection.content
        if item.get("stable_item_key") in decision.heading_stable_keys
    ]
    return {
        "schema_version": "er_commons.recovery.stage_correspondence.v1",
        "stage_role": "semantic_sections_and_target_aliases",
        "change_class": "distinct_missing_whole_chapter_target",
        "policy_version": "missing_whole_chapter_v1",
        "source_id": decision.source_id,
        "chapter_marker": decision.chapter_marker,
        "chapter_title": decision.chapter_title,
        "representation": decision.representation,
        "decision_ref": copy.deepcopy(projection.decisions_ref),
        "old_targets": [],
        "new_target": {"section_id": target_id, "state": "projected_candidate_local"},
        "retained_heading_block_ids": retained,
        "ordered_child_refs": list(decision.ordered_child_refs),
        "chapter_scope_content_ids": next(
            item["chapter_scope_content_ids"]
            for item in projection.sections
            if item["id"] == target_id
        ),
        "direct_content_ownership": [
            item
            for item in projection.direct_content_ownership_correspondence
            if item["chapter_scope_section_id"] == target_id
        ],
        "logical_content_page_extent": list(_required_extent(decision)),
        "following_boundary_record_id": next(
            item["following_boundary_record_id"]
            for item in projection.sections
            if item["id"] == target_id
        ),
        "following_boundary_kind": decision.following_boundary_kind,
        "scope_boundary_record_id": next(
            item["scope_boundary_record_id"]
            for item in projection.sections
            if item["id"] == target_id
        ),
        "content_record_count": len(projection.content),
        "content_record_ids_unique": len({item["id"] for item in projection.content})
        == len(projection.content),
    }


def _resolve_child_run(sections: list[JsonObject], refs: tuple[str, ...]) -> list[JsonObject]:
    resolved = [_resolve_section(sections, ref) for ref in refs]
    if any(item is None for item in resolved) or len(
        {item["id"] for item in resolved if item}
    ) != len(refs):
        raise StructureContractError("missing-chapter child references do not resolve uniquely")
    return [item for item in resolved if item is not None]


def _resolve_section(sections: list[JsonObject], ref: str | None) -> JsonObject | None:
    if ref is None:
        return None
    matches = [
        item
        for item in sections
        if item["id"] == ref
        or item.get("source_stable_item_key") == ref
        or _structural_tail(str(item["id"]), "section") == _structural_tail(ref, "section")
    ]
    if len(matches) > 1:
        raise StructureContractError(f"ambiguous section reference: {ref}")
    return matches[0] if matches else None


def _resolve_section_with_redirect(
    sections: list[JsonObject], ref: str | None, redirects: dict[str, str]
) -> JsonObject | None:
    """Resolve an accepted ID directly or through the verified 06D correspondence."""
    resolved = _resolve_section(sections, ref)
    if resolved is not None or ref is None:
        return resolved
    redirected = redirects.get(ref)
    return _resolve_section(sections, redirected)


def _resolve_content(content: list[JsonObject], ref: str | None) -> JsonObject | None:
    if ref is None:
        return None
    matches = [
        item
        for item in content
        if item["id"] == ref or item["id"].endswith("/" + ref) or item.get("stable_item_key") == ref
    ]
    if len(matches) > 1:
        raise StructureContractError(f"ambiguous content reference: {ref}")
    return matches[0] if matches else None


def _resolve_logical_start(
    content: list[JsonObject], decision: MissingChapterDecision
) -> _ResolvedLogicalStart:
    """Resolve the start and distinguish a mixed index from a family-local sequence."""
    start = _resolve_content(content, decision.start_record_ref)
    if start is None:
        raise _field_mismatch(
            "missing-chapter start record is absent",
            decision,
            decision.start_record_ref,
            "start_record_ref",
            decision.start_record_ref,
            None,
        )
    observed_source = _record_source_id(str(start["id"]), str(start["record_type"]))
    if observed_source != decision.source_id:
        raise _field_mismatch(
            "missing-chapter start record is cross-source",
            decision,
            str(start["id"]),
            "source_id",
            decision.source_id,
            observed_source,
        )
    is_direct_content_start = bool(
        decision.direct_content_topology
        and _entity_tail(str(start["id"]))
        == _entity_tail(decision.direct_content_topology[0].record_id)
    )
    if is_direct_content_start:
        return _ResolvedLogicalStart(
            start,
            content.index(start),
            "global_mixed_content_index",
        )
    return _ResolvedLogicalStart(
        start,
        int(start["sequence"]),
        "family_record_sequence",
    )


def _field_mismatch(
    context: str,
    decision: MissingChapterDecision,
    record_id: object,
    field: str,
    expected: object,
    observed: object,
) -> StructureContractError:
    """Build one actionable frozen-evidence error without changing record contracts."""
    return StructureContractError(
        f"{context}: chapter={decision.chapter_marker!r}, record={record_id!r}, "
        f"field={field!r}, expected={expected!r}, observed={observed!r}"
    )


def _validate_frozen_fields(
    context: str,
    decision: MissingChapterDecision,
    record_id: object,
    fields: tuple[tuple[str, object, object], ...],
) -> None:
    """Report the first changed frozen field with its evidence coordinates."""
    for field, expected, observed in fields:
        if observed != expected:
            raise _field_mismatch(
                context,
                decision,
                record_id,
                field,
                expected,
                observed,
            )


def _topmost_selected_children(
    children: list[JsonObject], sections: list[JsonObject]
) -> list[JsonObject]:
    selected = {item["id"] for item in children}
    by_id = {item["id"]: item for item in sections}
    result = []
    for child in children:
        parent = cast(str | None, child.get("parent_section_id"))
        ancestors: set[str] = set()
        while parent is not None and parent in by_id:
            ancestors.add(parent)
            parent = cast(str | None, by_id[parent].get("parent_section_id"))
        if not ancestors.intersection(selected):
            result.append(child)
    return result


def _validate_frozen_extent(
    decision: MissingChapterDecision, scope_content: list[JsonObject]
) -> None:
    extent = _required_extent(decision)
    pages = [page for item in scope_content for page in _content_pages(item)]
    observed_extent = (min(pages), max(pages)) if pages else None
    if observed_extent != extent:
        raise _field_mismatch(
            "missing-chapter projected records differ from frozen extent",
            decision,
            "chapter_scope",
            "logical_content_page_extent",
            extent,
            observed_extent,
        )


def _validate_complete_content_scope(
    decision: MissingChapterDecision,
    child_subtree_ids: set[str],
    sections: list[JsonObject],
    content: list[JsonObject],
    redirects: dict[str, str],
) -> tuple[list[JsonObject], list[JsonObject]]:
    """Freeze the exact body interval and its non-child ownership complement."""
    start = _resolve_content(content, decision.start_record_ref)
    if start is None:
        raise _field_mismatch(
            "missing-chapter start record is absent",
            decision,
            decision.start_record_ref,
            "start_record_ref",
            decision.start_record_ref,
            None,
        )
    index_by_id = {str(item["id"]): index for index, item in enumerate(content)}
    start_index = index_by_id[str(start["id"])]
    if decision.following_boundary_kind == "following_heading":
        boundary = _resolve_content(
            content,
            decision.following_scope_start_stable_key
            or decision.following_scope_start_ref
            or decision.following_boundary_stable_key,
        )
        if boundary is None:
            raise _field_mismatch(
                "missing-chapter following boundary is absent",
                decision,
                decision.following_scope_start_ref,
                "following_scope_start_ref",
                decision.following_scope_start_ref,
                None,
            )
        boundary_index = index_by_id[str(boundary["id"])]
    else:
        boundary_index = len(content)
    if boundary_index <= start_index:
        raise _field_mismatch(
            "missing-chapter boundary does not follow start",
            decision,
            "chapter_scope",
            "global_mixed_content_interval",
            f"boundary index > {start_index}",
            boundary_index,
        )
    component_keys = set(decision.heading_stable_keys)
    scope = [
        item
        for item in content[start_index:boundary_index]
        if item.get("content_layer") == "body" or item.get("stable_item_key") in component_keys
    ]
    observed_component_keys = [
        item.get("stable_item_key")
        for item in scope
        if item.get("stable_item_key") in component_keys
    ]
    if observed_component_keys != list(decision.heading_stable_keys):
        raise _field_mismatch(
            "missing-chapter heading components fall outside scope",
            decision,
            "chapter_scope",
            "heading_stable_keys",
            list(decision.heading_stable_keys),
            observed_component_keys,
        )
    foreign = next(
        (
            item
            for item in scope
            if _record_source_id(str(item["id"]), str(item["record_type"])) != decision.source_id
        ),
        None,
    )
    if foreign is not None:
        raise _field_mismatch(
            "missing-chapter scope contains foreign-source content",
            decision,
            foreign["id"],
            "source_id",
            decision.source_id,
            _record_source_id(str(foreign["id"]), str(foreign["record_type"])),
        )
    scope_ids = {str(item["id"]) for item in scope}
    selected_child_body_ids = {
        str(item["id"])
        for item in content
        if item.get("content_layer") == "body" and item.get("section_id") in child_subtree_ids
    }
    if not selected_child_body_ids <= scope_ids:
        raise _field_mismatch(
            "missing-chapter selected child content falls outside scope",
            decision,
            "chapter_scope",
            "selected_child_body_ids",
            sorted(selected_child_body_ids),
            sorted(selected_child_body_ids & scope_ids),
        )
    direct = [
        item
        for item in scope
        if item.get("stable_item_key") not in component_keys
        and item.get("section_id") not in child_subtree_ids
    ]
    frozen = decision.direct_content_topology
    if len(frozen) != len(direct):
        raise _field_mismatch(
            "missing-chapter direct content topology is incomplete",
            decision,
            "chapter_scope",
            "direct_content_record_count",
            len(frozen),
            len(direct),
        )
    allowed_owners = {
        item["id"]
        for ref in (decision.parent_ref, *decision.enclosing_section_refs)
        if (item := _resolve_section_with_redirect(sections, ref, redirects)) is not None
    }
    for item, fact in zip(direct, frozen, strict=True):
        frozen_owner = _resolve_section_with_redirect(sections, fact.original_owner_ref, redirects)
        if frozen_owner is None or frozen_owner["id"] not in allowed_owners:
            raise _field_mismatch(
                "missing-chapter direct content owner is outside the frozen topology",
                decision,
                item["id"],
                "original_owner_ref",
                fact.original_owner_ref,
                item.get("section_id"),
            )
        pages = _content_pages(item)
        _validate_frozen_fields(
            "missing-chapter direct content topology changed",
            decision,
            item["id"],
            (
                ("record_id", _entity_tail(fact.record_id), _entity_tail(str(item["id"]))),
                ("stable_item_key", fact.stable_item_key, item.get("stable_item_key")),
                ("record_type", fact.record_type, item.get("record_type")),
                (
                    "source_id",
                    fact.source_id,
                    _record_source_id(str(item["id"]), str(item["record_type"])),
                ),
                ("global_mixed_content_index", fact.content_order, index_by_id[str(item["id"])]),
                ("physical_pages", fact.physical_pages, pages),
                (
                    "original_owner_ref",
                    _entity_tail(fact.original_owner_ref),
                    _entity_tail(str(item.get("section_id"))),
                ),
            ),
        )
    return scope, direct


def _validate_frozen_child_topology(
    decision: MissingChapterDecision,
    children: list[JsonObject],
    sections: list[JsonObject],
    content: list[JsonObject],
) -> None:
    """Compare every frozen child fact with the current source-local tree."""
    if tuple(item.section_ref for item in decision.child_topology) != decision.ordered_child_refs:
        raise _field_mismatch(
            "missing-chapter child topology order differs from decision",
            decision,
            "child_topology",
            "ordered_child_refs",
            decision.ordered_child_refs,
            tuple(item.section_ref for item in decision.child_topology),
        )
    observed_orders: list[int] = []
    for child in children:
        key = cast(str | None, child.get("source_stable_item_key"))
        frozen_matches = [
            item
            for item in decision.child_topology
            if item.section_ref == key
            or _structural_tail(item.section_ref, "section")
            == _structural_tail(str(child["id"]), "section")
        ]
        frozen = frozen_matches[0] if len(frozen_matches) == 1 else None
        if frozen is None:
            raise _field_mismatch(
                "missing-chapter child lacks frozen topology",
                decision,
                child["id"],
                "child_topology",
                "one matching frozen record",
                len(frozen_matches),
            )
        anchor = _resolve_content(content, logical_section_start_id(child))
        if anchor is None:
            raise _field_mismatch(
                "missing-chapter child lacks a current start anchor",
                decision,
                child["id"],
                "logical_section_start_id",
                logical_section_start_id(child),
                None,
            )
        descendant_ids = _descendants({child["id"]}, sections)
        pages = [
            page
            for item in content
            if item["section_id"] in descendant_ids
            for page in _content_pages(item)
        ]
        _validate_frozen_fields(
            "missing-chapter frozen child topology changed",
            decision,
            child["id"],
            (
                ("source_id", frozen.source_id, _record_source_id(child["id"], "section")),
                ("family_record_sequence", frozen.content_order, int(anchor["sequence"])),
                (
                    "parent_ref",
                    _entity_tail(frozen.parent_ref),
                    _entity_tail(str(child["parent_section_id"])),
                ),
                ("semantic_level", frozen.semantic_level, int(child["semantic_level"])),
                (
                    "physical_page_extent",
                    (frozen.extent_start_page, frozen.extent_end_page),
                    (min(pages), max(pages)) if pages else None,
                ),
                ("heading_raw_text", frozen.heading_raw_text, anchor.get("canonical_text")),
                ("decision_source_id", decision.source_id, frozen.source_id),
            ),
        )
        observed_orders.append(int(anchor["sequence"]))
    if observed_orders != sorted(observed_orders):
        raise _field_mismatch(
            "missing-chapter child run changed source order",
            decision,
            "child_topology",
            "family_record_sequence",
            sorted(observed_orders),
            observed_orders,
        )


def _validate_complete_enclosing_topology(
    decision: MissingChapterDecision,
    children: list[JsonObject],
    sections: list[JsonObject],
    content: list[JsonObject],
    redirects: dict[str, str],
) -> None:
    """Require one complete run while allowing only frozen unnumbered enclosures."""
    selected = {item["id"] for item in children}
    enclosing_items = [_resolve_section(sections, ref) for ref in decision.enclosing_section_refs]
    if any(item is None for item in enclosing_items):
        raise StructureContractError("missing-chapter enclosing section is absent")
    enclosing = {str(item["id"]) for item in enclosing_items if item is not None}
    if tuple(item.section_ref for item in decision.enclosing_topology) != (
        decision.enclosing_section_refs
    ):
        raise _field_mismatch(
            "missing-chapter enclosing topology differs from decision",
            decision,
            "enclosing_topology",
            "enclosing_section_refs",
            decision.enclosing_section_refs,
            tuple(item.section_ref for item in decision.enclosing_topology),
        )
    for frozen, enclosing_item in zip(decision.enclosing_topology, enclosing_items, strict=True):
        assert enclosing_item is not None
        anchor = _resolve_content(content, enclosing_item.get("heading_block_id"))
        frozen_parent = _resolve_section_with_redirect(sections, frozen.parent_ref, redirects)
        if anchor is None or frozen_parent is None:
            raise StructureContractError("missing-chapter enclosing heading is absent")
        _validate_frozen_fields(
            "missing-chapter enclosing topology changed",
            decision,
            enclosing_item["id"],
            (
                (
                    "source_id",
                    frozen.source_id,
                    _record_source_id(str(enclosing_item["id"]), "section"),
                ),
                (
                    "stable_item_key",
                    frozen.stable_item_key,
                    enclosing_item.get("source_stable_item_key"),
                ),
                (
                    "heading_block_ref",
                    _entity_tail(frozen.heading_block_ref),
                    _entity_tail(str(enclosing_item.get("heading_block_id"))),
                ),
                ("heading_raw_text", frozen.heading_raw_text, anchor.get("canonical_text")),
                ("family_record_sequence", frozen.content_order, anchor.get("sequence")),
                (
                    "parent_ref",
                    _entity_tail(str(frozen_parent["id"])),
                    _entity_tail(str(enclosing_item.get("parent_section_id"))),
                ),
                ("semantic_level", frozen.semantic_level, enclosing_item.get("semantic_level")),
            ),
        )
    parent = _resolve_section_with_redirect(sections, decision.parent_ref, redirects)
    if parent is None:
        raise StructureContractError("missing-chapter parent is absent")
    by_id = {str(item["id"]): item for item in sections}
    used_enclosing: set[str] = set()
    for child in children:
        current = cast(str | None, child.get("parent_section_id"))
        while current is not None and current != parent["id"]:
            if current not in selected and current not in enclosing:
                raise StructureContractError(
                    "missing-chapter child has an unfrozen enclosing section"
                )
            if current in enclosing:
                used_enclosing.add(current)
            current_item = by_id.get(current)
            if current_item is None:
                raise StructureContractError("missing-chapter child ancestry is dangling")
            current = cast(str | None, current_item.get("parent_section_id"))
        if current != parent["id"]:
            raise StructureContractError("missing-chapter child is outside the frozen parent")
    direct_owners = {
        item["id"]
        for fact in decision.direct_content_topology
        if (item := _resolve_section_with_redirect(sections, fact.original_owner_ref, redirects))
        is not None
        and item["id"] in enclosing
    }
    if used_enclosing | direct_owners != enclosing:
        raise StructureContractError("missing-chapter enclosing topology is not exact")
    content_order = {item["id"]: index for index, item in enumerate(content)}
    semantic_with_order: list[tuple[int, str]] = []
    for section in sections:
        if section["section_kind"].startswith("synthetic_"):
            continue
        anchor = _resolve_content(content, logical_section_start_id(section))
        if anchor is None:
            raise StructureContractError("semantic section lacks a current start anchor")
        semantic_with_order.append((content_order[anchor["id"]], str(section["id"])))
    ordered_ids = [item_id for _, item_id in sorted(semantic_with_order)]
    positions = [index for index, item_id in enumerate(ordered_ids) if item_id in selected]
    permitted = selected | enclosing | _descendants(selected, sections)
    intervening = set(ordered_ids[min(positions) : max(positions) + 1])
    if not intervening <= permitted:
        raise StructureContractError("missing-chapter topology contains an unrelated section")


def _validate_frozen_components_and_boundary(
    decision: MissingChapterDecision, content: list[JsonObject], page_count: int | None
) -> None:
    """Verify retained source block facts before any authorized reclassification."""
    if (
        tuple(item.stable_item_key for item in decision.heading_components)
        != decision.heading_stable_keys
    ):
        raise _field_mismatch(
            "missing-chapter component evidence differs from key order",
            decision,
            "heading_components",
            "heading_stable_keys",
            decision.heading_stable_keys,
            tuple(item.stable_item_key for item in decision.heading_components),
        )
    for frozen in decision.heading_components:
        current = _resolve_content(content, frozen.stable_item_key)
        if current is None:
            raise _field_mismatch(
                "missing-chapter heading component is absent",
                decision,
                frozen.block_id,
                "stable_item_key",
                frozen.stable_item_key,
                None,
            )
        pages = _content_pages(current)
        _validate_frozen_fields(
            "missing-chapter frozen component evidence changed",
            decision,
            current["id"],
            (
                ("block_id", _entity_tail(frozen.block_id), _entity_tail(str(current["id"]))),
                ("stable_item_key", frozen.stable_item_key, current.get("stable_item_key")),
                ("raw_text", frozen.raw_text, current.get("canonical_text")),
                ("physical_page", frozen.physical_page, pages[0] if len(pages) == 1 else None),
                ("family_record_sequence", frozen.sequence, current.get("sequence")),
                ("block_type", frozen.block_type, current.get("block_type")),
                ("content_layer", frozen.content_layer, current.get("content_layer")),
                ("is_toc_row", frozen.is_toc_row, current.get("is_toc_row")),
                ("source_id", frozen.source_id, _record_source_id(str(current["id"]), "block")),
                ("decision_source_id", decision.source_id, frozen.source_id),
            ),
        )
    if decision.following_boundary_kind == "following_heading":
        boundary = _resolve_content(content, decision.following_boundary_stable_key)
        if boundary is None:
            raise _field_mismatch(
                "missing-chapter following boundary is absent",
                decision,
                decision.following_boundary_ref,
                "following_boundary_stable_key",
                decision.following_boundary_stable_key,
                None,
            )
        pages = _content_pages(boundary)
        _validate_frozen_fields(
            "missing-chapter following boundary changed",
            decision,
            boundary["id"],
            (
                (
                    "following_boundary_ref",
                    _entity_tail(str(decision.following_boundary_ref)),
                    _entity_tail(str(boundary["id"])),
                ),
                (
                    "following_boundary_stable_key",
                    decision.following_boundary_stable_key,
                    boundary.get("stable_item_key"),
                ),
                (
                    "following_boundary_raw_text",
                    decision.following_boundary_raw_text,
                    boundary.get("canonical_text"),
                ),
                (
                    "following_boundary_page",
                    decision.following_boundary_page,
                    pages[0] if len(pages) == 1 else None,
                ),
                (
                    "following_boundary_family_sequence",
                    decision.following_boundary_content_order,
                    boundary.get("sequence"),
                ),
            ),
        )
        if decision.following_scope_start_ref is not None:
            scope_start = _resolve_content(
                content,
                decision.following_scope_start_stable_key or decision.following_scope_start_ref,
            )
            if scope_start is None:
                raise _field_mismatch(
                    "missing-chapter scope boundary changed",
                    decision,
                    decision.following_scope_start_ref,
                    "following_scope_start_ref",
                    decision.following_scope_start_ref,
                    None,
                )
            _validate_frozen_fields(
                "missing-chapter scope boundary changed",
                decision,
                scope_start["id"],
                (
                    (
                        "following_scope_start_ref",
                        _entity_tail(decision.following_scope_start_ref),
                        _entity_tail(str(scope_start["id"])),
                    ),
                    (
                        "following_scope_start_global_mixed_index",
                        decision.following_scope_start_content_order,
                        content.index(scope_start),
                    ),
                    (
                        "following_scope_start_stable_key",
                        decision.following_scope_start_stable_key,
                        scope_start.get("stable_item_key"),
                    ),
                    (
                        "scope_start_precedes_heading",
                        True,
                        content.index(scope_start) <= content.index(boundary),
                    ),
                    (
                        "source_id",
                        decision.source_id,
                        _record_source_id(str(scope_start["id"]), str(scope_start["record_type"])),
                    ),
                ),
            )
    elif decision.following_boundary_kind == "document_end":
        source_content = [
            item
            for item in content
            if _record_source_id(str(item["id"]), str(item["record_type"])) == decision.source_id
        ]
        terminal_pages = [page for item in source_content for page in _content_pages(item)]
        source_sequences = [int(item["sequence"]) for item in source_content]
        observed_boundary_source = (
            _record_source_id(decision.following_boundary_ref, "document")
            if decision.following_boundary_ref is not None
            else None
        )
        checks = (
            ("following_boundary_source_id", decision.source_id, observed_boundary_source),
            ("terminal_content_present", True, bool(terminal_pages)),
            ("configured_page_count", decision.following_boundary_page, page_count),
            (
                "terminal_content_within_page_count",
                True,
                bool(
                    terminal_pages and page_count is not None and max(terminal_pages) <= page_count
                ),
            ),
            ("extent_end_page", decision.extent_end_page, decision.following_boundary_page),
            ("terminal_sequence_present", True, bool(source_sequences)),
            (
                "following_boundary_content_order",
                max(source_sequences) + 1 if source_sequences else None,
                decision.following_boundary_content_order,
            ),
        )
        _validate_frozen_fields(
            "missing-chapter document-end boundary changed",
            decision,
            decision.following_boundary_ref,
            checks,
        )


def _resolved_boundary_id(
    decision: MissingChapterDecision,
    sections: list[JsonObject],
    content: list[JsonObject],
    redirects: dict[str, str],
) -> str:
    """Resolve the boundary into the current candidate namespace."""
    if decision.following_boundary_kind == "following_heading":
        boundary = _resolve_content(content, decision.following_boundary_stable_key)
        if boundary is None:
            raise StructureContractError("missing-chapter following boundary is absent")
        return str(boundary["id"])
    parent = _resolve_section_with_redirect(sections, decision.parent_ref, redirects)
    if parent is None:
        raise StructureContractError("missing-chapter parent is absent")
    return str(parent["document_id"])


def _resolved_scope_boundary_id(
    decision: MissingChapterDecision, content: list[JsonObject], boundary_id: str
) -> str:
    """Resolve the first excluded mixed-order record separately from its heading proof."""
    if decision.following_scope_start_ref is None:
        return boundary_id
    item = _resolve_content(
        content,
        decision.following_scope_start_stable_key or decision.following_scope_start_ref,
    )
    if item is None:
        raise StructureContractError("missing-chapter scope boundary is absent")
    return str(item["id"])


def _required_extent(decision: MissingChapterDecision) -> tuple[int, int]:
    if decision.extent_start_page is None or decision.extent_end_page is None:
        raise StructureContractError("eligible missing-chapter decision lacks extent")
    return decision.extent_start_page, decision.extent_end_page


def _resolve_component_ids(
    content: list[JsonObject], decision: MissingChapterDecision
) -> tuple[str, ...]:
    if decision.representation == "toc_children_fallback":
        if decision.heading_stable_keys:
            raise StructureContractError("fallback cannot carry heading components")
        return ()
    components = [_resolve_content(content, key) for key in decision.heading_stable_keys]
    if any(item is None for item in components):
        raise StructureContractError("recovered heading component is absent")
    return tuple(item["id"] for item in components if item is not None)


def _descendants(start: set[str], sections: list[JsonObject]) -> set[str]:
    result = set(start)
    changed = True
    while changed:
        before = len(result)
        result.update(item["id"] for item in sections if item.get("parent_section_id") in result)
        changed = len(result) != before
    return result


def _content_pages(item: JsonObject) -> tuple[int, ...]:
    pages: list[int] = []
    for region in item.get("regions", []):
        page_id = region.get("page_id")
        if isinstance(page_id, str) and "/p" in page_id:
            try:
                pages.append(int(page_id.rsplit("/p", 1)[1]))
            except ValueError as error:
                raise StructureContractError("invalid missing-chapter page ID") from error
    return tuple(sorted(set(pages)))


def _entity_tail(record_id: str) -> str:
    """Compare accepted and candidate-local identifiers without equating namespaces."""
    return record_id.split("/", maxsplit=1)[1] if record_id.startswith("exv1-") else record_id


def _structural_tail(record_id: str, family: str) -> str:
    """Return source and local identity, independent of candidate namespace."""
    marker = f"/{family}/"
    if marker in record_id:
        return record_id.split(marker, maxsplit=1)[1]
    prefix = f"{family}/"
    return record_id[len(prefix) :] if record_id.startswith(prefix) else record_id


def _record_source_id(record_id: str, family: str) -> str:
    """Read a canonical source ID from one namespaced record identifier."""
    marker = f"/{family}/"
    if marker in record_id:
        return record_id.split(marker, maxsplit=1)[1].split("/", maxsplit=1)[0]
    prefix = f"{family}/"
    if record_id.startswith(prefix):
        return record_id[len(prefix) :].split("/", maxsplit=1)[0]
    else:
        raise StructureContractError(f"missing-chapter record has invalid {family} ID")


def _allocate_section_id(sections: list[JsonObject], sequence: int) -> str:
    sample = sections[0]["id"]
    prefix = sample.rsplit("/sec", 1)[0]
    candidate = f"{prefix}/sec{sequence:06d}"
    if any(item["id"] == candidate for item in sections):
        raise StructureContractError("missing-chapter section ID collision")
    return candidate


def _section_start_order(section: JsonObject, content: list[JsonObject]) -> int:
    start_id = logical_section_start_id(section)
    for index, item in enumerate(content):
        if item["id"] == start_id:
            return int(item.get("sequence", index))
    raise StructureContractError("missing-chapter section start record is absent")


def _rebuild(sections: list[JsonObject], content: list[JsonObject], order: dict[str, int]) -> None:
    by_id = {item["id"]: item for item in sections}

    def path(section: JsonObject, seen: frozenset[str] = frozenset()) -> list[str]:
        if section["id"] in seen:
            raise StructureContractError("missing-chapter projection produced a cycle")
        parent_id = section.get("parent_section_id")
        if parent_id is None:
            return [section["id"]]
        parent = by_id.get(parent_id)
        if parent is None:
            raise StructureContractError("missing-chapter projection produced a dangling parent")
        return [*path(parent, seen | {section["id"]}), section["id"]]

    starts = {
        item["id"]: order.get(cast(str, logical_section_start_id(item)), -1) for item in sections
    }
    roots = sorted(
        (item for item in sections if item["section_kind"].startswith("synthetic_")),
        key=lambda item: item["sequence"],
    )
    semantic = sorted(
        (item for item in sections if not item["section_kind"].startswith("synthetic_")),
        key=lambda item: (starts[item["id"]], int(item["semantic_level"])),
    )
    sections[:] = [*roots, *semantic]
    for sequence, section in enumerate(sections, start=1):
        section["sequence"] = sequence
        section["section_path_ids"] = path(section)
        positioned = [
            (order[item["id"]], item["id"])
            for item in content
            if item["section_id"] == section["id"]
        ]
        positioned.extend(
            (starts[child["id"]], child["id"])
            for child in semantic
            if child.get("parent_section_id") == section["id"]
        )
        section["ordered_child_ids"] = [item_id for _, item_id in sorted(positioned)]
