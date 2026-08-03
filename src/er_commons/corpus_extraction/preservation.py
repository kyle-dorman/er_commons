"""Offline preservation proof for imported immutable document candidates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_extraction.identity import canonical_digest
from er_commons.source_freeze import sha256_file


@dataclass(frozen=True)
class PreservationReport:
    """Exact path/byte comparison grouped by accepted candidate roles."""

    status: str
    file_count: int
    record_count: int
    asset_count: int
    support_count: int
    warning_policy_count: int
    manifest_digest: str
    mismatches: tuple[str, ...]


def compare_imported_candidate(
    reference_root: Path, imported_content_root: Path
) -> PreservationReport:
    """Prove the stage-one content namespace is a byte-exact identity projection."""
    reference = _manifest(reference_root)
    imported = _manifest(imported_content_root)
    paths = sorted(set(reference) | set(imported))
    mismatches = tuple(path for path in paths if reference.get(path) != imported.get(path))
    return PreservationReport(
        status="exact" if not mismatches else "mismatch",
        file_count=len(reference),
        record_count=sum(path.endswith(".jsonl") for path in reference),
        asset_count=sum(
            path in {"canonical/assets.jsonl", "canonical/figures.jsonl", "canonical/images.jsonl"}
            or path.startswith("assets/")
            for path in reference
        ),
        support_count=sum(path.startswith("support/") for path in reference),
        warning_policy_count=sum(
            "warning" in path.lower()
            or "policy" in path.lower()
            or path
            in {
                "records/canonicalization_summary.json",
                "records/extraction_identity.json",
                "records/manifest.json",
                "support/bounded_control_verification.json",
                "support/cross_reference_summary.json",
            }
            for path in reference
        ),
        manifest_digest=canonical_digest(reference),
        mismatches=mismatches,
    )


def _manifest(root: Path) -> dict[str, dict[str, int | str]]:
    """Build an ordered path/size/checksum manifest for every immutable byte."""
    if not root.is_dir():
        raise FileNotFoundError(root)
    return {
        path.relative_to(root).as_posix(): {
            "byte_size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
