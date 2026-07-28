"""Tests for semantic JSON and timing comparison."""

import json
from pathlib import Path

import pytest

from er_commons.document_extraction.acceptance import require_acceptance
from er_commons.document_extraction.comparison import (
    compare_json_file,
    compare_timings,
    normalize_document_json,
    structural_diff,
)


def test_document_normalization_masks_only_known_data_uris() -> None:
    """Image metadata and unexpected URIs remain part of equivalence."""
    payload = {
        "pages": {
            "4": {
                "image": {
                    "mimetype": "image/png",
                    "dpi": 144,
                    "uri": "data:image/png;base64,page",
                }
            }
        },
        "pictures": [
            {
                "image": {
                    "mimetype": "image/png",
                    "size": [20, 30],
                    "uri": "data:image/png;base64,picture",
                }
            }
        ],
        "unexpected": {"uri": "must-remain"},
    }

    normalized = normalize_document_json(payload)

    assert normalized["pages"]["4"]["image"] == {
        "mimetype": "image/png",
        "dpi": 144,
        "uri": "<generated-image-data-uri>",
    }
    assert normalized["pictures"][0]["image"]["size"] == [20, 30]
    assert normalized["pictures"][0]["image"]["uri"] == "<generated-image-data-uri>"
    assert normalized["unexpected"]["uri"] == "must-remain"


def test_structural_diff_counts_all_but_bounds_details() -> None:
    """Mismatch reports stay readable without understating total changes."""
    result = structural_diff(
        {"values": [1, 2, 3, 4]},
        {"values": [10, 20, 30, 40]},
        limit=2,
    )

    assert result["total_difference_count"] == 4
    assert result["difference_count_shown"] == 2
    assert result["truncated"] is True


def test_full_json_comparison_ignores_only_formatting(tmp_path: Path) -> None:
    """Canonical equality is independent of JSON whitespace and key order."""
    old = tmp_path / "old.json"
    new = tmp_path / "new.json"
    old.write_text('{"b": 2, "a": 1}\n')
    new.write_text(json.dumps({"a": 1, "b": 2}, indent=2))

    comparison = compare_json_file(old, new, mode="full")

    assert comparison["old_raw_sha256"] != comparison["new_raw_sha256"]
    assert comparison["old_sha256"] == comparison["new_sha256"]
    assert comparison["equal"] is True


def test_timing_comparison_is_report_only() -> None:
    """Runtime differences are measured without entering semantic equality."""
    old = [{"source_id": "a", "first_page": 1, "last_page": 1, "wall_seconds": 2.0}]
    new = [{"source_id": "a", "first_page": 1, "last_page": 1, "wall_seconds": 3.0}]

    result = compare_timings(old, new)

    assert result["difference_seconds"] == 1.0
    assert result["difference_percent"] == 50.0


def test_acceptance_failure_stops_after_report_path_is_known(tmp_path: Path) -> None:
    """The pipeline raises rather than promoting a changed parser artifact."""
    comparison_path = tmp_path / "comparison.json"

    with pytest.raises(RuntimeError, match="comparison.json"):
        require_acceptance({"accepted": False}, comparison_path)
