"""Bundle identity, serialization, and scope policies."""

from __future__ import annotations

from collections import Counter

from er_commons.document_records.record_mapping.bundle import (
    BundleView,
    find_key,
    ids,
    references,
    typed_references,
)
from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.identifiers import (
    has_valid_local_key,
    record_type,
)
from er_commons.document_records.record_mapping.identity import extraction_identity_sha256
from er_commons.document_records.record_mapping.layout import RECORD_COLLECTIONS

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
        raise MappingContractError("extraction identity and manifest digest differ")


def record_ids_are_unique_and_well_formed(view: BundleView) -> None:
    """Reject collisions, misplaced records, and invalid local prefixes."""
    duplicates = sorted(
        record_id for record_id, count in Counter(ids(view.records)).items() if count > 1
    )
    if duplicates:
        raise MappingContractError(f"duplicate record IDs: {duplicates}")

    extraction_id = view.bundle["manifest"]["extraction_id"]
    for collection in RECORD_COLLECTIONS:
        for record in view.bundle[collection.bundle_key]:
            if f"/{collection.record_type}/" not in record["id"]:
                raise MappingContractError(
                    f"{collection.bundle_key} contains a wrong-type record ID"
                )
            if not has_valid_local_key(record["id"], collection.record_type):
                raise MappingContractError(f"{collection.bundle_key} contains an invalid local ID")
            if record["extraction_id"] != extraction_id or not record["id"].startswith(
                f"{extraction_id}/"
            ):
                raise MappingContractError(f"record escaped extraction scope: {record['id']}")


def human_review_fields_are_absent(view: BundleView) -> None:
    """Keep Task 04 judgments out of machine extraction records."""
    forbidden_path = find_key(view.bundle, FORBIDDEN_HUMAN_REVIEW_FIELDS)
    if forbidden_path is not None:
        raise MappingContractError(f"human-review field at {forbidden_path}")


def references_exist_and_have_expected_types(view: BundleView) -> None:
    """Require every relationship to resolve to an allowed record family."""
    known_ids = set(view.records_by_id)
    for record in view.records:
        missing = sorted(set(references(record)) - known_ids)
        if missing:
            raise MappingContractError(f"unknown references from {record['id']}: {missing}")
        for target_id, allowed_types in typed_references(record):
            if record_type(target_id) not in allowed_types:
                raise MappingContractError(f"wrong-type reference from {record['id']}: {target_id}")


def manifest_matches_serialized_records(view: BundleView) -> None:
    """Match manifest order and counts to the materialized collections."""
    manifest = view.bundle["manifest"]
    document_ids = set(ids(view.bundle["documents"]))
    missing_documents = set(manifest["ordered_document_ids"]) - document_ids
    if missing_documents:
        raise MappingContractError(f"manifest references unknown documents: {missing_documents}")

    expected_types = [item.record_type.replace("-", "_") for item in RECORD_COLLECTIONS]
    actual_types = [item["record_type"] for item in manifest["record_files"]]
    if actual_types != expected_types:
        raise MappingContractError("manifest record files are not in canonical order")

    for file_record, collection in zip(manifest["record_files"], RECORD_COLLECTIONS, strict=True):
        if file_record["record_count"] != len(view.bundle[collection.bundle_key]):
            raise MappingContractError(f"record count mismatch for {collection.bundle_key}")


def source_release_matches_documents(view: BundleView) -> None:
    """Match selected documents to their entries in the full frozen release."""
    identity_release = view.bundle["identity"]["source_release"]
    materialization_scope = view.bundle["identity"]["materialization_scope"]
    manifest = view.bundle["manifest"]
    release_sources = {
        source["source_id"]: source for source in identity_release["ordered_model_corpus"]
    }
    selected_source_ids = materialization_scope["ordered_source_ids"]
    document_source_ids = [document["source_id"] for document in view.bundle["documents"]]
    if selected_source_ids != document_source_ids:
        raise MappingContractError("materialization scope differs from canonical documents")

    missing_release_sources = [
        source_id for source_id in selected_source_ids if source_id not in release_sources
    ]
    if missing_release_sources:
        raise MappingContractError(
            f"materialization scope references unknown release sources: {missing_release_sources}"
        )

    for document in view.bundle["documents"]:
        release_source = release_sources[document["source_id"]]
        if (
            document["source_sha256"] != release_source["sha256"]
            or document["page_count"] != release_source["pdf_page_count"]
        ):
            raise MappingContractError(
                f"canonical document differs from release source: {document['source_id']}"
            )

    producer_source_ids = [
        producer_run["source_id"] for producer_run in materialization_scope["producer_runs"]
    ]
    if producer_source_ids != selected_source_ids:
        raise MappingContractError("producer run order differs from materialization scope")

    release_fields = (
        "source_release_version",
        "source_manifest_path",
        "source_manifest_sha256",
    )
    if any(identity_release[field] != manifest[field] for field in release_fields):
        raise MappingContractError("identity source release differs from manifest")


def document_pages_are_complete(view: BundleView) -> None:
    """Match page counts and ordered page IDs to each document record."""
    page_counts = Counter(page["document_id"] for page in view.bundle["pages"])
    for document in view.bundle["documents"]:
        document_id = document["id"]
        if page_counts[document_id] != document["page_count"]:
            raise MappingContractError(f"page count mismatch for {document_id}")
        actual_page_ids = [
            page["id"] for page in view.bundle["pages"] if page["document_id"] == document_id
        ]
        if document["page_ids"] != actual_page_ids:
            raise MappingContractError(f"page IDs differ for {document_id}")


def source_edition_overrides_propagate(view: BundleView) -> None:
    """Copy source provenance exceptions exactly onto their pages."""
    for page in view.bundle["pages"]:
        document = view.documents_by_id[page["document_id"]]
        if page["source_edition_override"] != document["source_edition_override"]:
            raise MappingContractError("page source-edition override differs from its document")


def records_are_canonically_ordered(view: BundleView) -> None:
    """Enforce stable document, page, and per-document sequence order."""
    manifest_document_ids = view.bundle["manifest"]["ordered_document_ids"]
    if ids(view.bundle["documents"]) != manifest_document_ids:
        raise MappingContractError("documents are not in sealed manifest order")

    document_order = {document_id: index for index, document_id in enumerate(manifest_document_ids)}
    page_keys = [
        (document_order[page["document_id"]], page["physical_page_number"])
        for page in view.bundle["pages"]
    ]
    if page_keys != sorted(page_keys) or len(page_keys) != len(set(page_keys)):
        raise MappingContractError("pages are not in physical-page order")

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
                raise MappingContractError(f"{bundle_key} sequence is not strictly ordered")
