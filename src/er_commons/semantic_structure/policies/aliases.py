"""Deterministic target-alias normalization and resolution policies."""

from __future__ import annotations

from er_commons.semantic_structure.bundle import JsonObject, SemanticBundleView
from er_commons.semantic_structure.constants import ALIAS_TARGET_TYPES
from er_commons.semantic_structure.errors import SemanticContractError
from er_commons.semantic_structure.normalization import normalize_alias

TARGET_TYPE_BY_ALIAS_KIND = {
    "document": "document",
    "appendix": "section",
    "section": "section",
    "table": "table",
    "figure": "figure",
    "printed_page": "page",
}

# Structural targets precede printed-page lookup keys. Within a type, the
# first target's physical or mixed-content position determines record order.
TARGET_TYPE_ORDER = {
    "document": 0,
    "section": 1,
    "table": 2,
    "figure": 3,
    "page": 4,
}


def validate_target_aliases(view: SemanticBundleView) -> None:
    """Validate alias order, spelling, collision state, and target evidence."""
    _validate_alias_order(view)
    seen_keys: set[tuple[str, str]] = set()
    for alias in view.aliases:
        _validate_alias_document_scope(view, alias)
        _validate_unique_alias_key(alias, seen_keys)
        _validate_raw_spellings(alias)
        _validate_collision_state(alias)
        _validate_alias_targets(view, alias)


def _validate_alias_document_scope(view: SemanticBundleView, alias: JsonObject) -> None:
    """Keep alias identity and its declared document in one namespace."""
    if alias["document_id"] != view.bundle["document_id"] or not view.belongs_to_document(
        alias["id"]
    ):
        raise SemanticContractError(f"target alias escaped document scope: {alias['id']}")


def _validate_alias_order(view: SemanticBundleView) -> None:
    """Require contiguous sequences and the contract's deterministic sort order."""
    aliases = view.aliases
    expected = list(range(1, len(aliases) + 1))
    actual = [alias["sequence"] for alias in aliases]
    if actual != expected:
        raise SemanticContractError("target aliases are not in deterministic sequence")
    if aliases != sorted(aliases, key=lambda alias: _alias_sort_key(view, alias)):
        raise SemanticContractError("target aliases are not in deterministic order")


def _alias_sort_key(view: SemanticBundleView, alias: JsonObject) -> tuple[object, ...]:
    """Project one alias onto its persisted document-order key."""
    targets = alias["targets"]
    target_type = targets[0]["target_type"]
    target_orders = [_target_document_order(view, target) for target in targets]
    if target_orders != sorted(target_orders):
        raise SemanticContractError(f"alias targets are not in document order: {alias['id']}")
    return (
        TARGET_TYPE_ORDER[target_type],
        target_orders[0],
        alias["alias_kind"],
        alias["normalized_alias"].encode("utf-8"),
    )


def _target_document_order(view: SemanticBundleView, target: JsonObject) -> int:
    """Return the physical or mixed-content position of one alias target."""
    target_type = target["target_type"]
    target_id = target["target_id"]
    if target_type == "document":
        return 0
    if target_type == "page":
        observation = _page_observation_by_id(view).get(target_id)
        return -1 if observation is None else int(observation["physical_page_number"])
    if target_type == "section":
        section = view.sections_by_id.get(target_id)
        if section is None or section["heading_block_id"] is None:
            return -1
        return view.global_order_by_id.get(section["heading_block_id"], -1)
    return view.global_order_by_id.get(target_id, -1)


def _validate_unique_alias_key(
    alias: JsonObject,
    seen_keys: set[tuple[str, str]],
) -> None:
    """Require one record per alias kind and normalized spelling."""
    alias_key = (alias["alias_kind"], alias["normalized_alias"])
    if alias_key in seen_keys:
        raise SemanticContractError(f"normalized alias key is duplicated: {alias_key}")
    seen_keys.add(alias_key)


def _validate_raw_spellings(alias: JsonObject) -> None:
    """Require every source spelling to produce the persisted alias key."""
    normalized_alias = alias["normalized_alias"]
    mismatches = [
        value for value in alias["raw_values"] if normalize_alias(value) != normalized_alias
    ]
    if mismatches:
        raise SemanticContractError(
            f"target alias normalization differs for {alias['id']}: {mismatches}"
        )


