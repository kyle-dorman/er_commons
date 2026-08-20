"""Strict requests and observations exchanged by qualification processes."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QualificationRecord(BaseModel):
    """Reject coercion and undeclared fields at process boundaries."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ResourceLimits(QualificationRecord):
    """Hard limits enforced around one isolated child process."""

    max_rss_bytes: int = Field(gt=0)
    max_wall_seconds: float = Field(gt=0)
    minimum_available_bytes: int = Field(default=4 * 1024**3, gt=0)
    max_swap_growth_bytes: int = Field(default=512 * 1024**2, ge=0)
    sample_interval_seconds: float = Field(default=0.1, gt=0, le=1.0)
    termination_grace_seconds: float = Field(default=15.0, gt=0)


class ResourceObservation(QualificationRecord):
    """Measured process-tree and system resource outcome for one child."""

    process_tree_peak_rss_bytes: int = Field(ge=0)
    wall_seconds: float = Field(ge=0)
    minimum_system_available_bytes: int = Field(ge=0)
    swap_delta_bytes: int = Field(ge=0)
    stdout: str
    stderr: str


class GateCRequest(QualificationRecord):
    """Coordinator inputs after CLI parsing and environment resolution."""

    data_root: Path
    source_root: Path
    output_root: Path
    config_path: Path
    stop_after_ranges: int | None = Field(default=None, gt=0)
    range_limits: ResourceLimits
    aggregate_limits: ResourceLimits

    @field_validator("data_root", "source_root", "output_root", "config_path")
    @classmethod
    def require_absolute_paths(cls, value: Path) -> Path:
        if not value.is_absolute():
            raise ValueError("qualification paths must be absolute")
        return value


class RangeWorkerSpec(QualificationRecord):
    """Validated file protocol for one range-conversion subprocess."""

    run_id: str
    run_root: Path
    data_root: Path
    source_root: Path
    config_path: Path
    plan_path: Path
    range_id: str

    @field_validator("run_root", "data_root", "source_root", "config_path", "plan_path")
    @classmethod
    def require_absolute_paths(cls, value: Path) -> Path:
        if not value.is_absolute():
            raise ValueError("worker paths must be absolute")
        return value


class AggregateWorkerSpec(QualificationRecord):
    """Validated file protocol for the global aggregate subprocess."""

    run_id: str
    run_root: Path
    data_root: Path
    source_root: Path
    config_path: Path
    plan_path: Path

    @field_validator("run_root", "data_root", "source_root", "config_path", "plan_path")
    @classmethod
    def require_absolute_paths(cls, value: Path) -> Path:
        if not value.is_absolute():
            raise ValueError("worker paths must be absolute")
        return value


class GateCCompletion(QualificationRecord):
    """Terminal Gate C record required before completed-run reuse."""

    schema_version: str
    run_id: str
    status: str
    plan_id: str
    aggregate_conversion_id: str
    artifact_inventory: str
    artifact_inventory_sha256: str
    completion_last: bool


class ExpectedGateCCompletion(QualificationRecord):
    """Identity and lineage expected by a caller reusing Gate C evidence."""

    run_id: str
    plan_id: str
    aggregate_conversion_id: str | None = None
