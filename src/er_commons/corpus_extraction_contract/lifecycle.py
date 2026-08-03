"""Whole-document state history and completion validation."""

from __future__ import annotations

from collections import defaultdict
from typing import cast

from er_commons.corpus_extraction_contract.checks import fail
from er_commons.corpus_extraction_contract.model import JsonObject, LifecycleEvidence

SCOPE_TERMINAL_STATES = {"complete", "complete_with_warnings", "failed_terminal"}
RETRY_STATES = {"failed_retryable", "cancelled"}
SUCCESS_STATES = {"complete", "complete_with_warnings"}
ALLOWED_TRANSITIONS = {
    (None, "selected"),
    ("selected", "running"),
    ("running", "complete"),
    ("running", "complete_with_warnings"),
    ("running", "failed_retryable"),
    ("running", "failed_terminal"),
    ("running", "cancelled"),
}


def validate_document_lifecycle(bundle: JsonObject) -> LifecycleEvidence:
    """Validate all transaction histories, then their successful completions."""
    final_events = _final_events_by_transaction(bundle["state_events"])
    _validate_attempt_order(final_events)
    completions = _completions_by_transaction(bundle["document_completions"], final_events)
    return LifecycleEvidence(final_events=final_events, completions=completions)


def _final_events_by_transaction(events: list[JsonObject]) -> dict[str, JsonObject]:
    histories: dict[str, list[JsonObject]] = defaultdict(list)
    for event in events:
        histories[event["transaction_id"]].append(event)
    return {
        transaction_id: _validate_transaction_history(transaction_id, history)
        for transaction_id, history in histories.items()
    }


def _validate_transaction_history(
    transaction_id: str,
    history: list[JsonObject],
) -> JsonObject:
    """Return the terminal event for one internally consistent history."""
    ordered = sorted(history, key=lambda event: cast(int, event["sequence"]))
    sequences = [event["sequence"] for event in ordered]
    if sequences != list(range(1, len(ordered) + 1)):
        fail("event_sequence", "event sequence is not contiguous", subject=transaction_id)

    if (
        len({event["source_id"] for event in ordered}) != 1
        or len({event["attempt"] for event in ordered}) != 1
    ):
        fail("event_identity", "transaction source or attempt changes", subject=transaction_id)

    previous_state: str | None = None
    for event in ordered:
        transition = (event["from_state"], event["to_state"])
        if transition not in ALLOWED_TRANSITIONS or event["from_state"] != previous_state:
            fail(
                "illegal_transition",
                f"illegal state transition {transition}",
                subject=transaction_id,
            )
        previous_state = cast(str, event["to_state"])

    if previous_state not in SCOPE_TERMINAL_STATES | RETRY_STATES:
        fail("nonterminal_accounting", "attempt has no final disposition", subject=transaction_id)
    return ordered[-1]


def _validate_attempt_order(final_events: dict[str, JsonObject]) -> None:
    """Require contiguous attempts and a scope-terminal latest attempt per source."""
    attempts_by_source: dict[str, list[JsonObject]] = defaultdict(list)
    for event in final_events.values():
        attempts_by_source[event["source_id"]].append(event)
    for source_id, attempts in attempts_by_source.items():
        ordered = sorted(attempts, key=lambda event: cast(int, event["attempt"]))
        attempt_numbers = [event["attempt"] for event in ordered]
        if attempt_numbers != list(range(1, len(ordered) + 1)):
            fail("attempt_sequence", "attempt numbers are not contiguous", subject=source_id)
        if any(event["to_state"] not in RETRY_STATES for event in ordered[:-1]):
            fail("attempt_sequence", "an earlier attempt is scope-terminal", subject=source_id)
        if ordered[-1]["to_state"] not in SCOPE_TERMINAL_STATES:
            fail(
                "nonterminal_accounting", "latest attempt is not scope-terminal", subject=source_id
            )


def _completions_by_transaction(
    completions: list[JsonObject],
    final_events: dict[str, JsonObject],
) -> dict[str, JsonObject]:
    indexed: dict[str, JsonObject] = {}
    for completion in completions:
        transaction_id = completion["transaction_id"]
        if transaction_id in indexed:
            fail("duplicate_completion", "transaction has two completions", subject=transaction_id)
        terminal = final_events.get(transaction_id)
        if terminal is None or terminal["to_state"] not in SUCCESS_STATES:
            fail(
                "premature_completion",
                "completion lacks a successful terminal event",
                subject=transaction_id,
            )
        _validate_complete_pdf(completion)
        if completion["source"]["source_id"] != terminal["source_id"]:
            fail(
                "completion_source",
                "completion source differs from its transaction history",
                subject=transaction_id,
            )
        indexed[transaction_id] = completion
    return indexed


def _validate_complete_pdf(completion: JsonObject) -> None:
    """Reject partial-page or non-successful Docling publications."""
    transaction_id = completion["transaction_id"]
    page_count = completion["source"]["pdf_page_count"]
    if completion["processed_pages"] != list(range(1, page_count + 1)):
        fail("partial_document", "completion is not a complete PDF", subject=transaction_id)
    if completion["raw_docling_status"] != "SUCCESS":
        fail("docling_status", "only Docling SUCCESS can publish", subject=transaction_id)
