"""Small support seams for derived publication and aggregate reference binding."""

from __future__ import annotations

from pathlib import Path

from er_commons.artifact_io import write_json_atomic
from er_commons.document_parsing.content_parsing.conversion_seal import SealedConversion
from er_commons.document_parsing.content_parsing.preparation import PreparedContentParsing
from er_commons.document_parsing.content_parsing.publication import ProducerWorkspace
from er_commons.document_parsing.content_parsing.records import PageRouteRecord
from er_commons.document_parsing.content_parsing.sources import CompleteResolvedSource
from er_commons.document_parsing.content_parsing.table_markers import MARKER_LABELS


def rebind_aggregate_references(
    routes: list[PageRouteRecord],
    document_payload: dict[str, object],
) -> list[PageRouteRecord]:
    """Replace page-local refs from one linear index of the aggregate document."""
    observations_by_page = _layout_observations_by_page(document_payload)
    markers_by_page = _marker_candidates_by_page(document_payload)
    rebound: list[PageRouteRecord] = []
    for route in routes:
        page_number = route.physical_pdf_page
        observations = observations_by_page.get(page_number, [])
        rebound.append(
            PageRouteRecord.model_validate(
                {
                    **route.model_dump(mode="json"),
                    "layout_table_observations": observations,
                    "boundary_markers_before_first_table": _markers_before_first_table(
                        markers_by_page.get(page_number, []), observations
                    ),
                }
            )
        )
    return rebound


def _layout_observations_by_page(
    document_payload: dict[str, object],
) -> dict[int, list[dict[str, object]]]:
    """Index global table references once in aggregate document order."""
    indexed: dict[int, list[dict[str, object]]] = {}
    tables = document_payload.get("tables", [])
    if not isinstance(tables, list):
        return indexed
    for table_index, table in enumerate(tables):
        if not isinstance(table, dict):
            continue
        provenances = table.get("prov", [])
        if not isinstance(provenances, list):
            continue
        for provenance_index, provenance in enumerate(provenances):
            if not isinstance(provenance, dict):
                continue
            page_number = int(provenance.get("page_no", -1))
            bbox = provenance.get("bbox", {})
            if page_number < 1 or not isinstance(bbox, dict):
                continue
            indexed.setdefault(page_number, []).append(
                {
                    "raw_object_ref": f"#/tables/{table_index}",
                    "provenance_index": provenance_index,
                    "bbox_pdf_points_bottom_left": [
                        float(bbox["l"]),
                        float(bbox["b"]),
                        float(bbox["r"]),
                        float(bbox["t"]),
                    ],
                }
            )
    return indexed


def _marker_candidates_by_page(
    document_payload: dict[str, object],
) -> dict[int, list[dict[str, object]]]:
    """Index only caption and section-header candidates used by table families."""
    indexed: dict[int, list[dict[str, object]]] = {}
    texts = document_payload.get("texts", [])
    if not isinstance(texts, list):
        return indexed
    for text_index, item in enumerate(texts):
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", ""))
        if label not in MARKER_LABELS:
            continue
        provenances = item.get("prov", [])
        if not isinstance(provenances, list):
            continue
        for provenance_index, provenance in enumerate(provenances):
            if not isinstance(provenance, dict):
                continue
            page_number = int(provenance.get("page_no", -1))
            bbox = provenance.get("bbox", {})
            if page_number < 1 or not isinstance(bbox, dict):
                continue
            indexed.setdefault(page_number, []).append(
                {
                    "raw_object_ref": f"#/texts/{text_index}",
                    "provenance_index": provenance_index,
                    "label": label,
                    "text": str(item.get("text", "")),
                    "bbox_pdf_points_bottom_left": [
                        float(bbox["l"]),
                        float(bbox["b"]),
                        float(bbox["r"]),
                        float(bbox["t"]),
                    ],
                }
            )
    return indexed


def _markers_before_first_table(
    candidates: list[dict[str, object]],
    observations: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Filter one page's indexed markers with the accepted vertical rule."""
    if not observations:
        return []
    first_table_top = max(
        float(observation["bbox_pdf_points_bottom_left"][3])  # type: ignore[index]
        for observation in observations
    )
    retained = [
        candidate
        for candidate in candidates
        if float(candidate["bbox_pdf_points_bottom_left"][1]) >= first_table_top  # type: ignore[index]
    ]
    return sorted(
        retained,
        key=lambda marker: (
            -float(marker["bbox_pdf_points_bottom_left"][3]),  # type: ignore[index]
            str(marker["raw_object_ref"]),
        ),
    )


def write_conversion_reference(
    data_root: Path,
    prepared: PreparedContentParsing,
    sealed: SealedConversion,
    workspace: ProducerWorkspace,
) -> None:
    """Persist the exact immutable conversion seal consumed by derived stages."""
    write_json_atomic(
        workspace.records_root / "conversion_input.json",
        {
            "schema_version": "er_commons.conversion_input_reference.v1",
            **sealed.reference,
            "document_view": (
                "heading" if prepared.config.heading_hierarchy_options is not None else "base"
            ),
            "path": sealed.root.relative_to(data_root.resolve()).as_posix(),
            "completion_path": sealed.completion_path.relative_to(data_root.resolve()).as_posix(),
            "inventory_path": sealed.inventory_path.relative_to(data_root.resolve()).as_posix(),
        },
    )


def producer_warnings(
    source: CompleteResolvedSource,
    python_warnings: list[str],
    zero_table_pages: list[int],
) -> list[str]:
    """Combine source, runtime, and table-stage warnings for the producer seal."""
    warnings_out = [*source.warnings, *python_warnings]
    if zero_table_pages:
        warnings_out.append(f"routed pages with zero reconstructed tables: {zero_table_pages}")
    return warnings_out
