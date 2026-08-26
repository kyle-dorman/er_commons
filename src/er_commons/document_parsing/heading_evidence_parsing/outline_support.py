"""Narrow text and destination primitives for PDF outline processing."""

from __future__ import annotations

import re
from typing import Any

from er_commons.document_parsing.heading_evidence_parsing.text_evidence import normalize_text

APPENDIX_IDENTIFIER = re.compile(r"\bappendix\s+(?P<identifier>[a-z0-9]+)\b", re.IGNORECASE)
COMPACT_APPENDIX_IDENTIFIER = re.compile(
    r"\bapp(?P<identifier>[a-z])(?=[^a-z0-9]|$)", re.IGNORECASE
)
DISTINCTIVE_NUMBER = re.compile(r"[0-9]{4,}")
TITLE_TOKEN = re.compile(r"[a-z0-9]+")
GENERIC_TITLE_TOKENS = frozenset(
    {"appendix", "app", "pdf", "final", "report", "reports", "rpt", "rpts"}
)


def valid_outline_page(reader: Any, node: Any) -> int | None:
    """Return a one-based valid destination page, or ``None``."""
    if isinstance(node, list):
        return None
    try:
        page_index = reader.get_destination_page_number(node)
    except Exception:
        return None
    return (
        page_index + 1
        if isinstance(page_index, int) and 0 <= page_index < len(reader.pages)
        else None
    )


def semantic_title_tokens(value: str) -> set[str]:
    """Return distinctive normalized words used for title evidence."""
    return {
        token
        for token in TITLE_TOKEN.findall(normalize_text(value))
        if token not in GENERIC_TITLE_TOKENS and not token.isdigit()
    }


def appendix_identifier(value: str) -> str | None:
    """Read a conventional or compact appendix identifier."""
    match = APPENDIX_IDENTIFIER.search(normalize_text(value))
    if match is not None:
        return match.group("identifier")
    compact_match = COMPACT_APPENDIX_IDENTIFIER.search(normalize_text(value))
    return compact_match.group("identifier") if compact_match is not None else None


def native_page_text(reader: Any, physical_page: int) -> str:
    """Return normalized native text for one narrowly selected candidate page."""
    try:
        text = reader.pages[physical_page - 1].extract_text()
    except (AttributeError, IndexError, TypeError):
        return ""
    return normalize_text(text) if isinstance(text, str) else ""


def fuzzy_container_title_matches(title: str, page_text: str) -> bool:
    """Require distinctive numeric or appendix-plus-token agreement."""
    title_digits = set(DISTINCTIVE_NUMBER.findall(title))
    page_digits = set(DISTINCTIVE_NUMBER.findall(page_text))
    if title_digits & page_digits:
        return True
    identifier = appendix_identifier(title)
    if identifier is None or appendix_identifier(page_text) != identifier:
        return False
    expanded_title = normalize_text(title).replace("datavalrpts", "data validation reports")
    title_tokens = set(TITLE_TOKEN.findall(expanded_title)) - GENERIC_TITLE_TOKENS
    page_tokens = set(TITLE_TOKEN.findall(page_text))
    expanded_title_tokens = {
        "validation" if token == "val" else "reports" if token == "rpts" else token
        for token in title_tokens
    }
    return len(expanded_title_tokens & page_tokens) >= 2
