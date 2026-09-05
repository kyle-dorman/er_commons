"""Prepare Task 04D's sealed production identity and 35-source link run.

This command is source-free. It reads only checked-in contracts and sealed
Task 03J/04D records, then writes reviewable JSON specifications in the
repository. It never invokes extraction, linking, or publication.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.artifact_io import atomic_text_writer, sha256_bytes, sha256_file
from er_commons.collection_processing.config import CollectionRunSpec
from er_commons.document_publication.identity import canonical_digest
from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.document_records.document_references.relinking_config import (
    OUTPUT_SCHEMA_ROLES,
    DocumentLinkRunSpec,
)

JsonObject = dict[str, Any]
BASE_IDENTITY = Path(
    "benchmarks/er_bench/fixtures/document_publication/v4/task03h_production_identity.json"
)
BASE_DOCUMENT_SPEC = Path("configs/brisbane_baylands_2025_deir_task03h_document_v4.json")
BASE_COLLECTION_SPEC = Path("configs/brisbane_baylands_2025_deir_task03h_collection_v4.json")
REPLAY_AUTHORIZATION = Path("configs/brisbane_baylands_2025_deir_task04d_downstream_replay_v1.json")
PRODUCTION_IDENTITY = Path(
    "benchmarks/er_bench/fixtures/document_publication/v5/task04d_production_identity.json"
)
DOCUMENT_SPEC = Path("configs/brisbane_baylands_2025_deir_task04d_document_v1.json")
LINK_SPEC = Path("configs/brisbane_baylands_2025_deir_task04d_link_v1.json")
COLLECTION_SPEC = Path("configs/brisbane_baylands_2025_deir_task04d_collection_v1.json")
LINK_SCHEMA_ROOT = Path("benchmarks/er_bench/schemas/document_linking/v1")
SOURCE_CATALOG = Path(
    "pipelines/brisbane_baylands/task_03h_clean_full_v4/inputs/"
    "brisbane_baylands_2025_deir_task03h_v4_source_family_catalog_v1.json"
)


def main() -> None:
    """Build and validate the three identity-bearing Gate C specifications."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--reviewed-navigation-bundle", type=Path, required=True)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    prepare_specs(
        repo_root=repo_root,
        data_root=args.data_root.resolve(),
        reviewed_descriptor=args.reviewed_navigation_bundle.resolve(),
    )


def prepare_specs(*, repo_root: Path, data_root: Path, reviewed_descriptor: Path) -> None:
    """Build and validate all specs before replacing any checked-in file."""
    base_identity = _read_object(repo_root / BASE_IDENTITY)
    collection_spec = _collection_spec(repo_root)
    CollectionRunSpec.model_validate(collection_spec)
    _validate_schema(
        collection_spec,
        repo_root
        / "benchmarks/er_bench/schemas/collection_processing/v2/collection_run_spec.schema.json",
    )
    production_identity = _production_identity(repo_root, base_identity, collection_spec)
    validate_production_identity(production_identity)
    _validate_schema(
        production_identity,
        repo_root
        / "benchmarks/er_bench/schemas/document_publication/v2/production_identity.schema.json",
    )

    document_spec = _document_spec(repo_root, production_identity)
    _validate_schema(
        document_spec,
        repo_root
        / "benchmarks/er_bench/schemas/document_publication/v2/document_run_spec.schema.json",
    )

    link_spec = _link_spec(
        repo_root=repo_root,
        data_root=data_root,
        production_identity=production_identity,
        document_spec=document_spec,
        collection_spec=collection_spec,
        reviewed_descriptor=reviewed_descriptor,
    )
    DocumentLinkRunSpec.model_validate(link_spec)
    _validate_schema(link_spec, repo_root / LINK_SCHEMA_ROOT / "document_link_run.schema.json")

    # Keep preparation reviewable: invalid downstream input leaves all three
    # checked-in identity-bearing specifications untouched.
    _write_json(repo_root / COLLECTION_SPEC, collection_spec)
    _write_json(repo_root / PRODUCTION_IDENTITY, production_identity)
    _write_json(repo_root / DOCUMENT_SPEC, document_spec)
    _write_json(repo_root / LINK_SPEC, link_spec)
    validate_production_identity(production_identity, project_root=repo_root)


