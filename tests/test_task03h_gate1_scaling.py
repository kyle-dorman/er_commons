"""Source-free tests for the Task 03H.1 scaling ledger."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.artifact_io import write_json_atomic
from er_commons.document_performance.task03h_gate1 import (
    SOURCE_ID,
    benchmark_alignment_scaling,
    build_alignment_projection,
    build_task03h_gate1_ledger,
    compare_table_bundles,
    profile_assembled_reconstruction,
    profile_conversion_pages,
    profile_document_level_overlay,
)


def test_ledger_uses_seals_without_reading_large_payloads(tmp_path: Path) -> None:
    raw = _owner(tmp_path, "document_parse_evidence/docling_conversions/dconv1-a")
    derived = _owner(tmp_path, "document_parse_evidence/prv1-a")
    for owner in (raw, derived):
        document = _payload(owner, "document.json", b"doc")
        pages = _payload(owner, "conversion_pages.json", b"pages")
        _seal(
            owner,
            {
                document.relative_to(owner).as_posix(): ("d" * 64, 3),
                pages.relative_to(owner).as_posix(): ("p" * 64, 5),
            },
        )

    report = build_task03h_gate1_ledger(tmp_path)

    assert report["execution_boundary"]["large_payload_bytes_read"] is False
    assert report["payload_totals"]["path_count"] == 4
    assert report["payload_totals"]["known_checksum_path_bytes"] == 16
    assert report["payload_totals"]["known_unique_content_bytes"] == 8
    assert report["payload_totals"]["known_duplicate_logical_bytes"] == 8
    groups = report["content_groups"]
    assert {(group["payload_role"], group["path_count"]) for group in groups} == {
        ("document", 2),
        ("conversion_pages", 2),
    }


def test_ledger_retains_unknown_incomplete_payload_without_hashing(tmp_path: Path) -> None:
    attempt = _owner(tmp_path, "document_parse_evidence/.tmp/prv1-a.attempt")
    _payload(attempt, "conversion_pages.json", b"partial")

    report = build_task03h_gate1_ledger(tmp_path)

    [payload] = report["large_payloads"]
    assert payload["publication_state"] == "incomplete"
    assert payload["inventory_sha256"] is None
    assert report["payload_totals"]["incomplete_path_count"] == 1


def test_ledger_collects_only_k2_completed_stage_timings(tmp_path: Path) -> None:
    attempts = tmp_path / "pipelines/brisbane_baylands/task_03h/document_publications/attempts"
    _attempt(attempts, "wanted", SOURCE_ID, 31.25)
    _attempt(attempts, "other", "another_source", 99.0)

    report = build_task03h_gate1_ledger(tmp_path)

    [timing] = report["document_process_timings"]
    assert timing["stage"] == "record_mapping"
    assert timing["wall_seconds"] == 31.25


def test_ledger_keeps_interrupted_attempt_without_terminal_record(tmp_path: Path) -> None:
    attempt = (
        tmp_path / "pipelines/brisbane_baylands/task_03h/document_publications/attempts/interrupted"
    )
    events = attempt / "document_process_events"
    events.mkdir(parents=True)
    write_json_atomic(attempt / "execution_preflight.json", {"source_id": SOURCE_ID})
    write_json_atomic(
        events / "01_content_parsing_completed.json",
        {"stage": "content_parsing", "state": "completed", "wall_seconds": 90.0},
    )

    report = build_task03h_gate1_ledger(tmp_path)

    [timing] = report["document_process_timings"]
    assert timing["attempt_record_present"] is False
    assert timing["wall_seconds"] == 90.0


def test_conversion_pages_profile_builds_only_page_scoped_measurements(tmp_path: Path) -> None:
    path = tmp_path / "conversion_pages.json"
    write_json_atomic(
        path,
        {
            "pages": [
                {
                    "page_no": 1,
                    "size": {"width": 10, "height": 20},
                    "parsed_page": {
                        "textline_cells": [{"text": "first"}, {"text": "second"}],
                        "word_cells": [{"text": "first"}],
                    },
                    "assembled": {"elements": [1, 2, 3]},
                },
                {
                    "page_no": 2,
                    "size": {"width": 10, "height": 20},
                    "parsed_page": {"textline_cells": [{"text": "third"}]},
                    "assembled": {"elements": []},
                },
            ],
            "assembled": {"timings": {}},
            "confidence": {"mean": 1.0},
        },
    )

    report = profile_conversion_pages(path, expected_page_count=2)

    assert report["page_count"] == 2
    assert report["execution_boundary"]["complete_json_object_constructed"] is False
    counts = {item["field"]: item["item_count"] for item in report["collection_item_counts"]}
    assert counts["pages[].parsed_page.textline_cells"] == 3
    assert counts["pages[].assembled.elements"] == 3
    assert report["pages_reencoded_byte_size"] < report["file_byte_size"]


def test_document_overlay_profile_proves_only_level_changes(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    heading = tmp_path / "heading.json"
    baseline.write_text('{\n  "text": "same",\n  "level": 1\n}\n')
    heading.write_text('{\n  "text": "same",\n  "level": 4\n}\n')

    report = profile_document_level_overlay(baseline, heading)

    assert report["level_field_count"] == 1
    assert report["differing_level_field_count"] == 1
    assert report["level_transitions"] == [{"transition": "1->4", "count": 1}]
    assert report["non_level_differing_line_count"] == 0
    assert report["level_normalized_documents_identical"] is True


def test_document_overlay_profile_rejects_other_differences(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    heading = tmp_path / "heading.json"
    baseline.write_text('{"text": "first"}\n')
    heading.write_text('{"text": "second"}\n')

    report = profile_document_level_overlay(baseline, heading)

    assert report["non_level_differing_line_count"] == 1
    assert report["level_normalized_documents_identical"] is False


def test_alignment_benchmark_preserves_semantics_and_exposes_comparison_growth() -> None:
    report = benchmark_alignment_scaling((5, 10, 20))

    measurements = report["measurements"]
    assert [item["current_cartesian_comparisons"] for item in measurements] == [25, 100, 400]
    assert all(item["speedup"] is not None for item in measurements)
    assert report["execution_boundary"]["synthetic_only"] is True


def test_table_bundle_comparison_ignores_only_runtime_measurements(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    heading = tmp_path / "heading"
    for root, seconds in ((baseline, 1.0), (heading, 2.0)):
        root.mkdir()
        write_json_atomic(root / "configuration.json", {"pipeline": root.name})
        write_json_atomic(root / "result.json", {"value": 3, "wall_seconds": seconds})
        _table_inventory(root)

    report = compare_table_bundles(baseline, heading)

    assert report["path_sets_equal"] is True
    assert report["runtime_measurement_only_file_count"] == 1
    assert report["identity_configuration_files"] == ["configuration.json"]
    assert report["semantic_difference_count"] == 0
    assert report["semantically_equivalent"] is True


def test_assembled_reconstruction_matches_concatenated_page_lists(tmp_path: Path) -> None:
    path = tmp_path / "conversion_pages.json"
    assembled = {
        "elements": [{"value": 1}, {"value": 2}],
        "headers": ["first", "second"],
        "body": [1, 2, 3],
    }
    write_json_atomic(
        path,
        {
            "pages": [
                {
                    "page_no": 1,
                    "assembled": {
                        "elements": assembled["elements"][:1],
                        "headers": assembled["headers"][:1],
                        "body": assembled["body"][:2],
                    },
                },
                {
                    "page_no": 2,
                    "assembled": {
                        "elements": assembled["elements"][1:],
                        "headers": assembled["headers"][1:],
                        "body": assembled["body"][2:],
                    },
                },
            ],
            "assembled": assembled,
            "confidence": {"mean": 1.0},
        },
    )

    report = profile_assembled_reconstruction(path, expected_page_count=2)

    assert report["all_lists_identical"] is True
    assert {item["field"]: item["page_item_count"] for item in report["comparisons"]} == {
        "elements": 2,
        "headers": 2,
        "body": 3,
    }


def test_alignment_projection_is_compact_json_and_preserves_states(tmp_path: Path) -> None:
    source = tmp_path / "conversion_pages.json"
    output = tmp_path / "projection.jsonl"
    write_json_atomic(
        source,
        {
            "pages": [
                {
                    "page_no": 1,
                    "size": {"width": 10, "height": 20},
                    "parsed_page": {
                        "textline_cells": [
                            {"text": "Unique line"},
                            {"text": "Repeated"},
                            {"text": " repeated "},
                        ]
                    },
                    "large_unused_field": "x" * 1000,
                }
            ]
        },
    )

    report = build_alignment_projection(source, output, expected_page_count=1)
    [record] = [json.loads(line) for line in output.read_text().splitlines()]

    assert record["alignment_index"] == [
        ["repeated", "ambiguous", None],
        ["unique line", "unique_aligned", 1],
    ]
    assert report["projection_byte_size"] < source.stat().st_size
    assert report["normalized_key_count"] == 2


def _table_inventory(root: Path) -> None:
    files = []
    for path in sorted(root.glob("*.json")):
        files.append(
            {
                "path": path.name,
                "sha256": "different-" + root.name + "-" + path.name,
                "byte_size": path.stat().st_size,
            }
        )
    write_json_atomic(root / "artifact_inventory.json", {"files": files})


def _owner(root: Path, relative: str) -> Path:
    path = root / "pipelines/brisbane_baylands/task_03h" / relative
    path.mkdir(parents=True)
    return path


def _payload(owner: Path, name: str, value: bytes) -> Path:
    path = owner / "documents" / SOURCE_ID / "producer/docling" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)
    return path


def _seal(owner: Path, entries: dict[str, tuple[str, int]]) -> None:
    records = owner / "records"
    records.mkdir()
    write_json_atomic(
        records / "artifact_inventory.json",
        {
            "files": [
                {"path": path, "sha256": digest, "byte_size": size}
                for path, (digest, size) in entries.items()
            ]
        },
    )
    write_json_atomic(records / "completion_record.json", {"status": "complete"})


def _attempt(root: Path, name: str, source_id: str, seconds: float) -> None:
    attempt = root / name
    events = attempt / "document_process_events"
    events.mkdir(parents=True)
    write_json_atomic(
        attempt / "attempt_record.json",
        {"source_id": source_id, "transaction_id": name},
    )
    event: dict[str, Any] = {
        "stage": "record_mapping",
        "state": "completed",
        "wall_seconds": seconds,
    }
    write_json_atomic(events / "03_record_mapping_completed.json", event)
