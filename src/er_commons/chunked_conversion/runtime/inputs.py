"""Source-neutral preparation, plan validation, and runtime identity."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from er_commons.artifact_io import canonical_json_sha256, sha256_file
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.document_parsing.content_parsing.config import load_content_parsing_config
from er_commons.document_parsing.content_parsing.identity import code_identity
from er_commons.document_parsing.content_parsing.preparation import (
    PreparedContentParsing,
    prepare_content_parsing,
)


@dataclass(frozen=True)
class RuntimeCodeIdentity:
    """Behavior-owned code digests with narrow invalidation boundaries."""

    page_evidence: str
    range_conversion: str
    planning: str
    aggregate: str
    coordinator: str


@dataclass(frozen=True)
class VerifiedChunkInputs:
    """Prepared source/model/runtime inputs and the caller-supplied range plan."""

    prepared: PreparedContentParsing
    plan: RangePlan


def verify_chunk_inputs(
    config_path: Path,
    plan_path: Path,
    data_root: Path,
    code: RuntimeCodeIdentity | None = None,
) -> VerifiedChunkInputs:
    """Prepare immutable inputs and bind the plan to current conversion behavior."""
    config, config_sha256 = load_content_parsing_config(config_path)
    prepared = prepare_content_parsing(data_root, config=config, config_sha256=config_sha256)
    plan = RangePlan.model_validate_json(plan_path.read_bytes())
    source = plan.inputs.source
    actual = (
        prepared.source.source_id,
        prepared.source.source_sha256,
        prepared.source.source_byte_size,
        prepared.source.source_page_count,
    )
    expected = (source.source_id, source.sha256, source.byte_size, source.physical_page_count)
    if actual != expected:
        raise ValueError(
            f"range plan source differs from prepared source: {actual!r} != {expected!r}"
        )
    active_code = code or behavior_code_identity(Path(__file__).resolve().parents[4])
    conversion = prepared.conversion_identity.payload
    bindings = {
        "converter_identity": prepared.conversion_identity.run_id,
        "sealed_source_release_identity": canonical_json_sha256(conversion["sealed_release"]),
        "package_identity": canonical_json_sha256(conversion["package_versions"]),
        "model_identity": canonical_json_sha256(conversion["model_inventory"]),
        "adapter_identity": active_code.page_evidence,
        "page_evidence_contract_identity": (
            f"compact_typed_page_evidence:{active_code.page_evidence}"
        ),
        "range_conversion_identity": active_code.range_conversion,
        "range_planner_identity": active_code.planning,
        "aggregate_merge_identity": active_code.aggregate,
    }
    mismatches = {
        field: {"expected": wanted, "actual": getattr(plan.inputs, field)}
        for field, wanted in bindings.items()
        if getattr(plan.inputs, field) != wanted
    }
    if mismatches:
        raise ValueError(f"range plan runtime bindings differ: {mismatches!r}")
    return VerifiedChunkInputs(prepared=prepared, plan=plan)


def behavior_code_identity(project_root: Path) -> RuntimeCodeIdentity:
    """Hash only production modules able to alter plan, child, or aggregate bytes."""
    package = project_root / "src/er_commons/chunked_conversion"

    def digest(*relative_paths: str) -> str:
        paths = [package / path for path in relative_paths]
        return str(code_identity(paths, repo_root=project_root)["sha256"])

    return RuntimeCodeIdentity(
        page_evidence=digest("page_evidence.py", "page_evidence_store.py"),
        range_conversion=digest(
            "runtime/docling_adapter.py",
            "runtime/range_store.py",
            "runtime/worker.py",
        ),
        planning=digest("range_contract.py", "runtime/planning.py"),
        aggregate=digest("runtime/docling_adapter.py", "runtime/aggregate.py"),
        coordinator=digest(
            "runtime/application.py",
            "runtime/completion.py",
            "runtime/publication.py",
            "runtime/workflow.py",
        ),
    )


def chunked_run_identity(
    *,
    plan_path: Path,
    verified: VerifiedChunkInputs,
    code: RuntimeCodeIdentity,
) -> dict[str, object]:
    """Bind the explicit plan and production behavior without touching monolithic IDs."""
    return {
        "identity_schema_version": "er_commons.chunked_conversion_run.v1",
        "prepared_conversion_id": verified.prepared.conversion_identity.run_id,
        "plan_id": verified.plan.plan_id,
        "plan_sha256": sha256_file(plan_path),
        "behavior_code": code.__dict__,
    }


def chunked_run_id(identity: dict[str, object]) -> str:
    """Derive the coordinator ID from its complete operational identity."""
    return f"chunk1-{canonical_json_sha256(identity)}"


def resolve_data_root(value: Path | None) -> Path:
    """Resolve an explicit data root or require the documented environment setting."""
    if value is not None:
        return value.resolve()
    configured = os.environ.get("ER_COMMONS_DATA_ROOT")
    if not configured:
        raise ValueError("ER_COMMONS_DATA_ROOT is not set and --data-root was not supplied")
    return Path(configured).resolve()


__all__ = [
    "RuntimeCodeIdentity",
    "VerifiedChunkInputs",
    "behavior_code_identity",
    "chunked_run_id",
    "chunked_run_identity",
    "resolve_data_root",
    "verify_chunk_inputs",
]
