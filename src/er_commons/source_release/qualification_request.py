"""Portable acquisition requests keep source qualification separate from execution."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.source_release.acquisition_limits import AcquisitionLimits
from er_commons.source_release.qualification import QualificationPolicy, validate_document_url


class EvidenceReference(BaseModel):
    """Bind a compact accepted record without claiming fresh payload equality."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    relative_path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def contained(self) -> EvidenceReference:
        """Keep evidence references portable and outside traversal paths."""
        path = Path(self.relative_path)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise ValueError("evidence reference must be a contained relative path")
        return self


class SubstitutionProvenance(BaseModel):
    """Record the selected F1 exception without granting general Final eligibility."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["er_commons.recovery.source_substitution.v1"]
    logical_source_id: Literal["deir_appendix_f1"]
    physical_source_id: Literal["feir_appendix_f1"]
    edition: Literal["final_eir"]
    scope_exception: Literal["f1_only"]
    edition_equivalence: Literal["not_established"]
    original_release_ref: EvidenceReference
    wrong_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    census_ref: EvidenceReference
    revision_context_unit_ids: tuple[str, str]
    substitution_reason: str = Field(min_length=1)
    processing_contract: Literal["qualified_substitute_separate_conversion_gate"]

    @model_validator(mode="after")
    def distinct_contexts(self) -> SubstitutionProvenance:
        """Require the two distinct reviewed revision-context units."""
        if len(set(self.revision_context_unit_ids)) != 2:
            raise ValueError("revision context units must be distinct")
        return self


class QualifiedAcquisitionSpec(BaseModel):
    """Select one URL, fresh namespace, finite policy and explicit provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["er_commons.qualified_acquisition_spec.v1"]
    source_url: str
    destination: Path
    policy: QualificationPolicy
    limits: AcquisitionLimits
    provenance: SubstitutionProvenance

    @model_validator(mode="after")
    def selected_identity(self) -> QualifiedAcquisitionSpec:
        """Reject ambiguous routing before any network or output operation."""
        validate_document_url(self.source_url, self.policy)
        if self.destination.is_absolute() or ".." in self.destination.parts:
            raise ValueError("destination must be a contained relative directory")
        if not self.destination.parts or self.destination.parts[:3] != ("datasets", "ceqa", "raw"):
            raise ValueError("destination must select a fresh raw source namespace")
        if self.policy.edition != self.provenance.edition:
            raise ValueError("qualification and substitution edition disagree")
        if self.policy.expected_document_center_id != 2972:
            raise ValueError("F1 substitution must select Document Center 2972")
        return self


def load_qualification_request(path: Path) -> QualifiedAcquisitionSpec:
    """Validate a small source-free request; never inspect referenced PDF bytes."""
    if path.stat().st_size > 1_048_576:
        raise ValueError("qualification request exceeds 1 MiB")
    return QualifiedAcquisitionSpec.model_validate_json(path.read_bytes())
