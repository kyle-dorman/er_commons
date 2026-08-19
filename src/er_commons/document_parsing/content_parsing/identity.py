"""Build the deterministic identity of complete-document producer behavior."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any

import rfc8785

from er_commons.artifact_io import sha256_file
from er_commons.document_parsing.content_parsing.config import ContentParsingConfig
from er_commons.document_parsing.content_parsing.sources import CompleteResolvedSource

PACKAGE_NAMES = (
    "pypdfium2",
    "camelot-py",
    "opencv-python-headless",
)


@dataclass(frozen=True)
class ContentParsingIdentity:
    """One content-derived run ID and the complete payload that produced it."""

    run_id: str
    payload: dict[str, Any]


def canonical_json_sha256(payload: Any) -> str:
    """Hash RFC 8785 canonical JSON for producer identity inputs."""
    return hashlib.sha256(rfc8785.dumps(payload)).hexdigest()


def parsing_code_paths(repo_root: Path) -> list[Path]:
    """List only routing/table owner code that can change producer bytes."""
    content = repo_root / "src/er_commons/document_parsing/content_parsing"
    tables = repo_root / "src/er_commons/document_parsing/table_reconstruction"
    content_names = (
        "application.py",
        "config.py",
        "derived_publication.py",
        "evidence.py",
        "identity.py",
        "preparation.py",
        "publication.py",
        "records.py",
        "routing.py",
        "routing_execution.py",
        "routing_geometry.py",
        "services.py",
        "sources.py",
        "table_markers.py",
        "table_processing.py",
        "table_request.py",
    )
    candidates = [
        *(content / name for name in content_names),
        *sorted(tables.rglob("*.py")),
        repo_root / "src/er_commons/artifact_io.py",
    ]
    return [path for path in candidates if path.is_file()]


def code_identity(paths: list[Path], *, repo_root: Path) -> dict[str, Any]:
    """Hash the relative path and content of every parsing-owned code file."""
    records = [
        {
            "path": path.resolve().relative_to(repo_root.resolve()).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in sorted(paths)
    ]
    return {
        "sha256": canonical_json_sha256(records),
        "files": records,
    }


def routing_table_policy(config: ContentParsingConfig) -> dict[str, Any]:
    """Project one combined config onto only shared routing/table behavior."""
    return {
        "strict_table_dominant_thresholds": config.strict_table_dominant_thresholds.model_dump(
            mode="json"
        ),
        "numeric_table_bearing_thresholds": config.numeric_table_bearing_thresholds.model_dump(
            mode="json"
        ),
        "table_detection": config.table_detection.model_dump(mode="json"),
        "table_cleanup": config.table_cleanup.model_dump(mode="json"),
        "learned_table_fallback": config.learned_table_fallback.model_dump(mode="json"),
    }


def build_content_parsing_identity(
    *,
    config: ContentParsingConfig,
    source: CompleteResolvedSource,
    source_manifest_path: Path,
    source_completion_path: Path,
    table_environment: dict[str, Any],
    project_code: dict[str, Any],
    conversion_id: str,
) -> ContentParsingIdentity:
    """Bind source, policy, runtime, models, packages, and code into one ID."""
    configuration_policy = routing_table_policy(config)
    payload = {
        "identity_schema_version": "er_commons.routing_table_identity.v2",
        "docling_conversion_id": conversion_id,
        "routing_table_contract_version": "er_commons.routing_table_bundle.v1",
        "configuration_policy": configuration_policy,
        "source": {
            "source_id": source.source_id,
            "sha256": source.source_sha256,
            "byte_size": source.source_byte_size,
            "pdf_page_count": source.source_page_count,
        },
        "sealed_release": {
            "source_release_version": config.source_release_version,
            "manifest_path": config.source_manifest_relative_path.as_posix(),
            "manifest_sha256": sha256_file(source_manifest_path),
            "completion_record_path": (
                config.source_manifest_relative_path.parent / "completion_record.json"
            ).as_posix(),
            "completion_record_sha256": sha256_file(source_completion_path),
        },
        "routing_sha256": canonical_json_sha256(
            {
                "strict": config.strict_table_dominant_thresholds.model_dump(mode="json"),
                "numeric": config.numeric_table_bearing_thresholds.model_dump(mode="json"),
            }
        ),
        "table_sha256": canonical_json_sha256(
            {
                "detection": config.table_detection.model_dump(mode="json"),
                "cleanup": config.table_cleanup.model_dump(mode="json"),
                "learned_fallback": config.learned_table_fallback.model_dump(mode="json"),
                "family_policy": "terminal-continuation-and-header-fragment-v3",
                "retain_review_derivatives": False,
            }
        ),
        "table_environment": table_environment,
        "package_versions": {name: version(name) for name in PACKAGE_NAMES},
        "code": project_code,
    }
    return ContentParsingIdentity(
        run_id=f"prv1-{canonical_json_sha256(payload)}",
        payload=payload,
    )
