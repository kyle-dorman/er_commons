"""Offline lifecycle coverage for the human-owned semantic materializer."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from er_commons.document_records.document_structure import lifecycle, sealing
from er_commons.document_records.document_structure.config import DocumentStructureExpectations
from er_commons.document_records.document_structure.runtime import RuntimeContext
from er_commons.document_records.document_structure.sealing import DocumentStructureSealingInputs
from er_commons.document_records.record_mapping.publication import CandidateWorkspace, write_json

CANDIDATE_ID = "exv1-" + "a" * 64


def test_fake_lifecycle_publishes_then_checksum_reuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The full lifecycle reaches publication and reuse without document tooling."""
    context = _context(tmp_path)
    _patch_lifecycle_edges(monkeypatch)

    completion = lifecycle.build_validate_and_publish(
        context=context,
        identity={"extraction_id": CANDIDATE_ID},
        candidate_id=CANDIDATE_ID,
    )

    candidate_root = context.task_root / CANDIDATE_ID
    assert completion == candidate_root / "records" / "completion_record.json"
    assert candidate_root.is_dir()

    reused_completion = lifecycle.reuse_completed_candidate(
        context=context, candidate_id=CANDIDATE_ID
    )
    assert reused_completion == completion


def test_fake_lifecycle_retains_failed_workspace_without_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failure after partial sealing cannot leave a misleading completed candidate."""
    context = _context(tmp_path)

    def fail_after_partial(**kwargs: Any) -> None:
        root = cast(Path, kwargs["root"])
        write_json(root / "records" / "partial.json", {"stage": "sealing"})
        write_json(root / "records" / "completion_record.json", {"status": "complete"})
        raise RuntimeError("simulated sealing failure")

    monkeypatch.setattr(lifecycle, "_write_candidate_workspace", fail_after_partial)

    with pytest.raises(RuntimeError, match="simulated sealing failure"):
        lifecycle.build_validate_and_publish(
            context=context,
            identity={"extraction_id": CANDIDATE_ID},
            candidate_id=CANDIDATE_ID,
        )

    attempts = sorted((context.task_root / "attempts").iterdir())
    partial = next(
        attempt for attempt in attempts if (attempt / "records" / "partial.json").is_file()
    )
    assert not (partial / "records" / "completion_record.json").exists()
    attempt = next(
        attempt / "records" / "attempt_record.json"
        for attempt in attempts
        if (attempt / "records" / "attempt_record.json").is_file()
    )
    assert "simulated sealing failure" in attempt.read_text()
    assert not (context.task_root / CANDIDATE_ID).exists()


def test_failure_retention_error_does_not_mask_original(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cleanup diagnostics augment rather than replace the application failure."""
    context = _context(tmp_path)
    monkeypatch.setattr(
        lifecycle,
        "_write_candidate_workspace",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("original failure")),
    )
    monkeypatch.setattr(
        lifecycle,
        "preserve_failed_attempt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("retention failure")),
    )

    with pytest.raises(RuntimeError, match="original failure") as captured:
        lifecycle.build_validate_and_publish(
            context=context,
            identity={"extraction_id": CANDIDATE_ID},
            candidate_id=CANDIDATE_ID,
        )

    assert captured.value.__notes__ == ["failed to retain semantic attempt: retention failure"]


def test_keyboard_interrupt_is_retained_and_retry_is_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An operator interruption cannot leave completion or block a clean retry."""
    context = _context(tmp_path)

    def interrupt_after_completion(**kwargs: Any) -> None:
        root = cast(Path, kwargs["root"])
        write_json(root / "records" / "partial.json", {"phase": "serialization"})
        write_json(root / "records" / "completion_record.json", {"status": "complete"})
        raise KeyboardInterrupt

    monkeypatch.setattr(lifecycle, "_write_candidate_workspace", interrupt_after_completion)
    with pytest.raises(KeyboardInterrupt):
        lifecycle.build_validate_and_publish(
            context=context,
            identity={"extraction_id": CANDIDATE_ID},
            candidate_id=CANDIDATE_ID,
        )

    attempts = tuple((context.task_root / "attempts").iterdir())
    assert len(attempts) == 1
    assert (attempts[0] / "records" / "partial.json").is_file()
    assert not (attempts[0] / "records" / "completion_record.json").exists()
    assert "KeyboardInterrupt" in (attempts[0] / "records" / "attempt_record.json").read_text()
    assert not (context.task_root / CANDIDATE_ID).exists()

    _patch_lifecycle_edges(monkeypatch)
    completion = lifecycle.build_validate_and_publish(
        context=context,
        identity={"extraction_id": CANDIDATE_ID},
        candidate_id=CANDIDATE_ID,
    )
    assert completion.is_file()


def test_prepublish_verification_failure_never_creates_final_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A sealed-but-invalid staging tree remains attempt evidence, never a final."""
    context = _context(tmp_path)

    def write_complete_workspace(**kwargs: Any) -> None:
        root = cast(Path, kwargs["root"])
        write_json(root / "records" / "completion_record.json", {"status": "complete"})

    monkeypatch.setattr(lifecycle, "_write_candidate_workspace", write_complete_workspace)
    monkeypatch.setattr(
        lifecycle,
        "verify_completed_document_structure",
        lambda *_args: (_ for _ in ()).throw(ValueError("invalid sealed workspace")),
    )

    with pytest.raises(ValueError, match="invalid sealed workspace"):
        lifecycle.build_validate_and_publish(
            context=context,
            identity={"extraction_id": CANDIDATE_ID},
            candidate_id=CANDIDATE_ID,
        )

    assert not (context.task_root / CANDIDATE_ID).exists()
    attempt = next((context.task_root / "attempts").iterdir())
    assert not (attempt / "records" / "completion_record.json").exists()


