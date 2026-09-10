"""Inspect explicitly selected conversion evidence and diagnostics."""

import argparse
import json
import logging
from pathlib import Path

from er_commons.document_performance.conversion_compatibility_audit import (
    audit_assembled_partition,
    benchmark_projection_packaging,
    compatibility_schema_decision,
    conversion_pages_consumer_audit,
    deep_audit_legacy_conversions,
    derive_legacy_alignment_projection,
    derive_legacy_heading_overlay,
    freeze_migration_inputs,
    write_compatibility_report,
)
from er_commons.document_performance.conversion_scaling import (
    bind_existing_conversion_pages_profile,
    write_alignment_projection_profile,
    write_alignment_scaling_benchmark,
    write_assembled_reconstruction_profile,
    write_conversion_pages_profile,
    write_conversion_scaling_ledger,
    write_document_level_overlay_profile,
    write_table_bundle_comparison,
)


def main() -> None:
    """Run the selected metadata, payload-profile, benchmark, or explicit deep-audit operation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--run-relative-root", type=Path, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--collection-spec", type=Path)
    parser.add_argument("--ledger", action="store_true")
    parser.add_argument("--conversion-pages", type=Path)
    parser.add_argument("--expected-page-count", type=int)
    parser.add_argument("--bind-existing-conversion-profile", action="store_true")
    parser.add_argument("--skip-conversion-profile", action="store_true")
    parser.add_argument("--baseline-document", type=Path)
    parser.add_argument("--heading-document", type=Path)
    parser.add_argument("--skip-document-overlay-profile", action="store_true")
    parser.add_argument("--alignment-benchmark", action="store_true")
    parser.add_argument("--baseline-table-root", type=Path)
    parser.add_argument("--heading-table-root", type=Path)
    parser.add_argument("--assembled-reconstruction", action="store_true")
    parser.add_argument("--alignment-projection", action="store_true")
    parser.add_argument("--assembled-partition-audit", action="store_true")
    parser.add_argument("--consumer-audit", action="store_true")
    parser.add_argument("--projection-packaging-benchmark", type=Path)
    parser.add_argument("--freeze-migration-inputs", action="store_true")
    parser.add_argument("--compatibility-schema-decision", action="store_true")
    parser.add_argument("--deep-audit-legacy-conversions", action="store_true")
    parser.add_argument("--legacy-alignment-output", type=Path)
    parser.add_argument("--legacy-conversion-pages-sha256")
    parser.add_argument("--legacy-overlay-output", type=Path)
    parser.add_argument("--baseline-document-sha256")
    parser.add_argument("--heading-document-sha256")
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    data_root = arguments.data_root.resolve()
    if arguments.run_relative_root.is_absolute() or ".." in arguments.run_relative_root.parts:
        parser.error("--run-relative-root must be contained beneath --data-root")
    if not any(
        (
            arguments.ledger,
            arguments.conversion_pages,
            arguments.baseline_document,
            arguments.alignment_benchmark,
            arguments.baseline_table_root,
            arguments.assembled_reconstruction,
            arguments.alignment_projection,
            arguments.assembled_partition_audit,
            arguments.consumer_audit,
            arguments.projection_packaging_benchmark,
            arguments.freeze_migration_inputs,
            arguments.compatibility_schema_decision,
            arguments.deep_audit_legacy_conversions,
            arguments.legacy_alignment_output,
            arguments.legacy_overlay_output,
        )
    ):
        parser.error("select an explicit operation, for example --ledger")
    if arguments.freeze_migration_inputs and arguments.collection_spec is None:
        parser.error("--collection-spec is required for --freeze-migration-inputs")
    if arguments.ledger:
        print(
            write_conversion_scaling_ledger(
                data_root,
                output_root=arguments.output_root,
                run_relative_root=arguments.run_relative_root,
                source_id=arguments.source_id,
            )
        )
    if arguments.conversion_pages is not None and not arguments.skip_conversion_profile:
        if arguments.bind_existing_conversion_profile:
            print(
                bind_existing_conversion_pages_profile(
                    data_root,
                    arguments.conversion_pages,
                    output_root=arguments.output_root,
                    run_relative_root=arguments.run_relative_root,
                )
            )
        elif arguments.expected_page_count is None:
            parser.error("--expected-page-count is required with --conversion-pages")
        else:
            print(
                write_conversion_pages_profile(
                    data_root,
                    arguments.conversion_pages,
                    expected_page_count=arguments.expected_page_count,
                    output_root=arguments.output_root,
                    run_relative_root=arguments.run_relative_root,
                    source_id=arguments.source_id,
                )
            )
    if (arguments.baseline_document is None) != (arguments.heading_document is None):
        parser.error("--baseline-document and --heading-document are required together")
    if (
        arguments.baseline_document is not None
        and arguments.heading_document is not None
        and not arguments.skip_document_overlay_profile
    ):
        print(
            write_document_level_overlay_profile(
                data_root,
                arguments.baseline_document,
                arguments.heading_document,
                output_root=arguments.output_root,
                run_relative_root=arguments.run_relative_root,
                source_id=arguments.source_id,
            )
        )
    if arguments.alignment_benchmark:
        print(write_alignment_scaling_benchmark(data_root, output_root=arguments.output_root))
    if (arguments.baseline_table_root is None) != (arguments.heading_table_root is None):
        parser.error("--baseline-table-root and --heading-table-root are required together")
    if arguments.baseline_table_root is not None and arguments.heading_table_root is not None:
        print(
            write_table_bundle_comparison(
                data_root,
                arguments.baseline_table_root,
                arguments.heading_table_root,
                output_root=arguments.output_root,
                source_id=arguments.source_id,
            )
        )
    if arguments.assembled_reconstruction or arguments.alignment_projection:
        if arguments.conversion_pages is None or arguments.expected_page_count is None:
            parser.error(
                "--conversion-pages and --expected-page-count are required for derived profiles"
            )
    if arguments.assembled_reconstruction:
        print(
            write_assembled_reconstruction_profile(
                data_root,
                arguments.conversion_pages,
                expected_page_count=arguments.expected_page_count,
                output_root=arguments.output_root,
                run_relative_root=arguments.run_relative_root,
                source_id=arguments.source_id,
            )
        )
    if arguments.alignment_projection:
        print(
            write_alignment_projection_profile(
                data_root,
                arguments.conversion_pages,
                expected_page_count=arguments.expected_page_count,
                output_root=arguments.output_root,
                run_relative_root=arguments.run_relative_root,
                source_id=arguments.source_id,
            )
        )
    performance_root = arguments.output_root
    if arguments.deep_audit_legacy_conversions:
        report = deep_audit_legacy_conversions(
            data_root / arguments.run_relative_root / "document_parse_evidence/docling_conversions",
            progress=lambda name, current, total, elapsed: logging.info(
                "deep conversion audit %s/%s id=%s elapsed=%.1fs",
                current,
                total,
                name,
                elapsed,
            ),
        )
        print(
            write_compatibility_report(
                performance_root / "task03h_legacy_conversion_deep_audit.json",
                report,
            )
        )
    if arguments.legacy_alignment_output is not None:
        if (
            arguments.conversion_pages is None
            or arguments.expected_page_count is None
            or arguments.legacy_conversion_pages_sha256 is None
        ):
            parser.error(
                "legacy alignment replay requires conversion pages, page count, and checksum"
            )
        report = derive_legacy_alignment_projection(
            arguments.conversion_pages,
            arguments.legacy_alignment_output,
            expected_page_count=arguments.expected_page_count,
            expected_sha256=arguments.legacy_conversion_pages_sha256,
            progress=lambda current, total, elapsed: logging.info(
                "alignment replay %s/%s pages elapsed=%.1fs eta=%.1fs",
                current,
                total,
                elapsed,
                elapsed / current * (total - current),
            ),
        )
        print(
            write_compatibility_report(
                performance_root / "task03h_k2_alignment_replay.json",
                report,
            )
        )
    if arguments.legacy_overlay_output is not None:
        if (
            arguments.baseline_document is None
            or arguments.heading_document is None
            or arguments.baseline_document_sha256 is None
            or arguments.heading_document_sha256 is None
        ):
            parser.error("legacy overlay replay requires both documents and checksums")
        report = derive_legacy_heading_overlay(
            arguments.baseline_document,
            arguments.heading_document,
            arguments.legacy_overlay_output,
            expected_baseline_sha256=arguments.baseline_document_sha256,
            expected_heading_sha256=arguments.heading_document_sha256,
        )
        print(
            write_compatibility_report(
                performance_root / "task03h_k2_heading_overlay_replay.json",
                report,
            )
        )
    if arguments.assembled_partition_audit:
        if arguments.conversion_pages is None or arguments.expected_page_count is None:
            parser.error(
                "--conversion-pages and --expected-page-count are required for partition audit"
            )
        report = audit_assembled_partition(
            arguments.conversion_pages,
            expected_page_count=arguments.expected_page_count,
        )
        print(
            write_compatibility_report(
                performance_root / "task03h_assembled_partition_audit.json",
                report,
            )
        )
    if arguments.consumer_audit:
        print(
            write_compatibility_report(
                performance_root / "task03h_conversion_pages_consumer_audit.json",
                conversion_pages_consumer_audit(),
            )
        )
    if arguments.projection_packaging_benchmark is not None:
        report = benchmark_projection_packaging(
            arguments.projection_packaging_benchmark,
            performance_root / "projection_packaging_candidates",
        )
        print(
            write_compatibility_report(
                performance_root / "task03h_projection_packaging_benchmark.json",
                report,
            )
        )
    if arguments.freeze_migration_inputs:
        collection = json.loads(arguments.collection_spec.read_bytes())
        report = freeze_migration_inputs(
            data_root / arguments.run_relative_root,
            list(collection["source_ids"]),
        )
        print(
            write_compatibility_report(
                performance_root / "task03h_migration_input_freeze.json",
                report,
            )
        )
    if arguments.compatibility_schema_decision:
        print(
            write_compatibility_report(
                performance_root / "task03h_gateb_schema_decision.json",
                compatibility_schema_decision(),
            )
        )
