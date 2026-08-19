"""Orchestrate one immutable complete-document producer publication."""

from __future__ import annotations

import logging
from pathlib import Path

from er_commons.document_parsing.content_parsing.config import load_content_parsing_config
from er_commons.document_parsing.content_parsing.conversion_bundle import (
    ensure_conversion_bundle,
    retained_conversion_attempt,
)
from er_commons.document_parsing.content_parsing.derived_publication import (
    DerivedPublicationProgress,
    build_and_publish_derived,
)
from er_commons.document_parsing.content_parsing.evidence import verify_completed_run
from er_commons.document_parsing.content_parsing.preparation import (
    PreparedContentParsing,
    prepare_content_parsing,
)
from er_commons.document_parsing.content_parsing.publication import (
    preserve_failed_attempt,
    task_artifact_root,
)
from er_commons.document_parsing.content_parsing.references import resolve_conversion_input
from er_commons.document_parsing.content_parsing.services import ContentParsingServices

LOGGER = logging.getLogger(__name__)


def run_document_parsing(
    data_root: Path,
    config_path: Path,
    *,
    services: ContentParsingServices | None = None,
    artifact_root_override: Path | None = None,
) -> Path:
    """Run or checksum-verify one complete immutable producer publication."""
    active_services = services or ContentParsingServices()
    started_at = active_services.now()
    started = active_services.monotonic()
    config, digest = load_content_parsing_config(config_path)
    task_root = task_artifact_root(
        data_root,
        artifact_root_override
        if artifact_root_override is not None
        else config.artifact_relative_root,
    )
    producer_run_id: str | None = None
    progress = DerivedPublicationProgress()
    try:
        prepared = prepare_content_parsing(
            data_root,
            config=config,
            config_sha256=digest,
        )
        producer_run_id = prepared.identity.run_id
        final_root = task_root / producer_run_id
        if final_root.exists():
            completion = verify_completed_run(final_root, producer_run_id)
            resolve_conversion_input(data_root, final_root / "records/conversion_input.json")
            return completion
        progress.stage = "docling_conversion"
        sealed_conversion = ensure_conversion_bundle(
            task_root=task_root,
            prepared=prepared,
            services=active_services,
        )
        return build_and_publish_derived(
            data_root=data_root,
            task_root=task_root,
            config_path=config_path,
            prepared=prepared,
            sealed_conversion=sealed_conversion,
            services=active_services,
            started=started,
            progress=progress,
        )
    except BaseException as error:
        conversion_attempt = retained_conversion_attempt(error)
        if conversion_attempt is not None:
            LOGGER.error("Conversion attempt failed; evidence=%s", conversion_attempt)
            raise
        attempt = preserve_failed_attempt(
            staging_root=(
                progress.workspace.staging_root if progress.workspace is not None else None
            ),
            task_root=task_root,
            producer_run_id=producer_run_id,
            failed_stage=progress.stage,
            started_at=started_at,
            finished_at=active_services.now(),
            wall_seconds=active_services.monotonic() - started,
            error=error,
            token=active_services.new_token(),
        )
        LOGGER.error("Producer attempt failed; evidence=%s", attempt)
        raise


__all__ = ["PreparedContentParsing", "prepare_content_parsing", "run_document_parsing"]
