"""Record assembly for the source-free Task 04A Gate A preparation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from er_commons.human_review_support.task04.models import JsonObject


@dataclass(frozen=True)
class PreparationRecordInputs:
    """Named inputs needed to serialize one Gate A preparation record."""

    review_run_id: str
    final_pass: str
    schema_version: str
    policy: dict[str, Any]
    policy_sha256: str
    input_sha256: str
    implementation: dict[str, Any]
    implementation_sha256: str
    dependencies: dict[str, Any]
    task03i: dict[str, Any]
    bundle: dict[str, Any]
    handoff: dict[str, Any]
    censuses: list[dict[str, Any]]
    upstream_validation_ran: bool


def build_preparation_record(inputs: PreparationRecordInputs) -> dict[str, Any]:
    """Assemble the no-PDF-read Gate A record and expected workload."""
    workload = _workload(inputs.censuses, inputs.task03i, inputs.bundle)
    task03j = cast(JsonObject, inputs.dependencies["task03j"])
    readiness = cast(JsonObject, task03j["readiness"])
    activation_plan = cast(JsonObject, task03j["activation_plan"])
    return {
        "schema_version": f"{inputs.schema_version}.gate_a_preparation",
        "review_run_id": inputs.review_run_id,
        "pass": inputs.final_pass,
        "status": "source_free_prepared",
        "policy": inputs.policy,
        "policy_sha256": inputs.policy_sha256,
        "input_sha256": inputs.input_sha256,
        "implementation": inputs.implementation,
        "implementation_sha256": inputs.implementation_sha256,
        "upstream_validation": {
            "task03i_status": inputs.task03i["status"],
            "task03j_status": inputs.handoff["status"],
            "task03j_task04_status": inputs.handoff["task04_status"],
            "verified_document_count": len(inputs.bundle.get("document_completions", [])),
            "mode": (
                "owning_validator"
                if inputs.upstream_validation_ran
                else "record_shape_only_mvp_using_prior_validation_evidence"
            ),
            "validator": (
                "er_commons.collection_processing.handoff_validation.validate_collection_handoff"
            ),
        },
        "inputs": {
            "task03j": inputs.dependencies["task03j"],
            "task03i": inputs.dependencies["task03i"],
            "source_count": len(inputs.dependencies["sources"]),
            "source_order": [
                str(item["source_id"])
                for item in cast(list[JsonObject], inputs.dependencies["sources"])
            ],
            "readiness_path": readiness["path"],
            "activation_plan_path": activation_plan["path"],
        },
        "task03i_recheck_plan": {
            "finding_ids": inputs.task03i["finding_ids"],
            "finding_count": inputs.task03i["finding_count"],
            "required_outcome": "one_exact_task03j_evidence_outcome_per_applicable_finding",
            "historical_anchors_transfer": False,
        },
        "toc_candidate_census": _census_record(inputs.censuses),
        "expected_review_workload": workload,
        "source_free_boundary": {
            "source_pdf_bytes_read": False,
            "source_pdf_checksum_verified": False,
            "renders_generated": False,
            "model_files_read": False,
            "human_review_started": False,
            "gate_c_status": "not_started",
            "gate_d_status": "not_started",
            "next_authorization": (
                "explicit approval before source-PDF reads, renders, or human review"
            ),
        },
    }


def _workload(
    censuses: list[dict[str, Any]], task03i: dict[str, Any], bundle: dict[str, Any]
) -> dict[str, Any]:
    """Summarize expected human workload without declaring usability."""
    summaries = [cast(dict[str, Any], census["summary"]) for census in censuses]
    census_complete = bool(summaries)
    return {
        "source_count": len(bundle.get("document_completions", [])),
        "candidate_page_count": _sum_or_none(summaries, "candidate_page_count", census_complete),
        "seed_page_count": _sum_or_none(summaries, "seed_page_count", census_complete),
        "adjacent_page_count": _sum_or_none(summaries, "adjacent_page_count", census_complete),
        "ambiguous_toc_alias_count": _sum_or_none(
            summaries, "ambiguous_toc_alias_count", census_complete
        ),
        "ambiguous_reference_link_count": _sum_or_none(
            summaries, "ambiguous_reference_link_count", census_complete
        ),
        "raw_document_index_count": _sum_or_none(
            summaries, "raw_document_index_count", census_complete
        ),
        "substantive_table_control_count": _sum_or_none(
            summaries, "substantive_table_control_count", census_complete
        ),
        "toc_census_status": "completed" if census_complete else "deferred_to_gate_b",
        "task03i_finding_recheck_count": int(task03i["finding_count"]),
        "all_source_terminal_disposition_count": len(bundle.get("document_completions", [])),
        "claim_boundary": (
            "candidate_census_is_complete_only_for_the_frozen_machine_detectable_population"
            if census_complete
            else "candidate_census_not_computed_in_mvp_gate_a"
        ),
    }


def _sum_or_none(summaries: list[dict[str, Any]], field: str, census_complete: bool) -> int | None:
    """Sum one census field only after the production census has run."""
    if not census_complete:
        return None
    return sum(int(item[field]) for item in summaries)


def _census_record(censuses: list[dict[str, Any]]) -> list[dict[str, Any]] | dict[str, Any]:
    """Represent a completed census or its explicit MVP deferral."""
    if censuses:
        return censuses
    return {
        "status": "deferred_to_gate_b",
        "machine_artifact_scan_completed": False,
        "reason": (
            "MVP Gate A freezes the census policy and boundary; the large "
            "production machine-artifact scan is opt-in for Gate B"
        ),
    }


def path_reference(path: Path, root: Path, declared_sha256: str | None = None) -> JsonObject:
    """Describe an existing file while avoiding a second checksum pass."""
    reference: JsonObject = {
        "path": path.resolve().relative_to(root.resolve()).as_posix(),
        "byte_size": path.stat().st_size,
    }
    if declared_sha256 is not None:
        reference["sha256"] = declared_sha256
    return reference


__all__ = ["PreparationRecordInputs", "build_preparation_record", "path_reference"]
