"""Bundle identity, serialization, and scope policies."""

from __future__ import annotations

from collections import Counter

from er_commons.canonical_extraction.bundle import (
    BundleView,
    find_key,
    ids,
    references,
    typed_references,
)
from er_commons.canonical_extraction.errors import ContractError
from er_commons.canonical_extraction.identifiers import (
    has_valid_local_key,
    record_type,
)
from er_commons.canonical_extraction.identity import extraction_identity_sha256
from er_commons.canonical_extraction.layout import RECORD_COLLECTIONS

FORBIDDEN_HUMAN_REVIEW_FIELDS = {
    "reviewer",
    "review_date",
    "usability",
    "excluded",
    "disposition",
    "curator_note",
    "gold",
    "gold_label",
}


def identity_matches_manifest(view: BundleView) -> None:
    """Bind the manifest to the normative, content-addressed identity."""
    manifest = view.bundle["manifest"]
    identity = view.bundle["identity"]
    digest = extraction_identity_sha256(identity)
    extraction_id = f"exv1-{digest}"
    if not (
        identity["extraction_id"] == extraction_id
        and manifest["extraction_id"] == extraction_id
        and identity["identity_sha256"] == digest
        and manifest["identity_sha256"] == digest
    ):
        raise ContractError("extraction identity and manifest digest differ")


def record_ids_are_unique_and_well_formed(view: BundleView) -> None:
    """Reject collisions, misplaced records, and invalid local prefixes."""
    duplicates = sorted(
        record_id for record_id, count in Counter(ids(view.records)).items() if count > 1
    )
    if duplicates:
        raise ContractError(f"duplicate record IDs: {duplicates}")

    extraction_id = view.bundle["manifest"]["extraction_id"]
    for collection in RECORD_COLLECTIONS:
        for record in view.bundle[collection.bundle_key]:
            if f"/{collection.record_type}/" not in record["id"]:
                raise ContractError(f"{collection.bundle_key} contains a wrong-type record ID")
            if not has_valid_local_key(record["id"], collection.record_type):
                raise ContractError(f"{collection.bundle_key} contains an invalid local ID")
            if record["extraction_id"] != extraction_id or not record["id"].startswith(
                f"{extraction_id}/"
            ):
                raise ContractError(f"record escaped extraction scope: {record['id']}")


def human_review_fields_are_absent(view: BundleView) -> None:
    """Keep Task 04 judgments out of machine extraction records."""
    forbidden_path = find_key(view.bundle, FORBIDDEN_HUMAN_REVIEW_FIELDS)
    if forbidden_path is not None:
        raise ContractError(f"human-review field at {forbidden_path}")


def references_exist_and_have_expected_types(view: BundleView) -> None:
    """Require every relationship to resolve to an allowed record family."""
    known_ids = set(view.records_by_id)
    for record in view.records:
        missing = sorted(set(references(record)) - known_ids)
        if missing:
            raise ContractError(f"unknown references from {record['id']}: {missing}")
        for target_id, allowed_types in typed_references(record):
            if record_type(target_id) not in allowed_types:
                raise ContractError(f"wrong-type reference from {record['id']}: {target_id}")


def manifest_matches_serialized_records(view: BundleView) -> None:
    """Match manifest order and counts to the materialized collections."""
    manifest = view.bundle["manifest"]
    document_ids = set(ids(view.bundle["documents"]))
    missing_documents = set(manifest["ordered_document_ids"]) - document_ids
    if missing_documents:
        raise ContractError(f"manifest references unknown documents: {missing_documents}")

    expected_types = [item.record_type.replace("-", "_") for item in RECORD_COLLECTIONS]
    actual_types = [item["record_type"] for item in manifest["record_files"]]
    if actual_types != expected_types:
        raise ContractError("manifest record files are not in canonical order")

    for file_record, collection in zip(manifest["record_files"], RECORD_COLLECTIONS, strict=True):
        if file_record["record_count"] != len(view.bundle[collection.bundle_key]):
            raise ContractError(f"record count mismatch for {collection.bundle_key}")


def source_release_matches_documents(view: BundleView) -> None:
    """Match frozen source identity to manifest and canonical documents."""
    identity_release = view.bundle["identity"]["source_release"]
    manifest = view.bundle["manifest"]
    document_sources = [
        {
            "source_id": document["source_id"],
            "sha256": document["source_sha256"],
            "pdf_page_count": document["page_count"],
        }
        for document in view.bundle["documents"]
    ]
    if identity_release["ordered_model_corpus"] != document_sources:
        raise ContractError("identity source order differs from canonical documents")

    release_fields = (
        "source_release_version",
        "source_manifest_path",
        "source_manifest_sha256",
    )
    if any(identity_release[field] != manifest[field] for field in release_fields):
        raise ContractError("identity source release differs from manifest")


def document_pages_are_complete(view: BundleView) -> None:
    """Match page counts and ordered page IDs to each document record."""
    page_counts = Counter(page["document_id"] for page in view.bundle["pages"])
    for document in view.bundle["documents"]:
        document_id = document["id"]
        if page_counts[document_id] != document["page_count"]:
            raise ContractError(f"page count mismatch for {document_id}")
        actual_page_ids = [
            page["id"] for page in view.bundle["pages"] if page["document_id"] == document_id
        ]
        if document["page_ids"] != actual_page_ids:
            raise ContractError(f"page IDs differ for {document_id}")


def source_edition_overrides_propagate(view: BundleView) -> None:
    """Copy source provenance exceptions exactly onto their pages."""
    for page in view.bundle["pages"]:
        document = view.documents_by_id[page["document_id"]]
        if page["source_edition_override"] != document["source_edition_override"]:
            raise ContractError("page source-edition override differs from its document")


def records_are_canonically_ordered(view: BundleView) -> None:
    """Enforce stable document, page, and per-document sequence order."""
    manifest_document_ids = view.bundle["manifest"]["ordered_document_ids"]
    if ids(view.bundle["documents"]) != manifest_document_ids:
        raise ContractError("documents are not in sealed manifest order")

    document_order = {document_id: index for index, document_id in enumerate(manifest_document_ids)}
    page_keys = [
        (document_order[page["document_id"]], page["physical_page_number"])
        for page in view.bundle["pages"]
    ]
    if page_keys != sorted(page_keys) or len(page_keys) != len(set(page_keys)):
        raise ContractError("pages are not in physical-page order")

    sequenced_collections = (
        "sections",
        "blocks",
        "tables",
        "table_families",
        "figures",
        "images",
    )
    for bundle_key in sequenced_collections:
        sequences_by_document: dict[str, list[int]] = {}
        for record in view.bundle[bundle_key]:
            sequences_by_document.setdefault(record["document_id"], []).append(record["sequence"])
        for sequence in sequences_by_document.values():
            if sequence != list(range(1, len(sequence) + 1)):
                raise ContractError(f"{bundle_key} sequence is not strictly ordered")
