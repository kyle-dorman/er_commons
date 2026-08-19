"""Derive the conversion-only identity used by the Docling restart boundary."""

from __future__ import annotations

from importlib.metadata import version
from pathlib import Path
from typing import Any

from er_commons.artifact_io import sha256_file
from er_commons.document_parsing.content_parsing.config import (
    ContentParsingConfig,
    HeadingHierarchyConfig,
)
from er_commons.document_parsing.content_parsing.identity import (
    ContentParsingIdentity,
    canonical_json_sha256,
    code_identity,
)
from er_commons.document_parsing.content_parsing.runtime import (
    ModelInventory,
    configuration_record,
)
from er_commons.document_parsing.content_parsing.sources import CompleteResolvedSource

CONVERSION_PACKAGE_NAMES = (
    "docling",
    "docling-core",
    "docling-parse",
    "docling-ibm-models",
    "pypdfium2",
    "torch",
)

COMMON_HEADING_HIERARCHY = HeadingHierarchyConfig(
    enabled=True,
    use_bookmarks=True,
    use_numbering=True,
    use_style=True,
    numbering_schemes=None,
    max_level=6,
    bookmark_match_threshold=0.8,
)


def conversion_code_paths(repo_root: Path) -> list[Path]:
    """List code that can change conversion bytes without routing/table policy."""
    relative_paths = (
        "src/er_commons/artifact_io.py",
        "src/er_commons/document_parsing/content_parsing/artifacts.py",
        "src/er_commons/document_parsing/content_parsing/conversion.py",
        "src/er_commons/document_parsing/content_parsing/conversion_bundle.py",
        "src/er_commons/document_parsing/content_parsing/conversion_execution.py",
        "src/er_commons/document_parsing/content_parsing/conversion_identity.py",
        "src/er_commons/document_parsing/content_parsing/conversion_preflight.py",
        "src/er_commons/document_parsing/content_parsing/conversion_seal.py",
        "src/er_commons/document_parsing/content_parsing/evidence.py",
        "src/er_commons/document_parsing/content_parsing/records.py",
        "src/er_commons/document_parsing/content_parsing/runtime.py",
        "src/er_commons/document_parsing/content_parsing/services.py",
        "src/er_commons/document_parsing/content_parsing/sources.py",
        "src/er_commons/document_parsing/heading_evidence_parsing/alignment_projection.py",
        "src/er_commons/document_parsing/heading_evidence_parsing/errors.py",
        "src/er_commons/document_parsing/heading_evidence_parsing/heading_overlay.py",
        "src/er_commons/document_parsing/heading_evidence_parsing/text_evidence.py",
        "src/er_commons/document_parsing/heading_evidence_parsing/types.py",
    )
    source_release = sorted((repo_root / "src/er_commons/source_release").rglob("*.py"))
    candidates = [*(repo_root / path for path in relative_paths), *source_release]
    return [path for path in candidates if path.is_file()]


def conversion_policy(config: ContentParsingConfig) -> dict[str, Any]:
    """Project the combined producer config onto Docling-owned inputs only."""
    return {
        "contract_version": "er_commons.docling_conversion.v2",
        "backend": config.backend,
        "device": config.device,
        "thread_count": config.thread_count,
        "document_timeout_seconds": config.document_timeout_seconds,
        "heading_hierarchy_options": COMMON_HEADING_HIERARCHY.model_dump(mode="json"),
        "native_text_only": True,
        "ocr_enabled": False,
        "table_structure_enabled": False,
        "picture_images_enabled": True,
        "durable_image_policy": {
            "contract_version": "er_commons.docling_image_externalization.v1",
            "figure_crops_preserved_as_assets": True,
            "full_page_renders_preserved": False,
        },
        "output_schemas": {
            "document": "docling_document_with_base_levels.v1",
            "heading_overlay": "er_commons.heading_level_overlay.v1",
            "alignment": "er_commons.hierarchy_alignment_page.v1",
        },
        "invocation_limits": {
            "page_range": [1, config.source.expected_pdf_page_count],
            "max_num_pages": config.source.expected_pdf_page_count,
            "max_file_size": config.source.expected_byte_size,
        },
    }


def effective_runtime_identity(
    config: ContentParsingConfig,
    options: Any,
    format_option: Any,
) -> dict[str, Any]:
    """Record effective conversion options without persisting a local model path."""
    record = configuration_record(config.configuration_id, options, format_option)
    effective = dict(record["effective_options"])
    effective["artifacts_path"] = (
        config.model_inventory_relative_path.parent / "models"
    ).as_posix()
    record["effective_options"] = effective
    record["invocation_limits"] = conversion_policy(config)["invocation_limits"]
    return record


def build_conversion_identity(
    *,
    config: ContentParsingConfig,
    source: CompleteResolvedSource,
    source_manifest_path: Path,
    source_completion_path: Path,
    model_inventory_path: Path,
    model_inventory: ModelInventory,
    project_code: dict[str, Any],
) -> ContentParsingIdentity:
    """Bind source, Docling policy/models/packages, and adapter code into one ID."""
    payload = {
        "identity_schema_version": "er_commons.docling_conversion_identity.v1",
        "conversion_policy": conversion_policy(config),
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
        "model_inventory": {
            "path": config.model_inventory_relative_path.as_posix(),
            "sha256": sha256_file(model_inventory_path),
            "models": model_inventory.model_dump(mode="json")["models"],
        },
        "package_versions": {name: version(name) for name in CONVERSION_PACKAGE_NAMES},
        "code": project_code,
    }
    return ContentParsingIdentity(
        run_id=f"dconv1-{canonical_json_sha256(payload)}",
        payload=payload,
    )


def derive_conversion_identity(
    *,
    repo_root: Path,
    config: ContentParsingConfig,
    source: CompleteResolvedSource,
    source_manifest_path: Path,
    source_completion_path: Path,
    model_inventory_path: Path,
    model_inventory: ModelInventory,
) -> ContentParsingIdentity:
    """Build a conversion identity from the maintained conversion code inventory."""
    return build_conversion_identity(
        config=config,
        source=source,
        source_manifest_path=source_manifest_path,
        source_completion_path=source_completion_path,
        model_inventory_path=model_inventory_path,
        model_inventory=model_inventory,
        project_code=code_identity(conversion_code_paths(repo_root), repo_root=repo_root),
    )