def _production_identity(
    repo_root: Path, base: JsonObject, collection_spec: JsonObject
) -> JsonObject:
    base_preimage = _object(base, "preimage")
    base_collection = _object(base_preimage, "collection_process_contract")
    link_artifacts = [
        *sorted(LINK_SCHEMA_ROOT.glob("*.json")),
        Path("configs/linking_policies/document_linking_v1.json"),
        REPLAY_AUTHORIZATION,
        Path("benchmarks/er_bench/schemas/document_publication/v2/document_run_spec.schema.json"),
        Path("benchmarks/er_bench/schemas/document_publication/v2/production_identity.schema.json"),
        BASE_IDENTITY,
    ]
    owned_code = [
        Path("src/er_commons/artifact_io.py"),
        Path("src/er_commons/cli.py"),
        Path("src/er_commons/source_family_catalog.py"),
        *sorted(Path("src/er_commons/document_records/document_references").glob("*.py")),
        Path("src/er_commons/navigation_overlay/link_resolution.py"),
        Path("src/er_commons/document_publication/downstream_replay.py"),
        Path("src/er_commons/document_publication/downstream_replay_validation.py"),
        Path("src/er_commons/document_publication/identity.py"),
        Path("src/er_commons/document_publication/production_identity.py"),
        Path("src/er_commons/document_publication/records.py"),
    ]
    collection_artifacts = [
        Path(str(item["path"]))
        for item in _list_of_objects(base_collection, "artifacts")
        if Path(str(item["path"])) != BASE_COLLECTION_SPEC
    ]
    if REPLAY_AUTHORIZATION not in collection_artifacts:
        collection_artifacts.append(REPLAY_AUTHORIZATION)
    collection_code = [
        Path(str(item["path"])) for item in _list_of_objects(base_collection, "owned_code")
    ]
    preimage: JsonObject = {
        "schema_version": "er_commons.document_publication_identity_preimage.v2",
        "contract_revision": "task_04d_relink_downstream_replay_v1",
        "extraction_version_name": "brisbane_baylands_2025_deir_task04d_relinked_v1",
        "production_scope": deepcopy(_object(base_preimage, "production_scope")),
        "document_process_contract": {
            "version": "task04d-document-linking-v1",
            "artifacts": [_repo_ref(repo_root, path) for path in sorted(set(link_artifacts))],
            "owned_code": [_repo_ref(repo_root, path) for path in sorted(set(owned_code))],
        },
        "collection_process_contract": {
            "version": "task04d-collection-downstream-replay-v1",
            "artifacts": [
                *[_repo_ref(repo_root, path) for path in sorted(set(collection_artifacts))],
                _generated_ref(COLLECTION_SPEC, collection_spec),
            ],
            "owned_code": [_repo_ref(repo_root, path) for path in sorted(set(collection_code))],
        },
    }
    # The actual link-run spec references this recipe, so placing that spec's
    # digest in this preimage would create an impossible checksum cycle. The
    # production identity binds the run-spec schema and implementation; each
    # linked-document identity separately binds the actual run-spec digest.
    digest = canonical_digest(preimage)
    return {
        "record_type": "production_identity",
        "schema_version": "er_commons.document_publication_identity.v2",
        "fixture_status": "identity_recipe",
        "execution_status": "not_executed",
        "extraction_id": f"exv1-{digest}",
        "identity_sha256": digest,
        "preimage": preimage,
    }


