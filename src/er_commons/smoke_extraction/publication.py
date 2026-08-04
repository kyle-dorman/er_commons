"""Identity evidence, attempt allocation, and final diagnostic publication."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_extraction.artifacts import artifact_inventory
from er_commons.document_extraction.runtime import configuration_record
from er_commons.smoke_extraction.config import SmokeSpec, load_smoke_spec
from er_commons.smoke_extraction.selection import smoke_id, validate_manifest_metadata
from er_commons.smoke_extraction.services import SmokeServices
from er_commons.source_freeze import write_json_atomic


@dataclass(frozen=True)
class PreparedSmoke:
    """Validated identity-level state shared by one fresh attempt."""

    spec: SmokeSpec
    spec_sha256: str
    run_id: str
    smoke_root: Path
    converter: Any


def _write_or_verify_json(path: Path, payload: dict[str, Any]) -> None:
    """Initialize identity evidence once and reject drift on resume."""
    if path.is_file():
        if json.loads(path.read_text()) != payload:
            raise ValueError(f"existing smoke identity evidence differs: {path.name}")
        return
    write_json_atomic(path, payload)


def _freeze_spec(smoke_root: Path, spec_path: Path) -> None:
    frozen = smoke_root / "smoke_spec.json"
    if frozen.is_file():
        if frozen.read_bytes() != spec_path.read_bytes():
            raise ValueError("existing smoke specification bytes differ")
        return
    frozen.write_bytes(spec_path.read_bytes())


def prepare_smoke(
    data_root: Path,
    spec_path: Path,
    services: SmokeServices,
) -> PreparedSmoke:
    """Validate immutable inputs and initialize reusable identity evidence."""
    spec, spec_sha256 = load_smoke_spec(spec_path)
    validate_manifest_metadata(data_root, spec)
    repo_root = Path(__file__).resolve().parents[3]
    run_id = smoke_id(repo_root, spec, spec_sha256)
    smoke_root = (data_root / spec.artifact_relative_root / run_id).resolve()
    if not smoke_root.is_relative_to(data_root.resolve()):
        raise ValueError("smoke artifact root escapes ER_COMMONS_DATA_ROOT")
    if (smoke_root / "diagnostic_summary.json").exists():
        raise FileExistsError(f"completed smoke already exists: {smoke_root}")

    models_path = data_root / spec.model_inventory_relative_path
    _inventory, models_root = services.verify_models(data_root, models_path)
    converter, options, format_option = services.build_converter(
        models_root, thread_count=spec.resource_policy.converter_thread_count
    )
    smoke_root.mkdir(parents=True, exist_ok=True)
    _write_or_verify_json(
        smoke_root / "identity.json",
        {
            "schema_version": "er_commons.task03g1_smoke_identity.v1",
            "smoke_id": run_id,
            "spec_sha256": spec_sha256,
            "selection_sha256": spec.selection_sha256,
            "production_extraction_id": spec.production_extraction_id,
            "diagnostic_only": True,
        },
    )
    _freeze_spec(smoke_root, spec_path)
    _write_or_verify_json(
        smoke_root / "runtime_configuration.json",
        configuration_record(spec.configuration_id, options, format_option),
    )
    return PreparedSmoke(spec, spec_sha256, run_id, smoke_root, converter)


def allocate_attempt(prepared: PreparedSmoke, services: SmokeServices) -> tuple[str, Path]:
    """Create a fresh no-clobber attempt below an incomplete smoke identity."""
    attempt_id = f"attempt-{services.new_token()}"
    attempt_root = prepared.smoke_root / "attempts" / attempt_id
    attempt_root.mkdir(parents=True, exist_ok=False)
    return attempt_id, attempt_root


def inventory_attempt(attempt_root: Path) -> dict[str, Any]:
    """Inventory retained attempt evidence before adding terminal records."""
    inventory = artifact_inventory(
        attempt_root, {"artifact_inventory.json", "diagnostic_summary.json"}
    )
    write_json_atomic(attempt_root / "artifact_inventory.json", inventory)
    return inventory


def publish_summary(
    prepared: PreparedSmoke,
    attempt_root: Path,
    summary: dict[str, Any],
) -> Path:
    """Publish attempt and identity-level diagnostic summaries, never a completion seal."""
    attempt_summary = attempt_root / "diagnostic_summary.json"
    write_json_atomic(attempt_summary, summary)
    summary_path = prepared.smoke_root / "diagnostic_summary.json"
    write_json_atomic(summary_path, summary)
    return summary_path