def _validate_collision_state(alias: JsonObject) -> None:
    """Represent one target as unique and multiple targets as ambiguous."""
    target_ids = [target["target_id"] for target in alias["targets"]]
    expected_status = "unique" if len(target_ids) == 1 else "ambiguous"
    has_duplicate_target = len(set(target_ids)) != len(target_ids)
    if alias["resolution_status"] != expected_status or has_duplicate_target:
        raise SemanticContractError(f"alias collision state differs for {alias['id']}")


def _validate_alias_targets(view: SemanticBundleView, alias: JsonObject) -> None:
    """Keep target types closed and TOC evidence attached to body sections."""
    for target in alias["targets"]:
        if target["target_type"] not in ALIAS_TARGET_TYPES:
            raise SemanticContractError(
                f"alias target type is forbidden for {alias['id']}: {target['target_type']}"
            )
        expected_target_type = TARGET_TYPE_BY_ALIAS_KIND[alias["alias_kind"]]
        if target["target_type"] != expected_target_type:
            raise SemanticContractError(
                f"alias kind and target type differ for {alias['id']}: "
                f"expected {expected_target_type}, got {target['target_type']}"
            )
        if target["evidence_kind"] == "visible_toc_reconciliation":
            _validate_toc_target(view, alias, target)
        if target["target_type"] == "page" and not _has_printed_page_provenance(target):
            raise SemanticContractError(f"printed-page alias has invalid provenance: {alias['id']}")
        if not _target_exists_with_declared_type(view, alias, target):
            raise SemanticContractError(
                f"alias target does not exist with declared type: {target['target_id']}"
            )
        target_content = view.content_by_id.get(target["target_id"])
        if target_content is not None and target_content["is_toc_row"]:
            raise SemanticContractError(f"TOC rows cannot be alias targets: {target['target_id']}")


def _validate_toc_target(
    view: SemanticBundleView,
    alias: JsonObject,
    target: JsonObject,
) -> None:
    """Require a visible-TOC alias to resolve to a reconciled body section."""
    section = view.sections_by_id.get(target["target_id"])
    is_reconciled_body_section = (
        section is not None
        and section["section_kind"] == "semantic"
        and section["content_layer"] == "body"
        and target["toc_reconciliation_ref"] is not None
    )
    if not is_reconciled_body_section:
        raise SemanticContractError(
            f"TOC alias does not target a reconciled body section: {alias['id']}"
        )


def _has_printed_page_provenance(target: JsonObject) -> bool:
    """Require page aliases to cite resolved-label evidence and no TOC row."""
    return bool(
        target["evidence_kind"] == "resolved_printed_page_label"
        and target["toc_reconciliation_ref"] is None
    )


def _target_exists_with_declared_type(
    view: SemanticBundleView,
    alias: JsonObject,
    target: JsonObject,
) -> bool:
    """Check target identity where the semantic fixture contains that family."""
    target_id = target["target_id"]
    target_type = target["target_type"]
    if target_type == "document":
        return bool(target_id == view.bundle["document_id"])
    if target_type == "section":
        return target_id in view.sections_by_id
    if target_type in {"table", "figure"}:
        record = view.content_by_id.get(target_id)
        return bool(record is not None and record["record_type"] == target_type)
    if target_type == "page":
        return _is_resolved_printed_page_target(view, alias, target_id)
    return False


def _is_resolved_printed_page_target(
    view: SemanticBundleView,
    alias: JsonObject,
    target_id: str,
) -> bool:
    """Match a printed-page alias to one existing page's resolved label."""
    observation = _page_observation_by_id(view).get(target_id)
    if observation is None or observation["resolved_state"] != "resolved":
        return False
    return bool(normalize_alias(observation["resolved_label"]) == alias["normalized_alias"])


def _page_observation_by_id(view: SemanticBundleView) -> dict[str, JsonObject]:
    """Derive canonical page IDs from document identity and physical page number."""
    extraction_id, record_type, source_id = view.bundle["document_id"].split("/", maxsplit=2)
    if record_type != "document":
        raise SemanticContractError(f"invalid canonical document ID: {view.bundle['document_id']}")
    return {
        f"{extraction_id}/page/{source_id}/p{item['physical_page_number']:06d}": item
        for item in view.page_labels
    }
