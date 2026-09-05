"""Machine-reference adapter over the reusable shared exact resolver."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

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
from er_commons.document_records.document_references.types import TargetIndexEntry


def index_entries_to_alias_evidence(
    entries: Sequence[TargetIndexEntry],
    *,
    parent_by_target: Mapping[str, str] | None = None,
) -> tuple[ExactAliasEvidence, ...]:
    """Project indexed body aliases into the resolver's neutral evidence type."""
    parents = parent_by_target or {}
    return tuple(
        ExactAliasEvidence(
            lookup_keys=tuple(sorted(entry.structural_lookup_keys())),
            target_type=entry.target_type,
            alias_id=entry.alias_record_id,
            target_id=entry.target_record_id,
            target_page_ids=(
                (entry.evidence_page_id,) if entry.evidence_page_id is not None else ()
            ),
            parent_target_id=parents.get(entry.target_record_id),
        )
        for entry in entries
    )


def resolve_machine_index_entries(
    *,
    lookup_key: str,
    target_type: str,
    entries: tuple[TargetIndexEntry, ...],
    policy: DocumentLinkingPolicy,
    destination_page_ids: tuple[str, ...] | None = None,
) -> ExactResolutionDecision:
    """Map existing v3 keys to a neutral query without navigation fallbacks."""
    return resolve_link_query(
        LinkQuery(
            caller=LinkCaller.MACHINE_REFERENCE,
            lookup_text=lookup_key,
            target_type=target_type,
            aliases=index_entries_to_alias_evidence(entries),
            destination_page_ids=destination_page_ids,
        ),
        policy=policy,
    )


__all__ = ["index_entries_to_alias_evidence", "resolve_machine_index_entries"]
