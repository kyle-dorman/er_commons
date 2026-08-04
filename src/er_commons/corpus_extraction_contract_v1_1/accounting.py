"""Exact Task 03F.2 terminal-evidence joins for corpus accounting v1.1."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import cast

from er_commons.corpus_extraction_contract_v1_1.checks import canonical_sha256, fail, verify_ref
from er_commons.corpus_extraction_contract_v1_1.model import ArtifactReader, JsonObject

SUCCESS_STATES = frozenset({"complete", "complete_with_warnings"})
RETRY_STATES = frozenset({"failed_retryable", "cancelled"})
SCOPE_TERMINAL_STATES = SUCCESS_STATES | {"failed_terminal"}
ALLOWED_TRANSITIONS = frozenset(
    {
        (None, "selected"),
        ("selected", "running"),
        ("running", "complete"),
        ("running", "complete_with_warnings"),
        ("running", "failed_retryable"),
        ("running", "failed_terminal"),
        ("running", "cancelled"),
    }
)


@dataclass(frozen=True)
class ScopeEvidence:
    """Verified source outcomes needed by index, resolution, and handoff."""

    sources: dict[str, JsonObject]
    source_ordinals: dict[str, int]
    candidate_sources: dict[str, str]
    candidate_inventory_refs: dict[str, JsonObject]
    failed_rows: dict[str, JsonObject]

    @property
    def successful_source_ids(self) -> frozenset[str]:
        """Return sources with a checksum-verified document completion."""
        return frozenset(self.candidate_sources.values())

    @property
    def unavailable_source_ids(self) -> frozenset[str]:
        """Return sources whose latest contiguous attempt failed terminally."""
        return frozenset(self.failed_rows)


def validate_scope_accounting(bundle: JsonObject, reader: ArtifactReader) -> ScopeEvidence:
    """Validate exact rows against retained Task 03F.2 bytes and histories."""
    accounting = cast(JsonObject, bundle["accounting"])
    if accounting["production_extraction_id"] != bundle["production_extraction_id"]:
        fail("scope_identity", "bundle and accounting production identities differ")

    sources = cast(list[JsonObject], accounting["ordered_sources"])
    rows = cast(list[JsonObject], accounting["rows"])
    source_by_id = {cast(str, source["source_id"]): source for source in sources}
    ordered_ids = [cast(str, source["source_id"]) for source in sources]
    if len(source_by_id) != len(sources) or [row["source_id"] for row in rows] != ordered_ids:
        fail("scope_closure", "accounting rows do not exactly match declared source order")
    _validate_scope_kind(cast(str, accounting["scope_kind"]), len(sources))
    _validate_counts(rows, cast(JsonObject, accounting["counts"]))
    verify_ref(cast(JsonObject, accounting["artifact_inventory"]), reader)

    events = _index_events(cast(list[JsonObject], bundle["state_events"]))
    attempts = _index_unique(
        cast(list[JsonObject], bundle["document_attempts"]), "transaction_id", "attempt"
    )
    completions = _index_unique(
        cast(list[JsonObject], bundle["document_completions"]),
        "transaction_id",
        "completion",
    )
    _validate_attempt_histories(events, attempts)

    candidate_sources: dict[str, str] = {}
    inventories: dict[str, JsonObject] = {}
    failed_rows: dict[str, JsonObject] = {}
    row_transactions: set[str] = set()
    for ordinal, row in enumerate(rows, start=1):
        source_id = cast(str, row["source_id"])
        if row["source_ordinal"] != ordinal:
            fail("scope_order", "accounting source ordinal differs", subject=source_id)
        transaction_id = cast(str, row["transaction_id"])
        if transaction_id in row_transactions:
            fail("scope_transactions", "accounting repeats a transaction", subject=transaction_id)
        row_transactions.add(transaction_id)
        terminal = _validate_row_evidence(row, events, attempts, reader)
        _require_latest_attempt(row, attempts)
        if row["terminal_state"] in SUCCESS_STATES:
            candidate_id, inventory_ref = _validate_success(
                row, source_by_id[source_id], completions, reader
            )
            if candidate_id in candidate_sources:
                fail(
                    "duplicate_candidate", "candidate appears for two sources", subject=candidate_id
                )
            candidate_sources[candidate_id] = source_id
            inventories[candidate_id] = inventory_ref
        else:
            _validate_failure(row, terminal, completions, reader)
            failed_rows[source_id] = row

    latest_scope_transactions = {
        transaction_id
        for transaction_id, attempt in attempts.items()
        if attempt["disposition"] in SCOPE_TERMINAL_STATES and _is_latest_attempt(attempt, attempts)
    }
    if row_transactions != latest_scope_transactions:
        fail("scope_transactions", "accounting does not cover every latest scope-terminal attempt")
    if set(completions) != {
        cast(str, row["transaction_id"]) for row in rows if row["terminal_state"] in SUCCESS_STATES
    }:
        fail("completion_closure", "document completions do not exactly match successful rows")
    return ScopeEvidence(
        sources=source_by_id,
        source_ordinals={source_id: index for index, source_id in enumerate(ordered_ids, start=1)},
        candidate_sources=candidate_sources,
        candidate_inventory_refs=inventories,
        failed_rows=failed_rows,
    )


def validate_unavailable_sources(
    records: list[JsonObject], scope: ScopeEvidence, reader: ArtifactReader
) -> dict[str, JsonObject]:
    """Require one manifest-ordered, source-exact record per failed row."""
    expected_ids = sorted(scope.failed_rows, key=scope.source_ordinals.__getitem__)
    observed_ids = [cast(str, record["source"]["source_id"]) for record in records]
    if observed_ids != expected_ids:
        fail("unavailable_catalog", "unavailable catalog differs from failed accounting")

    result: dict[str, JsonObject] = {}
    for record in records:
        source_id = cast(str, record["source"]["source_id"])
        row = scope.failed_rows[source_id]
        expected = {
            "source": scope.sources[source_id],
            "source_ordinal": row["source_ordinal"],
            "transaction_id": row["transaction_id"],
            "attempt": row["attempt"],
            "disposition": "failed_terminal",
            "failure_class": row["failure_class"],
            "terminal_event_ref": row["terminal_event_ref"],
            "attempt_record_ref": row["attempt_record_ref"],
            "retained_evidence_refs": row["retained_evidence_refs"],
        }
        if any(record.get(field) != value for field, value in expected.items()):
            fail(
                "unavailable_catalog",
                "unavailable evidence differs from accounting",
                subject=source_id,
            )
        for reference in cast(list[JsonObject], record["retained_evidence_refs"]):
            verify_ref(reference, reader)
        result[source_id] = record
    return result


def unavailable_source_digest(record: JsonObject) -> str:
    """Return the canonical digest bound by resolution and handoff evidence."""
    return canonical_sha256(record)


def _index_events(records: list[JsonObject]) -> dict[str, list[JsonObject]]:
    grouped: dict[str, list[JsonObject]] = defaultdict(list)
    for record in records:
        grouped[cast(str, record["transaction_id"])].append(record)
    return grouped


def _index_unique(records: list[JsonObject], key: str, label: str) -> dict[str, JsonObject]:
    indexed: dict[str, JsonObject] = {}
    for record in records:
        value = cast(str, record[key])
        if value in indexed:
            fail(f"duplicate_{label}", f"transaction has two {label} records", subject=value)
        indexed[value] = record
    return indexed


def _validate_attempt_histories(
    events: dict[str, list[JsonObject]], attempts: dict[str, JsonObject]
) -> None:
    if set(events) != set(attempts):
        fail("attempt_closure", "events and attempt records do not cover the same transactions")
    by_source: dict[str, list[JsonObject]] = defaultdict(list)
    for transaction_id, attempt in attempts.items():
        ordered = sorted(events[transaction_id], key=lambda event: cast(int, event["sequence"]))
        if [event["sequence"] for event in ordered] != list(range(1, len(ordered) + 1)):
            fail("event_sequence", "event sequence is not contiguous", subject=transaction_id)
        previous: str | None = None
        for event in ordered:
            if (
                event["transaction_id"] != transaction_id
                or event["source_id"] != attempt["source_id"]
                or event["attempt"] != attempt["attempt"]
                or (event["from_state"], event["to_state"]) not in ALLOWED_TRANSITIONS
                or event["from_state"] != previous
            ):
                fail("event_identity", "attempt state history differs", subject=transaction_id)
            previous = cast(str, event["to_state"])
        if previous != attempt["disposition"]:
            fail(
                "attempt_disposition",
                "attempt differs from its final event",
                subject=transaction_id,
            )
        by_source[cast(str, attempt["source_id"])].append(attempt)
    for source_id, source_attempts in by_source.items():
        ordered = sorted(source_attempts, key=lambda item: cast(int, item["attempt"]))
        if [item["attempt"] for item in ordered] != list(range(1, len(ordered) + 1)):
            fail("attempt_sequence", "attempt numbers are not contiguous", subject=source_id)
        if any(item["disposition"] not in RETRY_STATES for item in ordered[:-1]):
            fail("attempt_sequence", "an earlier attempt is scope-terminal", subject=source_id)
        if ordered[-1]["disposition"] not in SCOPE_TERMINAL_STATES:
            fail(
                "nonterminal_accounting", "latest attempt is not scope-terminal", subject=source_id
            )


def _validate_row_evidence(
    row: JsonObject,
    events: dict[str, list[JsonObject]],
    attempts: dict[str, JsonObject],
    reader: ArtifactReader,
) -> JsonObject:
    transaction_id = cast(str, row["transaction_id"])
    attempt = attempts.get(transaction_id)
    if attempt is None or not events.get(transaction_id):
        fail("accounting_attempt", "row lacks retained attempt evidence", subject=transaction_id)
    attempt_bytes = _read_json(cast(JsonObject, row["attempt_record_ref"]), reader)
    if attempt_bytes != attempt:
        fail(
            "accounting_attempt",
            "attempt reference differs from retained record",
            subject=transaction_id,
        )
    terminal = sorted(events[transaction_id], key=lambda event: cast(int, event["sequence"]))[-1]
    event_bytes = _read_json(cast(JsonObject, row["terminal_event_ref"]), reader)
    if event_bytes != terminal:
        fail("accounting_event", "terminal-event reference differs", subject=transaction_id)
    expected = (row["source_id"], row["attempt"], row["terminal_state"])
    if (attempt["source_id"], attempt["attempt"], attempt["disposition"]) != expected or (
        terminal["source_id"],
        terminal["attempt"],
        terminal["to_state"],
    ) != expected:
        fail(
            "accounting_join", "row differs from terminal attempt evidence", subject=transaction_id
        )
    attempt_root = PurePosixPath(cast(str, row["attempt_record_ref"]["path"])).parent
    declared_event_paths = {
        candidate
        for path in cast(list[str], attempt["state_event_paths"])
        for candidate in (path, (attempt_root / path).as_posix())
    }
    if cast(str, row["terminal_event_ref"]["path"]) not in declared_event_paths:
        fail(
            "accounting_event",
            "terminal event is absent from attempt paths",
            subject=transaction_id,
        )
    if row["failure_class"] != attempt["failure_class"]:
        fail("accounting_attempt", "row failure class differs from attempt", subject=transaction_id)
    return terminal


def _require_latest_attempt(row: JsonObject, attempts: dict[str, JsonObject]) -> None:
    source_attempts = [
        attempt for attempt in attempts.values() if attempt["source_id"] == row["source_id"]
    ]
    if row["attempt"] != max(cast(int, attempt["attempt"]) for attempt in source_attempts):
        fail(
            "scope_transactions",
            "accounting row does not name latest attempt",
            subject=row["source_id"],
        )


def _validate_success(
    row: JsonObject,
    source: JsonObject,
    completions: dict[str, JsonObject],
    reader: ArtifactReader,
) -> tuple[str, JsonObject]:
    transaction_id = cast(str, row["transaction_id"])
    completion = completions.get(transaction_id)
    if completion is None:
        fail("missing_completion", "successful row lacks completion", subject=row["source_id"])
    if _read_json(cast(JsonObject, row["document_completion_ref"]), reader) != completion:
        fail("missing_completion", "completion reference differs", subject=row["source_id"])
    inventory_ref = cast(JsonObject, row["candidate_inventory_ref"])
    completion_inventory = {
        "path": inventory_ref["path"],
        "sha256": inventory_ref["sha256"],
    }
    if (
        completion["source"] != source
        or completion["candidate_id"] != row["candidate_id"]
        or completion["candidate_inventory"] != completion_inventory
        or completion["processed_pages"] != list(range(1, cast(int, source["pdf_page_count"]) + 1))
        or completion["raw_docling_status"] != "SUCCESS"
        or completion["completion_last"] is not True
        or row["failure_class"] is not None
    ):
        fail("completion_join", "successful accounting evidence differs", subject=row["source_id"])
    verify_ref(inventory_ref, reader)
    return cast(str, row["candidate_id"]), inventory_ref


def _validate_failure(
    row: JsonObject,
    terminal: JsonObject,
    completions: dict[str, JsonObject],
    reader: ArtifactReader,
) -> None:
    attempt_id = cast(str, row["transaction_id"])
    failure_class = row["failure_class"]
    if (
        row["terminal_state"] != "failed_terminal"
        or row["candidate_id"] is not None
        or row["document_completion_ref"] is not None
        or row["candidate_inventory_ref"] is not None
        or attempt_id in completions
        or not isinstance(failure_class, str)
        or not failure_class
        or terminal["to_state"] != "failed_terminal"
    ):
        fail(
            "failed_candidate",
            "failed source has invalid terminal evidence",
            subject=row["source_id"],
        )
    for reference in cast(list[JsonObject], row["retained_evidence_refs"]):
        verify_ref(reference, reader)


def _is_latest_attempt(attempt: JsonObject, attempts: dict[str, JsonObject]) -> bool:
    return cast(int, attempt["attempt"]) == max(
        cast(int, candidate["attempt"])
        for candidate in attempts.values()
        if candidate["source_id"] == attempt["source_id"]
    )


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


def _validate_scope_kind(scope_kind: str, source_count: int) -> None:
    if (scope_kind == "production_full") != (source_count == 35):
        fail("scope_impersonation", "only production_full may contain all 35 sources")


def _read_json(reference: JsonObject, reader: ArtifactReader) -> JsonObject:
    try:
        value = json.loads(verify_ref(reference, reader))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail("artifact_json", f"referenced artifact is not valid JSON: {error}")
    if not isinstance(value, dict):
        fail("artifact_json", "referenced artifact must contain one JSON object")
    return value
