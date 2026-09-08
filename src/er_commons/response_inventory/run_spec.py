"""Portable, source-free run specification for the Task 05C pilot."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.response_inventory.code_inventory import owned_code_digest
from er_commons.response_inventory.pilot_policy import TASK05C_PILOT_RANGES


class StrictModel(BaseModel):
    """Reject undeclared fields and mutation after validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class PageRange(StrictModel):
    """One inclusive physical-page range and operational restart unit."""

    range_id: str = Field(pattern=r"^p[0-9]{4}-p[0-9]{4}$")
    first_page: int = Field(ge=1)
    last_page: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_bounds(self) -> PageRange:
        """Require a forward range whose label agrees with its bounds."""
        if self.last_page < self.first_page:
            raise ValueError("page range must end at or after its first page")
        expected = f"p{self.first_page:04d}-p{self.last_page:04d}"
        if self.range_id != expected:
            raise ValueError(f"page range ID must be {expected}")
        return self

    @property
    def page_count(self) -> int:
        """Return the inclusive number of pages in the range."""
        return self.last_page - self.first_page + 1


class ArtifactReference(StrictModel):
    """Compact accepted-artifact binding without copying its payload."""

    role: Literal["task05a_completion", "source_release_completion", "source_manifest"]
    authority: Literal["artifact_root"]
    path: Path
    byte_size: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_path(self) -> ArtifactReference:
        """Keep artifact references relative to the configured data root."""
        _require_contained_path(self.path, "artifact reference")
        return self


class RepositoryBinding(StrictModel):
    """Digest-bound checked-in schema or producer module."""

    role: Literal["response_record_schema", "producer_run_spec_code"]
    authority: Literal["repository"]
    path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_path(self) -> RepositoryBinding:
        """Keep repository bindings portable and contained."""
        _require_contained_path(self.path, "repository binding")
        return self


class SourceBinding(StrictModel):
    """Frozen source facts that preflight can verify without opening the PDF."""

    source_id: Literal["feir_volume_4"]
    source_role: Literal["curator_only_response_source"]
    source_release_version: Literal["brisbane_baylands_2025_deir_sources_v1"]
    path: Path
    recorded_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    recorded_byte_size: int = Field(gt=0)
    recorded_page_count: int = Field(gt=0)
    retrieval_status: Literal["downloaded"]
    validation_status: Literal["valid"]
    member_of_model_corpus: Literal[False]

    @model_validator(mode="after")
    def validate_path(self) -> SourceBinding:
        """Require an artifact-root-relative PDF path without reading it."""
        _require_contained_path(self.path, "source")
        if self.path.suffix.lower() != ".pdf":
            raise ValueError("response source path must name a PDF")
        return self


class OutputPolicy(StrictModel):
    """Contained, activity-derived pilot publication namespace."""

    artifact_relative_root: Path
    pilot_namespace_template: Literal["pilots/pilotv1-{activity_hash}"]
    completion_written_last: Literal[True]
    copy_source_payload: Literal[False]
    copy_upstream_payloads: Literal[False]

    @model_validator(mode="after")
    def validate_path(self) -> OutputPolicy:
        """Keep Task 05 outputs below a portable artifact-root path."""
        _require_contained_path(self.artifact_relative_root, "output")
        return self


class CachePolicy(StrictModel):
    """Replaceable cache boundary for selected-page diagnostics."""

    relative_path_template: Path
    replaceable: Literal[True]
    selected_pages_only: Literal[True]
    retain_range_receipts: Literal[True]

    @model_validator(mode="after")
    def validate_path(self) -> CachePolicy:
        """Keep cache paths below the artifact root."""
        _require_contained_path(self.relative_path_template, "cache")
        return self


