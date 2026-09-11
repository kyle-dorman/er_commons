"""Thin command services for separately gated qualification acquisition and reuse."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from er_commons.source_release.qualification_request import load_qualification_request
from er_commons.source_release.qualified_acquisition import (
    acquire_qualified_source,
    reuse_qualified_source,
)
from er_commons.source_release.substitution_evidence import validate_substitution_evidence

LOGGER = logging.getLogger(__name__)


def _clock() -> str:
    """Record observation time in UTC without inferring server timestamps."""
    return datetime.now(UTC).isoformat()


def acquire_from_spec(data_root: Path, spec_path: Path) -> dict[str, Any]:
    """Check accepted provenance before the sole separately authorized GET sequence."""
    import requests

    request = load_qualification_request(spec_path)
    validate_substitution_evidence(data_root, request)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    LOGGER.info("acquiring qualified source into %s", request.destination)
    with requests.Session() as session:
        result = acquire_qualified_source(
            session=session,
            data_root=data_root,
            destination=request.destination,
            source_url=request.source_url,
            policy=request.policy,
            limits=request.limits,
            clock=_clock,
            provenance=request.provenance.model_dump(mode="json"),
        )
    LOGGER.info(
        "qualification complete; conversion remains separately gated: %s", request.destination
    )
    return result


def reuse_from_spec(data_root: Path, spec_path: Path) -> dict[str, Any]:
    """Revalidate compact receipts and metadata without redownloading or reparsing."""
    request = load_qualification_request(spec_path)
    validate_substitution_evidence(data_root, request)
    result = reuse_qualified_source(
        data_root=data_root,
        destination=request.destination,
        source_url=request.source_url,
        policy=request.policy,
        limits=request.limits,
        provenance=request.provenance.model_dump(mode="json"),
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    LOGGER.info("reused qualified source receipt: %s", request.destination)
    return result
