"""Relocatable path and checksum contract for projected table-stage evidence."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from er_commons.artifact_io import read_json_object, read_jsonl, sha256_file
from er_commons.document_parsing.content_parsing.records import TableStageObservation
from er_commons.document_parsing.table_reconstruction.pipeline import (
    artifact_inventory as table_artifact_inventory,
)

NO_TABLE_HANDOFF_FILES = (
    "summary.json",
    "pages.jsonl",
    "tables.jsonl",
    "family_assignments.jsonl",
    "table_families.json",
    "manifest.json",
)


class ReferenceRecord(BaseModel):
    """Strict immutable record used by the table-stage reference boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class TableArtifactSeal(ReferenceRecord):
    """Checksum for one required file in a relocatable table-stage handoff."""

    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class TableStageReference(ReferenceRecord):
    """Relocatable, completion-bound reference to one contained table stage."""

    relative_path: str = Field(min_length=1)
    completion_marker: Literal["manifest.json", "no_table_stage.json"]
    completion_marker_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_inventory_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    no_table_handoff: tuple[TableArtifactSeal, ...] = ()

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        """Require a normalized POSIX path contained by its runtime owner."""
        path = PurePosixPath(value)
        if path.is_absolute() or value != path.as_posix() or ".." in path.parts:
            raise ValueError("table stage path must be a normalized contained relative path")
        if value in {"", "."}:
            raise ValueError("table stage path must name a child of its runtime owner")
        return value

    @field_validator("no_table_handoff", mode="before")
    @classmethod
    def accept_handoff_array(cls, value: Any) -> Any:
        """Normalize persisted handoff arrays into immutable evidence."""
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_evidence_shape(self) -> TableStageReference:
        """Require the evidence appropriate to the claimed completion marker."""
        has_inventory = self.artifact_inventory_sha256 is not None
        if (self.completion_marker == "manifest.json") != has_inventory:
            raise ValueError("manifest table references require artifact inventory evidence")
        paths = tuple(item.path for item in self.no_table_handoff)
        if self.completion_marker == "no_table_stage.json":
            if paths != NO_TABLE_HANDOFF_FILES:
                raise ValueError("no-table references require the complete handoff inventory")
        elif paths:
            raise ValueError("completed table references cannot carry no-table evidence")
        return self

    def resolve(self, runtime_root: Path) -> Path:
        """Resolve this reference beneath an explicit absolute runtime owner."""
        if not runtime_root.is_absolute():
            raise ValueError("table stage runtime root must be absolute")
        owner = runtime_root.resolve()
        resolved = (owner / self.relative_path).resolve()
        try:
            resolved.relative_to(owner)
        except ValueError as error:
            raise ValueError("table stage path escapes its runtime owner") from error
        return resolved

    def relocated(self, relative_path: str) -> TableStageReference:
        """Rebind identical sealed bytes under a new publication owner."""
        return TableStageReference.model_validate(
            {**self.model_dump(mode="python"), "relative_path": relative_path}
        )


def capture_table_stage_reference(
    runtime_root: Path,
    table_root: Path,
    observation: TableStageObservation,
) -> TableStageReference:
    """Capture contained completion evidence without persisting a machine path."""
    if not runtime_root.is_absolute() or not table_root.is_absolute():
        raise ValueError("table stage capture paths must be absolute")
    owner = runtime_root.resolve()
    resolved = table_root.resolve()
    try:
        relative = resolved.relative_to(owner).as_posix()
    except ValueError as error:
        raise ValueError("table stage must be contained by its runtime owner") from error
    marker: Literal["manifest.json", "no_table_stage.json"] = (
        "no_table_stage.json" if observation.status == "not_applicable" else "manifest.json"
    )
    inventory_sha256 = None
    no_table_handoff: tuple[TableArtifactSeal, ...] = ()
    if marker == "manifest.json":
        manifest = read_json_object(resolved / marker)
        inventory_path = _contained_table_file(resolved, manifest.get("artifact_inventory"))
        inventory_sha256 = sha256_file(inventory_path)
    else:
        no_table_handoff = _capture_no_table_handoff(resolved)
    return TableStageReference(
        relative_path=relative,
        completion_marker=marker,
        completion_marker_sha256=sha256_file(resolved / marker),
        artifact_inventory_sha256=inventory_sha256,
        no_table_handoff=no_table_handoff,
    )


