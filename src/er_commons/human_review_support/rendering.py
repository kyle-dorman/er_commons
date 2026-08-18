"""Provenance manifest for disposable review files rendered by an external tool."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.artifact_io import sha256_file
from er_commons.human_review_support.models import GeneratedReviewManifest


def write_generated_review_manifest(
    root: Path,
    *,
    manifest: GeneratedReviewManifest,
) -> Path:
    """Record externally rendered files without claiming to implement a renderer."""
    root.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, Any]] = []
    for generated in sorted(manifest.outputs, key=lambda item: item.path):
        resolved = generated.path.resolve()
        if not resolved.is_file() or not resolved.is_relative_to(root.resolve()):
            raise ValueError("review output must be an existing file inside the review root")
        files.append(
            {
                "path": resolved.relative_to(root.resolve()).as_posix(),
                "sha256": sha256_file(resolved),
                "byte_size": resolved.stat().st_size,
                "physical_page": generated.physical_page,
                "evidence_kind": generated.evidence_kind,
            }
        )
    payload = {
        "schema_version": "er_commons.requested_review_manifest.v1",
        "candidate_id": manifest.selection.candidate_id,
        "source_id": manifest.selection.source_id,
        "physical_pages": list(manifest.selection.physical_pages),
        "evidence_kinds": list(manifest.selection.evidence_kinds),
        "recipe": {
            "renderer": manifest.recipe.renderer,
            "renderer_version": manifest.recipe.renderer_version,
            "arguments": list(manifest.recipe.arguments),
            "inputs": [
                {"role": item.role, "path": item.path, "sha256": item.sha256}
                for item in manifest.recipe.inputs
            ],
        },
        "disposition": "disposable_outside_candidate_identity",
        "files": files,
    }
    path = root / "review_manifest.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path
