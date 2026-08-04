"""Typer-backed command line for maintained ER Commons workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from er_commons.corpus_extraction import run_document as run_restartable_document
from er_commons.corpus_extraction_contract_v1_1 import validate_fixture_directory
from er_commons.corpus_resolution import run_scope as run_corpus_scope
from er_commons.corpus_resolution import validate_handoff
from er_commons.settings import ProjectSettings, load_settings
from er_commons.source_freeze import freeze_release, verify_release

app = typer.Typer(
    help="Small, reproducible environmental-review data workflows.",
    no_args_is_help=True,
)
sources_app = typer.Typer(help="Acquire and verify immutable public source releases.")
extraction_app = typer.Typer(help="Validate and run explicit corpus-extraction scopes.")
app.add_typer(sources_app, name="sources")
app.add_typer(extraction_app, name="extraction")

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


@extraction_app.command("validate-contract")
def validate_extraction_contract(
    schema: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Restartable corpus-extraction v1.1 JSON Schema.",
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
    """Validate the current offline corpus-extraction contract fixtures."""
    validate_fixture_directory(schema.resolve(), fixtures.resolve())
    typer.echo("restartable_extraction_contract=valid")


@extraction_app.command("run-document")
def run_extraction_document(
    run_spec: Annotated[
        Path,
        typer.Option(
            "--run-spec",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Explicit restartable document-stage run specification.",
        ),
    ],
    source_id: Annotated[
        str,
        typer.Option("--source-id", help="Manifest source ID; no source is implicit."),
    ],
) -> None:
    """Run or checksum-reuse one complete manifest-selected document."""
    completion = run_restartable_document(load_settings().data_root, run_spec, source_id)
    typer.echo(f"document_completion={completion}")


@extraction_app.command("run-scope")
def run_extraction_scope(
    run_spec: Annotated[
        Path,
        typer.Option(
            "--run-spec",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Explicit stage-two scope run specification.",
        ),
    ],
) -> None:
    """Run or checksum-reuse one manifest-ordered corpus scope."""
    completion = run_corpus_scope(load_settings().data_root, run_spec)
    typer.echo(f"handoff_completion={completion}")


@extraction_app.command("validate-handoff")
def validate_extraction_handoff(
    extraction_root: Annotated[
        Path,
        typer.Option(
            "--extraction-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Published Task 03F extraction root.",
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
            help="Current corpus-extraction v1.1 schema.",
        ),
    ],
) -> None:
    """Verify one published handoff and its successful documents without rebuilding."""
    result = validate_handoff(
        extraction_root=extraction_root,
        scope_id=scope_id,
        schema_path=schema,
    )
    typer.echo(f"handoff_id={result.handoff_id}")
    typer.echo(f"documents={result.verified_document_count}")
    typer.echo(f"task04_status={result.task04_status}")


def main() -> None:
    """Run the intentionally small maintained command surface."""
    app()