def _document_spec(repo_root: Path, production_identity: JsonObject) -> JsonObject:
    spec = _read_object(repo_root / BASE_DOCUMENT_SPEC)
    spec["production_extraction_id"] = production_identity["extraction_id"]
    spec["production_identity_relative_path"] = PRODUCTION_IDENTITY.as_posix()
    spec["artifact_relative_root"] = (
        "pipelines/brisbane_baylands/task_04d_relinked_v1/document_publications"
    )
    return spec


def _collection_spec(repo_root: Path) -> JsonObject:
    """Select the replacement document lineage without allowing document attempts."""
    spec = _read_object(repo_root / BASE_COLLECTION_SPEC)
    spec["document_run_spec"] = DOCUMENT_SPEC.name
    spec["document_evidence_mode"] = "downstream_replay_only"
    return spec


def _link_spec(
    *,
    repo_root: Path,
    data_root: Path,
    production_identity: JsonObject,
    document_spec: JsonObject,
    collection_spec: JsonObject,
    reviewed_descriptor: Path,
) -> JsonObject:
    base_identity = _read_object(repo_root / BASE_IDENTITY)
    source_ids = list(
        _object(_object(base_identity, "preimage"), "production_scope")["ordered_source_ids"]
    )
    publication_root = (
        data_root
        / "pipelines/brisbane_baylands/task_03h_clean_full_v4/document_publications/documents"
    )
    documents = [
        _document_selection(data_root, publication_root, str(source_id)) for source_id in source_ids
    ]
    scope_root = _sole_directory(
        data_root
        / "pipelines/brisbane_baylands/task_03h_clean_full_v4/document_publications/scopes"
    )
    handoff_root = _sole_directory(scope_root / "handoffs")
    descriptor = _read_object(reviewed_descriptor)
    reviewed_root = data_root / Path(str(_object(descriptor, "completion_ref")["path"])).parents[1]
    output_names = {role: f"{role}.schema.json" for role in OUTPUT_SCHEMA_ROLES}
    payloads = _object(descriptor, "payloads")
    return {
        "schema_version": "er_commons.document_link_run_spec.v1",
        "artifact_relative_root": "pipelines/brisbane_baylands/task_04d_relinked_v1/document_links",
        "base_collection": {
            "handoff_ref": _artifact_ref(
                data_root, handoff_root / "records/completion_record.json"
            ),
            "contract_bundle_ref": _artifact_ref(data_root, scope_root / "contract_bundle.json"),
        },
        "base_production_identity_ref": _external_repo_ref(repo_root, BASE_IDENTITY),
        "replacement_production_identity_recipe_ref": _generated_repo_ref(
            PRODUCTION_IDENTITY, production_identity
        ),
        "document_publication_spec_ref": _generated_repo_ref(DOCUMENT_SPEC, document_spec),
        "collection_run_spec_ref": _generated_repo_ref(COLLECTION_SPEC, collection_spec),
        "linking_policy_ref": _external_repo_ref(
            repo_root, Path("configs/linking_policies/document_linking_v1.json")
        ),
        "linking_policy_schema_ref": _external_repo_ref(
            repo_root, LINK_SCHEMA_ROOT / "linking_policy.schema.json"
        ),
        "source_family_catalog_ref": _artifact_ref(
            data_root,
            data_root / SOURCE_CATALOG,
        ),
        "selected_source_ids": source_ids,
        "documents": documents,
        "reviewed_navigation": {
            "bundle_id": descriptor["bundle_id"],
            "bundle_ref": _artifact_ref(data_root, reviewed_descriptor),
            "schema_ref": _external_repo_ref(
                repo_root, LINK_SCHEMA_ROOT / "reviewed_navigation_bundle.schema.json"
            ),
            "source_ids": descriptor["source_ids"],
            "identity_ref": _artifact_ref(
                data_root, reviewed_root / "records/identity_preimage.json"
            ),
            "completion_ref": descriptor["completion_ref"],
            "inventory_ref": descriptor["inventory_ref"],
            "review_decisions_ref": _object(descriptor, "identity_preimage")[
                "review_decisions_ref"
            ],
            "semantic_view_ref": _object(descriptor, "identity_preimage")["semantic_view_ref"],
            "disposition_ref": payloads["dispositions_ref"],
            "text_entries_ref": payloads["text_entries_ref"],
            "parent_relations_ref": payloads["parent_relations_ref"],
        },
        "output_schema_refs": {
            role: _external_repo_ref(repo_root, LINK_SCHEMA_ROOT / filename)
            for role, filename in output_names.items()
        },
    }


