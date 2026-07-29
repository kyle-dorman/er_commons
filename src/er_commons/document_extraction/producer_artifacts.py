"""Export durable producer assets and verify completed immutable runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.document_extraction.artifacts import artifact_inventory
from er_commons.document_extraction.producer_identity import canonical_json_sha256
from er_commons.document_extraction.producer_records import (
    CompletionRecord,
    ProducerSummary,
)
from er_commons.source_freeze import sha256_file, write_json_atomic


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
    """Save lossless Docling records and picture crops without review renders."""
    from docling_core.types.doc.items.picture.picture import PictureItem

    docling_root = producer_root / "docling"
    docling_root.mkdir(parents=True, exist_ok=False)
    document = result.document
    document_payload = document.export_to_dict()
    write_json_atomic(docling_root / "document.json", document_payload)
    conversion_pages = {
        "pages": [page.model_dump(mode="json") for page in result.pages],
        "assembled": result.assembled.model_dump(mode="json"),
        "confidence": result.confidence.model_dump(mode="json"),
    }
    write_json_atomic(docling_root / "conversion_pages.json", conversion_pages)

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
    write_json_atomic(producer_root / "asset_inventory.json", {"assets": assets})
    return document_payload, assets


def verify_inventory(root: Path, inventory: dict[str, Any]) -> None:
    """Verify every immutable completed-run file named by its inventory."""
    for record in inventory.get("files", []):
        relative = Path(str(record["path"]))
        _require(
            "safe_inventory_path",
            not relative.is_absolute() and ".." not in relative.parts,
            f"unsafe path: {relative}",
        )
        path = root / relative
        _require("inventory_file_exists", path.is_file(), f"missing: {relative}")
        _require(
            "inventory_file_size",
            path.stat().st_size == record["byte_size"],
            f"byte size changed: {relative}",
        )
        _require(
            "inventory_file_checksum",
            sha256_file(path) == record["sha256"],
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
    verify_inventory(root, inventory)
    actual_inventory = artifact_inventory(
        root,
        excluded={
            "records/artifact_inventory.json",
            "records/completion_record.json",
        },
    )
    _require(
        "complete_file_set",
        actual_inventory == inventory,
        "inventory omits or differs from actual files",
    )
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
