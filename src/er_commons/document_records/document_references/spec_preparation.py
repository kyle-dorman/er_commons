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
from typing import Any, cast

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.artifact_io import publish_bytes_no_clobber, sha256_bytes
from er_commons.artifact_verification import VerificationBudget
from er_commons.collection_processing.config import CollectionRunSpec
from er_commons.document_publication.identity import canonical_digest
from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.document_records.document_references.relink_preflight import (
    task06g_base_membership_from_source_slots,
    validate_base_collection_selection,
)
from er_commons.document_records.document_references.relinking_config import (
    OUTPUT_SCHEMA_ROLES,
    DocumentLinkRunSpec,
)

from .preparation_spec import RelinkPreparationSpec

JsonObject = dict[str, Any]


def build_specs(
    spec: RelinkPreparationSpec, *, budget: VerificationBudget | None = None
) -> dict[Path, JsonObject]:
    """Build and validate deterministic specs without publishing any bytes."""
    budget = budget if budget is not None else VerificationBudget()
    repo_root, data_root, reviewed_descriptor = (
        spec.repo_root,
        spec.data_root,
        spec.reviewed_descriptor,
    )
    runtime_root = repo_root if spec.runtime_spec_authority == "repository" else data_root
    output_root = repo_root if spec.output_authority == "repository" else data_root
    base_identity = _read_object(runtime_root / spec.base_identity, budget=budget)
    validate_production_identity(base_identity)
    collection_spec = _collection_spec(runtime_root, spec=spec, budget=budget)
    CollectionRunSpec.model_validate(collection_spec)
    _validate_schema(collection_spec, repo_root / spec.collection_schema, budget=budget)
    production_identity = _production_identity(
        repo_root, base_identity, collection_spec, spec=spec, budget=budget
    )
    validate_production_identity(production_identity)
    _validate_schema(
        production_identity, repo_root / spec.production_identity_schema, budget=budget
    )

    document_spec = _document_spec(runtime_root, production_identity, spec=spec, budget=budget)
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

    return {
        output_root / spec.collection_spec: collection_spec,
        output_root / spec.production_identity: production_identity,
        output_root / spec.document_spec: document_spec,
        output_root / spec.link_spec: link_spec,
    }


