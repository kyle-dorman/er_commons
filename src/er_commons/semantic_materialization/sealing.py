"""Validate, serialize, inventory, and close one semantic candidate workspace."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.canonical_extraction.publication import (
    sha256_file,
    write_inventory,
    write_json,
    write_jsonl,
)
from er_commons.semantic_materialization.baseline import BASELINE_COLLECTION_PATHS
from er_commons.semantic_materialization.config import APPENDIX_P_SCOPE
from er_commons.semantic_materialization.construction import SemanticBuild
from er_commons.semantic_materialization.errors import SemanticMaterializationInvariantError
from er_commons.semantic_materialization.support import (
    SUPPORT_PATHS,
    CandidateSupport,
    semantic_validation_bundle,
)
from er_commons.semantic_structure import validate_semantic_contract

JsonObject = dict[str, Any]
SEMANTIC_SCHEMA_PATH = Path(
    "benchmarks/er_bench/schemas/canonical_extraction/v2/semantic_structure.schema.json"
)
PAGE_LABEL_PATH = "observations/page_labels.jsonl"
TARGET_ALIAS_PATH = "canonical/target_aliases.jsonl"
RECORD_TYPES = {
    "documents": "document",
    "pages": "page",
    "sections": "section",
    "blocks": "block",
    "tables": "table",
    "table_families": "table_family",
    "figures": "figure",
    "images": "image",
    "assets": "asset",
    "target_aliases": "target_alias",
    "cross_references": "cross_reference",
    "routing_observations": "routing_observation",
    "table_stage_observations": "table_stage_observation",
    "conversion_observations": "conversion_observation",
    "raw_mappings": "raw_mapping",
    "page_label_observations": "page_label_observation",
}


@dataclass(frozen=True)
class SemanticSealingInputs:
    """Validated values that determine one completion-last candidate bundle."""

    project_root: Path
    identity: JsonObject
    baseline_root: Path
    baseline_candidate_id: str
    baseline_producer_run_id: str
    hierarchy_producer_run_id: str
    control: JsonObject
    inherited_warnings: list[str]


def validate_serialize_and_seal(
    *, root: Path, build: SemanticBuild, support: CandidateSupport, inputs: SemanticSealingInputs
) -> None:
    """Apply all gates, write deterministic records, then write completion last."""
    _validate_semantic_contract(build, support, inputs)
    write_json(root / "records" / "extraction_identity.json", inputs.identity)
    record_files = _write_record_families(root, build)
    support_files = _write_support_files(root, support)
    manifest = _manifest(
        build=build,
        identity=inputs.identity,
        baseline_root=inputs.baseline_root,
        inherited_warnings=inputs.inherited_warnings,
        record_files=record_files,
        support_files=support_files,
    )
    write_json(root / "records" / "manifest.json", manifest)
    write_json(
        root / "records" / "canonicalization_summary.json",
        _summary(build, inputs.identity, inputs.inherited_warnings),
    )
    inventory_path = write_inventory(root)
    write_json(
        root / "records" / "completion_record.json",
        {
            "schema_version": "er_commons.canonical_extraction_completion.v2",
            "extraction_id": inputs.identity["extraction_id"],
            "status": "complete_with_warnings",
            "source_semantic_disposition": "accepted_with_known_limitations",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "support_files_verified": True,
            "undeclared_difference_count": 0,
        },
    )


def candidate_file_bytes(root: Path) -> dict[str, bytes]:
    """Return candidate-owned bytes for fresh-build reproducibility checks."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _validate_semantic_contract(
    build: SemanticBuild, support: CandidateSupport, inputs: SemanticSealingInputs
) -> None:
    bundle = semantic_validation_bundle(
        build=build,
        control=inputs.control,
        correspondence=support.correspondence,
        baseline_producer_run_id=inputs.baseline_producer_run_id,
        hierarchy_producer_run_id=inputs.hierarchy_producer_run_id,
    )
    schema = json.loads((inputs.project_root / SEMANTIC_SCHEMA_PATH).read_bytes())
    Draft202012Validator(schema).validate(bundle)
    validate_semantic_contract(bundle, bridge_evidence=build.bridge_evidence)
    _require_count(
        "page-label outcomes",
        APPENDIX_P_SCOPE.page_count,
        len(build.page_label_observations),
    )
    _require_count("sections", APPENDIX_P_SCOPE.section_count, len(build.collections["sections"]))


