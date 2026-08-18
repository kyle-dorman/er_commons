"""Checksummed, request-only review recipes outside candidate identity."""

from __future__ import annotations

import hashlib
from pathlib import Path

from er_commons.artifact_io import json_bytes, sha256_file, write_json_atomic
from er_commons.human_review_support.models import RenderPlan, RenderRecipe


def write_render_plan_manifest(
    path: Path,
    *,
    data_root: Path,
    plan: RenderPlan,
    recipe: RenderRecipe,
) -> Path:
    """Verify immutable inputs and persist a recipe without generating outputs."""
    root = data_root.resolve()
    input_records: list[dict[str, object]] = []
    for item in recipe.inputs:
        resolved = (root / item.path).resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file():
            raise ValueError(f"review input escapes or is absent: {item.path}")
        observed = sha256_file(resolved)
        if observed != item.sha256:
            raise ValueError(f"review input checksum differs: {item.path}")
        input_records.append({"role": item.role, "path": item.path, "sha256": item.sha256})

    payload: dict[str, object] = {
        "schema_version": "er_commons.render_request.v2",
        "scope_id": plan.scope_id,
        "selections": [
            {
                "candidate_id": item.candidate_id,
                "source_id": item.source_id,
                "physical_pages": list(item.physical_pages),
                "evidence_kinds": list(item.evidence_kinds),
            }
            for item in plan.selections
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