def build_task06g_relink_specs(
    preparation: JsonObject,
    link_spec: JsonObject,
    *,
    repo_root: Path,
    data_root: Path,
    link_schema: Path,
    budget: VerificationBudget | None = None,
) -> dict[str, JsonObject]:
    """Purely rebuild Task 06G replacement selections and validate both resolved specs.

    Task 06G stages its compact preparation contract under the artifact root rather
    than publishing the four generic preparation outputs. This narrow pure boundary
    retains the maintained document-selection construction while leaving all byte
    publication exclusively to the Task 06G resolver.
    """
    budget = budget if budget is not None else VerificationBudget()
    if not link_schema.resolve().is_relative_to(repo_root.resolve()):
        raise ValueError("Task 06G link schema escapes repository authority")
    if preparation.get("schema_version") != "er_commons.task06g.relink_preparation_template.v1":
        raise ValueError("unsupported Task 06G relink preparation schema")
    raw_roots = preparation.get("document_roots")
    if not isinstance(raw_roots, dict) or not raw_roots:
        raise ValueError("Task 06G relink preparation requires explicit document roots")
    if preparation.get("artifact_relative_root") != link_spec.get("artifact_relative_root"):
        raise ValueError("Task 06G relink output roots differ")
    policy = link_spec.get("linking_policy_ref")
    if not isinstance(policy, dict) or policy.get("path") != preparation.get("linking_policy"):
        raise ValueError("Task 06G relink policy binding differs")

    base_membership_value = preparation.get("base_membership_ref")
    if not isinstance(base_membership_value, dict):
        raise ValueError("Task 06G relink preparation lacks base membership")
    base_membership = _external_reference(
        base_membership_value, repo_root=repo_root, data_root=data_root, budget=budget
    )
    built_link = deepcopy(link_spec)
    built_link["resolution_status"] = "resolved"
    built_link["base_membership_ref"] = base_membership
    base_collection = _object(built_link, "base_collection")
    handoff_ref = _external_reference(
        _object(base_collection, "handoff_ref"),
        repo_root=repo_root,
        data_root=data_root,
        budget=budget,
    )
    contract_ref = _external_reference(
        _object(base_collection, "contract_bundle_ref"),
        repo_root=repo_root,
        data_root=data_root,
        budget=budget,
    )
    base_identity_ref = _external_reference(
        _object(built_link, "base_production_identity_ref"),
        repo_root=repo_root,
        data_root=data_root,
        budget=budget,
    )
    built_link["base_collection"] = {
        "handoff_ref": handoff_ref,
        "contract_bundle_ref": contract_ref,
    }
    built_link["base_production_identity_ref"] = base_identity_ref
    base_identity = _read_object(repo_root / str(base_identity_ref["path"]), budget=budget)
    production_id = validate_production_identity(base_identity).value
    contract_path = Path(str(contract_ref["path"]))
    if contract_path.name != "contract_bundle.json" or len(contract_path.parents) < 3:
        raise ValueError("Task 06G base collection contract path is invalid")
    base_documents = task06g_base_membership_from_source_slots(
        _read_object(data_root / str(base_membership["path"]), budget=budget),
        artifact_root=data_root,
        publication_root=data_root / contract_path.parents[2],
        production_extraction_id=production_id,
        budget=budget,
    )
    documents = [item.model_dump(mode="json") for item in base_documents]
    built_link["documents"] = documents
    by_source = {str(document["source_id"]): index for index, document in enumerate(documents)}
    logical_ids = preparation.get("logical_source_ids")
    change_classes = preparation.get("replacement_change_classes")
    reuse_bases = preparation.get("reuse_bases")
    evidence = preparation.get("change_evidence_refs")
    if not all(
        isinstance(item, dict) for item in (logical_ids, change_classes, reuse_bases, evidence)
    ):
        raise ValueError("Task 06G preparation lacks mixed-lineage policy maps")
    logical_ids = cast(JsonObject, logical_ids)
    change_classes = cast(JsonObject, change_classes)
    reuse_bases = cast(JsonObject, reuse_bases)
    evidence = cast(JsonObject, evidence)
    base_by_source = {row.source_id: row for row in base_documents}
    replacement_sources = set(raw_roots)
    if set(change_classes) != replacement_sources or set(reuse_bases) != replacement_sources:
        raise ValueError("Task 06G replacement policy differs from replacement roots")
    expected_policy = {
        "feir_appendix_f1": (
            "deir_appendix_f1",
            "new_source_addition_no_old_entity_equivalence",
            "qualified_substitute_new_source_no_entity_equivalence",
        ),
        "deir_appendix_a": (
            "deir_appendix_a",
            "repeated_heading_many_to_one",
            "accepted_repeated_heading_repair",
        ),
        "deir_main": (
            "deir_main",
            "missing_chapter_additions_and_fc1_aliases",
            "accepted_missing_chapter_and_fc1_repair",
        ),
    }
    observed_policy = {
        source_id: (
            logical_ids.get(source_id, source_id),
            change_classes.get(source_id),
            reuse_bases.get(source_id),
        )
        for source_id in replacement_sources
    }
    if observed_policy != expected_policy:
        raise ValueError("Task 06G replacement policy is not the accepted three-row mapping")
    replacement_logical_ids = {str(logical_ids[source_id]) for source_id in replacement_sources}
    if set(by_source) & replacement_sources != replacement_sources - {"feir_appendix_f1"}:
        raise ValueError("Task 06G replacement roots do not match base logical membership")
    if replacement_logical_ids != {"deir_appendix_f1", "deir_appendix_a", "deir_main"}:
        raise ValueError("Task 06G replacement logical membership differs")

    for source_id, relative_root in raw_roots.items():
        if not isinstance(source_id, str) or not isinstance(relative_root, str):
            raise ValueError("Task 06G replacement roots must be string bindings")
        root = (data_root / relative_root).resolve()
        if not root.is_relative_to(data_root.resolve()):
            raise ValueError("Task 06G replacement document root escapes artifact authority")
        logical_source_id = str(logical_ids[source_id])
        documents[by_source[logical_source_id]] = _document_selection(
            data_root, root, source_id, budget=budget
        )
    for document in documents:
        if not isinstance(document, dict):
            raise ValueError("Task 06G document selection must be an object")
        source_id = str(document["source_id"])
        logical_source_id = str(logical_ids.get(source_id, source_id))
        base = base_by_source.get(logical_source_id)
        if base is None:
            raise ValueError(f"Task 06G logical source is absent from base membership: {source_id}")
        changed = source_id in replacement_sources
        document.update(
            {
                "logical_source_id": logical_source_id,
                "base_source_id": base.source_id,
                "base_source_document": base.source_document.model_dump(mode="json"),
                "base_structured_document": base.structured_document.model_dump(mode="json"),
                "change_class": (change_classes[source_id] if changed else "preserved_semantic"),
                "reuse_basis": (
                    reuse_bases[source_id] if changed else "sealed_base_candidate_downstream_replay"
                ),
                "evidence_refs": (
                    [
                        _external_reference(
                            item, repo_root=repo_root, data_root=data_root, budget=budget
                        )
                        for item in evidence.get(source_id, [])
                    ]
                    if changed
                    else [base.source_document.completion_ref.model_dump(mode="json")]
                ),
                "correspondence_refs": (
                    _task06g_correspondence_refs(
                        document, data_root=data_root, source_id=source_id, budget=budget
                    )
                    if changed
                    else []
                ),
            }
        )
    built_link["selected_source_ids"] = [str(document["source_id"]) for document in documents]
    parsed_link = DocumentLinkRunSpec.model_validate(built_link)
    _validate_schema(built_link, link_schema, budget=budget)
    validate_base_collection_selection(
        spec=parsed_link,
        base_production_identity=base_identity,
        handoff=_read_object(data_root / str(handoff_ref["path"]), budget=budget),
        contract_bundle=_read_object(data_root / str(contract_ref["path"]), budget=budget),
        base_membership_spec=base_documents,
    )
    return {
        "task06g_relink_preparation_v1.json": deepcopy(preparation),
        "task06g_link_v1.json": built_link,
    }


