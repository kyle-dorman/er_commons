"""Typed, dependency-neutral inputs admitted to conversion execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_parsing.content_parsing.config import ContentParsingConfig
from er_commons.document_parsing.content_parsing.identity import ContentParsingIdentity
from er_commons.document_parsing.content_parsing.runtime import ModelInventory
from er_commons.document_parsing.content_parsing.sources import CompleteResolvedSource


@dataclass(frozen=True)
class PreparedConversion:
    """Verified conversion inputs whose expensive files remain unopened until a miss."""

    config: ContentParsingConfig
    source: CompleteResolvedSource
    source_manifest_path: Path
    models_root: Path
    model_inventory_path: Path
    model_inventory: ModelInventory
    model_inventory_sha256: str
    runtime: dict[str, Any]
    conversion_identity: ContentParsingIdentity
