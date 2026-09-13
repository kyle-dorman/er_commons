"""Derive typed document-candidate identities from verified publication inputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from er_commons.authority_reference import AuthorityReference, reference_for_path
from er_commons.document_publication.identity import build_candidate_id, canonical_digest
from er_commons.document_publication.preflight import DocumentRun
from er_commons.document_publication.records import (
    ArtifactRef,
    DocumentIdentityRecord,
    PipelineResult,
)
from er_commons.document_publication.storage import content_digest

SuccessDisposition = Literal["complete", "complete_with_warnings"]


@dataclass(frozen=True)
class CandidateIdentity:
    """Typed in-memory projection of the persisted candidate identity record."""

    candidate_id: str
    content_digest: str
    control_digest: str
    terminal_state: SuccessDisposition
    hierarchy_disposition: dict[str, object]
    stage_completions: dict[str, dict[str, object]]
    resolved_spec_ref: AuthorityReference | None = None
    resolved_process_config_refs: dict[str, AuthorityReference] | None = None

    def as_record(self, run: DocumentRun) -> DocumentIdentityRecord:
        """Return the exact v1 identity record written into a candidate."""
        return DocumentIdentityRecord(
            schema_version=(
                "er_commons.document_candidate_identity.v4"
                if self.resolved_process_config_refs is not None
                else "er_commons.document_candidate_identity.v3"
                if self.resolved_spec_ref is not None
                else "er_commons.document_candidate_identity.v2"
            ),
            production_extraction_id=run.spec.production_extraction_id,
            candidate_id=self.candidate_id,
            source=run.source,
            content_digest=self.content_digest,
            control_digest=self.control_digest,
            hierarchy_disposition=self.hierarchy_disposition,
            run_spec_sha256=run.spec_sha256,
            resolved_spec_ref=self.resolved_spec_ref,
            resolved_process_config_refs=self.resolved_process_config_refs,
            stage_completions={
                role: ArtifactRef.model_validate(reference)
                for role, reference in self.stage_completions.items()
            },
            terminal_state=self.terminal_state,
        )


def build_candidate_identity(
    run: DocumentRun,
    *,
    content_root: Path,
    result: PipelineResult,
    recorded_content_inventory: dict[str, Any] | None = None,
    allow_spec_only_identity: bool = False,
) -> CandidateIdentity:
    """Derive the document ID from content and all consumed publication controls."""
    terminal_state: SuccessDisposition = "complete_with_warnings" if result.warnings else "complete"
    stage_completions = {
        role: reference.model_dump(mode="json")
        for role, reference in result.stage_completions.items()
    }
    resolved_spec_ref = (
        reference_for_path(
            run.run_spec_path,
            repository_root=run.project_root,
            artifact_root=run.data_root,
            sha256=run.spec_sha256,
        )
        if run.spec.schema_version.endswith(".v4")
        else None
    )
    resolved_process_config_refs = result.resolved_process_config_refs
    if (
        run.spec.schema_version.endswith(".v4")
        and resolved_process_config_refs is None
        and not allow_spec_only_identity
    ):
        raise ValueError("document run spec v4 lacks sealed process-config references")
    controls = {
        "hierarchy_disposition": run.hierarchy_disposition,
        "run_spec_sha256": run.spec_sha256,
        "stage_completions": stage_completions,
        "terminal_state": terminal_state,
    }
    if resolved_spec_ref is not None:
        controls["resolved_spec_ref"] = resolved_spec_ref.model_dump(mode="json")
    if resolved_process_config_refs is not None:
        controls["resolved_process_config_refs"] = {
            role: item.model_dump(mode="json")
            for role, item in resolved_process_config_refs.items()
        }
    control_digest = canonical_digest(controls)
    digest = (
        canonical_digest(recorded_content_inventory)
        if recorded_content_inventory is not None
        else content_digest(content_root)
    )
    candidate_id = build_candidate_id(
        production_extraction_id=run.spec.production_extraction_id,
        source_id=run.source.source_id,
        content_digest=digest,
        control_digest=control_digest,
    )
    return CandidateIdentity(
        candidate_id=candidate_id,
        content_digest=digest,
        control_digest=control_digest,
        terminal_state=terminal_state,
        hierarchy_disposition=run.hierarchy_disposition,
        stage_completions=stage_completions,
        resolved_spec_ref=resolved_spec_ref,
        resolved_process_config_refs=resolved_process_config_refs,
    )


__all__ = ["CandidateIdentity", "build_candidate_identity"]
