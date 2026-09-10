"""Export durable producer assets and verify completed immutable runs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import (
    artifact_inventory,
    sha256_file,
    write_json_atomic,
    write_json_atomic_streaming,
    write_jsonl,
)
from er_commons.artifact_verification import VerificationBudget
from er_commons.document_parsing.content_parsing.identity import canonical_json_sha256
from er_commons.document_parsing.content_parsing.records import (
    CompletionRecord,
    ProducerSummary,
)
from er_commons.document_parsing.heading_evidence_parsing.alignment_projection import (
    write_result_alignment_projection,
)
from er_commons.document_parsing.heading_evidence_parsing.heading_overlay import (
    split_heading_overlay,
)


class CompletedRunInvariantError(ValueError):
    """A named invariant of an immutable completed run failed."""

    def __init__(self, invariant: str, detail: str) -> None:
        super().__init__(f"completed-run invariant failed [{invariant}]: {detail}")
        self.invariant = invariant


def _require(invariant: str, condition: bool, detail: str) -> None:
    if not condition:
        raise CompletedRunInvariantError(invariant, detail)


def export_durable_result(
    result: Any,
    producer_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Save semantic Docling evidence while externalizing memory-heavy raster payloads."""
    docling_root = producer_root / "docling"
    docling_root.mkdir(parents=True, exist_ok=False)
    document = result.document
    assets = _export_picture_assets(document, producer_root)
    externalization = _externalize_embedded_images(document)
    heading_document = document.export_to_dict()
    document_payload, heading_overlay = split_heading_overlay(heading_document)
    write_json_atomic_streaming(docling_root / "document.json", document_payload)
    write_jsonl(docling_root / "heading_overlay.jsonl", heading_overlay)
    write_result_alignment_projection(result, docling_root / "alignment_pages.jsonl")
    write_json_atomic(
        producer_root / "asset_inventory.json",
        {"assets": assets, "image_externalization": externalization},
    )
    return document_payload, assets


