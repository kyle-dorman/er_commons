"""Typed configuration for one complete-document producer run."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from er_commons.document_parsing.content_parsing.routing import (
    NumericTableThresholds,
    StrictTableThresholds,
)
from er_commons.document_parsing.table_reconstruction.models import (
    CleanupConfig,
    DetectionConfig,
    LearnedFallbackConfig,
)


class CompleteSource(BaseModel):
    """One frozen manifest-selected source and its expected immutable identity."""

    source_id: str
    official_title: str
    expected_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_byte_size: int = Field(gt=0)
    expected_pdf_page_count: int = Field(gt=0)


class HeadingHierarchyConfig(BaseModel):
    """Frozen maintained Docling hierarchy options for a producer candidate."""

    enabled: Literal[True]
    use_bookmarks: Literal[True]
    use_numbering: Literal[True]
    use_style: Literal[True]
    numbering_schemes: None = None
    max_level: Literal[6]
    bookmark_match_threshold: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_maintained_defaults(self) -> HeadingHierarchyConfig:
        """Reject threshold tuning outside Docling's maintained defaults."""
        if self.bookmark_match_threshold != 0.8:
            raise ValueError("heading bookmark threshold differs from maintained default")
        return self


class ContentParsingConfig(BaseModel):
    """Closed Task 03C producer policy and accepted parser configuration."""

    schema_version: Literal["1.0.0"]
    producer_policy_version: Literal[
        "task03c-v1",
        "task03c-v2",
        "task03e-v1",
        "task03c-v2-task03g1a-v1",
        "task03e-v1-task03g1a-v1",
    ]
    pipeline_id: str
    source_release_version: str
    source_manifest_relative_path: Path
    source: CompleteSource
    artifact_relative_root: Path
    model_inventory_relative_path: Path
    configuration_id: Literal[
        "docling_native_pypdfium2_heron_layout_only_cpu",
        "docling_native_pypdfium2_heron_layout_heading_hierarchy_defaults_cpu",
        "docling_native_pypdfium2_heron_layout_tableformer_fallback_cpu",
        "docling_native_pypdfium2_heron_layout_heading_hierarchy_tableformer_fallback_cpu",
    ]
    backend: Literal["pypdfium2"]
    device: Literal["cpu"]
    thread_count: Literal[4]
    document_timeout_seconds: None = None
    heading_hierarchy_options: HeadingHierarchyConfig | None = None
    strict_table_dominant_thresholds: StrictTableThresholds
    numeric_table_bearing_thresholds: NumericTableThresholds
    table_detection: DetectionConfig
    table_cleanup: CleanupConfig
    learned_table_fallback: LearnedFallbackConfig = Field(default_factory=LearnedFallbackConfig)

    @property
    def source_manifest_path(self) -> Path:
        """Expose the shared sealed-release selection interface."""
        return self.source_manifest_relative_path

    @model_validator(mode="after")
    def validate_relative_paths(self) -> ContentParsingConfig:
        """Keep paths contained and hierarchy identity fail-closed."""
        for path in (
            self.source_manifest_relative_path,
            self.artifact_relative_root,
            self.model_inventory_relative_path,
        ):
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("producer paths must be contained relative paths")
        hierarchy_enabled = self.heading_hierarchy_options is not None
        hierarchy_policy = self.producer_policy_version.startswith("task03e-v1")
        hierarchy_identity = "heading_hierarchy" in self.configuration_id
        if not (hierarchy_enabled == hierarchy_policy == hierarchy_identity):
            raise ValueError("producer hierarchy policy, options, and identity differ")
        fallback_enabled = self.learned_table_fallback.enabled
        fallback_policy = "task03g1a" in self.producer_policy_version
        fallback_identity = "tableformer_fallback" in self.configuration_id
        if not (fallback_enabled == fallback_policy == fallback_identity):
            raise ValueError("producer fallback policy, configuration, and identity differ")
        return self


def load_content_parsing_config(path: Path) -> tuple[ContentParsingConfig, str]:
    """Load the checked-in producer contract and return its byte checksum."""
    raw = path.read_bytes()
    return ContentParsingConfig.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
