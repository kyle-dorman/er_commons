"""Strict stage-two configuration outside the immutable document run spec."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScopeRunSpec(BaseModel):
    """One explicit manifest-ordered stage-two scope and its output policies."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["er_commons.scope_run_spec.v1"]
    document_run_spec: Path
    source_ids: tuple[str, ...] = Field(min_length=1)
    corpus_catalog_relative_path: Path
    blocking_policy: Literal["all_sources_successful", "terminal_failures_allowed"]
    document_evidence_mode: Literal["document_attempt", "downstream_replay_only"] = (
        "document_attempt"
    )
    target_policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    resolution_policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    ordering_policy_version: Literal["corpus_target_order_v1"] = "corpus_target_order_v1"

    @model_validator(mode="after")
    def validate_paths_and_sources(self) -> ScopeRunSpec:
        """Require contained paths and a unique declared source sequence."""
        for path in (self.document_run_spec, self.corpus_catalog_relative_path):
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("scope run paths must be contained relative paths")
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("scope source IDs must be unique")
        return self


def load_scope_run_spec(path: Path) -> tuple[ScopeRunSpec, str]:
    """Load a scope specification and return its exact checksum."""
    raw = path.read_bytes()
    return ScopeRunSpec.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
