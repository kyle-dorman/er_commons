"""Verify and load the already-materialized inputs consumed by Gate A."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import (
    canonical_json_sha256,
    iter_jsonl,
    read_json_object,
    sha256_file,
)
from er_commons.chunked_conversion.qualification.diagnostics import require
from er_commons.chunked_conversion.qualification.gate_a_profile import (
    SOURCE_CONVERSION_ID,
)
from er_commons.document_parsing.content_parsing.conversion_seal import (
    ConversionCompletion,
)
from er_commons.document_parsing.content_parsing.evidence import verify_inventory


@dataclass(frozen=True)
class GateAInputs:
    """Verified, already-materialized G1 payloads consumed by Gate A."""

    document: dict[str, Any]
    overlay: list[dict[str, Any]]
    alignment: list[dict[str, Any]]
    asset_inventory: dict[str, Any]
    producer_root: Path


def verify_source_identity(source_root: Path) -> dict[str, Any]:
    """Deep-verify the sealed G1 bundle and return its identity payload."""
    completion_path = source_root / "records/completion_record.json"
    inventory_path = source_root / "records/artifact_inventory.json"
    completion = ConversionCompletion.model_validate_json(completion_path.read_bytes())
    require(
        completion.conversion_id == SOURCE_CONVERSION_ID,
        "source_conversion_identity",
        stage="gate_a_inputs",
        path=str(completion_path),
        expected=SOURCE_CONVERSION_ID,
        actual=completion.conversion_id,
    )
    require(
        completion.artifact_inventory_sha256 == sha256_file(inventory_path),
        "source_inventory_seal",
        stage="gate_a_inputs",
        path=str(inventory_path),
        expected=completion.artifact_inventory_sha256,
        actual=sha256_file(inventory_path),
    )
    inventory = read_json_object(inventory_path)
    verify_inventory(source_root, inventory)
    identity_record_path = source_root / "records/conversion_identity.json"
    identity_record = read_json_object(identity_record_path)
    identity = identity_record.get("identity")
    if not isinstance(identity, dict):
        raise ValueError(f"conversion identity payload is invalid: {identity_record_path}")
    derived = f"dconv1-{canonical_json_sha256(identity)}"
    require(
        identity_record.get("conversion_id") == SOURCE_CONVERSION_ID
        and derived == SOURCE_CONVERSION_ID,
        "source_identity_derivation",
        stage="gate_a_inputs",
        path=str(identity_record_path),
        expected=SOURCE_CONVERSION_ID,
        actual={"recorded": identity_record.get("conversion_id"), "derived": derived},
    )
    return identity


def load_materialized_inputs(source_root: Path) -> GateAInputs:
    """Load stable G1 JSON/JSONL outputs without opening the source PDF."""
    producer = source_root / "documents/deir_appendix_g1/producer"
    document_path = producer / "docling/document.json"
    with document_path.open(encoding="utf-8") as stream:
        document = json.load(stream)
    if not isinstance(document, dict):
        raise ValueError(f"document is not an object: {document_path}")
    return GateAInputs(
        document=document,
        overlay=list(iter_jsonl(producer / "docling/heading_overlay.jsonl")),
        alignment=list(iter_jsonl(producer / "docling/alignment_pages.jsonl")),
        asset_inventory=read_json_object(producer / "asset_inventory.json"),
        producer_root=producer,
    )
