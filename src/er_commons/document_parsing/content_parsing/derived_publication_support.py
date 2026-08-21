"""Small support seams for derived publication and aggregate reference binding."""

from __future__ import annotations

from pathlib import Path

from er_commons.artifact_io import write_json_atomic
from er_commons.document_parsing.content_parsing.conversion_seal import SealedConversion
from er_commons.document_parsing.content_parsing.preparation import PreparedContentParsing
from er_commons.document_parsing.content_parsing.publication import ProducerWorkspace
from er_commons.document_parsing.content_parsing.records import PageRouteRecord
from er_commons.document_parsing.content_parsing.routing import layout_table_observations
from er_commons.document_parsing.content_parsing.sources import CompleteResolvedSource
from er_commons.document_parsing.content_parsing.table_markers import markers_before_first_table


def rebind_aggregate_references(
    routes: list[PageRouteRecord],
    document_payload: dict[str, object],
) -> list[PageRouteRecord]:
    """Replace page-local projection refs with document-global Docling refs."""
    rebound: list[PageRouteRecord] = []
    for route in routes:
        observations = layout_table_observations(document_payload, route.physical_pdf_page)
        rebound.append(
            PageRouteRecord.model_validate(
                {
                    **route.model_dump(mode="json"),
                    "layout_table_observations": observations,
                    "boundary_markers_before_first_table": markers_before_first_table(
                        document_payload,
                        route.physical_pdf_page,
                        observations,
                    ),
                }
            )
        )
    return rebound


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
