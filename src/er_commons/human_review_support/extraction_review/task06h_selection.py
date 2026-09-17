"""Pure frozen-population selection for Task 06H replacement review."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

F1_SOURCE = "feir_appendix_f1"
APPENDIX_A_SOURCE = "deir_appendix_a"
MAIN_SOURCE = "deir_main"
F1_NEW_PAGES = (1, 5, 27, 42, 43, 133, 136, 137)
F1_REUSED_PAGE = 28
APPENDIX_A_UNPROVEN = (
    12,
    13,
    15,
    16,
    17,
    47,
    48,
    67,
    103,
    120,
    121,
    123,
    133,
    140,
    144,
    150,
    154,
    157,
    166,
    174,
    175,
    181,
    182,
    190,
    191,
)
APPENDIX_A_STRUCTURAL = (
    310,
    311,
    312,
    313,
    450,
    451,
    452,
    453,
    478,
    479,
    480,
    481,
    490,
    491,
    492,
    493,
    500,
    501,
)
MAIN_UNPROVEN = (
    11,
    12,
    19,
    20,
    21,
    23,
    24,
    25,
    26,
    27,
    28,
    30,
    31,
    35,
    36,
    37,
    40,
    41,
    42,
    1003,
    1009,
    1081,
    1796,
    2035,
    2037,
    2055,
)
MAIN_BOUNDARIES = (1854, 1855, 1856, 2013, 2014, 2015, 2016, 2083, 2084, 2085, 2086)


@dataclass(frozen=True, order=True)
class SelectedPage:
    """One source/page render with every reason retained after page deduplication."""

    source_id: str
    physical_page: int
    evidence_kinds: tuple[str, ...]
    render_action: str = "render_new"
    entry_id: str | None = None


def deterministic_unchanged_sample(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Select the first entry in every source/disposition stratum."""
    candidates = [row for row in rows if row.get("classification") == "unchanged"]
    ordered = sorted(
        candidates,
        key=lambda row: (
            str(row["source_id"]),
            str(row["baseline_evidence"]["disposition"]),
            str(row["entry_id"]),
        ),
    )
    selected: dict[tuple[str, str], dict[str, Any]] = {}
    for row in ordered:
        key = (str(row["source_id"]), str(row["baseline_evidence"]["disposition"]))
        selected.setdefault(key, row)
    result = tuple(selected[key] for key in sorted(selected))
    if len(result) != 31:
        raise ValueError(f"Task 06H unchanged sample differs: expected=31 observed={len(result)}")
    return result


def build_selection(
    review_rows: list[dict[str, Any]], figure_decisions: list[dict[str, Any]]
) -> tuple[SelectedPage, ...]:
    """Materialize the exact 290-page frozen population from accepted metadata."""
    eligible = [row for row in figure_decisions if row.get("eligibility") == "eligible"]
    rejected = [row for row in figure_decisions if row.get("eligibility") == "rejected"]
    figure_pages = {int(row["physical_page_number"]) for row in eligible}
    if (len(eligible), len(figure_pages), len(rejected)) != (178, 170, 96):
        raise ValueError("Task 06F figure closure differs from 178 eligible/170 pages/96 rejected")
    reasons: dict[tuple[str, int], set[str]] = defaultdict(set)
    entries: dict[tuple[str, int], str] = {}

    def add(source: str, pages: tuple[int, ...] | set[int], reason: str) -> None:
        for page in pages:
            reasons[(source, page)].add(reason)

    add(F1_SOURCE, F1_NEW_PAGES, "final_f1_targeted_review")
    add(F1_SOURCE, {F1_REUSED_PAGE}, "final_f1_reused_sealed_render")
    add(APPENDIX_A_SOURCE, APPENDIX_A_UNPROVEN, "fresh_task04_navigation")
    add(APPENDIX_A_SOURCE, APPENDIX_A_STRUCTURAL, "appendix_a_repair_boundaries")
    add(MAIN_SOURCE, MAIN_UNPROVEN, "fresh_task04_navigation")
    add(MAIN_SOURCE, MAIN_BOUNDARIES, "chapter_8_9_boundaries")
    add(MAIN_SOURCE, figure_pages, "caption_backed_figure")
    for row in deterministic_unchanged_sample(review_rows):
        evidence = row["baseline_evidence"]
        key = (str(row["source_id"]), int(evidence["physical_page"]))
        reasons[key].add("unchanged_reuse_sample")
        entries[key] = str(row["entry_id"])

    selected = tuple(
        SelectedPage(
            source_id=source,
            physical_page=page,
            evidence_kinds=tuple(sorted(kinds)),
            render_action=(
                "reuse_sealed" if (source, page) == (F1_SOURCE, F1_REUSED_PAGE) else "render_new"
            ),
            entry_id=entries.get((source, page)),
        )
        for (source, page), kinds in sorted(reasons.items())
    )
    by_source = {
        source: sum(row.source_id == source for row in selected)
        for source in {row.source_id for row in selected}
    }
    expected = {F1_SOURCE: 9, APPENDIX_A_SOURCE: 43, MAIN_SOURCE: 207}
    for source, count in expected.items():
        if by_source.get(source) != count:
            raise ValueError(
                f"Task 06H source selection differs: source={source} "
                f"expected={count} observed={by_source.get(source)}"
            )
    if len(selected) != 290 or sum(row.render_action == "render_new" for row in selected) != 289:
        raise ValueError("Task 06H render closure must be 290 total, 289 new, and one reused")
    return selected


__all__ = [
    "APPENDIX_A_SOURCE",
    "F1_SOURCE",
    "MAIN_SOURCE",
    "SelectedPage",
    "build_selection",
    "deterministic_unchanged_sample",
]
