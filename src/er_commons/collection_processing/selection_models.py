"""Strict models for a frozen retained-document selection."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.collection_processing.authority_refs import CollectionArtifactReference
from er_commons.collection_processing.contract import canonical_sha256
from er_commons.document_publication.records import SourceIdentity


class SelectedDocumentCandidate(BaseModel):
    """Exact original evidence for one retained downstream-replay candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_ordinal: int = Field(ge=1)
    logical_source_id: str = Field(min_length=1)
    physical_source_id: str = Field(min_length=1)
    source_identity: SourceIdentity
    candidate_id: str = Field(pattern=r"^docv1-[0-9a-f]{64}$")
    candidate_root: str = Field(min_length=1)
    document_identity_ref: CollectionArtifactReference
    document_completion_ref: CollectionArtifactReference
    candidate_inventory_ref: CollectionArtifactReference
    downstream_replay_ref: CollectionArtifactReference
    linked_candidate_id: str = Field(pattern=r"^exv1-[0-9a-f]{64}$")
    linked_candidate_root: str = Field(min_length=1)
    linked_identity_ref: CollectionArtifactReference
    linked_completion_ref: CollectionArtifactReference
    linked_inventory_ref: CollectionArtifactReference

    @model_validator(mode="after")
    def require_pinned_roots_and_authorities(self) -> Self:
        """Require canonical roots and exact conventional record locations."""
        candidate_root = _normalized_relative_root(self.candidate_root)
        linked_root = _normalized_relative_root(self.linked_candidate_root)
        expected = {
            "document_identity_ref": f"{candidate_root}/records/document_identity.json",
            "document_completion_ref": f"{candidate_root}/records/completion_record.json",
            "candidate_inventory_ref": f"{candidate_root}/records/artifact_inventory.json",
            "downstream_replay_ref": f"{candidate_root}/records/downstream_replay.json",
            "linked_identity_ref": f"{linked_root}/records/extraction_identity.json",
            "linked_completion_ref": f"{linked_root}/records/completion_record.json",
            "linked_inventory_ref": f"{linked_root}/records/artifact_inventory.json",
        }
        for field, path in expected.items():
            reference = getattr(self, field)
            if reference.authority != "document_input_root" or reference.path != path:
                raise ValueError(f"selected document {field} differs from its pinned root")
        if PurePosixPath(candidate_root).name != self.candidate_id:
            raise ValueError("selected document candidate root differs from candidate ID")
        if PurePosixPath(linked_root).name != self.linked_candidate_id:
            raise ValueError("selected linked root differs from linked candidate ID")
        if self.source_identity.source_id != self.physical_source_id:
            raise ValueError("selected document source identity differs from physical source")
        return self

    @property
    def selection_sha256(self) -> str:
        """Return the canonical digest that pins this exact selected candidate."""
        return canonical_sha256(self.model_dump(mode="json"))


class ImportedDocumentSelection(BaseModel):
    """One ordered, sealed set of original candidates imported document candidates."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["er_commons.imported_document_selection.v1"]
    document_input_root_relative_path: str = Field(min_length=1)
    document_production_identity_ref: CollectionArtifactReference
    document_run_spec_ref: CollectionArtifactReference
    source_count: int = Field(ge=1)
    ordered_source_ids: tuple[str, ...] = Field(min_length=1)
    candidates: tuple[SelectedDocumentCandidate, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def require_closed_order(self) -> Self:
        """Reject duplicate, out-of-order, or cross-authority selections."""
        header_refs = (self.document_production_identity_ref, self.document_run_spec_ref)
        _normalized_relative_root(self.document_input_root_relative_path)
        if any(ref.authority != "document_input_root" for ref in header_refs):
            raise ValueError("imported document controls require document_input_root authority")
        physical = tuple(item.physical_source_id for item in self.candidates)
        logical = tuple(item.logical_source_id for item in self.candidates)
        ordinals = tuple(item.source_ordinal for item in self.candidates)
        if self.source_count != len(self.candidates) or self.ordered_source_ids != physical:
            raise ValueError("imported document selection count or order differs")
        if ordinals != tuple(range(1, self.source_count + 1)):
            raise ValueError("imported document selection ordinals are not contiguous")
        if len(set(physical)) != len(physical) or len(set(logical)) != len(logical):
            raise ValueError("imported document selection repeats a source")
        if len({item.candidate_id for item in self.candidates}) != len(self.candidates):
            raise ValueError("imported document selection repeats a candidate")
        return self


def _normalized_relative_root(value: str) -> str:
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or pure == PurePosixPath(".")
        or ".." in pure.parts
        or "\\" in value
        or pure.as_posix() != value
    ):
        raise ValueError("selected document root must be normalized POSIX")
    return pure.as_posix()


__all__ = ["ImportedDocumentSelection", "SelectedDocumentCandidate"]
