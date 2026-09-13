"""Regenerate frozen 06E child extents from complete compact content ownership."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from typing import Any

from er_commons.document_records.document_structure.missing_chapters import (
    ChapterChildEvidence,
    MissingChapterDecision,
)

JsonObject = dict[str, Any]


def amend_child_subtree_extents(
    decisions: Iterable[MissingChapterDecision],
    *,
    sections: Iterable[JsonObject],
    content: Iterable[JsonObject],
) -> tuple[tuple[MissingChapterDecision, ...], tuple[JsonObject, ...]]:
    """Replace block-only child extents with complete block/table/figure extents."""
    section_rows = tuple(sections)
    content_rows = tuple(content)
    by_key = _unique_sections_by_key(section_rows)
    children = _section_children(section_rows)
    amended: list[MissingChapterDecision] = []
    corrections: list[JsonObject] = []
    for decision in decisions:
        topology: list[ChapterChildEvidence] = []
        for frozen in decision.child_topology:
            section = by_key.get(frozen.section_ref)
            if section is None:
                raise ValueError(f"missing child section stable key: {frozen.section_ref}")
            descendant_ids = _descendants(str(section["id"]), children)
            pages = tuple(
                page
                for item in content_rows
                if item.get("section_id") in descendant_ids
                for page in _content_pages(item)
            )
            if not pages:
                raise ValueError(
                    f"child section has no compact content pages: {frozen.section_ref}"
                )
            observed = (min(pages), max(pages))
            expected = (frozen.extent_start_page, frozen.extent_end_page)
            topology.append(
                replace(
                    frozen,
                    extent_start_page=observed[0],
                    extent_end_page=observed[1],
                )
            )
            if observed != expected:
                corrections.append(
                    {
                        "chapter_marker": decision.chapter_marker,
                        "section_ref": frozen.section_ref,
                        "from_extent": list(expected),
                        "to_extent": list(observed),
                    }
                )
        amended.append(replace(decision, child_topology=tuple(topology)))
    return tuple(amended), tuple(corrections)


def _unique_sections_by_key(sections: tuple[JsonObject, ...]) -> dict[str, JsonObject]:
    result: dict[str, JsonObject] = {}
    for section in sections:
        key = section.get("source_stable_item_key")
        if not isinstance(key, str):
            continue
        if key in result:
            raise ValueError(f"duplicate section stable key: {key}")
        result[key] = section
    return result


def _section_children(sections: tuple[JsonObject, ...]) -> dict[str, tuple[str, ...]]:
    mutable: dict[str, list[str]] = {}
    for section in sections:
        parent = section.get("parent_section_id")
        child = section.get("id")
        if isinstance(parent, str) and isinstance(child, str):
            mutable.setdefault(parent, []).append(child)
    return {parent: tuple(values) for parent, values in mutable.items()}


def _descendants(section_id: str, children: dict[str, tuple[str, ...]]) -> set[str]:
    result = {section_id}
    pending = [section_id]
    while pending:
        for child in children.get(pending.pop(), ()):
            if child not in result:
                result.add(child)
                pending.append(child)
    return result


def _content_pages(item: JsonObject) -> tuple[int, ...]:
    pages: set[int] = set()
    for region in item.get("regions", []):
        page_id = region.get("page_id") if isinstance(region, dict) else None
        if not isinstance(page_id, str) or "/p" not in page_id:
            continue
        try:
            pages.add(int(page_id.rsplit("/p", maxsplit=1)[1]))
        except ValueError as error:
            raise ValueError(f"invalid compact content page ID: {page_id}") from error
    return tuple(sorted(pages))
