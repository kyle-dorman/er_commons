"""Typed neutral queries and outputs shared by document-linking adapters."""

from __future__ import annotations

from dataclasses import dataclass

from er_commons.document_records.document_references.exact_resolution import (
    ExactAliasEvidence,
    ExactResolutionDecision,
    resolve_exact_aliases,
)
from er_commons.document_records.document_references.linking_policy import (
    DocumentLinkingPolicy,
    LinkCaller,
)
from er_commons.document_records.document_references.types import JsonObject


@dataclass(frozen=True)
class LinkQuery:
    """Adapter-neutral lookup request accepted by the shared exact resolver."""

    caller: LinkCaller
    lookup_text: str
    target_type: str
    aliases: tuple[ExactAliasEvidence, ...]
    destination_page_ids: tuple[str, ...] | None = None
    resolved_parent_target_ids: tuple[str, ...] | None = None


@dataclass(frozen=True)
class DerivedTargetAlias:
    """One body-evidence alias prepared for canonical publication."""

    record: JsonObject
    evidence: ExactAliasEvidence
    rule_id: str


@dataclass(frozen=True)
class LinkedSourceProducts:
    """Complete in-memory products required from a future per-source publisher."""

    target_aliases: tuple[JsonObject, ...]
    ordinary_references: tuple[JsonObject, ...]
    navigation_entries: tuple[JsonObject, ...]
    navigation_relations: tuple[JsonObject, ...]
    navigation_decisions: tuple[JsonObject, ...]
    navigation_links: tuple[JsonObject, ...]
    support_records: tuple[JsonObject, ...]


def resolve_link_query(
    query: LinkQuery, *, policy: DocumentLinkingPolicy
) -> ExactResolutionDecision:
    """Apply only the fallback family authorized for caller and target type."""
    profile = policy.profile(query.caller)
    if query.target_type == "section":
        fallbacks = profile.section_fallback_rules
        allow_goal_prefix = profile.allow_goal_prefix
    elif query.target_type == "table":
        fallbacks = profile.table_fallback_rules
        allow_goal_prefix = False
    else:
        fallbacks = ()
        allow_goal_prefix = False
    return resolve_exact_aliases(
        lookup_text=query.lookup_text,
        target_type=query.target_type,
        aliases=query.aliases,
        fallback_rules=fallbacks,
        allow_goal_prefix=allow_goal_prefix,
        destination_page_ids=query.destination_page_ids,
        parent_target_ids=query.resolved_parent_target_ids,
    )


__all__ = ["DerivedTargetAlias", "LinkedSourceProducts", "LinkQuery", "resolve_link_query"]
