"""Lightweight content-parsing package entrypoints."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from er_commons.document_parsing.content_parsing.services import ContentParsingServices


def run_document_parsing(
    data_root: Path,
    config_path: Path,
    *,
    services: ContentParsingServices | None = None,
    artifact_root_override: Path | None = None,
) -> Path:
    """Load the complete-document application only when requested."""
    from er_commons.document_parsing.content_parsing.application import (
        run_document_parsing as execute,
    )

    return execute(
        data_root,
        config_path,
        services=services,
        artifact_root_override=artifact_root_override,
    )


__all__ = ["run_document_parsing"]