def _capture_no_table_handoff(table_root: Path) -> tuple[TableArtifactSeal, ...]:
    """Bind every required no-table file with a path-aware missing-file error."""
    missing = [name for name in NO_TABLE_HANDOFF_FILES if not (table_root / name).is_file()]
    if missing:
        raise ValueError(f"no-table handoff artifacts are missing: {missing!r}")
    return tuple(
        TableArtifactSeal(path=name, sha256=sha256_file(table_root / name))
        for name in NO_TABLE_HANDOFF_FILES
    )


def verify_table_stage_reference(reference: TableStageReference, runtime_root: Path) -> Path:
    """Resolve and verify the referenced completion marker and table inventory."""
    table_root = reference.resolve(runtime_root)
    if not table_root.is_dir():
        raise ValueError("referenced table stage directory is missing")
    marker_path = table_root / reference.completion_marker
    if sha256_file(marker_path) != reference.completion_marker_sha256:
        raise ValueError("referenced table stage completion marker differs")
    if reference.completion_marker == "manifest.json":
        _verify_referenced_inventory(table_root, reference)
    else:
        _verify_no_table_handoff(table_root, reference)
    return table_root


def _verify_referenced_inventory(table_root: Path, reference: TableStageReference) -> None:
    """Verify both the inventory record and every file it seals."""
    manifest = read_json_object(table_root / "manifest.json")
    inventory_path = _contained_table_file(table_root, manifest.get("artifact_inventory"))
    if sha256_file(inventory_path) != reference.artifact_inventory_sha256:
        raise ValueError("referenced table-stage inventory seal differs")
    expected = read_json_object(inventory_path)
    actual = table_artifact_inventory(
        table_root,
        {"artifact_inventory.json", "manifest.json"},
    )
    if actual != expected:
        raise ValueError("referenced table-stage artifact inventory differs")


def _verify_no_table_handoff(table_root: Path, reference: TableStageReference) -> None:
    """Verify every required empty artifact and its producer-side semantics."""
    for artifact in reference.no_table_handoff:
        path = _contained_table_file(table_root, artifact.path)
        if sha256_file(path) != artifact.sha256:
            raise ValueError(f"no-table handoff artifact differs: {artifact.path}")
    for name in ("pages.jsonl", "tables.jsonl", "family_assignments.jsonl"):
        if read_jsonl(table_root / name):
            raise ValueError(f"no-table handoff is not empty: {name}")
    if read_json_object(table_root / "table_families.json") != {
        "families": [],
        "continuation_decisions": [],
    }:
        raise ValueError("no-table family handoff is not empty")
    _verify_no_table_summary(read_json_object(table_root / "summary.json"))
    _verify_no_table_manifest(read_json_object(table_root / "manifest.json"))


def _verify_no_table_summary(summary: Mapping[str, object]) -> None:
    """Require the exact producer-owned empty summary contract."""
    expected = {
        "physical_pdf_pages": [],
        "page_count": 0,
        "logical_table_count": 0,
        "family_count": 0,
        "zero_table_pages": [],
        "review_derivatives_retained": False,
    }
    if summary != expected:
        raise ValueError("no-table summary handoff differs")


def _verify_no_table_manifest(manifest: Mapping[str, object]) -> None:
    """Require the complete producer-owned empty manifest contract."""
    expected = {
        "schema_version": "1.0.0",
        "physical_pdf_pages": [],
        "summary": "summary.json",
        "pages": "pages.jsonl",
        "tables": "tables.jsonl",
        "family_assignments": "family_assignments.jsonl",
        "table_families": "table_families.json",
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("no-table manifest handoff differs")
    if not isinstance(manifest.get("source_id"), str) or not manifest["source_id"]:
        raise ValueError("no-table manifest source identity is missing")


def _contained_table_file(table_root: Path, value: object) -> Path:
    """Resolve one manifest-owned file without permitting path traversal."""
    if not isinstance(value, str) or not value:
        raise ValueError("table-stage manifest path is missing")
    candidate = (table_root / value).resolve()
    try:
        candidate.relative_to(table_root.resolve())
    except ValueError as error:
        raise ValueError("table-stage manifest path escapes its root") from error
    return candidate


__all__ = [
    "TableArtifactSeal",
    "TableStageReference",
    "capture_table_stage_reference",
    "verify_table_stage_reference",
]
