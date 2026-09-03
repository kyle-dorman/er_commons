"""Classify page shapes used to bound positive-TOC review suppression."""

from __future__ import annotations

import re
from pathlib import Path

from er_commons.human_review_support.task04.canonical_evidence import (
    canonical_files,
    page_number,
    page_profiles,
)
from er_commons.human_review_support.task04.json_io import read_jsonl_objects
from er_commons.human_review_support.task04.toc_models import (
    PageKey,
    TocDisposition,
    contiguous_page_runs,
    parse_toc_censuses,
)

OBVIOUS_NAVIGATION_HEADING_RE = re.compile(
    r"(?:\bcontents?\b|\blist\s+of\s+(?:figures?|tables?|append(?:ix|ices)|"
    r"attachments?|(?:support\s+)?exhibits?)\b|^\s*(?:appendices|tables|figures|"
    r"attachments)\s*$)",
    re.IGNORECASE,
)
INTENTIONAL_BLANK_RE = re.compile(
    r"^this page (?:(?:has been )?left blank intentionally|intentionally left blank)\.?$",
    re.IGNORECASE,
)
BASIC_PROJECT_INFORMATION_RE = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*\.?\s*)?basic project information\s*$",
    re.IGNORECASE,
)
RECOGNIZED_TOC_SIGNALS = {"canonical_toc_block", "canonical_toc_placement"}


def obvious_navigation_heading_pages(
    candidates: dict[str, Path],
) -> set[PageKey]:
    """Find pages with approved headings that can begin a safe TOC prefix."""
    selected: set[PageKey] = set()
    for source_id, candidate in candidates.items():
        blocks_path = canonical_files(candidate).get("blocks.jsonl")
        if blocks_path is None:
            continue
        for block in read_jsonl_objects(blocks_path):
            if str(block.get("block_type") or "").casefold() not in {"heading", "title"}:
                continue
            text = str(block.get("canonical_text") or block.get("raw_text") or "").strip()
            if not OBVIOUS_NAVIGATION_HEADING_RE.search(text):
                continue
            regions = block.get("regions")
            if not isinstance(regions, list):
                continue
            for region in regions:
                if isinstance(region, dict):
                    selected.add((source_id, page_number(str(region.get("page_id") or ""))))
    return selected


def navigation_continuation_pages(
    candidates: dict[str, Path],
) -> set[PageKey]:
    """Find list-dominant pages that can safely continue an obvious TOC start."""
    selected: set[PageKey] = set()
    for source_id, candidate in candidates.items():
        for page, profile in page_profiles(candidate).items():
            if profile.list_item_count >= 3 and (
                profile.list_item_count * 2 >= profile.body_block_count
            ):
                selected.add((source_id, page))
    return selected


def intentional_blank_pages(candidates: dict[str, Path]) -> set[PageKey]:
    """Find pages whose only non-furniture text is an intentional-blank notice."""
    text_by_page: dict[PageKey, list[str]] = {}
    for source_id, candidate in candidates.items():
        blocks_path = canonical_files(candidate).get("blocks.jsonl")
        if blocks_path is None:
            continue
        for block in read_jsonl_objects(blocks_path):
            if str(block.get("block_type") or "").casefold() in {"page_header", "page_footer"}:
                continue
            text = str(block.get("canonical_text") or block.get("raw_text") or "").strip()
            if not text:
                continue
            regions = block.get("regions")
            if not isinstance(regions, list):
                continue
            for region in regions:
                if isinstance(region, dict):
                    key = (source_id, page_number(str(region.get("page_id") or "")))
                    text_by_page.setdefault(key, []).append(text)
    return {
        key
        for key, texts in text_by_page.items()
        if all(INTENTIONAL_BLANK_RE.fullmatch(text) for text in texts)
    }


def basic_project_information_pages(
    candidates: dict[str, Path],
) -> set[PageKey]:
    """Find the one-off CalEEMod body heading used to auto-reject TOC positives."""
    selected: set[PageKey] = set()
    for source_id, candidate in candidates.items():
        blocks_path = canonical_files(candidate).get("blocks.jsonl")
        if blocks_path is None:
            continue
        for block in read_jsonl_objects(blocks_path):
            if str(block.get("block_type") or "").casefold() not in {"heading", "title"}:
                continue
            text = str(block.get("canonical_text") or block.get("raw_text") or "").strip()
            if not BASIC_PROJECT_INFORMATION_RE.fullmatch(text):
                continue
            regions = block.get("regions")
            if not isinstance(regions, list):
                continue
            for region in regions:
                if isinstance(region, dict):
                    selected.add((source_id, page_number(str(region.get("page_id") or ""))))
    return selected


def recognized_toc_run_suffixes(
    censuses: object, boundary_pages: set[PageKey]
) -> tuple[set[PageKey], set[str]]:
    """Expand known body-start boundaries through each contiguous positive run."""
    pages: set[PageKey] = set()
    entry_ids: set[str] = set()
    for census in parse_toc_censuses(censuses):
        source_id = census.source_id
        recognized = [page for page in census.pages if page.signals & RECOGNIZED_TOC_SIGNALS]
        for run in contiguous_page_runs(recognized):
            boundary = next(
                (
                    index
                    for index, page in enumerate(run)
                    if (source_id, page.physical_page) in boundary_pages
                ),
                None,
            )
            if boundary is None:
                continue
            for page in run[boundary:]:
                pages.add((source_id, page.physical_page))
                entry_ids.add(page.entry_id)
    return pages, entry_ids


def decided_not_toc_run_suffixes(
    censuses: object, decisions: dict[str, TocDisposition]
) -> tuple[set[PageKey], set[str]]:
    """Expand page-level not-TOC decisions through their positive-run suffixes."""
    boundaries = {
        (census.source_id, page.physical_page)
        for census in parse_toc_censuses(censuses)
        for page in census.pages
        if decisions.get(page.entry_id) == "not_toc"
    }
    return recognized_toc_run_suffixes(censuses, boundaries)


__all__ = [
    "BASIC_PROJECT_INFORMATION_RE",
    "INTENTIONAL_BLANK_RE",
    "OBVIOUS_NAVIGATION_HEADING_RE",
    "RECOGNIZED_TOC_SIGNALS",
    "basic_project_information_pages",
    "decided_not_toc_run_suffixes",
    "intentional_blank_pages",
    "navigation_continuation_pages",
    "obvious_navigation_heading_pages",
    "recognized_toc_run_suffixes",
]
