"""Explicit serial runner preserves fatal classification and identity-bound resume."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from document_publication_test_support import _workspace

from er_commons.document_publication import collection_runner as runner


@pytest.mark.parametrize(
    ("text", "fatal"),
    [
        ("resource guard breach", True),
        ("resource budget exceeded", True),
        ("identity mismatch", True),
        ("lineage mismatch", True),
        ("semantic loss", True),
        ("checksum failure", True),
        ("invariant failed", True),
        ("publication failed", True),
        ("ordinary source parsing failure", False),
        ("conversion completed", False),
    ],
)
def test_fatal_patterns_preserve_historical_runner_semantics(text, fatal):
    """Only the existing contract-level fatal categories stop the queue."""
    assert runner._hard_stop(text)[0] is fatal


def _request(tmp_path: Path):
    data, spec = _workspace(tmp_path)
    return runner.CollectionRunRequest(
        spec, data / "explicit-progress", tmp_path, data, all_sources=True
    )


def test_explicit_runner_resumes_only_matching_successful_spec(tmp_path, monkeypatch):
    """A repeated identical queue skips successes; changed spec controls cannot reuse them."""
    request = _request(tmp_path)
    calls = []

    class FakeProcess:
        def __init__(self, command, **kwargs):
            calls.append(command[-1])
            assert kwargs["env"]["ER_COMMONS_DATA_ROOT"] == str(request.data_root)
            kwargs["stdout"].write("ordinary conversion completed\n")

        def wait(self):
            return 0

    monkeypatch.setattr(runner.subprocess, "Popen", FakeProcess)
    assert runner.run_document_collection(request) == 0
    assert calls == ["alpha", "beta"]
    assert runner.run_document_collection(request) == 0
    assert calls == ["alpha", "beta"]
    request.document_spec.write_bytes(request.document_spec.read_bytes() + b" ")
    assert runner.run_document_collection(request) == 0
    assert calls == ["alpha", "beta", "alpha", "beta"]
    events = [json.loads(line) for line in request.progress_path.read_text().splitlines()]
    assert all("document_spec_sha256" in event for event in events)


def test_runner_continues_ordinary_failure_and_stops_fatal_failure(tmp_path, monkeypatch):
    """Ordinary failure yields exit 1; the same queue stops immediately on fatal evidence."""
    request = _request(tmp_path)
    calls = []
    fatal = False

    class FakeProcess:
        def __init__(self, command, **kwargs):
            calls.append(command[-1])
            kwargs["stdout"].write("identity mismatch\n" if fatal else "ordinary source failure\n")

        def wait(self):
            return 1

    monkeypatch.setattr(runner.subprocess, "Popen", FakeProcess)
    assert runner.run_document_collection(request) == 1
    assert calls == ["alpha", "beta"]
    fatal = True
    calls.clear()
    assert runner.run_document_collection(request) == 2
    assert calls == ["alpha"]


@pytest.mark.parametrize("selection", [("beta", "alpha"), ("alpha", "alpha"), ("missing",)])
def test_runner_rejects_ambiguous_or_reordered_selection_before_writes(tmp_path, selection):
    request = replace(_request(tmp_path), all_sources=False, source_ids=selection)
    with pytest.raises(ValueError, match="runner"):
        runner.run_document_collection(request)
    assert not request.progress_root.exists()


def test_runner_rejects_mid_invocation_spec_change_without_success_evidence(tmp_path, monkeypatch):
    """Changed controls never create a reusable success under the initial digest."""
    request = _request(tmp_path)

    class FakeProcess:
        def __init__(self, command, **kwargs):
            pass

        def wait(self):
            request.document_spec.write_bytes(request.document_spec.read_bytes() + b" ")
            return 0

    monkeypatch.setattr(runner.subprocess, "Popen", FakeProcess)
    with pytest.raises(ValueError, match="changed during"):
        runner.run_document_collection(request)
    events = [json.loads(line) for line in request.progress_path.read_text().splitlines()]
    assert [event["event"] for event in events] == ["runner_started"]
