"""Run-local current recipe verification and historical source selection contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from document_publication_test_support import _workspace
from test_task06b_publication_reuse import _current_recipe

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.artifact_verification import VerificationBudget
from er_commons.document_publication.accepted_inputs import prepare_publication_inputs
from er_commons.document_publication.identity import canonical_digest
from er_commons.document_publication.preflight import prepare_accepted_document_run


def _prepared_workspace(tmp_path: Path):
    """Use real config, recipe, source-manifest and preparation boundaries."""
    data, spec = _workspace(tmp_path)
    _current_recipe(spec, tmp_path)
    budget = VerificationBudget()
    prepared = prepare_publication_inputs(data, spec, repository_root=tmp_path, budget=budget)
    return data, spec, budget, prepared


def test_shared_manifest_is_verified_once_for_prepared_sources(tmp_path, monkeypatch):
    """Preparing alpha and beta consumes their shared manifest only once."""
    data, spec, budget, prepared = _prepared_workspace(tmp_path)
    original_open = Path.open

    def no_source_or_shared_reopen(path, *args, **kwargs):
        if path.suffix == ".pdf" or path.name == "source_manifest.json":
            raise AssertionError(f"unexpected source/shared manifest access: {path}")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", no_source_or_shared_reopen)
    before = budget.hashed_bytes, budget.read_bytes
    sources = [
        prepare_accepted_document_run(
            data, spec, source, repository_root=tmp_path, budget=budget, prepared_inputs=prepared
        ).source.source_id
        for source in ("alpha", "beta")
    ]
    assert sources == ["alpha", "beta"]
    assert (budget.hashed_bytes, budget.read_bytes) == before
    hashes = [
        row
        for row in budget.observations
        if row["role"] == "source_manifest" and row["verification_mode"] == "bytes_verified"
    ]
    assert len(hashes) == 1


def test_new_writer_rejects_changed_recorded_behavior(tmp_path):
    """Historical recipes stay readable, but current execution must match its code."""
    data, spec = _workspace(tmp_path)
    _current_recipe(spec, tmp_path)
    (tmp_path / "writer.py").write_text("# changed current behavior\n")
    with pytest.raises(ValueError, match="production artifact differs"):
        prepare_publication_inputs(
            data, spec, repository_root=tmp_path, budget=VerificationBudget()
        )


@pytest.mark.parametrize(
    "mutation", ["source", "spec_path", "spec_bytes", "writer", "manifest", "repository"]
)
def test_prepared_publication_rejects_changed_context(tmp_path, mutation):
    """A checked source cannot be transplanted or consumed after controls change."""
    data, spec, budget, prepared = _prepared_workspace(tmp_path)
    source = "alpha"
    repository = tmp_path
    if mutation == "source":
        source = "not_selected"
    elif mutation == "spec_path":
        other = tmp_path / "other.json"
        other.write_bytes(spec.read_bytes())
        spec = other
    elif mutation == "spec_bytes":
        spec.write_bytes(spec.read_bytes() + b" ")
    elif mutation == "writer":
        (tmp_path / "writer.py").write_text("# changed writer\n")
    elif mutation == "repository":
        repository = tmp_path / "other_repository"
    else:
        manifest = data / "release/records/source_manifest.json"
        manifest.write_bytes(manifest.read_bytes() + b" ")
    with pytest.raises(ValueError, match="prepared publication"):
        prepare_accepted_document_run(
            data, spec, source, repository_root=repository, budget=budget, prepared_inputs=prepared
        )


def test_current_recipe_rejects_changed_sealed_source_scope(tmp_path):
    """Same source IDs cannot hide a changed source identity under an old recipe."""
    data, spec = _workspace(tmp_path)
    _current_recipe(spec, tmp_path)
    manifest_path = data / "release/records/source_manifest.json"
    completion_path = manifest_path.parent / "completion_record.json"
    manifest = json.loads(manifest_path.read_text())
    recipe_path = tmp_path / "current_recipe.json"
    recipe = json.loads(recipe_path.read_text())
    scope = recipe["preimage"]["production_scope"]
    scope.update(
        allowed_scope_kinds=["production_full"],
        source_release_version="release",
        source_manifest={
            "path": "release/records/source_manifest.json",
            "sha256": sha256_file(manifest_path),
        },
        release_completion={
            "path": "release/records/completion_record.json",
            "sha256": sha256_file(completion_path),
        },
        ordered_source_records_sha256=canonical_digest(
            [
                {key: record[key] for key in ("source_id", "sha256", "pdf_page_count")}
                for record in manifest["sources"]
            ]
        ),
    )
    recipe["identity_sha256"] = canonical_digest(recipe["preimage"])
    recipe["extraction_id"] = "exv1-" + recipe["identity_sha256"]
    write_json_atomic(recipe_path, recipe)
    document = json.loads(spec.read_text())
    document.update(scope_kind="production_full", production_extraction_id=recipe["extraction_id"])
    write_json_atomic(spec, document)
    prepare_publication_inputs(data, spec, repository_root=tmp_path, budget=VerificationBudget())
    manifest["sources"][0]["sha256"] = "f" * 64
    write_json_atomic(manifest_path, manifest)
    completion = json.loads(completion_path.read_text())
    completion["manifest"].update(
        sha256=sha256_file(manifest_path), byte_size=manifest_path.stat().st_size
    )
    write_json_atomic(completion_path, completion)
    with pytest.raises(ValueError, match="scope|source|manifest"):
        prepare_publication_inputs(
            data, spec, repository_root=tmp_path, budget=VerificationBudget()
        )


def test_prepared_publication_rejects_replacement_invocation_budget(tmp_path):
    """Prepared source selection cannot reset the invocation's prior verification cost."""
    data, spec, _, prepared = _prepared_workspace(tmp_path)
    with pytest.raises(ValueError, match="budget"):
        prepare_accepted_document_run(
            data,
            spec,
            "alpha",
            repository_root=tmp_path,
            budget=VerificationBudget(),
            prepared_inputs=prepared,
        )


