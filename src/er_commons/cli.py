"""Typer-backed command line for maintained ER Commons workflows."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from er_commons.collection_processing import (
    assemble_collection_handoff,
    validate_collection_contract_fixtures,
    validate_collection_handoff,
)
from er_commons.document_publication import publish_document
from er_commons.document_records.document_references.relink_publication import (
    execute_document_relink_from_spec,
)
from er_commons.document_records.document_references.relink_replay import (
    relink_and_replay_document,
    relink_replay_and_assemble_collection,
)
from er_commons.document_records.document_references.reviewed_navigation import (
    materialize_reviewed_navigation_from_spec,
)
from er_commons.settings import ProjectSettings, load_settings
from er_commons.source_release import freeze_release, verify_release
from er_commons.task06g.comparison import publish_task06g_comparison

app = typer.Typer(
    help="Small, reproducible environmental-review data workflows.",
    no_args_is_help=True,
)
sources_app = typer.Typer(help="Acquire and verify immutable public source releases.")
documents_app = typer.Typer(help="Publish complete manifest-selected documents.")
collections_app = typer.Typer(help="Assemble and validate collection handoffs.")
app.add_typer(sources_app, name="sources")
app.add_typer(documents_app, name="documents")
app.add_typer(collections_app, name="collections")

DEFAULT_BRISBANE_SOURCE_SPEC = Path("configs/brisbane_baylands_2025_deir_sources_v1.json")


def configured_paths(settings: ProjectSettings) -> dict[str, Path]:
    """Return the documented external artifact paths from validated settings."""
    root = settings.data_root
    return {
        "data_root": root,
        "ceqa_dataset": root / "datasets" / "ceqa",
        "pipeline_artifacts": root / "pipelines",
        "benchmark_artifacts": root / "benchmarks" / "er_bench",
    }


@app.command()
def about() -> None:
    """Describe the current project scope without mutating data or artifacts."""
    typer.echo("ER Commons: small, reproducible environmental-review data workflows.")
    typer.echo("Current first capability: the CEQA-oriented er_bench benchmark.")


@app.command()
def paths() -> None:
    """Print the configured external data and artifact paths."""
    for name, path in configured_paths(load_settings()).items():
        typer.echo(f"{name}={path}")


@sources_app.command("freeze")
def freeze_sources(
    spec: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Reviewed JSON source specification.",
        ),
    ] = DEFAULT_BRISBANE_SOURCE_SPEC,
) -> None:
    """Acquire or safely resume one reviewed immutable source release."""
    manifest = freeze_release(load_settings().data_root, spec)
    typer.echo(f"release={manifest.source_release_version}")
    typer.echo(f"files={manifest.aggregates['file_count']}")
    typer.echo(f"bytes={manifest.aggregates['byte_count']}")
    typer.echo(f"pages={manifest.aggregates['page_count']}")


@sources_app.command("verify")
def verify_sources(
    spec: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Reviewed JSON source specification.",
        ),
    ] = DEFAULT_BRISBANE_SOURCE_SPEC,
) -> None:
    """Verify a completed source release locally without network access."""
    manifest = verify_release(load_settings().data_root, spec)
    typer.echo(f"verified_release={manifest.source_release_version}")
    typer.echo(f"files={manifest.aggregates['file_count']}")
    typer.echo(f"bytes={manifest.aggregates['byte_count']}")
    typer.echo(f"pages={manifest.aggregates['page_count']}")


@sources_app.command("validate-qualification-spec")
def validate_qualification_spec(
    spec: Annotated[Path, typer.Option(exists=True, dir_okay=False)],
) -> None:
    """Check a qualification request without contacting or opening any source."""
    from er_commons.source_release.qualification_request import load_qualification_request

    request = load_qualification_request(spec)
    typer.echo(f"qualification_spec=valid destination={request.destination}")


@sources_app.command("acquire-qualified")
def acquire_qualified(
    spec: Annotated[Path, typer.Option(exists=True, dir_okay=False)],
) -> None:
    """Execute separately authorized acquisition; never start conversion."""
    from er_commons.source_release.qualification_commands import acquire_from_spec

    acquire_from_spec(load_settings().data_root, spec)


@sources_app.command("reuse-qualified")
def reuse_qualified(
    spec: Annotated[Path, typer.Option(exists=True, dir_okay=False)],
) -> None:
    """Verify a completed qualification receipt without source access."""
    from er_commons.source_release.qualification_commands import reuse_from_spec

    reuse_from_spec(load_settings().data_root, spec)


@collections_app.command("validate-contract")
def validate_collection_contract(
    schema: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Versioned collection-processing JSON Schema.",
        ),
    ],
    fixtures: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing current contract fixtures.",
        ),
    ],
) -> None:
    """Validate the current offline collection-processing contract fixtures."""
    count = validate_collection_contract_fixtures(schema.resolve(), fixtures.resolve())
    typer.echo("collection_contract=valid")
    typer.echo(f"fixtures={count}")


@documents_app.command("publish")
def publish_selected_document(
    document_spec: Annotated[
        Path,
        typer.Option(
            "--document-spec",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Explicit document-publication specification.",
        ),
    ],
    source_id: Annotated[
        str,
        typer.Option("--source-id", help="Manifest source ID; no source is implicit."),
    ],
) -> None:
    """Run or checksum-reuse one complete manifest-selected document."""
    completion = publish_document(load_settings().data_root, document_spec, source_id)
    typer.echo(f"document_completion={completion}")


@documents_app.command("materialize-reviewed-navigation")
def materialize_reviewed_navigation_command(
    review_spec: Annotated[
        Path,
        typer.Option(
            "--review-spec",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Portable reviewed-navigation materialization request.",
        ),
    ],
) -> None:
    """Seal prepared human navigation evidence for the shared linker."""
    published = materialize_reviewed_navigation_from_spec(
        data_root=load_settings().data_root,
        review_spec=review_spec,
    )
    typer.echo(f"reviewed_navigation_bundle={published.descriptor_path}")


@documents_app.command("relink")
def relink_document(
    link_spec: Annotated[
        Path,
        typer.Option(
            "--link-spec",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Explicit portable document-link run specification.",
        ),
    ],
    source_id: Annotated[
        str,
        typer.Option("--source-id", help="The sole selected source to relink."),
    ],
) -> None:
    """Rebuild one source's linking products from sealed extraction records."""
    result = execute_document_relink_from_spec(
        data_root=load_settings().data_root,
        link_spec=link_spec,
        source_id=source_id,
    )
    typer.echo(f"document_link_completion={result.completion_path}")


