"""Build content-derived hierarchy candidate and environment records."""

from __future__ import annotations

import platform
import sys
from collections.abc import Iterable
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from er_commons.artifact_io import sha256_file
from er_commons.hierarchy_inference.config import HierarchyInferenceConfig
from er_commons.hierarchy_inference.digests import canonical_json_sha256
from er_commons.hierarchy_inference.inputs import HierarchyInferenceInputs

DEFAULT_ENVIRONMENT_PACKAGES = ("jsonschema", "pydantic", "pypdf", "pypdfium2", "rfc8785")


def code_bundle_sha256(project_root: Path, paths: Iterable[Path]) -> str:
    """Hash sorted repository-relative code paths and their exact bytes."""
    root = project_root.resolve()
    records = [
        {
            "path": path.resolve().relative_to(root).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in sorted(paths)
    ]
    if not records:
        raise ValueError("candidate code bundle must contain at least one file")
    return canonical_json_sha256(records)


def build_candidate_identity(
    *,
    config: HierarchyInferenceConfig,
    config_sha256: str,
    inputs: HierarchyInferenceInputs,
    policy_path: Path,
    schema_path: Path,
    project_root: Path,
    owned_code_paths: Iterable[Path],
) -> dict[str, Any]:
    """Content-bind all normative v1 inputs and derive the hcorv1 ID."""
    payload: dict[str, Any] = {
        "producer_run_id": config.producer_run_id,
        "source_id": config.source.source_id,
        "source_sha256": inputs.selected_source.source_sha256,
        "source_manifest_sha256": inputs.producer_completion.source_manifest_sha256,
        "producer_completion_sha256": inputs.input_inventory["producer_completion_sha256"],
        "producer_inventory_sha256": inputs.input_inventory["producer_inventory_sha256"],
        "policy_version": config.policy_version,
        "policy_sha256": sha256_file(policy_path),
        "config_sha256": config_sha256,
        "schema_sha256": sha256_file(schema_path),
        "code_bundle_sha256": code_bundle_sha256(project_root, owned_code_paths),
    }
    return {"candidate_id": f"hcorv1-{canonical_json_sha256(payload)}", **payload}


def build_environment_record(
    *,
    uv_lock_path: Path,
    package_names: tuple[str, ...] = DEFAULT_ENVIRONMENT_PACKAGES,
) -> dict[str, Any]:
    """Record diagnostic runtime evidence without changing candidate identity."""
    packages: dict[str, str] = {}
    for name in package_names:
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = "not-installed"
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "uv_lock_sha256": sha256_file(uv_lock_path),
        "package_versions": packages,
    }
