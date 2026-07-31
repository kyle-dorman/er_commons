"""Typer-backed command-line interface for ER Commons."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from er_commons.canonical_extraction import run_document_canonicalization
from er_commons.document_extraction import (
    run_complete_document_producer,
    run_document_extraction,
    run_hierarchy_producer_evaluation,
)
from er_commons.hierarchy_correction import (
    prepare_held_out_review,
    run_hierarchy_correction,
    seal_held_out_annotations,
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
canonicalize_app = typer.Typer(
    help="Materialize project-owned canonical records from verified producer artifacts."
)
hierarchy_app = typer.Typer(help="Build deterministic hierarchy-correction overlays.")
app.add_typer(sources_app, name="sources")
app.add_typer(documents_app, name="documents")
app.add_typer(tables_app, name="tables")
app.add_typer(canonicalize_app, name="canonicalize")
app.add_typer(hierarchy_app, name="hierarchy")

DEFAULT_BRISBANE_SOURCE_SPEC = Path("configs/brisbane_baylands_2025_deir_sources_v1.json")
DEFAULT_DOCUMENT_REVIEW_SPEC = Path(
    "configs/brisbane_baylands_2025_deir_task03a15_document_pipeline_v4.json"
)
DEFAULT_COMPLETE_DOCUMENT_SPEC = Path(
    "configs/brisbane_baylands_2025_deir_task03c_appendix_p_v2.json"
)
DEFAULT_HIERARCHY_EVALUATION_SPEC = Path(
    "configs/brisbane_baylands_2025_deir_task03e_hierarchy_evaluation_v1.json"
)
DEFAULT_CANONICALIZATION_SPEC = Path(
    "configs/brisbane_baylands_2025_deir_task03d_appendix_p_v1.json"
)
DEFAULT_HIERARCHY_CORRECTION_SPEC = Path(
    "configs/brisbane_baylands_2025_deir_task03e2_hierarchy_correction_v1.json"
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


@documents_app.command("evaluate-hierarchy")
def evaluate_document_hierarchy(
    evaluation: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Frozen Task 03E hierarchy evaluation specification.",
        ),
    ] = DEFAULT_HIERARCHY_EVALUATION_SPEC,
) -> None:
    """Run the repeated Appendix P hierarchy producer gate."""
    report_path = run_hierarchy_producer_evaluation(
        load_settings().data_root,
        evaluation,
    )
    typer.echo(f"hierarchy_producer_report={report_path}")


@canonicalize_app.command("run-document")
def run_canonical_document(
    config: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Reviewed document-scoped canonicalization configuration.",
        ),
    ] = DEFAULT_CANONICALIZATION_SPEC,
) -> None:
    """Publish or checksum-verify the Task 03D Appendix P core candidate."""
    completion_path = run_document_canonicalization(
        load_settings().data_root,
        config,
    )
    typer.echo(f"canonicalization_completion={completion_path}")


@hierarchy_app.command("correct-document")
def correct_document_hierarchy(
    config: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Reviewed deterministic hierarchy-correction configuration.",
        ),
    ] = DEFAULT_HIERARCHY_CORRECTION_SPEC,
) -> None:
    """Publish or exactly reuse one Task 03E.2 correction candidate."""
    completion_path = run_hierarchy_correction(load_settings().data_root, config)
    typer.echo(f"hierarchy_correction_completion={completion_path}")


@hierarchy_app.command("prepare-heldout")
def prepare_hierarchy_heldout(
    config: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Reviewed deterministic hierarchy-correction configuration.",
        ),
    ] = DEFAULT_HIERARCHY_CORRECTION_SPEC,
) -> None:
    """Prepare source-only held-out renders and an incomplete annotation template."""
    template_path = prepare_held_out_review(
        data_root=load_settings().data_root,
        config_path=config,
    )
    typer.echo(f"held_out_template={template_path}")


@hierarchy_app.command("seal-heldout")
def seal_hierarchy_heldout(
    completed_template: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Completed source-only held-out annotation template.",
        ),
    ],
    config: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Reviewed deterministic hierarchy-correction configuration.",
        ),
    ] = DEFAULT_HIERARCHY_CORRECTION_SPEC,
) -> None:
    """Validate and checksum-seal completed held-out annotations."""
    seal = seal_held_out_annotations(
        data_root=load_settings().data_root,
        config_path=config,
        completed_template_path=completed_template,
    )
    typer.echo(f"held_out_annotations={seal.annotations_path}")
    typer.echo(f"held_out_seal={seal.seal_path}")


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
