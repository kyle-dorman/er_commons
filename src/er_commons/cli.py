"""Typer-backed command-line interface for ER Commons."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from er_commons.document_extraction import (
    run_complete_document_producer,
    run_document_extraction,
)
from er_commons.settings import ProjectSettings, load_settings
from er_commons.source_freeze import freeze_release, verify_release
from er_commons.table_extraction import run_table_extraction

app = typer.Typer(
    help="Small, reproducible environmental-review data workflows.",
    no_args_is_help=True,
)
sources_app = typer.Typer(help="Acquire and verify immutable public source releases.")
documents_app = typer.Typer(help="Extract native PDF structure into reviewable artifacts.")
tables_app = typer.Typer(help="Extract native PDF tables into reviewable artifacts.")
app.add_typer(sources_app, name="sources")
app.add_typer(documents_app, name="documents")
app.add_typer(tables_app, name="tables")

DEFAULT_BRISBANE_SOURCE_SPEC = Path("configs/brisbane_baylands_2025_deir_sources_v1.json")
DEFAULT_DOCUMENT_REVIEW_SPEC = Path(
    "configs/brisbane_baylands_2025_deir_task03a15_document_pipeline_v4.json"
)
DEFAULT_COMPLETE_DOCUMENT_SPEC = Path(
    "configs/brisbane_baylands_2025_deir_task03c_appendix_p_v2.json"
)
DEFAULT_TABLE_REVIEW_SPEC = Path(
    "configs/brisbane_baylands_2025_deir_task03a13_unified_table_pipeline_v1.json"
)
DEFAULT_TABLE_FIRST_600_SPEC = Path(
    "configs/brisbane_baylands_2025_deir_task03a14_first_600_table_pipeline_v1.json"
)


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


@documents_app.command("run-review")
def run_document_review(
    config: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Fixed ten-page document-extraction pipeline configuration.",
        ),
    ] = DEFAULT_DOCUMENT_REVIEW_SPEC,
) -> None:
    """Run the clean Task 03A parser and compare it with accepted JSON."""
    manifest_path = run_document_extraction(load_settings().data_root, config)
    typer.echo(f"pipeline_manifest={manifest_path}")


@documents_app.command("run-complete")
def run_complete_document(
    config: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Manifest-selected complete-document producer configuration.",
        ),
    ] = DEFAULT_COMPLETE_DOCUMENT_SPEC,
) -> None:
    """Publish or checksum-verify one complete Task 03C producer run."""
    completion_path = run_complete_document_producer(
        load_settings().data_root,
        config,
    )
    typer.echo(f"producer_completion={completion_path}")


@tables_app.command("run-review")
def run_table_review(
    spec: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Reviewed ten-page table-extraction specification.",
        ),
    ] = DEFAULT_TABLE_REVIEW_SPEC,
) -> None:
    """Run or resume the fixed ten-page table-parser review."""
    manifest_path = run_table_extraction(load_settings().data_root, spec)
    typer.echo(f"pipeline_manifest={manifest_path}")


@tables_app.command("run-first-600")
def run_table_first_600(
    spec: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Reviewed first-600-page table-extraction specification.",
        ),
    ] = DEFAULT_TABLE_FIRST_600_SPEC,
) -> None:
    """Run or resume the parser on exactly physical PDF pages 1-600."""
    manifest_path = run_table_extraction(load_settings().data_root, spec)
    typer.echo(f"pipeline_manifest={manifest_path}")


def main() -> None:
    """Run the CLI defined by the current, intentionally small command surface."""
    app()
