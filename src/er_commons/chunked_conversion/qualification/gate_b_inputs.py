"""Sealed baseline, configuration, and identity ownership for Gate B."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from er_commons.artifact_io import (
    canonical_json_sha256,
    read_json_object,
    sha256_file,
)
from er_commons.chunked_conversion.qualification.gate_b_contracts import (
    CONVERSION_ID,
    SEAMS,
    SOURCE_ID,
    SOURCE_PAGE_COUNT,
    SOURCE_SHA256,
    THREAD_COUNT,
    GateBContractError,
    seam_payload,
)
from er_commons.document_parsing.content_parsing.config import (
    ContentParsingConfig,
    load_content_parsing_config,
)
from er_commons.document_parsing.content_parsing.evidence import verify_inventory
from er_commons.document_parsing.content_parsing.identity import code_identity
from er_commons.document_parsing.content_parsing.preparation import (
    PreparedContentParsing,
    prepare_content_parsing,
)


def verified_inputs(
    source_root: Path, config_path: Path, data_root: Path
) -> tuple[dict[str, Any], PreparedContentParsing]:
    """Verify that config, source, runtime, and models bind the accepted sealed G1."""
    completion = read_json_object(source_root / "records/completion_record.json")
    if (
        completion.get("status") not in {"complete", "complete_with_warnings"}
        or completion.get("conversion_id") != CONVERSION_ID
    ):
        raise GateBContractError(
            "sealed_completion_differs", source_root.as_posix(), "identity or status differs"
        )
    inventory_path = source_root / "records/artifact_inventory.json"
    verify_inventory(source_root, read_json_object(inventory_path))
    identity = read_json_object(source_root / "records/conversion_identity.json")
    if identity.get("conversion_id") != CONVERSION_ID:
        raise GateBContractError(
            "sealed_identity_differs", "records/conversion_identity.json", "conversion ID differs"
        )
    config, config_sha256 = load_content_parsing_config(config_path)
    require_accepted_config(config)
    prepared = prepare_content_parsing(data_root, config=config, config_sha256=config_sha256)
    sealed = _required_object(identity, "identity")
    if prepared.conversion_identity.run_id != CONVERSION_ID:
        raise GateBContractError(
            "prepared_identity_differs", "prepared.conversion_identity", "conversion ID differs"
        )
    if prepared.conversion_identity.payload != sealed:
        raise GateBContractError(
            "prepared_payload_differs", "prepared.conversion_identity.payload", "payload differs"
        )
    sealed_runtime = read_json_object(source_root / "records/runtime_configuration.json")
    if prepared.runtime != sealed_runtime:
        raise GateBContractError(
            "runtime_differs", "records/runtime_configuration.json", "prepared runtime differs"
        )
    _verify_source_and_models(sealed, config, prepared)
    return identity, prepared


def _verify_source_and_models(
    sealed: dict[str, Any], config: ContentParsingConfig, prepared: PreparedContentParsing
) -> None:
    source = sealed.get("source")
    expected_source = {
        "source_id": SOURCE_ID,
        "sha256": SOURCE_SHA256,
        "byte_size": config.source.expected_byte_size,
        "pdf_page_count": SOURCE_PAGE_COUNT,
    }
    if source != expected_source:
        raise GateBContractError(
            "source_identity_differs",
            "identity.source",
            f"expected={expected_source!r} actual={source!r}",
        )
    model_identity = _required_object(sealed, "model_inventory")
    if prepared.model_inventory_sha256 != model_identity.get("sha256"):
        raise GateBContractError(
            "model_inventory_digest_differs", "identity.model_inventory.sha256", "digest differs"
        )
    prepared_models = [item.model_dump(mode="json") for item in prepared.model_inventory.models]
    if prepared_models != model_identity.get("models"):
        raise GateBContractError(
            "model_inventory_records_differ", "identity.model_inventory.models", "records differ"
        )


def require_accepted_config(config: ContentParsingConfig) -> None:
    """Require the exact G1 CPU/4 configuration qualified by Gate B."""
    actual = (
        config.source.source_id,
        config.source.expected_sha256,
        config.source.expected_pdf_page_count,
        config.device,
        config.thread_count,
    )
    expected = (SOURCE_ID, SOURCE_SHA256, SOURCE_PAGE_COUNT, "cpu", THREAD_COUNT)
    if actual != expected:
        raise GateBContractError(
            "config_differs", "content_parsing_config", f"expected={expected!r} actual={actual!r}"
        )


def identity_payload(
    *,
    project_root: Path,
    source_root: Path,
    config_path: Path,
    prepared: PreparedContentParsing,
    max_rss_bytes: int,
    max_wall_seconds: float,
) -> dict[str, Any]:
    """Build the run identity from behavior owners, excluding the CLI shell bytes."""
    qualification = project_root / "src/er_commons/chunked_conversion/qualification"
    implementation = code_identity(
        [
            qualification / "gate_b_contracts.py",
            qualification / "gate_b_docling.py",
            qualification / "gate_b_inputs.py",
            qualification / "gate_b_trace.py",
            qualification / "gate_b_worker.py",
            qualification / "gate_b_application.py",
        ],
        repo_root=project_root,
    )
    return {
        "identity_schema_version": "er_commons.task03h2_gate_b_identity.v2",
        "source_conversion_id": CONVERSION_ID,
        "source_inventory_sha256": sha256_file(source_root / "records/artifact_inventory.json"),
        "prepared_conversion_id": prepared.conversion_identity.run_id,
        "prepared_conversion_payload_sha256": canonical_json_sha256(
            prepared.conversion_identity.payload
        ),
        "sealed_runtime_configuration_sha256": canonical_json_sha256(prepared.runtime),
        "sealed_runtime_configuration": prepared.runtime,
        "implementation": implementation,
        "gate_b_helper_sha256": sha256_file(
            project_root / "src/er_commons/chunked_conversion/gate_b.py"
        ),
        "config_sha256": sha256_file(config_path),
        "seams": [seam_payload(seam) for seam in SEAMS],
        "max_rss_bytes": max_rss_bytes,
        "max_wall_seconds": max_wall_seconds,
    }


def _required_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise GateBContractError("expected_object", key, f"observed {type(value).__name__}")
    return value


__all__ = ["identity_payload", "verified_inputs"]
