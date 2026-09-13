"""Deterministically freeze the repository-only collection recovery configuration."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.collection_processing.config import CollectionRunSpec
from er_commons.collection_processing.selection_models import ImportedDocumentSelection
from er_commons.task06g.collection_generation_owners import (
    collection_owner_paths,
    repository_control_ref,
)
from er_commons.task06g.collection_templates import (
    COLLECTION_NAME,
    COMPARISON_NAME,
    CONFIG,
    EXECUTION_NAME,
    GENERATION_NAME,
    HISTORICAL_CONFIG,
    INPUT,
    OUTPUT,
    PARENT,
    POLICIES,
    REPLAY,
    RESOLVED,
    SCHEMAS,
    SELECTION_NAME,
    collection_template,
    execution_template,
)
from er_commons.task06g.core import (
    JsonObject,
    canonical_bytes,
    content_reference,
    load_object,
    reference,
)

EXECUTION_SCHEMA = f"{SCHEMAS}/task06_recovery/v4/task06g_collection_execution.schema.json"
GENERATION_SCHEMA = f"{SCHEMAS}/task06_recovery/v4/task06g_collection_generation.schema.json"
COLLECTION_SCHEMA = f"{SCHEMAS}/collection_processing/v4/collection_run_spec.schema.json"
SELECTION_SCHEMA = f"{SCHEMAS}/task06_recovery/v1/imported_document_selection.schema.json"
COMPARISON_SCHEMA = f"{SCHEMAS}/task06_recovery/v1/task06g_template.schema.json"


def _entry(repository: Path, name: str, value: JsonObject, schema: str) -> JsonObject:
    """Bind a generated template to one exact schema and destination."""
    Draft202012Validator(load_object(repository / schema)).validate(value)
    return {
        "template": name,
        "destination": name,
        "schema": "../../../" + schema,
        "template_sha256": content_reference(name, canonical_bytes(value))["sha256"],
        "schema_sha256": reference(repository / schema)["sha256"],
        "generator": "task06g_collection_generation_v1",
        "resolutions": [],
    }


def build_collection_generation(repository: Path) -> dict[str, bytes]:
    """Build tracked controls without reading external evidence or allocating a run."""
    selection = load_object(repository / HISTORICAL_CONFIG / SELECTION_NAME)
    parsed = ImportedDocumentSelection.model_validate(selection)
    if (
        parsed.source_count != 35
        or sum(row.source_identity.pdf_page_count for row in parsed.candidates) != 49022
        or parsed.document_input_root_relative_path != INPUT
    ):
        raise ValueError("collection recovery requires the exact 35-source/49022-page v32 input")
    previous = load_object(repository / HISTORICAL_CONFIG / "task06g_collection_v1.json")
    if list(parsed.ordered_source_ids) != previous["source_ids"]:
        raise ValueError("imported selection differs from accepted Task04D source order")
    if [(row.logical_source_id, row.physical_source_id) for row in parsed.candidates] != [
        (row["logical_source_id"], row["physical_source_id"])
        for row in previous["source_membership"]
    ]:
        raise ValueError("imported selection differs from accepted mixed-lineage membership")
    selection_ref = {
        "authority": "artifact_root",
        **content_reference(f"{RESOLVED}/00_initial/{SELECTION_NAME}", canonical_bytes(selection)),
    }
    collection = collection_template(previous, selection, selection_ref)
    CollectionRunSpec.model_validate(collection)
    execution = execution_template(
        load_object(repository / HISTORICAL_CONFIG / "task06g_execution_v1.json")
    )
    comparison = deepcopy(
        load_object(repository / HISTORICAL_CONFIG / "task06g_comparison_v1.json")
    )
    comparison["artifact_relative_root"] = f"{REPLAY}/comparison_v1"
    values = {
        COLLECTION_NAME: collection,
        EXECUTION_NAME: execution,
        COMPARISON_NAME: comparison,
        SELECTION_NAME: selection,
    }
    recipe = _recipe(repository, values, selection)
    Draft202012Validator(load_object(repository / GENERATION_SCHEMA)).validate(recipe)
    return {
        f"{CONFIG}/{name}": canonical_bytes(value)
        for name, value in {**values, GENERATION_NAME: recipe}.items()
    }


def _phase_definitions(
    repository: Path, values: dict[str, JsonObject], selection: JsonObject
) -> JsonObject:
    """Bind exact initial identity fields and the single runtime handoff resolution."""
    initial = [
        _entry(repository, SELECTION_NAME, selection, SELECTION_SCHEMA),
        _entry(repository, COLLECTION_NAME, values[COLLECTION_NAME], COLLECTION_SCHEMA),
        _entry(repository, EXECUTION_NAME, values[EXECUTION_NAME], EXECUTION_SCHEMA),
    ]
    initial[1]["resolutions"] = [
        {
            "pointer": pointer,
            "source_pointer": source,
            "in_memory_checkpoint": "pre_execution_collection_identity",
        }
        for pointer, source in (
            ("/collection_production_id", "/derived_id"),
            ("/collection_production_identity_ref", "/identity_ref"),
            ("/imported_selection_ref", "/outputs/imported_selection_ref"),
        )
    ]
    comparison = _entry(repository, COMPARISON_NAME, values[COMPARISON_NAME], COMPARISON_SCHEMA)
    comparison["resolutions"] = [
        {
            "pointer": "/replacement_handoff_id",
            "source_pointer": "/derived_id",
            "checkpoint_authority": "artifact_root",
            "checkpoint": f"{REPLAY}/identity_checkpoints_v1/stages/collection_handoff.json",
        }
    ]
    return {
        "initial": {"directory": "00_initial", "specs": initial},
        "comparison": {"directory": "20_comparison", "specs": [comparison]},
    }


def _recipe(repository: Path, values: dict[str, JsonObject], selection: JsonObject) -> JsonObject:
    """Freeze sources, complete owner inventory, runtime allowlists, and finite bounds."""
    catalog_name = "task06g_source_family_catalog_v1.json"
    catalog_ref = {
        "authority": "artifact_root",
        **content_reference(
            f"{INPUT}/inputs/{catalog_name}",
            (repository / HISTORICAL_CONFIG / catalog_name).read_bytes(),
        ),
    }
    owners = [
        repository_control_ref(repository, path) for path in collection_owner_paths(repository)
    ]
    controls = [
        GENERATION_SCHEMA,
        EXECUTION_SCHEMA,
        COLLECTION_SCHEMA,
        SELECTION_SCHEMA,
        COMPARISON_SCHEMA,
        f"{SCHEMAS}/collection_processing/v3/records.schema.json",
        f"{HISTORICAL_CONFIG}/{SELECTION_NAME}",
        f"{HISTORICAL_CONFIG}/task06g_collection_v1.json",
        f"{HISTORICAL_CONFIG}/task06g_execution_v1.json",
        f"{HISTORICAL_CONFIG}/task06g_comparison_v1.json",
        f"{HISTORICAL_CONFIG}/{catalog_name}",
        f"{HISTORICAL_CONFIG}/{GENERATION_NAME}",
        "pyproject.toml",
        "uv.lock",
        *POLICIES,
    ]
    return {
        "schema_version": "er_commons.task06g_collection_generation.v1",
        "repository_root": "../../..",
        "data_root": "${ER_COMMONS_DATA_ROOT}",
        "accepted_repository_commit": "ff5613075c1e73d66e487381566e33dbfc6778f4",
        "tmux_session": "er-commons-06g-replay-v38",
        "initial_attempt_number": 20,
        "source_order": selection["ordered_source_ids"],
        "page_count": 49022,
        "generator_files": owners,
        "repository_control_refs": [
            repository_control_ref(repository, path) for path in sorted(controls)
        ],
        "collection_production_identity_recipe": {
            "schema_version": "er_commons.task06g.collection_production_identity_recipe.v1",
            "destination": "collection_production_identity.json",
            "collection_spec_destination": COLLECTION_NAME,
            "imported_selection_destination": SELECTION_NAME,
            "collection_output_namespace": OUTPUT,
            "source_catalog_ref": catalog_ref,
            "source_policy_refs": [repository_control_ref(repository, path) for path in POLICIES],
        },
        "namespaces": {
            "document_input_root": INPUT,
            "replay_root": REPLAY,
            "collection_output_root": OUTPUT,
            "recovery_root": f"{PARENT}/prelaunch_recovery_v38",
            "launch_root": f"{PARENT}/initial_launch_v38",
            "attempt_root": f"{PARENT}/execution_attempt_v20",
            "progress_root": f"{REPLAY}/collection_progress/attempt_v20",
            "log_path": f"{PARENT}/execution_attempt_v20/command.log",
        },
        "resource_policy": {
            "max_swap_growth_bytes": 0,
            "external_reserve_bytes": 67108864,
            "remaining_before_v38_bytes": 3844459676,
            "predicted_maximum_additional_bytes": 1443089302,
        },
        "phases": _phase_definitions(repository, values, selection),
    }


def generate_collection_configs(repository: Path, *, check: bool) -> tuple[str, ...]:
    """Validate the full v38 controls; the collection-only writer is retired."""
    full_recipe = repository.resolve() / CONFIG / "task06g_generation_v1.json"
    if full_recipe.is_file():
        if not check:
            raise ValueError("v38 full replay controls are frozen and check-only")
        from er_commons.document_publication.config_generation.task06g_generation import (
            check_task06g_generation,
        )

        check_task06g_generation(full_recipe)
        return tuple(
            f"{CONFIG}/{name}"
            for name in (
                "task06g_generation_v1.json",
                "task06g_document_v1.json",
                "task06g_collection_v1.json",
                "task06g_execution_v1.json",
                "task06g_relink_preparation_v1.json",
                "task06g_link_v1.json",
                "task06g_comparison_v1.json",
                "task06g_source_family_catalog_v1.json",
            )
        )
    products = build_collection_generation(repository.resolve())
    for relative, content in products.items():
        path = repository / relative
        if check:
            if not path.is_file() or path.read_bytes() != content:
                raise ValueError(f"frozen collection generation differs: {relative}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    return tuple(products)


def check_collection_generation(generation_spec: Path) -> tuple[str, ...]:
    """Require the named maintained recipe and exact deterministic repository closure."""
    if generation_spec.name == "task06g_generation_v1.json":
        repository = generation_spec.resolve().parents[3]
        if generation_spec.resolve() != repository / CONFIG / generation_spec.name:
            raise ValueError("historical full recipes cannot be checked as current generation")
        return generate_collection_configs(repository, check=True)
    if generation_spec.name != GENERATION_NAME:
        raise ValueError("collection generation requires its exact frozen recipe filename")
    repository = generation_spec.resolve().parents[3]
    if generation_spec.resolve() != repository / CONFIG / GENERATION_NAME:
        raise ValueError("historical collection recipes cannot be checked as current generation")
    return generate_collection_configs(repository, check=True)
