"""Production identity derivation and checked-artifact validation."""

from __future__ import annotations

from pathlib import Path

from er_commons.corpus_extraction_contract.checks import bytes_sha256, canonical_sha256, fail
from er_commons.corpus_extraction_contract.model import JsonObject

CONTRACT_SECTIONS = (
    "producer_contract",
    "canonical_contract",
    "hierarchy_contract",
    "cross_reference_contract",
    "corpus_workflow_contract",
)
PRODUCTION_SOURCE_COUNT = 35


def validate_production_identity(
    record: JsonObject,
    *,
    expected_source_ids: list[str] | None = None,
    expected_scope: JsonObject | None = None,
    project_root: Path | None = None,
) -> None:
    """Verify the production recipe, source order, and referenced current bytes."""
    preimage = record["preimage"]
    digest = canonical_sha256(preimage)
    if record["identity_sha256"] != digest or record["extraction_id"] != f"exv1-{digest}":
        fail("identity_digest", "production identity does not derive from its preimage")

    source_ids = preimage["production_scope"]["ordered_source_ids"]
    if len(source_ids) != PRODUCTION_SOURCE_COUNT or len(set(source_ids)) != len(source_ids):
        fail(
            "production_scope",
            f"production identity must contain {PRODUCTION_SOURCE_COUNT} unique sources",
        )
    if expected_source_ids is not None and source_ids != expected_source_ids:
        fail("production_scope", "production source order differs from sealed evidence")
    if expected_scope is not None:
        _validate_scope_evidence(preimage["production_scope"], expected_scope)
    if project_root is not None:
        _validate_referenced_artifacts(preimage, project_root)


def _validate_scope_evidence(scope: JsonObject, evidence: JsonObject) -> None:
    """Anchor identity fields to a separate checked production-scope record."""
    observed = {
        "source_release_version": scope["source_release_version"],
        "source_manifest_sha256": scope["source_manifest"]["sha256"],
        "release_completion_sha256": scope["release_completion"]["sha256"],
        "ordered_source_records_sha256": scope["ordered_source_records_sha256"],
    }
    if observed != evidence:
        fail("production_scope", "production scope differs from checked evidence")


def _validate_referenced_artifacts(preimage: JsonObject, project_root: Path) -> None:
    """Require every reviewable artifact reference in the fixture to match disk."""
    for section_name in CONTRACT_SECTIONS:
        section = preimage[section_name]
        references = [*section["artifacts"], *section["owned_code"]]
        for reference in references:
            relative_path = reference["path"]
            path = project_root / relative_path
            if not path.is_file() or bytes_sha256(path.read_bytes()) != reference["sha256"]:
                fail(
                    "identity_artifact",
                    "identity artifact differs from its declared checksum",
                    subject=relative_path,
                )
