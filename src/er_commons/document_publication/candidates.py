"""Build, verify, find, and reconcile completed document candidates."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from er_commons.artifact_io import write_json_atomic
from er_commons.document_publication.attempts import record_attempt
from er_commons.document_publication.candidate_construction import (
    CandidateIdentity as CandidateIdentity,
)
from er_commons.document_publication.candidate_construction import (
    build_candidate_identity as build_candidate_identity,
)
from er_commons.document_publication.candidate_identity_validation import (
    verify_identity_and_upstreams,
)
from er_commons.document_publication.downstream_replay_validation import (
    verify_downstream_replay,
)
from er_commons.document_publication.lifecycle import Disposition
from er_commons.document_publication.preflight import DocumentRun
from er_commons.document_publication.records import (
    AttemptRecord,
    DocumentCompletion,
    DocumentIdentityRecord,
    SourceIdentity,
    StateEvent,
)
from er_commons.document_publication.retained_evidence import (
    read_attempt_record,
    read_retained_record,
    read_state_events,
    require_retained_evidence,
)
from er_commons.document_publication.storage import verify_candidate

LOGGER = logging.getLogger(__name__)
CandidateEvidenceKind = Literal["document_attempt", "downstream_replay"]


def write_candidate_identity(
    records_root: Path, identity: CandidateIdentity, run: DocumentRun
) -> None:
    """Persist the candidate identity after its managed content is complete."""
    records_root.mkdir()
    write_json_atomic(
        records_root / "document_identity.json",
        identity.as_record(run).model_dump(mode="json"),
    )


def find_reusable_candidate(
    run: DocumentRun,
    *,
    evidence_kind: CandidateEvidenceKind | None = None,
) -> Path | None:
    """Return the sole valid candidate matching the run and required evidence kind."""
    if not run.final_parent.is_dir():
        return None
    matches: list[Path] = []
    for root in sorted(run.final_parent.glob("docv1-*")):
        identity_path = root / "records" / "document_identity.json"
        if not identity_path.is_file():
            raise ValueError(f"partial document candidate occupies final namespace: {root}")
        identity_record = read_retained_record(
            identity_path,
            DocumentIdentityRecord,
            subject="candidate identity",
        )
        identity = identity_record.model_dump(mode="json")
        recorded_source = identity_record.source
        verify_candidate(root, root.name, recorded_source)
        if not _matches_run(identity, run):
            continue
        is_downstream_replay = (root / "records" / "downstream_replay.json").is_file()
        if evidence_kind is not None and is_downstream_replay != (
            evidence_kind == "downstream_replay"
        ):
            continue
        verify_identity_and_upstreams(root, identity=identity, data_root=run.data_root)
        if is_downstream_replay:
            verify_downstream_replay(root, data_root=run.data_root)
        else:
            reconcile_published_attempt(root, identity)
        matches.append(root / "records" / "completion_record.json")
    if len(matches) > 1:
        raise ValueError("multiple reusable document candidates match the same contract")
    if matches:
        LOGGER.info("Reusing document candidate %s", matches[0].parents[1].name)
    return matches[0] if matches else None


def reconcile_published_attempt(root: Path, identity: dict[str, object]) -> None:
    """Close the explicit crash window after atomic candidate publication."""
    completion_path = root / "records" / "completion_record.json"
    completion = read_retained_record(
        completion_path,
        DocumentCompletion,
        subject="candidate completion",
    )
    transaction_id = completion.transaction_id
    attempts_root = root.parents[2] / "attempts"
    matches = [path for path in attempts_root.glob(f"{transaction_id}.*") if path.is_dir()]
    require_retained_evidence(
        len(matches) == 1,
        path=attempts_root,
        subject="published attempt directory",
        detail=f"expected one directory for {transaction_id}, observed {len(matches)}",
    )
    attempt_root = matches[0]
    event_paths = sorted((attempt_root / "state_events").glob("*.json"))
    events = read_state_events(attempt_root / "state_events")
    require_retained_evidence(
        bool(events),
        path=attempt_root / "state_events",
        subject="published attempt state history",
        detail="no state events were retained",
    )
    if events[-1].to_state == "running":
        recovered_path, recovered_event = _write_recovered_success_event(
            attempt_root=attempt_root,
            transaction_id=transaction_id,
            identity=identity,
            events=events,
        )
        event_paths.append(recovered_path)
        events.append(recovered_event)
        _write_recovered_success_attempt(
            attempt_root=attempt_root,
            transaction_id=transaction_id,
            identity=identity,
            event_paths=event_paths,
            message="reconciled after completion-last atomic publication",
            completion_path=root / "records" / "completion_record.json",
        )
        LOGGER.info("Reconciled published candidate transaction %s", transaction_id)
    require_retained_evidence(
        events[-1].to_state == identity.get("terminal_state"),
        path=event_paths[-1],
        subject="candidate terminal state",
        detail=(
            f"identity records {identity.get('terminal_state')}, "
            f"event records {events[-1].to_state}"
        ),
    )
    attempt_record_path = attempt_root / "attempt_record.json"
    if not attempt_record_path.is_file():
        _write_recovered_success_attempt(
            attempt_root=attempt_root,
            transaction_id=transaction_id,
            identity=identity,
            event_paths=event_paths,
            message="reconstructed from retained terminal state event and candidate",
            completion_path=root / "records" / "completion_record.json",
        )
    attempt_record = read_attempt_record(attempt_record_path)
    _verify_reconciled_attempt(
        attempt_record,
        attempt_record_path,
        transaction_id=transaction_id,
        identity=identity,
    )


def _verify_reconciled_attempt(
    record: AttemptRecord,
    path: Path,
    *,
    transaction_id: str,
    identity: dict[str, object],
) -> None:
    """Require the retained attempt to identify the published terminal result."""
    expected_source = SourceIdentity.model_validate(identity["source"])
    expected_disposition = identity.get("terminal_state")
    require_retained_evidence(
        (
            record.transaction_id == transaction_id
            and record.source_id == expected_source.source_id
            and record.disposition == expected_disposition
        ),
        path=path,
        subject="published attempt record",
        detail=("transaction, source, or disposition differs from the published candidate"),
    )


def _matches_run(identity: dict[str, object], run: DocumentRun) -> bool:
    return bool(
        identity.get("production_extraction_id") == run.spec.production_extraction_id
        and identity.get("source") == run.source.model_dump(mode="json")
        and identity.get("run_spec_sha256") == run.spec_sha256
        and identity.get("hierarchy_disposition") == run.hierarchy_disposition
    )


def _write_recovered_success_event(
    *,
    attempt_root: Path,
    transaction_id: str,
    identity: dict[str, object],
    events: list[StateEvent],
) -> tuple[Path, StateEvent]:
    source = SourceIdentity.model_validate(identity["source"])
    path = attempt_root / "state_events" / f"{len(events) + 1:04d}.json"
    attempt_number = events[-1].attempt
    event = StateEvent(
        transaction_id=transaction_id,
        source_id=source.source_id,
        attempt=attempt_number,
        sequence=len(events) + 1,
        from_state="running",
        to_state=_successful_disposition(str(identity["terminal_state"])),
        raw_docling_status="SUCCESS",
    )
    write_json_atomic(path, event.model_dump(mode="json"))
    return path, event


def _write_recovered_success_attempt(
    *,
    attempt_root: Path,
    transaction_id: str,
    identity: dict[str, object],
    event_paths: list[Path],
    message: str,
    completion_path: Path,
) -> None:
    source = SourceIdentity.model_validate(identity["source"])
    terminal_state = _successful_disposition(str(identity["terminal_state"]))
    event = read_retained_record(event_paths[-1], StateEvent, subject="terminal state event")
    record_attempt(
        attempt_root,
        transaction_id=transaction_id,
        source_id=source.source_id,
        attempt=event.attempt,
        disposition=terminal_state,
        failure_class=None,
        message=message,
        event_paths=event_paths,
        completion_path=str(completion_path),
    )


def _successful_disposition(value: str) -> Disposition:
    if value not in {"complete", "complete_with_warnings"}:
        raise ValueError(f"candidate terminal success state is invalid: {value}")
    return value  # type: ignore[return-value]
