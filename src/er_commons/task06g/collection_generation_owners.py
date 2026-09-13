"""Explicit conservative owner boundary for collection-only recovery behavior."""

from __future__ import annotations

from pathlib import Path

from er_commons.task06g.core import JsonObject, reference

# Whole responsibility packages deliberately include their validators and observers.
# They are frozen as code, never invoked as document/source/model producers here.
OWNER_PACKAGES = (
    "src/er_commons/collection_processing",
    "src/er_commons/task06g",
    "src/er_commons/document_records/document_structure",
    "src/er_commons/document_records/document_references",
)
SUPPORT_OWNERS = (
    "src/er_commons/artifact_io.py",
    "src/er_commons/artifact_verification.py",
    "src/er_commons/authority_reference.py",
    "src/er_commons/cli.py",
    "src/er_commons/settings.py",
    "src/er_commons/source_family_catalog.py",
    "src/er_commons/document_publication/background_execution.py",
    "src/er_commons/document_publication/candidate_identity_validation.py",
    "src/er_commons/document_publication/candidates.py",
    "src/er_commons/document_publication/config.py",
    "src/er_commons/document_publication/downstream_replay_validation.py",
    "src/er_commons/document_publication/identity.py",
    "src/er_commons/document_publication/lifecycle.py",
    "src/er_commons/document_publication/observability.py",
    "src/er_commons/document_publication/outcomes.py",
    "src/er_commons/document_publication/process_observations.py",
    "src/er_commons/document_publication/production_identity.py",
    "src/er_commons/document_publication/published_document.py",
    "src/er_commons/document_publication/records.py",
    "src/er_commons/document_publication/retained_evidence.py",
    "src/er_commons/document_publication/storage.py",
    "src/er_commons/document_publication/config_generation/task06g_generation.py",
    "src/er_commons/document_records/record_mapping/errors.py",
    "src/er_commons/document_records/record_mapping/identity.py",
    "src/er_commons/document_records/record_mapping/publication.py",
)


def repository_control_ref(repository: Path, relative: str) -> JsonObject:
    """Hash only one explicitly named repository control or Python owner."""
    return {"authority": "repository", **reference(repository / relative, root=repository)}


def collection_owner_paths(repository: Path) -> list[str]:
    """Enumerate a reviewable complete owner set; new files invalidate the freeze."""
    paths = set(SUPPORT_OWNERS)
    for relative in OWNER_PACKAGES:
        paths.update(
            path.relative_to(repository).as_posix()
            for path in (repository / relative).rglob("*.py")
        )
    paths.update(
        path.relative_to(repository).as_posix()
        for path in (repository / "scripts").glob("*task06g*.py")
    )
    absent = sorted(path for path in paths if not (repository / path).is_file())
    if absent:
        raise ValueError(f"collection-only frozen owners are absent: {absent}")
    return sorted(paths)
