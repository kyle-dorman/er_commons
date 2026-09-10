"""Strict v2 configuration for collection handoff assembly."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
        "er_commons.collection_run_spec.v2", "er_commons.collection_run_spec.v3"
    ]
    source_membership: tuple[CollectionSourceMembership, ...] = Field(
        default=(), exclude_if=lambda value: not value
    )
    document_run_spec: Path
    source_ids: tuple[str, ...] = Field(min_length=1)
    source_family_catalog_relative_path: Path
    blocking_policy: Literal["all_sources_successful", "terminal_failures_allowed"]
    document_evidence_mode: Literal["document_attempt", "downstream_replay_only"] = (
        "document_attempt"
    )
    target_policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    resolution_policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    ordering_policy_version: Literal["record_target_order_v2"] = "record_target_order_v2"

    @model_validator(mode="after")
    def validate_paths_and_sources(self) -> CollectionRunSpec:
        """Require contained paths and a unique declared source sequence."""
        for path in (self.document_run_spec, self.source_family_catalog_relative_path):
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("collection run paths must be contained relative paths")
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("collection source IDs must be unique")
        if self.schema_version.endswith(".v2") and self.source_membership:
            raise ValueError("explicit source membership requires collection v3")
        if self.schema_version.endswith(".v3"):
            logical = [item.logical_source_id for item in self.source_membership]
            physical = [item.physical_source_id for item in self.source_membership]
            if len(logical) != len(set(logical)) or physical != list(self.source_ids):
                raise ValueError("source membership must cover each physical and logical slot once")
        return self


def load_collection_run_spec(path: Path) -> tuple[CollectionRunSpec, str]:
    """Load a strict v2 collection specification and its exact checksum."""
    raw = path.read_bytes()
    return CollectionRunSpec.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
