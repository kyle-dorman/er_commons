"""Build a source-free ledger of Task 03H K2 scaling evidence."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import resource
import sys
import time
from collections import defaultdict
from collections.abc import Callable
from heapq import heappush, heapreplace
from itertools import zip_longest
from pathlib import Path
from typing import Any

import ijson  # type: ignore[import-untyped]

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.document_parsing.heading_evidence_parsing.text_evidence import (
    LayoutEvidence,
    align_parsed_line,
    normalize_text,
)

TASK_ROOT = Path("pipelines/brisbane_baylands/task_03h")
SOURCE_ID = "deir_appendix_k2_part_5_of_5"
LARGE_PAYLOAD_NAMES = ("conversion_pages.json", "document.json")

JsonObject = dict[str, Any]
ProgressCallback = Callable[[int, int, float], None]
LOGGER = logging.getLogger(__name__)
LEVEL_LINE = re.compile(rb'^(?P<prefix>\s*"level": )(?P<level>[0-9]+)(?P<suffix>,?\r?\n?)$')


def write_task03h_gate1_ledger(data_root: Path) -> Path:
    """Write the exact metadata ledger without reading payload, PDF, or model bytes."""
    report = build_task03h_gate1_ledger(data_root)
    output = data_root / TASK_ROOT / "performance" / "task03h_gate1_scaling_ledger.json"
    write_json_atomic(output, report)
    return output


def write_conversion_pages_profile(
    data_root: Path,
    conversion_pages_path: Path,
    *,
    expected_page_count: int,
) -> Path:
    """Profile page-owned JSON fields one page at a time from sealed evidence."""
    parse_root = data_root.resolve() / TASK_ROOT / "document_parse_evidence"
    resolved_input = conversion_pages_path.resolve()
    if not resolved_input.is_relative_to(parse_root):
        raise ValueError(f"conversion pages input is outside Task 03H evidence: {resolved_input}")
    owner = _owner_root(parse_root, resolved_input)
    inventory_path = owner / "records/artifact_inventory.json"
    completion_path = owner / "records/completion_record.json"
    inventory = _inventory_by_path(owner)
    entry = inventory.get(resolved_input.relative_to(owner).as_posix())
    if entry is None or not completion_path.is_file():
        raise ValueError(f"conversion pages input is not sealed: {resolved_input}")
    report = profile_conversion_pages(
        conversion_pages_path,
        expected_page_count=expected_page_count,
        progress=_log_progress,
    )
    report["input_seal"] = {
        "owner_path": owner.relative_to(data_root.resolve()).as_posix(),
        "payload_sha256_from_inventory": entry["sha256"],
        "payload_byte_size_from_inventory": entry["byte_size"],
        "inventory_path": inventory_path.relative_to(data_root.resolve()).as_posix(),
        "inventory_sha256": sha256_file(inventory_path),
        "completion_path": completion_path.relative_to(data_root.resolve()).as_posix(),
        "completion_sha256": sha256_file(completion_path),
        "payload_checksum_recomputed": False,
    }
    output = data_root.resolve() / TASK_ROOT / "performance/task03h_conversion_pages_profile.json"
    write_json_atomic(output, report)
    return output


def bind_existing_conversion_pages_profile(
    data_root: Path,
    conversion_pages_path: Path,
) -> Path:
    """Attach current seal references to the completed one-time field scan."""
    data_root = data_root.resolve()
    output = data_root / TASK_ROOT / "performance/task03h_conversion_pages_profile.json"
    report = _object(output)
    if report.get("file_byte_size") != conversion_pages_path.stat().st_size:
        raise ValueError("existing conversion-pages profile byte size differs")
    report["input_seal"] = _sealed_payload_reference(
        data_root,
        conversion_pages_path.resolve(),
    )
    write_json_atomic(output, report)
    return output


def write_document_level_overlay_profile(
    data_root: Path,
    baseline_path: Path,
    heading_path: Path,
) -> Path:
    """Publish the bounded whole-file comparison of two sealed document variants."""
    data_root = data_root.resolve()
    report = profile_document_level_overlay(baseline_path, heading_path)
    report["input_seals"] = [
        _sealed_payload_reference(data_root, path.resolve())
        for path in (baseline_path, heading_path)
    ]
    output = data_root / TASK_ROOT / "performance/task03h_document_level_overlay_profile.json"
    write_json_atomic(output, report)
    return output


def write_alignment_scaling_benchmark(data_root: Path) -> Path:
    """Write the bounded old-versus-indexed alignment scaling experiment."""
    report = benchmark_alignment_scaling()
    output = data_root.resolve() / TASK_ROOT / "performance/task03h_alignment_scaling.json"
    write_json_atomic(output, report)
    return output


def write_table_bundle_comparison(
    data_root: Path,
    baseline_table_root: Path,
    heading_table_root: Path,
) -> Path:
    """Compare two sealed table trees while excluding runtime-only measurements."""
    data_root = data_root.resolve()
    report = compare_table_bundles(baseline_table_root, heading_table_root)
    report["input_seals"] = [
        _sealed_owner_reference(data_root, root.resolve().parents[3])
        for root in (baseline_table_root, heading_table_root)
    ]
    output = data_root / TASK_ROOT / "performance/task03h_table_bundle_comparison.json"
    write_json_atomic(output, report)
    return output


def write_assembled_reconstruction_profile(
    data_root: Path,
    conversion_pages_path: Path,
    *,
    expected_page_count: int,
) -> Path:
    """Prove that global assembled lists equal concatenated page-owned lists."""
    data_root = data_root.resolve()
    report = profile_assembled_reconstruction(
        conversion_pages_path,
        expected_page_count=expected_page_count,
        progress=_log_progress,
    )
    report["input_seal"] = _sealed_payload_reference(
        data_root,
        conversion_pages_path.resolve(),
    )
    output = data_root / TASK_ROOT / "performance/task03h_assembled_reconstruction.json"
    write_json_atomic(output, report)
    return output


def write_alignment_projection_profile(
    data_root: Path,
    conversion_pages_path: Path,
    *,
    expected_page_count: int,
) -> Path:
    """Build and measure a provisional JSON Lines hierarchy alignment projection."""
    data_root = data_root.resolve()
    performance_root = data_root / TASK_ROOT / "performance"
    performance_root.mkdir(parents=True, exist_ok=True)
    projection_path = performance_root / "task03h_alignment_projection.jsonl"
    report = build_alignment_projection(
        conversion_pages_path,
        projection_path,
        expected_page_count=expected_page_count,
        progress=_log_progress,
    )
    report["input_seal"] = _sealed_payload_reference(
        data_root,
        conversion_pages_path.resolve(),
    )
    output = performance_root / "task03h_alignment_projection_profile.json"
    write_json_atomic(output, report)
    return output


def profile_conversion_pages(
    path: Path,
    *,
    expected_page_count: int,
    progress: ProgressCallback | None = None,
) -> JsonObject:
    """Measure encoded page fields without constructing the complete 22 GB object graph."""
    started = time.perf_counter()
    field_bytes: dict[str, int] = defaultdict(int)
    collection_counts: dict[str, int] = defaultdict(int)
    largest_pages: list[tuple[int, int]] = []
    page_encoded_bytes = 0
    with path.open("rb") as stream:
        pages = ijson.items(stream, "pages.item", use_float=True)
        for index in range(expected_page_count):
            try:
                page = next(pages)
            except StopIteration as error:
                raise ValueError(
                    f"conversion pages ended before page {index + 1}: {path}"
                ) from error
            if not isinstance(page, dict):
                raise ValueError(f"conversion page is not an object: {index + 1}")
            page_no = page.get("page_no")
            if page_no != index + 1:
                raise ValueError(f"conversion page order differs: {page_no} != {index + 1}")
            encoded_bytes = _encoded_json_bytes(page)
            page_encoded_bytes += encoded_bytes
            _keep_largest(largest_pages, (encoded_bytes, page_no), count=25)
            _measure_fields(field_bytes, collection_counts, page)
            processed = index + 1
            if progress is not None and (processed % 100 == 0 or processed == expected_page_count):
                progress(processed, expected_page_count, time.perf_counter() - started)
    file_bytes = path.stat().st_size
    return {
        "schema_version": "er_commons.task03h_conversion_pages_profile.v1",
        "source_id": SOURCE_ID,
        "path": path.as_posix(),
        "streaming_parser": {"package": "ijson", "backend": ijson.backend},
        "execution_boundary": {
            "source_pdf_bytes_read": False,
            "model_files_read": False,
            "docling_constructed": False,
            "conversion_pages_bytes_read": True,
            "complete_json_object_constructed": False,
            "maximum_constructed_scope": "one pages[] item",
        },
        "file_byte_size": file_bytes,
        "page_count": expected_page_count,
        "pages_reencoded_byte_size": page_encoded_bytes,
        "raw_wrapper_assembled_confidence_and_formatting_bytes": file_bytes - page_encoded_bytes,
        "page_field_reencoded_bytes": [
            {"field": field, "byte_size": size}
            for field, size in sorted(field_bytes.items(), key=lambda item: (-item[1], item[0]))
        ],
        "collection_item_counts": [
            {"field": field, "item_count": count}
            for field, count in sorted(
                collection_counts.items(), key=lambda item: (-item[1], item[0])
            )
        ],
        "largest_pages": [
            {"page_no": page_no, "reencoded_byte_size": size}
            for size, page_no in sorted(largest_pages, reverse=True)
        ],
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": _peak_rss_bytes(),
        "measurement_note": (
            "field sizes are each value re-encoded with the producing JSON settings; "
            "they rank semantic bulk but overlap when parent and child fields are both reported"
        ),
    }


def _measure_fields(
    field_bytes: dict[str, int],
    collection_counts: dict[str, int],
    page: JsonObject,
) -> None:
    for key, value in page.items():
        _record_field(field_bytes, collection_counts, f"pages[].{key}", value)
    for parent in ("parsed_page", "assembled"):
        value = page.get(parent)
        if not isinstance(value, dict):
            continue
        for key, nested in value.items():
            _record_field(
                field_bytes,
                collection_counts,
                f"pages[].{parent}.{key}",
                nested,
            )


def _record_field(
    field_bytes: dict[str, int],
    collection_counts: dict[str, int],
    field: str,
    value: Any,
) -> None:
    field_bytes[field] += _encoded_json_bytes(value)
    if isinstance(value, list | dict):
        collection_counts[field] += len(value)


def _encoded_json_bytes(value: Any) -> int:
    return len(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=True).encode("utf-8"))


def _keep_largest(values: list[tuple[int, int]], value: tuple[int, int], *, count: int) -> None:
    if len(values) < count:
        heappush(values, value)
    elif value > values[0]:
        heapreplace(values, value)


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def _log_progress(processed: int, total: int, elapsed: float) -> None:
    rate = processed / elapsed if elapsed else 0.0
    LOGGER.info(
        "Profiled conversion pages processed=%d total=%d "
        "elapsed_seconds=%.1f pages_per_second=%.2f",
        processed,
        total,
        elapsed,
        rate,
    )


def profile_document_level_overlay(baseline_path: Path, heading_path: Path) -> JsonObject:
    """Prove whether two pretty-printed documents differ only by heading levels."""
    started = time.perf_counter()
    baseline_raw = hashlib.sha256()
    heading_raw = hashlib.sha256()
    baseline_normalized = hashlib.sha256()
    heading_normalized = hashlib.sha256()
    transitions: dict[str, int] = defaultdict(int)
    level_fields = 0
    differing_levels = 0
    other_differences = 0
    line_count = 0
    with baseline_path.open("rb") as baseline, heading_path.open("rb") as heading:
        for current_line_count, (left, right) in enumerate(
            zip_longest(baseline, heading, fillvalue=b""),
            start=1,
        ):
            line_count = current_line_count
            baseline_raw.update(left)
            heading_raw.update(right)
            left_match = LEVEL_LINE.fullmatch(left)
            right_match = LEVEL_LINE.fullmatch(right)
            if left_match is not None:
                level_fields += 1
            if left_match is not None and right_match is not None:
                left_level = left_match.group("level").decode("ascii")
                right_level = right_match.group("level").decode("ascii")
                left = left_match.group("prefix") + b"0" + left_match.group("suffix")
                right = right_match.group("prefix") + b"0" + right_match.group("suffix")
                if left_level != right_level:
                    differing_levels += 1
                    transitions[f"{left_level}->{right_level}"] += 1
            if left != right:
                other_differences += 1
            baseline_normalized.update(left)
            heading_normalized.update(right)
    return {
        "schema_version": "er_commons.task03h_document_level_overlay_profile.v1",
        "source_id": SOURCE_ID,
        "execution_boundary": {
            "source_pdf_bytes_read": False,
            "model_files_read": False,
            "docling_constructed": False,
            "document_json_bytes_read": True,
            "complete_json_object_constructed": False,
            "maximum_constructed_scope": "one serialized line from each input",
        },
        "baseline": {
            "path": baseline_path.as_posix(),
            "byte_size": baseline_path.stat().st_size,
            "sha256": baseline_raw.hexdigest(),
            "level_normalized_sha256": baseline_normalized.hexdigest(),
        },
        "heading": {
            "path": heading_path.as_posix(),
            "byte_size": heading_path.stat().st_size,
            "sha256": heading_raw.hexdigest(),
            "level_normalized_sha256": heading_normalized.hexdigest(),
        },
        "line_count": line_count,
        "level_field_count": level_fields,
        "differing_level_field_count": differing_levels,
        "level_transitions": [
            {"transition": transition, "count": count}
            for transition, count in sorted(transitions.items())
        ],
        "non_level_differing_line_count": other_differences,
        "level_normalized_documents_identical": baseline_normalized.digest()
        == heading_normalized.digest(),
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": _peak_rss_bytes(),
    }


def compare_table_bundles(baseline_root: Path, heading_root: Path) -> JsonObject:
    """Classify exact and runtime-only differences between two table publications."""
    started = time.perf_counter()
    baseline_inventory = _inventory_file_map(baseline_root / "artifact_inventory.json")
    heading_inventory = _inventory_file_map(heading_root / "artifact_inventory.json")
    baseline_paths = set(baseline_inventory)
    heading_paths = set(heading_inventory)
    common_paths = baseline_paths & heading_paths
    differing = sorted(
        path
        for path in common_paths
        if baseline_inventory[path]["sha256"] != heading_inventory[path]["sha256"]
    )
    normalized_equal: list[str] = []
    semantic_differences: list[JsonObject] = []
    excluded_identity_files: list[str] = []
    for relative in differing:
        if relative == "configuration.json":
            excluded_identity_files.append(relative)
            continue
        left_path = baseline_root / relative
        right_path = heading_root / relative
        if left_path.suffix not in {".json", ".jsonl"}:
            semantic_differences.append({"path": relative, "reason": "non_json_bytes_differ"})
            continue
        equal, differing_keys = _runtime_normalized_json_equal(left_path, right_path)
        if equal:
            normalized_equal.append(relative)
        else:
            semantic_differences.append(
                {"path": relative, "reason": "normalized_json_differs", "keys": differing_keys}
            )
    return {
        "schema_version": "er_commons.task03h_table_bundle_comparison.v1",
        "source_id": SOURCE_ID,
        "execution_boundary": {
            "source_pdf_bytes_read": False,
            "model_files_read": False,
            "docling_constructed": False,
            "table_artifact_bytes_read": True,
            "only_inventory_differences_opened": True,
        },
        "baseline_root": baseline_root.as_posix(),
        "heading_root": heading_root.as_posix(),
        "baseline_file_count": len(baseline_paths),
        "heading_file_count": len(heading_paths),
        "path_sets_equal": baseline_paths == heading_paths,
        "baseline_only_paths": sorted(baseline_paths - heading_paths),
        "heading_only_paths": sorted(heading_paths - baseline_paths),
        "byte_identical_file_count": len(common_paths) - len(differing),
        "byte_differing_file_count": len(differing),
        "runtime_measurement_only_file_count": len(normalized_equal),
        "identity_configuration_files": excluded_identity_files,
        "semantic_difference_count": len(semantic_differences),
        "semantic_differences": semantic_differences,
        "semantically_equivalent": (baseline_paths == heading_paths and not semantic_differences),
        "normalization": {
            "removed_runtime_keys": sorted(RUNTIME_MEASUREMENT_KEYS),
            "removed_identity_keys": sorted(IDENTITY_METADATA_KEYS),
            "excluded_identity_owned_paths": ["configuration.json"],
        },
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": _peak_rss_bytes(),
    }


def _inventory_file_map(path: Path) -> dict[str, JsonObject]:
    payload = _object(path)
    files = payload.get("files")
    if not isinstance(files, list):
        raise ValueError(f"artifact inventory files are invalid: {path}")
    return {str(entry["path"]): entry for entry in files if isinstance(entry, dict)}


RUNTIME_MEASUREMENT_KEYS = {
    "cpu_seconds",
    "inference_seconds",
    "page_wall_seconds_sum",
    "pipeline_wall_seconds",
    "wall_seconds",
}
IDENTITY_METADATA_KEYS = {"pipeline_id"}
ITEM_START_EVENTS = {"start_map", "start_array", "string", "number", "boolean", "null"}


def _runtime_normalized_json_equal(left: Path, right: Path) -> tuple[bool, list[str]]:
    if left.suffix == ".jsonl":
        left_values = [
            _normalize_runtime_json(json.loads(line)) for line in left.read_bytes().splitlines()
        ]
        right_values = [
            _normalize_runtime_json(json.loads(line)) for line in right.read_bytes().splitlines()
        ]
        return left_values == right_values, [] if left_values == right_values else ["jsonl"]
    left_value = json.loads(left.read_bytes())
    right_value = json.loads(right.read_bytes())
    normalized_left = _normalize_runtime_json(left_value)
    normalized_right = _normalize_runtime_json(right_value)
    if normalized_left == normalized_right:
        return True, []
    return False, _different_json_paths(normalized_left, normalized_right)


def _normalize_runtime_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _normalize_runtime_json(nested)
            for key, nested in value.items()
            if key not in RUNTIME_MEASUREMENT_KEYS | IDENTITY_METADATA_KEYS
        }
    if isinstance(value, list):
        return [_normalize_runtime_json(item) for item in value]
    return value


def _different_json_paths(left: Any, right: Any, prefix: str = "") -> list[str]:
    if type(left) is not type(right):
        return [prefix or "/"]
    if isinstance(left, dict):
        paths: list[str] = []
        for key in sorted(set(left) | set(right)):
            child = f"{prefix}/{key}"
            if key not in left or key not in right:
                paths.append(child)
            else:
                paths.extend(_different_json_paths(left[key], right[key], child))
            if len(paths) >= 25:
                break
        return paths
    if isinstance(left, list):
        if len(left) != len(right):
            return [f"{prefix}/length"]
        paths = []
        for index, (left_item, right_item) in enumerate(zip(left, right, strict=True)):
            paths.extend(_different_json_paths(left_item, right_item, f"{prefix}/{index}"))
            if len(paths) >= 25:
                break
        return paths
    return [] if left == right else [prefix or "/"]


def profile_assembled_reconstruction(
    path: Path,
    *,
    expected_page_count: int,
    progress: ProgressCallback | None = None,
) -> JsonObject:
    """Hash normalized parser events for page and global assembled list items."""
    started = time.perf_counter()
    names = ("elements", "headers", "body")
    page_hashes = {name: hashlib.sha256() for name in names}
    global_hashes = {name: hashlib.sha256() for name in names}
    page_counts = dict.fromkeys(names, 0)
    global_counts = dict.fromkeys(names, 0)
    pages_seen = 0
    stopped_after_global_assembled = False
    with path.open("rb") as stream:
        for prefix, event, value in ijson.parse(stream, use_float=True):
            if prefix == "pages.item" and event == "start_map":
                pages_seen += 1
                if progress is not None and (
                    pages_seen % 100 == 0 or pages_seen == expected_page_count
                ):
                    progress(pages_seen, expected_page_count, time.perf_counter() - started)
            for name in names:
                page_root = f"pages.item.assembled.{name}"
                global_root = f"assembled.{name}"
                if prefix.startswith(f"{page_root}.item"):
                    _update_event_hash(
                        page_hashes[name], prefix.removeprefix(page_root), event, value
                    )
                    if prefix == f"{page_root}.item" and event in ITEM_START_EVENTS:
                        page_counts[name] += 1
                elif prefix.startswith(f"{global_root}.item"):
                    _update_event_hash(
                        global_hashes[name], prefix.removeprefix(global_root), event, value
                    )
                    if prefix == f"{global_root}.item" and event in ITEM_START_EVENTS:
                        global_counts[name] += 1
            if prefix == "assembled" and event == "end_map":
                stopped_after_global_assembled = True
                break
    if pages_seen != expected_page_count:
        raise ValueError(f"assembled scan saw {pages_seen} pages, expected {expected_page_count}")
    comparisons = []
    for name in names:
        page_digest = page_hashes[name].hexdigest()
        global_digest = global_hashes[name].hexdigest()
        comparisons.append(
            {
                "field": name,
                "page_item_count": page_counts[name],
                "global_item_count": global_counts[name],
                "page_event_sha256": page_digest,
                "global_event_sha256": global_digest,
                "identical": page_counts[name] == global_counts[name]
                and page_digest == global_digest,
            }
        )
    return {
        "schema_version": "er_commons.task03h_assembled_reconstruction.v1",
        "source_id": SOURCE_ID,
        "path": path.as_posix(),
        "execution_boundary": {
            "source_pdf_bytes_read": False,
            "model_files_read": False,
            "docling_constructed": False,
            "conversion_pages_bytes_read": True,
            "complete_json_object_constructed": False,
            "maximum_constructed_scope": "one parser event",
        },
        "page_count": pages_seen,
        "stopped_after_global_assembled_before_confidence": stopped_after_global_assembled,
        "comparisons": comparisons,
        "all_lists_identical": all(item["identical"] for item in comparisons),
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": _peak_rss_bytes(),
    }


def _update_event_hash(digest: Any, prefix: str, event: str, value: Any) -> None:
    encoded_value = "" if value is None else str(value)
    digest.update(prefix.encode("utf-8"))
    digest.update(b"\0")
    digest.update(event.encode("ascii"))
    digest.update(b"\0")
    digest.update(encoded_value.encode("utf-8"))
    digest.update(b"\n")


def build_alignment_projection(
    input_path: Path,
    output_path: Path,
    *,
    expected_page_count: int,
    progress: ProgressCallback | None = None,
) -> JsonObject:
    """Write one compact JSON line per page with exact current alignment states."""
    started = time.perf_counter()
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    if temporary_path.exists():
        raise FileExistsError(f"stale projection attempt requires inspection: {temporary_path}")
    output_digest = hashlib.sha256()
    total_keys = 0
    ambiguous_keys = 0
    with input_path.open("rb") as stream, temporary_path.open("xb") as output:
        pages = ijson.items(stream, "pages.item", use_float=True)
        for index in range(expected_page_count):
            try:
                page = next(pages)
            except StopIteration as error:
                raise ValueError(f"projection input ended before page {index + 1}") from error
            if not isinstance(page, dict) or page.get("page_no") != index + 1:
                raise ValueError(f"projection page order differs at {index + 1}")
            parsed_page = page.get("parsed_page")
            size = page.get("size")
            if not isinstance(parsed_page, dict) or not isinstance(size, dict):
                raise ValueError(f"projection page fields are invalid at {index + 1}")
            alignment = _build_alignment_index(parsed_page)
            entries = [
                [text, evidence.state, evidence.line_count]
                for text, evidence in sorted(alignment.items())
            ]
            total_keys += len(entries)
            ambiguous_keys += sum(item[1] == "ambiguous" for item in entries)
            record = {
                "page_no": page["page_no"],
                "width": size.get("width"),
                "height": size.get("height"),
                "alignment_index": entries,
            }
            encoded = (json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n").encode(
                "utf-8"
            )
            output.write(encoded)
            output_digest.update(encoded)
            processed = index + 1
            if progress is not None and (processed % 100 == 0 or processed == expected_page_count):
                progress(processed, expected_page_count, time.perf_counter() - started)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary_path, output_path)
    build_seconds = time.perf_counter() - started
    read_digest, read_pages, read_keys, read_seconds = _read_alignment_projection(output_path)
    if read_pages != expected_page_count or read_keys != total_keys:
        raise ValueError("projection readback counts differ")
    if read_digest != output_digest.hexdigest():
        raise ValueError("projection readback checksum differs")
    return {
        "schema_version": "er_commons.task03h_alignment_projection_profile.v1",
        "source_id": SOURCE_ID,
        "execution_boundary": {
            "source_pdf_bytes_read": False,
            "model_files_read": False,
            "docling_constructed": False,
            "conversion_pages_bytes_read": True,
            "complete_json_object_constructed": False,
            "maximum_constructed_scope": "one input page and one output page index",
            "candidate_only_not_accepted_format": True,
        },
        "format": "newline-delimited JSON with one page per line",
        "projection_path": output_path.as_posix(),
        "projection_byte_size": output_path.stat().st_size,
        "projection_sha256": output_digest.hexdigest(),
        "page_count": expected_page_count,
        "normalized_key_count": total_keys,
        "ambiguous_key_count": ambiguous_keys,
        "build_wall_seconds": build_seconds,
        "readback_wall_seconds": read_seconds,
        "readback_bytes_per_second": output_path.stat().st_size / read_seconds,
        "peak_rss_bytes": _peak_rss_bytes(),
    }


def _read_alignment_projection(path: Path) -> tuple[str, int, int, float]:
    started = time.perf_counter()
    digest = hashlib.sha256()
    page_count = 0
    key_count = 0
    with path.open("rb") as stream:
        for line in stream:
            digest.update(line)
            record = json.loads(line)
            page_count += 1
            key_count += len(record["alignment_index"])
    return digest.hexdigest(), page_count, key_count, time.perf_counter() - started


def benchmark_alignment_scaling(
    sizes: tuple[int, ...] = (250, 500, 1000, 2000),
) -> JsonObject:
    """Measure the current Cartesian scan against one normalized page index."""
    measurements: list[JsonObject] = []
    for size in sizes:
        texts = [f"Synthetic heading {index}" for index in range(size)]
        page: JsonObject = {"textline_cells": [{"text": text} for text in texts]}

        started = time.perf_counter()
        current = [align_parsed_line(text, page) for text in texts]
        current_seconds = time.perf_counter() - started

        started = time.perf_counter()
        index = _build_alignment_index(page)
        proposed = [_lookup_alignment(text, index) for text in texts]
        indexed_seconds = time.perf_counter() - started
        if proposed != current:
            raise ValueError(f"indexed alignment differs at synthetic size {size}")
        measurements.append(
            {
                "text_count": size,
                "textline_cell_count": size,
                "current_cartesian_comparisons": size * size,
                "current_wall_seconds": current_seconds,
                "indexed_build_and_lookup_wall_seconds": indexed_seconds,
                "speedup": current_seconds / indexed_seconds if indexed_seconds else None,
            }
        )
    return {
        "schema_version": "er_commons.task03h_alignment_scaling.v1",
        "execution_boundary": {
            "synthetic_only": True,
            "source_pdf_bytes_read": False,
            "model_files_read": False,
            "sealed_payload_bytes_read": False,
        },
        "measurements": measurements,
        "current_doubling_ratios": _doubling_ratios(measurements, "current_wall_seconds"),
        "indexed_doubling_ratios": _doubling_ratios(
            measurements,
            "indexed_build_and_lookup_wall_seconds",
        ),
    }


def _build_alignment_index(page: JsonObject) -> dict[str, LayoutEvidence]:
    cells = page.get("textline_cells")
    if not isinstance(cells, list):
        raise ValueError("parsed page textline_cells is invalid")
    index: dict[str, LayoutEvidence] = {}
    for cell in cells:
        if not isinstance(cell, dict) or not isinstance(cell.get("text"), str):
            raise ValueError("parsed page text line is invalid")
        text = cell["text"]
        normalized = normalize_text(text)
        if normalized in index:
            index[normalized] = LayoutEvidence("ambiguous", None)
        else:
            line_count = len([line for line in text.splitlines() if line.strip()]) or 1
            index[normalized] = LayoutEvidence("unique_aligned", line_count)
    return index


def _lookup_alignment(text: str, index: dict[str, LayoutEvidence]) -> LayoutEvidence:
    return index.get(normalize_text(text), LayoutEvidence("absent", None))


def _doubling_ratios(measurements: list[JsonObject], key: str) -> list[float]:
    ratios: list[float] = []
    for previous, current in zip(measurements, measurements[1:], strict=False):
        previous_value = float(previous[key])
        current_value = float(current[key])
        ratios.append(current_value / previous_value if previous_value else 0.0)
    return ratios


def _sealed_payload_reference(data_root: Path, path: Path) -> JsonObject:
    parse_root = data_root / TASK_ROOT / "document_parse_evidence"
    if not path.is_relative_to(parse_root):
        raise ValueError(f"payload is outside Task 03H evidence: {path}")
    owner = _owner_root(parse_root, path)
    inventory_path = owner / "records/artifact_inventory.json"
    completion_path = owner / "records/completion_record.json"
    entry = _inventory_by_path(owner).get(path.relative_to(owner).as_posix())
    if entry is None or not completion_path.is_file():
        raise ValueError(f"payload is not sealed: {path}")
    return {
        "owner_path": owner.relative_to(data_root).as_posix(),
        "payload_path": path.relative_to(data_root).as_posix(),
        "payload_sha256_from_inventory": entry["sha256"],
        "payload_byte_size_from_inventory": entry["byte_size"],
        "inventory_path": inventory_path.relative_to(data_root).as_posix(),
        "inventory_sha256": sha256_file(inventory_path),
        "completion_path": completion_path.relative_to(data_root).as_posix(),
        "completion_sha256": sha256_file(completion_path),
    }


def _sealed_owner_reference(data_root: Path, owner: Path) -> JsonObject:
    inventory_path = owner / "records/artifact_inventory.json"
    completion_path = owner / "records/completion_record.json"
    if not inventory_path.is_file() or not completion_path.is_file():
        raise ValueError(f"publication is not sealed: {owner}")
    return {
        "owner_path": owner.relative_to(data_root).as_posix(),
        "inventory_path": inventory_path.relative_to(data_root).as_posix(),
        "inventory_sha256": sha256_file(inventory_path),
        "completion_path": completion_path.relative_to(data_root).as_posix(),
        "completion_sha256": sha256_file(completion_path),
    }


def build_task03h_gate1_ledger(data_root: Path) -> JsonObject:
    """Describe K2 payload copies and process timings from small seal records only."""
    data_root = data_root.resolve()
    task_root = data_root / TASK_ROOT
    parse_root = task_root / "document_parse_evidence"
    payloads = _payload_records(data_root, parse_root)
    return {
        "schema_version": "er_commons.task03h_gate1_scaling_ledger.v1",
        "source_id": SOURCE_ID,
        "task_root": TASK_ROOT.as_posix(),
        "execution_boundary": {
            "source_pdf_bytes_read": False,
            "model_files_read": False,
            "docling_constructed": False,
            "large_payload_bytes_read": False,
            "filesystem_metadata_read": True,
            "small_seal_and_event_records_read": True,
        },
        "large_payloads": payloads,
        "content_groups": _content_groups(payloads),
        "payload_totals": _payload_totals(payloads),
        "raw_conversion_metrics": _raw_conversion_metrics(data_root, parse_root),
        "derived_producer_metrics": _derived_producer_metrics(data_root, parse_root),
        "document_process_timings": _process_timings(data_root, task_root),
        "known_consumers": _known_consumers(),
        "limitations": [
            "distinct inodes prove separate path-owned files, not whether APFS extents are shared",
            (
                "unknown checksums on incomplete workspaces are not recomputed from "
                "large payload bytes"
            ),
            "field-level conversion_pages composition requires the separate streaming scan",
            "process RSS samples observed interactively are not reconstructed from event records",
        ],
    }


def _payload_records(data_root: Path, parse_root: Path) -> list[JsonObject]:
    inventory_cache: dict[Path, dict[str, JsonObject]] = {}
    records: list[JsonObject] = []
    for name in LARGE_PAYLOAD_NAMES:
        for path in parse_root.rglob(name):
            if SOURCE_ID not in path.parts:
                continue
            owner = _owner_root(parse_root, path)
            inventory = inventory_cache.setdefault(owner, _inventory_by_path(owner))
            relative_to_owner = path.relative_to(owner).as_posix()
            sealed = (owner / "records/completion_record.json").is_file()
            entry = inventory.get(relative_to_owner)
            stat = path.stat()
            records.append(
                {
                    "path": path.relative_to(data_root).as_posix(),
                    "owner_path": owner.relative_to(data_root).as_posix(),
                    "owner_kind": _owner_kind(parse_root, owner),
                    "publication_state": "sealed" if sealed else "incomplete",
                    "payload_role": name.removesuffix(".json"),
                    "byte_size": stat.st_size,
                    "allocated_bytes": getattr(stat, "st_blocks", 0) * 512,
                    "inode": stat.st_ino,
                    "link_count": stat.st_nlink,
                    "inventory_sha256": entry.get("sha256") if entry else None,
                    "inventory_byte_size": entry.get("byte_size") if entry else None,
                }
            )
    return sorted(records, key=lambda item: (str(item["payload_role"]), str(item["path"])))


def _owner_root(parse_root: Path, path: Path) -> Path:
    relative = path.relative_to(parse_root)
    parts = relative.parts
    if parts[0] == "docling_conversions" and parts[1] == ".tmp":
        return parse_root.joinpath(*parts[:3])
    if parts[0] == "docling_conversions":
        return parse_root.joinpath(*parts[:2])
    if parts[0] == ".tmp":
        return parse_root.joinpath(*parts[:2])
    return parse_root / parts[0]


def _owner_kind(parse_root: Path, owner: Path) -> str:
    relative = owner.relative_to(parse_root)
    if relative.parts[0] == "docling_conversions":
        return "raw_conversion_attempt" if ".tmp" in relative.parts else "raw_conversion"
    return "derived_producer_attempt" if relative.parts[0] == ".tmp" else "derived_producer"


def _inventory_by_path(owner: Path) -> dict[str, JsonObject]:
    path = owner / "records/artifact_inventory.json"
    if not path.is_file():
        return {}
    payload = _object(path)
    files = payload.get("files")
    if not isinstance(files, list):
        raise ValueError(f"artifact inventory files are invalid: {path}")
    result: dict[str, JsonObject] = {}
    for entry in files:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError(f"artifact inventory entry is invalid: {path}")
        result[entry["path"]] = entry
    return result


def _content_groups(payloads: list[JsonObject]) -> list[JsonObject]:
    grouped: dict[tuple[str, str], list[JsonObject]] = defaultdict(list)
    for payload in payloads:
        digest = payload.get("inventory_sha256")
        if isinstance(digest, str):
            grouped[(str(payload["payload_role"]), digest)].append(payload)
    result: list[JsonObject] = []
    for (role, digest), members in sorted(grouped.items()):
        sizes = {int(member["byte_size"]) for member in members}
        if len(sizes) != 1:
            raise ValueError(f"one checksum has differing sizes: {digest}")
        size = sizes.pop()
        inode_count = len({int(member["inode"]) for member in members})
        result.append(
            {
                "payload_role": role,
                "sha256": digest,
                "byte_size": size,
                "path_count": len(members),
                "distinct_inode_count": inode_count,
                "logical_bytes_across_paths": size * len(members),
                "duplicate_logical_bytes_beyond_one_copy": size * (len(members) - 1),
                "paths": [str(member["path"]) for member in members],
            }
        )
    return result


def _payload_totals(payloads: list[JsonObject]) -> JsonObject:
    known = [payload for payload in payloads if isinstance(payload.get("inventory_sha256"), str)]
    unique_content = {
        (str(payload["payload_role"]), str(payload["inventory_sha256"])): int(payload["byte_size"])
        for payload in known
    }
    return {
        "path_count": len(payloads),
        "sealed_path_count": sum(item["publication_state"] == "sealed" for item in payloads),
        "incomplete_path_count": sum(
            item["publication_state"] == "incomplete" for item in payloads
        ),
        "logical_bytes": sum(int(item["byte_size"]) for item in payloads),
        "allocated_bytes_from_stat": sum(int(item["allocated_bytes"]) for item in payloads),
        "known_checksum_path_bytes": sum(int(item["byte_size"]) for item in known),
        "known_unique_content_bytes": sum(unique_content.values()),
        "known_duplicate_logical_bytes": sum(int(item["byte_size"]) for item in known)
        - sum(unique_content.values()),
    }


def _process_timings(data_root: Path, task_root: Path) -> list[JsonObject]:
    attempts_root = task_root / "document_publications" / "attempts"
    records: list[JsonObject] = []
    if not attempts_root.is_dir():
        return records
    for attempt_root in sorted(path for path in attempts_root.iterdir() if path.is_dir()):
        attempt_path = attempt_root / "attempt_record.json"
        preflight_path = attempt_root / "execution_preflight.json"
        attempt = _object(attempt_path) if attempt_path.is_file() else {}
        preflight = _object(preflight_path) if preflight_path.is_file() else {}
        if attempt.get("source_id", preflight.get("source_id")) != SOURCE_ID:
            continue
        for event_path in sorted((attempt_root / "document_process_events").glob("*.json")):
            event = _object(event_path)
            wall_seconds = event.get("wall_seconds")
            if not isinstance(wall_seconds, int | float):
                continue
            records.append(
                {
                    "attempt_path": attempt_root.relative_to(data_root).as_posix(),
                    "transaction_id": attempt.get("transaction_id"),
                    "attempt_record_present": attempt_path.is_file(),
                    "event": event_path.name,
                    "stage": event.get("stage"),
                    "state": event.get("state"),
                    "wall_seconds": wall_seconds,
                    "completion_path": event.get("completion_path"),
                    "message": event.get("message"),
                }
            )
    return records


def _raw_conversion_metrics(data_root: Path, parse_root: Path) -> list[JsonObject]:
    root = parse_root / "docling_conversions"
    records: list[JsonObject] = []
    if not root.is_dir():
        return records
    for observation_path in sorted(
        root.glob(f"dconv1-*/documents/{SOURCE_ID}/producer/docling/conversion_observation.json")
    ):
        observation = _object(observation_path)
        owner = observation_path.parents[4]
        records.append(
            {
                "conversion_id": owner.name,
                "owner_path": owner.relative_to(data_root).as_posix(),
                "status": observation.get("status"),
                "wall_seconds": observation.get("wall_seconds"),
                "cpu_seconds": observation.get("cpu_seconds"),
                "peak_rss_bytes": observation.get("peak_rss_bytes"),
                "expected_page_count": len(observation.get("expected_physical_pages", [])),
                "converted_page_count": len(observation.get("converted_physical_pages", [])),
            }
        )
    return records


def _derived_producer_metrics(data_root: Path, parse_root: Path) -> list[JsonObject]:
    records: list[JsonObject] = []
    for summary_path in sorted(parse_root.glob("prv1-*/records/producer_summary.json")):
        summary = _object(summary_path)
        if summary.get("source_id") != SOURCE_ID:
            continue
        owner = summary_path.parents[1]
        table_summary_path = owner / "documents" / SOURCE_ID / "producer/tables/summary.json"
        table_summary = _object(table_summary_path) if table_summary_path.is_file() else {}
        routing = summary.get("routing")
        tables = summary.get("tables")
        records.append(
            {
                "producer_run_id": summary.get("producer_run_id"),
                "owner_path": owner.relative_to(data_root).as_posix(),
                "status": summary.get("producer_status"),
                "wall_seconds": summary.get("wall_seconds"),
                "conversion_cpu_seconds": summary.get("conversion_cpu_seconds"),
                "peak_rss_bytes": summary.get("peak_rss_bytes"),
                "output_bytes_before_inventory": summary.get("output_bytes_before_inventory"),
                "routing": routing,
                "routed_page_count": tables.get("routed_page_count")
                if isinstance(tables, dict)
                else None,
                "logical_table_count": tables.get("logical_table_count")
                if isinstance(tables, dict)
                else None,
                "family_count": tables.get("family_count") if isinstance(tables, dict) else None,
                "table_pipeline_wall_seconds": table_summary.get("pipeline_wall_seconds"),
                "table_page_wall_seconds_sum": table_summary.get("page_wall_seconds_sum"),
                "stream_table_count": table_summary.get("stream_table_count"),
                "lattice_table_count": table_summary.get("lattice_table_count"),
            }
        )
    return records


def _known_consumers() -> list[JsonObject]:
    return [
        {
            "artifact": "conversion_pages.json",
            "consumer": "hierarchy_inference.inputs.load_hierarchy_inference_inputs",
            "access": "loads the complete JSON object",
            "required_fields": "passes all fields onward without projection",
        },
        {
            "artifact": "conversion_pages.json",
            "consumer": "heading_evidence_parsing.source_features.extract_item_observations",
            "access": "indexes every page and scans textline_cells for every traversed text",
            "required_fields": [
                "pages[].page_no",
                "pages[].size",
                "pages[].parsed_page.textline_cells",
            ],
        },
        {
            "artifact": "conversion_pages.json",
            "consumer": "record_mapping.assets._AssetRegistry.external",
            "access": "registers size and recomputes SHA-256; does not consume semantic fields",
            "required_fields": [],
        },
        {
            "artifact": "document.json",
            "consumer": "content_parsing.conversion_bundle._load_output",
            "access": "loads the complete JSON object during raw conversion reuse",
            "required_fields": ["pages", "pictures", "picture image externalization evidence"],
        },
        {
            "artifact": "document.json",
            "consumer": "record_mapping and heading evidence",
            "access": (
                "loads complete object graphs and traverses texts, groups, tables, and pictures"
            ),
            "required_fields": "requires a separate field projection audit",
        },
    ]


def _object(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


__all__ = [
    "benchmark_alignment_scaling",
    "bind_existing_conversion_pages_profile",
    "build_alignment_projection",
    "build_task03h_gate1_ledger",
    "compare_table_bundles",
    "profile_assembled_reconstruction",
    "profile_document_level_overlay",
    "profile_conversion_pages",
    "write_alignment_projection_profile",
    "write_alignment_scaling_benchmark",
    "write_assembled_reconstruction_profile",
    "write_conversion_pages_profile",
    "write_document_level_overlay_profile",
    "write_table_bundle_comparison",
    "write_task03h_gate1_ledger",
]
