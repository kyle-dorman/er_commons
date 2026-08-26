"""Assemble the four deterministic Task 04 review queues."""

from __future__ import annotations

import hashlib
import json
import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from er_commons.human_review_support.task04.canonical_evidence import (
    chapter_pages,
    page_profiles,
    table_candidates,
    table_index_pages,
)
from er_commons.human_review_support.task04.config import MAIN_SOURCE_ID
from er_commons.human_review_support.task04.discovery import DiscoveredInputs
from er_commons.human_review_support.task04.failures import (
    attempt_workspace_count,
    failure_histories,
)
from er_commons.human_review_support.task04.models import (
    PageProfile,
    ReviewItem,
    ReviewItems,
    ReviewQueue,
    TableFamilyCandidate,
    WarningEvidence,
)
from er_commons.human_review_support.task04.page_selection import (
    select_content_pages,
    select_nearby_content_page,
    select_table_families,
)
from er_commons.human_review_support.task04.table_parser import (
    table_family_parser_evidence,
    warning_table_parser_evidence,
)
from er_commons.human_review_support.task04.warning_evidence import (
    PAGE_OBJECT_RE,
    pdf_object_pages,
    warning_instances,
    warning_page_anchor,
)
from er_commons.human_review_support.task04.warning_policy import build_warning_classes

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SelectionResult:
    """Typed durable queue selections and population accounting."""

    items: ReviewItems
    profiles: dict[str, dict[int, PageProfile]]
    populations: dict[str, int]


def build_selection(
    inputs: DiscoveredInputs,
    data_root: Path,
    review_run_id: str,
    policy_sha256: str,
) -> SelectionResult:
    """Build all review queues from validated discovered evidence."""
    candidates = inputs.candidates
    profiles = {source_id: page_profiles(path) for source_id, path in candidates.items()}
    failure_items, failure_population = _failure_items(inputs, review_run_id, policy_sha256)
    warning_items, warning_population = _warning_items(
        inputs, data_root, profiles, review_run_id, policy_sha256
    )
    page_items = _valid_page_items(inputs, profiles, review_run_id, policy_sha256)
    table_items = _table_items(inputs, data_root, review_run_id, policy_sha256)
    items = tuple(
        sorted(
            (*failure_items, *warning_items, *page_items, *table_items),
            key=lambda item: (item.queue.value, item.source_id or "", item.review_item_id),
        )
    )
    populations = {
        **failure_population,
        **warning_population,
        "candidate_source_count": len(candidates),
        "candidate_identity_count": sum(len(source.candidate_ids) for source in inputs.sources),
        "missing_publication_source_count": sum(
            source.selected_candidate is None for source in inputs.sources
        ),
        "available_page_count": sum(len(rows) for rows in profiles.values()),
    }
    LOGGER.info(
        "selected Task 04 review queues",
        extra={
            "queue_counts": dict(Counter(item.queue.value for item in items)),
            "review_item_count": len(items),
        },
    )
    return SelectionResult(items, profiles, populations)


def _failure_items(
    inputs: DiscoveredInputs, review_run_id: str, policy_sha256: str
) -> tuple[ReviewItems, dict[str, int]]:
    """Build source-level attempt-history review items."""
    selected_ids = {
        source.source_id: source.selected_candidate_id
        for source in inputs.sources
        if source.selected_candidate_id is not None
    }
    histories, raw_count = failure_histories(
        inputs.catalog_path.parents[1], inputs.ordered_source_ids, selected_ids
    )
    workspace_count = attempt_workspace_count(inputs.catalog_path.parents[1])
    items = tuple(
        ReviewItem(
            queue=ReviewQueue.FAILURE,
            review_item_id=_item_id(
                review_run_id,
                ReviewQueue.FAILURE,
                ["source_failure_history", history.source_id],
                policy_sha256,
            ),
            source_id=history.source_id,
            candidate_id=history.selected_candidate_id,
            physical_pages=(),
            reasons=(
                (
                    "recovered_attempt_history"
                    if history.current_status == "recovered_later"
                    else "unresolved_attempt_history"
                ),
                *(("missing_publication_evidence",) if not history.attempts else ()),
            ),
            failure=history,
            population={
                "attempt_workspaces": workspace_count,
                "retained_non_success_attempts": raw_count,
                "failure_source_histories": len(histories),
            },
        )
        for history in histories
    )
    return items, {
        "attempt_workspace_count": workspace_count,
        "failed_or_incomplete_review_count": len(histories),
        "raw_failed_or_incomplete_attempt_count": raw_count,
        "failure_source_group_count": len(histories),
    }


