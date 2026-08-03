"""Checked-in configuration for the Task 03E.5 Appendix P pilot."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CrossReferenceConfig:
    """Immutable paths and checksums that define one v3 candidate."""

    upstream_candidate_id: str
    upstream_completion_sha256: str
    upstream_inventory_sha256: str
    artifact_relative_root: Path
    specification_relative_path: Path
    schema_relative_path: Path


def load_config(path: Path) -> CrossReferenceConfig:
    """Load the narrow cross-reference configuration."""
    value = json.loads(path.read_bytes())
    return CrossReferenceConfig(
        upstream_candidate_id=value["upstream_candidate_id"],
        upstream_completion_sha256=value["upstream_completion_sha256"],
        upstream_inventory_sha256=value["upstream_inventory_sha256"],
        artifact_relative_root=Path(value["artifact_relative_root"]),
        specification_relative_path=Path(value["specification_relative_path"]),
        schema_relative_path=Path(value["schema_relative_path"]),
    )
