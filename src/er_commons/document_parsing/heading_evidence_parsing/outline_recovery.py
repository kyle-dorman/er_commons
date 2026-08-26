"""Recover destinationless semantic outline containers from unique evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from er_commons.document_parsing.heading_evidence_parsing.outline_support import (
    appendix_identifier,
    fuzzy_container_title_matches,
    native_page_text,
    semantic_title_tokens,
    valid_outline_page,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_types import JsonObject
from er_commons.document_parsing.heading_evidence_parsing.text_evidence import normalize_text
from er_commons.document_parsing.heading_evidence_parsing.types import ObservedItem


@dataclass(frozen=True)
class RecoveryContext:
    """Stable hierarchy location and output sinks for one recovery attempt."""

    parent_id: str | None
    depth: int
    root_depth: int
    heading_features: list[ObservedItem]
    observations: list[JsonObject]
    diagnostics: list[JsonObject]


def recover_appendix_container(
    *, reader: Any, title: str, children: list[Any], context: RecoveryContext
) -> str | None:
    """Bind one non-clickable container using unique adjacent-page evidence."""
    pages = _ordered_direct_child_pages(reader, children)
    if pages is None or not pages or pages[0] <= 1:
        return None
    identifier = appendix_identifier(title)
    preceding_page = pages[0] - 1
    matches = [
        feature
        for feature in context.heading_features
        if feature["content_layer"] == "body"
        and feature["raw_role"] == "section_header"
        and feature["physical_page"] == preceding_page
        and appendix_identifier(feature["text"]) == identifier
    ]
    if identifier is not None and len(matches) == 1:
        match = matches[0]
        return _append_recovered_container(
            title=title,
            normalized_title=match["normalized_text"],
            physical_page=preceding_page,
            context=context,
            reading_order_index=match["reading_order_index"],
            stable_item_key=match["stable_item_key"],
            evidence=(
                f"unique appendix identifier '{identifier}' and "
                f"{len(children)} ordered child destinations"
            ),
        )
    return _recover_from_fuzzy_native_title(
        reader=reader,
        title=title,
        pages=pages,
        preceding_page=preceding_page,
        context=context,
    )


def _recover_from_fuzzy_native_title(
    *,
    reader: Any,
    title: str,
    pages: list[int],
    preceding_page: int,
    context: RecoveryContext,
) -> str | None:
    matches = [
        (page, text)
        for page in (preceding_page, pages[0])
        if (text := native_page_text(reader, page)) and fuzzy_container_title_matches(title, text)
    ]
    if len(matches) != 1:
        return None
    physical_page, native_text = matches[0]
    return _append_recovered_container(
        title=title,
        normalized_title=normalize_text(title),
        physical_page=physical_page,
        context=context,
        reading_order_index=None,
        stable_item_key=None,
        evidence=(
            "unique fuzzy title evidence on the preceding or first-child page "
            f"({len(native_text)} native characters)"
        ),
    )


def recover_visible_title_container(
    *, reader: Any, title: str, children: list[Any], context: RecoveryContext
) -> str | None:
    """Bind a destinationless semantic title to one unique nearby title page."""
    pages = _ordered_direct_child_pages(reader, children)
    if pages is None or not pages:
        return None
    title_tokens = semantic_title_tokens(title)
    if len(title_tokens) < 2:
        return None
    candidates = _nearby_exact_title_candidates(reader, title_tokens, pages[0])
    candidate_pages = {page for page, _ in candidates}
    feature_matches = [
        feature
        for feature in context.heading_features
        if feature["content_layer"] == "body"
        and feature["raw_role"] == "section_header"
        and title_tokens <= semantic_title_tokens(feature["normalized_text"])
        and feature["physical_page"] in candidate_pages
    ]
    if len(feature_matches) == 1:
        physical_page = int(feature_matches[0]["physical_page"])
        page_text = native_page_text(reader, physical_page)
    elif len(candidates) == 1:
        physical_page, page_text = candidates[0]
    else:
        return None
    return _append_recovered_container(
        title=title,
        normalized_title=normalize_text(title),
        physical_page=physical_page,
        context=context,
        reading_order_index=None,
        stable_item_key=None,
        evidence=(
            "unique exact semantic-title evidence on a nearby title page "
            f"({len(page_text)} native characters)"
        ),
    )


def _ordered_direct_child_pages(reader: Any, children: list[Any]) -> list[int] | None:
    direct_children = [child for child in children if not isinstance(child, list)]
    child_pages = [valid_outline_page(reader, child) for child in direct_children]
    if any(page is None for page in child_pages):
        return None
    pages = [page for page in child_pages if page is not None]
    return pages if pages == sorted(pages) else None


def _nearby_exact_title_candidates(
    reader: Any, title_tokens: set[str], first_child_page: int
) -> list[tuple[int, str]]:
    candidates: list[tuple[int, str]] = []
    for physical_page in range(max(1, first_child_page - 12), first_child_page + 1):
        page_text = native_page_text(reader, physical_page)
        if title_tokens <= semantic_title_tokens(page_text):
            candidates.append((physical_page, page_text))
    return candidates


def _append_recovered_container(
    *,
    title: str,
    normalized_title: str,
    physical_page: int,
    context: RecoveryContext,
    reading_order_index: int | None,
    stable_item_key: str | None,
    evidence: str,
) -> str:
    """Append one uniquely evidenced synthetic outline parent."""
    outline_id = f"outline-{len(context.observations):08d}"
    context.observations.append(
        {
            "outline_id": outline_id,
            "parent_outline_id": context.parent_id,
            "title": title,
            "normalized_title": normalized_title,
            "physical_page": physical_page,
            "raw_depth": context.depth,
            "source_root_depth": context.root_depth,
            "effective_level": min(6, context.depth - context.root_depth + 1),
        }
    )
    context.diagnostics.append(
        {
            "reading_order_index": reading_order_index,
            "stable_item_key": stable_item_key,
            "code": "OUTLINE_CONTAINER_RECOVERED",
            "detail": (
                f"Bound destinationless PDF outline container '{title}' to physical page "
                f"{physical_page} from {evidence}."
            ),
        }
    )
    return outline_id
