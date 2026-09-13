"""Portable, collection-only Task 06G command and namespace templates."""

from __future__ import annotations

from copy import deepcopy

from er_commons.task06g.core import JsonObject

CONFIG = "configs/task06/v4"
HISTORICAL_CONFIG = "configs/task06/v1"
SCHEMAS = "benchmarks/er_bench/schemas"
PARENT = "pipelines/brisbane_baylands/task_06_recovery_v1/06g"
INPUT = f"{PARENT}/replay_v32"
REPLAY = f"{PARENT}/replay_v38"
OUTPUT = f"{REPLAY}/document_publications"
RESOLVED = f"{REPLAY}/resolved_specs_v1"
GENERATION_NAME = "task06g_collection_generation_v1.json"
COLLECTION_NAME = "task06g_collection_only_v1.json"
EXECUTION_NAME = "task06g_collection_execution_v1.json"
COMPARISON_NAME = "task06g_collection_comparison_v1.json"
SELECTION_NAME = "task06g_imported_document_selection_v1.json"
IDENTITY_CHECKPOINT = "00_initial/pre_execution_collection_identity_checkpoint.json"
POLICIES = (
    "configs/brisbane_baylands_2025_deir_task03g2_resolution_policy_v1.json",
    "configs/brisbane_baylands_2025_deir_task03g2_target_policy_v1.json",
)
COMMAND_ORDER = (
    "assemble_handoff",
    "resolve_comparison_specs",
    "publish_comparison",
    "validate_handoff",
)
LIMITS = {
    "max_wall_seconds": 86400,
    "cpu_threads": 4,
    "max_rss_bytes": 10737418240,
    "max_output_bytes": 34359738368,
    "minimum_free_bytes": 68719476736,
}
PROHIBITED = [
    "pdf_open",
    "image_open",
    "image_render",
    "model_load",
    "conversion_execute",
    "extraction_execute",
    "preserved_payload_hash",
    "document_publish",
    "document_relink",
]


def _commands() -> list[JsonObject]:
    """Declare only collection assembly, comparison, and mechanical handoff validation."""
    artifact = "{artifact_root}/"
    repository = "{repository_root}/"
    checkpoint = artifact + f"{REPLAY}/identity_checkpoints_v1/stages/collection_handoff.json"
    return [
        {
            "stage": "assemble_handoff",
            "argv": [
                "uv",
                "run",
                "er-commons",
                "collections",
                "assemble-handoff",
                "--collection-spec",
                artifact + f"{RESOLVED}/00_initial/{COLLECTION_NAME}",
            ],
            "checkpoint_after": {
                "stage_key": "collection_handoff",
                "path": checkpoint,
                "completion_source": "stdout_handoff",
            },
        },
        {
            "stage": "resolve_comparison_specs",
            "argv": [
                "uv",
                "run",
                "python",
                "scripts/resolve_task06g_specs.py",
                "--generation-spec",
                repository + f"{CONFIG}/{GENERATION_NAME}",
                "--phase",
                "comparison",
                "--output-root",
                artifact + RESOLVED,
                "--resume-existing",
            ],
        },
        {
            "stage": "publish_comparison",
            "argv": [
                "uv",
                "run",
                "er-commons",
                "collections",
                "publish-task06g-comparison",
                "--comparison-spec",
                artifact + f"{RESOLVED}/20_comparison/{COMPARISON_NAME}",
            ],
        },
        {
            "stage": "validate_handoff",
            "argv": [
                "uv",
                "run",
                "er-commons",
                "collections",
                "validate-handoff",
                "--collection-root",
                artifact + OUTPUT,
                "--scope-id",
                "{scope_id}",
                "--schema",
                repository + f"{SCHEMAS}/collection_processing/v3/records.schema.json",
                "--document-input-root",
                artifact + INPUT,
            ],
            "runtime_values": [
                {"name": "scope_id", "checkpoint": checkpoint, "pointer": "/outputs/scope_id"}
            ],
        },
    ]


def execution_template(previous: JsonObject) -> JsonObject:
    """Freeze four commands, one handoff checkpoint, and all predecessor ledger roots."""
    artifact, repository = "{artifact_root}/", "{repository_root}/"
    historical = [
        artifact + str(path).split("/er_commons/", 1)[-1]
        for path in previous["ledger_sibling_roots"]
    ]
    historical += [
        artifact + f"{PARENT}/{name}"
        for name in (
            "prelaunch_recovery_v32",
            "replay_v32",
            "initial_launch_v32",
            "execution_attempt_v16",
            "prelaunch_recovery_v33",
            "replay_v33",
            "prelaunch_recovery_v34",
            "replay_v34",
            "prelaunch_recovery_v35",
            "replay_v35",
            "initial_launch_v35",
            "execution_attempt_v17",
        )
    ]
    return {
        "schema_version": "er_commons.task06g.collection_execution_template.v1",
        "repository_working_directory": "{repository_root}",
        "generation_spec": repository + f"{CONFIG}/{GENERATION_NAME}",
        "tmux_session": "er-commons-06g-replay-v38",
        "initial_attempt_number": 20,
        "command_order": list(COMMAND_ORDER),
        "commands": _commands(),
        "resource_limits": dict(LIMITS),
        "prohibited_operations": list(PROHIBITED),
        "ledger_sibling_roots": historical,
        "pre_execution_identity_checkpoint": IDENTITY_CHECKPOINT,
        "finalization_required_files": [
            "correspondence_v1/completion.json",
            "comparison_v1/completion.json",
            "identity_checkpoints_v1/inventory.json",
            "resolved_specs_v1/aggregate_v1/resolved_spec_manifest.json",
            "resolved_specs_v1/aggregate_v1/artifact_inventory.json",
        ],
        "resolver_closure": {
            "checkpoint_root": artifact + f"{REPLAY}/identity_checkpoints_v1",
            "checkpoint_files": ["stages/collection_handoff.json"],
            "resolved_specs_root": artifact + RESOLVED,
            "phase_directories": ["00_initial", "20_comparison"],
            "process_checkpoint_files": [],
            "pre_execution_identity_checkpoint": IDENTITY_CHECKPOINT,
            "pre_execution_manifest_field": "pre_execution_collection_identity_checkpoint",
            "collection_spec": artifact + f"{RESOLVED}/00_initial/{COLLECTION_NAME}",
        },
    }


def collection_template(
    previous: JsonObject, selection: JsonObject, selection_ref: JsonObject
) -> JsonObject:
    """Retain policies/membership while replacing document execution with exact import."""
    result = deepcopy(previous)
    del result["document_run_spec"]
    result.update(
        schema_version="er_commons.collection_run_spec.v4",
        document_evidence_mode="imported_downstream_selection",
        collection_output_relative_root=OUTPUT,
        collection_production_id="cprodv1-" + "0" * 64,
        collection_production_identity_ref={
            "authority": "artifact_root",
            "path": f"{RESOLVED}/00_initial/collection_production_identity.json",
            "sha256": "0" * 64,
            "byte_size": 0,
        },
        imported_document_root_relative_path=INPUT,
        imported_selection_ref=selection_ref,
        imported_document_run_spec_ref=selection["document_run_spec_ref"],
        imported_document_production_identity_ref=selection["document_production_identity_ref"],
    )
    return result
