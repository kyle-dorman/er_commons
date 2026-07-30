"""Artifact-level comparison of two immutable complete-document producer runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from er_commons.document_extraction.comparison import structural_diff
from er_commons.document_extraction.hierarchy.artifact_normalization import (
    ProducerIdentityValues,
    load_json_records,
    normalize_artifact_json,
    normalized_completion,
    normalized_log,
)
from er_commons.document_extraction.hierarchy.document import JsonObject
from er_commons.document_extraction.hierarchy.document_comparison import (
    compare_docling_hierarchy,
)
from er_commons.document_extraction.producer_artifacts import verify_completed_run

DOCUMENT_PATH = "documents/deir_appendix_p/producer/docling/document.json"
DERIVED_INVENTORIES = {
    "records/artifact_inventory.json",
    "documents/deir_appendix_p/producer/tables/artifact_inventory.json",
}


def _inconclusive(reason: str) -> JsonObject:
    """Return the stable report shape for unverifiable producer roots."""
    return {
        "status": "inconclusive",
        "reason": reason,
        "artifact_path_set": {},
        "artifact_comparisons": [],
        "document_comparison": {},
        "unexpected_changes": [],
    }


def _rejected_path_set(
    baseline_paths: set[str],
    candidate_paths: set[str],
) -> JsonObject:
    """Return the stable report shape for a changed artifact inventory."""
    return {
        "status": "reject",
        "reason": "producer artifact path sets differ",
        "artifact_path_set": {
            "baseline_count": len(baseline_paths),
            "candidate_count": len(candidate_paths),
            "missing": sorted(baseline_paths - candidate_paths),
            "unexpected": sorted(candidate_paths - baseline_paths),
        },
        "artifact_comparisons": [],
        "document_comparison": {},
        "unexpected_changes": [],
    }


def _inventory(root: Path) -> dict[str, JsonObject]:
    value = load_json_records(root / "records/artifact_inventory.json")
    if not isinstance(value, dict) or not isinstance(value.get("files"), list):
        raise TypeError(f"artifact inventory has an invalid shape: {root}")
    return {str(item["path"]): item for item in value["files"]}


def _comparison_record(
    *,
    relative_path: str,
    mode: str,
    baseline_sha256: str,
    candidate_sha256: str,
    equal: bool,
) -> JsonObject:
    """Describe the policy and byte evidence used for one artifact."""
    return {
        "path": relative_path,
        "comparison": mode,
        "baseline_sha256": baseline_sha256,
        "candidate_sha256": candidate_sha256,
        "equal": equal,
    }


def _project_artifact(
    relative_path: str,
    path: Path,
    identity: ProducerIdentityValues,
) -> tuple[Any, str]:
    """Load one changed artifact through its declared comparison policy."""
    if relative_path == "logs/producer.log":
        return normalized_log(path, identity), "normalized_log"
    if path.suffix in {".json", ".jsonl"}:
        return (
            normalize_artifact_json(
                relative_path,
                load_json_records(path),
                identity,
            ),
            "declared_normalized_json",
        )
    return path.read_bytes(), "exact_bytes"


def _compare_changed_artifact(
    *,
    relative_path: str,
    baseline_root: Path,
    candidate_root: Path,
    baseline_sha256: str,
    candidate_sha256: str,
    baseline_identity: ProducerIdentityValues,
    candidate_identity: ProducerIdentityValues,
    review_pages: set[int] | None,
) -> tuple[JsonObject, JsonObject | None, JsonObject | None]:
    """Compare one byte-different artifact and return record, document, failure."""
    baseline_path = baseline_root / relative_path
    candidate_path = candidate_root / relative_path
    if relative_path == DOCUMENT_PATH:
        document = compare_docling_hierarchy(
            load_json_records(baseline_path),
            load_json_records(candidate_path),
            review_pages=review_pages,
        )
        equal = document["status"] == "pass"
        failure = None
        if not equal:
            failure = {
                "path": relative_path,
                "kind": "hierarchy_document_mismatch",
                "detail": document.get("reason"),
            }
        return (
            _comparison_record(
                relative_path=relative_path,
                mode="hierarchy_aware_json",
                baseline_sha256=baseline_sha256,
                candidate_sha256=candidate_sha256,
                equal=equal,
            ),
            document,
            failure,
        )
    if relative_path in DERIVED_INVENTORIES:
        return (
            _comparison_record(
                relative_path=relative_path,
                mode="derived_inventory_verified",
                baseline_sha256=baseline_sha256,
                candidate_sha256=candidate_sha256,
                equal=True,
            ),
            None,
            None,
        )

    baseline_value, mode = _project_artifact(
        relative_path,
        baseline_path,
        baseline_identity,
    )
    candidate_value, candidate_mode = _project_artifact(
        relative_path,
        candidate_path,
        candidate_identity,
    )
    if mode != candidate_mode:
        raise AssertionError(f"comparison policy differs for {relative_path}")
    diff = structural_diff(baseline_value, candidate_value)
    equal = diff["total_difference_count"] == 0
    failure = None
    if not equal:
        failure = {
            "path": relative_path,
            "kind": "undeclared_artifact_change",
            "diff": diff,
        }
    return (
        _comparison_record(
            relative_path=relative_path,
            mode=mode,
            baseline_sha256=baseline_sha256,
            candidate_sha256=candidate_sha256,
            equal=equal,
        ),
        None,
        failure,
    )


def compare_producer_runs(
    baseline_root: Path,
    candidate_root: Path,
    *,
    review_pages: set[int] | None = None,
) -> JsonObject:
    """Compare all inventoried producer artifacts under the Task 03E allowlist."""
    baseline_id = baseline_root.name
    candidate_id = candidate_root.name
    try:
        verify_completed_run(baseline_root, baseline_id)
        verify_completed_run(candidate_root, candidate_id)
    except (KeyError, OSError, TypeError, ValueError) as error:
        return _inconclusive(f"completed-run verification failed: {error}")

    baseline_inventory = _inventory(baseline_root)
    candidate_inventory = _inventory(candidate_root)
    baseline_paths = set(baseline_inventory)
    candidate_paths = set(candidate_inventory)
    if baseline_paths != candidate_paths:
        return _rejected_path_set(baseline_paths, candidate_paths)

    baseline_identity = ProducerIdentityValues.load(baseline_root)
    candidate_identity = ProducerIdentityValues.load(candidate_root)
    artifact_comparisons: list[JsonObject] = []
    unexpected: list[JsonObject] = []
    document_comparison: JsonObject = {}

    for relative_path in sorted(baseline_paths):
        baseline_sha256 = str(baseline_inventory[relative_path]["sha256"])
        candidate_sha256 = str(candidate_inventory[relative_path]["sha256"])
        if baseline_sha256 == candidate_sha256:
            artifact_comparisons.append(
                _comparison_record(
                    relative_path=relative_path,
                    mode="exact_bytes",
                    baseline_sha256=baseline_sha256,
                    candidate_sha256=candidate_sha256,
                    equal=True,
                )
            )
            continue

        comparison, document, failure = _compare_changed_artifact(
            relative_path=relative_path,
            baseline_root=baseline_root,
            candidate_root=candidate_root,
            baseline_sha256=baseline_sha256,
            candidate_sha256=candidate_sha256,
            baseline_identity=baseline_identity,
            candidate_identity=candidate_identity,
            review_pages=review_pages,
        )
        artifact_comparisons.append(comparison)
        if document is not None:
            document_comparison = document
        if failure is not None:
            unexpected.append(failure)

    completion_diff = structural_diff(
        normalized_completion(baseline_root),
        normalized_completion(candidate_root),
    )
    if completion_diff["total_difference_count"]:
        unexpected.append(
            {
                "path": "records/completion_record.json",
                "kind": "undeclared_completion_change",
                "diff": completion_diff,
            }
        )

    return {
        "status": "pass" if not unexpected else "reject",
        "reason": None if not unexpected else "one or more undeclared producer changes",
        "baseline_run_id": baseline_id,
        "candidate_run_id": candidate_id,
        "artifact_path_set": {
            "baseline_count": len(baseline_paths),
            "candidate_count": len(candidate_paths),
            "equal": True,
        },
        "artifact_comparisons": artifact_comparisons,
        "document_comparison": document_comparison,
        "unexpected_changes": unexpected,
    }
