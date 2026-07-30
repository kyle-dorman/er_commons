"""Build the deterministic, explicitly non-release Task 03D identity."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

import rfc8785

from er_commons.canonical_extraction.config import CanonicalizationConfig
from er_commons.canonical_extraction.identity import extraction_identity_sha256
from er_commons.canonical_extraction.inputs import CanonicalizationInputs
from er_commons.canonical_extraction.publication import sha256_file


def _json_digest(value: Any) -> str:
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def _git_state(project_root: Path) -> tuple[str, bool]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return commit, bool(status.strip())


def owned_code_digest(project_root: Path, paths: tuple[Path, ...]) -> str:
    """Hash ordered relative path and byte digest pairs for owned candidate code."""
    records = [
        {
            "path": path.relative_to(project_root).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in sorted(paths)
    ]
    return _json_digest(records)


def build_candidate_identity(
    *,
    project_root: Path,
    config: CanonicalizationConfig,
    inputs: CanonicalizationInputs,
    schema_path: Path,
    mapping_policy_path: Path,
    owned_paths: tuple[Path, ...],
) -> dict[str, Any]:
    """Return a content-bound identity with its derived extraction ID."""
    producer = inputs.producer_identity["identity"]
    source_records = [
        {
            "source_id": record.source_id,
            "sha256": record.sha256,
            "pdf_page_count": record.pdf_page_count,
        }
        for record in inputs.sealed_manifest.sources
        if record.source_role == "model_corpus"
    ]
    runtime = producer["runtime"]
    models = producer["model_inventory"]
    packages = producer["package_versions"]
    producer_inventory_path = (
        config.producer_artifact_relative_root
        / config.producer_run_id
        / "records"
        / "artifact_inventory.json"
    )
    git_commit, git_dirty = _git_state(project_root)
    identity: dict[str, Any] = {
        "schema_version": "er_commons.extraction_identity.v1",
        "extraction_version_name": config.candidate_version_name,
        "source_release": {
            "source_release_version": config.source_release_version,
            "source_manifest_path": config.source_manifest_relative_path.as_posix(),
            "source_manifest_sha256": (inputs.producer_completion_record.source_manifest_sha256),
            "completion_record_path": producer["sealed_release"]["completion_record_path"],
            "completion_record_sha256": producer["sealed_release"]["completion_record_sha256"],
            "ordered_model_corpus": source_records,
        },
        "materialization_scope": {
            "scope_kind": "document_candidate",
            "release_status": "non_release_candidate",
            "ordered_source_ids": [item.source_id for item in config.ordered_materialization_scope],
            "producer_runs": [
                {
                    "source_id": config.ordered_materialization_scope[0].source_id,
                    "producer_run_id": config.producer_run_id,
                    "artifact_inventory_path": producer_inventory_path.as_posix(),
                    "artifact_inventory_sha256": (
                        inputs.producer_completion_record.artifact_inventory_sha256
                    ),
                }
            ],
            "mapping_policy_version": config.mapping_policy_version,
            "mapping_policy_sha256": sha256_file(mapping_policy_path),
        },
        "docling": {
            "configuration_id": runtime["configuration_id"],
            "pipeline_class": runtime["pipeline_class"],
            "backend_class": runtime["backend_class"],
            "effective_options_sha256": _json_digest(runtime["effective_options"]),
            "package_versions": {
                key: value
                for key, value in packages.items()
                if key.startswith("docling") or key == "pypdfium2"
            },
            "model_inventory_path": models["path"],
            "model_inventory_sha256": models["sha256"],
            "resolved_models": [
                {
                    "purpose": model["purpose"],
                    "repository": model["repository"],
                    "requested_revision": model["requested_revision"],
                    "resolved_commit": model["resolved_commit"],
                    "ordered_file_sha256s": [item["sha256"] for item in model["files"]],
                }
                for model in models["models"]
            ],
        },
        "table_pipeline": {
            "package_versions": {
                key: value
                for key, value in packages.items()
                if key in {"camelot-py", "opencv-python-headless"}
            },
            "pdfium_version": packages["pypdfium2"],
            "routing_config_sha256": producer["routing_sha256"],
            "detection_config_sha256": producer["table_sha256"],
            "cleanup_config_sha256": producer["table_sha256"],
            "family_config_sha256": producer["table_sha256"],
        },
        "canonical_contract": {
            "schema_version": "er_commons.canonical_extraction.v1",
            "schema_bundle_sha256": sha256_file(schema_path),
            "id_policy_version": "2",
            "ordering_policy_version": "1",
            "serialization_policy_version": "1",
        },
        "project_code": {
            "git_commit": git_commit,
            "git_dirty": git_dirty,
            "owned_code_bundle_sha256": owned_code_digest(project_root, owned_paths),
        },
    }
    digest = extraction_identity_sha256(identity)
    identity["extraction_id"] = f"exv1-{digest}"
    identity["identity_sha256"] = digest
    return identity
