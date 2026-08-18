"""Public read-only observation of checksum-verified Task 03F.2 outcomes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from er_commons.corpus_extraction.candidates import find_reusable_candidate
from er_commons.corpus_extraction.identity import build_transaction_id
from er_commons.corpus_extraction.preflight import DocumentRun, prepare_document_run
from er_commons.corpus_extraction.records import AttemptRecord, DocumentCompletion, StateEvent
from er_commons.corpus_extraction.storage import verify_candidate
from er_commons.corpus_extraction_contract_v1_1.model import JsonObject

TerminalDisposition = Literal["complete", "complete_with_warnings", "failed_terminal"]
TARGET_RECORD_STREAMS = (
    "documents.jsonl",
    "sections.jsonl",
    "tables.jsonl",
    "figures.jsonl",
    "pages.jsonl",
)


@dataclass(frozen=True)
class DocumentTerminalEvidence:
    """One independently verified latest scope-terminal source outcome."""

    source: JsonObject
    source_ordinal: int
    evidence_kind: Literal["document_attempt", "downstream_replay"]
    transaction_id: str
    attempt: int | None
    disposition: TerminalDisposition
    terminal_event_ref: JsonObject | None
    attempt_record_ref: JsonObject | None
    downstream_replay_ref: JsonObject | None
    failure_class: str | None
    retained_evidence_refs: tuple[JsonObject, ...]
    candidate_id: str | None = None
    document_completion_ref: JsonObject | None = None
    candidate_inventory_ref: JsonObject | None = None
    cross_references_ref: JsonObject | None = None
    target_aliases_ref: JsonObject | None = None
    target_records_refs: tuple[JsonObject, ...] = ()


def observe_document_outcome(
    data_root: Path,
    document_run_spec: Path,
    source_id: str,
    *,
    source_ordinal: int,
) -> DocumentTerminalEvidence:
    """Return one verified successful candidate or latest terminal failure."""
    run = prepare_document_run(data_root, document_run_spec, source_id)
    completion_path = find_reusable_candidate(run)
    if completion_path is not None:
        completion = DocumentCompletion.model_validate_json(completion_path.read_bytes())
        candidate_root = completion_path.parents[1]
        verify_candidate(candidate_root, completion.candidate_id, run.source)
        replay_path = candidate_root / "records" / "downstream_replay.json"
        if replay_path.is_file():
            from er_commons.corpus_extraction.downstream_replay import (
                verify_downstream_replay,
            )

            verify_downstream_replay(candidate_root, data_root=data_root)
            identity = json.loads(
                (candidate_root / "records" / "document_identity.json").read_bytes()
            )
            return _successful_evidence(
                run=run,
                source_ordinal=source_ordinal,
                completion=completion,
                completion_path=completion_path,
                disposition=cast(TerminalDisposition, identity["terminal_state"]),
                attempt_number=None,
                evidence_kind="downstream_replay",
                terminal_event_ref=None,
                attempt_record_ref=None,
                downstream_replay_ref=_file_ref(replay_path, run.extraction_root),
            )
        attempt_root, attempt, terminal = _matching_attempt(
            run.extraction_root, run.scope_id, run.source.source_id, run.source.sha256
        )
        if attempt.disposition not in {"complete", "complete_with_warnings"}:
            raise ValueError("candidate attempt does not record terminal success")
        return _successful_evidence(
            run=run,
            source_ordinal=source_ordinal,
            completion=completion,
            completion_path=completion_path,
            disposition=cast(TerminalDisposition, attempt.disposition),
            attempt_number=attempt.attempt,
            evidence_kind="document_attempt",
            terminal_event_ref=_file_ref(terminal, run.extraction_root),
            attempt_record_ref=_file_ref(attempt_root / "attempt_record.json", run.extraction_root),
            downstream_replay_ref=None,
        )

    attempt_root, attempt, terminal = _matching_attempt(
        run.extraction_root, run.scope_id, run.source.source_id, run.source.sha256
    )
    if attempt.disposition != "failed_terminal" or not attempt.failure_class:
        raise ValueError("source lacks a verified scope-terminal outcome")
    retained = tuple(
        _file_ref(path, run.extraction_root)
        for path in sorted(attempt_root.iterdir())
        if path.is_file() and path.name != "attempt_record.json"
    )
    if not retained:
        retained = (_file_ref(terminal, run.extraction_root),)
    return DocumentTerminalEvidence(
        source=run.source.model_dump(mode="json"),
        source_ordinal=source_ordinal,
        evidence_kind="document_attempt",
        transaction_id=attempt.transaction_id,
        attempt=attempt.attempt,
        disposition="failed_terminal",
        terminal_event_ref=_file_ref(terminal, run.extraction_root),
        attempt_record_ref=_file_ref(attempt_root / "attempt_record.json", run.extraction_root),
        downstream_replay_ref=None,
        failure_class=attempt.failure_class,
        retained_evidence_refs=retained,
    )


def _successful_evidence(
    *,
    run: DocumentRun,
    source_ordinal: int,
    completion: DocumentCompletion,
    completion_path: Path,
    disposition: TerminalDisposition,
    attempt_number: int | None,
    evidence_kind: Literal["document_attempt", "downstream_replay"],
    terminal_event_ref: JsonObject | None,
    attempt_record_ref: JsonObject | None,
    downstream_replay_ref: JsonObject | None,
) -> DocumentTerminalEvidence:
    candidate_root = completion_path.parents[1]
    canonical = candidate_root / "content" / "canonical"
    return DocumentTerminalEvidence(
        source=run.source.model_dump(mode="json"),
        source_ordinal=source_ordinal,
        evidence_kind=evidence_kind,
        transaction_id=completion.transaction_id,
        attempt=attempt_number,
        disposition=disposition,
        terminal_event_ref=terminal_event_ref,
        attempt_record_ref=attempt_record_ref,
        downstream_replay_ref=downstream_replay_ref,
        failure_class=None,
        retained_evidence_refs=(),
        candidate_id=completion.candidate_id,
        document_completion_ref=_file_ref(completion_path, run.extraction_root),
        candidate_inventory_ref=_file_ref(
            candidate_root / "records" / "artifact_inventory.json", run.extraction_root
        ),
        cross_references_ref=_file_ref(canonical / "cross_references.jsonl", run.extraction_root),
        target_aliases_ref=_file_ref(canonical / "target_aliases.jsonl", run.extraction_root),
        target_records_refs=tuple(
            _file_ref(canonical / name, run.extraction_root) for name in TARGET_RECORD_STREAMS
        ),
    )


def _matching_attempt(
    extraction_root: Path,
    scope_id: str,
    source_id: str,
    source_sha256: str,
) -> tuple[Path, AttemptRecord, Path]:
    matches: list[tuple[Path, AttemptRecord, Path]] = []
    attempts_root = extraction_root / "attempts"
    for root in sorted(attempts_root.glob("txv1-*.*")):
        record_path = root / "attempt_record.json"
        if not record_path.is_file():
            continue
        attempt = AttemptRecord.model_validate_json(record_path.read_bytes())
        expected = build_transaction_id(
            scope_id=scope_id,
            source_id=source_id,
            source_sha256=source_sha256,
            attempt=attempt.attempt,
        )
        if attempt.source_id != source_id or attempt.transaction_id != expected:
            continue
        event_paths = [root / path for path in attempt.state_event_paths]
        events = [StateEvent.model_validate_json(path.read_bytes()) for path in event_paths]
        if not events or events[-1].to_state != attempt.disposition:
            raise ValueError("attempt record and terminal event differ")
        matches.append((root, attempt, event_paths[-1]))
    if not matches:
        raise ValueError(f"no retained attempt evidence for {source_id}")
    matches.sort(key=lambda item: item[1].attempt)
    numbers = [item[1].attempt for item in matches]
    if numbers != list(range(1, numbers[-1] + 1)):
        raise ValueError("source attempt history is not contiguous")
    latest = matches[-1]
    if latest[1].disposition not in {"complete", "complete_with_warnings", "failed_terminal"}:
        raise ValueError("latest source attempt is not scope-terminal")
    return latest


def _file_ref(path: Path, root: Path) -> JsonObject:
    """Return one contained exact-byte reference for terminal evidence."""
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        raise ValueError(f"terminal evidence escapes or is absent: {path}")
    value = resolved.read_bytes()
    return {
        "path": resolved.relative_to(root.resolve()).as_posix(),
        "sha256": hashlib.sha256(value).hexdigest(),
        "byte_size": len(value),
    }
