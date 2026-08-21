"""Explicit chunked alternative to the maintained monolithic conversion entrypoint."""

from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import read_json_object
from er_commons.chunked_conversion.runtime import (
    ChunkedConversionRequest,
    ensure_chunked_conversion_bundle,
)
from er_commons.document_parsing.content_parsing.config import load_content_parsing_config
from er_commons.document_parsing.content_parsing.derived_publication import (
    DerivedPublicationProgress,
    build_and_publish_derived,
)
from er_commons.document_parsing.content_parsing.evidence import verify_completed_run
from er_commons.document_parsing.content_parsing.identity import (
    ContentParsingIdentity,
    build_content_parsing_identity,
    code_identity,
    parsing_code_paths,
)
from er_commons.document_parsing.content_parsing.preparation import prepare_content_parsing
from er_commons.document_parsing.content_parsing.publication import (
    preserve_failed_attempt,
    task_artifact_root,
)
from er_commons.document_parsing.content_parsing.references import resolve_conversion_input
from er_commons.document_parsing.content_parsing.services import ContentParsingServices
from er_commons.document_parsing.table_reconstruction.pipeline import installed_table_environment

LOGGER = logging.getLogger(__name__)


def run_chunked_document_parsing(
    data_root: Path,
    config_path: Path,
    plan_path: Path,
    *,
    request: ChunkedConversionRequest,
    services: ContentParsingServices | None = None,
) -> Path:
    """Publish the normal producer bundle using an explicitly selected chunk plan."""
    active_services = services or ContentParsingServices()
    started_at = active_services.now()
    started = active_services.monotonic()
    if request.plan_path.resolve() != plan_path.resolve():
        raise ValueError("chunk request plan differs from the selected production plan")
    config, config_sha256 = load_content_parsing_config(config_path)
    prepared = prepare_content_parsing(data_root, config=config, config_sha256=config_sha256)
    project_root = Path(__file__).resolve().parents[4]
    sealed = ensure_chunked_conversion_bundle(request, project_root=project_root)
    producer_identity = build_content_parsing_identity(
        config=config,
        source=prepared.source,
        source_manifest_path=prepared.source_manifest_path,
        source_completion_path=prepared.source_manifest_path.parent / "completion_record.json",
        table_environment=installed_table_environment(),
        project_code=code_identity(parsing_code_paths(project_root), repo_root=project_root),
        conversion_id=sealed.conversion_id,
    )
    conversion_record = read_json_object(sealed.root / "records/conversion_identity.json")
    conversion_identity = ContentParsingIdentity(
        run_id=sealed.conversion_id,
        payload=cast(dict[str, Any], conversion_record["identity"]),
    )
    prepared = replace(
        prepared,
        conversion_identity=conversion_identity,
        identity=producer_identity,
    )
    task_root = task_artifact_root(data_root, config.artifact_relative_root)
    final_root = task_root / producer_identity.run_id
    progress = DerivedPublicationProgress()
    try:
        if final_root.exists():
            completion = verify_completed_run(final_root, producer_identity.run_id)
            resolve_conversion_input(data_root, final_root / "records/conversion_input.json")
            return completion
        return build_and_publish_derived(
            data_root=data_root,
            task_root=task_root,
            config_path=config_path,
            prepared=prepared,
            sealed_conversion=sealed,
            services=active_services,
            started=started,
            progress=progress,
        )
    except BaseException as error:
        attempt = preserve_failed_attempt(
            staging_root=(
                progress.workspace.staging_root if progress.workspace is not None else None
            ),
            task_root=task_root,
            producer_run_id=producer_identity.run_id,
            failed_stage=progress.stage,
            started_at=started_at,
            finished_at=active_services.now(),
            wall_seconds=active_services.monotonic() - started,
            error=error,
            token=active_services.new_token(),
        )
        LOGGER.error("Producer attempt failed; evidence=%s", attempt)
        raise


__all__ = ["run_chunked_document_parsing"]
