"""Source-free relink contract preparation over real tiny synthetic publications."""

from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
from test_relink_spec_preparation import _spec
from test_reviewed_navigation_materialization import _reference, _request
from test_task06b_publication_reuse import ROOT, _current_recipe, _sealed_fixture, _sentinels

from er_commons.artifact_io import write_json_atomic
from er_commons.artifact_verification import VerificationBudget
from er_commons.collection_processing.config import load_collection_run_spec
from er_commons.document_publication.config import load_document_run_spec
from er_commons.document_publication.identity import canonical_digest
from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.document_records.document_references.preparation_spec import RelinkPreparationSpec
from er_commons.document_records.document_references.relinking_config import (
    load_document_link_run_spec,
)
from er_commons.document_records.document_references.reviewed_navigation import (
    materialize_reviewed_navigation,
)
from er_commons.document_records.document_references.spec_preparation import (
    build_specs,
    prepare_specs,
)


def test_complete_v3_preparation_reloads_and_retries_without_payload_access(tmp_path, monkeypatch):
    """All four real contracts validate, preserve source bindings, and refuse clobber."""
    data, document_path, _, structured, completion, catalog = _sealed_fixture(tmp_path)
    _current_recipe(document_path, tmp_path)
    document = json.loads(document_path.read_text())
    document["schema_version"] = "er_commons.document_run_spec.v3"
    document["document_processes"] = document["document_processes"][:1]
    document["hierarchy_dispositions"] = document["hierarchy_dispositions"][:1]
    selected = document["document_processes"][0]
    selected.update(
        source_release_version=document["source_release_version"],
        source_manifest_relative_path=document["source_manifest_relative_path"],
    )
    write_json_atomic(document_path, document)
    base_identity_path = tmp_path / document["production_identity_relative_path"]
    base = json.loads(base_identity_path.read_text())
    base["preimage"]["production_scope"]["ordered_source_ids"] = ["alpha"]
    base["identity_sha256"] = canonical_digest(base["preimage"])
    base["extraction_id"] = "exv1-" + base["identity_sha256"]
    write_json_atomic(base_identity_path, base)
    document["production_extraction_id"] = base["extraction_id"]
    write_json_atomic(document_path, document)

    navigation = _request(data)
    changes = {"source_ids": ("alpha",)}
    for field in (
        "review_decisions_ref",
        "semantic_view_ref",
        "text_entries_ref",
        "dispositions_ref",
        "parent_relations_ref",
    ):
        path = data / getattr(navigation, field)["path"]
        path.write_text(path.read_text().replace("report_alpha", "alpha"))
        changes[field] = _reference(path, data)
    reviewed = materialize_reviewed_navigation(replace(navigation, **changes))

    for relative in (
        "document_publication/v2",
        "document_publication/v3",
        "collection_processing/v3",
        "document_linking/v1",
    ):
        shutil.copytree(
            ROOT / "benchmarks/er_bench/schemas" / relative, tmp_path / "schemas" / relative
        )
    shutil.copyfile(
        ROOT / "configs/linking_policies/document_linking_v1.json", tmp_path / "linking_policy.json"
    )
    shutil.copyfile(catalog, data / "catalog.json")
    write_json_atomic(data / "scope/contract_bundle.json", {"scope_id": "synthetic-scope"})
    write_json_atomic(
        data / "handoff/records/completion_record.json",
        {"status": "complete", "completion_last": True},
    )
    collection = {
        "schema_version": "er_commons.collection_run_spec.v3",
        "document_run_spec": document_path.name,
        "source_ids": ["alpha"],
        "source_membership": [
            {
                "logical_source_id": "deir_appendix_f1",
                "physical_source_id": "alpha",
                "substitution_relative_path": "substitution.json",
            }
        ],
        "source_family_catalog_relative_path": "catalog.json",
        "blocking_policy": "all_sources_successful",
        "target_policy_sha256": "a" * 64,
        "resolution_policy_sha256": "b" * 64,
    }
    write_json_atomic(tmp_path / "base_collection.json", collection)
    spec = RelinkPreparationSpec.model_validate(
        {
            **_spec(tmp_path).model_dump(),
            "base_identity": base_identity_path.relative_to(tmp_path),
            "base_document_spec": document_path.relative_to(tmp_path),
            "base_collection_spec": "base_collection.json",
            "reviewed_descriptor": reviewed.descriptor_path,
            "collection_schema": "schemas/collection_processing/v3/collection_run_spec.schema.json",
            "document_schema": "schemas/document_publication/v3/document_run_spec.schema.json",
            "production_identity_schema": (
                "schemas/document_publication/v2/production_identity.schema.json"
            ),
            "link_schema_root": "schemas/document_linking/v1",
            "document_roots": {"alpha": completion.parents[1].relative_to(data)},
            "source_catalog": "catalog.json",
            "scope_root": "scope",
            "handoff_root": "handoff",
            "document_artifacts": ["writer_config.json"],
            "document_owned_code": ["writer.py"],
            "collection_artifacts": ["writer_config.json"],
            "collection_owned_code": ["writer.py"],
        }
    )
    _sentinels(monkeypatch, (completion.parents[1], structured))
    from er_commons import artifact_verification

    original_hash = artifact_verification.sha256_file

    def guarded_hash(path):
        if (
            path.suffix == ".pdf"
            or "canonical" in path.parts
            or path.name == "preserved_payload.json"
        ):
            raise AssertionError(f"preserved payload hashing: {path}")
        return original_hash(path)

    monkeypatch.setattr(artifact_verification, "sha256_file", guarded_hash)
    budget = VerificationBudget()
    proposed = build_specs(spec, budget=budget)
    assert len(proposed) == 4
    assert not any(path.exists() for path in proposed)
    prepare_specs(spec, budget=budget)
    outputs = [
        tmp_path / getattr(spec, field)
        for field in ("production_identity", "document_spec", "collection_spec", "link_spec")
    ]
    original = {path: path.read_bytes() for path in outputs}
    identity = validate_production_identity(
        json.loads(outputs[0].read_text()), project_root=tmp_path
    )
    parsed_document, _ = load_document_run_spec(outputs[1])
    parsed_collection, _ = load_collection_run_spec(outputs[2])
    parsed_link, _ = load_document_link_run_spec(outputs[3])
    assert parsed_document.production_extraction_id == identity.value
    assert parsed_document.document_processes[0].source_manifest_relative_path == Path(
        document["source_manifest_relative_path"]
    )
    assert parsed_collection.source_membership[0].logical_source_id == "deir_appendix_f1"
    assert parsed_link.selected_source_ids == ("alpha",)
    assert parsed_link.documents[0].source_document.candidate_id == completion.parents[1].name

    prepare_specs(spec)
    assert all(path.read_bytes() == value for path, value in original.items())
    outputs[1].write_text("corrupted future contract")
    with pytest.raises(FileExistsError, match="refusing to replace existing contract"):
        prepare_specs(spec)
    assert outputs[1].read_text() == "corrupted future contract"
