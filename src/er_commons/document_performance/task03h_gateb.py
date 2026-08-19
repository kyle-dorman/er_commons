"""Audit and benchmark the Task 03H.1 post-Docling MVP schemas."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import resource
import sqlite3
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

import ijson  # type: ignore[import-untyped]

from er_commons.artifact_io import (
    artifact_inventory,
    read_json_object,
    sha256_file,
    write_json_atomic,
)
from er_commons.document_parsing.content_parsing.evidence import verify_inventory
from er_commons.document_parsing.heading_evidence_parsing.alignment_projection import (
    SCHEMA_VERSION as ALIGNMENT_SCHEMA_VERSION,
)
from er_commons.document_parsing.heading_evidence_parsing.alignment_projection import (
    alignment_record,
)
from er_commons.document_parsing.heading_evidence_parsing.heading_overlay import (
    BASE_LEVEL,
)
from er_commons.document_parsing.heading_evidence_parsing.heading_overlay import (
    SCHEMA_VERSION as OVERLAY_SCHEMA_VERSION,
)

JsonObject = dict[str, Any]
ProgressCallback = Callable[[int, int, float], None]
MASK_256 = (1 << 256) - 1
PARTITION_FIELDS = ("elements", "body", "headers")
_EXTRACTION_ID = re.compile(r"exv1-[0-9a-f]{64}")


class _HashingReader:
    """Hash every byte as a streaming JSON parser consumes it once."""

    def __init__(self, stream: BinaryIO) -> None:
        self._stream = stream
        self.digest = hashlib.sha256()
        self.byte_count = 0

    def read(self, size: int = -1) -> bytes:
        data = self._stream.read(size)
        self.digest.update(data)
        self.byte_count += len(data)
        return data


def derive_legacy_alignment_projection(
    input_path: Path,
    output_path: Path,
    *,
    expected_page_count: int,
    expected_sha256: str,
    progress: ProgressCallback | None = None,
) -> JsonObject:
    """Task-only one-pass migration from legacy conversion pages to current JSONL."""
    started = time.perf_counter()
    temporary = output_path.with_suffix(f"{output_path.suffix}.tmp")
    if output_path.exists() or temporary.exists():
        raise FileExistsError(f"replay output or interrupted attempt exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_digest = hashlib.sha256()
    key_count = 0
    ambiguous_count = 0
    with input_path.open("rb") as raw, temporary.open("xb") as output:
        source = _HashingReader(raw)
        pages = ijson.items(source, "pages.item", use_float=True)
        for expected in range(1, expected_page_count + 1):
            try:
                page = next(pages)
            except StopIteration as error:
                raise ValueError(f"legacy replay ended before page {expected}") from error
            if not isinstance(page, dict) or page.get("page_no") != expected:
                raise ValueError(f"legacy replay page order differs at {expected}")
            parsed = page.get("parsed_page")
            size = page.get("size")
            if not isinstance(parsed, dict) or not isinstance(size, dict):
                raise ValueError(f"legacy replay fields are invalid at page {expected}")
            cells = parsed.get("textline_cells")
            if not isinstance(cells, list):
                raise ValueError(f"legacy replay cells are invalid at page {expected}")
            record = alignment_record(
                page_no=expected,
                width=float(size["width"]),
                height=float(size["height"]),
                textline_cells=cells,
            )
            entries = record["alignment_index"]
            if not isinstance(entries, list):
                raise AssertionError("alignment record emitted a non-list index")
            key_count += len(entries)
            ambiguous_count += sum(entry[1] == "ambiguous" for entry in entries)
            encoded = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode()
            output.write(encoded)
            output_digest.update(encoded)
            if progress is not None and (expected % 100 == 0 or expected == expected_page_count):
                progress(expected, expected_page_count, time.perf_counter() - started)
        for _chunk in iter(lambda: source.read(1024 * 1024), b""):
            pass
        output.flush()
    if source.digest.hexdigest() != expected_sha256:
        raise ValueError("legacy conversion-pages checksum differs during replay")
    temporary.replace(output_path)
    return {
        "schema_version": "er_commons.task03h_legacy_alignment_replay.v1",
        "input_path": input_path.as_posix(),
        "input_sha256": source.digest.hexdigest(),
        "input_byte_size": source.byte_count,
        "output_path": output_path.as_posix(),
        "output_schema_version": ALIGNMENT_SCHEMA_VERSION,
        "output_sha256": output_digest.hexdigest(),
        "output_byte_size": output_path.stat().st_size,
        "page_count": expected_page_count,
        "normalized_key_count": key_count,
        "ambiguous_key_count": ambiguous_count,
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": _peak_rss_bytes(),
        "task_only_migration_code": True,
        "completion_written_last": True,
    }


def derive_legacy_heading_overlay(
    baseline_path: Path,
    heading_path: Path,
    output_path: Path,
    *,
    expected_baseline_sha256: str,
    expected_heading_sha256: str,
) -> JsonObject:
    """Task-only streaming proof that one level overlay reproduces the heading view."""
    started = time.perf_counter()
    if output_path.exists():
        raise FileExistsError(f"heading-overlay output exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with baseline_path.open("rb") as baseline_raw, heading_path.open("rb") as heading_raw:
        baseline = _HashingReader(baseline_raw)
        heading = _HashingReader(heading_raw)
        baseline_items = _leveled_objects(baseline)
        heading_items = _leveled_objects(heading)
        overlay: list[JsonObject] = []
        compared = 0
        while True:
            left = next(baseline_items, None)
            right = next(heading_items, None)
            if left is None or right is None:
                if left != right:
                    raise ValueError("baseline and heading leveled-object counts differ")
                break
            compared += 1
            if left[0] != right[0] or left[1] != BASE_LEVEL:
                raise ValueError(f"legacy heading overlay cannot target {left[0]}")
            if right[1] != BASE_LEVEL:
                overlay.append(
                    {
                        "schema_version": OVERLAY_SCHEMA_VERSION,
                        "raw_self_ref": right[0],
                        "level": right[1],
                    }
                )
        for reader in (baseline, heading):
            while reader.read(1024 * 1024):
                continue
    if baseline.digest.hexdigest() != expected_baseline_sha256:
        raise ValueError("legacy baseline-document checksum differs during replay")
    if heading.digest.hexdigest() != expected_heading_sha256:
        raise ValueError("legacy heading-document checksum differs during replay")
    overlay.sort(key=lambda record: str(record["raw_self_ref"]))
    with output_path.open("xb") as output:
        for record in overlay:
            encoded = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            output.write(encoded.encode())
    return {
        "schema_version": "er_commons.task03h_legacy_heading_overlay_replay.v1",
        "baseline_input_sha256": baseline.digest.hexdigest(),
        "heading_input_sha256": heading.digest.hexdigest(),
        "leveled_object_count": compared,
        "overlay_record_count": len(overlay),
        "output_path": output_path.as_posix(),
        "output_schema_version": OVERLAY_SCHEMA_VERSION,
        "output_sha256": sha256_file(output_path),
        "output_byte_size": output_path.stat().st_size,
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": _peak_rss_bytes(),
        "task_only_migration_code": True,
    }


def _leveled_objects(stream: _HashingReader) -> Iterator[tuple[str, int]]:
    frames: list[dict[str, Any]] = []
    for _prefix, event, value in ijson.parse(stream):
        if event == "start_map":
            frames.append({})
        elif event == "map_key" and frames:
            frames[-1]["key"] = value
        elif event in {"string", "number"} and frames:
            key = frames[-1].get("key")
            if key in {"self_ref", "level"}:
                frames[-1][str(key)] = value
        elif event == "end_map":
            frame = frames.pop()
            pointer = frame.get("self_ref")
            level = frame.get("level")
            if isinstance(pointer, str) and isinstance(level, int):
                yield pointer, level


def forecast_downstream_admission(
    *,
    document_bytes: int,
    text_items: int,
    alignment_cells: int,
    routed_pages: int,
    table_count: int,
    expected_records: int,
) -> JsonObject:
    """Return a conservative density-aware admission forecast for one source."""
    estimated_peak = int(
        document_bytes * 7.5
        + text_items * 900
        + alignment_cells * 180
        + table_count * 80_000
        + expected_records * 600
    )
    estimated_seconds = (
        document_bytes / 80_000_000
        + text_items / 20_000
        + alignment_cells / 80_000
        + routed_pages * 3.25
        + table_count * 0.35
        + expected_records / 25_000
    )
    return {
        "schema_version": "er_commons.downstream_admission_forecast.v1",
        "inputs": {
            "document_bytes": document_bytes,
            "text_items": text_items,
            "alignment_cells": alignment_cells,
            "routed_pages": routed_pages,
            "table_count": table_count,
            "expected_records": expected_records,
        },
        "estimated_peak_rss_bytes": estimated_peak,
        "estimated_critical_path_seconds": estimated_seconds,
        "admitted": estimated_peak < 16 * 1024**3 and estimated_seconds < 3600,
        "limits": {"peak_rss_bytes": 16 * 1024**3, "critical_path_seconds": 3600},
    }


def deep_audit_legacy_conversions(
    conversion_root: Path,
    *,
    progress: Callable[[str, int, int, float], None] | None = None,
) -> JsonObject:
    """Task-only full-byte verification of every frozen legacy conversion seal."""
    started = time.perf_counter()
    roots = sorted(
        path
        for path in conversion_root.glob("dconv1-*")
        if path.is_dir() and (path / "records/completion_record.json").is_file()
    )
    audits: list[JsonObject] = []
    for index, root in enumerate(roots, start=1):
        bundle_started = time.perf_counter()
        completion_path = root / "records/completion_record.json"
        inventory_path = root / "records/artifact_inventory.json"
        completion = json.loads(completion_path.read_bytes())
        inventory = json.loads(inventory_path.read_bytes())
        if completion.get("conversion_id") != root.name:
            raise ValueError(f"legacy conversion ID differs: {root}")
        if completion.get("artifact_inventory_sha256") != sha256_file(inventory_path):
            raise ValueError(f"legacy conversion inventory seal differs: {root}")
        verify_inventory(root, inventory)
        rebuilt = artifact_inventory(
            root,
            excluded={"records/artifact_inventory.json", "records/completion_record.json"},
        )
        if rebuilt != inventory:
            raise ValueError(f"legacy conversion managed file set differs: {root}")
        identity = json.loads((root / "records/conversion_identity.json").read_bytes())
        source = identity.get("identity", {}).get("source", {})
        audits.append(
            {
                "conversion_id": root.name,
                "source_id": source.get("source_id"),
                "managed_file_count": len(inventory.get("files", [])),
                "managed_byte_size": sum(
                    int(record["byte_size"]) for record in inventory.get("files", [])
                ),
                "completion_sha256": sha256_file(completion_path),
                "inventory_sha256": sha256_file(inventory_path),
                "wall_seconds": time.perf_counter() - bundle_started,
            }
        )
        if progress is not None:
            progress(root.name, index, len(roots), time.perf_counter() - started)
    return {
        "schema_version": "er_commons.task03h_legacy_conversion_deep_audit.v1",
        "conversion_root": conversion_root.as_posix(),
        "conversion_count": len(audits),
        "managed_byte_size": sum(int(item["managed_byte_size"]) for item in audits),
        "conversions": audits,
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": _peak_rss_bytes(),
        "source_pdf_bytes_read": False,
        "model_files_read": False,
        "all_managed_conversion_bytes_hashed": True,
    }


def compare_compact_mapping(legacy_root: Path, compact_root: Path) -> JsonObject:
    """Compare regenerated K2 semantics while declaring the compact storage changes."""
    started = time.perf_counter()
    paths = {
        "documents": "canonical/documents.jsonl",
        "pages": "canonical/pages.jsonl",
        "sections": "canonical/sections.jsonl",
        "blocks": "canonical/blocks.jsonl",
        "table_families": "canonical/table_families.jsonl",
        "figures": "canonical/figures.jsonl",
        "routing": "observations/routing.jsonl",
        "table_stage": "observations/table_stage.jsonl",
        "conversion": "observations/conversion.jsonl",
    }
    comparisons: list[JsonObject] = []
    for name, relative in paths.items():
        left = _semantic_jsonl_digest(legacy_root / relative)
        right = _semantic_jsonl_digest(compact_root / relative)
        comparisons.append(
            {
                "collection": name,
                "legacy_count": left[0],
                "compact_count": right[0],
                "legacy_semantic_sha256": left[1],
                "compact_semantic_sha256": right[1],
                "identical": left == right,
            }
        )
    for name, relative, transform in (
        ("images", "canonical/images.jsonl", _image_semantics),
        ("image_assets", "canonical/assets.jsonl", _content_image_asset_semantics),
    ):
        left = _semantic_jsonl_digest(legacy_root / relative, transform=transform)
        right = _semantic_jsonl_digest(compact_root / relative, transform=transform)
        comparisons.append(
            {
                "collection": name,
                "legacy_count": left[0],
                "compact_count": right[0],
                "legacy_semantic_sha256": left[1],
                "compact_semantic_sha256": right[1],
                "identical": left == right,
            }
        )
    legacy_tables = _semantic_jsonl_digest(
        legacy_root / "canonical/tables.jsonl", transform=_compact_table_semantics
    )
    compact_tables = _semantic_jsonl_digest(
        compact_root / "canonical/tables.jsonl", transform=_compact_table_semantics
    )
    comparisons.append(
        {
            "collection": "tables_compact_projection",
            "legacy_count": legacy_tables[0],
            "compact_count": compact_tables[0],
            "legacy_semantic_sha256": legacy_tables[1],
            "compact_semantic_sha256": compact_tables[1],
            "identical": legacy_tables == compact_tables,
        }
    )
    legacy_inventory = read_json_object(legacy_root / "records/artifact_inventory.json")
    compact_inventory = read_json_object(compact_root / "records/artifact_inventory.json")
    legacy_bytes = _required_int(legacy_inventory, "byte_size")
    compact_bytes = _required_int(compact_inventory, "byte_size")
    return {
        "schema_version": "er_commons.task03h_compact_mapping_comparison.v1",
        "legacy_root": legacy_root.as_posix(),
        "compact_root": compact_root.as_posix(),
        "semantic_comparisons": comparisons,
        "all_semantic_projections_identical": all(item["identical"] for item in comparisons),
        "storage": {
            "legacy_managed_bytes": legacy_bytes,
            "compact_managed_bytes": compact_bytes,
            "bytes_removed": legacy_bytes - compact_bytes,
            "reduction_fraction": 1 - compact_bytes / legacy_bytes,
            "legacy_managed_files": legacy_inventory["file_count"],
            "compact_managed_files": compact_inventory["file_count"],
        },
        "intentional_contract_changes": [
            "remove raw_mappings because canonical records retain direct raw links",
            "store invalid provenance once in observations/invalid_provenance.jsonl",
            "table cells retain indices, spans, and text; detailed geometry remains in raw cells",
            "reference four owner table assets instead of duplicating generated JSON/cell assets",
            "content-image paths now name the conversion owner instead of a producer copy",
        ],
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": _peak_rss_bytes(),
    }


def benchmark_sealed_hierarchy_features(
    document_path: Path,
    alignment_path: Path,
    *,
    expected_page_count: int,
) -> JsonObject:
    """Measure the fixed one-pass feature build from sealed non-PDF evidence."""
    from er_commons.document_parsing.heading_evidence_parsing.alignment_projection import (
        load_alignment_projection,
    )
    from er_commons.document_parsing.heading_evidence_parsing.source_features import (
        build_feature_seeds,
    )

    total_started = time.perf_counter()
    started = time.perf_counter()
    document = read_json_object(document_path)
    document_load_seconds = time.perf_counter() - started
    started = time.perf_counter()
    alignment = load_alignment_projection(alignment_path, expected_page_count=expected_page_count)
    alignment_load_seconds = time.perf_counter() - started
    started = time.perf_counter()
    features = build_feature_seeds(document, alignment)
    feature_seconds = time.perf_counter() - started
    return {
        "schema_version": "er_commons.task03h_sealed_hierarchy_feature_benchmark.v1",
        "document_path": document_path.as_posix(),
        "document_byte_size": document_path.stat().st_size,
        "alignment_path": alignment_path.as_posix(),
        "alignment_byte_size": alignment_path.stat().st_size,
        "page_count": len(alignment),
        "feature_count": len(features),
        "layout_state_counts": _value_counts(
            str(feature.get("layout_state")) for feature in features
        ),
        "substage_seconds": {
            "document_load": document_load_seconds,
            "alignment_load": alignment_load_seconds,
            "feature_index_and_build": feature_seconds,
        },
        "wall_seconds": time.perf_counter() - total_started,
        "peak_rss_bytes": _peak_rss_bytes(),
        "source_pdf_bytes_read": False,
        "model_files_read": False,
        "feature_seed_build_count": 1,
    }


def _value_counts(values: Iterator[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _semantic_jsonl_digest(
    path: Path,
    *,
    transform: Callable[[JsonObject], JsonObject] | None = None,
) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    with path.open() as stream:
        for line in stream:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"semantic comparison record is not an object: {path}")
            value = transform(record) if transform is not None else record
            if not value:
                continue
            normalized = _normalize_extraction_ids(value)
            digest.update(json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode())
            digest.update(b"\n")
            count += 1
    return count, digest.hexdigest()


def _normalize_extraction_ids(value: Any) -> Any:
    if isinstance(value, str):
        return _EXTRACTION_ID.sub("exv1-CURRENT", value)
    if isinstance(value, list):
        return [_normalize_extraction_ids(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_extraction_ids(item) for key, item in value.items()}
    return value


def _compact_table_semantics(record: JsonObject) -> JsonObject:
    projected = {key: value for key, value in record.items() if key != "raw_links"}
    cells = record.get("cells")
    if not isinstance(cells, list):
        raise ValueError("canonical table cells are invalid")
    projected["cells"] = [
        {
            key: value
            for key, value in {
                "row_index": cell.get("row_index"),
                "column_index": cell.get("column_index"),
                "row_span": cell.get("row_span"),
                "column_span": cell.get("column_span"),
                "end_row_offset_idx": cell.get("end_row_offset_idx"),
                "end_column_offset_idx": cell.get("end_column_offset_idx"),
                "text": cell.get("text", cell.get("canonical_text")),
            }.items()
            if value is not None
        }
        for cell in cells
        if isinstance(cell, dict)
    ]
    return projected


def _image_semantics(record: JsonObject) -> JsonObject:
    return {key: value for key, value in record.items() if key != "asset_id"}


def _content_image_asset_semantics(record: JsonObject) -> JsonObject:
    if record.get("role") != "content_image":
        return {}
    return {key: value for key, value in record.items() if key not in {"id", "path"}}


def _required_int(record: dict[str, Any], key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"required integer field is invalid: {key}")
    return value


@dataclass
class _MultisetDigest:
    """Order-independent pair of cryptographic aggregates for item membership."""

    count: int = 0
    digest_sum: int = 0
    digest_xor: int = 0

    def add(self, digest: bytes) -> None:
        """Add one item digest without retaining the item or digest collection."""
        value = int.from_bytes(digest, "big")
        self.count += 1
        self.digest_sum = (self.digest_sum + value) & MASK_256
        self.digest_xor ^= value

    def record(self) -> JsonObject:
        """Return the stable report representation."""
        return {
            "count": self.count,
            "sha256_sum_mod_2_256": f"{self.digest_sum:064x}",
            "sha256_xor": f"{self.digest_xor:064x}",
        }


def audit_assembled_partition(
    path: Path,
    *,
    expected_page_count: int,
) -> JsonObject:
    """Prove page elements equal the body/header partition in one bounded pass."""
    started = time.perf_counter()
    aggregates = {name: _MultisetDigest() for name in PARTITION_FIELDS}
    active: dict[str, Any] = {}
    pages_seen = 0
    with path.open("rb") as stream:
        for prefix, event, value in ijson.parse(stream, use_float=True):
            if prefix == "pages.item" and event == "start_map":
                pages_seen += 1
            if prefix == "pages" and event == "end_array":
                break
            for name in PARTITION_FIELDS:
                root = f"pages.item.assembled.{name}.item"
                if prefix == root and event == "start_map":
                    active[name] = hashlib.sha256()
                digest = active.get(name)
                if digest is not None and (prefix == root or prefix.startswith(f"{root}.")):
                    _update_event_hash(digest, prefix.removeprefix(root), event, value)
                if prefix == root and event == "end_map":
                    if digest is None:
                        raise ValueError(f"assembled item ended without start: {name}")
                    aggregates[name].add(digest.digest())
                    del active[name]
    if pages_seen != expected_page_count:
        raise ValueError(f"partition audit saw {pages_seen} pages, expected {expected_page_count}")
    elements = aggregates["elements"]
    partition = _combined_digest(aggregates["body"], aggregates["headers"])
    identical = elements.record() == partition.record()
    return {
        "schema_version": "er_commons.task03h_assembled_partition_audit.v1",
        "input_path": path.as_posix(),
        "input_byte_size": path.stat().st_size,
        "page_count": pages_seen,
        "execution_boundary": {
            "source_pdf_bytes_read": False,
            "model_files_read": False,
            "docling_constructed": False,
            "complete_json_object_constructed": False,
            "maximum_constructed_scope": "one parser event and one item digest",
        },
        "fields": {name: aggregate.record() for name, aggregate in aggregates.items()},
        "body_and_headers": partition.record(),
        "elements_equal_body_and_headers_multiset": identical,
        "digest_method": (
            "SHA-256 per normalized parser-event item, compared by count plus "
            "independent 256-bit modular-sum and XOR aggregates"
        ),
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": _peak_rss_bytes(),
    }


def _combined_digest(left: _MultisetDigest, right: _MultisetDigest) -> _MultisetDigest:
    return _MultisetDigest(
        count=left.count + right.count,
        digest_sum=(left.digest_sum + right.digest_sum) & MASK_256,
        digest_xor=left.digest_xor ^ right.digest_xor,
    )


def _update_event_hash(digest: Any, prefix: str, event: str, value: Any) -> None:
    encoded_value = "" if value is None else str(value)
    digest.update(prefix.encode())
    digest.update(b"\0")
    digest.update(event.encode())
    digest.update(b"\0")
    digest.update(encoded_value.encode())
    digest.update(b"\n")


def conversion_pages_consumer_audit() -> JsonObject:
    """Record every maintained semantic and byte-only consumer found in source."""
    return {
        "schema_version": "er_commons.task03h_conversion_pages_consumers.v1",
        "semantic_consumers": [
            {
                "owner": "hierarchy alignment projection",
                "code": (
                    "document_parsing/heading_evidence_parsing/"
                    "source_features.py:extract_item_observations"
                ),
                "fields": [
                    "pages[].page_no",
                    "pages[].size.width",
                    "pages[].size.height",
                    "pages[].parsed_page.textline_cells[].text",
                ],
                "replacement": "one normalized alignment-index record per page",
            }
        ],
        "byte_only_consumers": [
            {
                "owner": "conversion seal verification",
                "code": "content_parsing/evidence.py:verify_inventory",
                "behavior": "hashes the complete file but reads no semantic field",
            },
            {
                "owner": "canonical asset registration",
                "code": "record_mapping/assets.py:materialize_assets",
                "behavior": "hashes and names the file but reads no semantic field",
            },
        ],
        "non_consumers": [
            {
                "owner": "routing and table reconstruction",
                "actual_inputs": ["document.json", "source PDF"],
            },
            {
                "owner": "record mapping semantics",
                "actual_inputs": ["document.json", "routing bundle", "table bundle"],
            },
            {
                "owner": "conversion reuse loader",
                "actual_inputs": [
                    "document.json",
                    "conversion_observation.json",
                    "asset_inventory.json",
                ],
            },
        ],
        "field_classification": {
            "pages[].page_no": "required_but_represented_in_document_and_observation",
            "pages[].size": "required_by_hierarchy_projection",
            "pages[].parsed_page.textline_cells[].text": "required_by_hierarchy_projection",
            "pages[].parsed_page.other": "no_post_docling_consumer",
            "pages[].predictions": "no_post_docling_consumer",
            "pages[].assembled": "no_post_docling_consumer",
            "assembled": "exact_duplicate_and_no_post_docling_consumer",
            "confidence": "no_post_docling_consumer",
        },
        "mvp_decision_supported_by_current_consumers": (
            "do not publish conversion_pages.json; publish document.json and a separately "
            "sealed hierarchy alignment projection"
        ),
    }


def freeze_migration_inputs(task_root: Path, source_ids: list[str]) -> JsonObject:
    """Inventory all sealed and incomplete Task 03H state using metadata and small records."""
    sealed: list[JsonObject] = []
    for completion_path in sorted(task_root.rglob("completion_record.json")):
        if "performance" in completion_path.parts:
            continue
        root = completion_path.parent.parent
        inventory_path = completion_path.with_name("artifact_inventory.json")
        completion = json.loads(completion_path.read_bytes())
        inventory = json.loads(inventory_path.read_bytes()) if inventory_path.is_file() else None
        source_id = _record_source_id(completion)
        files = inventory.get("files", []) if isinstance(inventory, dict) else []
        sealed.append(
            {
                "root": root.relative_to(task_root).as_posix(),
                "owner_kind": _owner_kind(root, task_root),
                "source_id": source_id,
                "terminal_id": _record_terminal_id(completion),
                "schema_version": completion.get("schema_version"),
                "status": completion.get("status")
                or completion.get("producer_status")
                or completion.get("document_status"),
                "completion_sha256": sha256_file(completion_path),
                "inventory_path": (
                    inventory_path.relative_to(task_root).as_posix()
                    if inventory_path.is_file()
                    else None
                ),
                "inventory_sha256": (
                    sha256_file(inventory_path) if inventory_path.is_file() else None
                ),
                "managed_file_count": len(files),
                "managed_byte_size": sum(
                    int(record.get("byte_size", 0)) for record in files if isinstance(record, dict)
                ),
            }
        )
    attempts: list[JsonObject] = [
        {
            "path": path.relative_to(task_root).as_posix(),
            "byte_size": sum(item.stat().st_size for item in path.rglob("*") if item.is_file()),
        }
        for path in sorted(task_root.rglob("*"))
        if path.is_dir() and path.parent.name in {".tmp", "attempts"}
    ]
    sealed_sources = sorted(
        {str(record["source_id"]) for record in sealed if record["source_id"] in source_ids}
    )
    return {
        "schema_version": "er_commons.task03h_migration_input_freeze.v1",
        "task_root": task_root.as_posix(),
        "expected_source_ids": source_ids,
        "expected_source_count": len(source_ids),
        "sources_with_terminal_artifacts": sealed_sources,
        "sources_without_terminal_artifacts": sorted(set(source_ids) - set(sealed_sources)),
        "sealed_artifacts": sealed,
        "incomplete_or_failed_workspaces": attempts,
        "totals": {
            "sealed_artifact_count": len(sealed),
            "sealed_managed_bytes": sum(int(record["managed_byte_size"]) for record in sealed),
            "attempt_workspace_count": len(attempts),
            "attempt_bytes": sum(
                value if isinstance(value := record["byte_size"], int) else 0 for record in attempts
            ),
        },
        "execution_boundary": {
            "source_pdf_bytes_read": False,
            "model_files_read": False,
            "docling_constructed": False,
            "managed_payload_bytes_read": False,
            "small_completion_and_inventory_records_read": True,
            "files_deleted": False,
        },
    }


def gateb_schema_decision() -> JsonObject:
    """Record the selected single-version MVP schemas and replay invariants."""
    return {
        "schema_version": "er_commons.task03h_gateb_schema_decision.v1",
        "complete_replay": {
            "owner": "docling conversion bundle",
            "version": "er_commons.docling_conversion.v2",
            "files": [
                "docling/document.json",
                "docling/heading_overlay.jsonl",
                "docling/alignment_pages.jsonl",
                "docling/conversion_observation.json",
                "asset_inventory.json",
                "figure assets",
            ],
            "document_rule": (
                "document.json stores base level 1 once; heading_overlay.jsonl stores only "
                "stable self_ref and replacement level"
            ),
            "removed": "conversion_pages.json",
        },
        "hierarchy_alignment": {
            "version": "er_commons.hierarchy_alignment_page.v1",
            "format": "plain JSON Lines, one physical page per line",
            "fields": ["page_no", "width", "height", "normalized alignment index"],
        },
        "replay_invariants": [
            "routing and tables consume base document plus source PDF",
            "record mapping consumes document, routing, tables, observation, and assets",
            "hierarchy receives exact layout state for every normalized text lookup",
            "heading view is exactly reconstructable from base document plus overlay",
            "normal reuse verifies closed seals, exact paths, sizes, and consumed small files",
            "explicit deep audit rehashes every owner byte",
            "publication writes completion last and interrupted attempts remain inspectable",
        ],
        "format_decision": {
            "selected": "plain_json_and_json_lines",
            "reason": (
                "document.json is the native semantic replay object already required; the "
                "26 MB hierarchy projection reads in under one second, so a database or "
                "columnar dependency adds complexity without measured benefit"
            ),
            "not_selected": [
                "page-sharded JSON: same bytes and 2328 inventory entries",
                "gzip JSONL: smaller but loses direct inspection and byte offsets",
                "SQLite: larger than JSONL and opaque for no measured speed need",
                "Arrow/Parquet: nested sequential strings do not justify columnar storage",
            ],
        },
        "compatibility_policy": "single maintained MVP schema; no legacy runtime readers",
    }


def _record_source_id(record: JsonObject) -> str | None:
    value = record.get("source_id")
    if isinstance(value, str):
        return value
    values = record.get("source_ids")
    if isinstance(values, list) and len(values) == 1 and isinstance(values[0], str):
        return values[0]
    return None


def _record_terminal_id(record: JsonObject) -> str | None:
    for key in (
        "conversion_id",
        "producer_run_id",
        "candidate_id",
        "document_run_id",
        "collection_run_id",
    ):
        value = record.get(key)
        if isinstance(value, str):
            return value
    return None


def _owner_kind(root: Path, task_root: Path) -> str:
    relative = root.relative_to(task_root)
    return relative.parts[0] if relative.parts else "task_root"


def benchmark_projection_packaging(jsonl_path: Path, output_root: Path) -> JsonObject:
    """Measure JSONL, page-sharded JSON, gzip JSONL, and SQLite packaging."""
    output_root.mkdir(parents=True, exist_ok=True)
    results = [_measure_jsonl(jsonl_path)]
    results.append(_build_shards(jsonl_path, output_root / "page_shards"))
    results.append(_build_gzip(jsonl_path, output_root / "alignment_pages.jsonl.gz"))
    results.append(_build_sqlite(jsonl_path, output_root / "alignment_pages.sqlite"))
    return {
        "schema_version": "er_commons.task03h_projection_packaging_benchmark.v1",
        "source_jsonl_sha256": sha256_file(jsonl_path),
        "source_jsonl_byte_size": jsonl_path.stat().st_size,
        "candidates": results,
        "arrow_parquet_decision": (
            "not benchmarked: the access pattern is sequential page records with nested "
            "variable-length strings, and current JSON candidates already read in under one second"
        ),
    }


def _measure_jsonl(path: Path) -> JsonObject:
    started = time.perf_counter()
    records = 0
    with path.open("rb") as stream:
        for line in stream:
            json.loads(line)
            records += 1
    return _measurement("json_lines", path, records, time.perf_counter() - started, 1)


def _build_shards(source: Path, root: Path) -> JsonObject:
    if root.exists():
        raise FileExistsError(f"benchmark output already exists: {root}")
    root.mkdir()
    build_started = time.perf_counter()
    count = 0
    with source.open("rb") as stream:
        for count, line in enumerate(stream, start=1):
            (root / f"page_{count:05d}.json").write_bytes(line.rstrip(b"\n") + b"\n")
    build_seconds = time.perf_counter() - build_started
    read_started = time.perf_counter()
    for path in sorted(root.glob("*.json")):
        json.loads(path.read_bytes())
    read_seconds = time.perf_counter() - read_started
    total_bytes = sum(path.stat().st_size for path in root.glob("*.json"))
    return {
        "format": "page_sharded_json",
        "path": root.as_posix(),
        "byte_size": total_bytes,
        "record_count": count,
        "file_count": count,
        "build_wall_seconds": build_seconds,
        "read_wall_seconds": read_seconds,
    }


def _build_gzip(source: Path, path: Path) -> JsonObject:
    started = time.perf_counter()
    with source.open("rb") as input_stream, gzip.open(path, "wb", compresslevel=1) as output:
        _copy_stream(input_stream, output)
    build_seconds = time.perf_counter() - started
    read_started = time.perf_counter()
    count = 0
    with gzip.open(path, "rb") as stream:
        for line in stream:
            json.loads(line)
            count += 1
    return {
        **_measurement("gzip_json_lines", path, count, time.perf_counter() - read_started, 1),
        "build_wall_seconds": build_seconds,
    }


def _build_sqlite(source: Path, path: Path) -> JsonObject:
    started = time.perf_counter()
    with sqlite3.connect(path) as connection, source.open() as stream:
        connection.execute("CREATE TABLE pages (page_no INTEGER PRIMARY KEY, record_json TEXT)")
        for line in stream:
            record = json.loads(line)
            connection.execute(
                "INSERT INTO pages VALUES (?, ?)",
                (record["page_no"], line.rstrip("\n")),
            )
    build_seconds = time.perf_counter() - started
    read_started = time.perf_counter()
    count = 0
    with sqlite3.connect(path) as connection:
        for (value,) in connection.execute("SELECT record_json FROM pages ORDER BY page_no"):
            json.loads(value)
            count += 1
    return {
        **_measurement("sqlite", path, count, time.perf_counter() - read_started, 1),
        "build_wall_seconds": build_seconds,
    }


def _measurement(
    format_name: str,
    path: Path,
    records: int,
    read_seconds: float,
    files: int,
) -> JsonObject:
    return {
        "format": format_name,
        "path": path.as_posix(),
        "byte_size": path.stat().st_size,
        "record_count": records,
        "file_count": files,
        "read_wall_seconds": read_seconds,
    }


def _copy_stream(source: BinaryIO, destination: Any) -> None:
    while chunk := source.read(1024 * 1024):
        destination.write(chunk)


def write_gateb_report(path: Path, report: JsonObject) -> Path:
    """Write one small Gate B report atomically."""
    write_json_atomic(path, report)
    return path


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


__all__ = [
    "audit_assembled_partition",
    "benchmark_projection_packaging",
    "benchmark_sealed_hierarchy_features",
    "compare_compact_mapping",
    "conversion_pages_consumer_audit",
    "deep_audit_legacy_conversions",
    "derive_legacy_alignment_projection",
    "derive_legacy_heading_overlay",
    "forecast_downstream_admission",
    "freeze_migration_inputs",
    "gateb_schema_decision",
    "write_gateb_report",
]
