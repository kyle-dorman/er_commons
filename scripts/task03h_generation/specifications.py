"""Generate the Task 03H source catalog and collection/document run specs."""

from __future__ import annotations

import re
from typing import Any

from .shared import (
    CATALOG_DATA_RELATIVE,
    COLLECTION_SPEC_NAME,
    CONFIG_ROOT,
    DOCUMENT_SPEC_NAME,
    IDENTITY_RELATIVE,
    MANIFEST_RELATIVE,
    PUBLICATION_ROOT,
    RESOLUTION_POLICY,
    TARGET_POLICY,
    load_object,
    sha256,
)


def model_sources(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Select and verify the sealed 35-source production-full scope."""
    sources = [
        source for source in manifest["sources"] if source.get("source_role") == "model_corpus"
    ]
    if len(sources) != 35 or sum(source["pdf_page_count"] for source in sources) != 48_341:
        raise ValueError("sealed Task 03H scope is not the expected 35 sources / 48,341 pages")
    return sources


def source_titles() -> dict[str, str]:
    """Load official source labels from the sealed-release specification."""
    spec = load_object(CONFIG_ROOT / "brisbane_baylands_2025_deir_sources_v1.json")
    return {
        source["source_id"]: source["expected_label"]
        for source in spec["sources"]
        if source["role"] == "model_corpus"
    }


def source_family_catalog(sources: list[dict[str, Any]], titles: dict[str, str]) -> dict[str, Any]:
    """Generate conservative cross-document aliases for the exact source scope."""
    return {
        "schema_version": "er_commons.source_family_catalog.v1",
        "catalog_version": "brisbane_baylands_2025_deir_task03h_source_family_v1",
        "source_family_id": "brisbane_baylands_2025_deir",
        "sources": [
            {
                "source": {
                    "source_id": source["source_id"],
                    "sha256": source["sha256"],
                    "byte_size": source["byte_size"],
                    "pdf_page_count": source["pdf_page_count"],
                },
                "family_root_source_id": "deir_main",
                "document_role": (
                    "root_report" if source["source_id"] == "deir_main" else "top_level_appendix"
                ),
                "parent_source_id": (None if source["source_id"] == "deir_main" else "deir_main"),
                "reference_aliases": _aliases(source["source_id"], titles[source["source_id"]]),
            }
            for source in sources
        ],
    }


def _aliases(source_id: str, title: str) -> list[str]:
    clean_title = re.sub(r"\s*\(PDF\)$", "", title, flags=re.IGNORECASE).strip()
    if source_id == "deir_main":
        candidates = [
            "complete 2025 baylands specific plan deir",
            "baylands specific plan draft eir",
            "draft eir",
            "deir",
            title,
        ]
    else:
        label, _, subtitle = clean_title.partition(" - ")
        candidates = [clean_title, title, subtitle]
        if "_part_" in source_id:
            match = re.search(r"_part_(\d+)_of_(\d+)$", source_id)
            if match is None:
                raise ValueError(f"multipart source has no part suffix: {source_id}")
            candidates.append(f"{label} part {match.group(1)} of {match.group(2)}")
        else:
            candidates.append(label)
    aliases: list[str] = []
    for candidate in candidates:
        normalized = " ".join(candidate.casefold().split())
        if normalized and normalized not in aliases:
            aliases.append(normalized)
    return aliases


def collection_spec(sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate the collection handoff over the ordered 35-source scope."""
    return {
        "schema_version": "er_commons.collection_run_spec.v2",
        "document_run_spec": DOCUMENT_SPEC_NAME,
        "source_ids": [source["source_id"] for source in sources],
        "source_family_catalog_relative_path": CATALOG_DATA_RELATIVE.as_posix(),
        "blocking_policy": "all_sources_successful",
        "document_evidence_mode": "document_attempt",
        "target_policy_sha256": sha256(TARGET_POLICY),
        "resolution_policy_sha256": sha256(RESOLUTION_POLICY),
        "ordering_policy_version": "record_target_order_v2",
    }


def document_spec(
    sources: list[dict[str, Any]],
    process_paths: dict[str, dict[str, str]],
    extraction_id: str,
) -> dict[str, Any]:
    """Generate the production-full document run specification."""
    return {
        "schema_version": "er_commons.document_run_spec.v2",
        "production_extraction_id": extraction_id,
        "production_identity_relative_path": IDENTITY_RELATIVE.as_posix(),
        "scope_kind": "production_full",
        "source_release_version": "brisbane_baylands_2025_deir_sources_v1",
        "source_manifest_relative_path": MANIFEST_RELATIVE.as_posix(),
        "artifact_relative_root": PUBLICATION_ROOT,
        "document_processes": [
            {
                "source_id": source["source_id"],
                "lineage_mode": "fresh_build",
                "configs": process_paths[source["source_id"]],
            }
            for source in sources
        ],
        "hierarchy_dispositions": [
            {"source_id": source["source_id"], "authority": "machine_validation"}
            for source in sources
        ],
        "resource_policy": {
            "document_concurrency": 1,
            "page_batch_size": 4,
            "stage_batch_size": 4,
            "queue_capacity": 100,
            "cpu_threads_per_document": 4,
            "device": "cpu",
            "memory_estimate_bytes": 17_179_869_184,
            "storage_estimate_bytes": 429_496_729_600,
            "docling_timeout_seconds": None,
            "outer_process_deadline_seconds": 86_400,
            "cancellation_grace_seconds": 15,
            "retry_limit": 1,
        },
    }


__all__ = [
    "COLLECTION_SPEC_NAME",
    "collection_spec",
    "document_spec",
    "model_sources",
    "source_family_catalog",
    "source_titles",
]
