"""Offline runtime tests for the restartable whole-document stage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from document_publication_test_support import _source_record, _workspace

from er_commons.document_publication import process as process_module
from er_commons.document_publication.config import ResourcePolicy, load_document_run_spec
from er_commons.document_publication.records import SourceIdentity
from er_commons.document_publication.storage import (
    import_content,
    reserve_candidate_workspace,
    verify_candidate,
    write_inventory,
)


def test_precompletion_workspace_cannot_verify_or_enter_final_namespace(tmp_path: Path) -> None:
    source_root = tmp_path / "owner"
    source_root.mkdir()
    (source_root / "content.json").write_text("{}")
    attempt_root = tmp_path / "attempt"
    attempt_root.mkdir()
    final_parent = tmp_path / "documents" / "alpha"
    workspace = reserve_candidate_workspace(attempt_root, final_parent)
    import_content(source_root, workspace.staging_root)
    write_inventory(workspace.staging_root)
    source = _source_record(tmp_path, "alpha")
    source_identity = SourceIdentity(
        source_id="alpha",
        sha256=source["sha256"],
        pdf_page_count=source["pdf_page_count"],
    )

    with pytest.raises(ValueError, match="lacks completion"):
        verify_candidate(
            workspace.staging_root,
            "docv1-" + "1" * 64,
            source_identity,
        )
    assert not final_parent.exists()


def test_outer_deadline_terminates_then_returns_nonpublishable_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeProcess:
        returncode = None
        terminated = False
        pid = 123

        def communicate(self, timeout: float | None = None) -> tuple[str, str]:
            if not self.terminated:
                raise process_module.subprocess.TimeoutExpired("worker", timeout)
            self.returncode = -15
            return "", "terminated"

    child = FakeProcess()
    popen_options: dict[str, object] = {}

    def fake_popen(*args: Any, **kwargs: Any) -> FakeProcess:
        popen_options.update(kwargs)
        return child

    def fake_killpg(pid: int, signal_number: int) -> None:
        assert pid == child.pid
        child.terminated = True

    monkeypatch.setattr(process_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(process_module.os, "killpg", fake_killpg)
    resources = ResourcePolicy(
        document_concurrency=1,
        page_batch_size=4,
        stage_batch_size=4,
        queue_capacity=8,
        cpu_threads_per_document=4,
        device="cpu",
        memory_estimate_bytes=1,
        storage_estimate_bytes=1,
        docling_timeout_seconds=1,
        outer_process_deadline_seconds=2,
        cancellation_grace_seconds=1,
        retry_limit=0,
    )
    outcome = process_module.run_isolated_document(
        data_root=tmp_path,
        project_root=tmp_path,
        run_spec_path=tmp_path / "spec.json",
        source_id="alpha",
        attempt_root=tmp_path,
        resources=resources,
    )
    assert outcome.timed_out and outcome.result is None and child.terminated
    assert outcome.return_code == child.returncode
    assert outcome.stdout == ""
    assert popen_options["start_new_session"] is True


def test_run_spec_has_no_implicit_source_and_requires_document_authority(tmp_path: Path) -> None:
    _data_root, spec_path = _workspace(tmp_path)
    spec, _digest = load_document_run_spec(spec_path)
    assert not hasattr(spec, "source_id")
    with pytest.raises(ValueError, match="lacks one hierarchy disposition"):
        spec.hierarchy_disposition("gamma")


def test_child_output_retains_a_bounded_diagnostic_tail() -> None:
    """A noisy child cannot make retained failure evidence grow without bound."""
    value = "prefix" + "x" * process_module.MAX_RETAINED_OUTPUT_CHARS

    bounded = process_module._bounded_output(value)

    assert bounded.endswith("x" * process_module.MAX_RETAINED_OUTPUT_CHARS)
    assert "6 earlier characters omitted" in bounded


def test_process_outcome_combines_return_code_and_both_output_streams() -> None:
    """Retained failures give an operator enough context to reproduce the child exit."""
    outcome = process_module.ProcessOutcome(None, False, 7, "stderr detail", "stdout detail")

    assert outcome.diagnostic_text == (
        "return_code=7\nstderr:\nstderr detail\nstdout:\nstdout detail"
    )


def test_accepted_v1_identity_remains_legacy_publication_evidence() -> None:
    """The immutable pilot identity must not impersonate the moved v2 runtime."""
    record = json.loads(
        Path(
            "benchmarks/er_bench/fixtures/corpus_extraction/v1_1/production_identity_preimage.json"
        ).read_text()
    )
    owned = {item["path"] for item in record["preimage"]["corpus_workflow_contract"]["owned_code"]}
    assert any(path.startswith("src/er_commons/corpus_extraction/") for path in owned)
    assert not any(path.startswith("src/er_commons/document_publication/") for path in owned)
    assert "src/er_commons/cli.py" in owned
