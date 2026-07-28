"""Tests for the clean document-extraction configuration boundary."""

from pathlib import Path

from er_commons.document_extraction.config import (
    PipelineConfig,
    SelectionSpec,
    contiguous_ranges,
    load_pipeline_config,
    load_selection_spec,
    range_name,
)


def test_tracked_pipeline_preserves_exact_review_ranges() -> None:
    """The rewrite cannot quietly expand or regroup the accepted pilot."""
    config, _digest = load_pipeline_config(
        Path("configs/brisbane_baylands_2025_deir_task03a15_document_pipeline_v4.json")
    )
    selection, _selection_digest = load_selection_spec(config.selection_spec_path)
    derived = [
        range_name(source.source_id, first_page, last_page)
        for source in selection.sources
        for first_page, last_page in contiguous_ranges(source)
    ]

    assert selection.expected_selected_page_count == 10
    assert derived == config.expected_range_names


def test_contiguous_ranges_merge_only_adjacent_pages() -> None:
    """Sparse page selections become minimal ordered conversion ranges."""
    selection = SelectionSpec.model_validate(
        {
            "pilot_spec_schema_version": "1",
            "pilot_id": "example",
            "source_release_version": "release",
            "source_manifest_path": "datasets/example/manifest.json",
            "page_number_basis": "one_based_physical_pdf_page",
            "expected_selected_page_count": 4,
            "sources": [
                {
                    "source_id": "source",
                    "expected_sha256": "a" * 64,
                    "expected_pdf_page_count": 10,
                    "page_ranges": [
                        {
                            "first_page": 2,
                            "last_page": 3,
                            "expected_printed_labels": [],
                            "stressors": ["adjacent"],
                        },
                        {
                            "first_page": 7,
                            "last_page": 8,
                            "expected_printed_labels": [],
                            "stressors": ["adjacent"],
                        },
                    ],
                }
            ],
        }
    )

    assert list(contiguous_ranges(selection.sources[0])) == [(2, 3), (7, 8)]


def test_pipeline_paths_must_be_relative() -> None:
    """Committed execution contracts cannot embed a developer data root."""
    config, _ = load_pipeline_config(
        Path("configs/brisbane_baylands_2025_deir_task03a15_document_pipeline_v4.json")
    )
    payload = config.model_dump(mode="json")
    payload["artifact_relative_root"] = "/absolute/output"

    try:
        PipelineConfig.model_validate(payload)
    except ValueError as error:
        assert "paths must be relative" in str(error)
    else:
        raise AssertionError("absolute artifact root was accepted")
