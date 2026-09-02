"""Clean malformed or uniquely duplicated subtrees in embedded PDF outlines."""

from __future__ import annotations

import re
from typing import Any

from er_commons.document_parsing.heading_evidence_parsing.errors import (
    HierarchyInferenceContractError,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_diagnostics import (
    container_omission_diagnostic,
    missing_leaf_diagnostic,
    parentless_child_list_error,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_duplicate_recovery import (
    OutlineSubtreeSignature,
    index_valid_subtree_signatures,
    is_unique_exact_duplicate_broken_subtree,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_normalization import (
    outline_reference_key,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_support import (
    DISTINCTIVE_NUMBER,
    appendix_identifier,
    semantic_title_tokens,
    valid_outline_page,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_types import (
    JsonObject,
    OutlineCleanResult,
    OutlineTreeNode,
    RawReferenceKey,
)
from er_commons.document_parsing.heading_evidence_parsing.text_evidence import normalize_text
from er_commons.document_parsing.heading_evidence_parsing.types import ObservedItem

_TECHNICAL_FILENAME_CONTAINER = re.compile(
    r"(?:^|[_\s])(?:appendix[_\s]+complete[_\s]+[0-9]+|pages)(?:\.pdf)?$",
    re.IGNORECASE,
)


def requires_technical_outline_cleanup(
    reader: Any,
    outline: list[Any],
    *,
    malformed_filename_containers: frozenset[RawReferenceKey],
) -> bool:
    """Select cleanup for supported malformed or uniquely duplicated branches."""
    trees = _parse_outline_tree(reader, outline)
    valid_signatures = index_valid_subtree_signatures(trees)
    return any(
        _is_cleanup_eligible_container(
            tree,
            malformed_filename_containers=malformed_filename_containers,
            valid_signature_counts=valid_signatures,
        )
        and any(child.page is None for child in _iter_outline_tree(tree.children))
        for tree in _iter_outline_tree(trees)
    )


def clean_malformed_outline_tree(
    *,
    reader: Any,
    outline: list[Any],
    malformed_filename_containers: frozenset[RawReferenceKey],
    heading_features: list[ObservedItem],
) -> tuple[list[Any], list[JsonObject]]:
    """Flatten technical folders and remove only uniquely matched duplicate trees."""
    trees = _parse_outline_tree(reader, outline)
    valid_titles = {
        normalize_text(node.title) for node in _iter_outline_tree(trees) if node.page is not None
    }
    valid_signatures = index_valid_subtree_signatures(trees)
    cleaned = _clean_outline_nodes(
        trees,
        malformed_filename_containers=malformed_filename_containers,
        valid_titles=valid_titles,
        valid_signature_counts=valid_signatures,
        heading_features=heading_features,
        has_anchored_parent=False,
    )
    return _serialize_outline_tree(cleaned.nodes), cleaned.diagnostics


def omit_transparent_filename_container(
    *,
    reader: Any,
    node: Any,
    title: str,
    children: list[Any],
    malformed_filename_containers: frozenset[RawReferenceKey],
    diagnostics: list[JsonObject],
) -> bool:
    """Flatten one supported PDF-filename folder while preserving valid children."""
    malformed_destination = outline_reference_key(node) in malformed_filename_containers
    if not normalize_text(title).endswith(".pdf") or (
        not malformed_destination
        and (appendix_identifier(title) is not None or DISTINCTIVE_NUMBER.search(title) is not None)
    ):
        return False
    direct_children = [child for child in children if not isinstance(child, list)]
    child_pages = [valid_outline_page(reader, child) for child in direct_children]
    if not malformed_destination and any(page is None for page in child_pages):
        return False
    pages = [page for page in child_pages if page is not None]
    if not pages or pages != sorted(pages):
        return False
    missing_count = sum(page is None for page in child_pages)
    diagnostics.append(
        {
            "reading_order_index": None,
            "stable_item_key": None,
            "code": "OUTLINE_FILENAME_CONTAINER_OMITTED",
            "detail": (
                f"Omitted {'malformed' if malformed_destination else 'destinationless'} "
                f"PDF filename container '{title}' and flattened {len(pages)} ordered "
                f"child bookmarks"
                + (
                    f"; {missing_count} invalid child bookmarks remain leaf omissions."
                    if missing_count
                    else "."
                )
            ),
        }
    )
    return True


def _parse_outline_tree(reader: Any, nodes: list[Any]) -> list[OutlineTreeNode]:
    parsed: list[OutlineTreeNode] = []
    previous: OutlineTreeNode | None = None
    for node in nodes:
        if isinstance(node, list):
            if previous is None:
                raise parentless_child_list_error(
                    stage="tree_parse",
                    reason="child list appears before any bookmark",
                    children=node,
                )
            previous.children = _parse_outline_tree(reader, node)
            continue
        title = getattr(node, "title", None)
        if not isinstance(title, str) or not normalize_text(title):
            raise HierarchyInferenceContractError("outline title is invalid")
        parsed_node = OutlineTreeNode(node=node, title=title, page=valid_outline_page(reader, node))
        parsed.append(parsed_node)
        previous = parsed_node
    return parsed


def _iter_outline_tree(nodes: list[OutlineTreeNode]) -> list[OutlineTreeNode]:
    flattened: list[OutlineTreeNode] = []
    for node in nodes:
        flattened.append(node)
        flattened.extend(_iter_outline_tree(node.children))
    return flattened


def _clean_outline_nodes(
    nodes: list[OutlineTreeNode],
    *,
    malformed_filename_containers: frozenset[RawReferenceKey],
    valid_titles: set[str],
    valid_signature_counts: dict[OutlineSubtreeSignature, int],
    heading_features: list[ObservedItem],
    has_anchored_parent: bool,
) -> OutlineCleanResult:
    """Clean eligible folders without hiding an unsupported broken subtree."""
    result = OutlineCleanResult()
    for tree in nodes:
        supported = _is_cleanup_eligible_container(
            tree,
            malformed_filename_containers=malformed_filename_containers,
            valid_signature_counts=valid_signature_counts,
        )
        if tree.page is None and tree.children and not supported:
            result.nodes.append(tree)
            result.pages.extend(
                node.page for node in _iter_outline_tree(tree.children) if node.page is not None
            )
            continue
        children = _clean_outline_nodes(
            tree.children,
            malformed_filename_containers=malformed_filename_containers,
            valid_titles=valid_titles,
            valid_signature_counts=valid_signature_counts,
            heading_features=heading_features,
            has_anchored_parent=has_anchored_parent or tree.page is not None,
        )
        if tree.page is not None:
            result.nodes.append(OutlineTreeNode(tree.node, tree.title, tree.page, children.nodes))
            _merge_clean_result(result, children, pages=[tree.page, *children.pages])
        elif not tree.children:
            result.invalid_leaf_titles.append(tree.title)
            result.diagnostics.append(missing_leaf_diagnostic(tree.title))
        elif children.nodes:
            _retain_transparent_children(result, tree, children)
        else:
            omission = _omit_fully_broken_container(
                tree,
                children,
                has_anchored_parent=has_anchored_parent,
                valid_titles=valid_titles,
                heading_features=heading_features,
            )
            _merge_clean_result(result, omission)
    return result


def _is_cleanup_eligible_container(
    tree: OutlineTreeNode,
    *,
    malformed_filename_containers: frozenset[RawReferenceKey],
    valid_signature_counts: dict[OutlineSubtreeSignature, int],
) -> bool:
    return bool(
        tree.page is None
        and tree.children
        and (
            _is_supported_technical_container(
                tree, malformed_filename_containers=malformed_filename_containers
            )
            or is_unique_exact_duplicate_broken_subtree(
                tree, valid_signature_counts=valid_signature_counts
            )
        )
    )


def _merge_clean_result(
    result: OutlineCleanResult,
    child: OutlineCleanResult,
    *,
    pages: list[int] | None = None,
) -> None:
    result.diagnostics.extend(child.diagnostics)
    result.invalid_leaf_titles.extend(child.invalid_leaf_titles)
    result.pages.extend(child.pages if pages is None else pages)


def _retain_transparent_children(
    result: OutlineCleanResult, tree: OutlineTreeNode, children: OutlineCleanResult
) -> None:
    if not children.pages or children.pages != sorted(children.pages):
        raise HierarchyInferenceContractError(
            "transparent outline container children are unordered"
        )
    result.nodes.extend(children.nodes)
    result.diagnostics.append(
        container_omission_diagnostic(
            tree.title,
            retained_count=len(_iter_outline_tree(children.nodes)),
            invalid_count=len(children.invalid_leaf_titles),
            duplicate_subtree=False,
        )
    )
    _merge_clean_result(result, children)


def _omit_fully_broken_container(
    tree: OutlineTreeNode,
    children: OutlineCleanResult,
    *,
    has_anchored_parent: bool,
    valid_titles: set[str],
    heading_features: list[ObservedItem],
) -> OutlineCleanResult:
    """Omit a broken folder only when structure or replacement evidence supports it."""
    if not children.invalid_leaf_titles:
        raise parentless_child_list_error(
            stage="cleanup",
            reason="cleanup retained neither children nor invalid-leaf replacement evidence",
            children=tree.children,
            title=tree.title,
        )
    has_replacement_evidence = all(
        _invalid_leaf_has_replacement(
            title, valid_titles=valid_titles, heading_features=heading_features
        )
        for title in children.invalid_leaf_titles
    )
    if not has_anchored_parent and not has_replacement_evidence:
        raise HierarchyInferenceContractError(
            "destinationless technical outline subtree has no anchored parent "
            f"or replacement evidence: {tree.title}"
        )
    diagnostics = [
        container_omission_diagnostic(
            tree.title,
            retained_count=0,
            invalid_count=len(children.invalid_leaf_titles),
            duplicate_subtree=has_replacement_evidence,
        )
    ]
    if not has_replacement_evidence:
        diagnostics.extend(children.diagnostics)
    return OutlineCleanResult(
        diagnostics=diagnostics, invalid_leaf_titles=list(children.invalid_leaf_titles)
    )


def _is_supported_technical_container(
    tree: OutlineTreeNode, *, malformed_filename_containers: frozenset[RawReferenceKey]
) -> bool:
    normalized = normalize_text(tree.title)
    return (
        outline_reference_key(tree.node) in malformed_filename_containers
        or normalized.endswith(".pdf")
        or _TECHNICAL_FILENAME_CONTAINER.search(normalized) is not None
    )


def _invalid_leaf_has_replacement(
    title: str, *, valid_titles: set[str], heading_features: list[ObservedItem]
) -> bool:
    normalized = normalize_text(title)
    if normalized in valid_titles:
        return True
    title_tokens = semantic_title_tokens(normalized)
    if len(title_tokens) < 3:
        return False
    matches = [
        feature
        for feature in heading_features
        if feature["content_layer"] == "body"
        and feature["raw_role"] == "section_header"
        and title_tokens <= semantic_title_tokens(feature["normalized_text"])
    ]
    return len(matches) == 1


def _serialize_outline_tree(nodes: list[OutlineTreeNode]) -> list[Any]:
    serialized: list[Any] = []
    for tree in nodes:
        serialized.append(tree.node)
        if tree.children:
            serialized.append(_serialize_outline_tree(tree.children))
    return serialized
