"""Typer-backed command-line interface for ER Commons."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from er_commons.settings import ProjectSettings, load_settings
from er_commons.source_freeze import freeze_release, verify_release

app = typer.Typer(
    help="Small, reproducible environmental-review data workflows.",
    no_args_is_help=True,
)
sources_app = typer.Typer(help="Acquire and verify immutable public source releases.")
app.add_typer(sources_app, name="sources")

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


def main() -> None:
    """Run the CLI defined by the current, intentionally small command surface."""
    app()
