"""Explicit filesystem requests for maintained extraction-review commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.human_review_support.extraction_review.application import build_review_bundle
from er_commons.human_review_support.extraction_review.final_pass import (
    HANDOFF_ID,
    SCOPE_ID,
    prepare_final_extraction_review,
    publish_gate_a_preparation,
)
from er_commons.human_review_support.extraction_review.final_review import (
    FINAL_REVIEW_RUN_ID,
    build_final_extraction_review,
)
from er_commons.human_review_support.extraction_review.gate_d import (
    GateDRequest,
    publish_extraction_review,
)
from er_commons.human_review_support.extraction_review.models import BuildRequest
from er_commons.human_review_support.extraction_review.scope_policy import InputScopePolicy
from er_commons.human_review_support.extraction_review.task06h_review import (
    Task06HRequestSpec,
    execute_task06h_request,
)

Operation = Literal["prepare", "build_bundle", "build_final", "publish"]


class ReviewRequestSpec(BaseModel):
    """Closed request; historical profiles are selected explicitly, never inferred."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["er_commons.extraction_review_request.v1"]
    operation: Operation
    review_pass: Literal["task03h_first", "task03j_final"]
    data_root: Path
    retained_root: Path | None = None
    source_pdf_root: Path | None = None
    prior_review_root: Path | None = None
    gate_a_path: Path | None = None
    gate_c_root: Path | None = None
    schema_root: Path
    review_run_id: str | None = None
    scope_id: str | None = None
    handoff_id: str | None = None
    expected_source_count: int = Field(gt=0)
    required_readiness_status: str | None = None
    expected_decision_count: int | None = None
    expected_visible_toc_card_count: int | None = None
    expected_ambiguous_link_count: int | None = None
    toc_decisions_path: Path | None = None
    render_pages: bool = False
    validate_upstream: bool = False
    raw_docling_scan: bool = False
    build_census: bool = False

    @model_validator(mode="after")
    def validate_operation_inputs(self) -> ReviewRequestSpec:
        """Reject missing bindings and unsupported profile changes before filesystem access."""
        required = {
            "prepare": (
                "retained_root",
                "source_pdf_root",
                "prior_review_root",
                "scope_id",
                "handoff_id",
            ),
            "build_bundle": ("retained_root", "source_pdf_root", "required_readiness_status"),
            "build_final": (
                "retained_root",
                "source_pdf_root",
                "prior_review_root",
                "gate_a_path",
                "scope_id",
                "review_run_id",
            ),
            "publish": (
                "gate_a_path",
                "gate_c_root",
                "review_run_id",
                "expected_decision_count",
                "expected_visible_toc_card_count",
                "expected_ambiguous_link_count",
            ),
        }[self.operation]
        missing = [name for name in required if getattr(self, name) is None]
        if missing:
            raise ValueError(f"review operation {self.operation} requires: {', '.join(missing)}")
        expected_pass = "task03h_first" if self.operation == "build_bundle" else "task03j_final"
        if self.review_pass != expected_pass:
            raise ValueError("review operation and historical pass differ")
        if self.review_pass == "task03j_final":
            self._validate_final_profile()
        if self.operation in {"build_bundle", "build_final"} and not self.render_pages:
            raise ValueError("review rendering must be explicitly requested with render_pages=true")
        if self.operation in {"prepare", "publish"} and self.render_pages:
            raise ValueError("source-free review operation does not render pages")
        return self

    def _validate_final_profile(self) -> None:
        """Keep historical accepted semantics explicit until a later policy task replaces them."""
        if self.expected_source_count != 35:
            raise ValueError("historical final-pass profile requires 35 selected sources")
        for observed, expected in (
            (self.scope_id, SCOPE_ID),
            (self.handoff_id, HANDOFF_ID),
            (self.review_run_id, FINAL_REVIEW_RUN_ID),
        ):
            if observed is not None and observed != expected:
                raise ValueError("selected identity differs from historical final-pass profile")
        if self.operation == "publish" and (
            self.expected_decision_count,
            self.expected_visible_toc_card_count,
            self.expected_ambiguous_link_count,
        ) != (757, 341, 725):
            raise ValueError("selected counts differ from historical final-pass profile")

    def path(self, name: str) -> Path:
        """Return a validated required path with a useful missing-field error."""
        value = getattr(self, name)
        if not isinstance(value, Path):
            raise ValueError(f"review request requires path: {name}")
        return value


