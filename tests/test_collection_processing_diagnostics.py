"""Recovery and diagnostic contracts for collection-stage publication."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from er_commons.collection_processing.attempt_storage import read_attempt_events
from er_commons.collection_processing.domain import StageBuild, StageName
from er_commons.collection_processing.publication import StagePublisher


def _build(identity: str = "acctv2-test") -> StageBuild:
    return StageBuild(
        name=StageName.ACCOUNTING,
        identity=identity,
        payloads={"accounting.json": b"{}\n"},
        completion={"schema_version": "test.completion.v1", "status": "complete"},
    )


def _attempt_root(tmp_path: Path, identity: str = "acctv2-test") -> Path:
    return tmp_path / "scopes/scope-test/attempts/accounting" / identity / "attempt_0001"


def test_incomplete_journal_and_atomic_temporary_are_recovered(tmp_path: Path) -> None:
    attempt_root = _attempt_root(tmp_path)
    (attempt_root / "state_events").mkdir(parents=True)
    (attempt_root / "staging").mkdir()
    abandoned = attempt_root / "state_events/0001.json.part"
    abandoned.write_text("partial")

    published = StagePublisher(tmp_path, "scope-test").publish(_build())

    assert not abandoned.exists()
    assert [record["disposition"] for record in published.attempts] == ["cancelled", "complete"]
    cancelled = json.loads((attempt_root / "attempt_record.json").read_text())
    assert cancelled["failure_class"] == "InterruptedPublication"
    assert cancelled["recorded_at_utc"]
    assert not list(attempt_root.rglob("*.part"))


def test_empty_event_directory_is_valid_interrupted_input(tmp_path: Path) -> None:
    events_root = tmp_path / "state_events"
    events_root.mkdir()

    assert read_attempt_events(events_root) == ()


@pytest.mark.parametrize(
    ("relative_path", "content", "message"),
    [
        ("state_events/0001.json", "not-json", "collection stage event is invalid"),
        ("attempt_record.json", "[]", "collection attempt record is invalid"),
        ("attempt_record.json", "{}", "collection attempt record is invalid"),
    ],
)
def test_corrupt_journal_reports_exact_artifact_path(
    tmp_path: Path,
    relative_path: str,
    content: str,
    message: str,
) -> None:
    attempt_root = _attempt_root(tmp_path)
    path = attempt_root / relative_path
    path.parent.mkdir(parents=True)
    path.write_text(content)

    with pytest.raises(ValueError) as caught:
        StagePublisher(tmp_path, "scope-test").publish(_build())

    assert message in str(caught.value)
    assert str(path) in str(caught.value)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("stage_type", "identity differs"),
        ("stage_id", "identity differs"),
        ("attempt", "identity differs"),
        ("disposition", "differs from terminal event"),
        ("failure", "complete attempt requires completion and no failure"),
        ("empty_failure", "String should have at least 1 character"),
        ("missing_completion", "complete attempt requires completion and no failure"),
        ("wrong_completion", "completion path differs"),
    ],
)
def test_typed_attempt_record_rejects_semantic_drift(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    publisher = StagePublisher(tmp_path, "scope-test")
    publisher.publish(_build())
    record_path = _attempt_root(tmp_path) / "attempt_record.json"
    record = json.loads(record_path.read_text())
    if mutation == "stage_type":
        record["stage_type"] = "target_index"
    elif mutation == "stage_id":
        record["stage_id"] = "acctv2-other"
    elif mutation == "attempt":
        record["attempt"] = 2
    elif mutation == "disposition":
        record.update(disposition="cancelled", failure_class="InterruptedPublication")
        record["completion_path"] = None
    elif mutation == "failure":
        record["failure_class"] = "UnexpectedFailure"
    elif mutation == "empty_failure":
        record.update(disposition="cancelled", failure_class="")
        record["completion_path"] = None
    elif mutation == "missing_completion":
        record["completion_path"] = None
    else:
        record["completion_path"] = str(tmp_path / "wrong-completion.json")
    record_path.write_text(json.dumps(record))

    with pytest.raises(ValueError, match=message) as caught:
        publisher.publish(_build())

    assert str(record_path) in str(caught.value)


def test_attempt_record_must_match_terminal_event(tmp_path: Path) -> None:
    publisher = StagePublisher(tmp_path, "scope-test")
    publisher.publish(_build())
    event_path = _attempt_root(tmp_path) / "state_events/0003.json"
    event = json.loads(event_path.read_text())
    event["to_state"] = "cancelled"
    event_path.write_text(json.dumps(event))

    with pytest.raises(ValueError, match="differs from terminal event") as caught:
        publisher.publish(_build())

    assert str(_attempt_root(tmp_path) / "attempt_record.json") in str(caught.value)


def test_stage_lifecycle_logs_publish_and_exact_reuse(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="er_commons.collection_processing.publication")
    publisher = StagePublisher(tmp_path, "scope-test")

    first = publisher.publish(_build())
    second = publisher.publish(_build())

    assert first.completion_path == second.completion_path
    messages = [record.getMessage() for record in caplog.records]
    assert sum("Starting collection stage" in message for message in messages) == 2
    assert any(
        "Published collection stage" in message and "wall_seconds=" in message
        for message in messages
    )
    assert any(
        "Reused collection stage" in message and "wall_seconds=" in message for message in messages
    )
    complete_record = json.loads(
        (
            tmp_path
            / "scopes/scope-test/attempts/accounting/acctv2-test/attempt_0001/attempt_record.json"
        ).read_text()
    )
    assert complete_record["wall_seconds"] >= 0
