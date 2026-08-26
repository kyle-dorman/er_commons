from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from task04_test_support import AcceptingCandidateVerifier, make_synthetic_review_tree

import er_commons.human_review_support.task04.verification as verification_module
from er_commons.document_publication.records import SourceIdentity
from er_commons.human_review_support.task04.config import review_policy
from er_commons.human_review_support.task04.discovery import discover_inputs
from er_commons.human_review_support.task04.records import create_identity
from er_commons.human_review_support.task04.scope_policy import InputScopePolicy
from er_commons.human_review_support.task04.verification import (
    CandidateSeal,
    DocumentPublicationVerifier,
    Sha256SourceFileVerifier,
)


class RejectingCandidateVerifier:
    def verify(self, candidate: Path, source: SourceIdentity) -> CandidateSeal:
        raise ValueError(f"candidate failed full publication verification: {candidate}")


FIXTURE_SCOPE = InputScopePolicy.synthetic_fixture(source_count=1)


def test_completion_record_alone_does_not_make_candidate_selectable(tmp_path: Path) -> None:
    tree = make_synthetic_review_tree(tmp_path)

    with pytest.raises(ValueError, match="failed full publication verification"):
        discover_inputs(
            tree.retained_root,
            tree.data_root,
            candidate_verifier=RejectingCandidateVerifier(),
            input_scope=FIXTURE_SCOPE,
        )


def test_existing_source_pdf_must_match_catalog_bytes(tmp_path: Path) -> None:
    tree = make_synthetic_review_tree(tmp_path)
    tree.source_pdf.write_bytes(b"corrupt source bytes")

    with pytest.raises(ValueError, match="source PDF checksum differs"):
        discover_inputs(
            tree.retained_root,
            tree.data_root,
            candidate_verifier=AcceptingCandidateVerifier(),
            input_scope=FIXTURE_SCOPE,
        )


@pytest.mark.parametrize(
    ("field", "wrong_value"),
    (("source_count", 2), ("page_count", 2), ("byte_count", 1)),
)
def test_readiness_scope_must_exactly_match_discovered_catalog(
    tmp_path: Path, field: str, wrong_value: int
) -> None:
    tree = make_synthetic_review_tree(tmp_path)
    readiness = tree.retained_root / "inputs/task03h_preparation_readiness.json"
    record = json.loads(readiness.read_text())
    record["source_scope"][field] = wrong_value
    readiness.write_text(json.dumps(record) + "\n")

    suffix = (
        rf"required=1, readiness={wrong_value}"
        if field == "source_count"
        else rf"readiness={wrong_value}, discovered_catalog="
    )
    with pytest.raises(
        ValueError,
        match=rf"task03h_preparation_readiness\.json:\$\.source_scope\.{field}.*{suffix}",
    ):
        discover_inputs(
            tree.retained_root,
            tree.data_root,
            candidate_verifier=AcceptingCandidateVerifier(),
            input_scope=FIXTURE_SCOPE,
        )


def test_candidate_seal_and_renderer_version_change_review_identity(tmp_path: Path) -> None:
    tree = make_synthetic_review_tree(tmp_path)
    first_inputs = discover_inputs(
        tree.retained_root,
        tree.data_root,
        candidate_verifier=AcceptingCandidateVerifier(completion="a" * 64),
        input_scope=FIXTURE_SCOPE,
    )
    second_inputs = discover_inputs(
        tree.retained_root,
        tree.data_root,
        candidate_verifier=AcceptingCandidateVerifier(completion="d" * 64),
        input_scope=FIXTURE_SCOPE,
    )
    schema_root = Path(__file__).parents[1] / "benchmarks/er_bench/schemas/task04_review/v1"
    implementation_root = Path(verification_module.__file__).parent

    first = create_identity(
        first_inputs,
        review_policy(),
        implementation_root,
        schema_root,
        "renderer",
        "1.0",
        1.0,
    )
    changed_seal = create_identity(
        second_inputs,
        review_policy(),
        implementation_root,
        schema_root,
        "renderer",
        "1.0",
        1.0,
    )
    changed_renderer = create_identity(
        first_inputs,
        review_policy(),
        implementation_root,
        schema_root,
        "renderer",
        "2.0",
        1.0,
    )

    assert (
        len({first.review_run_id, changed_seal.review_run_id, changed_renderer.review_run_id}) == 3
    )
    changed_dependency = replace(first.dependencies[0], sha256="f" * 64)
    dependency_identity = create_identity(
        first_inputs,
        review_policy(),
        implementation_root,
        schema_root,
        "renderer",
        "1.0",
        1.0,
        dependencies=(changed_dependency, *first.dependencies[1:]),
    )
    assert dependency_identity.review_run_id != first.review_run_id


def test_publication_adapter_passes_catalog_identity_to_owner_verifier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate = tmp_path / f"docv1-{'a' * 64}"
    records = candidate / "records"
    records.mkdir(parents=True)
    completion = records / "completion_record.json"
    inventory = records / "artifact_inventory.json"
    completion.write_text("{}\n")
    inventory.write_text("{}\n")
    expected = SourceIdentity(source_id="source", sha256="b" * 64, pdf_page_count=4)
    received: list[SourceIdentity] = []

    def owner_verifier(path: Path, candidate_id: str, source: SourceIdentity) -> Path:
        assert path == candidate
        assert candidate_id == candidate.name
        received.append(source)
        return completion

    monkeypatch.setattr(verification_module, "verify_candidate", owner_verifier)

    seal = DocumentPublicationVerifier().verify(candidate, expected)

    assert received == [expected]
    assert len(seal.completion_sha256) == 64
    assert len(seal.inventory_sha256) == 64


def test_source_file_verifier_returns_verified_digest(tmp_path: Path) -> None:
    path = tmp_path / "source.pdf"
    path.write_bytes(b"source")
    expected = hashlib.sha256(b"source").hexdigest()

    assert Sha256SourceFileVerifier().verify(path, expected) == expected
