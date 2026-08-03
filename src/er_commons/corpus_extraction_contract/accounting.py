"""Exact run-scope accounting over validated document attempts."""

from __future__ import annotations

from collections import Counter
from typing import cast

from er_commons.corpus_extraction_contract.checks import fail
from er_commons.corpus_extraction_contract.lifecycle import (
    RETRY_STATES,
    SCOPE_TERMINAL_STATES,
    SUCCESS_STATES,
)
from er_commons.corpus_extraction_contract.model import (
    JsonObject,
    LifecycleEvidence,
    ScopeEvidence,
)

PRODUCTION_SOURCE_COUNT = 35


def validate_scope_accounting(
    bundle: JsonObject,
    lifecycle: LifecycleEvidence,
) -> ScopeEvidence:
    """Close declared sources, terminal attempts, completions, and aggregates."""
    accounting = bundle["accounting"]
    if bundle["production_extraction_id"] != accounting["production_extraction_id"]:
        fail("scope_identity", "bundle and accounting production identities differ")

    ordered_sources = accounting["ordered_sources"]
    source_by_id = {source["source_id"]: source for source in ordered_sources}
    ordered_ids = [source["source_id"] for source in ordered_sources]
    rows = accounting["rows"]
    row_ids = [row["source_id"] for row in rows]
    if row_ids != ordered_ids or len(source_by_id) != len(ordered_sources):
        fail("scope_closure", "accounting rows do not exactly match declared source order")
    _validate_scope_kind(accounting["scope_kind"], len(ordered_ids))
    _validate_counts(rows, accounting["counts"])

    row_transactions = {row["transaction_id"] for row in rows}
    final_scope_transactions = {
        transaction_id
        for transaction_id, event in lifecycle.final_events.items()
        if event["to_state"] in SCOPE_TERMINAL_STATES
    }
    if row_transactions != final_scope_transactions:
        fail("scope_transactions", "accounting does not cover every scope-terminal attempt")

    candidate_sources: dict[str, str] = {}
    candidate_inventories: dict[str, str] = {}
    unavailable_sources: set[str] = set()
    successful_transactions: set[str] = set()
    for row in rows:
        source = source_by_id[row["source_id"]]
        event = lifecycle.final_events.get(row["transaction_id"])
        if event is None or event["source_id"] != row["source_id"]:
            fail("accounting_event", "row lacks its terminal event", subject=row["source_id"])
        if event["to_state"] != row["terminal_state"]:
            fail("accounting_event", "row state differs from its event", subject=row["source_id"])
        completion = lifecycle.completions.get(row["transaction_id"])
        if row["terminal_state"] in SUCCESS_STATES:
            _record_success(
                row=row,
                source=source,
                completion=completion,
                candidate_sources=candidate_sources,
                candidate_inventories=candidate_inventories,
            )
            successful_transactions.add(row["transaction_id"])
        else:
            if row["candidate_id"] is not None or completion is not None:
                fail(
                    "failed_candidate", "failed source claims a candidate", subject=row["source_id"]
                )
            unavailable_sources.add(cast(str, row["source_id"]))

    if set(lifecycle.completions) != successful_transactions:
        fail("completion_closure", "document completions do not exactly match successful rows")
    if any(event["to_state"] in RETRY_STATES for event in lifecycle.final_events.values()):
        _validate_retry_sources(lifecycle, set(ordered_ids))

    return ScopeEvidence(
        candidate_sources=candidate_sources,
        candidate_inventories=candidate_inventories,
        unavailable_source_ids=frozenset(unavailable_sources),
    )


def _validate_scope_kind(scope_kind: str, source_count: int) -> None:
    if scope_kind == "production_full" and source_count != PRODUCTION_SOURCE_COUNT:
        fail("scope_impersonation", "production_full must contain all 35 sources")
    if scope_kind != "production_full" and source_count == PRODUCTION_SOURCE_COUNT:
        fail("scope_impersonation", "subordinate scope cannot claim production scope")


def _validate_counts(rows: list[JsonObject], persisted: JsonObject) -> None:
    counts = Counter(row["terminal_state"] for row in rows)
    expected = {
        "total": len(rows),
        "complete": counts["complete"],
        "complete_with_warnings": counts["complete_with_warnings"],
        "failed_terminal": counts["failed_terminal"],
    }
    if persisted != expected:
        fail("accounting_counts", "accounting aggregates do not recompute")


def _record_success(
    *,
    row: JsonObject,
    source: JsonObject,
    completion: JsonObject | None,
    candidate_sources: dict[str, str],
    candidate_inventories: dict[str, str],
) -> None:
    source_id = row["source_id"]
    if completion is None or row["candidate_id"] != completion["candidate_id"]:
        fail("missing_completion", "successful row lacks completion", subject=source_id)
    if completion["source"] != source:
        fail(
            "completion_source", "completion source differs from declared scope", subject=source_id
        )
    candidate_id = cast(str, row["candidate_id"])
    if candidate_id in candidate_sources:
        fail("duplicate_candidate", "candidate appears for two sources", subject=candidate_id)
    candidate_sources[candidate_id] = cast(str, source_id)
    candidate_inventories[candidate_id] = completion["candidate_inventory"]["sha256"]


def _validate_retry_sources(lifecycle: LifecycleEvidence, declared_sources: set[str]) -> None:
    retry_sources = {
        event["source_id"]
        for event in lifecycle.final_events.values()
        if event["to_state"] in RETRY_STATES
    }
    if not retry_sources <= declared_sources:
        fail("scope_transactions", "retry attempt belongs to an undeclared source")
