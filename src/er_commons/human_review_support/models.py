"""Validated models shared by requested and generated human-review artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReviewSelection:
    """One source-qualified page sample from an immutable document candidate."""

    candidate_id: str
    source_id: str
    physical_pages: tuple[int, ...]
    evidence_kinds: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.candidate_id or not self.source_id:
            raise ValueError("review selection requires candidate and source IDs")
        if (
            not self.physical_pages
            or self.physical_pages != tuple(sorted(set(self.physical_pages)))
            or any(page < 1 for page in self.physical_pages)
        ):
            raise ValueError("review pages must be positive, non-empty, sorted, and unique")
        if not self.evidence_kinds or self.evidence_kinds != tuple(
            sorted(set(self.evidence_kinds))
        ):
            raise ValueError("review evidence kinds must be non-empty, sorted, and unique")


@dataclass(frozen=True)
class ReviewArtifactInput:
    """One immutable render input named by artifact-relative path and checksum."""

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
    inputs: tuple[ReviewArtifactInput, ...]

    def __post_init__(self) -> None:
        if not self.renderer or not self.renderer_version or not self.arguments or not self.inputs:
            raise ValueError("render recipe requires renderer, version, arguments, and inputs")
        input_keys = [(item.role, item.path) for item in self.inputs]
        if len(input_keys) != len(set(input_keys)):
            raise ValueError("render recipe inputs must be unique")


@dataclass(frozen=True)
class RenderPlan:
    """A grouped evidence sample that grants no render or publication authority."""

    scope_id: str
    selections: tuple[ReviewSelection, ...]

    def __post_init__(self) -> None:
        if not self.scope_id or not self.selections:
            raise ValueError("render plan requires a scope and selections")
        keys = [(item.source_id, item.candidate_id) for item in self.selections]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("review selections must be sorted and unique by source and candidate")


@dataclass(frozen=True)
class GeneratedReviewOutput:
    """One generated file explicitly mapped to selected page evidence."""

    path: Path
    physical_page: int
    evidence_kind: str

    def __post_init__(self) -> None:
        if self.physical_page < 1 or not self.evidence_kind:
            raise ValueError("generated-review output requires a positive page and evidence kind")


@dataclass(frozen=True)
class GeneratedReviewManifest:
    """Inputs and outputs needed to validate a generated-review manifest."""

    selection: ReviewSelection
    recipe: RenderRecipe
    outputs: tuple[GeneratedReviewOutput, ...]

    def __post_init__(self) -> None:
        if not self.outputs:
            raise ValueError("generated-review manifest requires at least one output")
        output_paths = [item.path.resolve() for item in self.outputs]
        if len(output_paths) != len(set(output_paths)):
            raise ValueError("generated-review outputs must be unique")
        for output in self.outputs:
            if output.physical_page not in self.selection.physical_pages:
                raise ValueError("generated-review output page was not selected")
            if output.evidence_kind not in self.selection.evidence_kinds:
                raise ValueError("generated-review output evidence kind was not selected")


__all__ = [
    "GeneratedReviewManifest",
    "GeneratedReviewOutput",
    "RenderPlan",
    "RenderRecipe",
    "ReviewArtifactInput",
    "ReviewSelection",
]
