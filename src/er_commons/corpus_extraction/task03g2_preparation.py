"""Stage and audit Task 03G.2 inputs without touching source PDF bytes."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from er_commons.corpus_extraction.config import load_run_spec
from er_commons.corpus_extraction.fresh_preflight import validate_fresh_build_templates
from er_commons.corpus_extraction.owner_inputs import (
    OwnerConfigs,
    verify_owner_resource_contract,
)
from er_commons.corpus_extraction.preflight import _production_scope_evidence
from er_commons.corpus_extraction_contract_v1_1 import validate_production_identity
from er_commons.source_freeze import sha256_file, write_json_atomic

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOCUMENT_SPEC = PROJECT_ROOT / "configs/brisbane_baylands_2025_deir_task03g2_document_v1.json"
SCOPE_SPEC = PROJECT_ROOT / "configs/brisbane_baylands_2025_deir_task03g2_scope_v1.json"
CATALOG = PROJECT_ROOT / "configs/brisbane_baylands_2025_deir_task03g2_corpus_catalog_v1.json"
TASK_ROOTS = (
    Path("pipelines/brisbane_baylands/task_03g2_document_producers"),
    Path("pipelines/brisbane_baylands/task_03g2_canonical_records"),
    Path("pipelines/brisbane_baylands/task_03g2_hierarchy_correction"),
    Path("pipelines/brisbane_baylands/task_03g2_representative_pilot"),
)


def prepare_task03g2(data_root: Path) -> Path:
    """Stage the exact catalog and publish a source-PDF-free readiness report."""
    data_root = data_root.resolve()
    spec, spec_sha256 = load_run_spec(DOCUMENT_SPEC)
    scope = _object(SCOPE_SPEC)
    catalog_relative = Path(str(scope["corpus_catalog_relative_path"]))
    staged_catalog = (data_root / catalog_relative).resolve()
    if not staged_catalog.is_relative_to(data_root):
        raise ValueError("Task 03G.2 catalog path escapes the data root")
    staged_catalog.parent.mkdir(parents=True, exist_ok=True)
    if staged_catalog.exists():
        if staged_catalog.read_bytes() != CATALOG.read_bytes():
            raise FileExistsError("staged Task 03G.2 catalog differs from checked-in bytes")
    else:
        shutil.copyfile(CATALOG, staged_catalog)

    config_refs: list[dict[str, Any]] = []
    for owner in spec.document_owners:
        paths = {
            role: (PROJECT_ROOT / path).resolve()
            for role, path in owner.configs.model_dump().items()
        }
        configs = OwnerConfigs(**paths)
        validate_fresh_build_templates(
            configs=configs,
            source_id=owner.source_id,
            disposition=spec.hierarchy_disposition(owner.source_id),
            data_root=data_root,
        )
        verify_owner_resource_contract(configs, spec)
        config_refs.extend(
            {
                "source_id": owner.source_id,
                "owner": role,
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "sha256": sha256_file(path),
                "byte_size": path.stat().st_size,
            }
            for role, path in paths.items()
        )

    completion_markers = sorted(
        path.relative_to(data_root).as_posix()
        for root in TASK_ROOTS
        for path in (data_root / root).rglob("completion_record.json")
        if (data_root / root).is_dir()
    )
    if completion_markers:
        raise ValueError("Task 03G.2 namespace already contains completed candidates")

    identity_path = (PROJECT_ROOT / spec.production_identity_relative_path).resolve()
    identity = _object(identity_path)
    source_ids, scope_evidence = _production_scope_evidence(
        spec=spec,
        identity=identity,
        data_root=data_root,
    )
    validated_identity = validate_production_identity(
        identity,
        expected_source_ids=source_ids,
        expected_scope=scope_evidence,
        expected_scope_kind=spec.scope_kind,
        project_root=PROJECT_ROOT,
    )
    if validated_identity.value != spec.production_extraction_id:
        raise ValueError("Task 03G.2 run spec differs from the production identity")
    report_path = staged_catalog.parent / "task03g2_preparation_readiness.json"
    report = {
        "schema_version": "er_commons.task03g2_preparation_readiness.v1",
        "status": "ready_for_source_verification",
        "source_pdf_bytes_read": False,
        "production_extraction_id": spec.production_extraction_id,
        "production_identity_sha256": sha256_file(identity_path),
        "document_run_spec_sha256": spec_sha256,
        "scope_run_spec_sha256": sha256_file(SCOPE_SPEC),
        "catalog": {
            "checked_in_path": CATALOG.relative_to(PROJECT_ROOT).as_posix(),
            "staged_path": catalog_relative.as_posix(),
            "sha256": sha256_file(CATALOG),
            "byte_size": CATALOG.stat().st_size,
        },
        "source_ids": [owner.source_id for owner in spec.document_owners],
        "owner_configs": config_refs,
        "freshness": {
            "task_roots": [path.as_posix() for path in TASK_ROOTS],
            "completed_candidate_markers": completion_markers,
            "historical_lineage_pins": [],
            "bounded_authorizations": [],
        },
        "execution_boundary": "source verification and producer identity derivation not run",
        "identity_record_type": identity.get("record_type"),
    }
    write_json_atomic(report_path, report)
    return report_path


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


__all__ = ["prepare_task03g2"]
