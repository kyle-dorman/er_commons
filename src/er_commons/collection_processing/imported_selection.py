"""Strict frozen selection of retained document candidates for a new collection."""

from __future__ import annotations

import hashlib
from pathlib import Path

from er_commons.collection_processing.authority_refs import (
    CollectionArtifactReference,
    CollectionArtifactResolver,
)
from er_commons.collection_processing.contract import JsonObject
from er_commons.collection_processing.selection_models import (
    ImportedDocumentSelection,
    SelectedDocumentCandidate,
)


def load_imported_document_selection(
    path: Path,
    *,
    expected_source_order: tuple[str, ...],
    expected_sha256: str,
    expected_byte_size: int,
    resolver: CollectionArtifactResolver,
) -> ImportedDocumentSelection:
    """Load a sealed manifest and verify every selected compact artifact in place."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("imported document selection is not a regular non-symlink file")
    raw = path.read_bytes()
    if len(raw) != expected_byte_size:
        raise ValueError("imported document selection byte size differs")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("imported document selection checksum differs")
    selection = ImportedDocumentSelection.model_validate_json(raw)
    if selection.ordered_source_ids != expected_source_order:
        raise ValueError("imported document selection differs from expected source order")
    production_identity = resolver.read_json(
        selection.document_production_identity_ref,
        expected_authority="document_input_root",
    )
    document_spec = resolver.read_json(
        selection.document_run_spec_ref,
        expected_authority="document_input_root",
    )
    production_id = production_identity.get("extraction_id")
    if (
        not isinstance(production_id, str)
        or document_spec.get("production_extraction_id") != production_id
    ):
        raise ValueError("imported document production identity and run spec differ")
    for candidate in selection.candidates:
        _verify_candidate(
            candidate,
            resolver,
            production_id=production_id,
            document_run_spec_ref=selection.document_run_spec_ref,
            document_input_root_relative_path=(selection.document_input_root_relative_path),
        )
    return selection


def _verify_candidate(
    candidate: SelectedDocumentCandidate,
    resolver: CollectionArtifactResolver,
    *,
    production_id: str,
    document_run_spec_ref: CollectionArtifactReference,
    document_input_root_relative_path: str,
) -> None:
    records = _candidate_records(candidate, resolver)
    for role in ("identity", "completion", "downstream"):
        value = records[role]
        if value.get("candidate_id") != candidate.candidate_id:
            raise ValueError(f"selected document {role} names a different candidate")
        if value.get("source") != candidate.source_identity.model_dump(mode="json"):
            raise ValueError(f"selected document {role} names a different source")
    identity = records["identity"]
    if identity.get("production_extraction_id") != production_id:
        raise ValueError("selected document identity names a different production")
    if identity.get("run_spec_sha256") != document_run_spec_ref.sha256:
        raise ValueError("selected document identity names a different run spec digest")
    resolved_spec = identity.get("resolved_spec_ref")
    if not isinstance(resolved_spec, dict) or not _embedded_ref_matches(
        resolved_spec,
        document_run_spec_ref,
        prefix=document_input_root_relative_path,
    ):
        raise ValueError("selected document identity names a different resolved spec")
    completion_inventory = records["completion"].get("candidate_inventory")
    candidate_inventory_path = candidate.candidate_inventory_ref.path
    publication_prefix = "document_publications/"
    if not candidate_inventory_path.startswith(publication_prefix):
        raise ValueError("selected document inventory is outside document publications")
    if not isinstance(completion_inventory, dict) or not _embedded_ref_matches(
        completion_inventory,
        candidate.candidate_inventory_ref,
        override_path=candidate_inventory_path.removeprefix(publication_prefix),
    ):
        raise ValueError("selected document completion inventory binding differs")
    identity_stages = identity.get("stage_completions")
    linked_stage = (
        identity_stages.get("linked_document") if isinstance(identity_stages, dict) else None
    )
    if not isinstance(linked_stage, dict) or not _embedded_ref_matches(
        linked_stage,
        candidate.linked_completion_ref,
        prefix=document_input_root_relative_path,
    ):
        raise ValueError("selected document identity linked completion binding differs")
    for role in ("linked_identity", "linked_completion"):
        value = records[role]
        if value.get("candidate_id", value.get("extraction_id")) != candidate.linked_candidate_id:
            raise ValueError(f"selected document {role} names a different linked candidate")
    replacement = records["downstream"].get("replacement_linked_document_completion_ref")
    if not isinstance(replacement, dict):
        raise ValueError("selected downstream replay lacks its linked completion binding")
    if not _embedded_ref_matches(
        replacement,
        candidate.linked_completion_ref,
        prefix=document_input_root_relative_path,
    ):
        raise ValueError("selected downstream replay linked completion seal differs")
    for role in ("inventory", "linked_inventory"):
        value = records[role]
        files = value.get("files")
        if not isinstance(files, list):
            raise ValueError(f"selected document {role} lacks a managed file list")
    resolver.verify_managed_inventory(
        root_relative_path=candidate.candidate_root,
        inventory=records["inventory"],
        expected_authority="document_input_root",
    )
    linked_completion = records["linked_completion"]
    if linked_completion.get("artifact_inventory_sha256") != candidate.linked_inventory_ref.sha256:
        raise ValueError("selected linked completion inventory binding differs")
    resolver.verify_managed_inventory(
        root_relative_path=candidate.linked_candidate_root,
        inventory=records["linked_inventory"],
        expected_authority="document_input_root",
    )


def _candidate_records(
    candidate: SelectedDocumentCandidate,
    resolver: CollectionArtifactResolver,
) -> dict[str, JsonObject]:
    """Read the exact compact evidence named by one selected candidate."""
    refs = {
        "identity": candidate.document_identity_ref,
        "completion": candidate.document_completion_ref,
        "inventory": candidate.candidate_inventory_ref,
        "downstream": candidate.downstream_replay_ref,
        "linked_identity": candidate.linked_identity_ref,
        "linked_completion": candidate.linked_completion_ref,
        "linked_inventory": candidate.linked_inventory_ref,
    }
    return {
        role: resolver.read_json(ref, expected_authority="document_input_root")
        for role, ref in refs.items()
    }


def _embedded_ref_matches(
    embedded: JsonObject,
    selected: CollectionArtifactReference,
    *,
    prefix: str | None = None,
    override_path: str | None = None,
) -> bool:
    """Compare the path and digest shared by historical and authority-aware refs."""
    path = override_path or selected.path
    if prefix is not None:
        path = f"{prefix}/{path}"
    return embedded.get("path") == path and embedded.get("sha256") == selected.sha256


__all__ = [
    "ImportedDocumentSelection",
    "SelectedDocumentCandidate",
    "load_imported_document_selection",
]