@documents_app.command("relink-and-replay")
def relink_and_replay_selected_document(
    link_spec: Annotated[
        Path,
        typer.Option(
            "--link-spec",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Explicit portable document-link run specification.",
        ),
    ],
    source_id: Annotated[
        str,
        typer.Option("--source-id", help="The sole selected source to relink and republish."),
    ],
) -> None:
    """Relink one source and publish its downstream-only document descendant."""
    result = relink_and_replay_document(
        data_root=load_settings().data_root,
        link_spec=link_spec,
        source_id=source_id,
    )
    typer.echo(f"document_link_completion={result.linked_completion_path}")
    typer.echo(f"document_completion={result.document_completion_path}")


@collections_app.command("assemble-handoff")
def assemble_handoff(
    collection_spec: Annotated[
        Path,
        typer.Option(
            "--collection-spec",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Explicit collection handoff specification.",
        ),
    ],
) -> None:
    """Assemble or checksum-reuse one manifest-ordered collection handoff."""
    completion = assemble_collection_handoff(load_settings().data_root, collection_spec)
    typer.echo(f"handoff_completion={completion}")


@collections_app.command("relink-and-assemble")
def relink_and_assemble_collection(
    link_spec: Annotated[
        Path,
        typer.Option(
            "--link-spec",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Sealed relink run specification including its collection recipe.",
        ),
    ],
) -> None:
    """Relink and replay every selected document, then assemble one collection."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = relink_replay_and_assemble_collection(
        data_root=load_settings().data_root,
        link_spec=link_spec,
    )
    typer.echo(f"documents_replayed={len(result.documents)}")
    typer.echo(f"handoff_completion={result.handoff_completion_path}")


@collections_app.command("validate-handoff")
def validate_published_handoff(
    collection_root: Annotated[
        Path,
        typer.Option(
            "--collection-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Published collection-processing root.",
        ),
    ],
    scope_id: Annotated[str, typer.Option("--scope-id", help="Published scope ID.")],
    schema: Annotated[
        Path,
        typer.Option(
            "--schema",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Versioned collection-processing schema.",
        ),
    ],
    document_input_root: Annotated[
        Path | None,
        typer.Option(
            "--document-input-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Explicit retained-document authority for collection-only bundles.",
        ),
    ] = None,
) -> None:
    """Verify one published handoff and its successful documents without rebuilding."""
    result = validate_collection_handoff(
        extraction_root=collection_root,
        scope_id=scope_id,
        schema_path=schema,
        data_root=load_settings().data_root,
        document_input_root=document_input_root,
    )
    typer.echo(f"handoff_id={result.handoff_id}")
    typer.echo(f"verified_documents={result.verified_document_count}")
    typer.echo(f"task04_status={result.task04_status}")


@collections_app.command("publish-task06g-comparison")
def publish_task06g_comparison_command(
    comparison_spec: Annotated[
        Path,
        typer.Option(
            "--comparison-spec",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Resolved, receipt-bound Task 06G comparison specification.",
        ),
    ],
) -> None:
    """Publish source-free Task 06G correspondence and comparison closure."""
    correspondence, comparison = publish_task06g_comparison(
        data_root=load_settings().data_root,
        comparison_spec=comparison_spec,
    )
    typer.echo(f"correspondence_completion={correspondence}")
    typer.echo(f"comparison_completion={comparison}")


def main() -> None:
    """Run the intentionally small maintained command surface."""
    app()
