"""Compare clean parser artifacts with the accepted Task 03A behavioral oracle."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from er_commons.document_extraction.artifacts import load_json, stable_json_sha256
from er_commons.source_freeze import sha256_file

STABLE_CONVERSION_RECORD_FIELDS = (
    "source_id",
    "source_sha256",
    "first_page",
    "last_page",
    "status",
    "errors",
    "captured_python_warnings",
    "source_manifest_warnings",
    "pipeline_class",
    "backend_class",
)


def normalize_document_json(payload: Any) -> Any:
    """Replace only known generated image data URIs, retaining all metadata."""
    normalized = copy.deepcopy(payload)
    pages = normalized.get("pages", {}) if isinstance(normalized, dict) else {}
    for page in pages.values():
        image = page.get("image") if isinstance(page, dict) else None
        if isinstance(image, dict) and "uri" in image:
            image["uri"] = "<generated-image-data-uri>"
    pictures = normalized.get("pictures", []) if isinstance(normalized, dict) else []
    for picture in pictures:
        image = picture.get("image") if isinstance(picture, dict) else None
        if isinstance(image, dict) and "uri" in image:
            image["uri"] = "<generated-image-data-uri>"
    for table in normalized.get("tables", []) if isinstance(normalized, dict) else []:
        if isinstance(table, dict) and "data" in table:
            table["data"] = "<owned-by-clean-table-pipeline>"
    return normalized


def normalize_conversion_pages(payload: Any) -> Any:
    """Remove only TableFormer predictions from otherwise complete page state."""
    normalized = copy.deepcopy(payload)
    for page in normalized.get("pages", []) if isinstance(normalized, dict) else []:
        predictions = page.get("predictions") if isinstance(page, dict) else None
        if isinstance(predictions, dict) and "tablestructure" in predictions:
            predictions["tablestructure"] = "<owned-by-clean-table-pipeline>"
    return normalized


def stable_conversion_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Select the conversion fields that belong to parser semantics."""
    return {field: payload.get(field) for field in STABLE_CONVERSION_RECORD_FIELDS}


def _summary(value: Any) -> Any:
    """Keep diff records readable when a changed value is a large payload."""
    if isinstance(value, str) and len(value) > 200:
        return {
            "type": "string",
            "length": len(value),
            "sha256": hashlib.sha256(value.encode()).hexdigest(),
        }
    if isinstance(value, (dict, list)):
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if len(encoded) > 500:
            return {
                "type": type(value).__name__,
                "length": len(value),
                "canonical_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
            }
    return value


def structural_diff(
    old: Any,
    new: Any,
    *,
    limit: int = 50,
    path: str = "$",
) -> dict[str, Any]:
    """Count all structural differences and retain only the first bounded set."""
    differences: list[dict[str, Any]] = []
    total = 0

    def visit(left: Any, right: Any, location: str) -> None:
        nonlocal total
        if type(left) is not type(right):
            total += 1
            if len(differences) < limit:
                differences.append(
                    {
                        "path": location,
                        "kind": "type",
                        "old": type(left).__name__,
                        "new": type(right).__name__,
                    }
                )
            return
        if isinstance(left, dict):
            for key in sorted(set(left) | set(right)):
                child = f"{location}.{key}"
                if key not in left:
                    total += 1
                    if len(differences) < limit:
                        differences.append(
                            {"path": child, "kind": "added", "new": _summary(right[key])}
                        )
                elif key not in right:
                    total += 1
                    if len(differences) < limit:
                        differences.append(
                            {"path": child, "kind": "removed", "old": _summary(left[key])}
                        )
                else:
                    visit(left[key], right[key], child)
            return
        if isinstance(left, list):
            if len(left) != len(right):
                total += 1
                if len(differences) < limit:
                    differences.append(
                        {
                            "path": location,
                            "kind": "length",
                            "old": len(left),
                            "new": len(right),
                        }
                    )
            for index, (left_item, right_item) in enumerate(zip(left, right, strict=False)):
                visit(left_item, right_item, f"{location}[{index}]")
            return
        if isinstance(left, float) and math.isnan(left) and math.isnan(right):
            return
        if left != right:
            total += 1
            if len(differences) < limit:
                differences.append(
                    {
                        "path": location,
                        "kind": "value",
                        "old": _summary(left),
                        "new": _summary(right),
                    }
                )

    visit(old, new, path)
    return {
        "total_difference_count": total,
        "difference_count_shown": len(differences),
        "truncated": total > len(differences),
        "differences": differences,
    }


