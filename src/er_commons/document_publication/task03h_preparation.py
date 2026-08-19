"""Stage and audit Task 03H inputs without reading source PDF or model bytes."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.collection_processing.config import CollectionRunSpec, load_collection_run_spec
from er_commons.collection_processing.preflight import prepare_collection_run
from er_commons.document_publication.config import DocumentRunSpec, load_document_run_spec
from er_commons.document_publication.fresh_preflight import validate_fresh_build_templates
from er_commons.document_publication.preflight import build_production_scope_evidence
from er_commons.document_publication.process_inputs import (
    ProcessConfigs,
    verify_process_resource_contract,
)
from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.source_family_catalog import SourceFamilyCatalog

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOCUMENT_SPEC = PROJECT_ROOT / "configs/brisbane_baylands_2025_deir_task03h_document_v2.json"
COLLECTION_SPEC = PROJECT_ROOT / "configs/brisbane_baylands_2025_deir_task03h_collection_v2.json"
CATALOG = PROJECT_ROOT / "configs/brisbane_baylands_2025_deir_task03h_source_family_catalog_v1.json"
TARGET_POLICY = PROJECT_ROOT / "configs/brisbane_baylands_2025_deir_task03g2_target_policy_v1.json"
RESOLUTION_POLICY = (
    PROJECT_ROOT / "configs/brisbane_baylands_2025_deir_task03g2_resolution_policy_v1.json"
)
TASK_ROOT = Path("pipelines/brisbane_baylands/task_03h")
SCHEMAS = {
    "document": PROJECT_ROOT
    / "benchmarks/er_bench/schemas/document_publication/v2/document_run_spec.schema.json",
    "collection": PROJECT_ROOT
    / "benchmarks/er_bench/schemas/collection_processing/v2/collection_run_spec.schema.json",
    "identity": PROJECT_ROOT
    / "benchmarks/er_bench/schemas/document_publication/v2/production_identity.schema.json",
}


@dataclass(frozen=True)
class SourceScope:
    """Manifest-derived readiness counts and retained warning evidence."""

    ordered_source_ids: list[str]
    page_count: int
    byte_count: int
    warning_count: int
    edition_override: str

    def as_record(self) -> dict[str, Any]:
        """Return the persisted source-scope evidence."""
        return {
            "source_count": len(self.ordered_source_ids),
            "page_count": self.page_count,
            "byte_count": self.byte_count,
            "ordered_source_ids": self.ordered_source_ids,
            "manifest_warning_count": self.warning_count,
            "k2_part_2_source_edition_override": self.edition_override,
        }


def prepare_task03h(data_root: Path) -> Path:
    """Stage the exact catalog and publish a source/model-free readiness report."""
    data_root = data_root.resolve()
    document, document_sha256 = load_document_run_spec(DOCUMENT_SPEC)
    collection, collection_sha256 = load_collection_run_spec(COLLECTION_SPEC)
    identity_path = (PROJECT_ROOT / document.production_identity_relative_path).resolve()
    identity = _object(identity_path)
    _validate_schemas(identity)
    staged_catalog = _stage_catalog(data_root, collection.source_family_catalog_relative_path)

    source_ids, scope_evidence = build_production_scope_evidence(
        spec=document,
        identity=identity,
        data_root=data_root,
    )
    if source_ids != list(collection.source_ids):
        raise ValueError("Task 03H document and collection source scopes differ")
    validated = validate_production_identity(
        identity,
        expected_source_ids=source_ids,
        expected_scope=scope_evidence,
        expected_scope_kind="production_full",
        project_root=PROJECT_ROOT,
    )
    if validated.value != document.production_extraction_id:
        raise ValueError("Task 03H document spec differs from its production identity")
    config_refs = _validate_process_configs(document, data_root)
    collection_run = prepare_collection_run(data_root, COLLECTION_SPEC)
    if collection_run.document_spec.production_extraction_id != validated.value:
        raise ValueError("Task 03H collection resolves another production identity")
    _validate_policy_hashes(collection)

    completion_markers = _completed_candidate_markers(data_root)
    if completion_markers:
        raise ValueError("Task 03H namespace already contains completed candidates")

    source_scope = _source_scope(data_root / document.source_manifest_relative_path)
    if source_scope.ordered_source_ids != source_ids:
        raise ValueError("Task 03H readiness scope differs from production scope")
    report_path = staged_catalog.parent / "task03h_preparation_readiness.json"
    _write_readiness_report(
        report_path=report_path,
        identity_path=identity_path,
        extraction_id=validated.value,
        document=document,
        document_sha256=document_sha256,
        collection=collection,
        collection_sha256=collection_sha256,
        source_scope=source_scope,
        config_refs=config_refs,
        completion_markers=completion_markers,
    )
    return report_path


def _validate_schemas(identity: dict[str, Any]) -> None:
    values = {
        "document": _object(DOCUMENT_SPEC),
        "collection": _object(COLLECTION_SPEC),
        "identity": identity,
    }
    for name, value in values.items():
        Draft202012Validator(_object(SCHEMAS[name])).validate(value)


def _stage_catalog(data_root: Path, relative_path: Path) -> Path:
    destination = (data_root / relative_path).resolve()
    if not destination.is_relative_to(data_root):
        raise ValueError("Task 03H catalog path escapes the data root")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() != CATALOG.read_bytes():
            raise FileExistsError("staged Task 03H catalog differs from checked-in bytes")
    else:
        shutil.copyfile(CATALOG, destination)
    SourceFamilyCatalog.load(destination)
    return destination


def _validate_process_configs(document: DocumentRunSpec, data_root: Path) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for selection in document.document_processes:
        paths = {
            role: (PROJECT_ROOT / path).resolve()
            for role, path in selection.configs.model_dump().items()
        }
        if any(
            not path.is_relative_to(PROJECT_ROOT) or not path.is_file() for path in paths.values()
        ):
            raise FileNotFoundError("Task 03H process config is missing or uncontained")
        if seen.intersection(paths.values()):
            raise ValueError("Task 03H process config is reused across source selections")
        seen.update(paths.values())
        configs = ProcessConfigs(**paths)
        validate_fresh_build_templates(
            configs=configs,
            source_id=selection.source_id,
            disposition=document.hierarchy_disposition(selection.source_id),
            data_root=data_root,
        )
        verify_process_resource_contract(configs, document)
        refs.extend(
            {
                "source_id": selection.source_id,
                "process": role,
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "sha256": sha256_file(path),
                "byte_size": path.stat().st_size,
            }
            for role, path in paths.items()
        )
    if len(refs) != 210:
        raise ValueError(f"Task 03H must seal exactly 210 process configs: {len(refs)}")
    return refs


def _validate_policy_hashes(collection: CollectionRunSpec) -> None:
    if collection.target_policy_sha256 != sha256_file(TARGET_POLICY):
        raise ValueError("Task 03H target policy checksum differs")
    if collection.resolution_policy_sha256 != sha256_file(RESOLUTION_POLICY):
        raise ValueError("Task 03H resolution policy checksum differs")


def _completed_candidate_markers(data_root: Path) -> list[str]:
    task_root = data_root / TASK_ROOT
    if not task_root.is_dir():
        return []
    return sorted(
        path.relative_to(data_root).as_posix() for path in task_root.rglob("completion_record.json")
    )


def _source_scope(manifest_path: Path) -> SourceScope:
    manifest = _object(manifest_path)
    sources = [
        source for source in manifest["sources"] if source.get("source_role") == "model_corpus"
    ]
    edition_warnings = next(
        source["warnings"]
        for source in sources
        if source["source_id"] == "deir_appendix_k2_part_2_of_5"
    )
    edition_override = next(
        warning for warning in edition_warnings if warning.startswith("source_edition_override:")
    )
    return SourceScope(
        ordered_source_ids=[source["source_id"] for source in sources],
        page_count=sum(source["pdf_page_count"] for source in sources),
        byte_count=sum(source["byte_size"] for source in sources),
        warning_count=sum(len(source.get("warnings", [])) for source in sources),
        edition_override=edition_override,
    )


def _write_readiness_report(
    *,
    report_path: Path,
    identity_path: Path,
    extraction_id: str,
    document: DocumentRunSpec,
    document_sha256: str,
    collection: CollectionRunSpec,
    collection_sha256: str,
    source_scope: SourceScope,
    config_refs: list[dict[str, Any]],
    completion_markers: list[str],
) -> None:
    """Persist one explicit no-source/no-model readiness boundary."""
    write_json_atomic(
        report_path,
        {
            "schema_version": "er_commons.task03h_preparation_readiness.v1",
            "status": "ready_for_user_authorized_first_wave",
            "production_extraction_id": extraction_id,
            "production_identity_sha256": sha256_file(identity_path),
            "document_run_spec_sha256": document_sha256,
            "collection_run_spec_sha256": collection_sha256,
            "source_scope": source_scope.as_record(),
            "catalog": {
                "checked_in_path": CATALOG.relative_to(PROJECT_ROOT).as_posix(),
                "staged_path": collection.source_family_catalog_relative_path.as_posix(),
                "sha256": sha256_file(CATALOG),
                "byte_size": CATALOG.stat().st_size,
            },
            "owner_configs": config_refs,
            "resource_policy": document.resource_policy.model_dump(mode="json"),
            "freshness": {
                "task_root": TASK_ROOT.as_posix(),
                "completed_candidate_markers": completion_markers,
                "historical_lineage_pins": [],
                "bounded_authorizations": [],
            },
            "source_pdf_bytes_read": False,
            "model_files_read": False,
            "producer_identity_derivation_run": False,
            "execution_boundary": (
                "source/model verification and producer identity derivation not run"
            ),
        },
    )


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


__all__ = ["prepare_task03h"]
