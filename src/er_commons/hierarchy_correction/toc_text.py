"""Shared text operations used by TOC parsing and reconciliation."""

from __future__ import annotations

import re
from typing import Any

from er_commons.hierarchy_correction.text_evidence import normalize_text

JsonObject = dict[str, Any]

_DASH_TRANSLATION = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "‐": "-",
        "‑": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
        "―": "-",
        "−": "-",
    }
)


def typographic_canonical(value: str) -> str:
    """Fold only approved apostrophe, dash, and hyphen-whitespace variants."""
    translated = normalize_text(value).translate(_DASH_TRANSLATION)
    return re.sub(r"\s*-\s*", "-", translated)


def split_body_title(feature: JsonObject) -> tuple[str, str]:
    """Split one supported heading marker from its normalized body title."""
    return split_heading_text(feature["text"])


def split_heading_text(value: str) -> tuple[str, str]:
    """Split one supported heading marker from raw heading text."""
    text = normalize_text(value, casefold=False)
    patterns = (
        re.compile(
            r"^(?:Article|ARTICLE)[ \t]+(?P<token>[0-9]+|[IVXLCDM]+)\.?(?:[ \t]+)(?P<title>.+)$"
        ),
        re.compile(r"^(?P<token>[0-9]+(?:\.[0-9]+){0,5})\.?[ \t]+(?P<title>.+)$"),
        re.compile(r"^(?P<token>[IVXLCDM]+)\.[ \t]+(?P<title>.+)$"),
        re.compile(r"^(?P<token>[A-HJ-UW-Z])\.[ \t]+(?P<title>.+)$"),
    )
    for pattern in patterns:
        match = pattern.match(text)
        if match is not None:
            return match.group("token"), normalize_text(match.group("title"))
    return "", normalize_text(text)
