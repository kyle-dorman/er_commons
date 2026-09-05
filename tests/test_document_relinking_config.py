"""Tests for strict, portable document relinking configuration."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from er_commons.document_records.document_references.relinking_config import (
    DocumentLinkRunSpec,
    RelinkArtifactRef,
    load_document_link_run_spec,
)

FIXTURES = Path(__file__).parents[1] / "benchmarks/er_bench/fixtures/document_linking/v1"


def _fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text())


def test_machine_and_reviewed_fixtures_load_with_closed_source_scopes(tmp_path: Path) -> None:
    for name in ("machine_only_run.json", "reviewed_navigation_run.json"):
        path = tmp_path / name
        path.write_text(json.dumps(_fixture(name)))
        spec, digest = load_document_link_run_spec(path)
        assert spec.document(spec.selected_source_ids[0]).source_id == spec.selected_source_ids[0]
        assert len(digest) == 64


def test_selected_sources_must_equal_unique_ordered_document_rows() -> None:
    value = _fixture("machine_only_run.json")
    value["selected_source_ids"] = ["different_source"]
    with pytest.raises(ValidationError, match="must equal unique ordered"):
        DocumentLinkRunSpec.model_validate(value)


def test_candidate_kinds_are_strict() -> None:
    wrong_candidate = _fixture("machine_only_run.json")
    wrong_candidate["documents"][0]["source_document"]["candidate_id"] = "exv1-" + "1" * 64
    with pytest.raises(ValidationError, match="candidate_id"):
        DocumentLinkRunSpec.model_validate(wrong_candidate)


def test_reviewed_payloads_are_bundle_relative_and_coverage_is_selected() -> None:
    wrong_authority = _fixture("reviewed_navigation_run.json")
    wrong_authority["reviewed_navigation"]["text_entries_ref"]["authority"] = "artifact_root"
    with pytest.raises(ValidationError, match="bundle"):
        DocumentLinkRunSpec.model_validate(wrong_authority)

    wrong_coverage = deepcopy(_fixture("reviewed_navigation_run.json"))
    wrong_coverage["reviewed_navigation"]["source_ids"] = ["unselected_report"]
    with pytest.raises(ValidationError, match="coverage escapes"):
        DocumentLinkRunSpec.model_validate(wrong_coverage)

    malformed_source = deepcopy(_fixture("reviewed_navigation_run.json"))
    malformed_source["reviewed_navigation"]["source_ids"] = ["Report Beta"]
    with pytest.raises(ValidationError, match="invalid source ID"):
        DocumentLinkRunSpec.model_validate(malformed_source)


def test_reference_resolution_obeys_authority_and_checks_seal(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    artifacts = tmp_path / "artifacts"
    repository.mkdir()
    artifacts.mkdir()
    payload = artifacts / "evidence.json"
    payload.write_text("evidence")
    import hashlib

    reference = RelinkArtifactRef(
        authority="artifact_root",
        path="evidence.json",
        sha256=hashlib.sha256(payload.read_bytes()).hexdigest(),
        byte_size=payload.stat().st_size,
    )
    assert reference.resolve(repository_root=repository, artifact_root=artifacts) == payload

    payload.write_text("changed")
    with pytest.raises(ValueError, match="seal differs"):
        reference.resolve(repository_root=repository, artifact_root=artifacts)
