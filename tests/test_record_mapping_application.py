"""Offline application-shell tests for canonical candidate publication."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from er_commons.document_records.record_mapping import MappingContractError, materialize
from er_commons.document_records.record_mapping.publication import (
    sha256_file,
    write_inventory,
    write_json,
)

CANDIDATE_ID = "exv1-" + "c" * 64


def _configure_fake_run(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    input_events: list[str] = []
    config = SimpleNamespace(
        artifact_relative_root=Path("pipelines/task03d1-test"),
    )
    monkeypatch.setattr(
        materialize,
        "load_record_mapping_config",
        lambda _path: (config, "config-sha"),
    )

    def identity_inputs() -> object:
        input_events.append("identity")
        return object()

    def semantic_inputs() -> object:
        input_events.append("semantic")
        return object()

    prepared = SimpleNamespace(identity_inputs=identity_inputs, semantic_inputs=semantic_inputs)

    def prepare_inputs(_root: Path, _config: object) -> object:
        input_events.append("prepare")
        return prepared

    monkeypatch.setattr(
        materialize,
        "prepare_record_mapping_inputs",
        prepare_inputs,
    )
    monkeypatch.setattr(
        materialize,
        "build_candidate_identity",
        lambda **_kwargs: {"extraction_id": CANDIDATE_ID},
    )
    return input_events


def _write_fake_candidate(root: Path) -> None:
    write_json(root / "canonical" / "documents.jsonl", {"id": "fake-document"})
    inventory_path = write_inventory(root)
    write_json(
        root / "records" / "completion_record.json",
        {
            "schema_version": "er_commons.canonicalization_completion.v1",
            "candidate_id": CANDIDATE_ID,
            "release_candidate": False,
            "candidate_scope": "document_scoped",
            "source_ids": ["fake"],
            "status": "complete",
            "manifest_sha256": "0" * 64,
            "artifact_inventory": "records/artifact_inventory.json",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "warning_count": 0,
            "error_count": 0,
        },
    )


def test_identity_owned_paths_include_shared_conversion_view_dependencies() -> None:
    paths = materialize._owned_paths(
        materialize.PROJECT_ROOT / "configs/brisbane_baylands_2025_deir_task03d_appendix_p_v1.json",
        materialize.MAPPING_POLICY_PATH,
    )
    relative = {
        path.relative_to(materialize.PROJECT_ROOT).as_posix()
        for path in paths
        if path.is_relative_to(materialize.PROJECT_ROOT)
    }

    assert {
        "src/er_commons/artifact_io.py",
        "src/er_commons/document_parsing/content_parsing/evidence.py",
        "src/er_commons/document_parsing/content_parsing/records.py",
        "src/er_commons/document_parsing/content_parsing/references.py",
        "src/er_commons/document_parsing/content_parsing/sources.py",
        "src/er_commons/source_release/models.py",
    } <= relative


def test_fake_application_publishes_then_checksum_reuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_events = _configure_fake_run(monkeypatch)
    build_calls = 0

    def fake_build(**kwargs: Any) -> None:
        nonlocal build_calls
        build_calls += 1
        _write_fake_candidate(kwargs["staging_root"])

    monkeypatch.setattr(materialize, "build_candidate_in_workspace", fake_build)
    config_path = tmp_path / "config.json"

    completion = materialize.map_document_records(tmp_path, config_path)
    assert input_events == ["prepare", "identity", "semantic"]
    published_root = completion.parents[1]
    first_hashes = {
        path.relative_to(published_root): sha256_file(path)
        for path in published_root.rglob("*")
        if path.is_file()
    }

    def unexpected_build(**_kwargs: Any) -> None:
        raise AssertionError("completed candidate should be reused")

    monkeypatch.setattr(
        materialize,
        "build_candidate_in_workspace",
        unexpected_build,
    )
    monkeypatch.setattr(
        materialize,
        "prepare_record_mapping_inputs",
        lambda _root, _config: SimpleNamespace(
            identity_inputs=lambda: object(),
            semantic_inputs=lambda: (_ for _ in ()).throw(
                AssertionError("semantic inputs must not load for exact reuse")
            ),
        ),
    )
    reused = materialize.map_document_records(tmp_path, config_path)
    second_hashes = {
        path.relative_to(published_root): sha256_file(path)
        for path in published_root.rglob("*")
        if path.is_file()
    }

    assert reused == completion
    assert build_calls == 1
    assert second_hashes == first_hashes


def test_fake_application_preserves_failure_without_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_fake_run(monkeypatch)

    def fail_build(**kwargs: Any) -> None:
        write_json(kwargs["staging_root"] / "partial.json", {"stage": "content"})
        raise RuntimeError("synthetic content failure")

    monkeypatch.setattr(materialize, "build_candidate_in_workspace", fail_build)

    with pytest.raises(RuntimeError, match="synthetic content failure"):
        materialize.map_document_records(tmp_path, tmp_path / "config.json")

    attempts = list((tmp_path / "pipelines" / "task03d1-test" / "attempts").iterdir())
    assert len(attempts) == 1
    assert (attempts[0] / "partial.json").is_file()
    assert not (attempts[0] / "records" / "completion_record.json").exists()
    assert not (tmp_path / "pipelines" / "task03d1-test" / CANDIDATE_ID).exists()


def test_application_verifies_staging_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_fake_run(monkeypatch)

    def corrupt_build(**kwargs: Any) -> None:
        root = kwargs["staging_root"]
        _write_fake_candidate(root)
        (root / "canonical/documents.jsonl").write_text("corrupt after seal")

    monkeypatch.setattr(materialize, "build_candidate_in_workspace", corrupt_build)

    with pytest.raises(MappingContractError, match="checksum differs"):
        materialize.map_document_records(tmp_path, tmp_path / "config.json")

    task_root = tmp_path / "pipelines/task03d1-test"
    assert not (task_root / CANDIDATE_ID).exists()
    attempt = next((task_root / "attempts").iterdir())
    assert not (attempt / "records/completion_record.json").exists()


def test_keyboard_interrupt_is_retained_without_completion_and_retry_is_clean(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_fake_run(monkeypatch)

    def interrupt_after_seal(**kwargs: Any) -> None:
        _write_fake_candidate(kwargs["staging_root"])
        raise KeyboardInterrupt

    monkeypatch.setattr(materialize, "build_candidate_in_workspace", interrupt_after_seal)
    config_path = tmp_path / "config.json"

    with pytest.raises(KeyboardInterrupt):
        materialize.map_document_records(tmp_path, config_path)

    task_root = tmp_path / "pipelines/task03d1-test"
    attempt = next((task_root / "attempts").iterdir())
    assert not (attempt / "records/completion_record.json").exists()
    assert not (task_root / CANDIDATE_ID).exists()

    monkeypatch.setattr(
        materialize,
        "build_candidate_in_workspace",
        lambda **kwargs: _write_fake_candidate(kwargs["staging_root"]),
    )
    completion = materialize.map_document_records(tmp_path, config_path)

    assert completion == task_root / CANDIDATE_ID / "records/completion_record.json"
    assert completion.is_file()
