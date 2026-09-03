"""Select a bounded false-negative TOC review sample from the Gate B census."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from er_commons.artifact_io import canonical_json_sha256
from er_commons.human_review_support.task04.models import JsonValue, ReviewItem, ReviewQueue
from er_commons.human_review_support.task04.toc_models import (
    PageKey,
    TocCandidatePage,
    TocDisposition,
    TocSourceCensus,
    contiguous_page_runs,
    parse_toc_censuses,
)
from er_commons.human_review_support.task04.toc_page_shapes import (
    RECOGNIZED_TOC_SIGNALS,
    basic_project_information_pages,
    intentional_blank_pages,
    navigation_continuation_pages,
    obvious_navigation_heading_pages,
    recognized_toc_run_suffixes,
)

DIRECT_NAVIGATION_SIGNALS = {
    "document_index_table_stage",
    "plausible_navigation_layout",
    "raw_docling_document_index",
}
MAX_FULLY_EXCLUDED_POSITIVE_RUN_PAGES = 5


@dataclass(frozen=True)
class TocSelection:
    """Bounded TOC false-negative items and population accounting."""

    items: tuple[ReviewItem, ...]
    population: dict[str, int]


@dataclass(frozen=True)
class PositiveTocSelection:
    """Representative machine-positive TOC items and population accounting."""

    items: tuple[ReviewItem, ...]
    population: dict[str, int]


@dataclass
class _FalseNegativeSelectionStats:
    """Named counters collected while selecting possible missed TOCs."""

    recognized: int = 0
    unrecognized: int = 0
    eligible_full_page: int = 0
    carried_forward: int = 0
    imported_positive: int = 0


@dataclass
class _PositiveSelectionStats:
    """Named counters collected while reducing machine-positive TOC runs."""

    fully_excluded_runs: int = 0
    fully_excluded_pages: int = 0
    navigation_prefix_pages: int = 0
    split_runs: int = 0
    long_run_guardrails: int = 0
    intentional_blanks: int = 0
    auto_false_positives: int = 0

    def population(self, *, recognized_count: int, selected_count: int) -> dict[str, int]:
        """Serialize counters using the stable review-manifest field names."""
        return {
            "machine_positive_page_count": recognized_count,
            "fully_excluded_navigation_run_count": self.fully_excluded_runs,
            "fully_excluded_navigation_run_page_count": self.fully_excluded_pages,
            "navigation_prefix_page_count": self.navigation_prefix_pages,
            "split_after_navigation_prefix_run_count": self.split_runs,
            "long_run_guardrail_representative_count": self.long_run_guardrails,
            "intentional_blank_review_page_count_excluded": self.intentional_blanks,
            "auto_false_positive_page_count_excluded": self.auto_false_positives,
            "maximum_fully_excluded_run_page_count": MAX_FULLY_EXCLUDED_POSITIVE_RUN_PAGES,
            "selected_positive_review_page_count": selected_count,
        }


def build_toc_review_selection(
    censuses: object,
    review_run_id: str,
    policy_sha256: str,
    *,
    full_page_table_pages: set[tuple[str, int]] | None = None,
    prior_decisions: dict[str, TocDisposition] | None = None,
) -> TocSelection:
    """Select unrecognized tables plus imported human-positive pages for review."""
    source_censuses = parse_toc_censuses(censuses)
    selected_rows: list[tuple[int, str, str, TocCandidatePage]] = []
    stats = _FalseNegativeSelectionStats()
    decisions = prior_decisions or {}
    for census in source_censuses:
        selected_rows.extend(
            _select_source_false_negative_pages(census, full_page_table_pages, decisions, stats)
        )
    return _toc_selection_result(
        source_censuses,
        review_run_id,
        policy_sha256,
        selected_rows,
        stats,
    )


def _select_source_false_negative_pages(
    census: TocSourceCensus,
    full_page_table_pages: set[PageKey] | None,
    decisions: dict[str, TocDisposition],
    stats: _FalseNegativeSelectionStats,
) -> list[tuple[int, str, str, TocCandidatePage]]:
    """Apply the false-negative policy to one source without serializing items."""
    ordinal, candidate_id = census.selection_identity()
    groups: dict[tuple[str, ...], list[TocCandidatePage]] = {}
    eligible_pages: list[TocCandidatePage] = []
    imported_pages: list[TocCandidatePage] = []
    for page in census.pages:
        if page.signals & RECOGNIZED_TOC_SIGNALS:
            stats.recognized += 1
            continue
        stats.unrecognized += 1
        if (
            full_page_table_pages is not None
            and (
                census.source_id,
                page.physical_page,
            )
            not in full_page_table_pages
        ):
            continue
        if page.substantive_table_control:
            continue
        stats.eligible_full_page += 1
        prior_decision = decisions.get(page.entry_id)
        if prior_decision == "not_toc":
            stats.carried_forward += 1
        elif prior_decision == "toc":
            stats.imported_positive += 1
            if full_page_table_pages is None:
                imported_pages.append(page)
        if full_page_table_pages is not None:
            eligible_pages.append(page)
        elif prior_decision is None:
            key = tuple(sorted(page.signals - {"adjacent_navigation_run"}))
            groups.setdefault(key or ("adjacent_navigation_run",), []).append(page)

    selected = [*imported_pages]
    grouped_pages = (
        contiguous_page_runs(eligible_pages)
        if full_page_table_pages is not None
        else tuple(tuple(group) for group in groups.values())
    )
    for group in grouped_pages:
        ordered = sorted(group, key=lambda page: page.physical_page)
        positive_pages = _positive_rows(ordered, decisions)
        indexes = _representative_indexes(
            len(ordered),
            positive_count=len(positive_pages),
            one_per_run=full_page_table_pages is not None,
        )
        selected.extend(
            positive_pages[index] if positive_pages else ordered[index] for index in indexes
        )
    return [(ordinal, census.source_id, candidate_id, page) for page in selected]


def _representative_indexes(
    page_count: int, *, positive_count: int, one_per_run: bool
) -> tuple[int, ...]:
    """Choose all imported positives, one run page, or first/middle/last pages."""
    if positive_count:
        return tuple(range(positive_count))
    if one_per_run:
        return (0,)
    return tuple(sorted({0, page_count // 2, page_count - 1}))


def _positive_rows(
    rows: list[TocCandidatePage], decisions: dict[str, TocDisposition]
) -> list[TocCandidatePage]:
    """Return previously confirmed TOC pages from one review run."""
    return [page for page in rows if decisions.get(page.entry_id) == "toc"]


def _toc_selection_result(
    censuses: tuple[TocSourceCensus, ...],
    review_run_id: str,
    policy_sha256: str,
    selected_rows: list[tuple[int, str, str, TocCandidatePage]],
    stats: _FalseNegativeSelectionStats,
) -> TocSelection:
    """Deduplicate selected rows and assemble their population accounting."""
    deduplicated = {
        (source_id, page.physical_page): (ordinal, source_id, candidate_id, page)
        for ordinal, source_id, candidate_id, page in selected_rows
    }
    ordered = sorted(deduplicated.values(), key=lambda item: (item[0], item[3].physical_page))
    items = tuple(
        _review_item(review_run_id, policy_sha256, source_id, candidate_id, page)
        for _, source_id, candidate_id, page in ordered
    )
    signal_counts = Counter(signal for *_, page in ordered for signal in page.signals)
    population = {
        "machine_census_page_count": sum(len(census.pages) for census in censuses),
        "recognized_toc_page_count_excluded": stats.recognized,
        "unrecognized_candidate_page_count": stats.unrecognized,
        "eligible_full_page_table_count": stats.eligible_full_page,
        "prior_decision_page_count_excluded": stats.carried_forward,
        "imported_positive_page_count_included": stats.imported_positive,
        "selected_toc_review_page_count": len(items),
        **{f"selected_signal_{key}": value for key, value in sorted(signal_counts.items())},
    }
    return TocSelection(items, population)


def build_positive_toc_items(
    censuses: object,
    review_run_id: str,
    policy_sha256: str,
    *,
    excluded_heading_pages: set[PageKey] | None = None,
    navigation_shaped_pages: set[PageKey] | None = None,
    excluded_review_pages: set[PageKey] | None = None,
    auto_false_positive_pages: set[PageKey] | None = None,
) -> PositiveTocSelection:
    """Select every reviewable page after each safe positive-TOC prefix."""
    source_censuses = parse_toc_censuses(censuses)
    excluded = excluded_heading_pages or set()
    navigation_pages = navigation_shaped_pages or set()
    review_exclusions = excluded_review_pages or set()
    auto_false_positives = auto_false_positive_pages or set()
    rows: list[tuple[int, str, str, dict[str, Any]]] = []
    recognized_count = 0
    stats = _PositiveSelectionStats()
    for census in source_censuses:
        source_id = census.source_id
        ordinal, candidate_id = census.selection_identity()
        recognized_pages = [page for page in census.pages if page.signals & RECOGNIZED_TOC_SIGNALS]
        recognized_count += len(recognized_pages)
        for run in contiguous_page_runs(recognized_pages):
            selected_rows = _positive_run_review_rows(
                source_id,
                run,
                excluded,
                navigation_pages,
                review_exclusions,
                auto_false_positives,
                stats,
            )
            rows.extend(
                (
                    ordinal,
                    source_id,
                    candidate_id,
                    selected_row,
                )
                for selected_row in selected_rows
            )
    items = tuple(
        _positive_review_item(review_run_id, policy_sha256, source_id, candidate_id, row)
        for _, source_id, candidate_id, row in sorted(
            rows, key=lambda item: (item[0], _integer(item[3]["physical_page"]))
        )
    )
    return PositiveTocSelection(
        items,
        stats.population(recognized_count=recognized_count, selected_count=len(items)),
    )


def _positive_run_review_rows(
    source_id: str,
    run: tuple[TocCandidatePage, ...],
    heading_pages: set[PageKey],
    navigation_pages: set[PageKey],
    review_exclusions: set[PageKey],
    auto_false_positives: set[PageKey],
    stats: _PositiveSelectionStats,
) -> list[dict[str, Any]]:
    """Return every reviewable page after reducing only a supported safe prefix."""
    prefix_length = 0
    basis = "unheaded_run_start"
    candidates = run
    if (source_id, run[0].physical_page) in heading_pages:
        prefix_length = _navigation_prefix_length(source_id, run, navigation_pages)
        stats.navigation_prefix_pages += prefix_length
        if prefix_length < len(run):
            stats.split_runs += 1
            candidates = run[prefix_length:]
            basis = "first_page_after_navigation_prefix"
        elif len(run) > MAX_FULLY_EXCLUDED_POSITIVE_RUN_PAGES:
            stats.long_run_guardrails += 1
            candidates = run[1:2]
            basis = "long_run_guardrail"
        else:
            stats.fully_excluded_runs += 1
            stats.fully_excluded_pages += len(run)
            return []
    selected: list[dict[str, Any]] = []
    for page in candidates:
        physical_page = page.physical_page
        key = (source_id, physical_page)
        if key in review_exclusions:
            stats.intentional_blanks += 1
            continue
        if key in auto_false_positives:
            stats.auto_false_positives += 1
            continue
        review_row = page.to_json()
        review_row["positive_run"] = {
            "start_page": run[0].physical_page,
            "end_page": run[-1].physical_page,
            "page_count": len(run),
            "navigation_prefix_page_count": prefix_length,
            "selection_basis": basis,
            "suffix_entry_ids": [
                run_page.entry_id for run_page in run if run_page.physical_page >= physical_page
            ],
        }
        selected.append(review_row)
    return selected


def _navigation_prefix_length(
    source_id: str,
    ordered_run: tuple[TocCandidatePage, ...],
    navigation_pages: set[PageKey],
) -> int:
    """Keep the heading page plus only directly supported navigation continuations."""
    prefix_length = 1
    for page in ordered_run[1:]:
        page_key = (source_id, page.physical_page)
        if page_key not in navigation_pages and not page.signals & DIRECT_NAVIGATION_SIGNALS:
            break
        prefix_length += 1
    return prefix_length


def _integer(value: object) -> int:
    """Read a selected physical page stored in a queue-enriched JSON record."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"expected numeric physical page, got {value!r}")
    return int(value)


