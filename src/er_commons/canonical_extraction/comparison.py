"""Independent semantic comparison for completed canonical candidates."""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from er_commons.canonical_extraction.publication import (
    sha256_file,
    stable_json_bytes,
    verify_completed_candidate,
    write_json,
)

SEMANTIC_JSONL_PATHS = (
    "canonical/documents.jsonl",
    "canonical/pages.jsonl",
    "canonical/sections.jsonl",
    "canonical/blocks.jsonl",
    "canonical/tables.jsonl",
    "canonical/table_families.jsonl",
    "canonical/figures.jsonl",
    "canonical/images.jsonl",
    "canonical/assets.jsonl",
    "canonical/cross_references.jsonl",
    "observations/routing.jsonl",
    "observations/table_stage.jsonl",
    "observations/conversion.jsonl",
    "mappings/raw_to_canonical.jsonl",
)
IDENTITY_PATH = "records/extraction_identity.json"
MANIFEST_PATH = "records/manifest.json"
SUMMARY_PATH = "records/canonicalization_summary.json"
INVENTORY_PATH = "records/artifact_inventory.json"
COMPLETION_PATH = "records/completion_record.json"
_PROJECT_CODE_FIELDS = frozenset({"git_commit", "git_dirty", "owned_code_bundle_sha256"})
_TERMINAL_HASH_FIELDS = frozenset({"artifact_inventory_sha256", "manifest_sha256"})


@dataclass(frozen=True)
class ComparisonMismatch:
    """One exact semantic or structural difference."""

    path: str
    kind: str
    reference: Any
    candidate: Any


@dataclass(frozen=True)
class ComparedPath:
    """Hashes and comparison result for one candidate-relative path."""

    path: str
    reference_sha256: str
    candidate_sha256: str
    equal: bool
    comparison: Literal["normalized_json", "normalized_jsonl", "exact_bytes"]


