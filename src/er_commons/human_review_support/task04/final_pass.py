"""Source-free Gate A preparation for the Task 03J final review pass."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import (
    canonical_json_sha256,
    json_bytes,
    publish_bytes_no_clobber,
)
from er_commons.collection_processing.handoff_validation import validate_collection_handoff
from er_commons.human_review_support.task04.final_pass_record import (
    PreparationRecordInputs,
    build_preparation_record,
)
from er_commons.human_review_support.task04.final_pass_record import (
    path_reference as _path_reference,
)
from er_commons.human_review_support.task04.final_policy import (
    FINAL_PASS,
    FINAL_SCHEMA_VERSION,
    final_review_policy,
)
from er_commons.human_review_support.task04.json_io import read_json_object
from er_commons.human_review_support.task04.toc_census import build_toc_census

TASK_ROOT_RELATIVE = "pipelines/brisbane_baylands/task_03h_clean_full_v4"
SOURCE_RELEASE_RELATIVE = (
    "datasets/ceqa/raw/brisbane_baylands/"
    "brisbane_baylands_2025_deir_sources_v1/sources/model_corpus"
)
HANDOFF_ID = "handoffv1-44d510d545026a427ccdb47497d30f1d46c66130291af66fc0d5883a35102325"
SCOPE_ID = "scopev1-bd4b7ca85b299ae528376b1a6e88b9d0fdba02e4f7e8862c5fa91a28b719e893"


def prepare_task03j_final(
    data_root: Path,
    *,
    repo_root: Path,
    task_root_relative: str = TASK_ROOT_RELATIVE,
    task03i_root: Path | None = None,
    validate_upstream: bool = True,
    raw_docling_scan: bool = True,
    build_census: bool = False,
) -> dict[str, Any]:
    """Prepare Gate A without opening PDFs or rendering.

    The large per-source machine-artifact census is opt-in so the MVP path can
    establish the review boundary without scanning every JSONL product.
    """
    task_root = (data_root / task_root_relative).resolve()
    plan_path = task_root / "inputs/task03j_activation_plan.json"
    readiness_path = task_root / "inputs/task03j_preparation_readiness.json"
    publication_root = task_root / "document_publications"
    scope_root = publication_root / "scopes" / SCOPE_ID
    bundle_path = scope_root / "contract_bundle.json"
    handoff_path = _handoff_path(publication_root)
    plan = read_json_object(plan_path)
    readiness = read_json_object(readiness_path)
    bundle = read_json_object(bundle_path)
    handoff = read_json_object(handoff_path)
    _validate_task03j_boundary(plan, readiness, bundle, handoff, handoff_path)
    if validate_upstream:
        _run_handoff_validator(publication_root, repo_root)
    task03i = _load_task03i(task03i_root or _default_task03i_root(data_root), repo_root)
    dependencies = _dependency_inventory(
        data_root,
        task_root,
        plan_path,
        readiness_path,
        plan,
        bundle,
        handoff,
        task03i,
    )
    policy = final_review_policy()
    policy_sha256 = canonical_json_sha256(policy)
    implementation = _implementation_inventory(repo_root)
    input_payload = _input_payload(plan, readiness, bundle, handoff, task03i, dependencies)
    input_sha256 = canonical_json_sha256(input_payload)
    implementation_sha256 = canonical_json_sha256(implementation)
    identity_preimage = {
        "pass": FINAL_PASS,
        "policy_sha256": policy_sha256,
        "input_sha256": input_sha256,
        "implementation_sha256": implementation_sha256,
    }
    review_run_id = f"reviewv1-task03j-final-{canonical_json_sha256(identity_preimage)[:16]}"
    censuses = (
        _build_censuses(plan, dependencies, data_root, raw_docling_scan) if build_census else []
    )
    record = build_preparation_record(
        PreparationRecordInputs(
            review_run_id=review_run_id,
            final_pass=FINAL_PASS,
            schema_version=FINAL_SCHEMA_VERSION,
            policy=policy,
            policy_sha256=policy_sha256,
            input_sha256=input_sha256,
            implementation=implementation,
            implementation_sha256=implementation_sha256,
            dependencies=dependencies,
            task03i=task03i,
            bundle=bundle,
            handoff=handoff,
            censuses=censuses,
            upstream_validation_ran=validate_upstream,
        )
    )
    return record


def publish_gate_a_preparation(
    record: dict[str, Any], data_root: Path, *, relative_path: str | None = None
) -> Path:
    """Publish the compact source-free Gate A record without clobbering bytes."""
    target = data_root / (relative_path or _default_output_path(record["review_run_id"]))
    publish_bytes_no_clobber(target, json_bytes(record))
    return target


def _validate_task03j_boundary(
    plan: dict[str, Any],
    readiness: dict[str, Any],
    bundle: dict[str, Any],
    handoff: dict[str, Any],
    handoff_path: Path,
) -> None:
    """Reject stale lineage and incomplete current handoff bindings."""
    expected_identity = "exv1-6913f56bed93302d7cf5ef424ee63c0b7427e90e2b2cd5c4ec483d275009a773"
    if (
        plan.get("run_label") != "task03j_final_v4"
        or plan.get("production_extraction_id") != expected_identity
    ):
        raise ValueError("activation plan is not the frozen Task 03J final plan")
    if readiness.get("production_extraction_id") != expected_identity:
        raise ValueError("readiness record is from a different production identity")
    if (
        readiness.get("source_pdf_bytes_read") is not False
        or readiness.get("model_files_read") is not False
    ):
        raise ValueError("Task 03J readiness reports a forbidden source or model read")
    if bundle.get("production_extraction_id") != expected_identity:
        raise ValueError("contract bundle is from a different production identity")
    if handoff.get("handoff_id") != HANDOFF_ID or handoff.get("scope_id") != SCOPE_ID:
        raise ValueError("Task 03J handoff identity differs from the frozen Gate A anchor")
    if handoff.get("status") != "ready" or handoff.get("task04_status") != "not_evaluated":
        raise ValueError("Task 03J handoff is not an unevaluated ready handoff")
    if handoff != bundle.get("handoff"):
        raise ValueError("handoff completion does not match the contract bundle")
    expected = handoff_path.parent / "completion_record.json"
    if expected != handoff_path or not expected.is_file():
        raise ValueError("handoff completion path is invalid")
    completions = bundle.get("document_completions")
    if not isinstance(completions, list) or len(completions) != 35:
        raise ValueError("Task 03J handoff must contain exactly 35 document completions")


def _run_handoff_validator(publication_root: Path, repo_root: Path) -> None:
    """Run the owning read-only validator over machine artifacts only."""
    validate_collection_handoff(
        extraction_root=publication_root,
        scope_id=SCOPE_ID,
        schema_path=repo_root
        / "benchmarks/er_bench/schemas/collection_processing/v2/records.schema.json",
        data_root=publication_root.parent,
    )


def _load_task03i(task03i_root: Path, repo_root: Path) -> dict[str, Any]:
    """Validate the historical first-pass disposition without importing its anchors."""
    register_path = task03i_root / "records/finding_register.json"
    handoff_path = task03i_root / "records/task03i_handoff.json"
    register = read_json_object(register_path)
    handoff = read_json_object(handoff_path)
    from er_commons.human_review_support.task04.records import RecordValidator

    validator = RecordValidator(repo_root / "benchmarks/er_bench/schemas/task04_review/v1")
    validator.validate("finding_register", register)
    validator.validate("task03i_handoff", handoff)
    if register.get("status") != "approved" or handoff.get("status") != "approved":
        raise ValueError("Task 03I disposition is not approved")
    if not isinstance(handoff.get("finding_register_sha256"), str):
        raise ValueError("Task 03I handoff lacks its sealed finding register checksum")
    findings = register.get("findings")
    if not isinstance(findings, list):
        raise ValueError("Task 03I finding register has no findings array")
    return {
        "register": _path_reference(
            register_path, task03i_root, str(handoff["finding_register_sha256"])
        ),
        "handoff": _path_reference(handoff_path, task03i_root),
        "finding_ids": [str(item["finding_id"]) for item in findings if isinstance(item, dict)],
        "finding_count": len(findings),
        "status": "approved",
        "recheck_policy": "every_applicable_finding_gets_one_exact_task03j_evidence_outcome",
    }


def _default_task03i_root(data_root: Path) -> Path:
    """Return the retained first-pass review namespace."""
    return (
        data_root
        / "pipelines/brisbane_baylands/task_04_review/reviewv1-task03h-first-7e8e89a40907adba"
    )


def _handoff_path(publication_root: Path) -> Path:
    """Resolve the completion-last Task 03J handoff record."""
    return (
        publication_root
        / "scopes"
        / SCOPE_ID
        / "handoffs"
        / HANDOFF_ID
        / "records/completion_record.json"
    )


def _dependency_inventory(
    data_root: Path,
    task_root: Path,
    plan_path: Path,
    readiness_path: Path,
    plan: dict[str, Any],
    bundle: dict[str, Any],
    handoff: dict[str, Any],
    task03i: dict[str, Any],
) -> dict[str, Any]:
    """Bind source, candidate, and machine evidence references without source hashes."""
    order = _object_list(plan, "source_order")
    completions = _object_list(bundle, "document_completions")
    by_source = {str(item["source"]["source_id"]): item for item in completions}
    sources = []
    for item in order:
        source_id = str(item["source_id"])
        completion = by_source.get(source_id)
        if completion is None:
            raise ValueError(f"activation plan source is absent from handoff: {source_id}")
        candidate_id = str(completion["candidate_id"])
        candidate = task_root / "document_publications" / "documents" / source_id / candidate_id
        sources.append(
            {
                "ordinal": int(item["ordinal"]),
                "source_id": source_id,
                "source_sha256": str(completion["source"]["sha256"]),
                "pdf_page_count": int(item["pdf_page_count"]),
                "byte_size": int(item["byte_size"]),
                "source_pdf": {
                    "relative_path": f"{SOURCE_RELEASE_RELATIVE}/{source_id}.pdf",
                    "expected_sha256": str(completion["source"]["sha256"]),
                    "verification": "deferred_until_gate_c",
                },
                "candidate": _candidate_dependencies(candidate, data_root),
            }
        )
    return {
        "task03j": {
            "production_extraction_id": str(plan["production_extraction_id"]),
            "scope_id": SCOPE_ID,
            "handoff_id": HANDOFF_ID,
            "handoff_completion": _path_reference(
                _handoff_path(task_root / "document_publications"), data_root
            ),
            "contract_bundle": _path_reference(
                task_root / "document_publications/scopes" / SCOPE_ID / "contract_bundle.json",
                data_root,
            ),
            "handoff_identity_preimage": handoff.get("identity_preimage"),
            "activation_plan": _path_reference(plan_path, data_root),
            "readiness": _path_reference(readiness_path, data_root),
        },
        "sources": sources,
        "task03i": task03i,
        "stale_inputs_rejected": [
            "historical_task03h_candidate_ids",
            "historical_task04_review_ids",
            "historical_task04_anchors",
            "historical_task04_renders",
            "source_pdf_sha256_computation_before_gate_c",
        ],
    }


def _candidate_dependencies(candidate: Path, data_root: Path) -> dict[str, Any]:
    """Record checksummed candidate products needed by final review."""
    if not candidate.is_dir():
        raise FileNotFoundError(candidate)
    inventory_path = candidate / "records/artifact_inventory.json"
    inventory = read_json_object(inventory_path)
    completion = read_json_object(candidate / "records/completion_record.json")
    inventory_files = inventory.get("files")
    if not isinstance(inventory_files, list):
        raise ValueError(f"candidate inventory has no files array: {inventory_path}")
    completion_inventory = completion.get("candidate_inventory")
    if not isinstance(completion_inventory, dict):
        raise ValueError(f"candidate completion has no inventory reference: {candidate}")
    selected_files = [
        item
        for item in inventory_files
        if isinstance(item, dict)
        and (
            str(item.get("path", ""))
            in {
                "content/canonical/assets.jsonl",
                "content/canonical/blocks.jsonl",
                "content/canonical/cross_references.jsonl",
                "content/canonical/pages.jsonl",
                "content/canonical/sections.jsonl",
                "content/canonical/table_families.jsonl",
                "content/canonical/tables.jsonl",
                "content/canonical/target_aliases.jsonl",
                "content/observations/routing.jsonl",
                "content/observations/table_stage.jsonl",
            }
            or str(item.get("path", "")).endswith("content/records/canonicalization_summary.json")
        )
    ]
    return {
        "candidate_id": candidate.name,
        "relative_path": candidate.relative_to(data_root).as_posix(),
        "candidate_inventory": completion_inventory,
        "completion_record_relative_path": (candidate / "records/completion_record.json")
        .relative_to(data_root)
        .as_posix(),
        "managed_machine_artifacts": sorted(selected_files, key=lambda item: str(item.get("path"))),
        "render_inputs": {
            "candidate_machine_evidence": "bound",
            "source_pdf": "path_and_expected_checksum_only_until_gate_c",
            "renderer": "qualified_task04_pypdfium2_adapter_deferred_until_gate_c",
        },
    }


def _implementation_inventory(repo_root: Path) -> dict[str, Any]:
    """Bind final-pass code, qualified UI seams, and checked-in schemas."""
    paths = [
        "src/er_commons/human_review_support/task04/final_policy.py",
        "src/er_commons/human_review_support/task04/final_pass.py",
        "src/er_commons/human_review_support/task04/final_pass_record.py",
        "src/er_commons/human_review_support/task04/toc_census.py",
        "src/er_commons/human_review_support/task04/toc_census_support.py",
        "src/er_commons/human_review_support/task04/toc_raw_scan.py",
        "src/er_commons/human_review_support/task04/application.py",
        "src/er_commons/human_review_support/task04/canonical_evidence.py",
        "src/er_commons/human_review_support/task04/geometry.py",
        "src/er_commons/human_review_support/task04/rendering.py",
        "benchmarks/er_bench/schemas/task04a_review/v1/gate_a_preparation.schema.json",
        "benchmarks/er_bench/schemas/task04a_review/v1/usability_registry.schema.json",
        "benchmarks/er_bench/schemas/task04a_review/v1/release_freeze.schema.json",
    ]
    return {
        "files": [_path_reference(repo_root / path, repo_root) for path in paths],
        "qualified_seams": [
            "task04_application_side_by_side_presentation",
            "task04_canonical_and_table_overlay_evidence",
            "task04_shared_display_geometry_transform",
            "task04_pypdfium2_renderer",
        ],
    }


def _input_payload(
    plan: dict[str, Any],
    readiness: dict[str, Any],
    bundle: dict[str, Any],
    handoff: dict[str, Any],
    task03i: dict[str, Any],
    dependencies: dict[str, Any],
) -> dict[str, Any]:
    """Create the closed identity preimage from exact upstream references."""
    return {
        "production_extraction_id": plan["production_extraction_id"],
        "activation_plan_path": dependencies["task03j"]["activation_plan"]["path"],
        "readiness_path": dependencies["task03j"]["readiness"]["path"],
        "contract_bundle_path": dependencies["task03j"]["contract_bundle"]["path"],
        "readiness_status": readiness.get("status"),
        "handoff": handoff,
        "task03i": task03i,
        "source_and_candidate_bindings": [
            {
                "source_id": item["source_id"],
                "source_sha256": item["source_sha256"],
                "candidate_id": item["candidate"]["candidate_id"],
                "candidate_inventory_sha256": item["candidate"]["candidate_inventory"].get(
                    "sha256"
                ),
            }
            for item in dependencies["sources"]
        ],
        "bundle_completion_count": len(bundle.get("document_completions", [])),
    }


def _build_censuses(
    plan: dict[str, Any], dependencies: dict[str, Any], data_root: Path, raw_docling_scan: bool
) -> list[dict[str, Any]]:
    """Build per-source workload evidence from canonical and raw machine artifacts."""
    result = []
    for source in dependencies["sources"]:
        candidate = data_root / str(source["candidate"]["relative_path"])
        result.append(
            build_toc_census(
                candidate,
                source_id=str(source["source_id"]),
                source_ordinal=int(source["ordinal"]),
                data_root=data_root,
                raw_docling_scan=raw_docling_scan,
            )
        )
    return sorted(result, key=lambda item: int(item["source_ordinal"]))


def _object_list(value: dict[str, Any], field: str) -> list[dict[str, Any]]:
    """Require an object array at a machine-contract boundary."""
    observed = value.get(field)
    if not isinstance(observed, list) or not all(isinstance(item, dict) for item in observed):
        raise ValueError(f"expected object array: {field}")
    return cast(list[dict[str, Any]], observed)


def _default_output_path(review_run_id: str) -> str:
    """Return the non-review, source-free Gate A artifact path."""
    return (
        f"pipelines/brisbane_baylands/task_04_review/{review_run_id}/"
        "records/gate_a_preparation.json"
    )


__all__ = (
    "FINAL_PASS",
    "HANDOFF_ID",
    "SCOPE_ID",
    "final_review_policy",
    "prepare_task03j_final",
    "publish_gate_a_preparation",
)
