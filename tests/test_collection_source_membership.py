"""Replacement membership preserves 34 original releases without PDF access."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from collection_processing_test_support import write_collection_spec
from document_publication_test_support import _source_record, _workspace

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.artifact_verification import VerificationBudget
from er_commons.collection_processing.preflight import prepare_collection_run
from er_commons.document_publication.sources import manifest_selection_for


def _replacement_workspace(tmp_path: Path) -> tuple[Path, Path]:
    """Expand the ordinary fixture to the original 35 slots and one distinct F1."""
    data_root, document_path = _workspace(tmp_path)
    collection_path = write_collection_spec(tmp_path, data_root)
    logical = ["alpha", "beta", *[f"unchanged_{n}" for n in range(32)], "deir_appendix_f1"]
    manifest_path = data_root / "release/records/source_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["sources"].extend(_source_record(data_root, name) for name in logical[2:])
    write_json_atomic(manifest_path, manifest)
    completion = json.loads((manifest_path.parent / "completion_record.json").read_text())
    completion["manifest"].update(
        sha256=sha256_file(manifest_path), byte_size=manifest_path.stat().st_size
    )
    write_json_atomic(manifest_path.parent / "completion_record.json", completion)
    replacement = _source_record(data_root, "final_appendix_f1")
    replacement_manifest = copy.deepcopy(manifest)
    replacement_manifest.update(source_release_version="final_release", sources=[replacement])
    replacement_path = data_root / "final_release/records/source_manifest.json"
    write_json_atomic(replacement_path, replacement_manifest)
    replacement_completion = copy.deepcopy(completion)
    replacement_completion.update(
        source_release_version="final_release",
        manifest={
            "local_path": replacement_path.relative_to(data_root).as_posix(),
            "sha256": sha256_file(replacement_path),
            "byte_size": replacement_path.stat().st_size,
        },
    )
    write_json_atomic(replacement_path.parent / "completion_record.json", replacement_completion)
    write_json_atomic(
        data_root / "substitution.json",
        {
            "schema_version": "er_commons.recovery.source_substitution.v1",
            "logical_source_id": "deir_appendix_f1",
            "edition": "final_eir",
            "scope_exception": "f1_only",
            "edition_equivalence": "not_established",
            "replacement_source_ref": {"identity": replacement["sha256"]},
            "original_release_ref": {"recorded_digest": sha256_file(manifest_path)},
            "wrong_source_ref": {"identity": manifest["sources"][-1]["sha256"]},
        },
    )
    physical = [*logical[:-1], replacement["source_id"]]
    document = json.loads(document_path.read_text())
    template = document["document_processes"][0]
    document.update(
        schema_version="er_commons.document_run_spec.v3",
        scope_kind="production_full",
        document_processes=[{**template, "source_id": name} for name in physical],
        hierarchy_dispositions=[
            {"source_id": name, "authority": "machine_validation"} for name in physical
        ],
    )
    document["document_processes"][-1].update(
        source_release_version="final_release",
        source_manifest_relative_path=replacement_path.relative_to(data_root).as_posix(),
    )
    write_json_atomic(document_path, document)
    collection = json.loads(collection_path.read_text())
    collection.update(
        schema_version="er_commons.collection_run_spec.v3",
        source_ids=physical,
        source_membership=[
            {
                "logical_source_id": old,
                "physical_source_id": new,
                **({"substitution_relative_path": "substitution.json"} if old != new else {}),
            }
            for old, new in zip(logical, physical, strict=True)
        ],
    )
    write_json_atomic(collection_path, collection)
    catalog_path = data_root / "catalog.json"
    catalog = json.loads(catalog_path.read_text())
    original = {row["source_id"]: row for row in manifest["sources"]}
    original[replacement["source_id"]] = replacement
    catalog["sources"] = [
        {
            "source": {
                key: original[name][key]
                for key in ("source_id", "sha256", "byte_size", "pdf_page_count")
            },
            "family_root_source_id": "alpha",
            "document_role": "root_report" if name == "alpha" else "top_level_appendix",
            "parent_source_id": None if name == "alpha" else "alpha",
            "reference_aliases": [f"report {name}"],
        }
        for name in physical
    ]
    write_json_atomic(catalog_path, catalog)
    return data_root, collection_path


def test_35_slot_replacement_preserves_original_manifest_bindings(tmp_path, monkeypatch):
    """Exactly one replacement selection changes; no source bytes are read."""
    data_root, path = _replacement_workspace(tmp_path)
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        if path.suffix == ".pdf":
            raise AssertionError("source PDF access")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    budget = VerificationBudget()
    run = prepare_collection_run(data_root, path, budget=budget)
    selections = [
        manifest_selection_for(run.document_spec, source)
        for source in run.collection_spec.source_ids
    ]
    assert len(selections) == 35
    assert all(selection.source_release_version == "release" for selection in selections[:-1])
    assert selections[-1].source_release_version == "final_release"
    manifest_hashes = [
        row
        for row in budget.observations
        if row["role"] == "source_manifest" and row["verification_mode"] == "bytes_verified"
    ]
    assert len(manifest_hashes) == 2


@pytest.mark.parametrize(
    "mutation",
    ["unchanged_manifest", "missing_slot", "wrong_replacement", "wrong_order", "wrong_original"],
)
def test_mixed_membership_rejects_changed_original_binding(tmp_path, mutation):
    """Replacement composition never silently rebuilds unrelated source identities."""
    data_root, path = _replacement_workspace(tmp_path)
    document_path = tmp_path / "run_spec.json"
    if mutation == "unchanged_manifest":
        document = json.loads(document_path.read_text())
        document["document_processes"][0].update(
            source_release_version="final_release",
            source_manifest_relative_path="final_release/records/source_manifest.json",
        )
        write_json_atomic(document_path, document)
    elif mutation == "missing_slot":
        collection = json.loads(path.read_text())
        collection["source_membership"].pop()
        write_json_atomic(path, collection)
    elif mutation == "wrong_order":
        collection = json.loads(path.read_text())
        for key in ("source_ids", "source_membership"):
            collection[key][0], collection[key][1] = collection[key][1], collection[key][0]
        write_json_atomic(path, collection)
    else:
        substitution_path = data_root / "substitution.json"
        substitution = json.loads(substitution_path.read_text())
        if mutation == "wrong_original":
            substitution["original_release_ref"]["recorded_digest"] = "f" * 64
        else:
            substitution["replacement_source_ref"]["identity"] = "f" * 64
        write_json_atomic(substitution_path, substitution)
    with pytest.raises(ValueError):
        prepare_collection_run(data_root, path)


def test_historical_v2_round_trip_keeps_closed_schema(tmp_path: Path) -> None:
    """Absent v3 extensions cannot leak into serialized historical v2 specs."""
    from jsonschema import Draft202012Validator

    from er_commons.collection_processing.config import load_collection_run_spec
    from er_commons.document_publication.config import load_document_run_spec

    data_root, document_path = _workspace(tmp_path)
    collection_path = write_collection_spec(tmp_path, data_root)
    root = Path(__file__).parents[1]
    for path, loader, owner, filename in (
        (document_path, load_document_run_spec, "document_publication", "document_run_spec"),
        (collection_path, load_collection_run_spec, "collection_processing", "collection_run_spec"),
    ):
        model, _ = loader(path)
        schema = json.loads(
            (root / f"benchmarks/er_bench/schemas/{owner}/v2/{filename}.schema.json").read_text()
        )
        Draft202012Validator(schema).validate(model.model_dump(mode="json"))
