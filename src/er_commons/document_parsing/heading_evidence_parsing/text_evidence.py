"""Normalize text and derive exact numbering and layout evidence."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from er_commons.document_parsing.heading_evidence_parsing.errors import (
    HierarchyInferenceContractError,
)
from er_commons.document_parsing.heading_evidence_parsing.types import LayoutState, NumberingKind

_ASCII_WHITESPACE = re.compile(r"[ \t\n\r\f\v]+")
_NUMBERING_PATTERNS: tuple[tuple[NumberingKind, re.Pattern[str]], ...] = (
    ("decimal", re.compile(r"^(?P<token>[0-9]+(?:\.[0-9]+){0,5})\.?[ \t]+")),
    (
        "article",
        re.compile(r"^(?:Article|ARTICLE)[ \t]+(?P<token>[0-9]+|[IVXLCDM]+)\.?(?:[ \t]|$)"),
    ),
    ("upper_roman", re.compile(r"^(?P<token>[IVXLCDM]+)\.[ \t]+")),
    ("upper_alpha", re.compile(r"^(?P<token>[A-HJ-UW-Z])\.[ \t]+")),
    ("bullet", re.compile(r"^(?P<token>[•·▪◦o])(?:[ \t]+|$)")),
)


@dataclass(frozen=True)
class NumberingEvidence:
    """One frozen numbering-grammar result."""

    kind: NumberingKind
    token: str | None
    depth: int | None


@dataclass(frozen=True)
class LayoutEvidence:
    """Exact normalized alignment of an item to parsed-page line cells."""

    state: LayoutState
    line_count: int | None


def normalize_text(value: str, *, casefold: bool = True) -> str:
    """Apply the contract's Unicode, NBSP, and ASCII-whitespace normalization."""
    normalized = unicodedata.normalize("NFC", value).replace("\N{NO-BREAK SPACE}", " ")
    normalized = _ASCII_WHITESPACE.sub(" ", normalized).strip()
    return normalized.casefold() if casefold else normalized


def parse_numbering(
    text: str,
    *,
    raw_role: str,
    article_regime: bool = False,
) -> NumberingEvidence:
    """Match the frozen grammar without turning list markers into headings."""
    if raw_role == "list_item" or text.startswith("("):
        return NumberingEvidence("none", None, None)

    grammar_text = normalize_text(text, casefold=False)
    for kind, pattern in _NUMBERING_PATTERNS:
        match = pattern.match(grammar_text)
        if match is None:
            continue
        token = match.group("token")
        if kind == "decimal" and not _eligible_decimal(grammar_text, token):
            return NumberingEvidence("none", None, None)
        if kind == "decimal":
            depth = 2 if article_regime and "." in token else len(token.split("."))
        elif kind == "article":
            depth = 1
        elif kind in {"upper_alpha", "upper_roman"}:
            depth = 3 if article_regime else 1
        else:
            depth = None
        return NumberingEvidence(kind, token, depth)
    return NumberingEvidence("none", None, None)


def align_parsed_line(text: str, parsed_page: dict[str, object]) -> LayoutEvidence:
    """Return exact normalized line-cell alignment, never fuzzy layout evidence."""
    target = normalize_text(text)
    cells = parsed_page.get("textline_cells", [])
    if not isinstance(cells, list):
        raise HierarchyInferenceContractError("parsed page textline_cells is invalid")
    matches: list[str] = []
    for cell in cells:
        if not isinstance(cell, dict) or not isinstance(cell.get("text"), str):
            raise HierarchyInferenceContractError("parsed page text line is invalid")
        if normalize_text(cell["text"]) == target:
            matches.append(cell["text"])
    if not matches:
        return LayoutEvidence("absent", None)
    if len(matches) > 1:
        return LayoutEvidence("ambiguous", None)
    line_count = len([line for line in matches[0].splitlines() if line.strip()]) or 1
    return LayoutEvidence("unique_aligned", line_count)


def _eligible_decimal(text: str, token: str) -> bool:
    suffix = text[len(token) :]
    return "." in token or suffix.startswith(".") or 1 <= int(token) <= 99
