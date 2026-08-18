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
from er_commons.document_parsing.content_parsing.runtime import ModelInventory, configuration_record
from er_commons.document_parsing.content_parsing.sources import CompleteResolvedSource

PACKAGE_NAMES = (
    "docling",
    "docling-core",
    "docling-parse",
    "docling-ibm-models",
    "pypdfium2",
    "camelot-py",
    "opencv-python-headless",
    "torch",
)


@dataclass(frozen=True)
class ContentParsingIdentity:
    """One content-derived run ID and the complete payload that produced it."""

    run_id: str
    payload: dict[str, Any]


def canonical_json_sha256(payload: Any) -> str:
    """Hash RFC 8785 canonical JSON for producer identity inputs."""
    return hashlib.sha256(rfc8785.dumps(payload)).hexdigest()


def runtime_identity(
    config: ContentParsingConfig,
    options: Any,
    format_option: Any,
) -> dict[str, Any]:
    """Record effective options while replacing the local absolute model path."""
    record = configuration_record(config.configuration_id, options, format_option)
    effective = dict(record["effective_options"])
    effective["artifacts_path"] = (
        config.model_inventory_relative_path.parent / "models"
    ).as_posix()
    record["effective_options"] = effective
    record["invocation_limits"] = {
        "page_range": [1, config.source.expected_pdf_page_count],
        "max_num_pages": config.source.expected_pdf_page_count,
        "max_file_size": config.source.expected_byte_size,
        "document_timeout_seconds": config.document_timeout_seconds,
    }
    return record


def parsing_code_paths(repo_root: Path) -> list[Path]:
    """List every tracked-code surface that can change parsing behavior."""
    parsing_code = sorted((repo_root / "src/er_commons/document_parsing").rglob("*.py"))
    source_release_code = sorted((repo_root / "src/er_commons/source_release").rglob("*.py"))
    candidates = [
        *parsing_code,
        *source_release_code,
        repo_root / "src/er_commons/artifact_io.py",
        repo_root / "src/er_commons/cli.py",
        repo_root / "pyproject.toml",
        repo_root / "uv.lock",
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


def build_content_parsing_identity(
    *,
    config: ContentParsingConfig,
    source: CompleteResolvedSource,
    source_manifest_path: Path,
    source_completion_path: Path,
    model_inventory_path: Path,
    model_inventory: ModelInventory,
    runtime: dict[str, Any],
    table_environment: dict[str, Any],
    project_code: dict[str, Any],
) -> ContentParsingIdentity:
    """Bind source, policy, runtime, models, packages, and code into one ID."""
    configuration_policy = config.model_dump(
        mode="json",
        exclude={"artifact_relative_root"},
    )
    if config.heading_hierarchy_options is None:
        configuration_policy.pop("heading_hierarchy_options")
    payload = {
        "identity_schema_version": "task03c-producer-identity-v1",
        "producer_policy_version": config.producer_policy_version,
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
        "runtime": runtime,
        "model_inventory": {
            "path": config.model_inventory_relative_path.as_posix(),
            "sha256": sha256_file(model_inventory_path),
            "models": model_inventory.model_dump(mode="json")["models"],
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
