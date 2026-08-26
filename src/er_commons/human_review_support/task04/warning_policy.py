"""Warning normalization and class-based sampling policy for Task 04."""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from er_commons.human_review_support.task04.models import WarningClass, WarningInstance

_PATH = re.compile(r"(?<!#)(?<!#/tables)(?<!#/pages)(?<!#/texts)(?:[A-Za-z]:[\\/]|/)[^\s,;]+")
_LONG_ID = re.compile(r"\b(?:[a-z][a-z0-9_-]*v\d+-)?[0-9a-f]{16,}\b", re.IGNORECASE)
_PAGE = re.compile(r"\b(?:physical[_ ]pdf[_ ]page|page|p)\s*[=:]?\s*\d+\b", re.IGNORECASE)
_INDEX = re.compile(r"(?P<prefix>#/(?:tables|pages|texts)/)\d+\b")
_PDF_OBJECT = re.compile(r"\bpage object \d+ \d+ stream \d+ \d+\b", re.IGNORECASE)
_PDF_OFFSET = re.compile(r"\boffset \d+\b", re.IGNORECASE)
_OVERFLOW_INTEGER = re.compile(
    r"\boverflow/underflow converting [+-]?\d+ to 64-bit integer\b", re.IGNORECASE
)
_INVALID_PROVENANCE_COUNT = re.compile(r"\binvalid provenance records:\s*\d+\b", re.IGNORECASE)
_ZERO_TABLE_PAGE_LIST = re.compile(
    r"\brouted pages with zero reconstructed tables:\s*\[[^]]*\]", re.IGNORECASE
)
_RESOURCES_REPAIR = re.compile(r"\bResources is missing or invalid;\s*repairing\b", re.IGNORECASE)
_WHITESPACE = re.compile(r"\s+")


def normalize_warning_message(message: str) -> str:
    """Remove instance-specific paths, IDs, page values, and indexes from a message."""
    normalized = _PDF_OBJECT.sub("page object <object> stream <stream>", message)
    normalized = _PDF_OFFSET.sub("offset <offset>", normalized)
    normalized = _OVERFLOW_INTEGER.sub(
        "overflow/underflow converting <integer> to 64-bit integer", normalized
    )
    normalized = _INDEX.sub(r"\g<prefix><index>", normalized)
    normalized = _PATH.sub("<path>", normalized)
    normalized = normalized.replace("overflow<path>", "overflow/underflow")
    normalized = _LONG_ID.sub("<id>", normalized)
    normalized = _PAGE.sub("page <page>", normalized)
    normalized = _INVALID_PROVENANCE_COUNT.sub("invalid provenance records: <count>", normalized)
    normalized = _ZERO_TABLE_PAGE_LIST.sub(
        "routed pages with zero reconstructed tables: <page-list>", normalized
    )
    if _RESOURCES_REPAIR.search(normalized):
        normalized = "Resources is missing or invalid; repairing"
    return _WHITESPACE.sub(" ", normalized).strip()


def build_warning_classes(instances: list[WarningInstance]) -> tuple[WarningClass, ...]:
    """Group propagated warnings while retaining raw owner/code observations."""
    grouped: dict[str, list[WarningInstance]] = defaultdict(list)
    for instance in instances:
        grouped[normalize_warning_message(instance.message)].append(instance)
    return tuple(
        sorted(
            (
                _build_warning_class(fingerprint, members)
                for fingerprint, members in grouped.items()
            ),
            key=lambda item: item.fingerprint,
        )
    )


def _build_warning_class(fingerprint: str, members: list[WarningInstance]) -> WarningClass:
    """Build one warning class and collapse pass-through pipeline emissions."""
    owner_code_counts = Counter((member.owner, member.code) for member in members)
    source_owner_code_counts: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)
    for member in members:
        source_owner_code_counts[member.source_id][(member.owner, member.code)] += 1
    source_counts = {
        source_id: max(counts.values()) for source_id, counts in source_owner_code_counts.items()
    }
    representative = min(
        members, key=lambda member: (member.source_id, member.evidence_id, member.message)
    )
    return WarningClass(
        fingerprint=fingerprint,
        occurrence_count=sum(source_counts.values()),
        raw_occurrence_count=len(members),
        source_counts=tuple(sorted(source_counts.items())),
        owner_code_counts=tuple(
            (owner, code, count) for (owner, code), count in sorted(owner_code_counts.items())
        ),
        representative=representative,
    )


def warning_guidance(message: str) -> tuple[str, str]:
    """Translate common machine warnings into review-oriented language."""
    lowered = message.lower()
    if "invalid provenance records:" in lowered:
        return (
            "Some extracted items came with source-location evidence that failed geometry "
            "validation. A provenance record links an extracted item to its source page and "
            "bounding box. Invalid links were rejected and counted rather than silently used.",
            "Treat the number as a record count, not a page count. This summary cannot identify "
            "every affected page or distinguish the individual geometry failure reasons.",
        )
    if "document index preserved as text:" in lowered:
        return (
            "The parser recognized a table-shaped document index and intentionally retained it "
            "as text rather than admitting it as a substantive canonical table.",
            "Check the linked page for readable index text. This warning does not mean the page "
            "content disappeared.",
        )
    if "zero table mapping:" in lowered:
        return (
            "The parser reported a table-like region without assigning a clean canonical table.",
            "Use the overlay to decide whether the region is a missed table or ordinary layout.",
        )
    if "listitem parent must be a list group" in lowered:
        return (
            "Canonicalization found list items without the expected list container and "
            "created one.",
            "Check that list membership and reading order remain understandable.",
        )
    if "resources is missing or invalid" in lowered or "repairing" in lowered:
        return (
            "The PDF contained incomplete resource metadata that the PDF parser repaired "
            "while reading.",
            "Check the linked page for missing visual content, unreadable text, or "
            "rendering differences.",
        )
    if "treating object as null" in lowered and "64-bit integer" in lowered:
        return (
            "A PDF content stream contained an integer outside the parser's 64-bit range. The "
            "malformed object was treated as null and parsing continued.",
            "Check the linked page for missing or visibly damaged content.",
        )
    return (
        "This is a retained producer or canonicalization diagnostic associated with the source.",
        "Compare the source page with parsed evidence and record only material review defects.",
    )


__all__ = ["build_warning_classes", "normalize_warning_message", "warning_guidance"]