def _write_record_families(root: Path, build: SemanticBuild) -> list[JsonObject]:
    ordered = [
        (family, path)
        for family, path in BASELINE_COLLECTION_PATHS.items()
        if family != "cross_references"
    ]
    assets_index = next(index for index, (family, _) in enumerate(ordered) if family == "assets")
    ordered[assets_index + 1 : assets_index + 1] = [
        ("target_aliases", TARGET_ALIAS_PATH),
        ("cross_references", BASELINE_COLLECTION_PATHS["cross_references"]),
    ]
    ordered.append(("page_label_observations", PAGE_LABEL_PATH))
    record_files = []
    for family, relative_path in ordered:
        records = _records_for_family(build, family)
        count = write_jsonl(root / relative_path, records)
        record_files.append(
            {
                "record_type": RECORD_TYPES[family],
                "path": relative_path,
                "sha256": sha256_file(root / relative_path),
                "record_count": count,
            }
        )
    return record_files


def _records_for_family(build: SemanticBuild, family: str) -> list[JsonObject]:
    if family == "target_aliases":
        return build.target_aliases
    if family == "page_label_observations":
        return build.page_label_observations
    return build.collections[family]


def _write_support_files(root: Path, support: CandidateSupport) -> list[JsonObject]:
    files = []
    for role, relative_path in SUPPORT_PATHS.items():
        write_json(root / relative_path, support.payloads[role])
        files.append(
            {
                "role": role,
                "path": relative_path,
                "sha256": sha256_file(root / relative_path),
                "schema_version": "2.0.0",
            }
        )
    return files


def _manifest(
    *,
    build: SemanticBuild,
    identity: JsonObject,
    baseline_root: Path,
    inherited_warnings: list[str],
    record_files: list[JsonObject],
    support_files: list[JsonObject],
) -> JsonObject:
    baseline_manifest = json.loads((baseline_root / "records" / "manifest.json").read_bytes())
    return {
        "schema_version": "er_commons.canonical_extraction_manifest.v2",
        "extraction_id": identity["extraction_id"],
        "identity_sha256": identity["identity_sha256"],
        "source_semantic_disposition": "accepted_with_known_limitations",
        "canonicalization_status": "complete_with_warnings",
        "canonicalization_warnings": inherited_warnings,
        "canonicalization_errors": [],
        "source_release_version": baseline_manifest["source_release_version"],
        "source_manifest_path": baseline_manifest["source_manifest_path"],
        "source_manifest_sha256": baseline_manifest["source_manifest_sha256"],
        "document_scope_complete": True,
        "ordered_document_ids": [build.collections["documents"][0]["id"]],
        "record_files": record_files,
        "page_label_observation_count": len(build.page_label_observations),
        "target_alias_count": len(build.target_aliases),
        "support_files": support_files,
    }


def _summary(build: SemanticBuild, identity: JsonObject, warnings: list[str]) -> JsonObject:
    return {
        "schema_version": "er_commons.semantic_materialization_summary.v2",
        "candidate_id": identity["extraction_id"],
        "release_candidate": False,
        "counts": {
            **{family: len(records) for family, records in build.collections.items()},
            "page_label_observations": len(build.page_label_observations),
            "target_aliases": len(build.target_aliases),
            "clean_table_cells": sum(len(item["cells"]) for item in build.collections["tables"]),
            "bridge_entries": len(build.bridge_entries),
        },
        "source_semantic_disposition": "accepted_with_known_limitations",
        "undeclared_difference_count": 0,
        "warnings": warnings,
        "errors": [],
        "validation": {
            "semantic_schema_valid": True,
            "semantic_contract_valid": True,
            "baseline_preservation_valid": True,
            "bounded_control_valid": True,
        },
    }


def _require_count(label: str, expected: int, observed: int) -> None:
    if observed != expected:
        raise SemanticMaterializationInvariantError(
            stage="semantic validation",
            invariant=f"accepted {label} count",
            expected=expected,
            observed=observed,
            subject="Appendix P candidate",
        )
