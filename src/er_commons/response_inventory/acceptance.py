"""Explicit post-review acceptance for a terminal Task 05D working revision."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from er_commons.artifact_io import (
    canonical_json_sha256,
    json_bytes,
    publish_bytes_no_clobber,
    read_json_object,
    read_jsonl,
)
from er_commons.response_inventory.contract import (
    semantic_bundle_digest,
    task05d_completion_counts,
    task05d_warning_entries,
    validate_managed_files,
)
from er_commons.response_inventory.task05d_policy import TASK05D_ALLOWED_WARNING_CODES

type JsonObject = dict[str, Any]


def publish_task05d_acceptance(
    candidate_root: Path,
    artifact_root: Path,
    *,
    accepted_by: str,
    accepted_at: str,
) -> JsonObject:
    """Validate and accept one unchanged terminal 05D revision outside its closure."""
    validation = validate_task05d_candidate(candidate_root, artifact_root)
    record = _acceptance_record(
        Path(str(validation["working_revision"])),
        {
            "activity_id": validation["activity_id"],
            "completion_id": validation["completion_id"],
            "status": validation["completion_status"],
        },
        {"inventory_id": validation["inventory_id"]},
        {
            "semantic_digest": validation["semantic_digest"],
            "diagnostic_counts": validation["diagnostic_counts"],
        },
        accepted_by=accepted_by,
        accepted_at=accepted_at,
    )
    candidate = candidate_root.resolve()
    path = candidate.parent / f"{candidate.name}.acceptance.json"
    publish_bytes_no_clobber(path, json_bytes(record))
    return record


def validate_task05d_candidate(candidate_root: Path, artifact_root: Path) -> JsonObject:
    """Validate one terminal Task 05D candidate without writing acceptance state."""
    root = artifact_root.resolve()
    candidate = candidate_root.resolve()
    if not candidate.is_relative_to(root) or not candidate.is_dir():
        raise ValueError("05D candidate is missing or escapes the artifact root")
    completion = read_json_object(candidate / "records/stage_completion.json")
    inventory = read_json_object(candidate / "records/managed_file_inventory.json")
    summary = read_json_object(candidate / "diagnostics/build_summary.json")
    qualification = read_json_object(candidate / "diagnostics/qualification.json")
    structural = read_json_object(candidate / "diagnostics/structural_accounting.json")
    records = [dict(row) for row in read_jsonl(candidate / "inventory/source_records.jsonl")]
    activity = next((row for row in records if row.get("record_type") == "activity"), None)
    _validate_terminal_candidate(
        completion,
        inventory,
        summary,
        qualification,
        structural,
        activity,
        records,
    )
    validate_managed_files(
        inventory,
        candidate,
        excluded_paths={
            "records/managed_file_inventory.json",
            "records/stage_completion.json",
        },
    )
    managed_files = inventory.get("files")
    if not isinstance(managed_files, list):
        raise ValueError("05D managed inventory lacks its file list")
    return {
        "schema_version": "er_commons.task05d.candidate_validation.v1",
        "status": "valid",
        "candidate_root": candidate.as_posix(),
        "working_revision": candidate.relative_to(root).as_posix(),
        "activity_id": completion["activity_id"],
        "completion_id": completion["completion_id"],
        "completion_status": completion["status"],
        "inventory_id": inventory["inventory_id"],
        "semantic_digest": summary["semantic_digest"],
        "diagnostic_counts": summary["diagnostic_counts"],
        "managed_file_count": len(managed_files),
    }


def _validate_terminal_candidate(
    completion: Mapping[str, Any],
    inventory: Mapping[str, Any],
    summary: Mapping[str, Any],
    qualification: Mapping[str, Any],
    structural: Mapping[str, Any],
    activity: Mapping[str, Any] | None,
    records: list[JsonObject],
) -> None:
    """Reject nonterminal or internally mismatched candidates before acceptance."""
    if activity is None:
        raise ValueError("05D candidate has no activity record")
    _validate_candidate_identity(completion, inventory, summary, activity, records)
    _validate_candidate_warnings(completion, summary, activity, records)
    _validate_candidate_reports(summary, qualification, structural, records)
    _validate_review_completion(qualification)


def _validate_candidate_identity(
    completion: Mapping[str, Any],
    inventory: Mapping[str, Any],
    summary: Mapping[str, Any],
    activity: Mapping[str, Any],
    records: list[JsonObject],
) -> None:
    """Require the terminal records and summary to name one unchanged activity."""
    if completion.get("stage") != "05d" or completion.get("status") not in {
        "complete",
        "complete_with_warnings",
    }:
        raise ValueError("acceptance requires one terminal Task 05D candidate")
    if activity.get("activity_id") != completion.get("activity_id"):
        raise ValueError("05D completion and activity identities differ")
    if inventory.get("inventory_id") != completion.get("inventory_id"):
        raise ValueError("05D completion and managed inventory identities differ")
    if inventory.get("activity_id") != activity.get("activity_id"):
        raise ValueError("05D inventory and activity identities differ")
    if summary.get("activity_id") != activity.get("activity_id"):
        raise ValueError("05D summary and activity identities differ")
    if summary.get("semantic_digest") != semantic_bundle_digest(records):
        raise ValueError("05D summary semantic digest differs from the candidate")


def _validate_candidate_warnings(
    completion: Mapping[str, Any],
    summary: Mapping[str, Any],
    activity: Mapping[str, Any],
    records: list[JsonObject],
) -> None:
    """Reconcile allowed warning classes, occurrences, status, and counts."""
    allowed_codes = summary.get("allowed_terminal_warning_codes")
    if allowed_codes != list(TASK05D_ALLOWED_WARNING_CODES):
        raise ValueError("05D summary warning policy differs from the accepted run spec")
    warnings = task05d_warning_entries(
        records,
        str(activity["activity_id"]),
        allowed_codes=allowed_codes,
    )
    expected_status = "complete_with_warnings" if warnings else "complete"
    if completion.get("status") != expected_status or completion.get("warnings") != list(warnings):
        raise ValueError("05D completion warnings differ from candidate diagnostics")
    if completion.get("counts") != task05d_completion_counts(activity, records):
        raise ValueError("05D completion counts differ from candidate records")
    diagnostic_counts = dict(
        sorted(
            Counter(
                str(record["code"])
                for record in records
                if record.get("record_type") == "diagnostic"
            ).items()
        )
    )
    if summary.get("diagnostic_counts") != diagnostic_counts:
        raise ValueError("05D summary diagnostic counts differ from candidate records")


def _validate_candidate_reports(
    summary: Mapping[str, Any],
    qualification: Mapping[str, Any],
    structural: Mapping[str, Any],
    records: list[JsonObject],
) -> None:
    """Verify derived report digests and diagnostic-instance accounting."""
    structural_payload = dict(structural)
    structural_digest = structural_payload.pop("report_digest", None)
    if (
        structural_digest != canonical_json_sha256(structural_payload)
        or summary.get("structural_accounting_digest") != structural_digest
    ):
        raise ValueError("05D structural-accounting digest differs")
    population = qualification.get("review_population")
    pages = qualification.get("pages")
    if not isinstance(population, list) or not isinstance(pages, list):
        raise ValueError("05D qualification lacks its frozen review population")
    population_digest = canonical_json_sha256(population)
    if (
        qualification.get("review_population_digest") != population_digest
        or summary.get("review_population_digest") != population_digest
    ):
        raise ValueError("05D review-population digest differs")

    diagnostic_ids = sorted(
        str(record["diagnostic_id"])
        for record in records
        if record.get("record_type") == "diagnostic"
    )
    instances = structural.get("diagnostic_instances")
    if (
        not isinstance(instances, list)
        or sorted(str(row.get("diagnostic_id")) for row in instances if isinstance(row, dict))
        != diagnostic_ids
    ):
        raise ValueError("05D structural accounting differs from candidate diagnostics")


def _validate_review_completion(qualification: Mapping[str, Any]) -> None:
    """Require every page in the frozen population to be explicitly accepted."""
    population = qualification.get("review_population")
    pages = qualification.get("pages")
    if not isinstance(population, list) or not isinstance(pages, list):
        raise ValueError("05D qualification lacks its frozen review population")
    required_pages = {int(row["physical_page"]) for row in population if isinstance(row, dict)}
    accepted_pages = {
        int(row["physical_page"])
        for row in pages
        if isinstance(row, dict)
        and isinstance(row.get("visual_disposition"), dict)
        and row["visual_disposition"].get("status") == "accepted"
    }
    missing_or_nonaccepted = sorted(required_pages - accepted_pages)
    reported_unresolved = qualification.get("unresolved_review_pages")
    if (
        qualification.get("review_complete") is not True
        or reported_unresolved != []
        or missing_or_nonaccepted
    ):
        raise ValueError(
            "05D acceptance requires every frozen review page to be accepted: "
            f"missing_or_nonaccepted_pages={_bounded_pages(missing_or_nonaccepted)}; "
            f"reported_unresolved_pages={_bounded_pages(reported_unresolved)}; "
            f"review_complete={qualification.get('review_complete')!r}"
        )


def _bounded_pages(value: object, *, limit: int = 20) -> str:
    """Render exact physical page IDs while bounding malformed or long diagnostics."""
    if not isinstance(value, (list, tuple, set)):
        return repr(value)
    pages = sorted(page for page in value if isinstance(page, int) and not isinstance(page, bool))
    shown = pages[:limit]
    suffix = f"...(+{len(pages) - limit} more)" if len(pages) > limit else ""
    return f"{shown}{suffix}"


def _acceptance_record(
    candidate_path: Path,
    completion: Mapping[str, Any],
    inventory: Mapping[str, Any],
    summary: Mapping[str, Any],
    *,
    accepted_by: str,
    accepted_at: str,
) -> JsonObject:
    """Build the compact immutable pointer written only after explicit acceptance."""
    if not accepted_by.strip() or not accepted_at.strip():
        raise ValueError("acceptance requires nonempty reviewer and timestamp")
    record: JsonObject = {
        "schema_version": "er_commons.task05d.acceptance.v1",
        "task_id": "05D",
        "status": "accepted",
        "working_revision": candidate_path.as_posix(),
        "activity_id": completion["activity_id"],
        "completion_id": completion["completion_id"],
        "completion_status": completion["status"],
        "inventory_id": inventory["inventory_id"],
        "semantic_digest": summary["semantic_digest"],
        "accepted_warning_counts": summary["diagnostic_counts"],
        "downstream_consumers": ["05E"],
        "accepted_by": accepted_by.strip(),
        "accepted_at": accepted_at.strip(),
    }
    record["acceptance_id"] = f"acceptancev1-{canonical_json_sha256(record)}"
    return record


__all__ = ["publish_task05d_acceptance", "validate_task05d_candidate"]
