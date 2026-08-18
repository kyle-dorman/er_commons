"""Typer-backed command line for maintained ER Commons workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from er_commons.collection_processing import (
    assemble_collection_handoff,
    validate_collection_contract_fixtures,
    validate_collection_handoff,
)
from er_commons.document_publication import publish_document
from er_commons.settings import ProjectSettings, load_settings
from er_commons.source_release import freeze_release, verify_release

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
) -> None:
    """Verify one published handoff and its successful documents without rebuilding."""
    result = validate_collection_handoff(
        extraction_root=collection_root,
        scope_id=scope_id,
        schema_path=schema,
    )
    typer.echo(f"handoff_id={result.handoff_id}")
    typer.echo(f"verified_documents={result.verified_document_count}")
    typer.echo(f"task04_status={result.task04_status}")


def main() -> None:
    """Run the intentionally small maintained command surface."""
    app()
