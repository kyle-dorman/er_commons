"""Persisted stage-one lifecycle, result, and observability records."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

STAGE_COMPLETION_ROLES = (
    "baseline_producer",
    "hierarchy_producer",
    "canonical",
    "hierarchy_correction",
    "semantic",
    "cross_references",
)
STAGE_COMPLETION_ROLE_SET = frozenset(STAGE_COMPLETION_ROLES)


class StrictRecord(BaseModel):
    """Closed immutable record base."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceIdentity(StrictRecord):
    """Manifest-derived source identity used in completion records."""

    source_id: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    pdf_page_count: int = Field(gt=0)


class StateEvent(StrictRecord):
    """One append-only transition matching the accepted v1 schema shape."""

    record_type: Literal["document_state_event"] = "document_state_event"
    schema_version: Literal["er_commons.document_state_event.v1"] = (
        "er_commons.document_state_event.v1"
    )
    transaction_id: str
    source_id: str
    attempt: int = Field(ge=1)
    sequence: int = Field(ge=1)
    from_state: Literal["selected", "running"] | None
    to_state: Literal[
        "selected",
        "running",
        "complete",
        "complete_with_warnings",
        "failed_retryable",
        "failed_terminal",
        "cancelled",
    ]
    raw_docling_status: (
        Literal["PENDING", "STARTED", "SUCCESS", "PARTIAL_SUCCESS", "FAILURE", "SKIPPED"] | None
    )


class ArtifactRef(StrictRecord):
    """Relative path and checksum reference."""

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DocumentIdentityRecord(StrictRecord):
    """Persisted preimage proving one document candidate's content and controls."""

    schema_version: Literal["er_commons.document_candidate_identity.v1"]
    production_extraction_id: str = Field(pattern=r"^exv1-[0-9a-f]{64}$")
    candidate_id: str = Field(pattern=r"^docv1-[0-9a-f]{64}$")
    source: SourceIdentity
    content_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    control_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    hierarchy_disposition: dict[str, object]
    run_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stage_completions: dict[str, ArtifactRef]
    terminal_state: Literal["complete", "complete_with_warnings"]

    @model_validator(mode="after")
    def require_all_content_owners(self) -> DocumentIdentityRecord:
        """Require the exact six stage-one completion roles."""
        if set(self.stage_completions) != STAGE_COMPLETION_ROLE_SET:
            raise ValueError("document identity must seal exactly six content owners")
        return self


class DocumentCompletion(StrictRecord):
    """Completion-last record matching the accepted v1 schema shape."""

    record_type: Literal["document_completion"] = "document_completion"
    schema_version: Literal["er_commons.document_completion.v1"] = (
        "er_commons.document_completion.v1"
    )
    transaction_id: str
    source: SourceIdentity
    scope_kind: Literal["full_document"] = "full_document"
    processed_pages: list[int]
    raw_docling_status: Literal["SUCCESS"] = "SUCCESS"
    candidate_id: str
    candidate_inventory: ArtifactRef
    completion_last: Literal[True] = True


class PipelineResult(StrictRecord):
    """Typed child-process handoff from the existing content owners."""

    source_id: str
    raw_docling_status: Literal["SUCCESS", "PARTIAL_SUCCESS", "FAILURE", "SKIPPED"]
    processed_pages: list[int]
    structured_errors: list[dict[str, Any]]
    warnings: list[str]
    final_candidate_root: str
    stage_completions: dict[str, ArtifactRef]
    stage_timings: dict[str, float]
    resource_enforcement: Literal["validated_before_content_owners"]

    @model_validator(mode="after")
    def require_complete_owner_handoff(self) -> PipelineResult:
        """Reject partial or expanded owner handoffs at the process boundary."""
        if set(self.stage_completions) != STAGE_COMPLETION_ROLE_SET:
            raise ValueError("pipeline result must contain exactly six stage completions")
        if set(self.stage_timings) != STAGE_COMPLETION_ROLE_SET:
            raise ValueError("pipeline result must contain exactly six stage timings")
        return self


class AttemptRecord(StrictRecord):
    """Retained non-completion evidence for every transaction attempt."""

    schema_version: Literal["er_commons.document_attempt.v1"] = "er_commons.document_attempt.v1"
    transaction_id: str
    source_id: str
    attempt: int
    disposition: Literal[
        "complete",
        "complete_with_warnings",
        "failed_retryable",
        "failed_terminal",
        "cancelled",
    ]
    failure_class: str | None
    message: str | None
    state_event_paths: list[str]
    completion_path: str | None


class ObservabilityRecord(StrictRecord):
    """Non-identity timing and resource evidence for one attempt."""

    schema_version: Literal["er_commons.document_observability.v1"] = (
        "er_commons.document_observability.v1"
    )
    transaction_id: str
    wall_seconds: float = Field(ge=0)
    peak_rss_bytes: int | None = Field(default=None, ge=0)
    output_bytes: int = Field(ge=0)
    stage_timings: dict[str, float]


class ResourceRecord(StrictRecord):
    """Parent-declared resources for one transaction."""

    schema_version: Literal["er_commons.document_resources.v1"] = "er_commons.document_resources.v1"
    transaction_id: str
    policy: dict[str, Any]
    enforcement: Literal["declared"] = "declared"


class ResourceEnforcementRecord(StrictRecord):
    """Worker-returned proof that preflight preceded content-owner execution."""

    schema_version: Literal["er_commons.document_resource_enforcement.v1"] = (
        "er_commons.document_resource_enforcement.v1"
    )
    transaction_id: str
    enforcement: Literal["validated_before_content_owners"]
