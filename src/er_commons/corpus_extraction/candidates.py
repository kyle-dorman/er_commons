"""Build, verify, find, and reconcile completed document candidates."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from er_commons.corpus_extraction.attempts import record_attempt
from er_commons.corpus_extraction.identity import build_candidate_id, canonical_digest
from er_commons.corpus_extraction.lifecycle import Disposition
from er_commons.corpus_extraction.preflight import DocumentRun
from er_commons.corpus_extraction.records import (
    ArtifactRef,
    DocumentIdentityRecord,
    PipelineResult,
    SourceIdentity,
    StateEvent,
)
from er_commons.corpus_extraction.storage import content_digest, verify_candidate
from er_commons.source_freeze import sha256_file, write_json_atomic

LOGGER = logging.getLogger(__name__)
SuccessDisposition = Literal["complete", "complete_with_warnings"]


@dataclass(frozen=True)
class CandidateIdentity:
    """Typed in-memory projection of the persisted candidate identity record."""

    candidate_id: str
    content_digest: str
    control_digest: str
    terminal_state: SuccessDisposition
    hierarchy_disposition: dict[str, object]
    stage_completions: dict[str, dict[str, object]]

    def as_record(self, run: DocumentRun) -> DocumentIdentityRecord:
        """Return the exact v1 identity record written into a candidate."""
        return DocumentIdentityRecord(
            schema_version="er_commons.document_candidate_identity.v1",
            production_extraction_id=run.spec.production_extraction_id,
            candidate_id=self.candidate_id,
            source=run.source,
            content_digest=self.content_digest,
            control_digest=self.control_digest,
            hierarchy_disposition=self.hierarchy_disposition,
            run_spec_sha256=run.spec_sha256,
            stage_completions={
                role: ArtifactRef.model_validate(reference)
                for role, reference in self.stage_completions.items()
            },
            terminal_state=self.terminal_state,
        )


def build_candidate_identity(
    run: DocumentRun,
    *,
    content_root: Path,
    result: PipelineResult,
) -> CandidateIdentity:
    """Derive the document ID from content and all publication controls."""
    terminal_state: SuccessDisposition = "complete_with_warnings" if result.warnings else "complete"
    stage_completions = {
        role: reference.model_dump(mode="json")
        for role, reference in result.stage_completions.items()
    }
    control_digest = canonical_digest(
        {
            "hierarchy_disposition": run.hierarchy_disposition,
            "run_spec_sha256": run.spec_sha256,
            "stage_completions": stage_completions,
            "terminal_state": terminal_state,
        }
    )
    digest = content_digest(content_root)
    candidate_id = build_candidate_id(
        production_extraction_id=run.spec.production_extraction_id,
        source_id=run.source.source_id,
        content_digest=digest,
        control_digest=control_digest,
    )
    return CandidateIdentity(
        candidate_id=candidate_id,
        content_digest=digest,
        control_digest=control_digest,
        terminal_state=terminal_state,
        hierarchy_disposition=run.hierarchy_disposition,
        stage_completions=stage_completions,
    )


def write_candidate_identity(
    records_root: Path, identity: CandidateIdentity, run: DocumentRun
) -> None:
    """Persist the candidate identity after its managed content is complete."""
    records_root.mkdir()
    write_json_atomic(
        records_root / "document_identity.json",
        identity.as_record(run).model_dump(mode="json"),
    )


def find_reusable_candidate(run: DocumentRun) -> Path | None:
    """Return the sole checksum-valid candidate matching this run contract."""
    if not run.final_parent.is_dir():
        return None
    matches: list[Path] = []
    for root in sorted(run.final_parent.glob("docv1-*")):
        identity_path = root / "records" / "document_identity.json"
        if not identity_path.is_file():
            raise ValueError(f"partial document candidate occupies final namespace: {root}")
        identity = json.loads(identity_path.read_text())
        recorded_source = SourceIdentity.model_validate(identity.get("source"))
        verify_candidate(root, root.name, recorded_source)
        if not _matches_run(identity, run):
            continue
        verify_identity_and_upstreams(root, identity=identity, data_root=run.data_root)
        if (root / "records" / "downstream_replay.json").is_file():
            from er_commons.corpus_extraction.downstream_replay import (
                verify_downstream_replay,
            )

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
    completion = json.loads((root / "records" / "completion_record.json").read_text())
    transaction_id = str(completion["transaction_id"])
    attempts_root = root.parents[2] / "attempts"
    matches = [path for path in attempts_root.glob(f"{transaction_id}.*") if path.is_dir()]
    if len(matches) != 1:
        raise ValueError("published candidate lacks one matching retained attempt")
    attempt_root = matches[0]
    event_paths = sorted((attempt_root / "state_events").glob("*.json"))
    events = [json.loads(path.read_text()) for path in event_paths]
    if not events:
        raise ValueError("published candidate attempt lacks state events")
    if events[-1].get("to_state") == "running":
        recovered_path = _write_recovered_success_event(
            attempt_root=attempt_root,
            transaction_id=transaction_id,
            identity=identity,
            events=events,
        )
        event_paths.append(recovered_path)
        events.append(json.loads(recovered_path.read_text()))
        _write_recovered_success_attempt(
            attempt_root=attempt_root,
            transaction_id=transaction_id,
            identity=identity,
            event_paths=event_paths,
            message="reconciled after completion-last atomic publication",
            completion_path=root / "records" / "completion_record.json",
        )
        LOGGER.info("Reconciled published candidate transaction %s", transaction_id)
    if events[-1].get("to_state") != identity.get("terminal_state"):
        raise ValueError("candidate completion and terminal state event differ")
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
    attempt_record = json.loads(attempt_record_path.read_text())
    if attempt_record.get("disposition") != identity.get("terminal_state"):
        raise ValueError("candidate completion and attempt record differ")


def _matches_run(identity: dict[str, object], run: DocumentRun) -> bool:
    return bool(
        identity.get("production_extraction_id") == run.spec.production_extraction_id
        and identity.get("source") == run.source.model_dump(mode="json")
        and identity.get("run_spec_sha256") == run.spec_sha256
        and identity.get("hierarchy_disposition") == run.hierarchy_disposition
    )


def verify_identity_and_upstreams(
    root: Path, *, identity: dict[str, object], data_root: Path
) -> None:
    """Recompute the candidate ID and every content-owner completion seal."""
    control_digest = canonical_digest(
        {
            "hierarchy_disposition": identity.get("hierarchy_disposition"),
            "run_spec_sha256": identity.get("run_spec_sha256"),
            "stage_completions": identity.get("stage_completions"),
            "terminal_state": identity.get("terminal_state"),
        }
    )
    if identity.get("control_digest") != control_digest:
        raise ValueError("document candidate control digest differs")
    source = SourceIdentity.model_validate(identity["source"])
    candidate_id = build_candidate_id(
        production_extraction_id=str(identity["production_extraction_id"]),
        source_id=source.source_id,
        content_digest=content_digest(root / "content"),
        control_digest=control_digest,
    )
    if identity.get("candidate_id") != candidate_id or root.name != candidate_id:
        raise ValueError("document candidate identity does not derive from managed inputs")
    completions = identity.get("stage_completions")
    if not isinstance(completions, dict):
        raise ValueError("document candidate lacks typed stage completions")
    for role, value in completions.items():
        reference = ArtifactRef.model_validate(value)
        path = (data_root / reference.path).resolve()
        if (
            not path.is_relative_to(data_root.resolve())
            or not path.is_file()
            or sha256_file(path) != reference.sha256
        ):
            raise ValueError(f"document candidate upstream seal differs: {role}")


def _write_recovered_success_event(
    *,
    attempt_root: Path,
    transaction_id: str,
    identity: dict[str, object],
    events: list[dict[str, object]],
) -> Path:
    source = SourceIdentity.model_validate(identity["source"])
    path = attempt_root / "state_events" / f"{len(events) + 1:04d}.json"
    attempt_number = events[-1]["attempt"]
    if not isinstance(attempt_number, int):
        raise ValueError("published candidate attempt number is invalid")
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
    return path


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
    last_event = json.loads(event_paths[-1].read_text())
    record_attempt(
        attempt_root,
        transaction_id=transaction_id,
        source_id=source.source_id,
        attempt=int(last_event["attempt"]),
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
