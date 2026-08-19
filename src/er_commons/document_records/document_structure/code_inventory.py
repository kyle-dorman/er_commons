"""Narrow code and dependency ownership for document-structure identity."""

from __future__ import annotations

from importlib.metadata import version
from pathlib import Path


def owned_code_paths(project_root: Path, config_path: Path) -> tuple[Path, ...]:
    """Return code and contracts that can change document-structure bytes."""
    package = project_root / "src/er_commons/document_records/document_structure"
    paths = {path.resolve() for path in package.rglob("*.py")}
    cross_owner_modules = (
        "src/er_commons/artifact_io.py",
        "src/er_commons/document_parsing/content_parsing/evidence.py",
        "src/er_commons/document_parsing/content_parsing/records.py",
        "src/er_commons/document_parsing/content_parsing/references.py",
        "src/er_commons/document_parsing/heading_evidence_parsing/document.py",
        "src/er_commons/document_parsing/heading_evidence_parsing/heading_overlay.py",
        "src/er_commons/document_records/record_mapping/candidate_identity.py",
        "src/er_commons/document_records/record_mapping/errors.py",
        "src/er_commons/document_records/record_mapping/identity.py",
        "src/er_commons/document_records/record_mapping/provenance.py",
        "src/er_commons/document_records/record_mapping/publication.py",
        "src/er_commons/document_records/record_mapping/record_sets.py",
        "src/er_commons/document_records/record_mapping/table_artifacts.py",
        "src/er_commons/document_records/record_mapping/table_cleanup.py",
        "src/er_commons/document_records/record_mapping/table_families.py",
        "src/er_commons/document_records/record_mapping/table_projection.py",
        "src/er_commons/document_records/record_mapping/table_records.py",
        "src/er_commons/document_records/record_mapping/table_regions.py",
        "src/er_commons/document_records/record_mapping/tables.py",
    )
    paths.update(
        {
            *((project_root / relative).resolve() for relative in cross_owner_modules),
            config_path.resolve(),
            (project_root / "docs/specs/semantic_structure_v2.md").resolve(),
            (
                project_root
                / (
                    "benchmarks/er_bench/schemas/canonical_extraction/v2/"
                    "semantic_structure.schema.json"
                )
            ).resolve(),
        }
    )
    return tuple(sorted(paths))


def runtime_dependency_versions() -> dict[str, str]:
    """Bind only third-party runtimes used by document-structure construction."""
    return {name: version(name) for name in ("jsonschema", "pydantic", "rfc8785")}
