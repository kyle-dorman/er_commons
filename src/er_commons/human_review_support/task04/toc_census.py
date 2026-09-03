"""Build a source-free machine-detectable TOC candidate census."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import iter_jsonl
from er_commons.human_review_support.task04.json_io import read_jsonl_objects
from er_commons.human_review_support.task04.toc_census_support import (
    bool_field as _bool_field,
)
from er_commons.human_review_support.task04.toc_census_support import (
    cell_text as _cell_text,
)
from er_commons.human_review_support.task04.toc_census_support import (
    integer as _integer,
)
from er_commons.human_review_support.task04.toc_census_support import (
    iter_jsonl_lines as _iter_jsonl_lines,
)
from er_commons.human_review_support.task04.toc_census_support import (
    page_ids as _page_ids,
)
from er_commons.human_review_support.task04.toc_census_support import (
    sha256_json as _sha256_json,
)
from er_commons.human_review_support.task04.toc_census_support import (
    snippet as _snippet,
)
from er_commons.human_review_support.task04.toc_census_support import (
    string as _string,
)
from er_commons.human_review_support.task04.toc_census_support import (
    string_field as _string_field,
)
from er_commons.human_review_support.task04.toc_raw_scan import (
    load_raw_document_indexes as _load_raw_document_indexes,
)

NAVIGATION_HEADING_RE = re.compile(
    r"\b(contents|table of contents|document index|list of tables|list of figures|index)\b",
    re.IGNORECASE,
)
DOT_LEADER_RE = re.compile(
    r"(?:^|\s)(?:\d+(?:\.\d+)*|[ivxlcdm]+)[.)]?\s+\S.{2,}(?:\.{2,}|…+|\s{2,})\s*\d{1,4}\s*$",
    re.IGNORECASE,
)
PAGE_LABEL_RE = re.compile(r"\b(?:page\s*)?\d{1,4}\b", re.IGNORECASE)
NAVIGATION_TERMS = (
    "contents",
    "table of contents",
    "document index",
    "list of tables",
    "list of figures",
)


@dataclass
class _Page:
    """Small mutable page projection used while streaming canonical rows."""

    page_id: str
    physical_page: int
    printed_page_label: str | None
    evidence: dict[str, set[str]] = field(default_factory=dict)
    snippets: dict[str, list[str]] = field(default_factory=dict)

    def add(self, signal: str, object_id: str, snippet: str = "") -> None:
        """Attach one deterministic signal and bounded human-readable context."""
        self.evidence.setdefault(signal, set()).add(object_id)
        if snippet:
            values = self.snippets.setdefault(signal, [])
            if snippet not in values and len(values) < 3:
                values.append(snippet)


@dataclass(frozen=True)
class _Section:
    """Hierarchy fields needed to explain table ancestry without body rewriting."""

    parent_id: str | None
    heading_block_id: str | None
    section_kind: str | None


@dataclass(frozen=True)
class _Table:
    """Compact canonical table context used for substantive controls."""

    table_id: str
    page_ids: tuple[str, ...]
    section_id: str | None
    family_id: str | None
    navigation: bool


def build_toc_census(
    candidate: Path,
    *,
    source_id: str,
    source_ordinal: int,
    data_root: Path,
    raw_docling_scan: bool = True,
    adjacency_radius_pages: int = 1,
    substantive_controls_per_source: int = 2,
) -> dict[str, Any]:
    """Return deterministic TOC candidates using machine artifacts only.

    This function deliberately accepts a candidate directory, never a source
    PDF.  It may read the retained raw Docling JSON asset because that is
    machine evidence and not a source-document read.
    """
    if adjacency_radius_pages < 0 or substantive_controls_per_source < 0:
        raise ValueError("census bounds must be non-negative")
    canonical = _canonical_dir(candidate)
    pages = _load_pages(canonical / "pages.jsonl")
    sections = _load_sections(canonical / "sections.jsonl")
    block_context = _load_blocks(canonical / "blocks.jsonl", pages)
    tables = _load_tables(canonical / "tables.jsonl", pages, sections, block_context)
    _load_routing(canonical / "../observations/routing.jsonl", pages)
    _load_table_stage(canonical / "../observations/table_stage.jsonl", pages)
    aliases = _load_ambiguous_aliases(canonical / "target_aliases.jsonl", pages)
    links = _load_ambiguous_links(canonical / "cross_references.jsonl", pages)
    raw_objects = _load_raw_document_indexes(
        canonical / "assets.jsonl", data_root, pages, enabled=raw_docling_scan
    )
    controls = _add_substantive_controls(tables, pages, limit=substantive_controls_per_source)
    seeds = {page for page, value in pages.items() if value.evidence}
    selected = _expand_adjacent_pages(pages, seeds, adjacency_radius_pages)
    page_records = tuple(
        _page_record(
            pages[page],
            candidate.name,
            page not in seeds,
            bool(pages[page].evidence.get("substantive_table_control")),
        )
        for page in sorted(selected, key=lambda value: pages[value].physical_page)
    )
    signal_counts = Counter(
        signal for page in page_records for signal in cast(list[str], page["signals"])
    )
    result: dict[str, Any] = {
        "source_id": source_id,
        "source_ordinal": source_ordinal,
        "candidate_id": candidate.name,
        "candidate_pages": list(page_records),
        "ambiguous_toc_aliases": aliases,
        "ambiguous_reference_links": links,
        "raw_document_index_objects": raw_objects,
        "substantive_table_controls": controls,
        "summary": {
            "seed_page_count": len(seeds),
            "adjacent_page_count": len(selected - seeds),
            "candidate_page_count": len(page_records),
            "ambiguous_toc_alias_count": len(aliases),
            "ambiguous_reference_link_count": len(links),
            "raw_document_index_count": len(raw_objects),
            "substantive_table_control_count": len(controls),
            "signal_counts": dict(sorted(signal_counts.items())),
        },
        "census_policy": {
            "adjacency_radius_pages": adjacency_radius_pages,
            "raw_docling_scan": raw_docling_scan,
            "candidate_identity": "tocpagev1-sha256(candidate_id,physical_page)",
            "ordering": "source_ordinal,physical_page,candidate_page_id",
        },
    }
    return result


def _canonical_dir(candidate: Path) -> Path:
    """Resolve one candidate's canonical directory without searching PDFs."""
    roots = sorted(candidate.rglob("canonical"))
    if len(roots) != 1:
        raise ValueError(f"expected one canonical directory below {candidate}; found {len(roots)}")
    return roots[0]