def test_post_rename_durability_failure_retains_diagnostic_and_final_is_reusable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A parent-fsync error leaves a valid final plus separate attempt evidence."""
    context = _context(tmp_path)
    _patch_lifecycle_edges(monkeypatch)

    def rename_then_fail(workspace: CandidateWorkspace) -> Path:
        workspace.staging_root.rename(workspace.final_root)
        raise OSError("destination parent fsync failed")

    monkeypatch.setattr(lifecycle, "publish_workspace", rename_then_fail)
    with pytest.raises(OSError, match="destination parent fsync failed"):
        lifecycle.build_validate_and_publish(
            context=context,
            identity={"extraction_id": CANDIDATE_ID},
            candidate_id=CANDIDATE_ID,
        )

    final_root = context.task_root / CANDIDATE_ID
    assert (final_root / "records" / "completion_record.json").is_file()
    attempts = tuple((context.task_root / "attempts").iterdir())
    assert len(attempts) == 1
    assert (
        "destination parent fsync failed"
        in (attempts[0] / "records" / "attempt_record.json").read_text()
    )
    assert lifecycle.reuse_completed_candidate(context=context, candidate_id=CANDIDATE_ID).is_file()


def test_semantic_validation_reads_the_configured_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The schema recorded in candidate identity is the schema used by validation."""
    schema_path = tmp_path / "configured-schema.json"
    write_json(schema_path, {"configured": True})
    seen: list[object] = []

    def validator(schema: object) -> SimpleNamespace:
        seen.append(schema)
        return SimpleNamespace(validate=lambda _bundle: None)

    monkeypatch.setattr(
        sealing,
        "Draft202012Validator",
        validator,
    )
    monkeypatch.setattr(sealing, "document_structure_validation_bundle", lambda **_kwargs: {})
    monkeypatch.setattr(
        sealing, "validate_document_structure_contract", lambda *_args, **_kwargs: None
    )
    build = SimpleNamespace(
        collections={"pages": [], "sections": []},
        page_label_observations=[],
        target_aliases=[],
        bridge_entries=[],
        bridge_evidence={},
    )
    support = SimpleNamespace(correspondence={})
    inputs = DocumentStructureSealingInputs(
        project_root=tmp_path,
        identity={},
        baseline_root=tmp_path,
        baseline_candidate_id="exv1-" + "b" * 64,
        baseline_producer_run_id="prv1-baseline",
        hierarchy_producer_run_id="prv1-hierarchy",
        control={"physical_page_count": 0},
        inherited_warnings=[],
        expectations=DocumentStructureExpectations(
            section_count=0,
            bridge_entry_count=0,
            canonical_block_count=0,
            heading_count=0,
            direct_membership_count=0,
            mapped_block_count=0,
            table_replacement_count=0,
            figure_suppression_count=0,
        ),
        source_semantic_disposition="strict_quality_gate",
        semantic_schema_path=schema_path,
    )

    sealing._validate_semantic_contract(build, support, inputs)  # type: ignore[arg-type]

    assert seen == [{"configured": True}]


def test_strict_quality_gate_records_observed_sections_without_reviewed_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fresh machine validation must not require Appendix P's reviewed count."""
    schema_path = tmp_path / "schema.json"
    write_json(schema_path, {})
    monkeypatch.setattr(
        sealing,
        "Draft202012Validator",
        lambda _schema: SimpleNamespace(validate=lambda _bundle: None),
    )
    monkeypatch.setattr(sealing, "document_structure_validation_bundle", lambda **_kwargs: {})
    monkeypatch.setattr(
        sealing, "validate_document_structure_contract", lambda *_args, **_kwargs: None
    )
    build = SimpleNamespace(
        collections={"pages": [], "sections": [{"id": "observed"}]},
        page_label_observations=[],
        bridge_evidence={},
    )
    inputs = DocumentStructureSealingInputs(
        project_root=tmp_path,
        identity={},
        baseline_root=tmp_path,
        baseline_candidate_id="exv1-" + "b" * 64,
        baseline_producer_run_id="prv1-baseline",
        hierarchy_producer_run_id="prv1-hierarchy",
        control={"physical_page_count": 0},
        inherited_warnings=[],
        expectations=None,
        source_semantic_disposition="strict_quality_gate",
        semantic_schema_path=schema_path,
    )

    sealing._validate_semantic_contract(  # type: ignore[arg-type]
        build, SimpleNamespace(correspondence={}), inputs
    )


def _context(tmp_path: Path) -> RuntimeContext:
    task_root = tmp_path / "task"
    return cast(
        RuntimeContext,
        SimpleNamespace(
            task_root=task_root,
            construction_inputs=None,
            inputs=None,
            config=SimpleNamespace(
                baseline_candidate_id="exv1-" + "b" * 64,
                baseline_producer_run_id="prv1-baseline",
                hierarchy_producer_run_id="prv1-hierarchy",
            ),
            project_root=tmp_path,
            semantic_schema_path=tmp_path / "configured-semantic-schema.json",
        ),
    )


def _patch_lifecycle_edges(monkeypatch: pytest.MonkeyPatch) -> None:
    def write_complete_workspace(**kwargs: Any) -> None:
        root = cast(Path, kwargs["root"])
        write_json(root / "canonical" / "payload.json", {"status": "built"})
        write_json(root / "records" / "completion_record.json", {"status": "complete"})

    monkeypatch.setattr(lifecycle, "_write_candidate_workspace", write_complete_workspace)
    monkeypatch.setattr(
        lifecycle,
        "verify_completed_document_structure",
        lambda root, candidate_id: root / "records" / "completion_record.json",
    )
