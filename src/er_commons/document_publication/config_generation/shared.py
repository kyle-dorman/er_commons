"""Explicit generation request and deterministic record operations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.artifact_io import assert_contained
from er_commons.document_publication.config import ResourcePolicy

ZERO_SHA256 = "0" * 64
ZERO_EXV1 = f"exv1-{ZERO_SHA256}"
ZERO_PRV1 = f"prv1-{ZERO_SHA256}"
ZERO_HCORV1 = f"hcorv1-{ZERO_SHA256}"


class SourceBinding(BaseModel):
    """One ordered physical source and its original sealed manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    source_id: str
    source_release_version: str
    source_manifest_relative_path: Path
    expected_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reference_aliases: tuple[str, ...] = Field(min_length=1)
    logical_source_id: str | None = None
    substitution_relative_path: Path | None = None

    @property
    def source_manifest_path(self) -> Path:
        """Provide the shared sealed-manifest reader protocol."""
        return self.source_manifest_relative_path


class GenerationSpec(BaseModel):
    """All variable generation choices; no hidden corpus/version defaults."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["er_commons.document_config_generation.v1"]
    repository_root: Path
    data_root: Path
    templates: dict[str, Path]
    sources: tuple[SourceBinding, ...] = Field(min_length=1)
    baseline_manifest_relative_path: Path
    baseline_release_version: str
    config_root: Path
    run_root: Path
    catalog_output: Path
    catalog_data_relative_path: Path
    document_spec_output: Path
    collection_spec_output: Path
    identity_output: Path
    model_inventory_relative_path: Path
    target_policy: Path
    resolution_policy: Path
    resource_policy: ResourcePolicy
    chunked_page_threshold: Literal[300]  # Current accepted runtime selection policy.
    chunked_policy: dict[str, Any]
    name_prefix: str
    source_family_id: str
    family_root_source_id: str
    document_code: tuple[Path, ...] = Field(min_length=1)
    collection_code: tuple[Path, ...] = Field(min_length=1)
    document_contracts: tuple[Path, ...]
    collection_contracts: tuple[Path, ...]

    @model_validator(mode="after")
    def validate_scope_and_paths(self) -> GenerationSpec:
        """Reject ambiguous selection, unsafe output paths and incomplete templates."""
        roles = {
            "content_parsing",
            "heading_evidence_parsing",
            "record_mapping",
            "hierarchy_inference",
            "document_structure",
            "document_reference_linking",
        }
        if set(self.templates) != roles:
            raise ValueError("generation templates must name all six process roles")
        ids = [source.source_id for source in self.sources]
        if len(ids) != len(set(ids)) or self.family_root_source_id not in ids:
            raise ValueError("generation source selection is duplicate or lacks its family root")
        paths = [
            self.config_root,
            self.run_root,
            self.catalog_output,
            self.catalog_data_relative_path,
            self.document_spec_output,
            self.collection_spec_output,
            self.identity_output,
            self.model_inventory_relative_path,
            self.baseline_manifest_relative_path,
            self.target_policy,
            self.resolution_policy,
            *self.templates.values(),
            *self.document_code,
            *self.collection_code,
            *self.document_contracts,
            *self.collection_contracts,
            *(source.source_manifest_path for source in self.sources),
        ]
        if any(path.is_absolute() or ".." in path.parts for path in paths):
            raise ValueError("generation paths must be contained relative paths")
        if self.catalog_output.name != self.catalog_data_relative_path.name:
            raise ValueError("catalog output and staging path must retain the same filename")
        if self.document_spec_output.parent != self.collection_spec_output.parent:
            raise ValueError("generated document and collection specs must share a directory")
        outputs = [
            self.catalog_output,
            self.document_spec_output,
            self.collection_spec_output,
            self.identity_output,
        ]
        if len(outputs) != len(set(outputs)):
            raise ValueError("generation outputs must be distinct")
        return self

    def project_path(self, relative: Path) -> Path:
        """Resolve one generation input/output within the declared repository."""
        return assert_contained(self.repository_root, relative.as_posix())

    def chunked_policy_paths(self, sources: list[dict[str, Any]]) -> tuple[Path, ...]:
        """Select policy outputs using the declared threshold only."""
        return tuple(
            self.project_path(self.config_root / source["source_id"] / "chunked_conversion.json")
            for source in sources
            if source["pdf_page_count"] > self.chunked_page_threshold
        )


def load_generation_spec(path: Path) -> GenerationSpec:
    """Resolve request roots relative to its own file rather than environment state."""
    value = load_object(path)
    for key in ("repository_root", "data_root"):
        value[key] = (path.resolve().parent / value[key]).resolve()
    return GenerationSpec.model_validate(value)


def json_bytes(value: dict[str, Any]) -> bytes:
    """Preserve established deterministic generated JSON formatting."""
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def json_sha256(value: dict[str, Any]) -> str:
    """Hash proposed new output bytes, never historical payloads."""
    return hashlib.sha256(json_bytes(value)).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    """Load one required JSON object."""
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write_or_check(values: dict[Path, dict[str, Any]], *, check: bool) -> None:
    """Check proposed bytes or publish new files without replacing other artifacts."""
    encoded = {path: json_bytes(value) for path, value in values.items()}
    differing = [
        str(path) for path, raw in encoded.items() if path.exists() and path.read_bytes() != raw
    ]
    missing = [str(path) for path in encoded if not path.exists()]
    if differing or (check and missing):
        raise ValueError("generated current outputs differ: " + ", ".join(differing + missing))
    if not check:
        for path, raw in encoded.items():
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    stream.write(raw)
