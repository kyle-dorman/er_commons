"""Synthetic stage integration protects review freshness and source-free publication."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from er_commons.artifact_io import canonical_json_sha256
from er_commons.response_inventory import release_execution
from er_commons.response_inventory import release_workflow as workflow
from er_commons.response_inventory.release_inputs import ReleaseInputs
from er_commons.response_inventory.release_review import validate_decisions
from er_commons.response_inventory.release_storage import digest, encode, read_container


def setup_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[workflow.ReleaseRun, ReleaseInputs, dict[str, Any]]:
    """Use a tiny reference container; no upstream parser/resolver participates."""
    data = tmp_path / "data"
    component = data / "pipeline/working/05d/revision/inventory/source_records.jsonl"
    component.parent.mkdir(parents=True)
    component.write_bytes(b'{"record_type":"fixture"}\n')
    components = [
        {
            "role": "source_records",
            "path": str(component.relative_to(data)),
            "sha256": None,
            "size_bytes": component.stat().st_size,
            "check_mode": "accepted_semantic_digest_and_size",
            "record_semantic_digest": canonical_json_sha256([{"record_type": "fixture"}]),
        }
    ]
    inputs = ReleaseInputs([], [], [], [], [], [], [], [], components, {}, {}, {}, "a" * 64)
    selection: dict[str, Any] = {"obligations": [], "strata": [], "selection_digest": "b" * 64}
    spec = {
        "authorization": dict.fromkeys(
            ("execution", "finalization", "publication", "acceptance"), True
        ),
        "repository_bindings": [{"path": "fixture.py", "sha256": "c" * 64}],
    }
    root = data / "pipeline/working/05h"
    run = workflow.ReleaseRun(spec, "plan05hv1-" + "d" * 64, tmp_path, data, root, 1)
    monkeypatch.setattr(workflow, "load_inputs", lambda _run: inputs)
    monkeypatch.setattr(workflow, "selected_review", lambda _run, _inputs: selection)
    monkeypatch.setattr(
        workflow,
        "_base_payloads",
        lambda _run, current, selected: {
            "inventory/components.json": encode(current.components),
            "records/review_selection.json": encode(selected),
        },
    )
    monkeypatch.setattr(
        release_execution,
        "verify_terminal_execution",
        lambda _run, operation, attempt: {
            "operation": operation,
            "attempt": attempt,
            "path": f"{operation}.json",
            "sha256": "e" * 64,
        },
    )
    monkeypatch.setattr(release_execution, "verify_finalized_result", lambda *_: None)
    return run, inputs, selection


def quality(
    run: workflow.ReleaseRun, inputs: ReleaseInputs, selection: dict[str, Any]
) -> dict[str, Any]:
    """An explicitly synthetic quality attestation binds the exact pre-completion payloads."""
    review = validate_decisions(selection, [], run.plan_id)
    return {
        "plan_id": run.plan_id,
        "input_semantic_digest": inputs.semantic_digest,
        "repository_bindings": run.spec["repository_bindings"],
        "status": "passed",
        "material_findings": [],
        "reviewer": "Synthetic independent reviewer",
        "independent_review": True,
        "dimensions": dict.fromkeys(
            ("readability", "editability", "debuggability", "operations", "testing"), "passed"
        ),
        "review_payload_digest": workflow.review_payload_digest(run, inputs, selection, [], review),
    }


def bind_review(run: workflow.ReleaseRun, report: dict[str, Any]) -> None:
    """Put synthetic review inputs under their explicit repository authority."""
    for key, value in (("review_decisions", []), ("quality_report", report)):
        path = run.repository_root / f"{key}.json"
        path.write_bytes(encode(value))
        run.spec[key] = {
            "authority": "repository",
            "path": path.name,
            "sha256": digest(path.read_bytes()),
        }


def test_prepare_resume_and_first_seal_preserve_upstream(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run, inputs, selection = setup_run(tmp_path, monkeypatch)
    component = run.artifact_root / inputs.components[0]["path"]
    before = component.read_bytes(), component.stat().st_mtime_ns
    first = workflow.prepare(run)
    checkpoint = run.prepared_root / "records/completion.json"
    stamp = checkpoint.stat().st_mtime_ns
    resumed = replace(run, attempt=2, resume_from=1)
    assert workflow.prepare(resumed)["completion"] == first["completion"]
    assert checkpoint.stat().st_mtime_ns == stamp
    bind_review(run, quality(run, inputs, selection))
    result = workflow.finalize(run)
    final = Path(result["candidate_root"])
    completion, payloads = read_container(final)
    sealed = json.loads(payloads["inventory/components.json"])[0]
    assert sealed["sha256"] == digest(before[0])
    assert inputs.components[0]["sha256"] is None
    assert (component.read_bytes(), component.stat().st_mtime_ns) == before
    assert json.loads(payloads["records/execution_evidence.json"])[0]["operation"] == "prepare"
    assert workflow.finalize(run)["completion"] == completion
    assert workflow.validate_candidate(run, final)["status"] == "valid"


def test_quality_cannot_cover_changed_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run, inputs, selection = setup_run(tmp_path, monkeypatch)
    report = quality(run, inputs, selection)
    changed = {**selection, "selection_digest": "f" * 64}
    with pytest.raises(ValueError, match="assembled review payloads"):
        workflow._final_extras(run, inputs, changed, [], report, [])


@pytest.mark.parametrize("key, suffix", [("review_decisions", ".pdf"), ("quality_report", ".png")])
def test_evidence_type_rejected_before_any_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, key: str, suffix: str
) -> None:
    run, _, _ = setup_run(tmp_path, monkeypatch)
    run.spec[key] = {
        "authority": "artifact_root",
        "path": f"prohibited{suffix}",
        "sha256": "a" * 64,
    }
    monkeypatch.setattr(
        workflow, "verify_file_binding", lambda *_: pytest.fail("prohibited evidence was read")
    )
    with pytest.raises(ValueError, match="source-free JSON"):
        workflow._evidence(run, key)


def test_prepared_semantic_drift_stops(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run, inputs, _ = setup_run(tmp_path, monkeypatch)
    workflow.prepare(run)
    changed = replace(inputs, semantic_digest="f" * 64)
    monkeypatch.setattr(workflow, "load_inputs", lambda _: changed)
    with pytest.raises(ValueError, match="closure mismatch"):
        workflow.validate_candidate(run, run.prepared_root)


def test_different_finalization_cannot_borrow_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run, _, _ = setup_run(tmp_path, monkeypatch)
    monkeypatch.setattr(workflow, "validate_candidate", lambda *_: {"status": "valid"})
    with pytest.raises(ValueError, match="exact supervised finalization"):
        workflow.execute(run, "publish", candidate=run.root / "other/finalized")


@pytest.mark.parametrize("operation", ["review", "publish", "accept"])
def test_named_stage_rejects_disabled_authorization_before_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    """Calling a stage directly must retain the same gate as supervised dispatch."""
    run, _, _ = setup_run(tmp_path, monkeypatch)
    run.spec["authorization"] = dict.fromkeys(run.spec["authorization"], False)
    monkeypatch.setattr(
        workflow, "validate_candidate", lambda *_: pytest.fail("read before authorization")
    )
    with pytest.raises(ValueError, match="requires separate explicit"):
        if operation == "review":
            workflow.review(run)
        elif operation == "publish":
            workflow.publish(run, run.root / "candidate")
        else:
            workflow.accept(run, run.root / "candidate", accepted_by="", accepted_at="")


def test_review_cache_reuse_rejects_child_symlinks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Disposable cache reuse must not follow links into unrelated artifacts."""
    from er_commons.response_inventory import release_views

    run, _, _ = setup_run(tmp_path, monkeypatch)
    monkeypatch.setattr(workflow, "validate_candidate", lambda *_: {})
    monkeypatch.setattr(workflow, "build_view_index", lambda *_: [])
    monkeypatch.setattr(release_views, "build_review_cache", lambda *_, **__: {})
    target = tmp_path / "unrelated.txt"
    target.write_text("not review evidence")
    run.cache_root.mkdir(parents=True)
    (run.cache_root / "card.html").symlink_to(target)
    with pytest.raises(ValueError, match="symbolic link"):
        workflow.review(run)
