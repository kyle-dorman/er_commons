"""Dispatch the standard document workflow through its explicit conversion policy."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.artifact_io import canonical_json_sha256, write_json_atomic
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.runtime import ChunkedConversionRequest, ResourceLimits
from er_commons.chunked_conversion.runtime.inputs import behavior_code_identity
from er_commons.chunked_conversion.runtime.planning import build_fixed_size_plan
from er_commons.document_parsing.content_parsing.application import run_document_parsing
from er_commons.document_parsing.content_parsing.chunked_application import (
    run_chunked_document_parsing,
)
from er_commons.document_parsing.content_parsing.config import load_content_parsing_config
from er_commons.document_parsing.content_parsing.preparation import prepare_content_parsing
from er_commons.document_parsing.content_parsing.publication import task_artifact_root


class ChunkedSourceSelection(BaseModel):
    """Stable source-size rule recorded in each generated policy."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    pdf_page_count_greater_than: Literal[300]


class ChunkedExecutionPolicy(BaseModel):
    """Checked, explicit opt-in for sources requiring restartable conversion."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: Literal["er_commons.chunked_execution_policy.v1"]
    mode: Literal["fixed_size"]
    source_selection: ChunkedSourceSelection
    target_range_size: int = Field(default=225, gt=0)
    hard_maximum: int = Field(default=275, gt=0)
    overlap_pages: Literal[1] = 1
    max_range_rss_bytes: int = Field(default=20 * 1024**3, gt=0)
    max_aggregate_rss_bytes: int = Field(default=16 * 1024**3, gt=0)
    max_wall_seconds: float = Field(default=14400.0, gt=0)

    @model_validator(mode="after")
    def validate_sizes(self) -> ChunkedExecutionPolicy:
        if self.target_range_size > self.hard_maximum:
            raise ValueError("target range size exceeds the hard maximum")
        return self


def run_configured_document_parsing(
    data_root: Path,
    config_path: Path,
    *,
    policy_path: Path | None = None,
) -> Path:
    """Use monolithic conversion unless a sibling policy explicitly selects chunking."""
    selected_policy = policy_path or config_path.with_name("chunked_conversion.json")
    if not selected_policy.is_file():
        return run_document_parsing(data_root, config_path)
    policy = ChunkedExecutionPolicy.model_validate_json(selected_policy.read_bytes())
    config, config_sha256 = load_content_parsing_config(config_path)
    prepared = prepare_content_parsing(data_root, config=config, config_sha256=config_sha256)
    threshold = policy.source_selection.pdf_page_count_greater_than
    if prepared.source.source_page_count <= threshold:
        raise ValueError("chunk policy selected a source at or below its page-count threshold")
    project_root = Path(__file__).resolve().parents[4]
    task_root = task_artifact_root(data_root, config.artifact_relative_root)
    monolithic_final = task_root / prepared.identity.run_id
    if monolithic_final.exists():
        return run_document_parsing(data_root, config_path)
    plan = build_fixed_size_plan(
        prepared,
        behavior_code_identity(project_root),
        target_range_size=policy.target_range_size,
        hard_maximum=policy.hard_maximum,
        overlap_pages=policy.overlap_pages,
    )
    plan_path = _persist_plan_variant(task_root, plan)

    request = ChunkedConversionRequest(
        data_root=data_root.resolve(),
        output_root=(task_root / "chunked_runs").resolve(),
        conversion_root=(task_root / "docling_conversions").resolve(),
        config_path=config_path.resolve(),
        plan_path=plan_path.resolve(),
        range_limits=ResourceLimits(
            max_rss_bytes=policy.max_range_rss_bytes,
            max_wall_seconds=policy.max_wall_seconds,
        ),
        aggregate_limits=ResourceLimits(
            max_rss_bytes=policy.max_aggregate_rss_bytes,
            max_wall_seconds=policy.max_wall_seconds,
        ),
    )
    return run_chunked_document_parsing(
        data_root,
        config_path,
        plan_path,
        request=request,
    )


def _persist_plan_variant(task_root: Path, plan: RangePlan) -> Path:
    """Store aggregate variants separately while requiring one exact child plan."""
    plan_root = task_root / "chunked_plans" / plan.plan_id
    variant_id = canonical_json_sha256(plan.model_dump(mode="json"))
    plan_path = plan_root / f"{variant_id}.json"
    if plan_path.is_file():
        if RangePlan.model_validate_json(plan_path.read_bytes()) != plan:
            raise ValueError(f"existing chunk plan differs: {plan_path}")
        return plan_path
    for existing_path in plan_root.glob("*.json"):
        existing = RangePlan.model_validate_json(existing_path.read_bytes())
        if existing.plan_id != plan.plan_id or existing.ranges != plan.ranges:
            raise ValueError(f"existing child plan differs: {existing_path}")
    plan_root.mkdir(parents=True, exist_ok=True)
    write_json_atomic(plan_path, plan.model_dump(mode="json"))
    return plan_path


__all__ = ["ChunkedExecutionPolicy", "run_configured_document_parsing"]
