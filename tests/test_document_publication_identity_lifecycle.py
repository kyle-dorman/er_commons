"""Offline runtime tests for the restartable whole-document stage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from document_publication_test_support import _result, _workspace
from pydantic import ValidationError

from er_commons.document_publication.config import ResourcePolicy
from er_commons.document_publication.identity import (
    build_candidate_id,
    build_scope_id,
    build_transaction_id,
)
from er_commons.document_publication.lifecycle import EventWriter
from er_commons.document_publication.process import ProcessOutcome
from er_commons.document_publication.records import (
    AttemptRecord,
    DocumentCompletion,
    ObservabilityRecord,
    ResourceEnforcementRecord,
    ResourceRecord,
    StateEvent,
)
from er_commons.document_publication.workflow import publish_document


def test_identities_are_typed_deterministic_and_attempt_sensitive() -> None:
    scope = build_scope_id(run_spec_sha256="a" * 64, production_extraction_id="exv1-" + "b" * 64)
    first = build_transaction_id(
        scope_id=scope, source_id="alpha", source_sha256="c" * 64, attempt=1
    )
    second = build_transaction_id(
        scope_id=scope, source_id="alpha", source_sha256="c" * 64, attempt=2
    )
    candidate = build_candidate_id(
        production_extraction_id="exv1-" + "b" * 64,
        source_id="alpha",
        content_digest="d" * 64,
        control_digest="e" * 64,
    )
    assert scope.startswith("scopev1-") and first.startswith("txv1-")
    assert first != second and candidate.startswith("docv1-")


def test_resource_policy_rejects_unbounded_or_inverted_deadlines() -> None:
    with pytest.raises(ValidationError):
        ResourcePolicy.model_validate(
            {
                "document_concurrency": 5,
                "page_batch_size": 4,
                "stage_batch_size": 4,
                "queue_capacity": 8,
                "cpu_threads_per_document": 4,
                "device": "cpu",
                "memory_estimate_bytes": 1,
                "storage_estimate_bytes": 1,
                "docling_timeout_seconds": 20,
                "outer_process_deadline_seconds": 10,
                "cancellation_grace_seconds": 1,
                "retry_limit": 0,
            }
        )


def test_event_writer_accepts_legal_history_and_rejects_premature_completion(
    tmp_path: Path,
) -> None:
    writer = EventWriter(
        tmp_path / "events",
        transaction_id="txv1-" + "1" * 64,
        source_id="alpha",
        attempt=1,
    )
    writer.transition("selected", "PENDING")
    with pytest.raises(ValueError, match="illegal state transition"):
        writer.transition("complete", "SUCCESS")


@pytest.mark.parametrize(
    ("terminal", "raw_status"),
    [
        ("complete", "SUCCESS"),
        ("complete_with_warnings", "SUCCESS"),
        ("failed_retryable", "PARTIAL_SUCCESS"),
        ("failed_terminal", "FAILURE"),
        ("cancelled", None),
    ],
)
def test_event_writer_accepts_every_legal_terminal_transition(
    tmp_path: Path, terminal: str, raw_status: str | None
) -> None:
    writer = EventWriter(
        tmp_path / terminal,
        transaction_id="txv1-" + "2" * 64,
        source_id="alpha",
        attempt=1,
    )
    writer.transition("selected", "PENDING")
    writer.transition("running", "STARTED")
    writer.transition(terminal, raw_status)  # type: ignore[arg-type]


def test_event_writer_rejects_incoherent_raw_status(tmp_path: Path) -> None:
    writer = EventWriter(
        tmp_path / "status",
        transaction_id="txv1-" + "3" * 64,
        source_id="alpha",
        attempt=1,
    )
    with pytest.raises(ValueError, match="invalid for state"):
        writer.transition("selected", "SUCCESS")


def test_state_and_completion_records_validate_with_owned_models(
    tmp_path: Path,
) -> None:
    data_root, spec_path = _workspace(tmp_path)

    def executor(*args: Any) -> ProcessOutcome:
        return ProcessOutcome(_result(tmp_path, "alpha"), False, 0, "")

    completion_path = publish_document(data_root, spec_path, "alpha", executor=executor)
    attempt_root = next((data_root / "pipelines/test/task_03f/attempts").iterdir())
    event = json.loads(next((attempt_root / "state_events").glob("*.json")).read_text())
    attempt = json.loads((attempt_root / "attempt_record.json").read_text())
    resources = json.loads((attempt_root / "resource_record.json").read_text())
    resource_enforcement = json.loads((attempt_root / "resource_enforcement.json").read_text())
    observability = json.loads((attempt_root / "observability.json").read_text())
    completion = json.loads(completion_path.read_text())
    for model, value in (
        (StateEvent, event),
        (AttemptRecord, attempt),
        (ResourceRecord, resources),
        (ResourceEnforcementRecord, resource_enforcement),
        (ObservabilityRecord, observability),
        (DocumentCompletion, completion),
    ):
        model.model_validate(value)


def test_run_spec_cannot_substitute_an_arbitrary_production_identity(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path)
    payload = json.loads(spec_path.read_text())
    payload["production_extraction_id"] = "exv1-" + "0" * 64
    spec_path.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="production extraction ID differs"):
        publish_document(data_root, spec_path, "alpha", executor=lambda *args: pytest.fail())


def test_nonfixture_scope_must_join_production_release_and_manifest(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path)
    payload = json.loads(spec_path.read_text())
    payload["scope_kind"] = "engineering_smoke"
    spec_path.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="differs from production source scope"):
        publish_document(data_root, spec_path, "alpha", executor=lambda *args: pytest.fail())
