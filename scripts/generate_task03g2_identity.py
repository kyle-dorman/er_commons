"""Refresh the exact three-source Task 03G.2 non-executed identity recipe."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from er_commons.corpus_extraction_contract_v1_1.checks import canonical_sha256
from er_commons.settings import load_settings

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "benchmarks/er_bench/fixtures/corpus_extraction/v1_1"
CURRENT_IDENTITY = FIXTURE_ROOT / "production_identity_preimage.json"
HISTORICAL_IDENTITY = FIXTURE_ROOT / "task03g1a_production_identity_preimage.json"
DOCUMENT_SPEC = ROOT / "configs/brisbane_baylands_2025_deir_task03g2_document_v1.json"
PILOT_SCOPE_EVIDENCE = FIXTURE_ROOT / "task03g2_production_scope_evidence.json"
SOURCE_IDS = ("deir_main", "deir_appendix_d", "deir_appendix_p")
MANIFEST_RELATIVE = Path(
    "datasets/ceqa/raw/brisbane_baylands/"
    "brisbane_baylands_2025_deir_sources_v1/records/source_manifest.json"
)


def main() -> None:
    """Preserve Task 03G.1a, write the pilot identity, and bind its run spec."""
    historical = _preserve_historical_identity()
    old_preimage = historical["preimage"]
    data_root = load_settings().data_root.resolve()
    manifest_path = data_root / MANIFEST_RELATIVE
    completion_path = manifest_path.parent / "completion_record.json"
    manifest = _read_object(manifest_path)
    selected_records = _selected_source_records(manifest)

    scope = {
        "source_release_version": manifest["source_release_version"],
        "source_manifest": _external_reference(manifest_path, data_root),
        "release_completion": _external_reference(completion_path, data_root),
        "ordered_source_ids": list(SOURCE_IDS),
        "ordered_source_records_sha256": canonical_sha256(
            [
                {
                    "source_id": item["source_id"],
                    "sha256": item["sha256"],
                    "pdf_page_count": item["pdf_page_count"],
                }
                for item in selected_records
            ]
        ),
    }
    _write_json(
        PILOT_SCOPE_EVIDENCE,
        {
            "source_release_version": scope["source_release_version"],
            "source_manifest_sha256": scope["source_manifest"]["sha256"],
            "release_completion_sha256": scope["release_completion"]["sha256"],
            "ordered_source_records_sha256": scope["ordered_source_records_sha256"],
        },
    )

    preimage = copy.deepcopy(old_preimage)
    preimage.update(
        {
            "contract_revision": "task_03g2_representative_pilot_v1",
            "extraction_version_name": "brisbane_baylands_representative_pilot_v1",
            "production_scope": scope,
            "producer_contract": _section(
                version="task03g2-fresh-producers-v1",
                artifacts=_owner_configs("baseline_producer", "hierarchy_producer"),
                code_roots=(
                    "src/er_commons/document_extraction",
                    "src/er_commons/table_extraction",
                    "src/er_commons/source_release",
                ),
                extra_code=("src/er_commons/artifact_io.py",),
            ),
            "canonical_contract": _section(
                version="task03g2-fresh-canonical-semantic-v1",
                artifacts=(
                    "benchmarks/er_bench/schemas/canonical_extraction/v1/records.schema.json",
                    "benchmarks/er_bench/schemas/canonical_extraction/v2/semantic_structure.schema.json",
                    "benchmarks/er_bench/schemas/canonical_extraction/v3/cross_references.schema.json",
                    *_owner_configs("canonical", "semantic"),
                ),
                code_roots=(
                    "src/er_commons/canonical_extraction",
                    "src/er_commons/semantic_materialization",
                    "src/er_commons/semantic_structure",
                ),
            ),
            "hierarchy_contract": _section(
                version="task03g2-machine-validation-hierarchy-v1",
                artifacts=(
                    "benchmarks/er_bench/schemas/hierarchy_correction/v1/records.schema.json",
                    "docs/specs/hierarchy_correction_v1.md",
                    *_owner_configs("hierarchy_correction"),
                ),
                code_roots=("src/er_commons/hierarchy_correction",),
                extra_code=("src/er_commons/document_extraction/hierarchy/document.py",),
            ),
            "cross_reference_contract": _section(
                version="task03g2f-shared-family-cross-reference-v4",
                artifacts=(
                    "docs/specs/cross_references_v3.md",
                    "docs/specs/semantic_structure_v2.md",
                    "configs/brisbane_baylands_2025_deir_task03g2_source_family_catalog_v1.json",
                    *_owner_configs("cross_references"),
                ),
                code_roots=("src/er_commons/cross_reference_enrichment",),
                extra_code=("src/er_commons/source_family_catalog.py",),
            ),
            "corpus_workflow_contract": _section(
                version="task03g2f-source-id-resolution-workflow-v1_1",
                artifacts=(
                    "benchmarks/er_bench/fixtures/corpus_extraction/v1_1/invalid_mutations.json",
                    "benchmarks/er_bench/fixtures/corpus_extraction/v1_1/positive_scenarios.json",
                    "benchmarks/er_bench/fixtures/corpus_extraction/v1_1/task03g2_production_scope_evidence.json",
                    "benchmarks/er_bench/schemas/corpus_extraction/v1_1/records.schema.json",
                    "docs/specs/restartable_corpus_extraction_v1_1.md",
                    "configs/brisbane_baylands_2025_deir_task03g2_source_family_catalog_v1.json",
                    "configs/brisbane_baylands_2025_deir_task03g2_scope_v1.json",
                    "configs/brisbane_baylands_2025_deir_task03g2_target_policy_v1.json",
                    "configs/brisbane_baylands_2025_deir_task03g2_resolution_policy_v1.json",
                ),
                code_roots=(
                    "src/er_commons/corpus_extraction",
                    "src/er_commons/corpus_extraction_contract_v1_1",
                    "src/er_commons/corpus_resolution",
                ),
                extra_code=(
                    "src/er_commons/cli.py",
                    "src/er_commons/source_family_catalog.py",
                ),
            ),
        }
    )
    digest = canonical_sha256(preimage)
    extraction_id = f"exv1-{digest}"
    record = {
        "record_type": "production_identity",
        "schema_version": "er_commons.corpus_extraction_identity.v1_1",
        "fixture_status": "identity_recipe",
        "execution_status": "not_executed",
        "extraction_id": extraction_id,
        "identity_sha256": digest,
        "preimage": preimage,
    }
    _write_json(CURRENT_IDENTITY, record)

    document_spec = _read_object(DOCUMENT_SPEC)
    document_spec["production_extraction_id"] = extraction_id
    document_spec["production_identity_relative_path"] = CURRENT_IDENTITY.relative_to(
        ROOT
    ).as_posix()
    _write_json(DOCUMENT_SPEC, document_spec)


def _preserve_historical_identity() -> dict[str, Any]:
    if HISTORICAL_IDENTITY.is_file():
        record = _read_object(HISTORICAL_IDENTITY)
    else:
        record = _read_object(CURRENT_IDENTITY)
        revision = record.get("preimage", {}).get("contract_revision")
        if revision != "task_03g1a_remediation_v1":
            raise ValueError("accepted Task 03G.1a identity is unavailable")
        HISTORICAL_IDENTITY.write_bytes(CURRENT_IDENTITY.read_bytes())
    if record.get("preimage", {}).get("contract_revision") != "task_03g1a_remediation_v1":
        raise ValueError("historical identity is not the Task 03G.1a recipe")
    return record


def _selected_source_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    selected = [item for item in manifest["sources"] if item["source_id"] in SOURCE_IDS]
    if [item["source_id"] for item in selected] != list(SOURCE_IDS):
        raise ValueError("selected sources do not match sealed manifest order")
    return selected


def _owner_configs(*roles: str) -> tuple[str, ...]:
    return tuple(
        f"configs/brisbane_baylands_2025_deir_task03g2_{slug}_{role}_v1.json"
        for role in roles
        for slug in ("main", "appendix_d", "appendix_p")
    )


def _section(
    *,
    version: str,
    artifacts: tuple[str, ...],
    code_roots: tuple[str, ...],
    extra_code: tuple[str, ...] = (),
) -> dict[str, Any]:
    code_paths = list(extra_code)
    for relative_root in code_roots:
        code_paths.extend(
            path.relative_to(ROOT).as_posix()
            for path in sorted((ROOT / relative_root).rglob("*.py"))
        )
    return {
        "version": version,
        "artifacts": [_project_reference(path) for path in artifacts],
        "owned_code": [_project_reference(path) for path in sorted(set(code_paths))],
    }


def _project_reference(relative_path: str) -> dict[str, Any]:
    path = ROOT / relative_path
    return {
        "path": relative_path,
        "sha256": _sha256(path),
        "byte_size": path.stat().st_size,
    }


def _external_reference(path: Path, data_root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(data_root).as_posix(),
        "sha256": _sha256(path),
        "byte_size": path.stat().st_size,
    }


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"JSON record is not an object: {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
