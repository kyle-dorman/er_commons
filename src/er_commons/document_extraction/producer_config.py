"""Typed configuration for one complete-document producer run."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from er_commons.document_extraction.routing import (
    NumericTableThresholds,
    StrictTableThresholds,
)
from er_commons.table_extraction.models import CleanupConfig, DetectionConfig


class CompleteSource(BaseModel):
    """One frozen manifest-selected source and its expected immutable identity."""

    source_id: str
    official_title: str
    expected_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_byte_size: int = Field(gt=0)
    expected_pdf_page_count: int = Field(gt=0)


class ProducerConfig(BaseModel):
    """Closed Task 03C producer policy and accepted parser configuration."""

    schema_version: Literal["1.0.0"]
    producer_policy_version: Literal["task03c-v1", "task03c-v2"]
    pipeline_id: str
    source_release_version: str
    source_manifest_relative_path: Path
    source: CompleteSource
    artifact_relative_root: Path
    model_inventory_relative_path: Path
    configuration_id: Literal["docling_native_pypdfium2_heron_layout_only_cpu"]
    backend: Literal["pypdfium2"]
    device: Literal["cpu"]
    thread_count: Literal[4]
    document_timeout_seconds: None = None
    strict_table_dominant_thresholds: StrictTableThresholds
    numeric_table_bearing_thresholds: NumericTableThresholds
    table_detection: DetectionConfig
    table_cleanup: CleanupConfig

    @property
    def source_manifest_path(self) -> Path:
        """Expose the shared sealed-release selection interface."""
        return self.source_manifest_relative_path

    @model_validator(mode="after")
    def validate_relative_paths(self) -> ProducerConfig:
        """Keep all committed paths contained below ER_COMMONS_DATA_ROOT."""
        for path in (
            self.source_manifest_relative_path,
            self.artifact_relative_root,
            self.model_inventory_relative_path,
        ):
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("producer paths must be contained relative paths")
        return self


def load_producer_config(path: Path) -> tuple[ProducerConfig, str]:
    """Load the checked-in producer contract and return its byte checksum."""
    raw = path.read_bytes()
    return ProducerConfig.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
