"""Closed request model for Task 06H planning and bounded rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


class Task06HRequestSpec(BaseModel):
    """Require every external Phase 2 input and every render limit explicitly."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["er_commons.extraction_review_request.v2"]
    operation: Literal["prepare", "build_final"]
    review_pass: Literal["task06h_replacement"]
    data_root: Path
    correspondence_root: Path
    comparison_root: Path
    qualification_root: Path
    task04_gate_d_root: Path
    baseline_publications_root: Path
    selected_publications_root: Path
    deir_source_manifest: Path
    f1_source_manifest: Path
    accepted_candidate_root: Path
    plan_root: Path | None = None
    expected_source_count: Literal[35]
    render_pages: bool = False
    renderer_scale: float = 1.0
    worker_count: Literal[1] = 1
    cpu_thread_limit: Literal[2] = 2
    rss_limit_bytes: Literal[2147483648] = 2147483648
    wall_time_limit_seconds: Literal[3600] = 3600
    output_limit_bytes: Literal[1073741824] = 1073741824
    minimum_free_bytes: Literal[2147483648] = 2147483648

    @model_validator(mode="after")
    def validate_operation(self) -> Task06HRequestSpec:
        """Keep preparation source-free and rendering explicitly enabled."""
        if self.operation == "prepare" and (self.render_pages or self.plan_root is not None):
            raise ValueError("Task 06H preparation cannot render or consume a plan root")
        if self.operation == "build_final" and (not self.render_pages or self.plan_root is None):
            raise ValueError("Task 06H rendering requires render_pages=true and plan_root")
        if self.renderer_scale != 1.0:
            raise ValueError("Task 06H renderer scale is frozen at 1.0")
        return self


__all__ = ["Task06HRequestSpec"]
