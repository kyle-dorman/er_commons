"""Explicit future recipes preserve historical source bindings and isolate outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.artifact_verification import VerificationBudget
from er_commons.document_records.document_references.preparation_spec import RelinkPreparationSpec
from er_commons.document_records.document_references.spec_preparation import (
    _document_spec,
    _production_identity,
)


def _spec(tmp_path: Path) -> RelinkPreparationSpec:
    """Build a one-source recipe whose historical filenames are irrelevant."""
    paths = {
        name: Path(name + ".json")
        for name in (
            "base_identity",
            "base_document_spec",
            "base_collection_spec",
            "production_identity",
            "document_spec",
            "link_spec",
            "collection_spec",
            "source_catalog",
            "linking_policy",
        )
    }
    return RelinkPreparationSpec(
        repo_root=tmp_path,
        data_root=tmp_path / "data",
        reviewed_descriptor=tmp_path / "navigation.json",
        **paths,
        collection_schema=Path("collection-schema.json"),
        document_schema=Path("document-schema.json"),
        production_identity_schema=Path("identity-schema.json"),
        link_schema_root=Path("schemas"),
        document_artifact_root=Path("next/documents"),
        link_artifact_root=Path("next/links"),
        document_roots={"source": Path("accepted/arbitrary-name")},
        scope_root=Path("accepted/scope"),
        handoff_root=Path("accepted/handoff"),
        contract_revision="relink-v2",
        extraction_version_name="replacement",
        document_contract_version="document-v2",
        collection_contract_version="collection-v2",
        document_artifacts=[Path("contract.json")],
        document_owned_code=[Path("behavior.py")],
        collection_artifacts=[Path("contract.json")],
        collection_owned_code=[Path("behavior.py")],
    )


def test_future_recipe_preserves_per_source_manifest_bindings(tmp_path: Path) -> None:
    spec = _spec(tmp_path)
    original = {
        "document_processes": [
            {"source_id": "source", "source_manifest_relative_path": "original/manifest.json"}
        ],
        "production_extraction_id": "historical",
    }
    (tmp_path / spec.base_document_spec).write_text(json.dumps(original))
    result = _document_spec(
        tmp_path, {"extraction_id": "future"}, spec=spec, budget=VerificationBudget()
    )
    assert result["document_processes"] == original["document_processes"]
    assert result["production_extraction_id"] == "future"
    assert result["artifact_relative_root"] == "next/documents"
    assert json.loads((tmp_path / spec.base_document_spec).read_text()) == original


def test_current_identity_uses_explicit_inventory_without_old_code_access(tmp_path: Path) -> None:
    spec = _spec(tmp_path)
    (tmp_path / "behavior.py").write_text("BEHAVIOR = 1\n")
    (tmp_path / "contract.json").write_text("{}\n")
    base = {
        "preimage": {
            "production_scope": {"ordered_source_ids": ["source"]},
            "collection_process_contract": {"owned_code": [{"path": "removed_historical.py"}]},
        }
    }
    result = _production_identity(
        tmp_path, base, {"source_ids": ["source"]}, spec=spec, budget=VerificationBudget()
    )
    assert result["preimage"]["production_scope"] == base["preimage"]["production_scope"]
    assert (
        result["preimage"]["collection_process_contract"]["owned_code"][0]["path"] == "behavior.py"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("document_spec", Path("base_document_spec.json")),
        ("link_spec", Path("../escape.json")),
        ("document_roots", {}),
    ],
)
def test_preparation_rejects_implicit_or_destructive_references(
    tmp_path: Path, field: str, value: object
) -> None:
    raw = _spec(tmp_path).model_dump()
    raw[field] = value
    with pytest.raises(ValueError):
        RelinkPreparationSpec.model_validate(raw)


def test_v3_membership_and_original_manifests_survive_preparation(tmp_path: Path) -> None:
    from er_commons.document_records.document_references.spec_preparation import _collection_spec

    spec = _spec(tmp_path)
    collection = {
        "schema_version": "er_commons.collection_run_spec.v3",
        "source_ids": ["unchanged", "replacement"],
        "source_membership": [
            {"logical_source_id": "unchanged", "physical_source_id": "unchanged"},
            {
                "logical_source_id": "deir_appendix_f1",
                "physical_source_id": "replacement",
                "substitution_relative_path": "accepted/substitution.json",
            },
        ],
    }
    (tmp_path / spec.base_collection_spec).write_text(json.dumps(collection))
    result = _collection_spec(tmp_path, spec=spec, budget=VerificationBudget())
    assert result["schema_version"] == collection["schema_version"]
    assert result["source_ids"] == collection["source_ids"]
    assert result["source_membership"] == collection["source_membership"]


def test_stale_base_recipe_rejected_before_any_output(tmp_path: Path) -> None:
    from er_commons.document_records.document_references.spec_preparation import prepare_specs

    spec = _spec(tmp_path)
    (tmp_path / spec.base_identity).write_text(
        json.dumps({"record_type": "production_identity", "preimage": {"scope": "tampered"}})
    )
    with pytest.raises(ValueError):
        prepare_specs(spec)
    assert not (tmp_path / spec.production_identity).exists()


def test_preparation_compact_hashes_share_one_limit(tmp_path: Path) -> None:
    from er_commons.document_records.document_references.spec_preparation import _artifact_ref

    first, second = tmp_path / "completion.json", tmp_path / "inventory.json"
    first.write_bytes(b"123456")
    second.write_bytes(b"123456")
    budget = VerificationBudget(hash_total_limit=10)
    _artifact_ref(tmp_path, first, budget=budget)
    with pytest.raises(ValueError, match="compact hash budget exceeded before open"):
        _artifact_ref(tmp_path, second, budget=budget)
    assert budget.hashed_bytes == 6


def test_preparation_rejects_oversized_accepted_inventory_before_hash(tmp_path: Path) -> None:
    from er_commons.document_records.document_references.spec_preparation import _artifact_ref

    inventory = tmp_path / "inventory.json"
    inventory.write_bytes(b"x" * 101)
    budget = VerificationBudget(hash_file_limit=100)
    with pytest.raises(ValueError, match="compact hash budget exceeded before open"):
        _artifact_ref(tmp_path, inventory, budget=budget)
    assert budget.hashed_bytes == 0


def test_spec_writer_rejects_concurrent_same_size_contract(tmp_path: Path) -> None:
    from er_commons.document_records.document_references.spec_preparation import _write_json

    output = tmp_path / "new.json"
    _write_json(output, {"status": "a"})
    accepted = output.read_bytes()
    with pytest.raises(FileExistsError):
        _write_json(output, {"status": "b"})
    assert output.read_bytes() == accepted
