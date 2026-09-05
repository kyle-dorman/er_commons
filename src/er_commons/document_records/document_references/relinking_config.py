"""Strict, root-aware configuration for reusable document relinking."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.artifact_io import sha256_file

OUTPUT_SCHEMA_ROLES = (
    "identity",
    "manifest",
    "inventory",
    "completion",
    "alias",
    "ordinary_reference",
    "navigation_entry",
    "navigation_relation",
    "navigation_decision",
    "navigation_link",
    "support",
)
_SOURCE_ID = re.compile(r"^[a-z][a-z0-9_]*$")


class _StrictModel(BaseModel):
    """Reject undeclared fields and mutation in identity-bearing inputs."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class RelinkArtifactRef(_StrictModel):
    """Base checksum reference resolved beneath one explicitly named authority."""

    authority: Literal["repository", "artifact_root", "bundle"]
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(gt=0)

    @model_validator(mode="after")
    def require_contained_path(self) -> RelinkArtifactRef:
        """Reject absolute and parent-traversing references before resolution."""
        path = Path(self.path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("relink artifact paths must be contained and relative")
        return self

    def resolve(
        self, *, repository_root: Path, artifact_root: Path, bundle_root: Path | None = None
    ) -> Path:
        """Resolve and verify this reference under its declared authority."""
        roots = {"repository": repository_root, "artifact_root": artifact_root}
        if self.authority == "bundle":
            if bundle_root is None:
                raise ValueError("bundle-relative reference requires a verified bundle root")
            root = bundle_root
        else:
            root = roots[self.authority]
        resolved_root = root.resolve()
        path = (resolved_root / self.path).resolve()
        if not path.is_relative_to(resolved_root):
            raise ValueError(f"relink artifact escapes {self.authority}: {self.path}")
        if not path.is_file():
            raise ValueError(f"relink artifact is absent from {self.authority}: {self.path}")
        if path.stat().st_size != self.byte_size:
            raise ValueError(f"relink artifact seal differs (byte size): {self.path}")
        if sha256_file(path) != self.sha256:
            raise ValueError(f"relink artifact seal differs (SHA-256): {self.path}")
        return path


class ExternalArtifactRef(RelinkArtifactRef):
    """Identity-bearing input owned by the repository or artifact root."""

    authority: Literal["repository", "artifact_root"]


class BundleArtifactRef(RelinkArtifactRef):
    """Payload owned by, and resolved relative to, a reviewed bundle."""

    authority: Literal["bundle"]


class _BaseCollection(_StrictModel):
    handoff_ref: ExternalArtifactRef
    contract_bundle_ref: ExternalArtifactRef


class _SealedDocument(_StrictModel):
    candidate_id: str = Field(pattern=r"^docv1-[0-9a-f]{64}$")
    completion_ref: ExternalArtifactRef
    inventory_ref: ExternalArtifactRef


class _SealedStructuredDocument(_StrictModel):
    candidate_id: str = Field(pattern=r"^exv1-[0-9a-f]{64}$")
    completion_ref: ExternalArtifactRef
    inventory_ref: ExternalArtifactRef


class RelinkDocumentSelection(_StrictModel):
    """One source and the two sealed products used at the replay boundary."""

    source_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    source_document: _SealedDocument
    structured_document: _SealedStructuredDocument


class ReviewedNavigationSelection(_StrictModel):
    """One verified generic reviewed-navigation bundle selection."""

    bundle_id: str = Field(pattern=r"^navreviewv1-[0-9a-f]{64}$")
    bundle_ref: ExternalArtifactRef
    schema_ref: ExternalArtifactRef
    source_ids: tuple[str, ...] = Field(min_length=1)
    identity_ref: ExternalArtifactRef
    completion_ref: ExternalArtifactRef
    inventory_ref: ExternalArtifactRef
    review_decisions_ref: ExternalArtifactRef
    semantic_view_ref: ExternalArtifactRef
    disposition_ref: BundleArtifactRef
    text_entries_ref: BundleArtifactRef
    parent_relations_ref: BundleArtifactRef

    @model_validator(mode="after")
    def require_unique_sources_and_bundle_payloads(self) -> ReviewedNavigationSelection:
        """Keep reviewed coverage unique and owned payloads bundle-relative."""
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("reviewed navigation repeats source IDs")
        invalid = [
            source_id for source_id in self.source_ids if _SOURCE_ID.fullmatch(source_id) is None
        ]
        if invalid:
            raise ValueError(f"reviewed navigation has invalid source ID: {invalid[0]}")
        return self


class OutputSchemaRefs(_StrictModel):
    """Named schema owners for every linked-document output role."""

    identity: ExternalArtifactRef
    manifest: ExternalArtifactRef
    inventory: ExternalArtifactRef
    completion: ExternalArtifactRef
    alias: ExternalArtifactRef
    ordinary_reference: ExternalArtifactRef
    navigation_entry: ExternalArtifactRef
    navigation_relation: ExternalArtifactRef
    navigation_decision: ExternalArtifactRef
    navigation_link: ExternalArtifactRef
    support: ExternalArtifactRef


class DocumentLinkRunSpec(_StrictModel):
    """Closed source set and all identity-bearing relink inputs."""

    schema_version: Literal["er_commons.document_link_run_spec.v1"]
    artifact_relative_root: str = Field(min_length=1)
    base_collection: _BaseCollection
    base_production_identity_ref: ExternalArtifactRef
    replacement_production_identity_recipe_ref: ExternalArtifactRef
    document_publication_spec_ref: ExternalArtifactRef
    collection_run_spec_ref: ExternalArtifactRef
    linking_policy_ref: ExternalArtifactRef
    linking_policy_schema_ref: ExternalArtifactRef
    source_family_catalog_ref: ExternalArtifactRef
    selected_source_ids: tuple[str, ...] = Field(min_length=1)
    documents: tuple[RelinkDocumentSelection, ...] = Field(min_length=1)
    reviewed_navigation: ReviewedNavigationSelection | None
    output_schema_refs: OutputSchemaRefs

    @model_validator(mode="after")
    def require_closed_source_scope(self) -> DocumentLinkRunSpec:
        """Make selected IDs, document rows, and reviewed coverage agree exactly."""
        output = Path(self.artifact_relative_root)
        if output.is_absolute() or ".." in output.parts:
            raise ValueError("relink artifact root must be contained and relative")
        source_ids = tuple(document.source_id for document in self.documents)
        if source_ids != self.selected_source_ids or len(source_ids) != len(set(source_ids)):
            raise ValueError("selected_source_ids must equal unique ordered document source IDs")
        invalid = [
            source_id
            for source_id in self.selected_source_ids
            if _SOURCE_ID.fullmatch(source_id) is None
        ]
        if invalid:
            raise ValueError(f"selected_source_ids contains invalid source ID: {invalid[0]}")
        reviewed = self.reviewed_navigation
        if reviewed is not None and not set(reviewed.source_ids).issubset(source_ids):
            raise ValueError("reviewed navigation coverage escapes selected sources")
        return self

    def document(self, source_id: str) -> RelinkDocumentSelection:
        """Return the sole selected row for an explicit source ID."""
        matches = [document for document in self.documents if document.source_id == source_id]
        if len(matches) != 1:
            raise ValueError(f"link run does not select exactly one source: {source_id}")
        return matches[0]


def load_document_link_run_spec(path: Path) -> tuple[DocumentLinkRunSpec, str]:
    """Load a strict relink run specification and return its byte digest."""
    raw = path.read_bytes()
    return DocumentLinkRunSpec.model_validate_json(raw), hashlib.sha256(raw).hexdigest()


__all__ = [
    "BundleArtifactRef",
    "DocumentLinkRunSpec",
    "ExternalArtifactRef",
    "OutputSchemaRefs",
    "OUTPUT_SCHEMA_ROLES",
    "RelinkArtifactRef",
    "RelinkDocumentSelection",
    "ReviewedNavigationSelection",
    "load_document_link_run_spec",
]