def _export_picture_assets(document: Any, producer_root: Path) -> list[dict[str, Any]]:
    """Persist every available figure crop before its in-memory image is released."""
    from docling_core.types.doc.items.picture.picture import PictureItem

    assets_root = producer_root.parent / "assets"
    (assets_root / "figures").mkdir(parents=True, exist_ok=True)
    (assets_root / "images").mkdir(parents=True, exist_ok=True)
    assets: list[dict[str, Any]] = []
    for index, (item, _level) in enumerate(document.iterate_items(), start=1):
        if not isinstance(item, PictureItem):
            continue
        image = item.get_image(document)
        if image is None:
            continue
        page_number = int(item.prov[0].page_no) if item.prov else 0
        path = assets_root / "figures" / f"p{page_number:05d}_figure_{index:05d}.png"
        image.save(path, "PNG")
        assets.append(
            {
                "asset_role": "figure",
                "physical_pdf_page": page_number,
                "raw_object_ref": str(item.self_ref),
                "path": path.relative_to(producer_root.parents[2]).as_posix(),
                "byte_size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return assets


def _externalize_embedded_images(document: Any) -> dict[str, Any]:
    """Remove page renders and in-object picture rasters after figure publication."""
    page_count = 0
    for page in document.pages.values():
        if page.image is not None:
            page_count += 1
            page.image = None
    picture_count = 0
    for picture in document.pictures:
        if picture.image is not None:
            picture_count += 1
            picture.image = None
    return {
        "contract_version": "er_commons.docling_image_externalization.v1",
        "embedded_page_images_removed": page_count,
        "embedded_picture_images_removed": picture_count,
        "figure_crops_preserved_as_assets": True,
        "full_page_renders_preserved": False,
    }


def verify_inventory(root: Path, inventory: dict[str, Any]) -> None:
    """Verify every immutable completed-run file named by its inventory."""
    records = _validated_inventory_records(inventory)
    verify_inventory_metadata(root, inventory)
    for relative, _byte_size, expected_sha256 in records:
        _require(
            "inventory_file_checksum",
            sha256_file(root / relative) == expected_sha256,
            f"checksum changed: {relative}",
        )


def verify_inventory_metadata(root: Path, inventory: dict[str, Any]) -> None:
    """Verify exact managed paths and sizes without rereading immutable payload bytes."""
    records = _validated_inventory_records(inventory)
    expected: dict[str, int] = {}
    for relative, byte_size, _sha256 in records:
        path = root / relative
        _require(
            "contained_inventory_path",
            path.resolve().is_relative_to(root.resolve()),
            f"escaping symlink: {relative}",
        )
        _require("inventory_file_exists", path.is_file(), f"missing: {relative}")
        expected[relative.as_posix()] = byte_size
        _require(
            "inventory_file_size",
            path.stat().st_size == byte_size,
            f"byte size changed: {relative}",
        )
    excluded = {
        "records/artifact_inventory.json",
        "records/completion_record.json",
    }
    actual = {
        path.relative_to(root).as_posix(): path.stat().st_size
        for path in root.rglob("*")
        if path.is_file() and path.relative_to(root).as_posix() not in excluded
    }
    _require("complete_file_set", actual == expected, "inventory differs from actual files")


def _validated_inventory_records(
    inventory: object,
) -> list[tuple[Path, int, str]]:
    """Validate the complete small inventory record before trusting payload digests."""
    _require(
        "inventory_shape",
        isinstance(inventory, dict) and set(inventory) == {"file_count", "byte_count", "files"},
        "expected exactly file_count, byte_count, and files",
    )
    assert isinstance(inventory, dict)
    raw_files = inventory.get("files")
    _require("inventory_files", isinstance(raw_files, list), "files is not a list")
    assert isinstance(raw_files, list)
    records: list[tuple[Path, int, str]] = []
    seen: set[str] = set()
    for index, raw_record in enumerate(raw_files):
        _require(
            "inventory_file_record",
            isinstance(raw_record, dict) and set(raw_record) == {"path", "sha256", "byte_size"},
            f"invalid file record at index {index}",
        )
        record = raw_record
        relative_value = record.get("path")
        byte_size = record.get("byte_size")
        sha256 = record.get("sha256")
        _require(
            "inventory_file_path",
            isinstance(relative_value, str) and bool(relative_value),
            f"invalid path at index {index}",
        )
        relative = Path(relative_value)
        _require(
            "safe_inventory_path",
            not relative.is_absolute() and ".." not in relative.parts,
            f"unsafe path: {relative}",
        )
        normalized = relative.as_posix()
        _require(
            "unique_inventory_path",
            normalized not in seen,
            f"duplicate path: {normalized}",
        )
        _require(
            "inventory_file_size_value",
            isinstance(byte_size, int) and not isinstance(byte_size, bool) and byte_size >= 0,
            f"invalid byte size: {normalized}",
        )
        _require(
            "inventory_file_digest",
            isinstance(sha256, str) and re.fullmatch(r"[0-9a-f]{64}", sha256) is not None,
            f"invalid SHA-256: {normalized}",
        )
        seen.add(normalized)
        records.append((relative, byte_size, sha256))
    declared_count = inventory.get("file_count")
    _require(
        "inventory_file_count",
        isinstance(declared_count, int)
        and not isinstance(declared_count, bool)
        and declared_count == len(records),
        f"declared={declared_count}, observed={len(records)}",
    )
    observed_bytes = sum(record[1] for record in records)
    declared_bytes = inventory.get("byte_count")
    _require(
        "inventory_byte_count",
        isinstance(declared_bytes, int)
        and not isinstance(declared_bytes, bool)
        and declared_bytes == observed_bytes,
        f"declared={declared_bytes}, observed={observed_bytes}",
    )
    return records


def verify_inventory_for_reuse(
    root: Path,
    inventory: dict[str, Any],
    *,
    checksum_limit_bytes: int = 64 * 1024 * 1024,
) -> None:
    """Verify closure and small files while trusting sealed digests for large payloads."""
    verify_inventory_metadata(root, inventory)
    for relative, byte_size, expected_sha256 in _validated_inventory_records(inventory):
        if byte_size > checksum_limit_bytes:
            continue
        _require(
            "inventory_file_checksum",
            sha256_file(root / relative) == expected_sha256,
            f"checksum changed: {relative}",
        )


def verify_completed_run(root: Path, producer_run_id: str) -> Path:
    """Verify a matching completed output before permitting reuse."""
    completion_path = root / "records" / "completion_record.json"
    inventory_path = root / "records" / "artifact_inventory.json"
    _require(
        "terminal_records_exist",
        completion_path.is_file() and inventory_path.is_file(),
        f"completion or inventory missing below {root}",
    )
    completion = CompletionRecord.model_validate_json(completion_path.read_bytes())
    inventory = json.loads(inventory_path.read_text())
    identity_path = root / "records" / "producer_identity.json"
    summary_path = root / "records" / "producer_summary.json"
    _require(
        "identity_and_summary_exist",
        identity_path.is_file() and summary_path.is_file(),
        "identity or summary is missing",
    )
    identity_record = json.loads(identity_path.read_text())
    summary = ProducerSummary.model_validate_json(summary_path.read_bytes())
    recomputed_id = f"prv1-{canonical_json_sha256(identity_record['identity'])}"
    _require(
        "derived_run_id",
        recomputed_id == producer_run_id,
        "identity payload does not derive the requested run ID",
    )
    _require(
        "completion_run_id",
        completion.producer_run_id == producer_run_id,
        "completion run ID differs",
    )
    _require(
        "completion_inventory_seal",
        completion.artifact_inventory_sha256 == sha256_file(inventory_path),
        "completion does not seal the inventory",
    )
    verify_inventory_for_reuse(root, inventory)
    _require(
        "summary_run_id",
        summary.producer_run_id == producer_run_id,
        "summary run ID differs",
    )
    _require(
        "terminal_status",
        completion.producer_status == summary.producer_status,
        "completion and summary status differ",
    )
    _require(
        "summary_source",
        completion.source_id == summary.source_id,
        "completion and summary source differ",
    )
    _require(
        "identity_source",
        completion.source_id == identity_record["identity"]["source"]["source_id"],
        "completion and identity source differ",
    )
    _require(
        "identity_source_checksum",
        completion.source_sha256 == identity_record["identity"]["source"]["sha256"],
        "completion and identity source checksum differ",
    )
    _require(
        "identity_manifest_checksum",
        completion.source_manifest_sha256
        == identity_record["identity"]["sealed_release"]["manifest_sha256"],
        "completion and identity manifest checksum differ",
    )
    return completion_path


def write_inventory(root: Path) -> Path:
    """Write the non-self-referential completed-run artifact inventory."""
    path = root / "records" / "artifact_inventory.json"
    payload = artifact_inventory(
        root,
        excluded={
            "records/artifact_inventory.json",
            "records/completion_record.json",
        },
    )
    write_json_atomic(path, payload)
    return path


def read_accepted_inventory(
    root: Path,
    *,
    expected_sha256: str,
    source_id: str,
    budget: VerificationBudget,
) -> dict[str, Any]:
    """Check a historical inventory seal and closure without hashing payloads."""
    path = root / "records/artifact_inventory.json"
    inventory = cast(
        dict[str, Any],
        budget.read_json(path, role="managed_inventory", source_id=source_id, root=root),
    )
    if path.stat().st_size <= 1_048_576:
        observed = budget.hash_file(path, role="managed_inventory", source_id=source_id, root=root)
        _require(
            "completion_inventory_seal", observed == expected_sha256, f"source={source_id}: {path}"
        )
    else:
        budget.observations.append(
            {
                "source_id": source_id,
                "role": "managed_inventory",
                "path": str(path),
                "recorded_digest": expected_sha256,
                "verification_mode": "metadata_checked",
                "limitation": "oversized inventory digest not freshly verified",
            }
        )
    verify_inventory_metadata(root, inventory)
    return inventory


def read_accepted_producer(
    root: Path,
    producer_run_id: str,
    *,
    budget: VerificationBudget,
    source_id: str,
) -> dict[str, Any]:
    """Consume the recorded producer identity without deriving today's recipe."""
    completion_path = root / "records/completion_record.json"
    completion = CompletionRecord.model_validate(
        budget.read_json(completion_path, role="completion", source_id=source_id, root=root)
    )
    budget.hash_file(completion_path, role="completion", source_id=source_id, root=root)
    identity_path = root / "records/producer_identity.json"
    record = cast(
        dict[str, Any],
        budget.read_json(identity_path, role="identity_preimage", source_id=source_id, root=root),
    )
    identity_digest = budget.hash_file(
        identity_path, role="identity_preimage", source_id=source_id, root=root
    )
    _require(
        "identity_record_id",
        record.get("producer_run_id") == producer_run_id,
        f"source={source_id}: identity record ID differs",
    )
    identity = record["identity"]
    _require(
        "terminal_status",
        completion.producer_status in {"complete", "complete_with_warnings"},
        f"source={source_id}: producer is not terminal",
    )
    _require(
        "derived_run_id",
        f"prv1-{canonical_json_sha256(identity)}" == producer_run_id,
        f"source={source_id}: recorded producer preimage differs",
    )
    _require(
        "completion_run_id",
        completion.producer_run_id == producer_run_id,
        f"source={source_id}: completion identity differs",
    )
    _require(
        "identity_schema",
        identity.get("identity_schema_version")
        in {"er_commons.routing_table_identity.v2", "er_commons.content_parsing_identity.v1"},
        f"source={source_id}: unsupported producer identity schema",
    )
    _require(
        "identity_source",
        completion.source_id == identity["source"]["source_id"] == source_id,
        f"source={source_id}: source differs",
    )
    _require(
        "identity_source_checksum",
        completion.source_sha256 == identity["source"]["sha256"],
        f"source={source_id}: source checksum differs",
    )
    _require(
        "identity_manifest_checksum",
        completion.source_manifest_sha256 == identity["sealed_release"]["manifest_sha256"],
        f"source={source_id}: manifest differs",
    )
    inventory = read_accepted_inventory(
        root,
        expected_sha256=completion.artifact_inventory_sha256,
        source_id=source_id,
        budget=budget,
    )
    require_compact_identity_seal(inventory, "records/producer_identity.json", identity_digest)
    _require(
        "required_producer_summary",
        any(row["path"] == "records/producer_summary.json" for row in inventory["files"]),
        f"source={source_id}: summary is not managed",
    )
    summary = ProducerSummary.model_validate(
        budget.read_json(
            root / "records/producer_summary.json",
            role="producer_summary",
            source_id=source_id,
            root=root,
        )
    )
    _require(
        "summary_identity",
        summary.producer_run_id == producer_run_id and summary.source_id == source_id,
        f"source={source_id}: summary identity differs",
    )
    _require(
        "summary_status",
        summary.producer_status == completion.producer_status and summary.error_count == 0,
        f"source={source_id}: summary status differs",
    )
    _require(
        "summary_page_count",
        summary.physical_page_count == identity["source"]["pdf_page_count"],
        f"source={source_id}: summary page count differs",
    )
    return {
        "producer_run_id": producer_run_id,
        "identity": identity,
        "completion": completion.model_dump(mode="json"),
        "inventory": inventory,
        "verification_mode": "metadata_checked",
    }


def require_compact_identity_seal(inventory: dict[str, Any], relative: str, digest: str) -> None:
    """Reconcile a freshly hashed compact identity with its recorded inventory digest."""
    selected = [row for row in inventory["files"] if row["path"] == relative]
    _require(
        "identity_inventory_seal",
        len(selected) == 1 and selected[0]["sha256"] == digest,
        f"identity preimage digest differs from managed inventory: {relative}",
    )
