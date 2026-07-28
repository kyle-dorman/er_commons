"""Tests for the clean table-extraction configuration contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from er_commons.table_extraction.models import (
    FIRST_600_PAGES,
    REVIEW_SAMPLE_PAGES,
    TableExtractionConfig,
    load_config,
)

UNIFIED_CONFIG = Path(
    "configs/brisbane_baylands_2025_deir_task03a13_unified_table_pipeline_v1.json"
)
FIRST_600_CONFIG = Path(
    "configs/brisbane_baylands_2025_deir_task03a14_first_600_table_pipeline_v1.json"
)


def test_task03a13_config_is_fixed_to_review_sample() -> None:
    """The draft command cannot silently become a 600-page run."""
    config, digest = load_config(UNIFIED_CONFIG)
    assert config.physical_pdf_pages == REVIEW_SAMPLE_PAGES
    assert len(digest) == 64


def test_task03a13_config_rejects_scope_expansion(tmp_path: Path) -> None:
    """Changing the reviewed physical pages requires a new task/configuration."""
    payload = json.loads(UNIFIED_CONFIG.read_text())
    payload["physical_pdf_pages"] = list(range(1, 601))
    changed = tmp_path / "expanded.json"
    changed.write_text(json.dumps(payload))
    with pytest.raises(ValidationError, match="exact configured physical pages"):
        load_config(changed)


def test_task03a13_uses_main_environment_and_baseline() -> None:
    """The unified run names its exact historical comparison input."""
    config, _ = load_config(UNIFIED_CONFIG)
    assert config.comparison_relative_root == Path(
        "pipelines/brisbane_baylands/task_03a12_clean_table_pipeline_v1"
    )


def test_task03a14_is_exactly_first_600_pages() -> None:
    """The large validation cannot silently expand to the full document."""
    config, _ = load_config(FIRST_600_CONFIG)
    assert config.validation_scope == "first_600"
    assert config.physical_pdf_pages == FIRST_600_PAGES
    assert config.comparison_scope == "baseline_pages"


def test_first_600_scope_rejects_partial_range(tmp_path: Path) -> None:
    """A large validation cannot silently skip its final page."""
    payload = json.loads(FIRST_600_CONFIG.read_text())
    payload["physical_pdf_pages"] = payload["physical_pdf_pages"][:-1]
    changed = tmp_path / "partial.json"
    changed.write_text(json.dumps(payload))
    with pytest.raises(ValidationError, match="exact configured physical pages"):
        load_config(changed)


def test_routed_scope_requires_matching_explicit_page_requests() -> None:
    """A document router can select pages without weakening fixed review scopes."""
    payload = json.loads(UNIFIED_CONFIG.read_text())
    payload.update(
        {
            "validation_scope": "routed_pages",
            "physical_pdf_pages": [1000],
            "table_id_prefix": "appendix_g3",
            "family_id_prefix": "appendix_g3_table",
            "routed_pages": [
                {
                    "physical_pdf_page": 1000,
                    "route": "full_page_numeric",
                    "layout_regions_pdf_points_bottom_left": [],
                }
            ],
        }
    )
    config = TableExtractionConfig.model_validate(payload)
    assert config.routed_pages[0].route == "full_page_numeric"

    payload["physical_pdf_pages"] = [999]
    with pytest.raises(ValidationError, match="exact configured physical pages"):
        TableExtractionConfig.model_validate(payload)