def load_review_request(path: Path, operation: Operation) -> ReviewRequestSpec | Task06HRequestSpec:
    """Resolve explicit request paths relative to the request, without settings defaults."""
    raw = path.read_bytes()
    try:
        envelope = json.loads(raw)
    except ValueError as error:
        raise ValueError(f"invalid extraction review request JSON: {path}") from error
    if envelope.get("schema_version") == "er_commons.extraction_review_request.v2":
        task06h = Task06HRequestSpec.model_validate_json(raw)
        if task06h.operation != operation:
            raise ValueError(
                f"review request operation differs: expected={operation} "
                f"observed={task06h.operation}"
            )
        values = task06h.model_dump()
        for name, value in values.items():
            if isinstance(value, Path):
                values[name] = (path.parent / value).resolve()
        return Task06HRequestSpec.model_validate(values)
    spec = ReviewRequestSpec.model_validate_json(raw)
    if spec.operation != operation:
        raise ValueError(
            f"review request operation differs: expected={operation} observed={spec.operation}"
        )
    values = spec.model_dump()
    for name, value in values.items():
        if isinstance(value, Path):
            values[name] = (path.parent / value).resolve()
    return ReviewRequestSpec.model_validate(values)


def execute_review_request(spec: ReviewRequestSpec | Task06HRequestSpec, output_root: Path) -> Path:
    """Dispatch one explicit historical policy request without selecting hidden inputs."""
    if isinstance(spec, Task06HRequestSpec):
        return execute_task06h_request(spec, output_root)
    if spec.operation == "build_bundle":
        return build_review_bundle(
            BuildRequest(
                spec.path("retained_root"),
                spec.data_root,
                output_root,
                InputScopePolicy(spec.expected_source_count, str(spec.required_readiness_status)),
                source_pdf_root=spec.path("source_pdf_root"),
            ),
            schema_root=spec.schema_root,
        )
    if spec.operation == "build_final":
        return build_final_extraction_review(
            spec.data_root,
            spec.path("gate_a_path"),
            output_root,
            task_root=spec.path("retained_root"),
            scope_id=str(spec.scope_id),
            source_pdf_root=spec.path("source_pdf_root"),
            prior_review_root=spec.path("prior_review_root"),
            review_run_id=str(spec.review_run_id),
            schema_root=spec.schema_root,
            toc_decisions_path=spec.toc_decisions_path,
        )
    if spec.operation == "publish":
        return publish_extraction_review(
            GateDRequest(
                spec.path("gate_a_path"),
                spec.path("gate_c_root"),
                spec.schema_root,
                output_root,
                str(spec.review_run_id),
            )
        )
    record = prepare_final_extraction_review(
        spec.data_root,
        repo_root=Path(__file__).resolve().parents[4],
        task_root_relative=spec.path("retained_root").relative_to(spec.data_root).as_posix(),
        task03i_root=spec.path("prior_review_root"),
        source_release_relative=spec.path("source_pdf_root").relative_to(spec.data_root).as_posix(),
        scope_id=str(spec.scope_id),
        handoff_id=str(spec.handoff_id),
        validate_upstream=spec.validate_upstream,
        raw_docling_scan=spec.raw_docling_scan,
        build_census=spec.build_census,
    )
    from er_commons.human_review_support.extraction_review.records import RecordValidator

    RecordValidator(spec.schema_root).validate("gate_a_preparation", record)
    return publish_gate_a_preparation(record, output_root)


def review_command(operation: Operation) -> None:
    """Parse help before reading requests, settings, source files or model resources."""
    parser = argparse.ArgumentParser(description=f"{operation.replace('_', ' ')} extraction review")
    parser.add_argument("--review-spec", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    print(
        execute_review_request(
            load_review_request(args.review_spec.resolve(), operation), args.output_root.resolve()
        )
    )