def _load_pages(path: Path) -> dict[str, _Page]:
    """Load only page identity fields needed for all later joins."""
    rows = read_jsonl_objects(path)
    pages: dict[str, _Page] = {}
    for row in rows:
        page_id = _string(row.get("id"), f"{path}.id")
        physical = _integer(row.get("physical_page_number"), f"{path}.physical_page_number")
        if page_id in pages or any(page.physical_page == physical for page in pages.values()):
            raise ValueError(f"candidate repeats page identity in {path}: {page_id}")
        label = row.get("printed_page_label")
        pages[page_id] = _Page(page_id, physical, str(label) if label is not None else None)
    if not pages:
        raise ValueError(f"candidate has no canonical pages: {path}")
    return pages


def _load_sections(path: Path) -> dict[str, _Section]:
    """Load hierarchy ancestry without treating it as a classification decision."""
    if not path.is_file():
        return {}
    sections: dict[str, _Section] = {}
    for row in iter_jsonl(path):
        section_id = _string(row.get("id"), f"{path}.id")
        parent = row.get("parent_section_id")
        heading = row.get("heading_block_id")
        sections[section_id] = _Section(
            str(parent) if parent is not None else None,
            str(heading) if heading is not None else None,
            str(row["section_kind"]) if row.get("section_kind") is not None else None,
        )
    return sections


def _load_blocks(path: Path, pages: dict[str, _Page]) -> dict[str, str]:
    """Mark explicit TOC rows, navigation headings, and layout evidence."""
    block_texts: dict[str, str] = {}
    if not path.is_file():
        return block_texts
    for line in _iter_jsonl_lines(path):
        block_id = _string(_string_field(line, "id"), f"{path}.id")
        text = _string_field(line, "canonical_text") or _string_field(line, "raw_text") or ""
        block_texts[block_id] = text
        page_ids = _page_ids(line) & pages.keys()
        for page_id in page_ids:
            page = pages[page_id]
            if _bool_field(line, "is_toc_row") is True:
                page.add("canonical_toc_block", block_id, _snippet(text))
            if _string_field(line, "semantic_placement") == "toc_content":
                page.add("canonical_toc_placement", block_id, _snippet(text))
            if NAVIGATION_HEADING_RE.search(text):
                page.add("page_furniture_or_heading", block_id, _snippet(text))
            if DOT_LEADER_RE.search(text) or _ordered_navigation_text(text):
                page.add("plausible_navigation_layout", block_id, _snippet(text))
    return block_texts


