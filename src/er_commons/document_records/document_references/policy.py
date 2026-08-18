"""Readable, reviewable policy for cross-reference source and mention grammar."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from er_commons.document_records.document_references.types import MentionKind

LookupKeyBuilder = Callable[[re.Match[str]], str]

ELIGIBLE_BLOCK_TYPES = frozenset({"caption", "footnote", "list_item", "paragraph"})
TABLE_PAGE_WINDOW = 10
QUALIFIED_EXTERNAL_TABLE_PATTERN = re.compile(
    r"^\s+(?:in|from|of)\s+reference\s+[1-9][0-9]*\b", re.IGNORECASE
)
TABLE_LABEL_PATTERN = re.compile(r"table [1-9][0-9]*(?:[.-][a-z0-9]+)*", re.IGNORECASE)


def is_qualified_external_table_reference(suffix: str) -> bool:
    """Recognize a table mention explicitly qualified to an external reference."""
    return QUALIFIED_EXTERNAL_TABLE_PATTERN.match(suffix) is not None


@dataclass(frozen=True)
class MentionRule:
    """A named grammar rule and the lookup key it produces."""

    name: str
    kind: MentionKind
    pattern: re.Pattern[str]
    lookup_key: LookupKeyBuilder


@dataclass(frozen=True)
class BlockExclusion:
    """A whole-block exclusion evaluated before mention extraction."""

    name: str
    pattern: re.Pattern[str]
    requires_full_match: bool = False

    def matches(self, text: str) -> bool:
        """Return whether the block belongs to this unsupported surface."""
        if self.requires_full_match:
            return self.pattern.fullmatch(text.strip()) is not None
        return self.pattern.search(text) is not None


@dataclass(frozen=True)
class MentionPolicy:
    """Complete policy needed by the detector and local resolver."""

    pattern_version: str
    eligible_block_types: frozenset[str]
    mention_rules: tuple[MentionRule, ...]
    block_exclusions: tuple[BlockExclusion, ...]
    table_page_window: int


def default_mention_policy() -> MentionPolicy:
    """Build the frozen v3 policy from named, independently reviewable rules."""
    number = r"[1-9][0-9]*(?:\.[0-9]+)*"
    numbered_label = r"[1-9][0-9]*(?:[.-][A-Za-z0-9]+)*"

    # The document form is grammatical rather than fixture-specific. It accepts
    # a title-cased EIR title followed by the parenthetical source citation that
    # bounds prose uses in the pilot. Bibliography blocks are excluded first.
    environmental_document = re.compile(
        r"\b(?:Draft|Final) EIR for (?:the )?"
        r"[A-Z][A-Za-z0-9&'’.-]*(?:\s+[A-Z][A-Za-z0-9&'’.-]*)+"
        r"(?=\s*\()"
    )

    rules = (
        MentionRule(
            "named_environmental_document",
            MentionKind.DOCUMENT,
            environmental_document,
            lambda match: match.group(0).casefold(),
        ),
        MentionRule(
            "numbered_section",
            MentionKind.SECTION,
            re.compile(rf"\bSection\s+({number})\b"),
            lambda match: match.group(1).casefold(),
        ),
        MentionRule(
            "lettered_appendix",
            MentionKind.APPENDIX,
            re.compile(r"\bAppendix\s+([A-Z](?:[.-][A-Za-z0-9]+)*)\b"),
            lambda match: f"appendix {match.group(1).casefold()}",
        ),
        MentionRule(
            "numbered_table",
            MentionKind.TABLE,
            re.compile(rf"\bTable\s+({numbered_label})\b"),
            lambda match: f"table {match.group(1).casefold()}",
        ),
        MentionRule(
            "numbered_figure",
            MentionKind.FIGURE,
            re.compile(rf"\bFigure\s+({numbered_label})\b"),
            lambda match: f"figure {match.group(1).casefold()}",
        ),
        MentionRule(
            "printed_page",
            MentionKind.PRINTED_PAGE,
            re.compile(r"\bPage\s+([ivxlcdm]+|[1-9][0-9]*)\b", re.IGNORECASE),
            lambda match: match.group(1).casefold(),
        ),
    )
    exclusions = (
        BlockExclusion(
            "page_furniture",
            re.compile(r"Page\s+[1-9][0-9]*\s+of\s+[1-9][0-9]*", re.IGNORECASE),
            requires_full_match=True,
        ),
        BlockExclusion(
            "standalone_target_label",
            re.compile(r"(?:Table|Figure)\s+[1-9][0-9]*(?:[.-][A-Za-z0-9]+)*|APPENDIX\s+[A-Z]"),
            requires_full_match=True,
        ),
        BlockExclusion(
            "bibliography",
            re.compile(
                r"^[A-Z][A-Za-z&.'’ -]{1,80},\s*(?:19|20)[0-9]{2}[a-z]?\.",
                re.IGNORECASE,
            ),
        ),
        BlockExclusion(
            "deed_recordation",
            re.compile(
                r"\brecorded\s+on\b[^\n]+\b(?:Book|Deeds|Official Records)\b"
                r"[^\n]+\bpage\s+[1-9][0-9]*\b",
                re.IGNORECASE,
            ),
        ),
    )
    return MentionPolicy(
        pattern_version="cross_reference_patterns_v3",
        eligible_block_types=ELIGIBLE_BLOCK_TYPES,
        mention_rules=rules,
        block_exclusions=exclusions,
        table_page_window=TABLE_PAGE_WINDOW,
    )
