"""Independent behavior-preservation evidence for the human-owned rewrite."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.canonical_extraction.publication import stable_json_bytes

JsonObject = dict[str, Any]

_CONFIGURATION_PATH = "configs/brisbane_baylands_2025_deir_task03e4_semantic_v1.json"
_MVP_CONFIGURATION_SHA256 = "cf2bcd52da018581c92af059191229ff3602a920d64cba3fa7ee4cbf743871d6"
_HUMAN_REWRITE_CONFIGURATION_SHA256 = (
    "fb26c518ae817814608897d34fd65489777c5db553fdc6e871a10196842607bc"
)
_ALLOWED_CONFIGURATION_REFS = frozenset(
    {
        (_CONFIGURATION_PATH, _MVP_CONFIGURATION_SHA256),
        (_CONFIGURATION_PATH, _HUMAN_REWRITE_CONFIGURATION_SHA256),
    }
)


@dataclass(frozen=True)
class ReferenceComparison:
    """Normalized file-level comparison of the MVP and rewritten candidates."""

    reference_candidate_id: str
    candidate_id: str
    candidate_files: list[JsonObject]
    review_files: list[JsonObject]
    mismatches: list[JsonObject]
    review_mismatches: list[JsonObject]
    elapsed_seconds: float

    @property
    def status(self) -> str:
        """Return the publication-facing comparison result."""
        return "equivalent" if not self.mismatches and not self.review_mismatches else "different"

    def report(self) -> JsonObject:
        """Return a compact, persisted comparison report."""
        return {
            "schema_version": "er_commons.semantic_materialization_rewrite_comparison.v2",
            "reference_candidate_id": self.reference_candidate_id,
            "candidate_id": self.candidate_id,
            "normalization": {
                "candidate_id": "replace old/new candidate ID with <EXTRACTION_ID>",
                "identity": [
                    "ignore code bundle digest",
                    "allow only the frozen MVP-to-human-rewrite configuration transition",
                    "ignore the two corrected scalar-ID support preimage hashes; "
                    "compare their files",
                    "ignore derived identity digest",
                ],
                "terminal_records": [
                    "ignore candidate-derived manifest support and record checksums",
                    "ignore inventory file checksums",
                    "ignore completion inventory checksum",
                ],
                "review": (
                    "normalize candidate ID in diagnostics; compare every render and overlay byte"
                ),
            },
            "counts": {
                "candidate_files": len(self.candidate_files),
                "review_files": len(self.review_files),
                "candidate_mismatches": len(self.mismatches),
                "review_mismatches": len(self.review_mismatches),
            },
            "candidate_files": self.candidate_files,
            "review_files": self.review_files,
            "mismatches": self.mismatches,
            "review_mismatches": self.review_mismatches,
            "timings_seconds": {"comparison": self.elapsed_seconds},
            "status": self.status,
        }


def compare_reference_candidate(
    *,
    reference_root: Path,
    candidate_root: Path,
    reference_review_root: Path,
    candidate_review_root: Path,
    reference_candidate_id: str,
    candidate_id: str,
) -> ReferenceComparison:
    """Compare all candidate and review files under only declared normalization."""
    started = time.perf_counter()
    reference_files = _file_map(reference_root)
    candidate_files = _file_map(candidate_root)
    candidate_comparisons, mismatches = _compare_file_maps(
        reference_files,
        candidate_files,
        reference_candidate_id=reference_candidate_id,
        candidate_id=candidate_id,
        kind="candidate",
    )
    reference_review = _file_map(reference_review_root)
    candidate_review = _file_map(candidate_review_root)
    review_comparisons, review_mismatches = _compare_file_maps(
        reference_review,
        candidate_review,
        reference_candidate_id=reference_candidate_id,
        candidate_id=candidate_id,
        kind="review",
    )
    return ReferenceComparison(
        reference_candidate_id=reference_candidate_id,
        candidate_id=candidate_id,
        candidate_files=candidate_comparisons,
        review_files=review_comparisons,
        mismatches=mismatches,
        review_mismatches=review_mismatches,
        elapsed_seconds=time.perf_counter() - started,
    )


def write_comparison_report(root: Path, comparison: ReferenceComparison) -> Path:
    """Atomically retain one no-clobber comparison report keyed by its content."""
    payload = comparison.report()
    digest = hashlib.sha256(stable_json_bytes(_without_timings(payload))).hexdigest()
    report_root = root / f"cmpv1-{digest}"
    report_path = report_root / "comparison_report.json"
    if report_path.exists():
        existing = json.loads(report_path.read_bytes())
        if _without_timings(existing) != _without_timings(payload):
            raise ValueError(f"rewrite comparison report collision: {report_path}")
        return report_path
    root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{report_root.name}.", dir=root))
    try:
        path = staging / "comparison_report.json"
        path.write_bytes(stable_json_bytes(payload))
        staging.rename(report_root)
    except Exception:
        if staging.exists():
            for child in staging.iterdir():
                child.unlink()
            staging.rmdir()
        raise
    return report_path


def _file_map(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _compare_file_maps(
    reference: dict[str, bytes],
    candidate: dict[str, bytes],
    *,
    reference_candidate_id: str,
    candidate_id: str,
    kind: str,
) -> tuple[list[JsonObject], list[JsonObject]]:
    comparisons: list[JsonObject] = []
    mismatches: list[JsonObject] = []
    for relative_path in sorted(set(reference) | set(candidate)):
        old = reference.get(relative_path)
        new = candidate.get(relative_path)
        if old is None or new is None:
            comparison = {
                "path": relative_path,
                "status": "missing",
                "reference_present": old is not None,
                "candidate_present": new is not None,
                "reference_sha256": None if old is None else hashlib.sha256(old).hexdigest(),
                "candidate_sha256": None if new is None else hashlib.sha256(new).hexdigest(),
                "normalized_reference_sha256": None,
                "normalized_candidate_sha256": None,
            }
            comparisons.append(comparison)
            mismatches.append(
                {
                    "path": relative_path,
                    "reason": "file_set",
                    "reference_present": old is not None,
                    "candidate_present": new is not None,
                }
            )
            continue
        old_normalized = _normalized_bytes(old, relative_path, reference_candidate_id, kind=kind)
        new_normalized = _normalized_bytes(new, relative_path, candidate_id, kind=kind)
        normalized_reference_sha256 = hashlib.sha256(old_normalized).hexdigest()
        normalized_candidate_sha256 = hashlib.sha256(new_normalized).hexdigest()
        equivalent = old_normalized == new_normalized
        comparisons.append(
            {
                "path": relative_path,
                "status": "equivalent" if equivalent else "different",
                "reference_present": True,
                "candidate_present": True,
                "reference_sha256": hashlib.sha256(old).hexdigest(),
                "candidate_sha256": hashlib.sha256(new).hexdigest(),
                "normalized_reference_sha256": normalized_reference_sha256,
                "normalized_candidate_sha256": normalized_candidate_sha256,
            }
        )
        if not equivalent:
            mismatches.append(
                {
                    "path": relative_path,
                    "reason": "content",
                    "reference_sha256": normalized_reference_sha256,
                    "candidate_sha256": normalized_candidate_sha256,
                }
            )
    return comparisons, mismatches


def _normalized_bytes(raw: bytes, relative_path: str, candidate_id: str, *, kind: str) -> bytes:
    if relative_path.endswith(".jsonl"):
        records = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
        return stable_json_bytes(
            [_normalize_value(record, candidate_id, relative_path, kind=kind) for record in records]
        )
    if relative_path.endswith(".json"):
        return stable_json_bytes(
            _normalize_value(json.loads(raw), candidate_id, relative_path, kind=kind)
        )
    return raw


def _normalize_value(value: Any, candidate_id: str, relative_path: str, *, kind: str) -> Any:
    normalized = _replace_candidate_id(copy.deepcopy(value), candidate_id)
    if kind == "candidate" and relative_path == "records/extraction_identity.json":
        normalized.pop("extraction_id", None)
        normalized.pop("identity_sha256", None)
        contract = normalized.get("semantic_contract", {})
        contract.pop("owned_code_bundle_sha256", None)
        support_preimages = contract.get("support_preimage_sha256s")
        if isinstance(support_preimages, dict):
            support_preimages.pop("candidate_correspondence", None)
            support_preimages.pop("baseline_preservation", None)
        configuration = contract.get("configuration")
        if not isinstance(configuration, dict):
            raise ValueError("rewrite identity lacks a configuration reference")
        configuration_ref = (configuration.get("path"), configuration.get("sha256"))
        if configuration_ref not in _ALLOWED_CONFIGURATION_REFS:
            raise ValueError(
                f"rewrite identity has an undeclared configuration: {configuration_ref}"
            )
        contract["configuration"] = {"transition": "frozen_task03e4_human_rewrite"}
    elif kind == "candidate" and relative_path == "records/manifest.json":
        normalized.pop("extraction_id", None)
        normalized.pop("identity_sha256", None)
        _drop_key_recursively(normalized, "sha256")
    elif kind == "candidate" and relative_path == "records/artifact_inventory.json":
        _drop_key_recursively(normalized, "sha256")
    elif kind == "candidate" and relative_path == "records/completion_record.json":
        normalized.pop("artifact_inventory_sha256", None)
    elif kind == "review" and relative_path == "review_manifest.json":
        _drop_key_recursively(normalized, "sha256")
    return normalized


def _replace_candidate_id(value: Any, candidate_id: str) -> Any:
    if isinstance(value, str):
        return value.replace(candidate_id, "<EXTRACTION_ID>")
    if isinstance(value, list):
        return [_replace_candidate_id(item, candidate_id) for item in value]
    if isinstance(value, dict):
        return {key: _replace_candidate_id(item, candidate_id) for key, item in value.items()}
    return value


def _drop_key_recursively(value: Any, key: str) -> None:
    if isinstance(value, list):
        for item in value:
            _drop_key_recursively(item, key)
    elif isinstance(value, dict):
        value.pop(key, None)
        for item in value.values():
            _drop_key_recursively(item, key)


def _without_timings(payload: JsonObject) -> JsonObject:
    """Return the deterministic comparison identity projection."""
    normalized = copy.deepcopy(payload)
    normalized.pop("timings_seconds", None)
    return normalized