def _document_selection(data_root: Path, root: Path, source_id: str) -> JsonObject:
    document_root = _sole_directory(root / source_id)
    identity = _read_object(document_root / "records/document_identity.json")
    structured = _object(_object(identity, "stage_completions"), "structured_document")
    structured_completion = data_root / str(structured["path"])
    structured_root = structured_completion.parents[1]
    return {
        "source_id": source_id,
        "source_document": {
            "candidate_id": document_root.name,
            "completion_ref": _artifact_ref(
                data_root, document_root / "records/completion_record.json"
            ),
            "inventory_ref": _artifact_ref(
                data_root, document_root / "records/artifact_inventory.json"
            ),
        },
        "structured_document": {
            "candidate_id": structured_root.name,
            "completion_ref": _artifact_ref(data_root, structured_completion),
            "inventory_ref": _artifact_ref(
                data_root, structured_root / "records/artifact_inventory.json"
            ),
        },
    }


def _repo_ref(repo_root: Path, relative: Path) -> JsonObject:
    path = repo_root / relative
    return {
        "path": relative.as_posix(),
        "sha256": sha256_file(path),
        "byte_size": path.stat().st_size,
    }


def _external_repo_ref(repo_root: Path, relative: Path) -> JsonObject:
    return {"authority": "repository", **_repo_ref(repo_root, relative)}


def _generated_repo_ref(relative: Path, value: JsonObject) -> JsonObject:
    """Seal a generated file from the exact bytes that will be written later."""
    content = _encoded_json(value)
    return {
        "authority": "repository",
        "path": relative.as_posix(),
        "sha256": sha256_bytes(content),
        "byte_size": len(content),
    }


def _generated_ref(relative: Path, value: JsonObject) -> JsonObject:
    """Seal generated repository bytes where the owning schema omits authority."""
    content = _encoded_json(value)
    return {
        "path": relative.as_posix(),
        "sha256": sha256_bytes(content),
        "byte_size": len(content),
    }


def _artifact_ref(data_root: Path, path: Path) -> JsonObject:
    relative = path.resolve().relative_to(data_root).as_posix()
    return {
        "authority": "artifact_root",
        "path": relative,
        "sha256": sha256_file(path),
        "byte_size": path.stat().st_size,
    }


def _validate_schema(value: JsonObject, schema_path: Path) -> None:
    Draft202012Validator(_read_object(schema_path)).validate(value)


def _write_json(path: Path, value: JsonObject) -> None:
    """Atomically replace one fully validated, deterministically encoded spec."""
    with atomic_text_writer(path) as stream:
        stream.write(_encoded_json(value).decode())


def _encoded_json(value: JsonObject) -> bytes:
    """Return the single canonical-on-disk encoding used by generated specs."""
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _read_object(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _object(value: JsonObject, key: str) -> JsonObject:
    item = value.get(key)
    if not isinstance(item, dict):
        raise ValueError(f"expected object field {key!r}")
    return item


def _list_of_objects(value: JsonObject, key: str) -> list[JsonObject]:
    items = value.get(key)
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise ValueError(f"expected object array field {key!r}")
    return items


def _sole_directory(path: Path) -> Path:
    values = sorted(item for item in path.iterdir() if item.is_dir())
    if len(values) != 1:
        found = ", ".join(item.name for item in values) or "none"
        raise ValueError(f"expected exactly one directory beneath {path}; found: {found}")
    return values[0]


if __name__ == "__main__":
    main()
