"""Verify and audit immutable Docling conversion bundle seals."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict

from er_commons.artifact_io import read_json_object, sha256_file
from er_commons.artifact_verification import VerificationBudget
from er_commons.document_parsing.content_parsing.conversion import ConversionOutput
from er_commons.document_parsing.content_parsing.evidence import (
    CompletedRunInvariantError,
    read_accepted_inventory,
    require_compact_identity_seal,
    verify_inventory,
    verify_inventory_metadata,
)
from er_commons.document_parsing.content_parsing.records import ConversionObservation
from er_commons.document_parsing.heading_evidence_parsing.alignment_projection import (
    load_alignment_projection,
)


class _BundleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConversionCompletion(_BundleRecord):
    """Completion-last seal for one immutable Docling conversion bundle."""

    schema_version: Literal["er_commons.docling_conversion_completion.v1"] = (
        "er_commons.docling_conversion_completion.v1"
    )
    conversion_id: str
    status: Literal["complete", "complete_with_warnings"]
    source_id: str
    source_sha256: str
    source_manifest_sha256: str
    artifact_inventory: Literal["records/artifact_inventory.json"] = (
        "records/artifact_inventory.json"
    )
    artifact_inventory_sha256: str
    completed_at_utc: str


@dataclass(frozen=True)
class SealedConversion:
    """Verified conversion bundle and the payload required by derived stages."""

    conversion_id: str
    root: Path
    completion_path: Path
    inventory_path: Path
    output: ConversionOutput

    @property
    def reference(self) -> dict[str, str]:
        """Return the exact immutable upstream reference persisted by consumers."""
        return {
            "conversion_id": self.conversion_id,
            "completion_sha256": sha256_file(self.completion_path),
            "inventory_sha256": sha256_file(self.inventory_path),
        }


def _require(invariant: str, condition: bool, detail: str) -> None:
    if not condition:
        raise CompletedRunInvariantError(invariant, detail)


def _verify_externalized_images(
    document: dict[str, Any],
    assets_record: dict[str, Any],
    assets_path: Path,
) -> None:
    """Require durable Docling JSON to exclude embedded raster payloads."""
    record_value = assets_record.get("image_externalization")
    _require(
        "image_externalization_record",
        isinstance(record_value, dict),
        f"missing or invalid: {assets_path}",
    )
    record = cast(dict[str, Any], record_value)
    _require(
        "image_externalization_contract",
        record.get("contract_version") == "er_commons.docling_image_externalization.v1"
        and record.get("figure_crops_preserved_as_assets") is True
        and record.get("full_page_renders_preserved") is False,
        f"invalid externalization policy: {assets_path}",
    )
    pages = document.get("pages", {})
    pictures = document.get("pictures", [])
    _require("document_pages", isinstance(pages, dict), "document pages are invalid")
    _require("document_pictures", isinstance(pictures, list), "document pictures are invalid")
    _require(
        "embedded_page_images_absent",
        all(isinstance(page, dict) and page.get("image") is None for page in pages.values()),
        "document contains an embedded page image",
    )
    _require(
        "embedded_picture_images_absent",
        all(isinstance(picture, dict) and picture.get("image") is None for picture in pictures),
        "document contains an embedded picture image",
    )


def _load_output(root: Path, source_id: str) -> ConversionOutput:
    producer = root / "documents" / source_id / "producer"
    document_path = producer / "docling" / "document.json"
    observation_path = producer / "docling" / "conversion_observation.json"
    assets_path = producer / "asset_inventory.json"
    document = read_json_object(document_path)
    assets_record = read_json_object(assets_path)
    assets = assets_record.get("assets") if isinstance(assets_record, dict) else None
    _require("asset_inventory", isinstance(assets, list), f"invalid: {assets_path}")
    _verify_externalized_images(document, assets_record, assets_path)
    observation = ConversionObservation.model_validate_json(observation_path.read_bytes())
    return ConversionOutput(
        document_payload=document,
        assets=cast(list[dict[str, Any]], assets),
        observation=observation,
    )


@dataclass(frozen=True)
class _TerminalRecords:
    """Parsed terminal seal records and their immutable paths."""

    completion_path: Path
    inventory_path: Path
    completion: ConversionCompletion
    identity: dict[str, Any]
    inventory: dict[str, Any]


def _load_terminal_records(root: Path) -> _TerminalRecords:
    """Require and parse the three records that make a conversion reusable."""
    completion_path = root / "records" / "completion_record.json"
    inventory_path = root / "records" / "artifact_inventory.json"
    identity_path = root / "records" / "conversion_identity.json"
    _require(
        "terminal_records_exist",
        completion_path.is_file() and inventory_path.is_file() and identity_path.is_file(),
        f"conversion seal is incomplete below {root}",
    )
    completion = ConversionCompletion.model_validate_json(completion_path.read_bytes())
    identity = json.loads(identity_path.read_text())
    inventory = json.loads(inventory_path.read_text())
    return _TerminalRecords(completion_path, inventory_path, completion, identity, inventory)


def _verify_identity(records: _TerminalRecords, conversion_id: str) -> dict[str, Any]:
    """Require both terminal records to bind the canonically derived identity."""
    _require("completion_id", records.completion.conversion_id == conversion_id, "ID differs")
    _require("identity_id", records.identity.get("conversion_id") == conversion_id, "ID differs")
    _require(
        "identity_derivation",
        records.identity.get("identity") is not None,
        "conversion identity payload is missing",
    )
    from er_commons.document_parsing.content_parsing.identity import canonical_json_sha256

    _require(
        "derived_conversion_id",
        f"dconv1-{canonical_json_sha256(records.identity['identity'])}" == conversion_id,
        "identity payload does not derive the requested conversion ID",
    )
    return cast(dict[str, Any], records.identity["identity"])


def _verify_inventory_seal(root: Path, records: _TerminalRecords) -> None:
    """Require completion to seal a structurally valid managed-file inventory."""
    _require(
        "completion_inventory_seal",
        records.completion.artifact_inventory_sha256 == sha256_file(records.inventory_path),
        "completion does not seal the inventory",
    )
    verify_inventory_metadata(root, records.inventory)


def _verify_source(records: _TerminalRecords, identity: dict[str, Any]) -> dict[str, Any]:
    """Require completion source facts to equal their identity payload."""
    source = cast(dict[str, Any], identity["source"])
    release = cast(dict[str, Any], identity["sealed_release"])
    completion = records.completion
    _require("completion_source", completion.source_id == source["source_id"], "source differs")
    _require(
        "completion_source_sha256",
        completion.source_sha256 == source["sha256"],
        "source differs",
    )
    _require(
        "completion_manifest_sha256",
        completion.source_manifest_sha256 == release["manifest_sha256"],
        "manifest differs",
    )
    return source


def _verify_terminal_observation(
    completion: ConversionCompletion,
    output: ConversionOutput,
) -> None:
    """Require one clean successful observation matching completion."""
    _require(
        "terminal_conversion_status",
        output.observation.status in {"complete", "complete_with_warnings"},
        f"status={output.observation.status}",
    )
    _require(
        "completion_observation_status",
        completion.status == output.observation.status,
        "completion and observation status differ",
    )
    _require(
        "observation_source",
        output.observation.source_id == completion.source_id,
        "observation source differs",
    )
    _require(
        "successful_raw_status",
        output.observation.raw_status == "success" and not output.observation.errors,
        "raw conversion is not a clean success",
    )


def _expected_pages(source: dict[str, Any]) -> list[int]:
    """Return the identity-declared physical page sequence."""
    return list(range(1, int(source["pdf_page_count"]) + 1))


def _verify_alignment(
    root: Path,
    completion: ConversionCompletion,
    expected_pages: list[int],
) -> None:
    """Require one valid alignment projection for every identity page."""
    load_alignment_projection(
        root
        / "documents"
        / completion.source_id
        / "producer"
        / "docling"
        / "alignment_pages.jsonl",
        expected_page_count=len(expected_pages),
    )


def _verify_page_accounting(
    expected_pages: list[int],
    output: ConversionOutput,
) -> None:
    """Require observation and document pages to cover all identity pages."""
    _require(
        "expected_page_accounting",
        output.observation.expected_physical_pages == expected_pages,
        "expected page list differs from identity",
    )
    _require(
        "converted_page_accounting",
        output.observation.converted_physical_pages == expected_pages,
        "converted page list differs from identity",
    )
    _require(
        "document_page_accounting",
        sorted(int(value) for value in output.document_payload.get("pages", {})) == expected_pages,
        "document page list differs from identity",
    )
    _require(
        "complete_page_coverage",
        output.observation.page_coverage_complete,
        "page coverage flag is false",
    )


def _verify_asset_accounting(output: ConversionOutput) -> None:
    """Require the terminal observation to count every externalized asset."""
    _require(
        "asset_accounting",
        output.observation.asset_count == len(output.assets),
        "asset count differs from inventory",
    )


def verify_conversion_bundle(root: Path, conversion_id: str) -> SealedConversion:
    """Verify identity, managed files, completion seal, and terminal conversion facts."""
    records = _load_terminal_records(root)
    identity = _verify_identity(records, conversion_id)
    _verify_inventory_seal(root, records)
    source = _verify_source(records, identity)
    output = _load_output(root, records.completion.source_id)
    expected_pages = _expected_pages(source)
    _verify_alignment(root, records.completion, expected_pages)
    _verify_terminal_observation(records.completion, output)
    _verify_page_accounting(expected_pages, output)
    _verify_asset_accounting(output)
    return SealedConversion(
        conversion_id,
        root,
        records.completion_path,
        records.inventory_path,
        output,
    )


def deep_audit_conversion_bundle(root: Path, conversion_id: str) -> SealedConversion:
    """Explicitly rehash every conversion byte after normal seal validation."""
    sealed = verify_conversion_bundle(root, conversion_id)
    inventory = read_json_object(sealed.inventory_path)
    verify_inventory(root, inventory)
    return sealed


def read_accepted_conversion(
    root: Path,
    conversion_id: str,
    *,
    budget: VerificationBudget,
    source_id: str,
) -> dict[str, Any]:
    """Validate historical conversion metadata without loading its document payload."""
    records, identity_digest = _read_accepted_terminal_records(root, budget, source_id)
    completion = records.completion
    identity = _verify_identity(records, conversion_id)
    _require(
        "identity_schema",
        identity.get("identity_schema_version")
        in {"er_commons.docling_conversion_identity.v1", "er_commons.chunked_docling_aggregate.v1"},
        f"source={source_id}: unsupported conversion identity schema",
    )
    source = _verify_source(records, identity)
    _require(
        "selected_source",
        source.get("source_id") == source_id,
        f"source={source_id}: selected source differs",
    )
    inventory = read_accepted_inventory(
        root,
        expected_sha256=completion.artifact_inventory_sha256,
        source_id=source_id,
        budget=budget,
    )
    require_compact_identity_seal(inventory, "records/conversion_identity.json", identity_digest)
    _require_accepted_conversion_roles(root, source_id, inventory)
    _verify_accepted_observation(root, source_id, source, completion, budget)
    return {
        "conversion_id": conversion_id,
        "identity": identity,
        "completion": completion.model_dump(mode="json"),
        "inventory": inventory,
        "verification_mode": "metadata_checked",
    }


def _read_accepted_terminal_records(
    root: Path,
    budget: VerificationBudget,
    source_id: str,
) -> tuple[_TerminalRecords, str]:
    """Read and account for the historical compact identity and completion."""
    completion_path = root / "records/completion_record.json"
    identity_path = root / "records/conversion_identity.json"
    completion = ConversionCompletion.model_validate(
        budget.read_json(completion_path, role="completion", source_id=source_id, root=root)
    )
    budget.hash_file(completion_path, role="completion", source_id=source_id, root=root)
    identity_record = cast(
        dict[str, Any],
        budget.read_json(identity_path, role="identity_preimage", source_id=source_id, root=root),
    )
    identity_digest = budget.hash_file(
        identity_path, role="identity_preimage", source_id=source_id, root=root
    )
    records = _TerminalRecords(
        completion_path, root / "records/artifact_inventory.json", completion, identity_record, {}
    )
    return records, identity_digest


def _require_accepted_conversion_roles(
    root: Path, source_id: str, inventory: dict[str, Any]
) -> None:
    """Require every durable conversion role to be explicitly managed."""
    producer = root / "documents" / source_id / "producer"
    required_paths = {"records/conversion_identity.json"} | {
        (producer / relative).relative_to(root).as_posix()
        for relative in (
            "docling/document.json",
            "docling/conversion_observation.json",
            "docling/alignment_pages.jsonl",
            "docling/heading_overlay.jsonl",
            "asset_inventory.json",
        )
    }
    managed = {row["path"] for row in inventory["files"]}
    _require(
        "required_conversion_files",
        required_paths <= managed,
        f"source={source_id}: missing roles {sorted(required_paths - managed)}",
    )


def _verify_accepted_observation(
    root: Path,
    source_id: str,
    source: dict[str, Any],
    completion: ConversionCompletion,
    budget: VerificationBudget,
) -> None:
    """Check terminal conversion and full page accounting without loading Docling JSON."""
    producer = root / "documents" / source_id / "producer"
    observation = ConversionObservation.model_validate(
        budget.read_json(
            producer / "docling/conversion_observation.json",
            role="conversion_observation",
            source_id=source_id,
            root=root,
        )
    )
    _require(
        "terminal_observation",
        observation.source_id == source_id
        and observation.status == completion.status
        and observation.raw_status == "success"
        and not observation.errors,
        f"source={source_id}: terminal observation differs",
    )
    expected_pages = _expected_pages(source)
    _require(
        "observation_page_coverage",
        observation.expected_physical_pages == expected_pages
        and observation.converted_physical_pages == expected_pages
        and observation.page_coverage_complete,
        f"source={source_id}: page coverage differs",
    )
