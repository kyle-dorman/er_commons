"""Verified G1 inputs and behavior-scoped identities for Gate C."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import canonical_json_sha256, read_json_object, sha256_file
from er_commons.chunked_conversion.qualification.g1_profile import G1CodeIdentity
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

SOURCE_ID = "deir_appendix_g1"
SOURCE_SHA256 = "e11835a7c6346c6780bfe26bee0037f4b6206b0a1573b3d480cb2b4170e79f7f"
SOURCE_PAGE_COUNT = 2488
THREAD_COUNT = 4
SEALED_CONVERSION_ID = "dconv1-97a8d4048839d9ba26c78151d0446e1c1bbef9848183f1ce9b9140c92e4c3f68"
DEFAULT_SOURCE_ROOT = Path(
    "pipelines/brisbane_baylands/task_03h_clean_full_v1/document_parse_evidence/"
    f"docling_conversions/{SEALED_CONVERSION_ID}"
)
DEFAULT_OUTPUT_ROOT = Path(
    "pipelines/brisbane_baylands/task_03h2_chunked_docling_conversion/gate_c"
)
DEFAULT_CONFIG = Path("configs/task03h/deir_appendix_g1/content_parsing.json")


@dataclass(frozen=True)
class VerifiedG1Inputs:
    """Closed conversion identity and prepared runtime for the accepted G1 source."""

    sealed_identity: dict[str, Any]
    prepared: PreparedContentParsing


def verify_g1_inputs(source_root: Path, config_path: Path, data_root: Path) -> VerifiedG1Inputs:
    """Verify the sealed G1 conversion and reproduce its preparation identity."""
    completion = read_json_object(source_root / "records/completion_record.json")
    if completion.get("conversion_id") != SEALED_CONVERSION_ID or completion.get("status") not in {
        "complete",
        "complete_with_warnings",
    }:
        raise ValueError("sealed G1 completion differs")
    verify_inventory(source_root, read_json_object(source_root / "records/artifact_inventory.json"))
    sealed_identity = read_json_object(source_root / "records/conversion_identity.json")
    config, config_sha256 = load_content_parsing_config(config_path)
    require_g1_config(config)
    prepared = prepare_content_parsing(data_root, config=config, config_sha256=config_sha256)
    if prepared.conversion_identity.run_id != SEALED_CONVERSION_ID:
        raise ValueError("prepared conversion identity differs from sealed G1")
    if prepared.conversion_identity.payload != sealed_identity.get("identity"):
        raise ValueError("prepared conversion payload differs from sealed G1")
    if prepared.runtime != read_json_object(source_root / "records/runtime_configuration.json"):
        raise ValueError("prepared runtime differs from sealed G1")
    return VerifiedG1Inputs(sealed_identity, prepared)


def require_g1_config(config: ContentParsingConfig) -> None:
    """Require the accepted source and CPU/thread execution configuration."""
    actual = (
        config.source.source_id,
        config.source.expected_sha256,
        config.source.expected_pdf_page_count,
        config.device,
        config.thread_count,
    )
    expected = (SOURCE_ID, SOURCE_SHA256, SOURCE_PAGE_COUNT, "cpu", THREAD_COUNT)
    if actual != expected:
        raise ValueError(f"Gate C requires accepted G1 CPU/4 config: {actual!r}")


def behavior_code_identity(project_root: Path) -> G1CodeIdentity:
    """Hash only modules that own planning, range conversion, and aggregation behavior."""
    package = project_root / "src/er_commons/chunked_conversion"

    def digest(*relative_paths: str) -> str:
        return str(
            code_identity([package / path for path in relative_paths], repo_root=project_root)[
                "sha256"
            ]
        )

    return G1CodeIdentity(
        page_evidence=digest("gate_b.py", "gate_c.py"),
        range_conversion=digest(
            "qualification/docling_adapter.py",
            "qualification/converted_range_store.py",
            "qualification/gate_c_worker.py",
        ),
        planning=digest("range_contract.py", "qualification/g1_profile.py"),
        aggregate=digest(
            "qualification/docling_adapter.py",
            "qualification/aggregation.py",
        ),
    )


def gate_c_run_identity(
    *,
    source_root: Path,
    config_path: Path,
    verified: VerifiedG1Inputs,
    plan_id: str,
    code: G1CodeIdentity,
    resource_limits: dict[str, object],
) -> dict[str, Any]:
    """Build operational identity without binding CLI or report-rendering bytes."""
    return {
        "identity_schema_version": "er_commons.task03h2_gate_c_identity.v2",
        "source_conversion_id": SEALED_CONVERSION_ID,
        "source_inventory_sha256": sha256_file(source_root / "records/artifact_inventory.json"),
        "prepared_conversion_id": verified.prepared.conversion_identity.run_id,
        "prepared_runtime": verified.prepared.runtime,
        "config_sha256": sha256_file(config_path),
        "plan_id": plan_id,
        "behavior_code": code.__dict__,
        "resource_limits": resource_limits,
        "scope": "G1 full qualification only; no G2 inspection",
    }


def gate_c_run_id(identity: dict[str, Any]) -> str:
    """Derive the operational run ID from the typed identity payload."""
    return f"gatec1-{canonical_json_sha256(identity)}"


def resolve_data_root(value: Path | None) -> Path:
    """Resolve an explicit data root or require the documented environment setting."""
    if value is not None:
        return value.resolve()
    configured = os.environ.get("ER_COMMONS_DATA_ROOT")
    if not configured:
        raise ValueError("ER_COMMONS_DATA_ROOT is not set and --data-root was not supplied")
    return Path(configured).resolve()


__all__ = [
    "DEFAULT_CONFIG",
    "DEFAULT_OUTPUT_ROOT",
    "DEFAULT_SOURCE_ROOT",
    "SEALED_CONVERSION_ID",
    "SOURCE_ID",
    "SOURCE_PAGE_COUNT",
    "THREAD_COUNT",
    "VerifiedG1Inputs",
    "behavior_code_identity",
    "gate_c_run_id",
    "gate_c_run_identity",
    "resolve_data_root",
    "verify_g1_inputs",
]
