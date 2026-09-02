"""Diagnostics shared by PDF outline cleanup and traversal."""

from __future__ import annotations

from typing import Any

from er_commons.document_parsing.heading_evidence_parsing.errors import (
    HierarchyInferenceContractError,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_types import JsonObject


def parentless_child_list_error(
    *,
    stage: str,
    reason: str,
    children: list[Any],
    title: str | None = None,
    depth: int | None = None,
    parent_id: str | None = None,
) -> HierarchyInferenceContractError:
    """Build one contextual error for an outline child list without a usable parent."""
    direct_count = sum(not isinstance(child, list) for child in children)
    nested_count = len(children) - direct_count
    context = [f"stage={stage}", f"direct_children={direct_count}", f"nested_lists={nested_count}"]
    if title is not None:
        context.append(f"title={title!r}")
    if depth is not None:
        context.append(f"depth={depth}")
    if parent_id is not None:
        context.append(f"parent_id={parent_id}")
    return HierarchyInferenceContractError(
        f"outline child list has no parent: {reason}; " + ", ".join(context)
    )


def missing_leaf_diagnostic(title: str) -> JsonObject:
    """Describe one invalid leaf omitted from hierarchy evidence."""
    return {
        "reading_order_index": None,
        "stable_item_key": None,
        "code": "TOC_TARGET_MISSING",
        "detail": f"PDF outline leaf has no valid destination and was omitted: {title}",
    }


def container_omission_diagnostic(
    title: str, *, retained_count: int, invalid_count: int, duplicate_subtree: bool
) -> JsonObject:
    """Describe one evidence-backed technical or duplicate-subtree omission."""
    if duplicate_subtree:
        detail = (
            f"Omitted duplicate broken outline subtree '{title}'; all {invalid_count} "
            "invalid leaf bookmarks have valid duplicate or unique visible-heading evidence."
        )
    else:
        detail = (
            f"Omitted technical filename container '{title}' and retained "
            f"{retained_count} ordered descendant bookmarks; {invalid_count} invalid "
            "leaf bookmarks remain omissions."
        )
    return {
        "reading_order_index": None,
        "stable_item_key": None,
        "code": "OUTLINE_FILENAME_CONTAINER_OMITTED",
        "detail": detail,
    }
