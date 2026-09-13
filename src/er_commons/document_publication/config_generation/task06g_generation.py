"""Source-free validation for the frozen Task 06G generation recipe."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema  # type: ignore[import-untyped]

from er_commons.artifact_io import sha256_file
from er_commons.collection_processing.config import CollectionRunSpec
from er_commons.document_parsing.content_parsing.config import ContentParsingConfig
from er_commons.document_publication.config import DocumentRunSpec
from er_commons.document_records.document_references.config import DocumentReferenceConfig
from er_commons.document_records.document_references.relinking_config import DocumentLinkRunSpec
from er_commons.document_records.document_structure.config import DocumentStructureConfig
from er_commons.document_records.record_mapping.config import RecordMappingConfig
from er_commons.hierarchy_inference.config import HierarchyInferenceConfig


@dataclass(frozen=True)
class Task06GGenerationCheck:
    """Validated frozen paths and counts; validation never publishes artifacts."""

    template_count: int
    evidence_count: int
    source_count: int


_PHASE2_RUNTIME_OWNERS = {
    "benchmarks/er_bench/schemas/task06_recovery/v1/task06g_execution.schema.json",
    "benchmarks/er_bench/schemas/task06_recovery/v1/repeated_heading_decision_v2.schema.json",
    "benchmarks/er_bench/schemas/task06_recovery/v1/task06g_generation.schema.json",
    "configs/task06/v1/deir_appendix_a/repeated_heading_qualification_v2.json",
    "configs/task06/v1/deir_main/missing_chapter_extent_amendment_v4.json",
    "configs/task06/v1/deir_main/missing_chapter_v17_projection_validation.json",
    "docs/specs/repeated_heading_repair_v2.md",
    "scripts/generate_document_configs.py",
    "scripts/amend_task06e_child_extents.py",
    "scripts/prepare_document_relink_specs.py",
    "scripts/qualify_task06d_repeated_headings.py",
    "src/er_commons/authority_reference.py",
    "src/er_commons/cli.py",
    "src/er_commons/collection_processing/preflight.py",
    "src/er_commons/collection_processing/production_identity.py",
    "src/er_commons/collection_processing/source_membership.py",
    "src/er_commons/document_parsing/content_parsing/accepted_aggregate.py",
    "src/er_commons/document_parsing/content_parsing/application.py",
    "src/er_commons/document_parsing/content_parsing/config.py",
    "src/er_commons/document_parsing/content_parsing/configured_application.py",
    "src/er_commons/document_parsing/content_parsing/conversion_preflight.py",
    "src/er_commons/document_parsing/content_parsing/derived_publication.py",
    "src/er_commons/document_parsing/content_parsing/derived_publication_support.py",
    "src/er_commons/document_parsing/content_parsing/derived_route_reuse.py",
    "src/er_commons/document_parsing/content_parsing/evidence.py",
    "src/er_commons/document_parsing/content_parsing/identity.py",
    "src/er_commons/document_parsing/content_parsing/preparation.py",
    "src/er_commons/document_parsing/content_parsing/publication.py",
    "src/er_commons/document_parsing/content_parsing/sources.py",
    "src/er_commons/document_publication/accepted_inputs.py",
    "src/er_commons/document_publication/candidate_identity_validation.py",
    "src/er_commons/document_publication/candidates.py",
    "src/er_commons/document_publication/config.py",
    "src/er_commons/document_publication/config_generation/task06g_generation.py",
    "src/er_commons/document_publication/config_generation/workflow.py",
    "src/er_commons/document_publication/config_generation/process_templates.py",
    "src/er_commons/document_publication/config_generation/production_identity.py",
    "src/er_commons/document_publication/config_generation/shared.py",
    "src/er_commons/document_publication/config_generation/specifications.py",
    "src/er_commons/document_publication/document_processes.py",
    "src/er_commons/document_publication/fresh_preflight.py",
    "src/er_commons/document_publication/fresh_lineage.py",
    "src/er_commons/document_publication/input_preparation.py",
    "src/er_commons/document_publication/lineage_preflight.py",
    "src/er_commons/document_publication/lineage_validation.py",
    "src/er_commons/document_publication/preflight.py",
    "src/er_commons/document_publication/process_inputs.py",
    "src/er_commons/document_publication/process_sequence.py",
    "src/er_commons/document_publication/production_identity.py",
    "src/er_commons/document_publication/records.py",
    "src/er_commons/document_publication/storage.py",
    "src/er_commons/document_publication/worker.py",
    "src/er_commons/hierarchy_inference/code_inventory.py",
    "src/er_commons/hierarchy_inference/config.py",
    "src/er_commons/hierarchy_inference/inputs.py",
    "src/er_commons/hierarchy_inference/single_build.py",
    "src/er_commons/document_records/record_mapping/candidate_identity.py",
    "src/er_commons/document_records/record_mapping/inputs.py",
    "src/er_commons/document_records/record_mapping/materialize.py",
    "src/er_commons/source_release/retained_processing.py",
    "src/er_commons/document_records/document_references/preparation_spec.py",
    "src/er_commons/document_records/document_references/relink_preflight.py",
    "src/er_commons/document_records/document_references/fc1_equivalence.py",
    "src/er_commons/document_records/document_references/relink_publication.py",
    "src/er_commons/document_records/document_references/relinking.py",
    "src/er_commons/document_records/document_references/relinking_config.py",
    "src/er_commons/document_records/document_references/spec_preparation.py",
    "src/er_commons/document_records/document_structure/code_inventory.py",
    "src/er_commons/document_records/document_structure/comparison.py",
    "src/er_commons/document_records/document_structure/aliases.py",
    "src/er_commons/document_records/document_structure/construction.py",
    "src/er_commons/document_records/document_structure/constants.py",
    "src/er_commons/document_records/document_structure/identity.py",
    "src/er_commons/document_records/document_structure/missing_chapter_extent_amendment.py",
    "src/er_commons/document_records/document_structure/missing_chapter_projection.py",
    "src/er_commons/document_records/document_structure/missing_chapter_policy.py",
    "src/er_commons/document_records/document_structure/missing_chapter_qualification.py",
    "src/er_commons/document_records/document_structure/missing_chapters.py",
    "src/er_commons/document_records/document_structure/policies/bridge.py",
    "src/er_commons/document_records/document_structure/publication.py",
    "src/er_commons/document_records/document_structure/repeated_heading_policy.py",
    "src/er_commons/document_records/document_structure/repeated_heading_projection.py",
    "src/er_commons/document_records/document_structure/repeated_heading_qualification.py",
    "src/er_commons/document_records/document_structure/repeated_headings.py",
    "src/er_commons/document_records/document_structure/repeated_heading_correspondence.py",
    "src/er_commons/document_records/document_structure/sealing.py",
    "src/er_commons/document_records/document_structure/support.py",
    "src/er_commons/document_records/document_structure/validation.py",
}

_COLLECTION_ONLY_OWNERS = {
    "scripts/generate_task06g_collection_configs.py",
    "scripts/generate_task06g_imported_selection.py",
    "src/er_commons/task06g/collection_generation.py",
    "src/er_commons/task06g/collection_generation_owners.py",
    "src/er_commons/task06g/collection_templates.py",
}


def expected_task06g_generator_paths(repository_root: Path) -> set[str]:
    """Return the closed Phase 2 runtime owner set that must be byte-frozen."""
    task_modules = {
        path.relative_to(repository_root).as_posix()
        for path in (repository_root / "src/er_commons/task06g").glob("*.py")
    }
    task_scripts = {
        path.relative_to(repository_root).as_posix()
        for path in (repository_root / "scripts").glob("*task06g*.py")
    }
    return _PHASE2_RUNTIME_OWNERS | task_modules | task_scripts


_PRODUCER_RESOLUTION_PAIRS = {
    "record_mapping": [
        ("/producer_artifact_relative_root", "content_parsing", "/outputs/producer_root"),
        ("/producer_run_id", "content_parsing", "/derived_id"),
    ],
    "hierarchy_inference": [
        (
            "/producer_artifact_relative_root",
            "heading_evidence_parsing",
            "/outputs/producer_root",
        ),
        ("/producer_run_id", "heading_evidence_parsing", "/derived_id"),
    ],
}


def _validate_producer_resolution_pairs(runtime: object) -> None:
    """Verify that each downstream producer root and ID share one checkpoint owner."""
    if not isinstance(runtime, dict):
        raise ValueError("Task 06G process runtime resolutions must be an object")
    for role, required in _PRODUCER_RESOLUTION_PAIRS.items():
        raw = runtime.get(role)
        if not isinstance(raw, list) or any(not isinstance(item, dict) for item in raw):
            raise ValueError(f"Task 06G producer resolutions are malformed: {role}")
        observed = [
            (item.get("pointer"), item.get("source_stage"), item.get("source_pointer"))
            for item in raw
        ]
        if observed != required:
            raise ValueError(f"Task 06G producer root/ID authority pair differs: {role}")


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _contained(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Task 06G path escapes its authority: {value}")
    return path


def check_task06g_generation(generation_spec: Path) -> Task06GGenerationCheck:
    """Verify templates, compact evidence, source order, and repair boundaries."""
    recipe = _object(generation_spec)
    recipe_root = generation_spec.resolve().parent
    repository_root = (recipe_root / str(recipe["repository_root"])).resolve()
    data_root = (recipe_root / str(recipe["data_root"])).resolve()
    config_version = recipe_root.name
    process_config_version = "v4" if config_version == "v4" else "v1"
    schema_path = repository_root / (
        f"benchmarks/er_bench/schemas/task06_recovery/{config_version}/"
        "task06g_generation.schema.json"
    )
    jsonschema.Draft202012Validator(_object(schema_path)).validate(recipe)
    observed_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    if observed_commit != recipe["accepted_repository_commit"]:
        raise ValueError("Task 06G repository base commit differs from the accepted basis")

    source_order = tuple(str(item) for item in recipe["source_order"])
    if len(source_order) != 35 or source_order[9] != "feir_appendix_f1":
        raise ValueError("Task 06G source order must retain 35 slots with Final F1 at ordinal 10")
    if source_order[17] != "deir_appendix_a" or source_order[24] != "deir_main":
        raise ValueError("Task 06G repaired source ordinals differ from the accepted plan")

    evidence = recipe["accepted_evidence"]
    for item in evidence:
        authority = repository_root if item["authority"] == "repository" else data_root
        path = _contained(authority, str(item["path"]))
        if path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".pt"}:
            raise ValueError(f"Task 06G check cannot access source/model payloads: {path}")
        if sha256_file(path) != item["sha256"]:
            raise ValueError(f"accepted compact evidence differs: {item['name']}")
        if path.stat().st_size != item["byte_size"]:
            raise ValueError(f"accepted compact evidence size differs: {item['name']}")

    generator_paths = [str(item["path"]) for item in recipe["generator_files"]]
    expected_generators = expected_task06g_generator_paths(repository_root)
    if config_version == "v1":
        expected_generators -= _COLLECTION_ONLY_OWNERS
    if (
        len(generator_paths) != len(set(generator_paths))
        or set(generator_paths) != expected_generators
    ):
        missing = sorted(expected_generators - set(generator_paths))
        extra = sorted(set(generator_paths) - expected_generators)
        raise ValueError(f"Task 06G generator closure differs: missing={missing}, extra={extra}")
    for item in recipe["generator_files"]:
        if item["authority"] != "repository":
            raise ValueError("Task 06G generators must remain repository-authoritative")
        path = _contained(repository_root, str(item["path"]))
        if sha256_file(path) != item["sha256"] or path.stat().st_size != item["byte_size"]:
            raise ValueError(f"Task 06G generator differs: {item['path']}")

    identity_references = recipe.get("production_identity_recipe", {}).get("additional_references")
    if not isinstance(identity_references, dict):
        raise ValueError("Task 06G production identity references are absent")
    for section_name in ("document_process_contract", "collection_process_contract"):
        section = identity_references.get(section_name)
        if not isinstance(section, dict):
            raise ValueError(f"Task 06G production identity section differs: {section_name}")
        for role in ("artifacts", "owned_code"):
            references = section.get(role)
            if not isinstance(references, list) or not references:
                raise ValueError(f"Task 06G production identity references differ: {section_name}")
            for item in references:
                if not isinstance(item, dict) or item.get("authority") != "repository":
                    raise ValueError("Task 06G production identity authority differs")
                path = _contained(repository_root, str(item.get("path")))
                if sha256_file(path) != item.get("sha256") or path.stat().st_size != item.get(
                    "byte_size"
                ):
                    raise ValueError(f"Task 06G production identity reference differs: {path}")

    process_recipe = recipe["document_process_templates"]
    expected_roles = (
        "content_parsing",
        "heading_evidence_parsing",
        "record_mapping",
        "hierarchy_inference",
        "document_structure",
        "document_reference_linking",
    )
    if process_recipe["stage_order"] != list(expected_roles):
        raise ValueError("Task 06G process stage order differs")
    if set(process_recipe["sources"]) != {
        "feir_appendix_f1",
        "deir_appendix_a",
        "deir_main",
    }:
        raise ValueError("Task 06G process-template source closure differs")
    if set(process_recipe["runtime_resolutions"]) != set(expected_roles):
        raise ValueError("Task 06G process resolution closure differs")
    _validate_producer_resolution_pairs(process_recipe["runtime_resolutions"])
    for source_id, process_templates in process_recipe["sources"].items():
        if set(process_templates) != set(expected_roles):
            raise ValueError(f"Task 06G process template roles differ: {source_id}")
        for role, item in process_templates.items():
            path = _contained(repository_root, str(item["template"]))
            if item["loader"] != role:
                raise ValueError(f"Task 06G process loader differs: {source_id}/{role}")
            if sha256_file(path) != item["template_sha256"]:
                raise ValueError(f"Task 06G process template differs: {source_id}/{role}")
            if path.stat().st_size != item["template_byte_size"]:
                raise ValueError(f"Task 06G process template size differs: {source_id}/{role}")
    expected_resolutions = {
        "content_parsing": [],
        "heading_evidence_parsing": [],
        "record_mapping": _PRODUCER_RESOLUTION_PAIRS["record_mapping"],
        "hierarchy_inference": _PRODUCER_RESOLUTION_PAIRS["hierarchy_inference"],
        "document_structure": [
            ("/baseline_candidate_relative_root", "record_mapping", "/outputs/candidate_root"),
            ("/baseline_candidate_id", "record_mapping", "/derived_id"),
            (
                "/baseline_producer_relative_root",
                "content_parsing",
                "/outputs/producer_root",
            ),
            ("/baseline_producer_run_id", "content_parsing", "/derived_id"),
            (
                "/hierarchy_producer_relative_root",
                "heading_evidence_parsing",
                "/outputs/producer_root",
            ),
            ("/hierarchy_producer_run_id", "heading_evidence_parsing", "/derived_id"),
            (
                "/hierarchy_candidate_relative_root",
                "hierarchy_inference",
                "/outputs/candidate_root",
            ),
            ("/hierarchy_candidate_id", "hierarchy_inference", "/derived_id"),
        ],
        "document_reference_linking": [
            (
                "/artifact_relative_root",
                "document_structure",
                "/outputs/artifact_root",
            ),
            ("/upstream_candidate_id", "document_structure", "/derived_id"),
            (
                "/upstream_completion_sha256",
                "document_structure",
                "/stage_completion/sha256",
            ),
            (
                "/upstream_inventory_sha256",
                "document_structure",
                "/stage_inventory/sha256",
            ),
        ],
    }
    observed_resolutions = {
        role: [
            (item.get("pointer"), item.get("source_stage"), item.get("source_pointer"))
            for item in resolutions
            if isinstance(item, dict)
        ]
        for role, resolutions in process_recipe["runtime_resolutions"].items()
    }
    if observed_resolutions != expected_resolutions:
        raise ValueError("Task 06G process resolution allowlist differs")

    templates: dict[str, dict[str, Any]] = {}
    entries = [entry for phase in recipe["phases"].values() for entry in phase["specs"]]
    for entry in entries:
        template_path = _contained(recipe_root, str(entry["template"]))
        schema = (recipe_root / str(entry["schema"])).resolve()
        if not schema.is_relative_to(repository_root):
            raise ValueError(f"template schema escapes repository: {entry['schema']}")
        if sha256_file(template_path) != entry["template_sha256"]:
            raise ValueError(f"frozen template digest differs: {entry['template']}")
        if sha256_file(schema) != entry["schema_sha256"]:
            raise ValueError(f"frozen template schema differs: {entry['schema']}")
        value = _object(template_path)
        jsonschema.Draft202012Validator(_object(schema)).validate(value)
        templates[str(entry["template"])] = value
        pointers = [str(item["pointer"]) for item in entry["resolutions"]]
        if len(pointers) != len(set(pointers)) or any("*" in pointer for pointer in pointers):
            raise ValueError(f"runtime resolution must use unique exact pointers: {template_path}")

    DocumentRunSpec.model_validate(templates["task06g_document_v1.json"])
    CollectionRunSpec.model_validate(templates["task06g_collection_v1.json"])
    DocumentLinkRunSpec.model_validate(templates["task06g_link_v1.json"])
    for source_id in ("feir_appendix_f1", "deir_appendix_a", "deir_main"):
        DocumentStructureConfig.model_validate(
            _object(
                repository_root
                / f"configs/task06/{process_config_version}/{source_id}/document_structure.json"
            )
        )
    for name in ("content_parsing", "heading_evidence_parsing"):
        ContentParsingConfig.model_validate(
            _object(
                repository_root
                / f"configs/task06/{process_config_version}/feir_appendix_f1/{name}.json"
            )
        )

    catalog_value = _object(
        repository_root / "configs/task06/v1/task06g_source_family_catalog_v1.json"
    )
    catalog_sources = catalog_value.get("sources")
    if not isinstance(catalog_sources, list):
        raise ValueError("Task 06G source-family catalog lacks source rows")
    catalog_order = [str(item["source"]["source_id"]) for item in catalog_sources]
    if catalog_order != list(source_order):
        raise ValueError("Task 06G source-family catalog differs from selected source order")
    final_f1 = catalog_sources[9]["source"]
    if (
        final_f1.get("sha256") != "e13c5b53f0f4da6a91f52ac784acce06619eeffd3fe053542d7ce1593b957e5e"
        or final_f1.get("pdf_page_count") != 756
    ):
        raise ValueError("Task 06G source-family catalog does not select accepted Final F1")
    f1_root = repository_root / f"configs/task06/{process_config_version}/feir_appendix_f1"
    RecordMappingConfig.model_validate(_object(f1_root / "record_mapping.json"))
    HierarchyInferenceConfig.model_validate(_object(f1_root / "hierarchy_inference.json"))
    catalog_path = repository_root / "configs/task06/v1/task06g_source_family_catalog_v1.json"
    catalog_digest = sha256_file(catalog_path)
    for source_id in ("feir_appendix_f1", "deir_appendix_a", "deir_main"):
        link_config = DocumentReferenceConfig.load(
            repository_root
            / f"configs/task06/{process_config_version}/{source_id}/document_reference_linking.json"
        )
        if link_config.source_family_catalog_sha256 != catalog_digest:
            raise ValueError(f"Task 06G local link catalog differs: {source_id}")

    document = templates["task06g_document_v1.json"]
    fresh = [
        row["source_id"]
        for row in document["document_processes"]
        if row["lineage_mode"] == "fresh_build"
    ]
    if fresh != ["feir_appendix_f1", "deir_appendix_a", "deir_main"]:
        raise ValueError("only the three accepted document descendants may be fresh builds")
    fresh_rows = {
        row["source_id"]: row
        for row in document["document_processes"]
        if row["lineage_mode"] == "fresh_build"
    }
    expected_resume = {
        "feir_appendix_f1": ("heading_evidence_parsing", {"content_parsing"}),
        "deir_appendix_a": (
            "document_structure",
            {
                "content_parsing",
                "heading_evidence_parsing",
                "record_mapping",
                "hierarchy_inference",
            },
        ),
        "deir_main": (
            "document_structure",
            {
                "content_parsing",
                "heading_evidence_parsing",
                "record_mapping",
                "hierarchy_inference",
            },
        ),
    }
    for source_id, (stage, roles) in expected_resume.items():
        row = fresh_rows[source_id]
        if row.get("resume_stage") != stage or set(row.get("reused_completions", {})) != roles:
            raise ValueError(f"Task 06G resume boundary differs: {source_id}")
        for reference in row["reused_completions"].values():
            if reference["authority"] != "artifact_root" or reference["byte_size"] <= 0:
                raise ValueError(f"Task 06G reused completion is not frozen: {source_id}")
    link = templates["task06g_link_v1.json"]
    if link.get("figure_alias_source_ids") != ["deir_main"]:
        raise ValueError("FC1 publication authority must remain deir_main only")
    fc1 = link.get("accepted_fc1_evidence")
    expected_fc1_roles = {
        "completion_ref",
        "inventory_ref",
        "identity_ref",
        "qualification_ref",
        "figure_aliases_ref",
        "target_index_entries_ref",
    }
    if (
        not isinstance(fc1, dict)
        or fc1.get("source_id") != "deir_main"
        or fc1.get("qualification_id")
        != "figqualv1-4c8002030423eaf6714ca5fb98ee3926d6cfda030d4cae3cfc367f0959ad8b14"
        or set(fc1) - {"qualification_id", "source_id"} != expected_fc1_roles
    ):
        raise ValueError("accepted FC1 evidence closure differs")
    execution = templates["task06g_execution_v1.json"]
    replay_version = "v38" if config_version == "v4" else "v32"
    if recipe.get("tmux_session") != f"er-commons-06g-replay-{replay_version}" or execution.get(
        "tmux_session"
    ) != recipe.get("tmux_session"):
        raise ValueError("Task 06G tmux binding differs")
    expected_max_output = (52 if config_version == "v4" else 32) * 1024**3
    if execution.get("resource_limits", {}).get("max_output_bytes") != expected_max_output:
        raise ValueError("Task 06G output resource limit differs")
    expected_ledger_roots = {
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v2",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v2",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v3",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v3",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v4",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v4",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v5",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v5",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v6",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v6",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v6",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v1",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v7",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v7",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v7",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v2",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v8",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v9",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v9",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v9",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v3",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v10",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v10",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v11",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v11",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v11",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v4",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_re_v12",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v12",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v12",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v12",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v5",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v13",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v13",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v14",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v14",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v14",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v6",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v15",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v15",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v16",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v16",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v16",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v7",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v17",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v17",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v18",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v18",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v18",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v8",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v19",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v19",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v19",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v9",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v20",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v20",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v20",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v10",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v21",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v22",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v22",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v22",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v11",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v23",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v23",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v24",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v24",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v24",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v12",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v25",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v25",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v25",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v13",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/diagnostic_v25_main_relink",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/diagnostic_v25_main_relink_2",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v26",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v26",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/diagnostic_v26_main_schema_gate",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v27",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v27",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v27",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v14",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/diagnostic_v27_g2_sandbox",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v28",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v28",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/initial_launch_v28",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/execution_attempt_v15",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v29",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v29",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v30",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v30",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
        "task_06_recovery_v1/06g/prelaunch_recovery_v31",
        "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v31",
    }
    if config_version == "v4":
        parent = "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g"
        expected_ledger_roots.update(
            {
                f"{parent}/prelaunch_recovery_v32",
                f"{parent}/replay_v32",
                f"{parent}/initial_launch_v32",
                f"{parent}/execution_attempt_v16",
                f"{parent}/prelaunch_recovery_v33",
                f"{parent}/replay_v33",
                f"{parent}/prelaunch_recovery_v34",
                f"{parent}/replay_v34",
                f"{parent}/prelaunch_recovery_v35",
                f"{parent}/replay_v35",
                f"{parent}/initial_launch_v35",
                f"{parent}/execution_attempt_v17",
                f"{parent}/prelaunch_recovery_v36",
                f"{parent}/replay_v36",
                f"{parent}/prelaunch_recovery_v37",
                f"{parent}/replay_v37",
                f"{parent}/initial_launch_v37",
                f"{parent}/execution_attempt_v19",
            }
        )
    if set(execution.get("ledger_sibling_roots", [])) != expected_ledger_roots:
        raise ValueError("Task 06G preserved-evidence ledger differs")
    closure = execution.get("resolver_closure")
    stage_order = [
        "content_parsing",
        "heading_evidence_parsing",
        "record_mapping",
        "hierarchy_inference",
        "document_structure",
        "document_reference_linking",
    ]
    process_phases = [
        f"document_stages/{source_id}/{ordinal:02d}_{stage}"
        for source_id in ("feir_appendix_f1", "deir_appendix_a", "deir_main")
        for ordinal, stage in enumerate(stage_order, start=1)
    ]
    process_checkpoints = [
        phase.replace("document_stages/", "document_stage_checkpoints_v1/") + ".json"
        for phase in process_phases
    ]
    if not isinstance(closure, dict) or closure.get("phase_directories") != [
        "00_initial",
        *process_phases,
        "10_relink",
        "20_comparison",
    ]:
        raise ValueError("Task 06G resolved phase closure differs")
    if closure.get("process_checkpoint_files") != process_checkpoints:
        raise ValueError("Task 06G process checkpoint closure differs")
    return Task06GGenerationCheck(len(entries), len(evidence), len(source_order))


__all__ = ["Task06GGenerationCheck", "check_task06g_generation"]
