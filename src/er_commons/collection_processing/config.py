"""Strict v2 configuration for collection handoff assembly."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.authority_reference import AuthorityReference
from er_commons.collection_processing.authority_refs import CollectionArtifactReference


class CollectionSourceMembership(BaseModel):
    """Map one original logical slot to an explicitly selected physical source."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    logical_source_id: str
    physical_source_id: str
    substitution_relative_path: Path | None = None

    @model_validator(mode="after")
    def validate_substitution(self) -> CollectionSourceMembership:
        """Permit only the declared F1 exception with explicit substitution evidence."""
        changed = self.logical_source_id != self.physical_source_id
        if changed and (
            self.logical_source_id != "deir_appendix_f1" or self.substitution_relative_path is None
        ):
            raise ValueError("only F1 may replace a physical source with substitution evidence")
        if not changed and self.substitution_relative_path is not None:
            raise ValueError("unchanged source cannot declare a substitution")
        path = self.substitution_relative_path
        if path is not None and (path.is_absolute() or ".." in path.parts):
            raise ValueError("substitution path must be contained")
        return self


class CollectionRunSpec(BaseModel):
    """One explicit manifest-ordered collection and its output policies."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[
        "er_commons.collection_run_spec.v2",
        "er_commons.collection_run_spec.v3",
        "er_commons.collection_run_spec.v4",
    ]
    source_membership: tuple[CollectionSourceMembership, ...] = Field(
        default=(), exclude_if=lambda value: not value
    )
    document_run_spec: Path | None = Field(default=None, exclude_if=lambda value: value is None)
    source_ids: tuple[str, ...] = Field(min_length=1)
    source_family_catalog_relative_path: Path
    blocking_policy: Literal["all_sources_successful", "terminal_failures_allowed"]
    document_evidence_mode: Literal[
        "document_attempt", "downstream_replay_only", "imported_downstream_selection"
    ] = "document_attempt"
    target_policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    resolution_policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    ordering_policy_version: Literal["record_target_order_v2"] = "record_target_order_v2"
    collection_output_relative_root: Path | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    collection_production_id: str | None = Field(
        default=None,
        pattern=r"^cprodv1-[0-9a-f]{64}$",
        exclude_if=lambda value: value is None,
    )
    collection_production_identity_ref: AuthorityReference | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    imported_document_root_relative_path: Path | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    imported_selection_ref: AuthorityReference | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    imported_document_run_spec_ref: CollectionArtifactReference | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    imported_document_production_identity_ref: CollectionArtifactReference | None = Field(
        default=None, exclude_if=lambda value: value is None
    )

    @model_validator(mode="after")
    def validate_paths_and_sources(self) -> CollectionRunSpec:
        """Require contained paths and a unique declared source sequence."""
        paths = [self.source_family_catalog_relative_path]
        if self.document_run_spec is not None:
            paths.append(self.document_run_spec)
        for path in paths:
            if path.is_absolute() or ".." in path.parts or path == Path("."):
                raise ValueError("collection run paths must be contained relative paths")
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("collection source IDs must be unique")
        if self.schema_version.endswith(".v2") and self.source_membership:
            raise ValueError("explicit source membership requires collection v3")
        if self.schema_version.endswith((".v3", ".v4")):
            logical = [item.logical_source_id for item in self.source_membership]
            physical = [item.physical_source_id for item in self.source_membership]
            if len(logical) != len(set(logical)) or physical != list(self.source_ids):
                raise ValueError("source membership must cover each physical and logical slot once")
        imported_fields = (
            self.collection_output_relative_root,
            self.collection_production_id,
            self.collection_production_identity_ref,
            self.imported_document_root_relative_path,
            self.imported_selection_ref,
            self.imported_document_run_spec_ref,
            self.imported_document_production_identity_ref,
        )
        if self.schema_version.endswith(".v4"):
            if self.document_run_spec is not None or any(
                value is None for value in imported_fields
            ):
                raise ValueError("collection v4 requires only its imported-selection controls")
            if self.document_evidence_mode != "imported_downstream_selection":
                raise ValueError("collection v4 requires imported downstream selection mode")
            if not self.source_membership:
                raise ValueError("collection v4 requires explicit source membership")
            output = self.collection_output_relative_root
            imported = self.imported_document_root_relative_path
            assert output is not None and imported is not None
            for path in (output, imported):
                if path.is_absolute() or ".." in path.parts or path == Path("."):
                    raise ValueError("collection v4 roots must be contained relative paths")
            if (
                output == imported
                or output.is_relative_to(imported)
                or imported.is_relative_to(output)
            ):
                raise ValueError("collection v4 document and output roots must be distinct")
            generic_refs = (
                self.collection_production_identity_ref,
                self.imported_selection_ref,
            )
            if any(ref is None or ref.authority != "artifact_root" for ref in generic_refs):
                raise ValueError("collection v4 resolved controls require artifact-root authority")
            document_refs = (
                self.imported_document_run_spec_ref,
                self.imported_document_production_identity_ref,
            )
            if any(ref is None or ref.authority != "document_input_root" for ref in document_refs):
                raise ValueError("collection v4 imported controls require document-input authority")
        elif self.document_run_spec is None or any(value is not None for value in imported_fields):
            raise ValueError("historical collection specs cannot add imported-selection controls")
        elif self.document_evidence_mode == "imported_downstream_selection":
            raise ValueError("historical collection specs cannot import a frozen selection")
        return self


def load_collection_run_spec(path: Path) -> tuple[CollectionRunSpec, str]:
    """Load a strict v2 collection specification and its exact checksum."""
    raw = path.read_bytes()
    return CollectionRunSpec.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
