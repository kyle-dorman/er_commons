"""Persisted document-publication lifecycle and handoff records."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

type JsonObject = dict[str, Any]

DOCUMENT_PROCESS_NAMES = (
    "content_parsing",
    "heading_evidence_parsing",
    "record_mapping",
    "hierarchy_inference",
    "document_structure",
    "document_reference_linking",
)
DOCUMENT_PRODUCT_ROLES = (
    "stable_content_evidence",
    "heading_evidence",
    "mapped_records",
    "hierarchy_decisions",
    "structured_document",
    "linked_document",
)
DOCUMENT_PROCESS_NAME_SET = frozenset(DOCUMENT_PROCESS_NAMES)
DOCUMENT_PRODUCT_ROLE_SET = frozenset(DOCUMENT_PRODUCT_ROLES)


class StrictRecord(BaseModel):
    """Closed immutable record base."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceIdentity(StrictRecord):
    """Manifest-derived source identity used in completion records."""

    source_id: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    pdf_page_count: int = Field(gt=0)


class StateEvent(StrictRecord):
    """One append-only transition in the strict native-v2 document contract."""

    record_type: Literal["document_state_event"] = "document_state_event"
    schema_version: Literal["er_commons.document_state_event.v2"] = (
        "er_commons.document_state_event.v2"
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

    schema_version: Literal["er_commons.document_candidate_identity.v2"]
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
    def require_all_document_processes(self) -> DocumentIdentityRecord:
        """Require the exact six stage-one completion roles."""
        if set(self.stage_completions) != DOCUMENT_PRODUCT_ROLE_SET:
            raise ValueError("document identity must seal exactly six document products")
        return self


class DocumentCompletion(StrictRecord):
    """Completion-last record in the strict native-v2 document contract."""

    record_type: Literal["document_completion"] = "document_completion"
    schema_version: Literal["er_commons.document_completion.v2"] = (
        "er_commons.document_completion.v2"
    )
    transaction_id: str
    source: SourceIdentity
    scope_kind: Literal["full_document"] = "full_document"
    processed_pages: list[int]
    raw_docling_status: Literal["SUCCESS"] = "SUCCESS"
    candidate_id: str
    candidate_inventory: ArtifactRef
    completion_last: Literal[True] = True


class DownstreamReplayRecord(StrictRecord):
    """Evidence for document republication without a document execution attempt."""

    schema_version: Literal["er_commons.downstream_document_replay.v2"] = (
        "er_commons.downstream_document_replay.v2"
    )
    replay_id: str = Field(pattern=r"^replayv1-[0-9a-f]{64}$")
    source: SourceIdentity
    source_candidate_id: str = Field(pattern=r"^docv1-[0-9a-f]{64}$")
    source_completion_ref: ArtifactRef
    source_inventory_ref: ArtifactRef
    reused_stage_completions: dict[str, ArtifactRef]
    replacement_linked_document_completion_ref: ArtifactRef
    candidate_id: str = Field(pattern=r"^docv1-[0-9a-f]{64}$")
    publication_mode: Literal["downstream_only"] = "downstream_only"
    document_attempt_allocated: Literal[False] = False

    @model_validator(mode="after")
    def require_only_reusable_upstream_owners(self) -> DownstreamReplayRecord:
        """Keep cross-reference replacement distinct from five reused owners."""
        expected = DOCUMENT_PRODUCT_ROLE_SET - {"linked_document"}
        if set(self.reused_stage_completions) != expected:
            raise ValueError("downstream replay must reuse exactly five upstream products")
        return self


class PipelineResult(StrictRecord):
    """Typed child-process handoff from document transformations."""

    source_id: str
    raw_docling_status: Literal["SUCCESS", "PARTIAL_SUCCESS", "FAILURE", "SKIPPED"]
    processed_pages: list[int]
    structured_errors: list[dict[str, Any]]
    warnings: list[str]
    final_candidate_root: str
    stage_completions: dict[str, ArtifactRef]
    stage_timings: dict[str, float]
    resource_enforcement: Literal["validated_before_document_processes"]

    @model_validator(mode="after")
    def require_complete_process_handoff(self) -> PipelineResult:
        """Reject partial or expanded document-process handoffs."""
        if set(self.stage_completions) != DOCUMENT_PRODUCT_ROLE_SET:
            raise ValueError("pipeline result must contain exactly six stage completions")
        if set(self.stage_timings) != DOCUMENT_PROCESS_NAME_SET:
            raise ValueError("pipeline result must contain exactly six stage timings")
        return self


class AttemptRecord(StrictRecord):
    """Retained non-completion evidence for every transaction attempt."""

    schema_version: Literal["er_commons.document_attempt.v2"] = "er_commons.document_attempt.v2"
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
    """Worker-returned proof that preflight preceded document processing."""

    schema_version: Literal["er_commons.document_resource_enforcement.v2"] = (
        "er_commons.document_resource_enforcement.v2"
    )
    transaction_id: str
    enforcement: Literal["validated_before_document_processes"]
