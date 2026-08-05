"""Validate fresh owner templates without requiring downstream candidates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.corpus_extraction.config import HierarchyDisposition
from er_commons.corpus_extraction.owner_inputs import OwnerConfigs
from er_commons.source_freeze import sha256_file

JsonObject = dict[str, Any]


def validate_fresh_build_templates(
    *,
    configs: OwnerConfigs,
    source_id: str,
    disposition: HierarchyDisposition,
    data_root: Path,
) -> tuple[Path, None]:
    """Validate fresh policy templates without requiring not-yet-built candidates."""
    values = {role: _json(path) for role, path in configs.as_dict().items()}
    mismatches: list[str] = []
    if disposition.authority != "machine_validation" or (
        disposition.authorization_relative_path is not None
    ):
        mismatches.append("fresh build requires machine hierarchy validation")
    correction = values["hierarchy_correction"]
    if correction.get("publication_authorization") != "machine_validation":
        mismatches.append("fresh correction template must use machine_validation")
    if correction.get("bounded_acceptance_artifact_relative_root") is not None or (
        correction.get("bounded_acceptance_config_relative_path") is not None
    ):
        mismatches.append("fresh correction template carries bounded-acceptance controls")
    semantic = values["semantic"]
    if semantic.get("control_profile") != "strict_quality_gate":
        mismatches.append("fresh semantic template must use strict_quality_gate")
    bounded_fields = (
        "bounded_acceptance_relative_path",
        "bounded_acceptance_policy_relative_path",
        "producer_comparison_relative_path",
    )
    if any(semantic.get(field) is not None for field in bounded_fields):
        mismatches.append("fresh semantic template carries historical review controls")
    _validate_manifest(data_root, source_id, values["cross_references"], mismatches)
    artifact_roots = _fresh_artifact_roots(values)
    invalid_roots = [str(path) for path in artifact_roots if not is_task03g2_root(path)]
    if invalid_roots:
        mismatches.append(
            "fresh owner artifact roots must use the task_03g2 namespace: "
            + ", ".join(invalid_roots)
        )
    _validate_fresh_placeholders(values, mismatches)
    final_value = values["cross_references"].get("artifact_relative_root")
    final_root = Path(final_value) if isinstance(final_value, str) else Path(".")
    if final_root.is_absolute() or ".." in final_root.parts:
        mismatches.append("fresh cross-reference artifact root is not contained")
    if mismatches:
        raise ValueError(
            "fresh content-owner lineage preflight failed before PDF work: " + "; ".join(mismatches)
        )
    return final_root, None


def is_task03g2_root(path: Path) -> bool:
    """Recognize only the exact task namespace or a named child namespace."""
    return any(part == "task_03g2" or part.startswith("task_03g2_") for part in path.parts)


def _validate_manifest(
    data_root: Path,
    source_id: str,
    cross_reference: JsonObject,
    mismatches: list[str],
) -> None:
    if cross_reference.get("source_id") != source_id:
        mismatches.append("fresh cross-reference template selects another source")
    manifest_value = cross_reference.get("source_manifest_relative_path")
    manifest_path = data_root / manifest_value if isinstance(manifest_value, str) else None
    if (
        manifest_path is None
        or not manifest_path.resolve().is_relative_to(data_root.resolve())
        or not manifest_path.is_file()
        or sha256_file(manifest_path) != cross_reference.get("source_manifest_sha256")
    ):
        mismatches.append("fresh cross-reference source manifest seal differs")


def _validate_fresh_placeholders(values: dict[str, JsonObject], mismatches: list[str]) -> None:
    zero = "0" * 64
    expected = {
        ("canonical", "producer_run_id"): f"prv1-{zero}",
        ("hierarchy_correction", "producer_run_id"): f"prv1-{zero}",
        ("semantic", "baseline_candidate_id"): f"exv1-{zero}",
        ("semantic", "baseline_producer_run_id"): f"prv1-{zero}",
        ("semantic", "hierarchy_producer_run_id"): f"prv1-{zero}",
        ("semantic", "hierarchy_candidate_id"): f"hcorv1-{zero}",
        ("cross_references", "upstream_candidate_id"): f"exv1-{zero}",
        ("cross_references", "upstream_completion_sha256"): zero,
        ("cross_references", "upstream_inventory_sha256"): zero,
    }
    stale = [
        f"{role}.{field}"
        for (role, field), placeholder in expected.items()
        if values[role].get(field) != placeholder
    ]
    if stale:
        mismatches.append(
            "fresh templates contain non-placeholder lineage pins: " + ", ".join(stale)
        )


def _fresh_artifact_roots(values: dict[str, JsonObject]) -> tuple[Path, ...]:
    fields = {
        "baseline_producer": ("artifact_relative_root",),
        "hierarchy_producer": ("artifact_relative_root",),
        "canonical": ("producer_artifact_relative_root", "artifact_relative_root"),
        "hierarchy_correction": (
            "producer_artifact_relative_root",
            "artifact_relative_root",
        ),
        "semantic": (
            "baseline_producer_relative_root",
            "hierarchy_producer_relative_root",
            "artifact_relative_root",
        ),
        "cross_references": ("artifact_relative_root",),
    }
    return tuple(
        Path(value) if isinstance(value, str) else Path(".")
        for role, names in fields.items()
        for name in names
        for value in (values[role].get(name),)
    )


def _json(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value
