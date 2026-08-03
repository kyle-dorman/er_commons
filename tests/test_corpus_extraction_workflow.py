"""Offline runtime tests for the restartable whole-document stage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from corpus_extraction_test_support import _result, _workspace

from er_commons.corpus_extraction.hooks import WorkflowHooks
from er_commons.corpus_extraction.process import ProcessOutcome
from er_commons.corpus_extraction.workflow import run_document


def test_success_publishes_complete_candidate_then_exactly_reuses(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path)
    calls = 0

    def executor(*args: Any) -> ProcessOutcome:
        nonlocal calls
        calls += 1
        return ProcessOutcome(_result(tmp_path, "alpha"), False, 0, "")

    completion = run_document(data_root, spec_path, "alpha", executor=executor)
    reused = run_document(data_root, spec_path, "alpha", executor=executor)

    assert completion == reused and calls == 1
    payload = json.loads(completion.read_text())
    assert payload["raw_docling_status"] == "SUCCESS"
    assert payload["processed_pages"] == [1, 2]
    assert (completion.parents[1] / "content" / "records.jsonl").is_file()


def test_reuse_is_invalidated_by_current_run_spec_controls(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path)
    calls = 0

    def executor(*args: Any) -> ProcessOutcome:
        nonlocal calls
        calls += 1
        return ProcessOutcome(_result(tmp_path, "alpha"), False, 0, "")

    first = run_document(data_root, spec_path, "alpha", executor=executor)
    payload = json.loads(spec_path.read_text())
    payload["resource_policy"]["queue_capacity"] = 9
    spec_path.write_text(json.dumps(payload))
    second = run_document(data_root, spec_path, "alpha", executor=executor)

    assert first != second
    assert calls == 2


def test_partial_success_is_retained_then_full_retry_publishes(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path, retry_limit=1)
    calls = 0

    def executor(*args: Any) -> ProcessOutcome:
        nonlocal calls
        calls += 1
        status = "PARTIAL_SUCCESS" if calls == 1 else "SUCCESS"
        return ProcessOutcome(_result(tmp_path, "alpha", status=status), False, 0, "")

    completion = run_document(data_root, spec_path, "alpha", executor=executor)

    assert completion.is_file() and calls == 2
    attempts = sorted(
        (data_root / "pipelines/test/task_03f/attempts").glob("*/attempt_record.json")
    )
    records = sorted(
        (json.loads(path.read_text()) for path in attempts),
        key=lambda item: item["attempt"],
    )
    assert [item["disposition"] for item in records] == [
        "failed_retryable",
        "complete",
    ]


def test_interrupted_invocation_recovers_cancelled_attempt_then_increments(
    tmp_path: Path,
) -> None:
    data_root, spec_path = _workspace(tmp_path, retry_limit=1)

    with pytest.raises(KeyboardInterrupt):
        run_document(
            data_root,
            spec_path,
            "alpha",
            executor=lambda *args: (_ for _ in ()).throw(KeyboardInterrupt()),
        )

    completion = run_document(
        data_root,
        spec_path,
        "alpha",
        executor=lambda *args: ProcessOutcome(_result(tmp_path, "alpha"), False, 0, ""),
    )
    records = sorted(
        (
            json.loads(path.read_text())
            for path in (data_root / "pipelines/test/task_03f/attempts").glob(
                "*/attempt_record.json"
            )
        ),
        key=lambda item: item["attempt"],
    )
    assert completion.is_file()
    assert [(item["attempt"], item["disposition"]) for item in records] == [
        (1, "cancelled"),
        (2, "complete"),
    ]
    assert records[0]["transaction_id"] != records[1]["transaction_id"]


def test_child_launch_failure_is_retained_with_observability(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path)

    def fail_launch(*args: Any) -> ProcessOutcome:
        raise OSError("worker launch failed")

    with pytest.raises(OSError, match="worker launch failed"):
        run_document(data_root, spec_path, "alpha", executor=fail_launch)
    attempt = next((data_root / "pipelines/test/task_03f/attempts").iterdir())
    assert json.loads((attempt / "attempt_record.json").read_text())["disposition"] == (
        "failed_terminal"
    )
    assert (attempt / "observability.json").is_file()
    assert (attempt / "resource_record.json").is_file()
    assert json.loads((attempt / "resource_record.json").read_text())["enforcement"] == ("declared")


def test_extra_file_invalidates_reuse_instead_of_silent_acceptance(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path)

    def executor(*args: Any) -> ProcessOutcome:
        return ProcessOutcome(_result(tmp_path, "alpha"), False, 0, "")

    completion = run_document(data_root, spec_path, "alpha", executor=executor)
    (completion.parents[1] / "unexpected.txt").write_text("stale")
    with pytest.raises(ValueError, match="managed-file closure"):
        run_document(data_root, spec_path, "alpha", executor=executor)


def test_changed_upstream_completion_invalidates_reuse(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path)
    completion = run_document(
        data_root,
        spec_path,
        "alpha",
        executor=lambda *args: ProcessOutcome(_result(tmp_path, "alpha"), False, 0, ""),
    )
    upstream = data_root / "owner-alpha/records/completion_record.json"
    upstream.write_text('{"status":"changed"}\n')

    with pytest.raises(ValueError, match="upstream seal differs"):
        run_document(data_root, spec_path, "alpha", executor=lambda *args: pytest.fail())
    assert completion.is_file()


def test_partial_final_namespace_is_rejected_before_execution(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path)
    partial = data_root / "pipelines/test/task_03f/documents/alpha" / ("docv1-" + "f" * 64)
    partial.mkdir(parents=True)

    with pytest.raises(ValueError, match="partial document candidate"):
        run_document(data_root, spec_path, "alpha", executor=lambda *args: pytest.fail())


def test_first_n_result_cannot_publish_a_complete_document(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path)

    def executor(*args: Any) -> ProcessOutcome:
        return ProcessOutcome(_result(tmp_path, "alpha", pages=1), False, 0, "")

    with pytest.raises(RuntimeError, match="retry loop"):
        run_document(data_root, spec_path, "alpha", executor=executor)
    attempts = list((data_root / "pipelines/test/task_03f/attempts").glob("*/attempt_record.json"))
    assert json.loads(attempts[0].read_text())["disposition"] == "failed_terminal"


def test_structured_docling_errors_block_success_publication(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path)

    def executor(*args: Any) -> ProcessOutcome:
        result = _result(tmp_path, "alpha")
        result = result.model_copy(
            update={"structured_errors": [{"category": "inference_failure"}]}
        )
        return ProcessOutcome(result, False, 0, "")

    with pytest.raises(RuntimeError, match="retry loop"):
        run_document(data_root, spec_path, "alpha", executor=executor)


def test_final_canonical_document_must_join_selected_source(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path)
    result = _result(tmp_path, "alpha")
    documents = Path(result.final_candidate_root) / "canonical" / "documents.jsonl"
    record = json.loads(documents.read_text())
    record["source_id"] = "beta"
    documents.write_text(json.dumps(record) + "\n")

    with pytest.raises(ValueError, match="final content candidate differs"):
        run_document(
            data_root,
            spec_path,
            "alpha",
            executor=lambda *args: ProcessOutcome(result, False, 0, ""),
        )


def test_publication_crash_window_is_reconciled_on_reuse(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path)

    def interrupt_after_publication(_completion: Path) -> None:
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        run_document(
            data_root,
            spec_path,
            "alpha",
            executor=lambda *args: ProcessOutcome(_result(tmp_path, "alpha"), False, 0, ""),
            hooks=WorkflowHooks(after_candidate_publish=interrupt_after_publication),
        )
    completion = run_document(
        data_root,
        spec_path,
        "alpha",
        executor=lambda *args: pytest.fail("published candidate should reconcile and reuse"),
    )
    attempt_root = next((data_root / "pipelines/test/task_03f/attempts").iterdir())
    assert completion.is_file()
    assert json.loads((attempt_root / "attempt_record.json").read_text())["disposition"] == (
        "complete"
    )


def test_success_terminal_event_reconstructs_missing_attempt_record(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path)
    interrupted = False

    def interrupt_attempt(disposition: Any) -> None:
        nonlocal interrupted
        if disposition == "complete" and not interrupted:
            interrupted = True
            raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        run_document(
            data_root,
            spec_path,
            "alpha",
            executor=lambda *args: ProcessOutcome(_result(tmp_path, "alpha"), False, 0, ""),
            hooks=WorkflowHooks(before_attempt_record=interrupt_attempt),
        )
    completion = run_document(
        data_root,
        spec_path,
        "alpha",
        executor=lambda *args: pytest.fail("terminal event should reconcile"),
    )
    attempt = next((data_root / "pipelines/test/task_03f/attempts").iterdir())
    assert completion.is_file()
    assert json.loads((attempt / "attempt_record.json").read_text())["disposition"] == "complete"


def test_failure_terminal_event_reconstructs_missing_attempt_record(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path)
    interrupted = False

    def interrupt_attempt(disposition: Any) -> None:
        nonlocal interrupted
        if disposition == "failed_terminal" and not interrupted:
            interrupted = True
            raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        run_document(
            data_root,
            spec_path,
            "alpha",
            executor=lambda *args: ProcessOutcome(
                _result(tmp_path, "alpha", status="FAILURE"), False, 1, "failed"
            ),
            hooks=WorkflowHooks(before_attempt_record=interrupt_attempt),
        )
    with pytest.raises(ValueError, match="already failed terminally"):
        run_document(data_root, spec_path, "alpha", executor=lambda *args: pytest.fail())
    attempt = next((data_root / "pipelines/test/task_03f/attempts").iterdir())
    assert json.loads((attempt / "attempt_record.json").read_text())["disposition"] == (
        "failed_terminal"
    )


def test_configured_offline_preservation_gate_is_persisted(tmp_path: Path) -> None:
    data_root, spec_path = _workspace(tmp_path, preserve=True)
    completion = run_document(
        data_root,
        spec_path,
        "alpha",
        executor=lambda *args: ProcessOutcome(_result(tmp_path, "alpha"), False, 0, ""),
    )
    report = json.loads((completion.parent / "preservation_report.json").read_text())
    assert report["status"] == "exact"
    assert report["mismatches"] == []
