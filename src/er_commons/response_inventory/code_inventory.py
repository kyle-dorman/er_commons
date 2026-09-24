"""Finite behavior inventories for new response-stage execution identities."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from er_commons.artifact_io import canonical_json_sha256

ResponseStage = Literal["source", "relationship", "reference", "presentation"]
_PACKAGE = "src/er_commons/response_inventory/"
_SHARED = (
    "contract.py",
    "response_lists.py",
    "source_structure.py",
    "pilot_policy.py",
    "complete_source_policy.py",
    "run_spec.py",
)
_STAGE_MODULES: dict[ResponseStage, tuple[str, ...]] = {
    "source": (
        *_SHARED,
        "observations.py",
        "pdf_access.py",
        "producer.py",
        "qualification.py",
        "range_receipts.py",
        "workflow.py",
        "full_policy.py",
        "full_workflow.py",
        "saved_evidence.py",
    ),
    "relationship": (
        *_SHARED,
        "acceptance.py",
        "relationship_baseline.py",
        "relationship_candidate.py",
    ),
    "reference": (*_SHARED, "reference_baseline.py"),
    "presentation": (
        "review_tool.py",
        "review_tool_static/app.js",
        "review_tool_static/index.html",
        "review_tool_static/styles.css",
    ),
}


def owned_code_paths(repository_root: Path, *, stage: ResponseStage = "source") -> tuple[Path, ...]:
    """Select finite current behavior paths; never rediscover historical recipes."""
    relative = {_PACKAGE + name for name in _STAGE_MODULES[stage]}
    relative.add("src/er_commons/artifact_io.py")
    if stage == "reference":
        relative.add("src/er_commons/document_records/document_structure/normalization.py")
    paths = tuple(repository_root / name for name in sorted(relative))
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise ValueError(f"response-inventory {stage} code path is missing: {missing[0]}")
    return paths


def owned_code_digest(repository_root: Path, *, stage: ResponseStage = "source") -> str:
    """Hash explicit path/byte dependencies for a future stage execution."""
    root = repository_root.resolve()
    inventory = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in owned_code_paths(root, stage=stage)
    ]
    return canonical_json_sha256(inventory)


__all__ = ["ResponseStage", "owned_code_digest", "owned_code_paths"]
