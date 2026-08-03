"""Configuration and verified runtime paths for the human-owned rewrite."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from er_commons.cross_reference_enrichment.storage import sha256_file


@dataclass(frozen=True)
class CrossReferenceEnrichmentConfig:
    """Immutable inputs and artifact locations for one candidate build."""

    upstream_candidate_id: str
    upstream_completion_sha256: str
    upstream_inventory_sha256: str
    reference_candidate_id: str
    reference_completion_sha256: str
    reference_inventory_sha256: str
    artifact_relative_root: Path
    source_manifest_relative_path: Path
    source_manifest_sha256: str
    specification_relative_path: Path
    schema_relative_path: Path
    comparison_relative_root: Path

    @classmethod
    def load(cls, path: Path) -> CrossReferenceEnrichmentConfig:
        """Load the checked-in rewrite configuration."""
        value = json.loads(path.read_bytes())
        return cls(
            upstream_candidate_id=value["upstream_candidate_id"],
            upstream_completion_sha256=value["upstream_completion_sha256"],
            upstream_inventory_sha256=value["upstream_inventory_sha256"],
            reference_candidate_id=value["reference_candidate_id"],
            reference_completion_sha256=value["reference_completion_sha256"],
            reference_inventory_sha256=value["reference_inventory_sha256"],
            artifact_relative_root=Path(value["artifact_relative_root"]),
            source_manifest_relative_path=Path(value["source_manifest_relative_path"]),
            source_manifest_sha256=value["source_manifest_sha256"],
            specification_relative_path=Path(value["specification_relative_path"]),
            schema_relative_path=Path(value["schema_relative_path"]),
            comparison_relative_root=Path(value["comparison_relative_root"]),
        )


@dataclass(frozen=True)
class RuntimeContext:
    """Resolved, checksum-verified paths used by the public workflow."""

    project_root: Path
    data_root: Path
    config_path: Path
    config: CrossReferenceEnrichmentConfig
    task_root: Path
    upstream_root: Path
    reference_root: Path
    source_manifest_path: Path
    comparison_root: Path

    @classmethod
    def load(cls, data_root: Path, config_path: Path) -> RuntimeContext:
        """Resolve configuration and verify both immutable candidate inputs."""
        project_root = Path(__file__).resolve().parents[3]
        resolved_config = config_path.resolve()
        config = CrossReferenceEnrichmentConfig.load(resolved_config)
        task_root = data_root / config.artifact_relative_root
        upstream_root = task_root / config.upstream_candidate_id
        reference_root = task_root / config.reference_candidate_id
        _verify_candidate_input(
            upstream_root,
            completion_sha256=config.upstream_completion_sha256,
            inventory_sha256=config.upstream_inventory_sha256,
        )
        _verify_candidate_input(
            reference_root,
            completion_sha256=config.reference_completion_sha256,
            inventory_sha256=config.reference_inventory_sha256,
        )
        source_manifest_path = data_root / config.source_manifest_relative_path
        if sha256_file(source_manifest_path) != config.source_manifest_sha256:
            raise ValueError("sealed model-corpus source manifest checksum differs")
        return cls(
            project_root=project_root,
            data_root=data_root,
            config_path=resolved_config,
            config=config,
            task_root=task_root,
            upstream_root=upstream_root,
            reference_root=reference_root,
            source_manifest_path=source_manifest_path,
            comparison_root=data_root / config.comparison_relative_root,
        )


def _verify_candidate_input(root: Path, *, completion_sha256: str, inventory_sha256: str) -> None:
    completion = root / "records" / "completion_record.json"
    inventory = root / "records" / "artifact_inventory.json"
    if sha256_file(completion) != completion_sha256:
        raise ValueError(f"candidate completion checksum differs: {root.name}")
    if sha256_file(inventory) != inventory_sha256:
        raise ValueError(f"candidate inventory checksum differs: {root.name}")