def _external_reference(
    value: JsonObject, *, repo_root: Path, data_root: Path, budget: VerificationBudget
) -> JsonObject:
    """Resolve and seal one authority-aware compact reference."""
    authority = value.get("authority")
    relative = value.get("path")
    if authority not in {"repository", "artifact_root"} or not isinstance(relative, str):
        raise ValueError("Task 06G evidence requires repository or artifact-root authority")
    root = repo_root if authority == "repository" else data_root
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Task 06G evidence reference escapes its authority")
    supplied_sha = value.get("sha256")
    supplied_size = value.get("byte_size")
    if (
        authority == "artifact_root"
        and path.is_file()
        and path.stat().st_size > budget.hash_file_limit
    ):
        if not isinstance(supplied_sha, str) or len(supplied_sha) != 64:
            raise ValueError("oversized Task 06G evidence requires a frozen digest")
        if not isinstance(supplied_size, int):
            raise ValueError("oversized Task 06G evidence requires a frozen byte size")
        budget.check_metadata(
            path,
            root=data_root,
            role="input_binding",
            source_id="relink_preparation",
            byte_size=supplied_size,
        )
        budget.observations.append(
            {
                "source_id": "relink_preparation",
                "role": "input_binding",
                "path": str(path),
                "byte_size": supplied_size,
                "recorded_digest": supplied_sha,
                "verification_mode": "metadata_checked",
                "limitation": "oversized accepted digest retained; bytes not freshly hashed",
            }
        )
        sealed = {
            "authority": "artifact_root",
            "path": path.relative_to(data_root).as_posix(),
            "sha256": supplied_sha,
            "byte_size": supplied_size,
        }
    else:
        sealed = (
            _artifact_ref(data_root, path, budget=budget)
            if authority == "artifact_root"
            else _external_repo_ref(repo_root, Path(relative), budget=budget)
        )
    if supplied_sha is not None and supplied_sha != sealed["sha256"]:
        raise ValueError("Task 06G evidence reference checksum differs")
    if supplied_size is not None and supplied_size != sealed["byte_size"]:
        raise ValueError("Task 06G evidence reference byte size differs")
    return sealed


def _task06g_correspondence_refs(
    document: JsonObject,
    *,
    data_root: Path,
    source_id: str,
    budget: VerificationBudget,
) -> list[JsonObject]:
    """Bind exact repair correspondence and forbid equivalence for substituted F1."""
    if source_id == "feir_appendix_f1":
        return []
    structured = _object(document, "structured_document")
    completion = data_root / str(_object(structured, "completion_ref")["path"])
    root = completion.parents[1]
    names = {
        "deir_appendix_a": "support/repeated_heading_correspondence.json",
        "deir_main": "support/missing_chapter_correspondence.json",
    }
    relative = names.get(source_id)
    if relative is None:
        raise ValueError(f"undeclared Task 06G replacement source: {source_id}")
    return [_artifact_ref(data_root, root / relative, budget=budget)]


