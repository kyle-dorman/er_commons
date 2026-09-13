"""Authority-aware, allowlisted Task 06G runtime spec resolution."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import cast

import jsonschema  # type: ignore[import-untyped]

from er_commons.artifact_io import sha256_file
from er_commons.authority_reference import AuthorityReference
from er_commons.collection_processing.contract import (
    build_collection_handoff_id,
    build_cross_document_link_id,
    build_record_target_index_id,
)
from er_commons.collection_processing.production_identity import (
    CollectionProductionIdentityPreimage,
    build_collection_production_identity,
)
from er_commons.document_publication.identity import build_candidate_id, canonical_digest
from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.task06g.core import (
    JsonObject,
    canonical_bytes,
    content_reference,
    load_object,
    pointer_value,
    publish_directory_no_clobber,
    reference,
    set_pointer,
    verify_reference,
)


def _roots(generation_spec: Path, generation: JsonObject) -> tuple[Path, Path, Path]:
    recipe = generation_spec.resolve().parent
    repository = (recipe / str(generation.get("repository_root", "."))).resolve()
    raw_data_root = generation.get("data_root", ".")
    if raw_data_root == "${ER_COMMONS_DATA_ROOT}":
        from er_commons.settings import load_settings

        artifacts = load_settings().data_root.resolve()
    else:
        artifacts = (recipe / str(raw_data_root)).resolve()
    if not generation_spec.resolve().is_relative_to(repository):
        raise ValueError("generation spec is outside repository authority")
    return recipe, repository, artifacts


def _phase_definition(generation: JsonObject, phase: str) -> JsonObject:
    phases = generation.get("phases")
    if not isinstance(phases, dict) or not isinstance(phases.get(phase), dict):
        raise ValueError(f"generation recipe does not define phase: {phase}")
    return cast(JsonObject, phases[phase])


def _authority_path(
    relative: str,
    authority: str,
    *,
    recipe_root: Path,
    repository_root: Path,
    artifact_root: Path,
) -> tuple[Path, Path]:
    roots = {
        "recipe": recipe_root,
        "repository": repository_root,
        "artifact_root": artifact_root,
    }
    if authority not in roots:
        raise ValueError(f"unsupported path authority: {authority}")
    root = roots[authority].resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"path escapes {authority}: {relative}")
    return path, root


def _checkpoint_value(
    mapping: JsonObject,
    *,
    recipe_root: Path,
    repository_root: Path,
    artifact_root: Path,
) -> tuple[object, JsonObject]:
    path_value = mapping.get("checkpoint")
    source_pointer = mapping.get("source_pointer")
    authority = mapping.get("checkpoint_authority", "recipe")
    if not all(isinstance(value, str) for value in (path_value, source_pointer, authority)):
        raise ValueError("resolution requires checkpoint authority, path, and source pointer")
    path, root = _authority_path(
        cast(str, path_value),
        cast(str, authority),
        recipe_root=recipe_root,
        repository_root=repository_root,
        artifact_root=artifact_root,
    )
    checkpoint = load_object(path)
    if checkpoint.get("verified") is not True:
        raise ValueError(f"identity checkpoint is not independently verified: {path_value}")
    if checkpoint.get("derived_id") is not None and checkpoint.get("derived_id") != checkpoint.get(
        "recomputed_id"
    ):
        raise ValueError(f"identity checkpoint recomputation mismatch: {path_value}")
    completion = checkpoint.get("stage_completion")
    if completion is not None:
        if not isinstance(completion, dict):
            raise ValueError("stage completion reference must be an object")
        completion_root = (
            artifact_root if completion.get("authority") == "artifact_root" else repository_root
        )
        verify_reference(completion, root=completion_root)
    ref_authority = "artifact_root" if root == artifact_root else "repository"
    return pointer_value(checkpoint, cast(str, source_pointer)), {
        "authority": ref_authority,
        **reference(path, root=root),
    }


def _resolve_spec(
    entry: JsonObject,
    *,
    recipe_root: Path,
    repository_root: Path,
    artifact_root: Path,
    generator_refs: list[JsonObject] | None = None,
    memory: dict[str, JsonObject] | None = None,
    root_substitutions: dict[str, str] | None = None,
) -> tuple[str, bytes, JsonObject]:
    template_name = entry.get("template")
    destination = entry.get("destination")
    schema_name = entry.get("schema")
    if not all(isinstance(value, str) for value in (template_name, destination, schema_name)):
        raise ValueError("spec entry requires template, destination, and schema")
    template_path = (recipe_root / cast(str, template_name)).resolve()
    schema_path = (recipe_root / cast(str, schema_name)).resolve()
    if not template_path.is_relative_to(repository_root) or not schema_path.is_relative_to(
        repository_root
    ):
        raise ValueError("templates and schemas must be repository-authoritative")
    if entry.get("template_sha256") != sha256_file(template_path):
        raise ValueError(f"template digest mismatch: {template_path}")
    if entry.get("schema_sha256") != sha256_file(schema_path):
        raise ValueError(f"schema digest mismatch: {schema_path}")
    resolved = copy.deepcopy(load_object(template_path))
    populated: list[JsonObject] = []
    raw_resolutions = entry.get("resolutions", [])
    if not isinstance(raw_resolutions, list):
        raise ValueError("resolutions must be an ordered list")
    seen: set[str] = set()
    for raw in raw_resolutions:
        if not isinstance(raw, dict) or not isinstance(raw.get("pointer"), str):
            raise ValueError("each resolution requires an exact pointer")
        mapping = cast(JsonObject, raw)
        pointer = cast(str, mapping["pointer"])
        if pointer in seen:
            raise ValueError(f"duplicate resolved pointer: {pointer}")
        seen.add(pointer)
        memory_key = mapping.get("in_memory_checkpoint")
        if isinstance(memory_key, str):
            if memory is None or memory_key not in memory:
                raise ValueError(f"missing in-memory checkpoint: {memory_key}")
            value = pointer_value(memory[memory_key], cast(str, mapping["source_pointer"]))
            checkpoint_ref: JsonObject = {"phase_local": memory_key}
        else:
            value, checkpoint_ref = _checkpoint_value(
                mapping,
                recipe_root=recipe_root,
                repository_root=repository_root,
                artifact_root=artifact_root,
            )
        set_pointer(resolved, pointer, value)
        populated.append({"pointer": pointer, "value": value, "checkpoint": checkpoint_ref})
    if root_substitutions:
        resolved = cast(JsonObject, _substitute_root_markers(resolved, root_substitutions))
    jsonschema.Draft202012Validator(load_object(schema_path)).validate(resolved)
    content = canonical_bytes(resolved)
    receipt: JsonObject = {
        "schema_version": "er_commons.task06g.resolved_spec_receipt.v1",
        "template": {"authority": "repository", **reference(template_path, root=repository_root)},
        "schema": {"authority": "repository", **reference(schema_path, root=repository_root)},
        "generator": entry.get("generator"),
        "generator_files": copy.deepcopy(generator_refs or []),
        "populated": populated,
        "resolved": content_reference(cast(str, destination), content),
        "validation": "passed",
    }
    return cast(str, destination), content, receipt


def _substitute_root_markers(value: object, substitutions: dict[str, str]) -> object:
    """Replace only the two reviewed absolute-root markers in a resolved template."""
    if isinstance(value, dict):
        return {key: _substitute_root_markers(item, substitutions) for key, item in value.items()}
    if isinstance(value, list):
        return [_substitute_root_markers(item, substitutions) for item in value]
    if isinstance(value, str):
        rendered = value
        for marker, replacement in substitutions.items():
            rendered = rendered.replace(marker, replacement)
        if ("{" in rendered or "}" in rendered) and rendered != "{scope_id}":
            raise ValueError(f"unsupported resolved-template marker: {value}")
        return rendered
    return value


def _collection_production_identity(
    generation_spec: Path,
    generation: JsonObject,
    *,
    collection_entry: JsonObject,
    imported_selection_name: str,
    imported_selection_content: bytes,
    repository_root: Path,
    artifact_root: Path,
    output_root: Path,
) -> tuple[str, JsonObject, JsonObject]:
    """Build the collection-only identity and its atomic pre-execution checkpoint."""
    recipe = generation.get("collection_production_identity_recipe")
    if not isinstance(recipe, dict):
        raise ValueError("collection-only initial phase requires its identity recipe")
    destination = recipe.get("destination")
    output_namespace = recipe.get("collection_output_namespace")
    if not isinstance(destination, str) or not isinstance(output_namespace, str):
        raise ValueError("collection identity recipe lacks destination or output namespace")
    template_path = (generation_spec.parent / str(collection_entry["template"])).resolve()
    schema_path = (generation_spec.parent / str(collection_entry["schema"])).resolve()
    imported_path = output_root / "00_initial" / imported_selection_name
    imported_ref = {
        "authority": "artifact_root",
        **content_reference(
            imported_path.resolve().relative_to(artifact_root).as_posix(),
            imported_selection_content,
        ),
    }
    generator_refs = generation.get("generator_files")
    if not isinstance(generator_refs, list) or not all(
        isinstance(row, dict) for row in generator_refs
    ):
        raise ValueError("collection generation requires closed generator references")
    source_catalog_ref = recipe.get("source_catalog_ref")
    source_policy_refs = recipe.get("source_policy_refs")
    if not isinstance(source_catalog_ref, dict) or not isinstance(source_policy_refs, list):
        raise ValueError("collection identity recipe lacks source catalog or policies")
    preimage = CollectionProductionIdentityPreimage(
        schema_version="er_commons.collection_production_identity_preimage.v1",
        generation_ref=AuthorityReference(
            authority="repository", **reference(generation_spec, root=repository_root)
        ),
        collection_template_ref=AuthorityReference(
            authority="repository", **reference(template_path, root=repository_root)
        ),
        collection_schema_ref=AuthorityReference(
            authority="repository", **reference(schema_path, root=repository_root)
        ),
        owned_code_refs=tuple(AuthorityReference.model_validate(row) for row in generator_refs),
        imported_selection_ref=AuthorityReference.model_validate(imported_ref),
        imported_selection_sha256=str(imported_ref["sha256"]),
        source_catalog_ref=AuthorityReference.model_validate(source_catalog_ref),
        source_policy_refs=tuple(
            AuthorityReference.model_validate(row) for row in source_policy_refs
        ),
        output_namespace=output_namespace,
    )
    identity = build_collection_production_identity(preimage)
    identity_content = canonical_bytes(identity)
    identity_path = output_root / "00_initial" / destination
    identity_ref = {
        "authority": "artifact_root",
        **content_reference(
            identity_path.resolve().relative_to(artifact_root).as_posix(), identity_content
        ),
    }
    checkpoint: JsonObject = {
        "schema_version": "er_commons.task06g.identity_checkpoint.v1",
        "stage_key": "pre_execution_collection_identity",
        "recipe_checkpoint": {
            "authority": "repository",
            **reference(generation_spec, root=repository_root),
        },
        "stage_completion": None,
        "identity_ref": identity_ref,
        "derived_id": identity["collection_production_id"],
        "identity_preimage": identity["preimage"],
        "recomputed_id": build_collection_production_identity(identity["preimage"])[
            "collection_production_id"
        ],
        "outputs": {
            "collection_production_id": identity["collection_production_id"],
            "collection_production_identity_ref": identity_ref,
            "imported_selection_ref": imported_ref,
        },
        "verified": True,
    }
    return destination, identity, checkpoint


def _production_identity(
    generation_spec: Path,
    generation: JsonObject,
    collection_content: bytes,
    *,
    repository_root: Path,
    artifact_root: Path,
    output_root: Path,
) -> tuple[JsonObject, JsonObject]:
    """Build the v3 identity from the frozen recipe and resolved collection bytes."""
    recipe = generation.get("production_identity_recipe")
    if not isinstance(recipe, dict):
        raise ValueError("initial phase requires production_identity_recipe")
    base_path, _ = _authority_path(
        str(recipe["base_identity_path"]),
        str(recipe.get("base_identity_authority", "repository")),
        recipe_root=generation_spec.resolve().parent,
        repository_root=repository_root,
        artifact_root=artifact_root,
    )
    if sha256_file(base_path) != recipe.get("base_identity_sha256"):
        raise ValueError("base production identity digest differs")
    base = load_object(base_path)
    preimage = copy.deepcopy(cast(JsonObject, base["preimage"]))
    preimage.update(
        {
            "schema_version": "er_commons.document_publication_identity_preimage.v3",
            "contract_revision": recipe["contract_revision"],
            "extraction_version_name": recipe["extraction_version_name"],
            "production_scope": copy.deepcopy(recipe["production_scope"]),
        }
    )
    extras = recipe.get("additional_references", {})
    if not isinstance(extras, dict):
        raise ValueError("additional_references must be an object")
    for name in ("document_process_contract", "collection_process_contract"):
        section = cast(JsonObject, preimage[name])
        section["version"] = recipe[f"{name}_version"]
        for role in ("artifacts", "owned_code"):
            addition = cast(JsonObject, extras.get(name, {})).get(role, [])
            if not isinstance(addition, list) or not addition:
                raise ValueError("production identity inventories must be nonempty lists")
            section[role] = copy.deepcopy(addition)
    generator_refs = generation.get("generator_files")
    if not isinstance(generator_refs, list) or not all(
        isinstance(row, dict) for row in generator_refs
    ):
        raise ValueError("generation recipe requires closed generator file references")
    phase_refs: list[JsonObject] = []
    for phase in cast(dict[str, JsonObject], generation["phases"]).values():
        for entry in cast(list[JsonObject], phase["specs"]):
            for field in ("template", "schema"):
                path = (generation_spec.parent / str(entry[field])).resolve()
                phase_refs.append(
                    {"authority": "repository", **reference(path, root=repository_root)}
                )
    for name in ("document_process_contract", "collection_process_contract"):
        section = cast(JsonObject, preimage[name])
        section["owned_code"].extend(copy.deepcopy(generator_refs))
        section["artifacts"].extend(copy.deepcopy(phase_refs))
    relative_collection = (
        (output_root / "00_initial/task06g_collection_v1.json")
        .resolve()
        .relative_to(artifact_root)
        .as_posix()
    )
    cast(JsonObject, preimage["collection_process_contract"])["artifacts"].append(
        {
            "authority": "artifact_root",
            **content_reference(relative_collection, collection_content),
        }
    )
    digest = canonical_digest(preimage)
    identity: JsonObject = {
        "record_type": "production_identity",
        "schema_version": "er_commons.document_publication_identity.v3",
        "fixture_status": "identity_recipe",
        "execution_status": "not_executed",
        "extraction_id": f"exv1-{digest}",
        "identity_sha256": digest,
        "preimage": preimage,
    }
    validate_production_identity(identity)
    identity_bytes = canonical_bytes(identity)
    relative_identity = (
        (output_root / "00_initial/production_identity.json")
        .resolve()
        .relative_to(artifact_root)
        .as_posix()
    )
    identity_ref = {
        "authority": "artifact_root",
        **content_reference(relative_identity, identity_bytes),
    }
    checkpoint: JsonObject = {
        "schema_version": "er_commons.task06g.identity_checkpoint.v1",
        "stage_key": "pre_execution_production_identity",
        "recipe_checkpoint": {
            "authority": "repository",
            **reference(generation_spec, root=repository_root),
        },
        "stage_completion": None,
        "identity_ref": identity_ref,
        "derived_id": identity["extraction_id"],
        "identity_preimage": preimage,
        "recomputed_id": f"exv1-{canonical_digest(preimage)}",
        "verified": True,
    }
    return identity, checkpoint


def _verify_existing(destination: Path, expected: dict[str, bytes]) -> None:
    if not destination.is_dir():
        raise ValueError(f"resolved phase is not a directory: {destination}")
    observed = {
        path.relative_to(destination).as_posix(): path.read_bytes()
        for path in destination.rglob("*")
        if path.is_file()
    }
    if observed != expected:
        raise ValueError(
            f"existing resolved phase differs from deterministic rebuild: {destination}"
        )


def _publish_checkpoint(path: Path, value: JsonObject, *, resume: bool = False) -> Path:
    content = canonical_bytes(value)
    if path.exists():
        if not resume or path.read_bytes() != content:
            raise FileExistsError(f"identity checkpoint collision: {path}")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)
    return path


def _phase_files(
    generation_spec: Path,
    phase: str,
    output_root: Path,
    *,
    prelaunch_recovery_receipt: Path | None = None,
) -> tuple[str, dict[str, bytes]]:
    """Rebuild one phase completely in memory without publishing any path."""
    from er_commons.document_publication.config_generation.task06g_generation import (
        check_task06g_generation,
    )

    generation = load_object(generation_spec)
    if generation.get("schema_version") == "er_commons.task06g_generation.v1":
        check_task06g_generation(generation_spec)
    recipe_root, repository_root, artifact_root = _roots(generation_spec, generation)
    generator_refs = generation.get("generator_files")
    if generation.get("schema_version") == "er_commons.task06g_generation.v1":
        if not isinstance(generator_refs, list) or not all(
            isinstance(row, dict) and row.get("authority") == "repository" for row in generator_refs
        ):
            raise ValueError("generation recipe lacks repository generator references")
        for row in generator_refs:
            verify_reference(cast(JsonObject, row), root=repository_root)
    elif generation.get("schema_version") == "er_commons.task06g_collection_generation.v1":
        from er_commons.task06g.collection_generation import check_collection_generation

        check_collection_generation(generation_spec)
        if not isinstance(generator_refs, list) or not all(
            isinstance(row, dict) and row.get("authority") == "repository" for row in generator_refs
        ):
            raise ValueError("collection generation lacks repository generator references")
        for row in generator_refs:
            verify_reference(cast(JsonObject, row), root=repository_root)
    elif not isinstance(generator_refs, list):
        generator_refs = []
    definition = _phase_definition(generation, phase)
    directory, raw_entries = definition.get("directory"), definition.get("specs")
    if not isinstance(directory, str) or not isinstance(raw_entries, list):
        raise ValueError("phase requires directory and specs")
    if prelaunch_recovery_receipt is not None:
        recovery = load_object(prelaunch_recovery_receipt)
        generation_ref = recovery.get("generation_spec")
        process_inspection = recovery.get("process_inspection")
        if (
            recovery.get("schema_version") != "er_commons.task06g.prelaunch_recovery.v1"
            or recovery.get("status") != "accepted"
            or recovery.get("supervisor_started") is not False
            or recovery.get("replay_root") != str(output_root.resolve().parent)
            or recovery.get("initial_phase_state") not in {"absent", "published_exact"}
            or not isinstance(process_inspection, dict)
            or process_inspection.get("matching_processes") != []
            or process_inspection.get("tmux_session_live") is not False
            or not isinstance(generation_ref, dict)
        ):
            raise ValueError("prelaunch recovery receipt is not accepted")
        if verify_reference(generation_ref) != generation_spec.resolve():
            raise ValueError("prelaunch recovery receipt binds another generation spec")

    entries = list(raw_entries)
    files: dict[str, bytes] = {}
    receipts: list[JsonObject] = []
    memory: dict[str, JsonObject] = {}
    root_substitutions = (
        {
            "{artifact_root}": str(artifact_root),
            "{repository_root}": str(repository_root),
        }
        if generation.get("schema_version") == "er_commons.task06g_collection_generation.v1"
        else None
    )
    if phase == "initial" and generation.get("production_identity_recipe") is not None:
        collection_entry = next(
            cast(JsonObject, row)
            for row in entries
            if isinstance(row, dict) and row.get("destination") == "task06g_collection_v1.json"
        )
        entries.remove(collection_entry)
        name, content, receipt = _resolve_spec(
            collection_entry,
            recipe_root=recipe_root,
            repository_root=repository_root,
            artifact_root=artifact_root,
            generator_refs=cast(list[JsonObject], generator_refs),
        )
        files[name] = content
        receipt_name = f"receipts/{Path(name).name}.receipt.json"
        files[receipt_name] = canonical_bytes(receipt)
        receipts.append(content_reference(receipt_name, files[receipt_name]))
        identity, checkpoint = _production_identity(
            generation_spec,
            generation,
            content,
            repository_root=repository_root,
            artifact_root=artifact_root,
            output_root=output_root,
        )
        files["production_identity.json"] = canonical_bytes(identity)
        memory["pre_execution_production_identity"] = checkpoint
        files["pre_execution_production_identity_checkpoint.json"] = canonical_bytes(checkpoint)

    if phase == "initial" and generation.get("collection_production_identity_recipe") is not None:
        recipe = cast(JsonObject, generation["collection_production_identity_recipe"])
        imported_destination = recipe.get("imported_selection_destination")
        collection_destination = recipe.get("collection_spec_destination")
        if not isinstance(imported_destination, str) or not isinstance(collection_destination, str):
            raise ValueError("collection identity recipe lacks initial spec destinations")
        imported_entry = next(
            cast(JsonObject, row)
            for row in entries
            if isinstance(row, dict) and row.get("destination") == imported_destination
        )
        collection_entry = next(
            cast(JsonObject, row)
            for row in entries
            if isinstance(row, dict) and row.get("destination") == collection_destination
        )
        entries.remove(imported_entry)
        name, content, receipt = _resolve_spec(
            imported_entry,
            recipe_root=recipe_root,
            repository_root=repository_root,
            artifact_root=artifact_root,
            generator_refs=cast(list[JsonObject], generator_refs),
            root_substitutions=root_substitutions,
        )
        files[name] = content
        receipt_name = f"receipts/{Path(name).name}.receipt.json"
        files[receipt_name] = canonical_bytes(receipt)
        receipts.append(content_reference(receipt_name, files[receipt_name]))
        identity_name, identity, checkpoint = _collection_production_identity(
            generation_spec,
            generation,
            collection_entry=collection_entry,
            imported_selection_name=name,
            imported_selection_content=content,
            repository_root=repository_root,
            artifact_root=artifact_root,
            output_root=output_root,
        )
        files[identity_name] = canonical_bytes(identity)
        memory["pre_execution_collection_identity"] = checkpoint
        files["pre_execution_collection_identity_checkpoint.json"] = canonical_bytes(checkpoint)

    for raw in entries:
        if not isinstance(raw, dict):
            raise ValueError("phase spec entry must be an object")
        name, content, receipt = _resolve_spec(
            cast(JsonObject, raw),
            recipe_root=recipe_root,
            repository_root=repository_root,
            artifact_root=artifact_root,
            generator_refs=cast(list[JsonObject], generator_refs),
            memory=memory,
            root_substitutions=root_substitutions,
        )
        if name in files:
            raise ValueError(f"duplicate resolved destination: {name}")
        files[name] = content
        receipt_name = f"receipts/{Path(name).name}.receipt.json"
        files[receipt_name] = canonical_bytes(receipt)
        receipts.append(content_reference(receipt_name, files[receipt_name]))
    if phase == "relink":
        from er_commons.document_records.document_references.spec_preparation import (
            build_task06g_relink_specs,
        )

        link_entry = next(
            cast(JsonObject, row)
            for row in raw_entries
            if isinstance(row, dict) and row.get("destination") == "task06g_link_v1.json"
        )
        built = build_task06g_relink_specs(
            cast(JsonObject, json.loads(files["task06g_relink_preparation_v1.json"])),
            cast(JsonObject, json.loads(files["task06g_link_v1.json"])),
            repo_root=repository_root,
            data_root=artifact_root,
            link_schema=(recipe_root / str(link_entry["schema"])).resolve(),
        )
        if built["task06g_relink_preparation_v1.json"] != cast(
            JsonObject, json.loads(files["task06g_relink_preparation_v1.json"])
        ):
            raise ValueError("pure relink builder changed its resolved preparation")
        link_name = "task06g_link_v1.json"
        files[link_name] = canonical_bytes(built[link_name])
        receipt_name = f"receipts/{link_name}.receipt.json"
        receipt_value = json.loads(files[receipt_name])
        receipt_value["resolved"] = content_reference(link_name, files[link_name])
        receipt_value["pure_builder"] = "build_task06g_relink_specs"
        files[receipt_name] = canonical_bytes(receipt_value)
        receipts = [
            content_reference(receipt_name, files[receipt_name])
            if item.get("path") == receipt_name
            else item
            for item in receipts
        ]
    manifest: JsonObject = {
        "schema_version": "er_commons.task06g.resolved_phase.v1",
        "phase": phase,
        "directory": directory,
        "generation_spec": {
            "authority": "repository",
            **reference(generation_spec, root=repository_root),
        },
        "spec_count": len(raw_entries),
        "receipts": receipts,
        "external_checkpoints": [],
        "managed_files": [
            content_reference(path, content) for path, content in sorted(files.items())
        ],
    }
    files["phase_manifest.json"] = canonical_bytes(manifest)
    return directory, files


def verify_existing_phase(
    generation_spec: Path,
    phase: str,
    output_root: Path,
    *,
    prelaunch_recovery_receipt: Path | None = None,
) -> Path:
    """Read-only verify every byte of an already published deterministic phase."""
    directory, files = _phase_files(
        generation_spec,
        phase,
        output_root,
        prelaunch_recovery_receipt=prelaunch_recovery_receipt,
    )
    destination = output_root / directory
    _verify_existing(destination, files)
    return destination


def resolve_phase(
    generation_spec: Path,
    phase: str,
    output_root: Path,
    *,
    resume_existing: bool = False,
    prelaunch_recovery_receipt: Path | None = None,
) -> Path:
    """Build a complete phase, publish atomically, or verify exact resume reuse."""
    directory, files = _phase_files(
        generation_spec,
        phase,
        output_root,
        prelaunch_recovery_receipt=prelaunch_recovery_receipt,
    )
    destination = output_root / directory
    if destination.exists():
        if not resume_existing:
            raise FileExistsError(f"resolved phase already exists: {destination}")
        _verify_existing(destination, files)
        return destination
    publish_directory_no_clobber(destination, files)
    _verify_existing(destination, files)
    return destination


def publish_stage_checkpoint(
    generation_spec: Path,
    stage_key: str,
    completion_path: Path,
    checkpoint_path: Path,
    *,
    resume_existing: bool = False,
) -> Path:
    """Recompute a terminal document or handoff identity and seal its outputs."""
    generation = load_object(generation_spec)
    _, repository_root, artifact_root = _roots(generation_spec, generation)
    completion = load_object(completion_path)
    if completion.get("completion_last") is not True:
        raise ValueError(f"stage completion is not completion-last: {stage_key}")
    completion_ref = {
        "authority": "artifact_root",
        **reference(completion_path, root=artifact_root),
    }
    outputs: JsonObject
    if stage_key.startswith("document_"):
        candidate_root = completion_path.parents[1]
        identity = load_object(candidate_root / "records/document_identity.json")
        controls = {
            "hierarchy_disposition": identity["hierarchy_disposition"],
            "run_spec_sha256": identity["run_spec_sha256"],
            "stage_completions": identity["stage_completions"],
            "terminal_state": identity["terminal_state"],
        }
        if "resolved_spec_ref" in identity:
            controls["resolved_spec_ref"] = identity["resolved_spec_ref"]
        if "resolved_process_config_refs" in identity:
            controls["resolved_process_config_refs"] = identity["resolved_process_config_refs"]
        recomputed = build_candidate_id(
            production_extraction_id=str(identity["production_extraction_id"]),
            source_id=str(cast(JsonObject, identity["source"])["source_id"]),
            content_digest=str(identity["content_digest"]),
            control_digest=canonical_digest(controls),
        )
        derived_id = str(identity["candidate_id"])
        structured_ref = cast(
            JsonObject, cast(JsonObject, identity["stage_completions"])["structured_document"]
        )
        structured_path = (artifact_root / str(structured_ref["path"])).resolve()
        if (
            not structured_path.is_relative_to(artifact_root)
            or not structured_path.is_file()
            or sha256_file(structured_path) != structured_ref.get("sha256")
        ):
            raise ValueError("structured document completion seal differs")
        structured = load_object(structured_path)
        structured_root = structured_path.parents[1]
        outputs = {
            "source_document": {
                "candidate_id": derived_id,
                "root_relative_path": candidate_root.relative_to(artifact_root).as_posix(),
                "completion_ref": completion_ref,
                "inventory_ref": {
                    "authority": "artifact_root",
                    **reference(
                        candidate_root / "records/artifact_inventory.json", root=artifact_root
                    ),
                },
            },
            "structured_document": {
                "candidate_id": structured.get("extraction_id", structured_root.name),
                "completion_ref": {
                    "authority": "artifact_root",
                    **reference(structured_path, root=artifact_root),
                },
                "inventory_ref": {
                    "authority": "artifact_root",
                    **reference(
                        structured_root / "records/artifact_inventory.json", root=artifact_root
                    ),
                },
            },
        }
        replay_root = checkpoint_path.resolve().parents[2]
        if not replay_root.is_relative_to(artifact_root):
            raise ValueError("document checkpoint is outside the artifact root")
        initial = replay_root / "resolved_specs_v1/00_initial"
        resolved_initial_refs = {
            "document_publication_spec_ref": {
                "authority": "artifact_root",
                **reference(initial / "task06g_document_v1.json", root=artifact_root),
            },
            "collection_run_spec_ref": {
                "authority": "artifact_root",
                **reference(initial / "task06g_collection_v1.json", root=artifact_root),
            },
        }
        preimage: object = identity
    elif stage_key == "collection_handoff":
        if completion.get("status") != "ready":
            raise ValueError("replacement collection handoff is not ready")
        derived_id = str(completion["handoff_id"])
        preimage = completion["identity_preimage"]
        recomputed = build_collection_handoff_id(cast(JsonObject, preimage))
        handoff_root = completion_path.parents[1]
        collection_roots = [
            parent for parent in completion_path.parents if parent.name == "document_publications"
        ]
        if len(collection_roots) != 1:
            raise ValueError("handoff completion lacks one document-publications authority")
        collection_root = collection_roots[0]
        index_path = verify_reference(
            cast(JsonObject, completion["index_completion_ref"]), root=collection_root
        )
        resolution_path = verify_reference(
            cast(JsonObject, completion["resolution_completion_ref"]), root=collection_root
        )
        index, resolution = load_object(index_path), load_object(resolution_path)
        if index["index_id"] != build_record_target_index_id(index["identity_preimage"]):
            raise ValueError("target-index identity recomputation mismatch")
        if resolution["resolution_id"] != build_cross_document_link_id(
            resolution["identity_preimage"]
        ):
            raise ValueError("resolution identity recomputation mismatch")
        outputs = {
            "handoff_id": derived_id,
            "scope_id": completion["scope_id"],
            "target_index_id": index["index_id"],
            "resolution_id": resolution["resolution_id"],
            "handoff_completion_ref": completion_ref,
            "handoff_inventory_ref": {
                "authority": "artifact_root",
                **reference(handoff_root / "records/artifact_inventory.json", root=artifact_root),
            },
            "target_index_completion_ref": {
                "authority": "artifact_root",
                **reference(index_path, root=artifact_root),
            },
            "resolution_completion_ref": {
                "authority": "artifact_root",
                **reference(resolution_path, root=artifact_root),
            },
        }
    else:
        raise ValueError(f"unsupported checkpoint stage: {stage_key}")
    if derived_id != recomputed:
        raise ValueError(f"stage identity recomputation mismatch: {stage_key}")
    checkpoint: JsonObject = {
        "schema_version": "er_commons.task06g.identity_checkpoint.v1",
        "stage_key": stage_key,
        "recipe_checkpoint": {
            "authority": "repository",
            **reference(generation_spec, root=repository_root),
        },
        "stage_completion": completion_ref,
        "derived_id": derived_id,
        "identity_preimage": preimage,
        "recomputed_id": recomputed,
        "outputs": outputs,
        "verified": True,
    }
    if stage_key.startswith("document_"):
        checkpoint["resolved_initial_refs"] = resolved_initial_refs
    return _publish_checkpoint(checkpoint_path, checkpoint, resume=resume_existing)


def publish_checkpoint_inventory(
    checkpoint_root: Path,
    expected_names: list[str],
    *,
    resume_existing: bool = False,
) -> Path:
    """Close the exact explicitly ordered checkpoint set without discovery."""
    inventory_path = checkpoint_root / "inventory.json"
    observed = sorted(
        path.relative_to(checkpoint_root).as_posix()
        for path in checkpoint_root.rglob("*.json")
        if path != inventory_path
    )
    if observed != sorted(expected_names):
        raise ValueError("identity checkpoint set differs from frozen expected set")
    value: JsonObject = {
        "schema_version": "er_commons.task06g.identity_checkpoint_inventory.v1",
        "files": [
            reference(checkpoint_root / name, root=checkpoint_root) for name in expected_names
        ],
    }
    return _publish_checkpoint(inventory_path, value, resume=resume_existing)


def publish_aggregate(
    output_root: Path,
    phases: list[str],
    checkpoint_path: Path,
    *,
    process_checkpoint_names: list[str] | None = None,
    pre_execution_manifest_field: str = "pre_execution_production_identity_checkpoint",
    resume_existing: bool = False,
) -> Path:
    """Atomically close resolved phases and every identity checkpoint."""
    if pre_execution_manifest_field not in {
        "pre_execution_production_identity_checkpoint",
        "pre_execution_collection_identity_checkpoint",
    }:
        raise ValueError("unsupported pre-execution checkpoint manifest field")
    checkpoint_ref = reference(checkpoint_path, root=output_root)
    process_checkpoint_refs = [
        reference(output_root / name, root=output_root) for name in (process_checkpoint_names or [])
    ]
    manifest = {
        "schema_version": "er_commons.task06g.resolved_spec_manifest.v1",
        "phases": [
            reference(output_root / phase / "phase_manifest.json", root=output_root)
            for phase in phases
        ],
        pre_execution_manifest_field: checkpoint_ref,
        "process_identity_checkpoints": process_checkpoint_refs,
    }
    files = {"resolved_spec_manifest.json": canonical_bytes(manifest)}
    inventory = {
        "schema_version": "er_commons.task06g.resolved_spec_inventory.v1",
        "files": [content_reference(name, content) for name, content in files.items()],
        "external_files": [checkpoint_ref, *process_checkpoint_refs],
    }
    files["artifact_inventory.json"] = canonical_bytes(inventory)
    destination = output_root / "aggregate_v1"
    if destination.exists():
        if not resume_existing:
            raise FileExistsError(f"resolved aggregate already exists: {destination}")
        _verify_existing(destination, files)
        return destination
    publish_directory_no_clobber(destination, files)
    _verify_existing(destination, files)
    return destination


__all__ = [
    "publish_aggregate",
    "publish_checkpoint_inventory",
    "publish_stage_checkpoint",
    "resolve_phase",
    "verify_existing_phase",
]
