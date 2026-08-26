"""Deterministic page and table selection policies for Task 04."""

from __future__ import annotations

from collections import defaultdict

from er_commons.human_review_support.task04.models import PageProfile, TableFamilyCandidate


def select_content_pages(
    candidates: list[PageProfile], *, region_count: int = 3
) -> tuple[PageProfile, ...]:
    """Select one content-bearing page from each longitudinal document region."""
    if region_count < 1:
        raise ValueError("region_count must be positive")
    ordered = sorted(candidates, key=lambda item: item.physical_page)
    if len(ordered) <= region_count:
        return tuple(ordered)

    selected = [_best_region_page(ordered, region, region_count) for region in range(region_count)]
    return _replace_empty_pages(ordered, selected)


def _best_region_page(ordered: list[PageProfile], region: int, region_count: int) -> PageProfile:
    """Choose the strongest page from one stable longitudinal slice."""
    start = len(ordered) * region // region_count
    end = len(ordered) * (region + 1) // region_count
    members = ordered[start:end]
    content_bearing = [item for item in members if item.is_content_bearing]
    pool = content_bearing or members
    center = (members[0].physical_page + members[-1].physical_page) / 2
    return max(
        pool,
        key=lambda item: (
            item.review_score,
            -abs(item.physical_page - center),
            -item.physical_page,
        ),
    )


def _replace_empty_pages(
    ordered: list[PageProfile], selected: list[PageProfile]
) -> tuple[PageProfile, ...]:
    """Replace empty short-document slices with strong unused evidence."""
    used = {item.physical_page for item in selected}
    replacements = sorted(
        (item for item in ordered if item.physical_page not in used and item.review_score > 0),
        key=lambda item: (-item.review_score, item.physical_page),
    )
    for index, item in enumerate(selected):
        if item.review_score > 0 or not replacements:
            continue
        replacement = replacements.pop(0)
        used.discard(item.physical_page)
        used.add(replacement.physical_page)
        selected[index] = replacement
    return tuple(selected)


def select_nearby_content_page(
    candidates: list[PageProfile], anchor_page: int, *, radius: int = 2
) -> PageProfile | None:
    """Choose the strongest content page near an exact structural anchor."""
    if radius < 0:
        raise ValueError("radius must be non-negative")
    nearby = [item for item in candidates if abs(item.physical_page - anchor_page) <= radius]
    if not nearby:
        return None
    content_bearing = [item for item in nearby if item.is_content_bearing]
    return max(
        content_bearing or nearby,
        key=lambda item: (
            item.review_score,
            -abs(item.physical_page - anchor_page),
            -item.physical_page,
        ),
    )


def select_table_families(
    candidates: list[TableFamilyCandidate],
    *,
    main_source_id: str,
    main_limit: int = 6,
    appendix_limit: int = 2,
) -> tuple[TableFamilyCandidate, ...]:
    """Select the approved deterministic main and appendix table workload."""
    if main_limit < 1 or appendix_limit < 1:
        raise ValueError("table selection limits must be positive")
    keys = [(item.source_id, item.family_id) for item in candidates]
    if len(keys) != len(set(keys)):
        raise ValueError("table candidates must be unique by source and family")

    def rank(item: TableFamilyCandidate) -> tuple[int, int, str]:
        return (-item.page_count, -item.table_count, item.family_id)

    main = sorted((item for item in candidates if item.source_id == main_source_id), key=rank)[
        :main_limit
    ]
    by_source: dict[str, list[TableFamilyCandidate]] = defaultdict(list)
    for item in candidates:
        if item.source_id != main_source_id and item.page_count > 1:
            by_source[item.source_id].append(item)

    appendix = [
        item
        for source_id in sorted(by_source)
        for item in sorted(by_source[source_id], key=rank)[:appendix_limit]
    ]
    return tuple(sorted((*main, *appendix), key=lambda item: (item.source_id, item.family_id)))


__all__ = ["select_content_pages", "select_nearby_content_page", "select_table_families"]