@pytest.mark.parametrize("mutation", ["link_spec", "shared_control"])
def test_prepared_relink_rejects_mutated_snapshot_files(tmp_path, mutation):
    """Prepared relinking rejects changed shared controls before source selection."""
    from types import SimpleNamespace

    from er_commons.document_publication.accepted_inputs import file_stamp
    from er_commons.document_records.document_references.relink_publication import (
        verify_prepared_link_spec,
    )

    spec_path = tmp_path / "link.json"
    shared_path = tmp_path / "policy.json"
    spec_path.write_text("{}")
    shared_path.write_text("{}")
    prepared = SimpleNamespace(
        spec_path=spec_path,
        spec_sha256=sha256_file(spec_path),
        budget=VerificationBudget(),
        repository_root=tmp_path,
        input_stamps={spec_path: file_stamp(spec_path), shared_path: file_stamp(shared_path)},
    )
    verify_prepared_link_spec(prepared)
    changed = spec_path if mutation == "link_spec" else shared_path
    changed.write_text('{"changed":true}')
    with pytest.raises(ValueError, match="prepared link"):
        verify_prepared_link_spec(prepared)


def test_preparation_rejects_source_evidence_mutated_after_validation(tmp_path, monkeypatch):
    """Snapshot stamps must describe verified bytes, not a later unvalidated state."""
    from er_commons.document_publication import accepted_inputs

    data, spec = _workspace(tmp_path)
    _current_recipe(spec, tmp_path)
    original = accepted_inputs.load_sealed_manifest_metadata

    def read_then_mutate(root, selection, budget):
        manifest = original(root, selection, budget)
        path = root / selection.source_manifest_path
        path.write_bytes(path.read_bytes() + b" ")
        return manifest

    monkeypatch.setattr(accepted_inputs, "load_sealed_manifest_metadata", read_then_mutate)
    with pytest.raises(ValueError, match="changed|drift"):
        prepare_publication_inputs(
            data, spec, repository_root=tmp_path, budget=VerificationBudget()
        )
