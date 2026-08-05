"""Checksummed, request-only review recipes outside candidate identity."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_resolution.storage import json_bytes
from er_commons.extraction_review.rendering import RenderRecipe
from er_commons.source_freeze import write_json_atomic


@dataclass(frozen=True)
class PilotReviewSelection:
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
class PilotReviewRequest:
    """A combined pilot sample that grants no render or publication authority."""

    scope_id: str
    selections: tuple[PilotReviewSelection, ...]

    def __post_init__(self) -> None:
        if not self.scope_id or not self.selections:
            raise ValueError("pilot review request requires a scope and selections")
        keys = [(item.source_id, item.candidate_id) for item in self.selections]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("review selections must be sorted and unique by source and candidate")


def write_review_request_manifest(
    path: Path,
    *,
    data_root: Path,
    request: PilotReviewRequest,
    recipe: RenderRecipe,
) -> Path:
    """Verify immutable inputs and persist a recipe without generating outputs."""
    root = data_root.resolve()
    input_records: list[dict[str, object]] = []
    for item in recipe.inputs:
        resolved = (root / item.path).resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file():
            raise ValueError(f"review input escapes or is absent: {item.path}")
        observed = hashlib.sha256(resolved.read_bytes()).hexdigest()
        if observed != item.sha256:
            raise ValueError(f"review input checksum differs: {item.path}")
        input_records.append({"role": item.role, "path": item.path, "sha256": item.sha256})

    payload: dict[str, object] = {
        "schema_version": "er_commons.requested_review_request.v1",
        "scope_id": request.scope_id,
        "selections": [
            {
                "candidate_id": item.candidate_id,
                "source_id": item.source_id,
                "physical_pages": list(item.physical_pages),
                "evidence_kinds": list(item.evidence_kinds),
            }
            for item in request.selections
        ],
        "recipe": {
            "renderer": recipe.renderer,
            "renderer_version": recipe.renderer_version,
            "arguments": list(recipe.arguments),
            "inputs": input_records,
        },
        "status": "requested_not_rendered",
        "disposition": "disposable_outside_candidate_identity",
        "publication_authority": False,
        "task04_status": "not_evaluated",
    }
    payload["request_sha256"] = hashlib.sha256(json_bytes(payload)).hexdigest()
    write_json_atomic(path, payload)
    return path
