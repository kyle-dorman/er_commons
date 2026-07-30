"""Offline application-shell tests for canonical candidate publication."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from er_commons.canonical_extraction import materialize
from er_commons.canonical_extraction.publication import (
    sha256_file,
    write_inventory,
    write_json,
)

CANDIDATE_ID = "exv1-" + "c" * 64


def _configure_fake_run(monkeypatch: pytest.MonkeyPatch) -> None:
    config = SimpleNamespace(
        artifact_relative_root=Path("pipelines/task03d1-test"),
    )
    monkeypatch.setattr(
        materialize,
        "load_canonicalization_config",
        lambda _path: (config, "config-sha"),
    )
    monkeypatch.setattr(
        materialize,
        "load_canonicalization_inputs",
        lambda _root, _config: object(),
    )
    monkeypatch.setattr(
        materialize,
        "build_candidate_identity",
        lambda **_kwargs: {"extraction_id": CANDIDATE_ID},
    )


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


def test_fake_application_publishes_then_checksum_reuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_fake_run(monkeypatch)
    build_calls = 0

    def fake_build(**kwargs: Any) -> None:
        nonlocal build_calls
        build_calls += 1
        _write_fake_candidate(kwargs["staging_root"])

    monkeypatch.setattr(materialize, "build_candidate_in_workspace", fake_build)
    config_path = tmp_path / "config.json"

    completion = materialize.run_document_canonicalization(tmp_path, config_path)
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
    reused = materialize.run_document_canonicalization(tmp_path, config_path)
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
        materialize.run_document_canonicalization(tmp_path, tmp_path / "config.json")

    attempts = list((tmp_path / "pipelines" / "task03d1-test" / "attempts").iterdir())
    assert len(attempts) == 1
    assert (attempts[0] / "partial.json").is_file()
    assert not (attempts[0] / "records" / "completion_record.json").exists()
    assert not (tmp_path / "pipelines" / "task03d1-test" / CANDIDATE_ID).exists()
