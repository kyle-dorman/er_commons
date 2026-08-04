"""Provenance manifest for disposable review files rendered by an external tool."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReviewRequest:
    """Frozen requested sample; it carries no publication or acceptance authority."""

    candidate_id: str
    source_id: str
    physical_pages: tuple[int, ...]
    evidence_kinds: tuple[str, ...]

    def __post_init__(self) -> None:
        normalized_pages = tuple(sorted(set(self.physical_pages)))
        if not self.physical_pages or normalized_pages != self.physical_pages:
            raise ValueError("review pages must be non-empty, sorted, and unique")
        if not self.evidence_kinds:
            raise ValueError("at least one review evidence kind is required")


@dataclass(frozen=True)
class ReviewInput:
    """One immutable input named by artifact-relative path and checksum."""

    role: str
    path: str
    sha256: str

    def __post_init__(self) -> None:
        artifact_path = Path(self.path)
        checksum_is_hex = len(self.sha256) == 64 and all(
            character in "0123456789abcdef" for character in self.sha256
        )
        if (
            not self.role
            or not self.path
            or artifact_path.is_absolute()
            or ".." in artifact_path.parts
            or not checksum_is_hex
        ):
            raise ValueError("review input requires role, path, and SHA-256")


@dataclass(frozen=True)
class RenderRecipe:
    """Caller-supplied invocation needed to reproduce externally generated files."""

    renderer: str
    renderer_version: str
    arguments: tuple[str, ...]
    inputs: tuple[ReviewInput, ...]

    def __post_init__(self) -> None:
        if not self.renderer or not self.renderer_version or not self.arguments or not self.inputs:
            raise ValueError("render recipe requires renderer, version, arguments, and inputs")
        input_keys = [(item.role, item.path) for item in self.inputs]
        if len(input_keys) != len(set(input_keys)):
            raise ValueError("render recipe inputs must be unique")


@dataclass(frozen=True)
class GeneratedReviewFile:
    """One generated file explicitly mapped to requested page evidence."""

    path: Path
    physical_page: int
    evidence_kind: str


def write_review_manifest(
    root: Path,
    *,
    request: ReviewRequest,
    recipe: RenderRecipe,
    generated_files: tuple[GeneratedReviewFile, ...],
) -> Path:
    """Record externally rendered files without claiming to implement a renderer."""
    root.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, Any]] = []
    if not generated_files:
        raise ValueError("review manifest requires at least one generated file")
    output_paths = [item.path.resolve() for item in generated_files]
    if len(output_paths) != len(set(output_paths)):
        raise ValueError("review output files must be unique")
    for generated in sorted(generated_files, key=lambda item: item.path):
        if generated.physical_page not in request.physical_pages:
            raise ValueError("review output page was not requested")
        if generated.evidence_kind not in request.evidence_kinds:
            raise ValueError("review output evidence kind was not requested")
        resolved = generated.path.resolve()
        if not resolved.is_file() or not resolved.is_relative_to(root.resolve()):
            raise ValueError("review output must be an existing file inside the review root")
        files.append(
            {
                "path": resolved.relative_to(root.resolve()).as_posix(),
                "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
                "byte_size": resolved.stat().st_size,
                "physical_page": generated.physical_page,
                "evidence_kind": generated.evidence_kind,
            }
        )
    manifest = {
        "schema_version": "er_commons.requested_review_manifest.v1",
        "candidate_id": request.candidate_id,
        "source_id": request.source_id,
        "physical_pages": list(request.physical_pages),
        "evidence_kinds": list(request.evidence_kinds),
        "recipe": {
            "renderer": recipe.renderer,
            "renderer_version": recipe.renderer_version,
            "arguments": list(recipe.arguments),
            "inputs": [
                {"role": item.role, "path": item.path, "sha256": item.sha256}
                for item in recipe.inputs
            ],
        },
        "disposition": "disposable_outside_candidate_identity",
        "files": files,
    }
    path = root / "review_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return path
