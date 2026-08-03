"""Human-readable mention detection over eligible canonical body blocks."""

from __future__ import annotations

import re

from er_commons.cross_reference_enrichment.policy import MentionPolicy
from er_commons.cross_reference_enrichment.source_scope import SourceScope
from er_commons.cross_reference_enrichment.types import (
    DetectedMention,
    Diagnostic,
    JsonObject,
    MentionKind,
    TextSpan,
)


class MentionDetector:
    """Apply source eligibility, exclusions, and the frozen mention grammar."""

    def __init__(self, policy: MentionPolicy, source_scope: SourceScope | None = None) -> None:
        self._policy = policy
        self._source_scope = source_scope

    def is_eligible_source(self, block: JsonObject) -> bool:
        """Return whether a canonical block is an authorized mention source."""
        return (
            block.get("content_layer") == "body"
            and block.get("is_toc_row") is False
            and block.get("block_type") in self._policy.eligible_block_types
        )

    def detect(self, block: JsonObject) -> tuple[list[DetectedMention], list[Diagnostic]]:
        """Return supported mentions and diagnostic-only excluded surfaces."""
        text = _canonical_text(block)
        if not self.is_eligible_source(block):
            return [], [Diagnostic("ineligible_source", text)]

        structural_exclusion = (
            self._source_scope.exclusion_for(block) if self._source_scope is not None else None
        )
        if structural_exclusion is not None:
            return [], [Diagnostic(structural_exclusion, text)]

        exclusion = next(
            (rule for rule in self._policy.block_exclusions if rule.matches(text)), None
        )
        if exclusion is not None:
            return [], [Diagnostic(exclusion.name, text)]

        mentions: list[DetectedMention] = []
        diagnostics: list[Diagnostic] = []
        for rule in self._policy.mention_rules:
            for match in rule.pattern.finditer(text):
                section_disposition = self._section_disposition(rule.kind, text, match)
                if section_disposition is not None:
                    diagnostics.append(Diagnostic(section_disposition, match.group(0)))
                    continue
                if self._is_statutory_section_number(rule.kind, match):
                    diagnostics.append(Diagnostic("statutory", match.group(0)))
                    continue
                if self._is_inline_page_furniture(rule.kind, text, match.end()):
                    diagnostics.append(Diagnostic("page_furniture", match.group(0)))
                    continue
                mentions.append(
                    DetectedMention(
                        kind=rule.kind,
                        raw_text=match.group(0),
                        span=TextSpan(match.start(), match.end()),
                        lookup_key=rule.lookup_key(match),
                    )
                )
        return _non_overlapping_mentions(mentions), diagnostics

    @staticmethod
    def _is_statutory_section_number(kind: MentionKind, match: re.Match[str]) -> bool:
        return kind is MentionKind.SECTION and len(match.group(1).split(".")[0]) >= 4

    @staticmethod
    def _section_disposition(kind: MentionKind, text: str, match: re.Match[str]) -> str | None:
        """Classify explicit section qualifiers before local numeric lookup."""
        if kind is not MentionKind.SECTION:
            return None
        suffix = text[match.end() :]
        if re.match(r"^\s+of\s+the\s+(?:[A-Z][\w'-]*\s+){0,5}(?:Act|Code)\b", suffix):
            return "statutory"
        if re.match(r"^\s+of\s+this\s+Agreement\b", suffix, re.IGNORECASE):
            return None
        if re.match(
            r"^\s+of\s+(?:the\s+)?[^.;:\n]{0,80}"
            r"(?:Agreement|UWMP|Plan|Report|Assessment|EIR)\b",
            suffix,
            re.IGNORECASE,
        ):
            return "qualified_external_section"
        return None

    @staticmethod
    def _is_inline_page_furniture(kind: MentionKind, text: str, end: int) -> bool:
        return (
            kind is MentionKind.PRINTED_PAGE
            and re.match(r"\s+of\s+[1-9][0-9]*\b", text[end:], re.IGNORECASE) is not None
        )


def _canonical_text(block: JsonObject) -> str:
    value = block.get("canonical_text")
    if not isinstance(value, str):
        raise TypeError("canonical block text must be a string")
    return value


def _non_overlapping_mentions(mentions: list[DetectedMention]) -> list[DetectedMention]:
    """Apply longest-at-one-start precedence, then retain source order."""
    ordered = sorted(
        mentions,
        key=lambda item: (
            item.span.start,
            -(item.span.end - item.span.start),
            item.kind.value,
        ),
    )
    accepted: list[DetectedMention] = []
    occupied_until = -1
    for mention in ordered:
        if mention.span.start >= occupied_until:
            accepted.append(mention)
            occupied_until = mention.span.end
    return accepted
