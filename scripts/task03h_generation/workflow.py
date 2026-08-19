"""Orchestrate deterministic Task 03H generation without source PDF/model reads."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .process_templates import generate_process_configs
from .production_identity import production_identity
from .shared import (
    CATALOG_PROJECT_PATH,
    COLLECTION_SPEC_PATH,
    COMPLETION_SHA256,
    DOCUMENT_SPEC_PATH,
    IDENTITY_PATH,
    MANIFEST_RELATIVE,
    MANIFEST_SHA256,
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
