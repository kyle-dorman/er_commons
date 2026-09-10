"""Prepare an explicitly bound source-free document relink run.

This command is source-free. It reads only checked-in contracts and sealed
Task 03J/04D records, then writes reviewable JSON specifications in the
repository. It never invokes extraction, linking, or publication.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.artifact_io import publish_bytes_no_clobber, sha256_bytes
from er_commons.artifact_verification import VerificationBudget
from er_commons.collection_processing.config import CollectionRunSpec
from er_commons.document_publication.identity import canonical_digest
from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.document_records.document_references.relinking_config import (
    OUTPUT_SCHEMA_ROLES,
    DocumentLinkRunSpec,
)

from .preparation_spec import RelinkPreparationSpec

JsonObject = dict[str, Any]


def prepare_specs(spec: RelinkPreparationSpec, *, budget: VerificationBudget | None = None) -> None:
    """Build and validate all specs before replacing any checked-in file."""
    budget = budget if budget is not None else VerificationBudget()
    repo_root, data_root, reviewed_descriptor = (
        spec.repo_root,
        spec.data_root,
        spec.reviewed_descriptor,
    )
    base_identity = _read_object(repo_root / spec.base_identity, budget=budget)
    validate_production_identity(base_identity)
    collection_spec = _collection_spec(repo_root, spec=spec, budget=budget)
    CollectionRunSpec.model_validate(collection_spec)
    _validate_schema(collection_spec, repo_root / spec.collection_schema, budget=budget)
    production_identity = _production_identity(
        repo_root, base_identity, collection_spec, spec=spec, budget=budget
    )
    validate_production_identity(production_identity)
    _validate_schema(
        production_identity, repo_root / spec.production_identity_schema, budget=budget
    )

    document_spec = _document_spec(repo_root, production_identity, spec=spec, budget=budget)
    _validate_schema(document_spec, repo_root / spec.document_schema, budget=budget)

    link_spec = _link_spec(
        repo_root=repo_root,
        data_root=data_root,
        production_identity=production_identity,
        document_spec=document_spec,
        collection_spec=collection_spec,
        reviewed_descriptor=reviewed_descriptor,
        spec=spec,
        budget=budget,
    )
    DocumentLinkRunSpec.model_validate(link_spec)
    _validate_schema(
        link_spec,
        repo_root / spec.link_schema_root / "document_link_run.schema.json",
        budget=budget,
    )

    outputs = {
        repo_root / spec.collection_spec: collection_spec,
        repo_root / spec.production_identity: production_identity,
        repo_root / spec.document_spec: document_spec,
        repo_root / spec.link_spec: link_spec,
    }
    # Check every destination before publishing any future recipe.
    for path, value in outputs.items():
        if path.exists():
            budget.reserve_read(path, root=repo_root, role="config", source_id="relink_preparation")
        if path.exists() and path.read_bytes() != _encoded_json(value):
            raise FileExistsError(f"refusing to replace existing contract: {path}")
    for path, value in outputs.items():
        if not path.exists():
            _write_json(path, value)
    validate_production_identity(production_identity, project_root=repo_root, budget=budget)


def _production_identity(
    repo_root: Path,
    base: JsonObject,
    collection_spec: JsonObject,
    *,
    spec: RelinkPreparationSpec,
    budget: VerificationBudget,
) -> JsonObject:
    base_preimage = _object(base, "preimage")
    link_artifacts = spec.document_artifacts
    owned_code = spec.document_owned_code
    collection_artifacts = spec.collection_artifacts
    collection_code = spec.collection_owned_code
    preimage: JsonObject = {
        "schema_version": "er_commons.document_publication_identity_preimage.v2",
        "contract_revision": spec.contract_revision,
        "extraction_version_name": spec.extraction_version_name,
        "production_scope": deepcopy(
            spec.replacement_scope
            if spec.replacement_scope is not None
            else _object(base_preimage, "production_scope")
        ),
        "document_process_contract": {
            "version": spec.document_contract_version,
            "artifacts": [
                _repo_ref(repo_root, path, budget=budget) for path in sorted(set(link_artifacts))
            ],
            "owned_code": [
                _repo_ref(repo_root, path, budget=budget) for path in sorted(set(owned_code))
            ],
        },
        "collection_process_contract": {
            "version": spec.collection_contract_version,
            "artifacts": [
                *[
                    _repo_ref(repo_root, path, budget=budget)
                    for path in sorted(set(collection_artifacts))
                ],
                _generated_ref(spec.collection_spec, collection_spec),
            ],
            "owned_code": [
                _repo_ref(repo_root, path, budget=budget) for path in sorted(set(collection_code))
            ],
        },
    }
    if preimage["production_scope"]["ordered_source_ids"] != collection_spec["source_ids"]:
        raise ValueError("replacement scope must bind the selected physical source population")
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


def _document_spec(
    repo_root: Path,
    production_identity: JsonObject,
    *,
    spec: RelinkPreparationSpec,
    budget: VerificationBudget,
) -> JsonObject:
    document = _read_object(repo_root / spec.base_document_spec, budget=budget)
    document["production_extraction_id"] = production_identity["extraction_id"]
    document["production_identity_relative_path"] = spec.production_identity.as_posix()
    document["artifact_relative_root"] = spec.document_artifact_root.as_posix()
    return document


def _collection_spec(
    repo_root: Path, *, spec: RelinkPreparationSpec, budget: VerificationBudget
) -> JsonObject:
    """Select the replacement document lineage without allowing document attempts."""
    collection = _read_object(repo_root / spec.base_collection_spec, budget=budget)
    collection["document_run_spec"] = os.path.relpath(
        spec.document_spec, spec.collection_spec.parent
    )
    collection["document_evidence_mode"] = "downstream_replay_only"
    return collection


def _link_spec(
    *,
    repo_root: Path,
    data_root: Path,
    production_identity: JsonObject,
    document_spec: JsonObject,
    collection_spec: JsonObject,
    reviewed_descriptor: Path,
    spec: RelinkPreparationSpec,
    budget: VerificationBudget,
) -> JsonObject:
    source_ids = list(collection_spec["source_ids"])
    if set(spec.document_roots) != set(source_ids):
        raise ValueError("explicit document bindings differ from the accepted source scope")
    documents = [
        _document_selection(
            data_root,
            data_root / spec.document_roots[str(source_id)],
            str(source_id),
            budget=budget,
        )
        for source_id in source_ids
    ]
    scope_root = data_root / spec.scope_root
    handoff_root = data_root / spec.handoff_root
    descriptor = _read_object(reviewed_descriptor, budget=budget)
    reviewed_root = data_root / Path(str(_object(descriptor, "completion_ref")["path"])).parents[1]
    output_names = {role: f"{role}.schema.json" for role in OUTPUT_SCHEMA_ROLES}
    payloads = _object(descriptor, "payloads")
    return {
        "schema_version": "er_commons.document_link_run_spec.v1",
        "artifact_relative_root": spec.link_artifact_root.as_posix(),
        "base_collection": {
            "handoff_ref": _artifact_ref(
                data_root, handoff_root / "records/completion_record.json", budget=budget
            ),
            "contract_bundle_ref": _artifact_ref(
                data_root, scope_root / "contract_bundle.json", budget=budget
            ),
        },
        "base_production_identity_ref": _external_repo_ref(
            repo_root, spec.base_identity, budget=budget
        ),
        "replacement_production_identity_recipe_ref": _generated_repo_ref(
            spec.production_identity, production_identity
        ),
        "document_publication_spec_ref": _generated_repo_ref(spec.document_spec, document_spec),
        "collection_run_spec_ref": _generated_repo_ref(spec.collection_spec, collection_spec),
        "linking_policy_ref": _external_repo_ref(repo_root, spec.linking_policy, budget=budget),
        "linking_policy_schema_ref": _external_repo_ref(
            repo_root, spec.link_schema_root / "linking_policy.schema.json", budget=budget
        ),
        "source_family_catalog_ref": _artifact_ref(
            data_root, data_root / spec.source_catalog, budget=budget
        ),
        "selected_source_ids": source_ids,
        "documents": documents,
        "reviewed_navigation": {
            "bundle_id": descriptor["bundle_id"],
            "bundle_ref": _artifact_ref(data_root, reviewed_descriptor, budget=budget),
            "schema_ref": _external_repo_ref(
                repo_root,
                spec.link_schema_root / "reviewed_navigation_bundle.schema.json",
                budget=budget,
            ),
            "source_ids": descriptor["source_ids"],
            "identity_ref": _artifact_ref(
                data_root, reviewed_root / "records/identity_preimage.json", budget=budget
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
            role: _external_repo_ref(repo_root, spec.link_schema_root / filename, budget=budget)
            for role, filename in output_names.items()
        },
    }


def _document_selection(
    data_root: Path, document_root: Path, source_id: str, *, budget: VerificationBudget
) -> JsonObject:
    identity = _read_object(document_root / "records/document_identity.json", budget=budget)
    structured = _object(_object(identity, "stage_completions"), "structured_document")
    structured_completion = data_root / str(structured["path"])
    structured_root = structured_completion.parents[1]
    return {
        "source_id": source_id,
        "source_document": {
            "candidate_id": document_root.name,
            "completion_ref": _artifact_ref(
                data_root, document_root / "records/completion_record.json", budget=budget
            ),
            "inventory_ref": _artifact_ref(
                data_root, document_root / "records/artifact_inventory.json", budget=budget
            ),
        },
        "structured_document": {
            "candidate_id": structured_root.name,
            "completion_ref": _artifact_ref(data_root, structured_completion, budget=budget),
            "inventory_ref": _artifact_ref(
                data_root, structured_root / "records/artifact_inventory.json", budget=budget
            ),
        },
    }


def _repo_ref(repo_root: Path, relative: Path, *, budget: VerificationBudget) -> JsonObject:
    path = repo_root / relative
    return {
        "path": relative.as_posix(),
        "sha256": budget.hash_file(
            path, root=path.parent, role="input_binding", source_id="relink_preparation"
        ),
        "byte_size": path.stat().st_size,
    }


def _external_repo_ref(
    repo_root: Path, relative: Path, *, budget: VerificationBudget
) -> JsonObject:
    return {"authority": "repository", **_repo_ref(repo_root, relative, budget=budget)}


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


def _artifact_ref(data_root: Path, path: Path, *, budget: VerificationBudget) -> JsonObject:
    relative = path.resolve().relative_to(data_root).as_posix()
    return {
        "authority": "artifact_root",
        "path": relative,
        "sha256": budget.hash_file(
            path, root=path.parent, role="input_binding", source_id="relink_preparation"
        ),
        "byte_size": path.stat().st_size,
    }


def _validate_schema(value: JsonObject, schema_path: Path, *, budget: VerificationBudget) -> None:
    Draft202012Validator(_read_object(schema_path, budget=budget)).validate(value)


def _write_json(path: Path, value: JsonObject) -> None:
    """Publish validated bytes without replacing a concurrently created contract."""
    publish_bytes_no_clobber(path, _encoded_json(value))


def _encoded_json(value: JsonObject) -> bytes:
    """Return the single canonical-on-disk encoding used by generated specs."""
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _read_object(path: Path, *, budget: VerificationBudget) -> JsonObject:
    value = budget.read_json(
        path, root=path.parent, role="input_binding", source_id="relink_preparation"
    )
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
