"""Validate explicit original and replacement collection source bindings."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from er_commons.artifact_io import assert_contained
from er_commons.artifact_verification import VerificationBudget
from er_commons.collection_processing.config import CollectionRunSpec, CollectionSourceMembership
from er_commons.document_parsing.content_parsing.sources import load_sealed_manifest_metadata
from er_commons.document_publication.config import DocumentRunSpec
from er_commons.document_publication.sources import manifest_selection_for
from er_commons.source_release.models import SourceManifest, SourceRecord, SourceRole
from er_commons.source_release.retained_processing import validate_processing_source


def select_collection_sources(
    data_root: Path,
    collection_spec: CollectionRunSpec,
    document_spec: DocumentRunSpec,
    manifest: SourceManifest,
    budget: VerificationBudget,
) -> dict[str, SourceRecord]:
    """Select each physical member once while retaining original manifest bindings."""
    manifest_by_id = {record.source_id: record for record in manifest.sources}
    original_manifest_by_id = dict(manifest_by_id)
    original_manifest_digest = _original_manifest_digest(
        data_root, collection_spec, document_spec, budget
    )
    if collection_spec.source_membership:
        manifests = {
            (document_spec.source_release_version, document_spec.source_manifest_path): manifest
        }
        manifest_by_id = {}
        for member in collection_spec.source_membership:
            selected = manifest_selection_for(document_spec, member.physical_source_id)
            key = (selected.source_release_version, selected.source_manifest_path)
            if key not in manifests:
                manifests[key] = load_sealed_manifest_metadata(data_root, selected, budget)
            matches = [
                record
                for record in manifests[key].sources
                if record.source_id == member.physical_source_id
                and _role_matches_membership(record, member)
            ]
            if len(matches) != 1:
                raise ValueError(f"membership lacks one sealed source: {member.physical_source_id}")
            if member.logical_source_id == member.physical_source_id and key != (
                document_spec.source_release_version,
                document_spec.source_manifest_path,
            ):
                raise ValueError("unchanged membership must retain original source manifest")
            if member.substitution_relative_path is not None:
                validate_processing_source(data_root, manifests[key], matches[0])
                _verify_substitution(
                    data_root,
                    member,
                    matches[0],
                    original_manifest_by_id,
                    original_manifest_digest,
                    budget,
                )
            manifest_by_id[member.physical_source_id] = matches[0]
    return manifest_by_id


def _role_matches_membership(record: SourceRecord, member: CollectionSourceMembership) -> bool:
    """Keep ordinary members model-only and admit the explicit retained F1 exception."""
    if member.logical_source_id == member.physical_source_id:
        return record.source_role == SourceRole.MODEL_CORPUS
    return record.source_role == SourceRole.MODEL_CORPUS or (
        member.logical_source_id == "deir_appendix_f1"
        and member.substitution_relative_path is not None
        and record.source_role == SourceRole.QUALIFIED_SUBSTITUTE
    )


def _original_manifest_digest(
    data_root: Path,
    collection_spec: CollectionRunSpec,
    document_spec: DocumentRunSpec,
    budget: VerificationBudget,
) -> str | None:
    """Read the original completion's sealed digest only for replacement scopes."""
    original_manifest_digest: str | None = None
    if any(
        member.substitution_relative_path is not None
        for member in collection_spec.source_membership
    ):
        completion = budget.read_json(
            data_root / document_spec.source_manifest_path.parent / "completion_record.json",
            root=data_root,
            role="completion",
            source_id=document_spec.source_release_version,
        )
        if not isinstance(completion, dict) or not isinstance(completion.get("manifest"), dict):
            raise ValueError("original release completion lacks a manifest binding")
        sealed_manifest = completion["manifest"]
        assert isinstance(sealed_manifest, dict)
        original_manifest_digest = str(sealed_manifest["sha256"])
    return original_manifest_digest


def _verify_substitution(
    data_root: Path,
    member: CollectionSourceMembership,
    replacement_source: SourceRecord,
    original_manifest_by_id: dict[str, SourceRecord],
    original_manifest_digest: str | None,
    budget: VerificationBudget,
) -> None:
    """Bind the F1 exception to sealed 06C provenance and both source identities."""
    assert member.substitution_relative_path is not None
    substitution_path = assert_contained(data_root, member.substitution_relative_path.as_posix())
    evidence = budget.read_json(
        substitution_path,
        root=data_root,
        role="input_binding",
        source_id=member.logical_source_id,
    )
    if not isinstance(evidence, dict):
        raise ValueError("invalid F1 source substitution evidence")
    substitution = _substitution_record(evidence)
    if (
        substitution.get("schema_version") != "er_commons.recovery.source_substitution.v1"
        or substitution.get("logical_source_id") != member.logical_source_id
        or substitution.get("physical_source_id", member.physical_source_id)
        != member.physical_source_id
        or substitution.get("scope_exception") != "f1_only"
        or substitution.get("edition") != "final_eir"
        or substitution.get("edition_equivalence") != "not_established"
    ):
        raise ValueError("invalid F1 source substitution evidence")
    original_release = substitution.get("original_release_ref")
    wrong_source = substitution.get("wrong_source_ref")
    wrong_source_sha256 = substitution.get("wrong_source_sha256")
    if wrong_source_sha256 is None and isinstance(wrong_source, dict):
        wrong_source_sha256 = wrong_source.get("identity")
    original_source = original_manifest_by_id.get(member.logical_source_id)
    if (
        not isinstance(original_release, dict)
        or original_release.get("sha256", original_release.get("recorded_digest"))
        != original_manifest_digest
        or original_source is None
        or wrong_source_sha256 != original_source.sha256
    ):
        raise ValueError("F1 substitution original release/source binding differs")
    replacement = substitution.get("replacement_source_ref")
    if replacement is not None and (
        not isinstance(replacement, dict)
        or replacement.get("identity") != replacement_source.sha256
    ):
        raise ValueError("F1 substitution replacement digest differs from selected source")
    if evidence is not substitution:
        sources = evidence.get("sources")
        if (
            not isinstance(sources, list)
            or len(sources) != 1
            or not isinstance(sources[0], dict)
            or sources[0].get("source_id") != member.physical_source_id
            or sources[0].get("sha256") != replacement_source.sha256
        ):
            raise ValueError("sealed F1 manifest does not bind the selected replacement source")


def _substitution_record(evidence: Mapping[str, object]) -> Mapping[str, object]:
    """Select only the declared 06C aggregate provenance or a legacy standalone record."""
    if evidence.get("schema_version") == "er_commons.recovery.source_substitution.v1":
        return evidence
    aggregates = evidence.get("aggregates")
    if not isinstance(aggregates, dict):
        raise ValueError("F1 evidence lacks sealed substitution provenance")
    substitution = aggregates.get("substitution")
    if not isinstance(substitution, dict):
        raise ValueError("F1 evidence lacks sealed substitution provenance")
    acquisition = aggregates.get("acquisition_spec")
    if not isinstance(acquisition, dict) or acquisition.get("provenance") != substitution:
        raise ValueError("F1 manifest repeats inconsistent substitution provenance")
    return substitution
