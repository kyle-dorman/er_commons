"""Orchestrate deterministic Task 03H generation without source PDF/model reads."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .process_templates import generate_process_configs
from .production_identity import production_identity
from .shared import (
    CATALOG_PROJECT_PATH,
    CHUNKED_PAGE_THRESHOLD,
    COLLECTION_SPEC_PATH,
    COMPLETION_SHA256,
    DOCUMENT_SPEC_PATH,
    IDENTITY_PATH,
    MANIFEST_RELATIVE,
    MANIFEST_SHA256,
    chunked_policy_paths,
    json_sha256,
    load_object,
    require_digest,
    write_or_check,
)
from .specifications import (
    collection_spec,
    document_spec,
    model_sources,
    source_family_catalog,
    source_titles,
)


def generate_task03h(data_root: Path, *, check: bool) -> None:
    """Generate or check every Task 03H config from sealed metadata only."""
    manifest_path = data_root / MANIFEST_RELATIVE
    completion_path = manifest_path.parent / "completion_record.json"
    require_digest(manifest_path, MANIFEST_SHA256)
    require_digest(completion_path, COMPLETION_SHA256)
    sources = model_sources(load_object(manifest_path))
    titles = source_titles()
    catalog = source_family_catalog(sources, titles)
    process_values, process_paths = generate_process_configs(sources, titles, json_sha256(catalog))
    initial: dict[Path, dict[str, Any]] = {
        CATALOG_PROJECT_PATH: catalog,
        COLLECTION_SPEC_PATH: collection_spec(sources),
        **{path: _chunked_policy() for path in chunked_policy_paths(sources)},
        **process_values,
    }
    write_or_check(initial, check=check)
    identity = production_identity(
        sources=sources,
        manifest_path=manifest_path,
        completion_path=completion_path,
        data_root=data_root,
        process_paths=process_paths,
    )
    write_or_check(
        {
            IDENTITY_PATH: identity,
            DOCUMENT_SPEC_PATH: document_spec(sources, process_paths, identity["extraction_id"]),
        },
        check=check,
    )


def _chunked_policy() -> dict[str, Any]:
    """Return the maintained source-neutral policy for sources over 300 pages."""
    return {
        "schema_version": "er_commons.chunked_execution_policy.v1",
        "mode": "fixed_size",
        "source_selection": {"pdf_page_count_greater_than": CHUNKED_PAGE_THRESHOLD},
        "target_range_size": 225,
        "hard_maximum": 275,
        "overlap_pages": 1,
        "max_range_rss_bytes": 20 * 1024**3,
        "max_aggregate_rss_bytes": 16 * 1024**3,
        "max_wall_seconds": 14400.0,
    }