def compare_json_file(
    old_path: Path,
    new_path: Path,
    *,
    mode: str,
) -> dict[str, Any]:
    """Compare one old/new JSON file under the declared normalization."""
    old = load_json(old_path)
    new = load_json(new_path)
    if mode == "conversion_record":
        old = stable_conversion_record(old)
        new = stable_conversion_record(new)
    elif mode == "document":
        old = normalize_document_json(old)
        new = normalize_document_json(new)
    elif mode == "conversion_pages":
        old = normalize_conversion_pages(old)
        new = normalize_conversion_pages(new)
    elif mode != "full":
        raise ValueError(f"unknown JSON comparison mode: {mode}")
    diff = structural_diff(old, new)
    return {
        "file": new_path.name,
        "mode": mode,
        "old_raw_sha256": sha256_file(old_path),
        "new_raw_sha256": sha256_file(new_path),
        "old_sha256": stable_json_sha256(old),
        "new_sha256": stable_json_sha256(new),
        "equal": diff["total_difference_count"] == 0,
        **diff,
    }


def compare_range_outputs(
    baseline_root: Path,
    candidate_root: Path,
    expected_range_names: list[str],
) -> dict[str, Any]:
    """Compare all semantic JSON outputs for the exact fixed range set."""
    baseline_ranges = baseline_root / "raw_docling"
    candidate_ranges = candidate_root / "ranges"
    actual_baseline = sorted(path.name for path in baseline_ranges.iterdir() if path.is_dir())
    actual_candidate = sorted(path.name for path in candidate_ranges.iterdir() if path.is_dir())
    expected = sorted(expected_range_names)
    range_set_equal = actual_baseline == expected and actual_candidate == expected

    ranges = []
    for name in expected_range_names:
        baseline = baseline_ranges / name
        candidate = candidate_ranges / name
        files = [
            compare_json_file(
                baseline / "document.json",
                candidate / "document.json",
                mode="document",
            ),
            compare_json_file(
                baseline / "conversion_pages.json",
                candidate / "conversion_pages.json",
                mode="conversion_pages",
            ),
            compare_json_file(
                baseline / "conversion_record.json",
                candidate / "conversion_record.json",
                mode="conversion_record",
            ),
        ]
        ranges.append(
            {
                "range_name": name,
                "equal": all(file["equal"] for file in files),
                "files": files,
            }
        )
    return {
        "normalization": (
            "document.json replaces only known generated page/picture data-URI values; "
            "conversion_pages.json excludes only TableFormer predictions; conversion_record.json "
            "compares the declared stable field set"
        ),
        "expected_range_names": expected_range_names,
        "baseline_range_names": actual_baseline,
        "candidate_range_names": actual_candidate,
        "range_set_equal": range_set_equal,
        "ranges": ranges,
        "exact_semantic_match": range_set_equal and all(item["equal"] for item in ranges),
    }


def compare_timings(
    old_records: list[dict[str, Any]],
    new_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Report range and total wall-time differences without making them a gate."""
    old_by_range = {
        (record["source_id"], record["first_page"], record["last_page"]): record
        for record in old_records
    }
    ranges = []
    for new in new_records:
        key = (new["source_id"], new["first_page"], new["last_page"])
        old = old_by_range[key]
        old_seconds = float(old["wall_seconds"])
        new_seconds = float(new["wall_seconds"])
        difference = new_seconds - old_seconds
        ranges.append(
            {
                "source_id": key[0],
                "first_page": key[1],
                "last_page": key[2],
                "old_wall_seconds": old_seconds,
                "new_wall_seconds": new_seconds,
                "difference_seconds": difference,
                "difference_percent": difference / old_seconds * 100,
            }
        )
    old_total = sum(float(record["wall_seconds"]) for record in old_records)
    new_total = sum(float(record["wall_seconds"]) for record in new_records)
    difference = new_total - old_total
    return {
        "ranges": ranges,
        "old_total_wall_seconds": old_total,
        "new_total_wall_seconds": new_total,
        "difference_seconds": difference,
        "difference_percent": difference / old_total * 100,
    }
