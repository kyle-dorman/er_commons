"""Prepare the fresh Task 03J v4 namespace without reading PDFs or models."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.collection_processing.config import load_collection_run_spec
from er_commons.document_publication.config import load_document_run_spec
from er_commons.document_publication.fresh_preflight import validate_fresh_build_templates
from er_commons.document_publication.preflight import build_production_scope_evidence
from er_commons.document_publication.process_inputs import (
    ProcessConfigs,
    verify_process_resource_contract,
)
from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.settings import load_settings
from er_commons.source_family_catalog import SourceFamilyCatalog

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = load_settings().data_root.resolve()
DOCUMENT_SPEC = PROJECT_ROOT / "configs/brisbane_baylands_2025_deir_task03h_document_v4.json"
COLLECTION_SPEC = PROJECT_ROOT / "configs/brisbane_baylands_2025_deir_task03h_collection_v4.json"
IDENTITY = (
    PROJECT_ROOT
    / "benchmarks/er_bench/fixtures/document_publication/v4/task03h_production_identity.json"
)
CATALOG = PROJECT_ROOT / (
    "configs/brisbane_baylands_2025_deir_task03h_v4_source_family_catalog_v1.json"
)
TASK_ROOT = Path("pipelines/brisbane_baylands/task_03h_clean_full_v4")
CATALOG_RELATIVE = Path(
    "pipelines/brisbane_baylands/task_03h_clean_full_v4/inputs/"
    "brisbane_baylands_2025_deir_task03h_v4_source_family_catalog_v1.json"
)
SCHEMAS = {
    "document": PROJECT_ROOT
    / "benchmarks/er_bench/schemas/document_publication/v2/document_run_spec.schema.json",
    "collection": PROJECT_ROOT
    / "benchmarks/er_bench/schemas/collection_processing/v2/collection_run_spec.schema.json",
    "identity": PROJECT_ROOT
    / "benchmarks/er_bench/schemas/document_publication/v2/production_identity.schema.json",
}


def main() -> None:
    """Validate and stage the v4 source-free run boundary."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--resume-existing-v4",
        action="store_true",
        help="Restage identity evidence for a repaired v4 run using only validated caches.",
    )
    args = parser.parse_args()
    document, document_digest = load_document_run_spec(DOCUMENT_SPEC)
    collection, collection_digest = load_collection_run_spec(COLLECTION_SPEC)
    identity = _object(IDENTITY)
    for name, path in SCHEMAS.items():
        Draft202012Validator(_object(path)).validate(
            _object(
                DOCUMENT_SPEC
                if name == "document"
                else COLLECTION_SPEC
                if name == "collection"
                else IDENTITY
            )
        )
    task_root_exists = (DATA_ROOT / TASK_ROOT).exists()
    if task_root_exists and not args.resume_existing_v4:
        raise ValueError(f"fresh v4 namespace already exists: {DATA_ROOT / TASK_ROOT}")
    if args.resume_existing_v4 and not task_root_exists:
        raise ValueError(f"repaired v4 namespace does not exist: {DATA_ROOT / TASK_ROOT}")
    source_ids, scope = build_production_scope_evidence(
        spec=document, identity=identity, data_root=DATA_ROOT
    )
    if source_ids != list(collection.source_ids):
        raise ValueError("v4 document and collection source scopes differ")
    validated = validate_production_identity(
        identity,
        expected_source_ids=source_ids,
        expected_scope=scope,
        expected_scope_kind="production_full",
        project_root=PROJECT_ROOT,
    )
    if validated.value != document.production_extraction_id:
        raise ValueError("v4 document spec differs from its production identity")
    _validate_configs(document)
    if collection.source_family_catalog_relative_path != CATALOG_RELATIVE:
        raise ValueError("v4 collection catalog path is not fresh")
    destination = DATA_ROOT / CATALOG_RELATIVE
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(CATALOG, destination)
    SourceFamilyCatalog.load(destination)
    manifest = _object(DATA_ROOT / document.source_manifest_relative_path)
    sources = [item for item in manifest["sources"] if item.get("source_role") == "model_corpus"]
    sources_by_id = {item["source_id"]: item for item in sources}
    activation_plan = {
        "schema_version": "er_commons.task03j_activation_plan.v1",
        "run_label": "task03j_final_v4",
        "production_extraction_id": validated.value,
        "document_spec": {
            "path": DOCUMENT_SPEC.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": document_digest,
        },
        "collection_spec": {
            "path": COLLECTION_SPEC.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": collection_digest,
        },
        "production_identity": {
            "path": IDENTITY.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": sha256_file(IDENTITY),
        },
        "fresh_artifact_root": TASK_ROOT.as_posix(),
        "source_order": [
            {
                "ordinal": ordinal,
                "source_id": source_id,
                "pdf_page_count": sources_by_id[source_id]["pdf_page_count"],
                "byte_size": sources_by_id[source_id]["byte_size"],
            }
            for ordinal, source_id in enumerate(source_ids, start=1)
        ],
        "execution_policy": {
            "document_concurrency": document.resource_policy.document_concurrency,
            "cpu_threads_per_document": document.resource_policy.cpu_threads_per_document,
            "chunk_target_pages": 225,
            "chunk_hard_maximum_pages": 275,
            "chunk_overlap_pages": 1,
            "range_rss_limit_bytes": 20 * 1024**3,
            "aggregate_rss_limit_bytes": 20 * 1024**3,
            "per_process_wall_limit_seconds": 14_400,
            "retry_limit_per_source": document.resource_policy.retry_limit,
            "disk_budget_bytes": document.resource_policy.storage_estimate_bytes,
        },
        "forecast": {
            "planning_rate_seconds_per_page_per_producer": 0.55,
            "producer_page_passes": sum(item["pdf_page_count"] for item in sources) * 2,
            "conversion_floor_seconds": sum(item["pdf_page_count"] for item in sources) * 2 * 0.55,
            "eta_method": (
                "update from observed per-document critical path after each terminal source"
            ),
        },
        "failure_behavior": {
            "ordinary_source_failure": (
                "retain terminal failure evidence and continue to the next ordered source"
            ),
            "hard_stop_conditions": [
                "resource guard breach",
                "identity or lineage mismatch",
                "semantic loss or invariant failure",
                "publication or checksum failure",
                "main-report material failure",
            ],
            "collection_policy": "all_sources_successful",
        },
        "source_pdf_bytes_read": False,
        "model_files_read": False,
    }
    if args.resume_existing_v4:
        activation_plan["resume_policy"] = {
            "mode": "repaired_v4_identity",
            "reuse": "only checksum-validated deterministic stage components",
            "prior_identity_terminal_evidence": False,
        }
    write_json_atomic(destination.parent / "task03j_activation_plan.json", activation_plan)
    readiness = {
        "schema_version": "er_commons.task03j_preparation_readiness.v1",
        "status": (
            "ready_for_authorized_repaired_rerun"
            if args.resume_existing_v4
            else "ready_for_user_authorized_clean_run"
        ),
        "run_label": "task03j_final_v4",
        "production_extraction_id": validated.value,
        "production_identity_sha256": sha256_file(IDENTITY),
        "document_run_spec_sha256": document_digest,
        "collection_run_spec_sha256": collection_digest,
        "source_scope": {
            "source_count": len(source_ids),
            "page_count": sum(item["pdf_page_count"] for item in sources),
            "byte_count": sum(item["byte_size"] for item in sources),
            "ordered_source_ids": source_ids,
            "manifest_warning_count": sum(len(item.get("warnings", [])) for item in sources),
        },
        "freshness": {
            "task_root": TASK_ROOT.as_posix(),
            "completed_candidate_markers": [],
            "historical_lineage_pins": [],
            "existing_v4_root_reused": args.resume_existing_v4,
        },
        "source_pdf_bytes_read": False,
        "model_files_read": False,
        "producer_identity_derivation_run": False,
        "activation_plan_relative_path": "task03j_activation_plan.json",
    }
    write_json_atomic(destination.parent / "task03j_preparation_readiness.json", readiness)
    print(destination.parent / "task03j_preparation_readiness.json")


def _validate_configs(document: Any) -> None:
    """Validate every v4 process config and its fresh-build contract."""
    if len(document.document_processes) != 35:
        raise ValueError("v4 must configure exactly 35 sources")
    seen: set[Path] = set()
    for selection in document.document_processes:
        paths = {
            role: (PROJECT_ROOT / path).resolve()
            for role, path in selection.configs.model_dump().items()
        }
        if any(
            not path.is_relative_to(PROJECT_ROOT) or not path.is_file() for path in paths.values()
        ):
            raise FileNotFoundError(f"v4 process config is missing: {selection.source_id}")
        if seen.intersection(paths.values()):
            raise ValueError("v4 process config is reused across source selections")
        seen.update(paths.values())
        configs = ProcessConfigs(**paths)
        validate_fresh_build_templates(
            configs=configs,
            source_id=selection.source_id,
            disposition=document.hierarchy_disposition(selection.source_id),
            data_root=DATA_ROOT,
        )
        verify_process_resource_contract(configs, document)
    if len(seen) != 210:
        raise ValueError(f"v4 must seal exactly 210 process configs: {len(seen)}")


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


if __name__ == "__main__":
    main()
