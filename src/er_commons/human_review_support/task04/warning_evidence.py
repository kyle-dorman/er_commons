"""Discover warning occurrences and resolve honest page context for Task 04."""

from __future__ import annotations

import re
from pathlib import Path

from er_commons.human_review_support.task04.json_io import read_json_object, require_list
from er_commons.human_review_support.task04.models import PageProfile, WarningInstance

TABLE_POINTER_RE = re.compile(r"#/tables/(\d+)")
PAGE_OBJECT_RE = re.compile(r"\bpage object\s+(\d+)\b", re.IGNORECASE)
EXPLICIT_PAGE_RE = re.compile(
    r"\b(?:physical[_ ]pdf[_ ]page|page|p)\s*[=:]?\s*(\d+)\b", re.IGNORECASE
)
ROUTED_PAGE_LIST_RE = re.compile(
    r"routed pages with zero reconstructed tables:\s*\[([^]]+)]", re.IGNORECASE
)


def warning_instances(
    retained_root: Path, selected_candidates: dict[str, Path]
) -> list[WarningInstance]:
    """Read retained producer and selected-candidate canonicalization warnings."""
    instances = _producer_warnings(retained_root)
    for source_id, candidate in sorted(selected_candidates.items()):
        summaries = sorted(candidate.rglob("canonicalization_summary.json"))
        if not summaries:
            continue
        if len(summaries) != 1:
            raise ValueError(
                f"expected one canonicalization summary below {candidate}; found {len(summaries)}"
            )
        record = read_json_object(summaries[0])
        warnings = require_list(record.get("warnings", []), path=f"{summaries[0]}.warnings")
        for index, message in enumerate(warnings):
            if isinstance(message, str) and message:
                instances.append(
                    WarningInstance(
                        source_id,
                        "canonicalization",
                        "canonicalization_warning",
                        message,
                        f"{candidate.name}:{index:06d}",
                    )
                )
    return instances


def _producer_warnings(retained_root: Path) -> list[WarningInstance]:
    """Read producer warnings from retained producer summaries."""
    root = retained_root / "document_parse_evidence"
    if not root.is_dir():
        raise ValueError(f"required producer evidence root is missing: {root}")
    instances: list[WarningInstance] = []
    for path in sorted(root.rglob("producer_summary.json")):
        record = read_json_object(path)
        source_id = str(record.get("source_id") or "unknown")
        warnings = require_list(record.get("warnings", []), path=f"{path}.warnings")
        for index, message in enumerate(warnings):
            if isinstance(message, str) and message:
                instances.append(
                    WarningInstance(
                        source_id,
                        "producer",
                        "producer_warning",
                        message,
                        f"{path.parent.parent.name}:{index:06d}",
                    )
                )
    return instances


def warning_page_anchor(
    message: str,
    profiles: dict[int, PageProfile],
    table_pages: dict[int, int],
    object_pages: dict[int, int],
) -> tuple[int | None, str]:
    """Resolve an exact warning page or label an honest contextual fallback."""
    routed = _routed_page_anchor(message, profiles)
    if routed is not None:
        return routed, "exact_warning_page"
    table_match = TABLE_POINTER_RE.search(message)
    if table_match is not None and int(table_match.group(1)) in table_pages:
        return table_pages[int(table_match.group(1))], "exact_table_warning_page"
    object_match = PAGE_OBJECT_RE.search(message)
    if object_match is not None and int(object_match.group(1)) in object_pages:
        return object_pages[int(object_match.group(1))], "exact_pdf_object_page"
    explicit_match = EXPLICIT_PAGE_RE.search(message)
    if explicit_match is not None and int(explicit_match.group(1)) in profiles:
        return int(explicit_match.group(1)), "exact_warning_page"
    return _context_page(message, profiles)


def _routed_page_anchor(message: str, profiles: dict[int, PageProfile]) -> int | None:
    """Select the strongest page explicitly listed by a zero-table warning."""
    match = ROUTED_PAGE_LIST_RE.search(message)
    if match is None:
        return None
    listed = [int(value) for value in re.findall(r"\d+", match.group(1))]
    candidates = [profiles[page] for page in listed if page in profiles]
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item.review_score, -item.physical_page)).physical_page


def _context_page(message: str, profiles: dict[int, PageProfile]) -> tuple[int | None, str]:
    """Choose a useful page while clearly labeling it as non-causal context."""
    candidates = list(profiles.values())
    if not candidates:
        return None, "no_page_evidence"
    if "listitem" in message.lower():
        list_pages = [item for item in candidates if item.list_item_count]
        if list_pages:
            selected = max(
                list_pages,
                key=lambda item: (
                    item.list_item_count,
                    item.review_score,
                    -item.physical_page,
                ),
            )
            return selected.physical_page, "construct_context_page"
    content_pages = [item for item in candidates if item.is_content_bearing]
    selected = max(
        content_pages or candidates, key=lambda item: (item.review_score, -item.physical_page)
    )
    return selected.physical_page, "source_context_page"


def pdf_object_pages(source_pdf: Path) -> dict[int, int]:
    """Map PDF page/content object numbers to physical pages for parser warnings."""
    from pypdf import PdfReader
    from pypdf.generic import ArrayObject, IndirectObject

    result: dict[int, int] = {}
    reader = PdfReader(source_pdf)
    for physical_page, page in enumerate(reader.pages, start=1):
        page_ref = getattr(page, "indirect_reference", None)
        if isinstance(page_ref, IndirectObject):
            result[page_ref.idnum] = physical_page
        contents = page.raw_get("/Contents") if "/Contents" in page else None
        refs = list(contents) if isinstance(contents, ArrayObject) else [contents]
        for ref in refs:
            if isinstance(ref, IndirectObject):
                result[ref.idnum] = physical_page
    return result


__all__ = [
    "PAGE_OBJECT_RE",
    "pdf_object_pages",
    "warning_instances",
    "warning_page_anchor",
]