def prepare_specs(spec: RelinkPreparationSpec, *, budget: VerificationBudget | None = None) -> None:
    """Publish the pure builder's validated values without replacing a contract."""
    budget = budget if budget is not None else VerificationBudget()
    outputs = build_specs(spec, budget=budget)
    output_root = spec.repo_root if spec.output_authority == "repository" else spec.data_root
    production_identity = outputs[output_root / spec.production_identity]
    # Check every destination before publishing any future recipe.
    for path, value in outputs.items():
        if path.exists():
            budget.reserve_read(
                path, root=output_root, role="config", source_id="relink_preparation"
            )
        if path.exists() and path.read_bytes() != _encoded_json(value):
            raise FileExistsError(f"refusing to replace existing contract: {path}")
    for path, value in outputs.items():
        if not path.exists():
            _write_json(path, value)
    validate_production_identity(
        production_identity,
        project_root=spec.repo_root,
        artifact_root=spec.data_root,
        budget=budget,
    )


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
    authority_aware = spec.output_authority == "artifact_root"

    def contract_ref(path: Path) -> JsonObject:
        reference = _repo_ref(repo_root, path, budget=budget)
        if authority_aware:
            reference["authority"] = "repository"
        return reference

    preimage: JsonObject = {
        "schema_version": (
            "er_commons.document_publication_identity_preimage.v3"
            if authority_aware
            else "er_commons.document_publication_identity_preimage.v2"
        ),
        "contract_revision": spec.contract_revision,
        "extraction_version_name": spec.extraction_version_name,
        "production_scope": deepcopy(
            spec.replacement_scope
            if spec.replacement_scope is not None
            else _object(base_preimage, "production_scope")
        ),
        "document_process_contract": {
            "version": spec.document_contract_version,
            "artifacts": [contract_ref(path) for path in sorted(set(link_artifacts))],
            "owned_code": [contract_ref(path) for path in sorted(set(owned_code))],
        },
        "collection_process_contract": {
            "version": spec.collection_contract_version,
            "artifacts": [
                *[contract_ref(path) for path in sorted(set(collection_artifacts))],
                (
                    _generated_authority_ref(
                        spec.collection_spec,
                        collection_spec,
                        authority=spec.output_authority,
                    )
                    if authority_aware
                    else _generated_ref(spec.collection_spec, collection_spec)
                ),
            ],
            "owned_code": [contract_ref(path) for path in sorted(set(collection_code))],
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
        "schema_version": (
            "er_commons.document_publication_identity.v3"
            if authority_aware
            else "er_commons.document_publication_identity.v2"
        ),
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
    if spec.output_authority == "artifact_root":
        document["schema_version"] = "er_commons.document_run_spec.v4"
        document.pop("production_identity_relative_path", None)
        document["production_identity_ref"] = _generated_authority_ref(
            spec.production_identity,
            production_identity,
            authority="artifact_root",
        )
    else:
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
        "schema_version": (
            "er_commons.document_link_run_spec.v2"
            if spec.output_authority == "artifact_root"
            else "er_commons.document_link_run_spec.v1"
        ),
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
        "replacement_production_identity_recipe_ref": _generated_authority_ref(
            spec.production_identity, production_identity, authority=spec.output_authority
        ),
        "document_publication_spec_ref": _generated_authority_ref(
            spec.document_spec, document_spec, authority=spec.output_authority
        ),
        "collection_run_spec_ref": _generated_authority_ref(
            spec.collection_spec, collection_spec, authority=spec.output_authority
        ),
        "linking_policy_ref": _external_repo_ref(repo_root, spec.linking_policy, budget=budget),
        "linking_policy_schema_ref": _external_repo_ref(
            repo_root, spec.link_schema_root / "linking_policy.schema.json", budget=budget
        ),
        "source_family_catalog_ref": _artifact_ref(
            data_root, data_root / spec.source_catalog, budget=budget
        ),
        "selected_source_ids": source_ids,
        **(
            {"figure_alias_source_ids": ["deir_main"]}
            if spec.output_authority == "artifact_root"
            else {}
        ),
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


def _generated_authority_ref(relative: Path, value: JsonObject, *, authority: str) -> JsonObject:
    """Seal generated bytes beneath the preparation request's explicit authority."""
    reference = _generated_repo_ref(relative, value)
    reference["authority"] = authority
    return reference


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
