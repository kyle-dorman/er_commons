"""Configuration and verified runtime paths for the human-owned rewrite."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from er_commons.cross_reference_enrichment.storage import read_jsonl, sha256_file


@dataclass(frozen=True)
class CrossReferenceEnrichmentConfig:
    """Immutable inputs and artifact locations for one candidate build."""

    upstream_candidate_id: str
    upstream_completion_sha256: str
    upstream_inventory_sha256: str
    source_id: str
    candidate_version_name: str
    artifact_relative_root: Path
    source_manifest_relative_path: Path
    source_manifest_sha256: str
    specification_relative_path: Path
    schema_relative_path: Path

    def __post_init__(self) -> None:
        """Reject artifact paths that escape their configured roots."""
        paths = (
            self.artifact_relative_root,
            self.source_manifest_relative_path,
            self.specification_relative_path,
            self.schema_relative_path,
        )
        if any(path.is_absolute() or ".." in path.parts for path in paths):
            raise ValueError("cross-reference paths must be contained relative paths")

    @classmethod
    def load(cls, path: Path) -> CrossReferenceEnrichmentConfig:
        """Load the checked-in rewrite configuration."""
        value = json.loads(path.read_bytes())
        return cls(
            upstream_candidate_id=value["upstream_candidate_id"],
            upstream_completion_sha256=value["upstream_completion_sha256"],
            upstream_inventory_sha256=value["upstream_inventory_sha256"],
            source_id=value["source_id"],
            candidate_version_name=value["candidate_version_name"],
            artifact_relative_root=Path(value["artifact_relative_root"]),
            source_manifest_relative_path=Path(value["source_manifest_relative_path"]),
            source_manifest_sha256=value["source_manifest_sha256"],
            specification_relative_path=Path(value["specification_relative_path"]),
            schema_relative_path=Path(value["schema_relative_path"]),
        )


@dataclass(frozen=True)
class RuntimeContext:
    """Resolved, checksum-verified paths used by the public workflow."""

    project_root: Path
    data_root: Path
    config_path: Path
    config_identity_path: Path
    config: CrossReferenceEnrichmentConfig
    task_root: Path
    upstream_root: Path
    source_manifest_path: Path

    @classmethod
    def load(
        cls,
        data_root: Path,
        config_path: Path,
        *,
        config_identity_path: Path | None = None,
    ) -> RuntimeContext:
        """Resolve configuration and verify the immutable upstream candidate."""
        project_root = Path(__file__).resolve().parents[3]
        resolved_config = config_path.resolve()
        config = CrossReferenceEnrichmentConfig.load(resolved_config)
        task_root = data_root / config.artifact_relative_root
        upstream_root = task_root / config.upstream_candidate_id
        _verify_candidate_input(
            upstream_root,
            completion_sha256=config.upstream_completion_sha256,
            inventory_sha256=config.upstream_inventory_sha256,
        )
        documents = read_jsonl(upstream_root / "canonical/documents.jsonl")
        if len(documents) != 1 or documents[0].get("source_id") != config.source_id:
            raise ValueError("cross-reference upstream source differs from config")
        source_manifest_path = data_root / config.source_manifest_relative_path
        if sha256_file(source_manifest_path) != config.source_manifest_sha256:
            raise ValueError("sealed model-corpus source manifest checksum differs")
        return cls(
            project_root=project_root,
            data_root=data_root,
            config_path=resolved_config,
            config_identity_path=(config_identity_path or resolved_config).resolve(),
            config=config,
            task_root=task_root,
            upstream_root=upstream_root,
            source_manifest_path=source_manifest_path,
        )


def _verify_candidate_input(root: Path, *, completion_sha256: str, inventory_sha256: str) -> None:
    completion = root / "records" / "completion_record.json"
    inventory = root / "records" / "artifact_inventory.json"
    if sha256_file(completion) != completion_sha256:
        raise ValueError(f"candidate completion checksum differs: {root.name}")
    if sha256_file(inventory) != inventory_sha256:
        raise ValueError(f"candidate inventory checksum differs: {root.name}")