def _load_tables(
    path: Path,
    pages: dict[str, _Page],
    sections: dict[str, _Section],
    block_texts: dict[str, str],
) -> list[_Table]:
    """Mark navigation-ancestry tables and retain bounded table controls."""
    if not path.is_file():
        return []
    tables: list[_Table] = []
    for line in _iter_jsonl_lines(path):
        table_id = _string(_string_field(line, "id"), f"{path}.id")
        page_ids = tuple(
            sorted(_page_ids(line) & pages.keys(), key=lambda item: pages[item].physical_page)
        )
        section_id = _string_field(line, "section_id")
        ancestry = _section_headings(section_id, sections, block_texts)
        is_toc_row = _bool_field(line, "is_toc_row") is True
        placement = _string_field(line, "semantic_placement")
        navigation = bool(
            is_toc_row
            or placement == "toc_content"
            or any(NAVIGATION_HEADING_RE.search(value) for value in ancestry)
        )
        table_text = _cell_text(line) if navigation or DOT_LEADER_RE.search(line) else ""
        snippet = _snippet(table_text)
        for page_id in page_ids:
            if is_toc_row:
                pages[page_id].add("canonical_toc_table", table_id, snippet)
            if placement == "toc_content":
                pages[page_id].add("canonical_toc_placement", table_id, snippet)
            if any(NAVIGATION_HEADING_RE.search(value) for value in ancestry):
                pages[page_id].add("table_under_navigation_ancestry", table_id, snippet)
            if DOT_LEADER_RE.search(table_text):
                pages[page_id].add("plausible_navigation_layout", table_id, snippet)
        family = _string_field(line, "table_family_id")
        tables.append(_Table(table_id, page_ids, section_id, family, navigation))
    return tables


def _load_routing(path: Path, pages: dict[str, _Page]) -> None:
    """Preserve hierarchy or routing rows that explicitly name visible TOCs."""
    if not path.is_file():
        return
    for row in iter_jsonl(path):
        if not _has_navigation_term(row):
            continue
        row_id = _string(row.get("id"), f"{path}.id")
        for page_id in _row_page_ids(row, pages):
            pages[page_id].add("hierarchy_visible_toc_evidence", row_id)


def _load_table_stage(path: Path, pages: dict[str, _Page]) -> None:
    """Preserve producer document-index routes excluded from canonical tables."""
    if not path.is_file():
        return
    for row in iter_jsonl(path):
        if row.get("unmapped_reason") != "document_index_not_canonical_table":
            continue
        row_id = _string(row.get("id"), f"{path}.id")
        page_id = row.get("page_id")
        if isinstance(page_id, str) and page_id in pages:
            raw = row.get("source_region_raw_link")
            pointer = raw.get("object_pointer") if isinstance(raw, dict) else ""
            pages[page_id].add("document_index_table_stage", row_id, str(pointer))


def _load_ambiguous_aliases(path: Path, pages: dict[str, _Page]) -> list[dict[str, Any]]:
    """Keep every non-unique target alias for conservative human reconciliation."""
    if not path.is_file():
        return []
    aliases: list[dict[str, Any]] = []
    for row in iter_jsonl(path):
        if row.get("resolution_status") == "unique":
            continue
        alias_id = _string(row.get("id"), f"{path}.id")
        targets = row.get("targets")
        target_ids = (
            [
                str(item.get("target_id"))
                for item in targets
                if isinstance(item, dict) and item.get("target_id") is not None
            ]
            if isinstance(targets, list)
            else []
        )
        raw_values = row.get("raw_values")
        record = {
            "alias_id": alias_id,
            "alias_kind": str(row.get("alias_kind") or "unknown"),
            "normalized_alias": str(row.get("normalized_alias") or ""),
            "resolution_status": str(row.get("resolution_status") or "unknown"),
            "raw_values": [str(value) for value in raw_values]
            if isinstance(raw_values, list)
            else [],
            "target_ids": sorted(target_ids),
        }
        aliases.append(record)
        for page_id in _row_page_ids(row, pages):
            pages[page_id].add("ambiguous_toc_alias", alias_id, str(record["normalized_alias"]))
    return sorted(aliases, key=lambda item: str(item["alias_id"]))


def _load_ambiguous_links(path: Path, pages: dict[str, _Page]) -> list[dict[str, Any]]:
    """Retain ambiguous canonical reference links and their page anchors."""
    if not path.is_file():
        return []
    links: list[dict[str, Any]] = []
    for row in iter_jsonl(path):
        if row.get("resolution_status") != "ambiguous":
            continue
        link_id = _string(row.get("id"), f"{path}.id")
        candidates = row.get("candidates")
        candidate_ids = (
            [
                str(item.get("target_record_id"))
                for item in candidates
                if isinstance(item, dict) and item.get("target_record_id") is not None
            ]
            if isinstance(candidates, list)
            else []
        )
        record = {
            "reference_id": link_id,
            "raw_text": str(row.get("raw_text") or ""),
            "lookup_key": str(row.get("lookup_key") or ""),
            "mention_class": str(row.get("mention_class") or "unknown"),
            "unresolved_reason": row.get("unresolved_reason"),
            "candidate_target_ids": sorted(candidate_ids),
        }
        links.append(record)
        for page_id in _row_page_ids(row, pages):
            pages[page_id].add(
                "ambiguous_reference_link", link_id, _snippet(str(record["raw_text"]))
            )
    return sorted(links, key=lambda item: str(item["reference_id"]))


