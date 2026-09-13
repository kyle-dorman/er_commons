"""Construct collection evidence from an already verified imported selection."""

from __future__ import annotations

from er_commons.collection_processing.authority_refs import (
    CollectionArtifactReference,
    CollectionArtifactResolver,
)
from er_commons.collection_processing.contract import JsonObject
from er_commons.collection_processing.imported_selection import (
    ImportedDocumentSelection,
    SelectedDocumentCandidate,
)
from er_commons.document_publication.published_document import DocumentTerminalEvidence

_TARGET_RECORD_STREAMS = (
    "documents.jsonl",
    "sections.jsonl",
    "tables.jsonl",
    "figures.jsonl",
    "pages.jsonl",
)


def build_imported_terminal_evidence(
    selection: ImportedDocumentSelection,
    *,
    selection_ref: JsonObject,
    resolver: CollectionArtifactResolver,
) -> tuple[DocumentTerminalEvidence, ...]:
    """Build source-free evidence only from exact selected candidates."""
    evidence: list[DocumentTerminalEvidence] = []
    for candidate in selection.candidates:
        completion = resolver.read_json(
            candidate.document_completion_ref,
            expected_authority="document_input_root",
        )
        identity = resolver.read_json(
            candidate.document_identity_ref,
            expected_authority="document_input_root",
        )
        inventory = resolver.read_json(
            candidate.candidate_inventory_ref,
            expected_authority="document_input_root",
        )
        files = inventory.get("files")
        if not isinstance(files, list):
            raise ValueError("selected candidate inventory lacks managed files")
        by_path = {
            str(item.get("path")): item
            for item in files
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        }
        target_refs = tuple(
            _managed_ref(candidate, by_path, f"content/canonical/{name}")
            for name in _TARGET_RECORD_STREAMS
        )
        transaction_id = completion.get("transaction_id")
        disposition = identity.get("terminal_state")
        if not isinstance(transaction_id, str) or disposition not in {
            "complete",
            "complete_with_warnings",
        }:
            raise ValueError("selected candidate lacks successful terminal identity")
        evidence.append(
            DocumentTerminalEvidence(
                source=candidate.source_identity.model_dump(mode="json"),
                source_ordinal=candidate.source_ordinal,
                evidence_kind="downstream_replay",
                transaction_id=transaction_id,
                attempt=None,
                disposition=disposition,
                terminal_event_ref=None,
                attempt_record_ref=None,
                downstream_replay_ref=candidate.downstream_replay_ref.model_dump(mode="json"),
                failure_class=None,
                retained_evidence_refs=(),
                candidate_id=candidate.candidate_id,
                document_completion_ref=candidate.document_completion_ref.model_dump(mode="json"),
                candidate_inventory_ref=candidate.candidate_inventory_ref.model_dump(mode="json"),
                cross_references_ref=_managed_ref(
                    candidate, by_path, "content/canonical/cross_references.jsonl"
                ),
                target_aliases_ref=_managed_ref(
                    candidate, by_path, "content/canonical/target_aliases.jsonl"
                ),
                target_records_refs=target_refs,
                imported_selection_ref=selection_ref,
                imported_selection_entry_sha256=candidate.selection_sha256,
            )
        )
    return tuple(evidence)


def _managed_ref(
    candidate: SelectedDocumentCandidate,
    by_path: dict[str, JsonObject],
    relative: str,
) -> JsonObject:
    """Build one authority-aware ref from the sealed candidate inventory."""
    item = by_path.get(relative)
    if item is None:
        raise ValueError(f"selected candidate inventory lacks {relative}")
    sha256 = item.get("sha256")
    byte_size = item.get("byte_size")
    if not isinstance(sha256, str) or not isinstance(byte_size, int):
        raise ValueError(f"selected candidate inventory has an invalid ref for {relative}")
    return CollectionArtifactReference(
        authority="document_input_root",
        path=f"{candidate.candidate_root}/{relative}",
        sha256=sha256,
        byte_size=byte_size,
    ).model_dump(mode="json")


__all__ = ["build_imported_terminal_evidence"]