class StopBehavior(StrictModel):
    """Material failures that stop rather than silently broaden the pilot."""

    on_source_binding_mismatch: Literal["stop"]
    on_invalid_anchor_or_schema: Literal["stop"]
    on_unclassified_page: Literal["stop"]
    on_new_structural_regime: Literal["stop"]
    on_nondeterministic_semantic_output: Literal["stop"]
    on_unsafe_restart_state: Literal["stop"]
    allow_additional_pages: Literal[False]
    allow_policy_repair_during_run: Literal[False]
    allowed_terminal_warning_codes: tuple[Literal["unit_boundary_ambiguous"], ...]


class ResponseInventoryRunSpec(StrictModel):
    """One explicit and bounded Task 05C pilot recipe."""

    schema_version: Literal["er_commons.response_inventory_run_spec.v1"]
    task_stage: Literal["05c"]
    scope_kind: Literal["representative_pilot"]
    source: SourceBinding
    accepted_inputs: tuple[ArtifactReference, ...]
    repository_bindings: tuple[RepositoryBinding, ...]
    producer_code_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_ranges: tuple[PageRange, ...]
    declared_page_count: int = Field(gt=0)
    restart_unit: Literal["declared_page_range"]
    cross_gap_continuations_allowed: Literal[False]
    output_policy: OutputPolicy
    cache_policy: CachePolicy
    stop_behavior: StopBehavior

    @model_validator(mode="after")
    def validate_closed_selection_and_roles(self) -> ResponseInventoryRunSpec:
        """Close range accounting and require one binding for every owned role."""
        if not self.page_ranges:
            raise ValueError("run spec must declare at least one page range")
        previous_last = 0
        for page_range in self.page_ranges:
            if page_range.first_page <= previous_last:
                raise ValueError("page ranges must be ordered and non-overlapping")
            if page_range.last_page > self.source.recorded_page_count:
                raise ValueError("page range exceeds the recorded source page count")
            previous_last = page_range.last_page
        actual_page_count = sum(item.page_count for item in self.page_ranges)
        if self.declared_page_count != actual_page_count:
            raise ValueError(
                "declared page count differs from inclusive ranges: "
                f"declared={self.declared_page_count}, ranges={actual_page_count}"
            )
        observed_ranges = tuple((item.first_page, item.last_page) for item in self.page_ranges)
        if observed_ranges != TASK05C_PILOT_RANGES:
            raise ValueError("05C run spec differs from the exact authorized pilot ranges")
        _require_exact_roles(
            [item.role for item in self.accepted_inputs],
            {"task05a_completion", "source_release_completion", "source_manifest"},
            "accepted input",
        )
        _require_exact_roles(
            [item.role for item in self.repository_bindings],
            {"response_record_schema", "producer_run_spec_code"},
            "repository binding",
        )
        if self.stop_behavior.allowed_terminal_warning_codes != ("unit_boundary_ambiguous",):
            raise ValueError("05C allows only its declared right-censored boundary warning")
        return self


def load_response_inventory_run_spec(path: Path) -> tuple[ResponseInventoryRunSpec, str]:
    """Load one strict run spec and return the digest used by its activity."""
    raw = path.read_bytes()
    return ResponseInventoryRunSpec.model_validate_json(raw), hashlib.sha256(raw).hexdigest()


def verify_repository_bindings(spec: ResponseInventoryRunSpec, repository_root: Path) -> None:
    """Verify small checked-in dependencies without touching source artifacts."""
    root = repository_root.resolve()
    for binding in spec.repository_bindings:
        path = (root / binding.path).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"repository binding is missing or escapes the repository: {path}")
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if observed != binding.sha256:
            raise ValueError(f"repository binding digest mismatch: {binding.role}")
    if owned_code_digest(root) != spec.producer_code_sha256:
        raise ValueError("producer code digest mismatch")


def _require_contained_path(path: Path, label: str) -> None:
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        raise ValueError(f"{label} path must be a contained relative path")


def _require_exact_roles(actual: list[str], expected: set[str], label: str) -> None:
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError(f"{label} roles must be exactly {sorted(expected)}")


__all__ = [
    "ResponseInventoryRunSpec",
    "load_response_inventory_run_spec",
    "verify_repository_bindings",
]
