"""Focused checks for authority-aware resolved-spec references."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from er_commons.authority_reference import AuthorityReference, reference_for_path
from er_commons.document_publication.config import DocumentRunSpec


def test_artifact_reference_resolves_and_verifies_its_declared_root(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    artifacts = tmp_path / "artifacts"
    repository.mkdir()
    artifacts.mkdir()
    spec = artifacts / "resolved_specs_v1/document.json"
    spec.parent.mkdir()
    spec.write_text("{}\n")
    digest = hashlib.sha256(spec.read_bytes()).hexdigest()

    reference = reference_for_path(
        spec, repository_root=repository, artifact_root=artifacts, sha256=digest
    )

    assert reference.authority == "artifact_root"
    assert reference.resolve(repository_root=repository, artifact_root=artifacts) == spec


def test_authority_reference_rejects_cross_root_and_seal_drift(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    artifacts = tmp_path / "artifacts"
    repository.mkdir()
    artifacts.mkdir()
    payload = artifacts / "spec.json"
    payload.write_text("first\n")
    reference = AuthorityReference(
        authority="artifact_root",
        path="spec.json",
        sha256=hashlib.sha256(payload.read_bytes()).hexdigest(),
        byte_size=payload.stat().st_size,
    )
    payload.write_text("other\n")
    with pytest.raises(ValueError, match="SHA-256 differs"):
        reference.resolve(repository_root=repository, artifact_root=artifacts)

    outside = tmp_path / "outside.json"
    outside.write_text("{}\n")
    with pytest.raises(ValueError, match="outside declared authorities"):
        reference_for_path(
            outside,
            repository_root=repository,
            artifact_root=artifacts,
            sha256=hashlib.sha256(outside.read_bytes()).hexdigest(),
        )


def test_document_v4_requires_an_authority_aware_production_identity() -> None:
    root = Path(__file__).parents[1]
    value = json.loads(
        (root / "configs/brisbane_baylands_2025_deir_task03h_document_v3.json").read_text()
    )
    value["schema_version"] = "er_commons.document_run_spec.v4"
    value.pop("production_identity_relative_path")
    value["production_identity_ref"] = {
        "authority": "artifact_root",
        "path": "resolved_specs_v1/production_identity.json",
        "sha256": "a" * 64,
        "byte_size": 100,
    }

    spec = DocumentRunSpec.model_validate(value)

    assert spec.production_identity_ref is not None
    assert spec.production_identity_ref.authority == "artifact_root"