def _warning_items(
    inputs: DiscoveredInputs,
    data_root: Path,
    profiles: dict[str, dict[int, PageProfile]],
    review_run_id: str,
    policy_sha256: str,
) -> tuple[ReviewItems, dict[str, int]]:
    """Build one item per normalized warning class with page context."""
    occurrences = warning_instances(inputs.catalog_path.parents[1], inputs.candidates)
    classes = build_warning_classes(occurrences)
    table_pages = {
        source_id: table_index_pages(candidate)
        for source_id, candidate in inputs.candidates.items()
    }
    object_pages: dict[str, dict[int, int]] = {}
    source_index = {source.source_id: source for source in inputs.sources}
    items: list[ReviewItem] = []
    for warning in classes:
        source_id = warning.representative.source_id
        message = warning.representative.message
        source = source_index.get(source_id)
        if PAGE_OBJECT_RE.search(message) and source_id not in object_pages:
            object_pages[source_id] = (
                pdf_object_pages(source.source_pdf)
                if source is not None and source.source_pdf.is_file()
                else {}
            )
        page, anchor_kind = warning_page_anchor(
            message,
            profiles.get(source_id, {}),
            table_pages.get(source_id, {}),
            object_pages.get(source_id, {}),
        )
        candidate = inputs.candidates.get(source_id)
        parser_evidence = warning_table_parser_evidence(data_root, candidate, source_id, page)
        items.append(
            ReviewItem(
                queue=ReviewQueue.WARNING,
                review_item_id=_item_id(
                    review_run_id, ReviewQueue.WARNING, [warning.fingerprint], policy_sha256
                ),
                source_id=source_id,
                candidate_id=candidate.name if candidate is not None else None,
                physical_pages=(page,) if page is not None else (),
                reasons=("one_representative_per_normalized_warning_class",),
                warning=WarningEvidence(warning, anchor_kind, parser_evidence),
                population={"normalized_warning_classes": len(classes)},
            )
        )
    owner_counts = Counter(
        owner
        for warning in classes
        for owner, _, count in warning.owner_code_counts
        for _ in range(count)
    )
    return tuple(items), {
        "raw_producer_warning_count": owner_counts["producer"],
        "raw_canonicalization_warning_count": owner_counts["canonicalization"],
        "raw_warning_count": len(occurrences),
        "normalized_warning_class_count": len(classes),
    }


def _valid_page_items(
    inputs: DiscoveredInputs,
    profiles: dict[str, dict[int, PageProfile]],
    review_run_id: str,
    policy_sha256: str,
) -> ReviewItems:
    """Build content-rich longitudinal samples plus main chapter coverage."""
    region_reasons = (
        "content_rich_early_region",
        "content_rich_middle_region",
        "content_rich_late_region",
    )
    items: list[ReviewItem] = []
    for source_id, source_profiles in profiles.items():
        selected = select_content_pages(list(source_profiles.values()))
        reasons_by_page = {
            profile.physical_page: [region_reasons[min(index, 2)]]
            for index, profile in enumerate(selected)
        }
        candidate = inputs.candidates[source_id]
        if source_id == MAIN_SOURCE_ID:
            _add_chapter_reasons(candidate, source_profiles, reasons_by_page)
        for page, reasons in sorted(reasons_by_page.items()):
            profile = source_profiles[page]
            items.append(
                ReviewItem(
                    ReviewQueue.VALID_PAGE,
                    _item_id(
                        review_run_id,
                        ReviewQueue.VALID_PAGE,
                        [source_id, candidate.name, page],
                        policy_sha256,
                    ),
                    source_id,
                    candidate.name,
                    (page,),
                    tuple(reasons),
                    {
                        "available_source_count": len(profiles),
                        "source_page_count": len(source_profiles),
                        "body_text_chars": profile.body_text_chars,
                        "body_block_count": profile.body_block_count,
                        "review_score": profile.review_score,
                    },
                )
            )
    return tuple(items)


def _add_chapter_reasons(
    candidate: Path,
    profiles: dict[int, PageProfile],
    reasons_by_page: dict[int, list[str]],
) -> None:
    """Add content-bearing main-report pages near every major chapter anchor."""
    candidates = list(profiles.values())
    for anchor_page in chapter_pages(candidate):
        nearby = select_nearby_content_page(candidates, anchor_page, radius=2)
        if nearby is not None:
            reasons_by_page.setdefault(nearby.physical_page, []).append(
                "main_major_chapter_coverage"
            )


def _table_items(
    inputs: DiscoveredInputs,
    data_root: Path,
    review_run_id: str,
    policy_sha256: str,
) -> ReviewItems:
    """Build the approved main and multi-page appendix family sample."""
    all_candidates: list[TableFamilyCandidate] = []
    family_pages: dict[str, dict[str, list[int]]] = {}
    for source_id, candidate in inputs.candidates.items():
        candidates, source_family_pages = table_candidates(candidate, source_id)
        all_candidates.extend(candidates)
        family_pages[source_id] = source_family_pages
    selected = select_table_families(all_candidates, main_source_id=MAIN_SOURCE_ID)
    items: list[ReviewItem] = []
    for table in selected:
        selected_pages = family_pages[table.source_id][table.family_id]
        candidate = inputs.candidates[table.source_id]
        parser_evidence = table_family_parser_evidence(
            data_root, candidate, table.source_id, selected_pages
        )
        items.append(
            ReviewItem(
                ReviewQueue.TABLE,
                _item_id(
                    review_run_id,
                    ReviewQueue.TABLE,
                    [table.source_id, table.family_id],
                    policy_sha256,
                ),
                table.source_id,
                candidate.name,
                tuple(selected_pages),
                (
                    "main_report_table_cap"
                    if table.source_id == MAIN_SOURCE_ID
                    else "largest_multi_page_appendix_family",
                ),
                {
                    "family_page_count": table.page_count,
                    "family_table_count": table.table_count,
                },
                table_family_id=table.family_id,
                table_parser_evidence=parser_evidence,
            )
        )
    return tuple(items)


def _item_id(
    review_run_id: str,
    queue: ReviewQueue,
    anchor: list[str | int],
    policy_sha256: str,
) -> str:
    """Create a stable review-item identity from its exact durable anchor."""
    payload = {
        "review_run_id": review_run_id,
        "queue": queue.value,
        "anchor": anchor,
        "policy": policy_sha256,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"reviewitem-{digest[:24]}"


__all__ = ["SelectionResult", "build_selection"]