@dataclass(frozen=True)
class ComparisonReport:
    """Compact machine-readable result of an independent candidate comparison."""

    schema_version: str
    reference_candidate_id: str
    candidate_id: str
    normalization_policy: tuple[str, ...]
    compared_paths: tuple[ComparedPath, ...]
    mismatches: tuple[ComparisonMismatch, ...]
    timings_seconds: Mapping[str, float]
    status: Literal["equivalent", "mismatch"]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable report without losing typed boundaries."""
        return asdict(self)


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(stable_json_bytes(value)).hexdigest()


def _escape_pointer(part: str) -> str:
    return part.replace("~", "~0").replace("/", "~1")


def _normalize_id_string(value: str, candidate_id: str) -> str:
    if value == candidate_id:
        return "<EXTRACTION_ID>"
    prefix = f"{candidate_id}/"
    if value.startswith(prefix):
        return f"<EXTRACTION_ID>/{value[len(prefix) :]}"
    return value


def _normalize_ids(value: Any, candidate_id: str) -> Any:
    if isinstance(value, str):
        return _normalize_id_string(value, candidate_id)
    if isinstance(value, list):
        return [_normalize_ids(item, candidate_id) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_ids(item, candidate_id) for key, item in value.items()}
    return value


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def _load_jsonl(path: Path) -> list[Any]:
    records = []
    with path.open() as stream:
        for line_number, line in enumerate(stream, start=1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(f"{path}:{line_number}: invalid JSON: {error.msg}") from error
    return records


def _record_differences(
    reference: Any,
    candidate: Any,
    path: str,
    mismatches: list[ComparisonMismatch],
) -> None:
    if type(reference) is not type(candidate):
        mismatches.append(
            ComparisonMismatch(path, "type", type(reference).__name__, type(candidate).__name__)
        )
        return
    if isinstance(reference, dict):
        reference_keys = set(reference)
        candidate_keys = set(candidate)
        for key in sorted(reference_keys - candidate_keys):
            mismatches.append(
                ComparisonMismatch(
                    f"{path}/{_escape_pointer(str(key))}", "missing", reference[key], None
                )
            )
        for key in sorted(candidate_keys - reference_keys):
            mismatches.append(
                ComparisonMismatch(
                    f"{path}/{_escape_pointer(str(key))}", "unexpected", None, candidate[key]
                )
            )
        for key in sorted(reference_keys & candidate_keys):
            _record_differences(
                reference[key],
                candidate[key],
                f"{path}/{_escape_pointer(str(key))}",
                mismatches,
            )
        return
    if isinstance(reference, list):
        if len(reference) != len(candidate):
            mismatches.append(
                ComparisonMismatch(f"{path}/length", "length", len(reference), len(candidate))
            )
        for index, (old_item, new_item) in enumerate(zip(reference, candidate, strict=False)):
            _record_differences(old_item, new_item, f"{path}/{index}", mismatches)
        return
    if reference != candidate:
        mismatches.append(ComparisonMismatch(path, "value", reference, candidate))


def _identity_projection(identity: Any, candidate_id: str) -> Any:
    projected = _normalize_ids(identity, candidate_id)
    if not isinstance(projected, dict):
        return projected
    projected["identity_sha256"] = "<IDENTITY_SHA256>"
    project_code = projected.get("project_code")
    if isinstance(project_code, dict):
        for field in _PROJECT_CODE_FIELDS:
            if field in project_code:
                project_code[field] = f"<PROJECT_CODE:{field}>"
    return projected


def _normalized_jsonl(path: Path, candidate_id: str) -> list[Any]:
    normalized = _normalize_ids(_load_jsonl(path), candidate_id)
    if not isinstance(normalized, list):
        raise TypeError(f"normalized JSONL is not a record list: {path}")
    return normalized


def _normalized_record_hash(path: Path, candidate_id: str) -> str:
    return _sha256_json(_normalized_jsonl(path, candidate_id))


def _manifest_projection(root: Path, candidate_id: str) -> Any:
    manifest = _normalize_ids(_load_json(root / MANIFEST_PATH), candidate_id)
    if not isinstance(manifest, dict):
        return manifest
    manifest["identity_sha256"] = "<IDENTITY_SHA256>"
    for record_file in manifest.get("record_files", []):
        relative_path = record_file.get("path")
        if isinstance(relative_path, str) and relative_path in SEMANTIC_JSONL_PATHS:
            record_file["sha256"] = _normalized_record_hash(root / relative_path, candidate_id)
    return manifest


def _summary_projection(root: Path, candidate_id: str) -> Any:
    return _normalize_ids(_load_json(root / SUMMARY_PATH), candidate_id)


def _completion_projection(root: Path, candidate_id: str) -> Any:
    completion = _normalize_ids(_load_json(root / COMPLETION_PATH), candidate_id)
    if isinstance(completion, dict):
        for field in _TERMINAL_HASH_FIELDS:
            if field in completion:
                completion[field] = f"<TERMINAL_HASH:{field}>"
    return completion


def _semantic_inventory_entry(
    root: Path,
    candidate_id: str,
    entry: Mapping[str, Any],
) -> dict[str, Any]:
    projected = dict(entry)
    relative = projected.get("path")
    if relative in SEMANTIC_JSONL_PATHS:
        projected["sha256"] = _normalized_record_hash(root / str(relative), candidate_id)
    elif relative == IDENTITY_PATH:
        projected["sha256"] = _sha256_json(
            _identity_projection(_load_json(root / IDENTITY_PATH), candidate_id)
        )
        projected["byte_size"] = "<IDENTITY_DEPENDENT>"
    elif relative == MANIFEST_PATH:
        projected["sha256"] = _sha256_json(_manifest_projection(root, candidate_id))
    elif relative == SUMMARY_PATH:
        projected["sha256"] = _sha256_json(_summary_projection(root, candidate_id))
    return projected


def _inventory_projection(root: Path, candidate_id: str) -> Any:
    inventory = _load_json(root / INVENTORY_PATH)
    if not isinstance(inventory, dict):
        return inventory
    projected = dict(inventory)
    files = projected.get("files")
    if isinstance(files, list):
        projected["files"] = [
            _semantic_inventory_entry(root, candidate_id, entry)
            if isinstance(entry, dict)
            else entry
            for entry in files
        ]
    projected["byte_size"] = "<IDENTITY_DEPENDENT_AGGREGATE>"
    return projected


def _clean_asset_paths(root: Path) -> tuple[str, ...]:
    documents = root / "documents"
    if not documents.exists():
        return ()
    return tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in documents.glob("*/assets/tables/*/*.json")
            if path.name in {"cells.json", "table.json"}
        )
    )


def _required_path_mismatches(
    label: str,
    root: Path,
) -> list[ComparisonMismatch]:
    required = (*SEMANTIC_JSONL_PATHS, IDENTITY_PATH, MANIFEST_PATH, SUMMARY_PATH)
    return [
        ComparisonMismatch(
            f"/verification/{label}/{relative_path}",
            "missing_required_path",
            "file",
            None,
        )
        for relative_path in required
        if not (root / relative_path).is_file()
    ]


def _compare_value(
    relative_path: str,
    reference: Any,
    candidate: Any,
    reference_root: Path,
    candidate_root: Path,
    comparison: Literal["normalized_json", "normalized_jsonl"],
    compared: list[ComparedPath],
    mismatches: list[ComparisonMismatch],
) -> None:
    before = len(mismatches)
    _record_differences(reference, candidate, f"/{relative_path}", mismatches)
    compared.append(
        ComparedPath(
            path=relative_path,
            reference_sha256=sha256_file(reference_root / relative_path),
            candidate_sha256=sha256_file(candidate_root / relative_path),
            equal=len(mismatches) == before,
            comparison=comparison,
        )
    )


def _compare_exact_files(
    paths: Sequence[str],
    reference_root: Path,
    candidate_root: Path,
    compared: list[ComparedPath],
    mismatches: list[ComparisonMismatch],
) -> None:
    for relative_path in paths:
        old_hash = sha256_file(reference_root / relative_path)
        new_hash = sha256_file(candidate_root / relative_path)
        equal = old_hash == new_hash
        compared.append(ComparedPath(relative_path, old_hash, new_hash, equal, "exact_bytes"))
        if not equal:
            mismatches.append(
                ComparisonMismatch(f"/{relative_path}", "byte_content", old_hash, new_hash)
            )


def _verification_mismatch(
    label: str,
    root: Path,
    candidate_id: str,
) -> ComparisonMismatch | None:
    try:
        verify_completed_candidate(root, candidate_id)
    except (OSError, ValueError, KeyError, TypeError) as error:
        return ComparisonMismatch(f"/verification/{label}", "invalid_candidate", None, str(error))
    return None


def _terminal_structure_mismatches(
    label: str,
    root: Path,
) -> list[ComparisonMismatch]:
    completion = _load_json(root / COMPLETION_PATH)
    if not isinstance(completion, dict):
        return [
            ComparisonMismatch(
                f"/verification/{label}/completion_record",
                "type",
                "object",
                type(completion).__name__,
            )
        ]
    expected_manifest_hash = sha256_file(root / MANIFEST_PATH)
    actual_manifest_hash = completion.get("manifest_sha256")
    if actual_manifest_hash != expected_manifest_hash:
        return [
            ComparisonMismatch(
                f"/verification/{label}/completion_record/manifest_sha256",
                "seal",
                expected_manifest_hash,
                actual_manifest_hash,
            )
        ]
    return []


def compare_completed_candidates(
    reference_root: Path,
    candidate_root: Path,
    *,
    report_path: Path | None = None,
    run_timings_seconds: Mapping[str, float] | None = None,
) -> ComparisonReport:
    """Compare two sealed candidates and optionally write the typed report."""
    started = time.perf_counter()
    reference_root = reference_root.resolve()
    candidate_root = candidate_root.resolve()
    reference_id = reference_root.name
    candidate_id = candidate_root.name
    mismatches: list[ComparisonMismatch] = []
    compared: list[ComparedPath] = []

    verify_started = time.perf_counter()
    for label, root, identifier in (
        ("reference", reference_root, reference_id),
        ("candidate", candidate_root, candidate_id),
    ):
        mismatch = _verification_mismatch(label, root, identifier)
        if mismatch is not None:
            mismatches.append(mismatch)
        else:
            mismatches.extend(_terminal_structure_mismatches(label, root))
            mismatches.extend(_required_path_mismatches(label, root))
    verify_seconds = time.perf_counter() - verify_started

    if not mismatches:
        for relative_path in SEMANTIC_JSONL_PATHS:
            _compare_value(
                relative_path,
                _normalized_jsonl(reference_root / relative_path, reference_id),
                _normalized_jsonl(candidate_root / relative_path, candidate_id),
                reference_root,
                candidate_root,
                "normalized_jsonl",
                compared,
                mismatches,
            )

        for relative_path, old_value, new_value in (
            (
                IDENTITY_PATH,
                _identity_projection(_load_json(reference_root / IDENTITY_PATH), reference_id),
                _identity_projection(_load_json(candidate_root / IDENTITY_PATH), candidate_id),
            ),
            (
                MANIFEST_PATH,
                _manifest_projection(reference_root, reference_id),
                _manifest_projection(candidate_root, candidate_id),
            ),
            (
                SUMMARY_PATH,
                _summary_projection(reference_root, reference_id),
                _summary_projection(candidate_root, candidate_id),
            ),
            (
                COMPLETION_PATH,
                _completion_projection(reference_root, reference_id),
                _completion_projection(candidate_root, candidate_id),
            ),
            (
                INVENTORY_PATH,
                _inventory_projection(reference_root, reference_id),
                _inventory_projection(candidate_root, candidate_id),
            ),
        ):
            _compare_value(
                relative_path,
                old_value,
                new_value,
                reference_root,
                candidate_root,
                "normalized_json",
                compared,
                mismatches,
            )

        old_assets = _clean_asset_paths(reference_root)
        new_assets = _clean_asset_paths(candidate_root)
        for relative_path in sorted(set(old_assets) - set(new_assets)):
            mismatches.append(
                ComparisonMismatch(
                    f"/generated_clean_assets/missing/{_escape_pointer(relative_path)}",
                    "missing",
                    relative_path,
                    None,
                )
            )
        for relative_path in sorted(set(new_assets) - set(old_assets)):
            mismatches.append(
                ComparisonMismatch(
                    f"/generated_clean_assets/unexpected/{_escape_pointer(relative_path)}",
                    "unexpected",
                    None,
                    relative_path,
                )
            )
        _compare_exact_files(
            tuple(sorted(set(old_assets) & set(new_assets))),
            reference_root,
            candidate_root,
            compared,
            mismatches,
        )

    total_seconds = time.perf_counter() - started
    timings = {
        key: float(value)
        for key, value in (run_timings_seconds or {}).items()
        if math.isfinite(value) and value >= 0
    }
    timings.update(
        {
            "comparison_verification": round(verify_seconds, 6),
            "comparison_total": round(total_seconds, 6),
        }
    )
    report = ComparisonReport(
        schema_version="er_commons.canonical_candidate_comparison.v1",
        reference_candidate_id=reference_id,
        candidate_id=candidate_id,
        normalization_policy=(
            "exact extraction IDs and extraction-ID-prefixed record IDs",
            "identity_sha256 and project_code Git/code fields",
            "manifest record hashes recomputed after record-ID normalization",
            "candidate-relative terminal hashes and inventory aggregate byte size",
        ),
        compared_paths=tuple(compared),
        mismatches=tuple(mismatches),
        timings_seconds=timings,
        status="equivalent" if not mismatches else "mismatch",
    )
    if report_path is not None:
        write_json(report_path, report.to_dict())
    return report
