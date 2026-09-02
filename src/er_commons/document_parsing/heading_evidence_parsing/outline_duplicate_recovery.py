"""Prove duplicate broken outline subtrees from complete ordered structure."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from er_commons.document_parsing.heading_evidence_parsing.outline_types import OutlineTreeNode
from er_commons.document_parsing.heading_evidence_parsing.text_evidence import normalize_text


@dataclass(frozen=True)
class OutlineSubtreeSignature:
    """Normalized title tree whose child tuple preserves source order."""

    title: str
    children: tuple[OutlineSubtreeSignature, ...]


def index_valid_subtree_signatures(
    nodes: list[OutlineTreeNode],
) -> dict[OutlineSubtreeSignature, int]:
    """Count fully destination-backed subtrees by exact ordered title structure."""
    counts: dict[OutlineSubtreeSignature, int] = {}
    for node in _walk(nodes):
        if _all_destinations_have_pages(node):
            signature = _signature(node)
            counts[signature] = counts.get(signature, 0) + 1
    return counts


def is_unique_exact_duplicate_broken_subtree(
    tree: OutlineTreeNode,
    *,
    valid_signature_counts: Mapping[OutlineSubtreeSignature, int],
) -> bool:
    """Accept a fully broken tree only when one valid tree has the same signature."""
    return bool(
        tree.children
        and _all_destinations_are_missing(tree)
        and valid_signature_counts.get(_signature(tree)) == 1
    )


def _signature(tree: OutlineTreeNode) -> OutlineSubtreeSignature:
    return OutlineSubtreeSignature(
        title=normalize_text(tree.title),
        children=tuple(_signature(child) for child in tree.children),
    )


def _all_destinations_have_pages(tree: OutlineTreeNode) -> bool:
    return tree.page is not None and all(
        _all_destinations_have_pages(child) for child in tree.children
    )


def _all_destinations_are_missing(tree: OutlineTreeNode) -> bool:
    return tree.page is None and all(
        _all_destinations_are_missing(child) for child in tree.children
    )


def _walk(nodes: list[OutlineTreeNode]) -> list[OutlineTreeNode]:
    flattened: list[OutlineTreeNode] = []
    for node in nodes:
        flattened.append(node)
        flattened.extend(_walk(node.children))
    return flattened
