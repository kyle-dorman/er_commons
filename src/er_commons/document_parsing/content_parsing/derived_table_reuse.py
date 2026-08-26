"""Validated cloning of canonical tables sealed by chunk aggregation."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from er_commons.artifact_io import read_json_object
from er_commons.document_parsing.content_parsing.conversion_seal import SealedConversion
from er_commons.document_parsing.content_parsing.ordering_projection import (
    OrderingProjectionArtifact,
    verify_table_stage_reference,
)
from er_commons.document_parsing.content_parsing.records import TableStageObservation
from er_commons.document_parsing.content_parsing.table_processing import (
    validate_table_artifacts,
)


def reuse_aggregate_table_stage(
    sealed_conversion: SealedConversion,
    target: Path,
) -> TableStageObservation:
    """Clone and revalidate canonical tables already sealed by chunk aggregation."""
    projection = OrderingProjectionArtifact.model_validate_json(
        (sealed_conversion.root / "records" / "ordering_projection.json").read_bytes()
    )
    observation = projection.table_stage_observation.as_producer_record()
    source = verify_table_stage_reference(projection.table_stage, sealed_conversion.root)
    if observation.status == "not_applicable":
        payload = source / "no_table_stage.json"
        if read_json_object(payload) != observation.model_dump(mode="json", exclude_none=True):
            raise ValueError("aggregate no-table stage differs")
    else:
        validated = validate_table_artifacts(source, observation.routed_pages)
        manifest = read_json_object(source / "manifest.json")
        source_id = manifest.get("source_id")
        expected_manifest = f"documents/{source_id}/producer/tables/manifest.json"
        if not isinstance(source_id, str) or observation.manifest != expected_manifest:
            raise ValueError("aggregate table-stage manifest identity differs")
        relocated = validated.model_copy(update={"manifest": expected_manifest})
        if relocated != observation:
            raise ValueError("aggregate table-stage observation differs")
    shutil.copytree(source, target, copy_function=_link_or_copy)
    return observation


def _link_or_copy(source: str, destination: str) -> str:
    """Hard-link immutable artifacts on one volume, with a portable copy fallback."""
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)
    return destination


__all__ = ["reuse_aggregate_table_stage"]
