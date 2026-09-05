"""Thin navigation adapter over the shared exact target resolver."""

from __future__ import annotations

import re

from er_commons.document_records.document_references.exact_resolution import (
    ExactAliasEvidence,
    ExactResolutionDecision,
)
from er_commons.document_records.document_references.linking_core import (
    LinkQuery,
    resolve_link_query,
)
from er_commons.document_records.document_references.linking_policy import (
    DocumentLinkingPolicy,
    LinkCaller,
)


def resolve_toc_heading(
    *,
    raw_entry_text: str,
    terminal_destination_token: str | None,
    target_type: str,
    aliases: tuple[ExactAliasEvidence, ...],
    policy: DocumentLinkingPolicy,
    destination_page_ids: tuple[str, ...] | None = None,
    resolved_parent_target_ids: tuple[str, ...] | None = None,
) -> ExactResolutionDecision:
    """Resolve one complete TOC heading without parsing target candidates here."""
    heading = _without_terminal_destination(raw_entry_text, terminal_destination_token)
    return resolve_link_query(
        LinkQuery(
            caller=LinkCaller.EFFECTIVE_NAVIGATION,
            lookup_text=heading,
            target_type=target_type,
            aliases=aliases,
            destination_page_ids=destination_page_ids,
            resolved_parent_target_ids=resolved_parent_target_ids,
        ),
        policy=policy,
    )


def _without_terminal_destination(value: str, terminal: str | None) -> str:
    """Remove only the parser-confirmed final destination token and dot leaders."""
    if terminal is None:
        return value.strip()
    separator = r"(?:(?:\s*\.){2,}\s*|\s+)"
    match = re.search(rf"{separator}{re.escape(terminal)}\s*$", value, flags=re.IGNORECASE)
    if match is None:
        raise ValueError("terminal destination token is not the final entry token")
    return value[: match.start()].rstrip()


__all__ = ["resolve_toc_heading"]
