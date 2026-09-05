"""Shared exact target resolution with explicit, fail-closed fallback rules."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum


class TextMatchRule(StrEnum):
    """Named exact-equivalence transforms available to caller policies."""

    TERMINAL_PERIOD = "terminal_period"
    AMPERSAND_AND = "standalone_ampersand_and"
    ALPHABETIC_HYPHEN = "alphabetic_hyphen_separator"
    SLASH_WHITESPACE = "slash_adjacent_whitespace"
    SPLIT_FI_LIGATURE = "split_fi_ligature"
    OPTIONAL_COMMA_BEFORE_AND = "optional_comma_before_and"
    APOSTROPHE_AND_TERMINAL_PERIOD = "apostrophe_and_terminal_period"
    RETAINED_HYPHEN_WHITESPACE = "retained_ascii_hyphen_adjacent_whitespace"
    STRAIGHT_CURLY_APOSTROPHE = "straight_curly_apostrophe"
    WHITESPACE_BEFORE_COMMA = "whitespace_before_comma"
    OPTIONAL_DIGIT_LETTER_HYPHEN = "optional_digit_letter_hyphen"


class ExactResolutionOutcome(StrEnum):
    """Closed diagnostic outcomes from the shared resolution stages."""

    NO_TEXT_MATCH = "no_text_match"
    PARENT_SCOPE_MISMATCH = "parent_scope_mismatch"
    DESTINATION_PAGE_MISMATCH = "destination_page_mismatch"
    RESOLVED_UNIQUE = "resolved_unique"
    AMBIGUOUS_TARGET = "ambiguous_target"


_APOSTROPHE_TRANSLATION = {ord("‘"): "'", ord("’"): "'", ord("ʼ"): "'"}


@dataclass(frozen=True)
class ExactAliasEvidence:
    """One eligible alias-to-target edge supplied by a caller adapter."""

    lookup_keys: tuple[str, ...]
    target_type: str
    alias_id: str
    target_id: str
    target_page_ids: tuple[str, ...] = ()
    parent_target_id: str | None = None


@dataclass(frozen=True)
class ExactTargetCandidate:
    """All matching alias evidence for one deduplicated target."""

    target_id: str
    alias_ids: tuple[str, ...]
    target_page_ids: tuple[str, ...]


@dataclass(frozen=True)
class ExactResolutionDecision:
    """Neutral result with enough staged evidence to explain a rejection."""

    candidates: tuple[ExactTargetCandidate, ...]
    outcome: ExactResolutionOutcome
    match_basis: tuple[str, ...]
    unscoped_text_candidate_count: int
    scoped_text_candidate_count: int
    parent_scope_applied: bool
    destination_page_intersection_applied: bool


@dataclass(frozen=True)
class _FallbackVariant:
    """One named, inspectable whole-string fallback comparison."""

    basis: str
    rule: TextMatchRule | None
    strip_goal_prefix: bool


def normalize_exact_text(value: str) -> str:
    """Apply the existing NFC, NBSP, whitespace, and case-folding policy."""
    normalized = unicodedata.normalize("NFC", value.replace("\u00a0", " "))
    return " ".join(normalized.split()).casefold()


def resolve_exact_aliases(
    *,
    lookup_text: str,
    target_type: str,
    aliases: tuple[ExactAliasEvidence, ...],
    fallback_rules: tuple[TextMatchRule, ...] = (),
    allow_goal_prefix: bool = False,
    destination_page_ids: tuple[str, ...] | None = None,
    parent_target_ids: tuple[str, ...] | None = None,
) -> ExactResolutionDecision:
    """Resolve exact aliases, using fallbacks only after a complete exact miss.

    Every fallback remains a whole-string equality test. Evidence from all
    authorized fallback rules is unioned before target-ID deduplication so rule
    order cannot turn conflicting targets into an accidental unique match.
    """
    query = normalize_exact_text(lookup_text)
    eligible = tuple(alias for alias in aliases if alias.target_type == target_type)
    unscoped_matched, bases = _match_text(
        query=query,
        aliases=eligible,
        fallback_rules=fallback_rules,
        allow_goal_prefix=allow_goal_prefix,
    )
    unscoped_text_candidate_count = len(_group_targets(unscoped_matched))
    # R4 is a disambiguator, not a requirement that can veto an otherwise
    # unique full-heading match when extracted body hierarchy is noisy.
    parent_applied = parent_target_ids is not None and unscoped_text_candidate_count > 1
    matched = (
        _narrow_to_parents(unscoped_matched, parent_target_ids)
        if parent_applied
        else unscoped_matched
    )
    scoped_text_candidate_count = len(_group_targets(matched))

    destination_applied = destination_page_ids is not None
    narrowed = _narrow_to_destinations(matched, destination_page_ids)
    candidates = _group_targets(narrowed)
    return ExactResolutionDecision(
        candidates=candidates,
        outcome=_resolution_outcome(
            candidates=candidates,
            unscoped_text_candidate_count=unscoped_text_candidate_count,
            scoped_text_candidate_count=scoped_text_candidate_count,
            parent_scope_applied=parent_applied,
            destination_page_intersection_applied=destination_applied,
        ),
        match_basis=tuple(sorted(bases)),
        unscoped_text_candidate_count=unscoped_text_candidate_count,
        scoped_text_candidate_count=scoped_text_candidate_count,
        parent_scope_applied=parent_applied,
        destination_page_intersection_applied=destination_applied,
    )


def _match_text(
    *,
    query: str,
    aliases: tuple[ExactAliasEvidence, ...],
    fallback_rules: tuple[TextMatchRule, ...],
    allow_goal_prefix: bool,
) -> tuple[tuple[ExactAliasEvidence, ...], set[str]]:
    exact = tuple(
        alias
        for alias in aliases
        if any(normalize_exact_text(key) == query for key in alias.lookup_keys)
    )
    if exact:
        return exact, {"exact"}
    return _match_fallbacks(
        query=query,
        aliases=aliases,
        fallback_rules=fallback_rules,
        allow_goal_prefix=allow_goal_prefix,
    )


def _match_fallbacks(
    *,
    query: str,
    aliases: tuple[ExactAliasEvidence, ...],
    fallback_rules: tuple[TextMatchRule, ...],
    allow_goal_prefix: bool,
) -> tuple[tuple[ExactAliasEvidence, ...], set[str]]:
    collected: dict[tuple[str, str], ExactAliasEvidence] = {}
    bases: set[str] = set()
    for variant in _fallback_variants(fallback_rules, allow_goal_prefix=allow_goal_prefix):
        transformed_query = _apply_rule(query, variant.rule)
        variant_matched = False
        for alias in aliases:
            if _alias_matches_variant(alias, query, transformed_query, variant):
                collected[(alias.alias_id, alias.target_id)] = alias
                variant_matched = True
        if variant_matched:
            bases.add(variant.basis)
    return tuple(collected.values()), bases


def _fallback_variants(
    rules: tuple[TextMatchRule, ...], *, allow_goal_prefix: bool
) -> tuple[_FallbackVariant, ...]:
    variants: list[_FallbackVariant] = []
    if allow_goal_prefix:
        variants.append(_FallbackVariant("goal_prefix", None, True))
    for rule in rules:
        variants.append(_FallbackVariant(rule.value, rule, False))
        if allow_goal_prefix:
            variants.append(_FallbackVariant(f"goal_prefix+{rule.value}", rule, True))
    return tuple(variants)


def _alias_matches_variant(
    alias: ExactAliasEvidence,
    query: str,
    transformed_query: str,
    variant: _FallbackVariant,
) -> bool:
    for lookup_key in alias.lookup_keys:
        candidate_key = _goal_projection(lookup_key) if variant.strip_goal_prefix else lookup_key
        if candidate_key is None:
            continue
        if not _rule_applies_to_pair(query, candidate_key, variant.rule):
            continue
        if _apply_rule(candidate_key, variant.rule) == transformed_query:
            return True
    return False


def _narrow_to_parents(
    aliases: tuple[ExactAliasEvidence, ...], parent_target_ids: tuple[str, ...] | None
) -> tuple[ExactAliasEvidence, ...]:
    if parent_target_ids is None:
        return aliases
    allowed = frozenset(parent_target_ids)
    return tuple(alias for alias in aliases if alias.parent_target_id in allowed)


def _narrow_to_destinations(
    aliases: tuple[ExactAliasEvidence, ...], destination_page_ids: tuple[str, ...] | None
) -> tuple[ExactAliasEvidence, ...]:
    if destination_page_ids is None:
        return aliases
    destinations = frozenset(destination_page_ids)
    return tuple(alias for alias in aliases if destinations.intersection(alias.target_page_ids))


def _resolution_outcome(
    *,
    candidates: tuple[ExactTargetCandidate, ...],
    unscoped_text_candidate_count: int,
    scoped_text_candidate_count: int,
    parent_scope_applied: bool,
    destination_page_intersection_applied: bool,
) -> ExactResolutionOutcome:
    if scoped_text_candidate_count == 0:
        if parent_scope_applied and unscoped_text_candidate_count > 0:
            return ExactResolutionOutcome.PARENT_SCOPE_MISMATCH
        return ExactResolutionOutcome.NO_TEXT_MATCH
    if destination_page_intersection_applied and not candidates:
        return ExactResolutionOutcome.DESTINATION_PAGE_MISMATCH
    if len(candidates) == 1:
        return ExactResolutionOutcome.RESOLVED_UNIQUE
    return ExactResolutionOutcome.AMBIGUOUS_TARGET


def _goal_projection(value: str) -> str | None:
    normalized = normalize_exact_text(value)
    match = re.fullmatch(r"goal\s+(?P<marker>\d+(?:\.\d+)+)\s*:\s*(?P<title>.+)", normalized)
    if match is None:
        return None
    return f"{match.group('marker')} {match.group('title')}"


def _apply_rule(value: str, rule: TextMatchRule | None) -> str:
    normalized = normalize_exact_text(value)
    if rule is None:
        return normalized
    if rule is TextMatchRule.TERMINAL_PERIOD:
        return normalized[:-1].rstrip() if normalized.endswith(".") else normalized
    if rule is TextMatchRule.AMPERSAND_AND:
        return _collapse(re.sub(r"(?<!\w)&(?!\w)", " and ", normalized))
    if rule is TextMatchRule.ALPHABETIC_HYPHEN:
        return _collapse(re.sub(r"(?<=[a-z])-+(?=[a-z])", " ", normalized))
    if rule is TextMatchRule.SLASH_WHITESPACE:
        return re.sub(r"\s*/\s*", "/", normalized)
    if rule is TextMatchRule.SPLIT_FI_LIGATURE:
        return re.sub(r"(?<=\w)fi\s+(?=[a-z])", "fi", normalized)
    if rule is TextMatchRule.OPTIONAL_COMMA_BEFORE_AND:
        return _collapse(re.sub(r",\s+(?=and\b)", " ", normalized))
    if rule is TextMatchRule.APOSTROPHE_AND_TERMINAL_PERIOD:
        normalized = normalized.translate(_APOSTROPHE_TRANSLATION)
        return normalized[:-1].rstrip() if normalized.endswith(".") else normalized
    if rule is TextMatchRule.RETAINED_HYPHEN_WHITESPACE:
        return re.sub(r"\s*-\s*", "-", normalized)
    if rule is TextMatchRule.STRAIGHT_CURLY_APOSTROPHE:
        return normalized.translate(_APOSTROPHE_TRANSLATION)
    if rule is TextMatchRule.WHITESPACE_BEFORE_COMMA:
        return re.sub(r"\s+,", ",", normalized)
    if rule is TextMatchRule.OPTIONAL_DIGIT_LETTER_HYPHEN:
        return re.sub(r"(?<=\d)-(?=[a-z])", "", normalized)
    raise ValueError(f"unsupported exact text match rule: {rule}")


def _rule_applies_to_pair(query: str, alias: str, rule: TextMatchRule | None) -> bool:
    """Require the named fallback to make a material comparison change."""
    if rule is None:
        return True
    normalized_query = normalize_exact_text(query)
    normalized_alias = normalize_exact_text(alias)
    if rule is TextMatchRule.APOSTROPHE_AND_TERMINAL_PERIOD:
        has_apostrophe_change = (
            normalized_query.translate(_APOSTROPHE_TRANSLATION) != normalized_query
            or normalized_alias.translate(_APOSTROPHE_TRANSLATION) != normalized_alias
        )
        has_period_difference = normalized_query.endswith(".") != normalized_alias.endswith(".")
        return has_apostrophe_change and has_period_difference
    return (
        _apply_rule(normalized_query, rule) != normalized_query
        or _apply_rule(normalized_alias, rule) != normalized_alias
    )


def _collapse(value: str) -> str:
    return " ".join(value.split())


def _group_targets(aliases: tuple[ExactAliasEvidence, ...]) -> tuple[ExactTargetCandidate, ...]:
    grouped: dict[str, list[ExactAliasEvidence]] = {}
    for alias in aliases:
        grouped.setdefault(alias.target_id, []).append(alias)
    return tuple(
        ExactTargetCandidate(
            target_id=target_id,
            alias_ids=tuple(sorted({row.alias_id for row in rows})),
            target_page_ids=tuple(
                sorted({page_id for row in rows for page_id in row.target_page_ids})
            ),
        )
        for target_id, rows in sorted(grouped.items())
    )


__all__ = [
    "ExactAliasEvidence",
    "ExactResolutionDecision",
    "ExactResolutionOutcome",
    "ExactTargetCandidate",
    "TextMatchRule",
    "normalize_exact_text",
    "resolve_exact_aliases",
]
