"""Source-free behavior tests for Task 03H.1 Gate B audits."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from er_commons.artifact_io import artifact_inventory, sha256_file, write_json_atomic
from er_commons.document_performance.task03h_gateb import (
    audit_assembled_partition,
    benchmark_projection_packaging,
    conversion_pages_consumer_audit,
    deep_audit_legacy_conversions,
    derive_legacy_alignment_projection,
    derive_legacy_heading_overlay,
    forecast_downstream_admission,
)


def test_assembled_partition_audit_matches_body_and_headers(tmp_path: Path) -> None:
    path = tmp_path / "conversion_pages.json"
    body = {"id": 1, "text": "body"}
    header = {"id": 2, "text": "header"}
    write_json_atomic(
        path,
        {
            "pages": [
                {
                    "page_no": 1,
                    "assembled": {
                        "elements": [header, body],
                        "body": [body],
                        "headers": [header],
                    },
                }
            ],
            "assembled": {},
        },
    )

    report = audit_assembled_partition(path, expected_page_count=1)

    assert report["elements_equal_body_and_headers_multiset"] is True
    assert report["fields"]["elements"]["count"] == 2
    assert report["body_and_headers"]["count"] == 2


def test_assembled_partition_audit_detects_changed_item(tmp_path: Path) -> None:
    path = tmp_path / "conversion_pages.json"
    write_json_atomic(
        path,
        {
            "pages": [
                {
                    "page_no": 1,
                    "assembled": {
                        "elements": [{"id": 1}],
                        "body": [{"id": 2}],
                        "headers": [],
                    },
                }
            ]
        },
    )

    report = audit_assembled_partition(path, expected_page_count=1)

    assert report["elements_equal_body_and_headers_multiset"] is False


def test_consumer_audit_selects_document_and_alignment_projection() -> None:
    report = conversion_pages_consumer_audit()

    [consumer] = report["semantic_consumers"]
    assert consumer["fields"] == [
        "pages[].page_no",
        "pages[].size.width",
        "pages[].size.height",
        "pages[].parsed_page.textline_cells[].text",
    ]
    assert report["field_classification"]["pages[].predictions"] == ("no_post_docling_consumer")


def test_projection_packaging_benchmark_preserves_all_records(tmp_path: Path) -> None:
    source = tmp_path / "alignment.jsonl"
    records = [
        {"page_no": 1, "alignment_index": [["first", "unique_aligned", 1]]},
        {"page_no": 2, "alignment_index": [["second", "ambiguous", None]]},
    ]
    source.write_text("".join(json.dumps(record) + "\n" for record in records))

    report = benchmark_projection_packaging(source, tmp_path / "benchmark")

    assert {item["format"] for item in report["candidates"]} == {
        "json_lines",
        "page_sharded_json",
        "gzip_json_lines",
        "sqlite",
    }
    assert all(item["record_count"] == 2 for item in report["candidates"])


def test_legacy_alignment_replay_hashes_input_and_writes_current_schema(tmp_path: Path) -> None:
    source = tmp_path / "conversion_pages.json"
    source.write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "page_no": 1,
                        "size": {"width": 10, "height": 20},
                        "parsed_page": {"textline_cells": [{"text": "Hello"}]},
                    }
                ],
                "assembled": {"ignored": True},
            }
        )
    )
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    output = tmp_path / "alignment.jsonl"

    report = derive_legacy_alignment_projection(
        source, output, expected_page_count=1, expected_sha256=digest
    )

    [record] = [json.loads(line) for line in output.read_text().splitlines()]
    assert record["schema_version"] == "er_commons.hierarchy_alignment_page.v1"
    assert report["input_sha256"] == digest
    assert report["completion_written_last"] is True


def test_legacy_heading_overlay_is_exact_and_small(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    heading = tmp_path / "heading.json"
    baseline.write_text(json.dumps({"texts": [{"self_ref": "#/texts/0", "level": 1}]}))
    heading.write_text(json.dumps({"texts": [{"self_ref": "#/texts/0", "level": 3}]}))
    output = tmp_path / "overlay.jsonl"

    report = derive_legacy_heading_overlay(
        baseline,
        heading,
        output,
        expected_baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
        expected_heading_sha256=hashlib.sha256(heading.read_bytes()).hexdigest(),
    )

    assert report["overlay_record_count"] == 1
    assert json.loads(output.read_text())["level"] == 3


def test_density_admission_rejects_k2_forecast_before_a_long_run() -> None:
    forecast = forecast_downstream_admission(
        document_bytes=1_471_964_647,
        text_items=1_092_851,
        alignment_cells=2_561_773,
        routed_pages=1_635,
        table_count=1_819,
        expected_records=1_100_000,
    )

    assert forecast["estimated_critical_path_seconds"] > 3_600
    assert forecast["admitted"] is False


def test_legacy_conversion_deep_audit_verifies_every_managed_byte(tmp_path: Path) -> None:
    root = tmp_path / ("dconv1-" + "a" * 64)
    write_json_atomic(
        root / "records/conversion_identity.json",
        {
            "conversion_id": root.name,
            "identity": {"source": {"source_id": "fixture"}},
        },
    )
    (root / "documents/fixture/producer/docling").mkdir(parents=True)
    (root / "documents/fixture/producer/docling/document.json").write_text("{}\n")
    inventory_path = root / "records/artifact_inventory.json"
    write_json_atomic(
        inventory_path,
        artifact_inventory(
            root,
            excluded={"records/artifact_inventory.json", "records/completion_record.json"},
        ),
    )
    write_json_atomic(
        root / "records/completion_record.json",
        {
            "conversion_id": root.name,
            "artifact_inventory_sha256": sha256_file(inventory_path),
        },
    )

    report = deep_audit_legacy_conversions(tmp_path)

    assert report["conversion_count"] == 1
    assert report["all_managed_conversion_bytes_hashed"] is True