def _review_item(
    review_run_id: str,
    policy_sha256: str,
    source_id: str,
    candidate_id: str,
    page: TocCandidatePage,
) -> ReviewItem:
    """Create one deterministic TOC false-negative review item."""
    candidate_page_id = page.entry_id
    signals: list[JsonValue] = []
    signals.extend(sorted(page.signals))
    preimage = {
        "review_run_id": review_run_id,
        "queue": ReviewQueue.TOC_REVIEW.value,
        "candidate_page_id": candidate_page_id,
        "policy_sha256": policy_sha256,
    }
    return ReviewItem(
        queue=ReviewQueue.TOC_REVIEW,
        review_item_id=f"reviewitem-{canonical_json_sha256(preimage)[:24]}",
        source_id=source_id,
        candidate_id=candidate_id,
        physical_pages=(page.physical_page,),
        reasons=("toc_false_negative_candidate",),
        population={
            "candidate_page_id": candidate_page_id,
            "signals": signals,
            "adjacent_only": page.adjacent_only,
            "substantive_table_control": page.substantive_table_control,
        },
    )


def _positive_review_item(
    review_run_id: str,
    policy_sha256: str,
    source_id: str,
    candidate_id: str,
    row: dict[str, Any],
) -> ReviewItem:
    """Create one deterministic machine-positive false-positive review item."""
    candidate_page_id = str(row["candidate_page_id"])
    preimage = {
        "review_run_id": review_run_id,
        "queue": ReviewQueue.POSITIVE_TOC.value,
        "candidate_page_id": candidate_page_id,
        "policy_sha256": policy_sha256,
    }
    return ReviewItem(
        queue=ReviewQueue.POSITIVE_TOC,
        review_item_id=f"reviewitem-{canonical_json_sha256(preimage)[:24]}",
        source_id=source_id,
        candidate_id=candidate_id,
        physical_pages=(int(row["physical_page"]),),
        reasons=("canonical_positive_toc",),
        population={
            "candidate_page_id": candidate_page_id,
            "signals": list(row.get("signals", [])),
            "positive_run": dict(row.get("positive_run", {})),
        },
    )


__all__ = [
    "RECOGNIZED_TOC_SIGNALS",
    "PositiveTocSelection",
    "TocSelection",
    "build_positive_toc_items",
    "basic_project_information_pages",
    "build_toc_review_selection",
    "intentional_blank_pages",
    "navigation_continuation_pages",
    "obvious_navigation_heading_pages",
    "recognized_toc_run_suffixes",
]
