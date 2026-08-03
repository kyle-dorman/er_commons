"""Closed-grammar mention detection over eligible canonical body blocks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

JsonObject = dict[str, Any]
ELIGIBLE_BLOCK_TYPES = frozenset({"caption", "footnote", "list_item", "paragraph"})
PATTERN_VERSION = "cross_reference_patterns_v1"

_NAMED_DOCUMENT = "Draft EIR for the Genentech Campus Master Plan Update"
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("document", re.compile(re.escape(_NAMED_DOCUMENT))),
    ("section", re.compile(r"\bSection\s+([1-9][0-9]*(?:\.[0-9]+)*)\b")),
    ("appendix", re.compile(r"\bAppendix\s+([A-Z](?:[.-][A-Za-z0-9]+)*)\b")),
    ("table", re.compile(r"\bTable\s+([1-9][0-9]*(?:[.-][A-Za-z0-9]+)*)\b")),
    ("figure", re.compile(r"\bFigure\s+([1-9][0-9]*(?:[.-][A-Za-z0-9]+)*)\b")),
    ("printed_page", re.compile(r"\bPage\s+([ivxlcdm]+|[1-9][0-9]*)\b", re.IGNORECASE)),
)
_STANDALONE_TARGET = re.compile(
    r"^(?:Table|Figure)\s+[1-9][0-9]*(?:[.-][A-Za-z0-9]+)*$|^APPENDIX\s+[A-Z]$"
)
_PAGE_FURNITURE = re.compile(r"^Page\s+[1-9][0-9]*\s+of\s+[1-9][0-9]*$", re.IGNORECASE)
_BIBLIOGRAPHY = re.compile(
    r"^[A-Z][^\n]{0,90},\s*(?:19|20)[0-9]{2}[a-z]?\.[^\n]*(?:Report|Plan|Assessment)",
    re.IGNORECASE,
)
_DEED_RECORDATION = re.compile(
    r"\brecorded\s+on\b[^\n]+\b(?:Book|Deeds|Official Records)\b[^\n]+\bpage\s+[1-9][0-9]*\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DetectedMention:
    """One literal supported-grammar span before candidate resolution."""

    mention_class: str
    raw_text: str
    start: int
    end: int
    lookup_key: str


@dataclass(frozen=True)
class Diagnostic:
    """One unsupported or excluded lexical surface counted for review."""

    diagnostic_class: str
    raw_text: str


def eligible_source(block: JsonObject) -> bool:
    """Apply the frozen source-record eligibility predicate."""
    return (
        block.get("content_layer") == "body"
        and block.get("is_toc_row") is False
        and block.get("block_type") in ELIGIBLE_BLOCK_TYPES
    )


def detect_mentions(block: JsonObject) -> tuple[list[DetectedMention], list[Diagnostic]]:
    """Detect non-overlapping supported spans and explicit negative diagnostics."""
    text = block["canonical_text"]
    if not eligible_source(block):
        return [], [Diagnostic("ineligible_source", text)]
    if _PAGE_FURNITURE.fullmatch(text.strip()):
        return [], [Diagnostic("page_furniture", text)]
    if _STANDALONE_TARGET.fullmatch(text.strip()):
        return [], [Diagnostic("standalone_target_label", text)]
    if _BIBLIOGRAPHY.search(text):
        return [], [Diagnostic("bibliography", text)]
    if _DEED_RECORDATION.search(text):
        return [], [Diagnostic("deed_recordation", text)]

    found: list[DetectedMention] = []
    diagnostics: list[Diagnostic] = []
    for mention_class, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            if mention_class == "section" and len(match.group(1).split(".")[0]) >= 4:
                diagnostics.append(Diagnostic("statutory", match.group(0)))
                continue
            if mention_class == "printed_page" and re.match(
                r"\s+of\s+[1-9][0-9]*\b", text[match.end() :], re.IGNORECASE
            ):
                diagnostics.append(Diagnostic("page_furniture", match.group(0)))
                continue
            key = _lookup_key(mention_class, match)
            found.append(
                DetectedMention(mention_class, match.group(0), match.start(), match.end(), key)
            )

    # Longest form wins at one start; otherwise retain non-overlapping source order.
    ordered = sorted(
        found, key=lambda item: (item.start, -(item.end - item.start), item.mention_class)
    )
    accepted: list[DetectedMention] = []
    occupied_until = -1
    for mention in ordered:
        if mention.start < occupied_until:
            continue
        accepted.append(mention)
        occupied_until = mention.end
    return accepted, diagnostics


def _lookup_key(mention_class: str, match: re.Match[str]) -> str:
    if mention_class == "document":
        return match.group(0).casefold()
    value = match.group(1).casefold()
    if mention_class in {"section", "printed_page"}:
        return value
    return f"{mention_class} {value}"