def _add_substantive_controls(
    tables: list[_Table], pages: dict[str, _Page], *, limit: int
) -> list[dict[str, Any]]:
    """Add bounded non-navigation table controls to expose ancestry overreach."""
    controls: list[dict[str, Any]] = []
    for table in sorted(tables, key=lambda item: item.table_id):
        if table.navigation or not table.page_ids or len(controls) >= limit:
            continue
        pages_for_table = [pages[page_id].physical_page for page_id in table.page_ids]
        controls.append(
            {
                "control_id": f"table-control-{len(controls) + 1:03d}",
                "table_id": table.table_id,
                "page_numbers": pages_for_table,
                "section_id": table.section_id,
                "table_family_id": table.family_id,
                "reason": "non_navigation_table_control",
            }
        )
        for page_id in table.page_ids:
            pages[page_id].add("substantive_table_control", table.table_id)
    return controls


def _expand_adjacent_pages(pages: dict[str, _Page], seeds: set[str], radius: int) -> set[str]:
    """Close the candidate page set with the frozen physical-page window."""
    by_number = {page.physical_page: page_id for page_id, page in pages.items()}
    selected = set(seeds)
    for page_id in seeds:
        physical = pages[page_id].physical_page
        selected.update(
            by_number[number]
            for number in range(physical - radius, physical + radius + 1)
            if number in by_number
        )
    for page_id in selected - seeds:
        pages[page_id].add("adjacent_navigation_run", page_id)
    return selected


def _page_record(
    page: _Page, candidate_id: str, adjacent_only: bool, control: bool
) -> dict[str, Any]:
    """Serialize one page with complete bounded signal provenance."""
    preimage = {"candidate_id": candidate_id, "physical_page": page.physical_page}
    page_id = f"tocpagev1-{_sha256_json(preimage)[:24]}"
    evidence = [
        {
            "signal": signal,
            "object_ids": sorted(page.evidence[signal]),
            "snippets": sorted(page.snippets.get(signal, [])),
        }
        for signal in sorted(page.evidence)
    ]
    return {
        "candidate_page_id": page_id,
        "page_id": page.page_id,
        "physical_page": page.physical_page,
        "printed_page_label": page.printed_page_label,
        "signals": [item["signal"] for item in evidence],
        "signal_evidence": evidence,
        "adjacent_only": adjacent_only,
        "substantive_table_control": control,
    }


def _section_headings(
    section_id: str | None,
    sections: dict[str, _Section],
    block_texts: dict[str, str],
) -> tuple[str, ...]:
    """Return bounded heading and kind context for one section ancestry."""
    values: list[str] = []
    seen: set[str] = set()
    current = section_id
    while current is not None and current not in seen and len(values) < 100:
        seen.add(current)
        section = sections.get(current)
        if section is None:
            break
        if section.section_kind:
            values.append(section.section_kind)
        if section.heading_block_id and section.heading_block_id in block_texts:
            values.append(block_texts[section.heading_block_id])
        current = section.parent_id
    return tuple(values)


def _row_page_ids(row: dict[str, Any], pages: dict[str, _Page]) -> set[str]:
    """Extract exact canonical page IDs from region-bearing machine rows."""
    result: set[str] = set()
    regions = row.get("regions")
    for region in regions if isinstance(regions, list) else []:
        if isinstance(region, dict) and isinstance(region.get("page_id"), str):
            page_id = cast(str, region["page_id"])
            if page_id in pages:
                result.add(page_id)
    direct_page_id = row.get("page_id")
    if isinstance(direct_page_id, str) and direct_page_id in pages:
        result.add(direct_page_id)
    return result


def _ordered_navigation_text(text: str) -> bool:
    """Recognize a conservative numbered-title-page-label combination."""
    return bool(
        PAGE_LABEL_RE.search(text) and any(term in text.lower() for term in NAVIGATION_TERMS)
    )


def _has_navigation_term(value: object) -> bool:
    """Find explicit navigation vocabulary in a small routing record."""
    if isinstance(value, dict):
        return any(_has_navigation_term(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_navigation_term(item) for item in value)
    return isinstance(value, str) and any(term in value.lower() for term in NAVIGATION_TERMS)


__all__ = ["build_toc_census"]
