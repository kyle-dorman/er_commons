"""Source-free reuse of conversion-sealed aggregate routing and table evidence."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import read_json_object, sha256_file
from er_commons.document_parsing.content_parsing.conversion_seal import SealedConversion
from er_commons.document_parsing.content_parsing.evidence import verify_inventory_metadata
from er_commons.document_parsing.content_parsing.ordering_projection import (
    OrderingProjectionArtifact,
    verify_table_stage_reference,
)
from er_commons.document_parsing.content_parsing.preparation import PreparedContentParsing
from er_commons.document_parsing.content_parsing.records import (
    PageRouteRecord,
    TableStageObservation,
)
from er_commons.document_parsing.content_parsing.table_processing import validate_table_artifacts


def accepted_aggregate_inventory(sealed: SealedConversion) -> dict[str, Any]:
    """Require the conversion seal to cover its projection and every inherited file."""
    completion = read_json_object(sealed.completion_path)
    if sha256_file(sealed.inventory_path) != completion["artifact_inventory_sha256"]:
        raise ValueError("accepted aggregate inventory seal differs")
    inventory = cast(dict[str, Any], read_json_object(sealed.inventory_path))
    verify_inventory_metadata(sealed.root, inventory)
    rows = {row["path"]: row for row in inventory["files"]}
    relative = "records/ordering_projection.json"
    if relative not in rows or sha256_file(sealed.root / relative) != rows[relative]["sha256"]:
        raise ValueError("accepted aggregate requires its sealed ordering projection")
    return inventory


def reuse_accepted_aggregate_tables(
    sealed: SealedConversion,
    prepared: PreparedContentParsing,
    routes: list[PageRouteRecord],
    target: Path,
    inventory: dict[str, Any],
    *,
    inherited_files: dict[Path, tuple[Path, int, str]] | None = None,
) -> tuple[TableStageObservation, dict[Path, tuple[Path, int, str]]]:
    """Validate compatible sealed tables, then hard-link without reading image bytes."""
    projection = OrderingProjectionArtifact.model_validate_json(
        (sealed.root / "records/ordering_projection.json").read_bytes()
    )
    observation = projection.table_stage_observation.as_producer_record()
    reference = projection.table_stage
    source = reference.resolve(sealed.root)
    rows = {row["path"]: row for row in inventory["files"]}
    marker = source / reference.completion_marker
    marker_relative = marker.relative_to(sealed.root).as_posix()
    if marker_relative not in rows or sha256_file(marker) != reference.completion_marker_sha256:
        raise ValueError("accepted aggregate table completion seal differs")
    routed = [row.physical_pdf_page for row in routes if row.route != "no_table_route"]
    if observation.routed_pages != routed:
        raise ValueError("accepted aggregate table routes differ from current policy")
    if observation.status == "not_applicable":
        verify_table_stage_reference(reference, sealed.root)
        if read_json_object(marker) != observation.model_dump(mode="json", exclude_none=True):
            raise ValueError("accepted aggregate no-table observation differs")
    else:
        manifest = read_json_object(marker)
        table_inventory = source / "artifact_inventory.json"
        if manifest.get("artifact_inventory") != "artifact_inventory.json" or (
            sha256_file(table_inventory) != reference.artifact_inventory_sha256
        ):
            raise ValueError("accepted aggregate table inventory seal differs")
        config = read_json_object(source / "configuration.json")
        expected = {
            "source_id": prepared.source.source_id,
            "expected_source_sha256": prepared.source.source_sha256,
            "expected_pdf_page_count": prepared.source.source_page_count,
            "detection": prepared.config.table_detection.model_dump(mode="json"),
            "cleanup": prepared.config.table_cleanup.model_dump(mode="json"),
            "learned_fallback": prepared.config.learned_table_fallback.model_dump(mode="json"),
        }
        if any(config.get(key) != value for key, value in expected.items()):
            raise ValueError("accepted aggregate table source or policy differs")
        recorded_routes = config.get("routed_pages")
        expected_routes = [
            (
                row.physical_pdf_page,
                row.route,
                row.layout_table_regions_pdf_points_bottom_left
                if row.route == "layout_regions"
                else [],
            )
            for row in routes
            if row.route != "no_table_route"
        ]
        if (
            not isinstance(recorded_routes, list)
            or [
                (
                    row.get("physical_pdf_page"),
                    row.get("route"),
                    row.get("layout_regions_pdf_points_bottom_left"),
                )
                for row in recorded_routes
                if isinstance(row, dict)
            ]
            != expected_routes
            or len(recorded_routes) != len(expected_routes)
        ):
            raise ValueError("accepted aggregate table route geometry differs")
        validated = validate_table_artifacts(source, routed).model_copy(
            update={
                "manifest": f"documents/{prepared.source.source_id}/producer/tables/manifest.json"
            }
        )
        if manifest.get("source_id") != prepared.source.source_id or validated != observation:
            raise ValueError("accepted aggregate table observation differs")
    if read_json_object(source / "manifest.json").get("source_id") != prepared.source.source_id:
        raise ValueError("accepted aggregate table source differs")
    inherited = inherited_files if inherited_files is not None else {}
    target.mkdir(parents=True, exist_ok=False)
    for item in sorted(source.rglob("*")):
        if item.is_symlink():
            raise ValueError("accepted aggregate table evidence contains a symlink")
        if not item.is_file():
            continue
        row = rows.get(item.relative_to(sealed.root).as_posix())
        if row is None or row["byte_size"] != item.stat().st_size:
            raise ValueError("accepted aggregate table file is outside its sealed inventory")
        destination = target / item.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.link(item, destination)  # No copy fallback: it would read preserved image payloads.
        inherited[destination] = (item, row["byte_size"], row["sha256"])
    return observation, inherited
