"""Close and validate one reviewed Task 05E relationship candidate."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import (
    canonical_json_sha256,
    json_bytes,
    publish_bytes_no_clobber,
    read_json_object,
    read_jsonl,
)
from er_commons.response_inventory.acceptance import validate_task05d_candidate
from er_commons.response_inventory.contract import (
    build_record_id,
    semantic_bundle_digest,
    validate_managed_files,
    validate_record_bundle,
)

type JsonObject = dict[str, Any]

SCHEMA_VERSION = "er_commons.response_inventory.v1"
CANDIDATE_SCHEMA_VERSION = "er_commons.task05e.relationship_candidate.v1"
QUALITY_SCHEMA_VERSION = "er_commons.task05e.code_quality_review.v1"
REVIEW_SCHEMA_VERSION = "er_commons.task05e.bounded_review.v1"

_REVIEW_PAYLOAD_PATHS = (
    "diagnostics/individual_diagnostics.jsonl",
    "diagnostics/review_census.json",
    "graph/review_edges.jsonl",
    "records/activity.json",
    "review_views/review_views.jsonl",
)
_TERMINAL_WARNINGS = (
    "one malformed General Response membership target remains unresolved",
    "one reviewed source-label typo remains unresolved",
    "the source-authored SA-CHSRA-29 orphan remains explicit",
    "the reviewed SA-Caltrans-48 source form remains unpaired",
)


def publish_task05e_candidate(
    review_root: Path,
    quality_report_path: Path,
    repository_root: Path,
    artifact_root: Path,
) -> JsonObject:
    """Wrap an unchanged closed review pass in completion-last candidate records."""
    root = artifact_root.resolve()
    review = review_root.resolve()
    if not review.is_relative_to(root) or not review.is_dir():
        raise ValueError("05E review root is missing or escapes the artifact root")
    receipt = _validate_review_pass(review)
    quality = _load_quality_report(quality_report_path, repository_root, receipt)
    activity = cast(JsonObject, read_json_object(review / "records/activity.json"))
    census = cast(JsonObject, read_json_object(review / "diagnostics/review_census.json"))
    payloads = {path: (review / path).read_bytes() for path in _REVIEW_PAYLOAD_PATHS}
    payloads["records/review_receipt.json"] = (review / "records/review_receipt.json").read_bytes()
    payloads["reports/code_quality_review.json"] = json_bytes(quality)

    inventory = _inventory_record(activity, payloads)
    completion = _completion_record(activity, inventory, census, quality)
    schema = read_json_object(
        repository_root / "benchmarks/er_bench/schemas/response_inventory/v1/records.schema.json"
    )
    upstream_records = _load_upstream_records(activity, root, schema)
    derived_records = _derived_records(review)
    validate_record_bundle([*upstream_records, *derived_records, inventory, completion], schema)

    activity_hash = str(activity["activity_id"]).removeprefix("activityv1-")
    candidate = review.parent / f"revisionv1-{activity_hash}"
    reused = _reuse_candidate(candidate, root, repository_root, receipt, quality)
    if reused is not None:
        return reused
    _publish_atomically(
        candidate,
        payloads,
        inventory,
        completion,
        artifact_root=root,
        repository_root=repository_root,
    )
    return validate_task05e_candidate(candidate, root, repository_root)


def publish_task05e_acceptance(
    candidate_root: Path,
    artifact_root: Path,
    repository_root: Path,
    *,
    accepted_by: str,
    accepted_at: str,
) -> JsonObject:
    """Accept one validated candidate through an adjacent immutable pointer."""
    validation = validate_task05e_candidate(candidate_root, artifact_root, repository_root)
    try:
        parsed_time = datetime.fromisoformat(accepted_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("05E acceptance time must be ISO 8601") from error
    if parsed_time.tzinfo is None:
        raise ValueError("05E acceptance time must include a timezone")
    if not accepted_by.strip():
        raise ValueError("05E acceptance requires a nonempty reviewer identity")
    record: JsonObject = {
        "schema_version": "er_commons.task05e.acceptance.v1",
        "status": "accepted",
        "accepted_by": accepted_by,
        "accepted_at": accepted_at,
        "accepted_downstream_consumer": "task05f",
        "working_revision": validation["working_revision"],
        "activity_id": validation["activity_id"],
        "completion_id": validation["completion_id"],
        "completion_status": validation["completion_status"],
        "inventory_id": validation["inventory_id"],
        "semantic_digest": validation["semantic_digest"],
        "quality_gate": validation["quality_gate"],
    }
    record["acceptance_id"] = f"acceptancev1-{canonical_json_sha256(record)}"
    candidate = candidate_root.resolve()
    pointer = candidate.parent / f"{candidate.name}.acceptance.json"
    publish_bytes_no_clobber(pointer, json_bytes(record))
    return record


def validate_task05e_candidate(
    candidate_root: Path,
    artifact_root: Path,
    repository_root: Path,
) -> JsonObject:
    """Validate one terminal 05E candidate without creating acceptance state."""
    root = artifact_root.resolve()
    candidate = candidate_root.resolve()
    if not candidate.is_relative_to(root) or not candidate.is_dir():
        raise ValueError("05E candidate is missing or escapes the artifact root")
    completion = cast(JsonObject, read_json_object(candidate / "records/stage_completion.json"))
    inventory = cast(
        JsonObject, read_json_object(candidate / "records/managed_file_inventory.json")
    )
    receipt = _validate_review_pass(candidate)
    quality = cast(JsonObject, read_json_object(candidate / "reports/code_quality_review.json"))
    activity = cast(JsonObject, read_json_object(candidate / "records/activity.json"))
    census = cast(JsonObject, read_json_object(candidate / "diagnostics/review_census.json"))
    _validate_terminal_records(completion, inventory, activity, census, quality, receipt)
    schema = read_json_object(
        repository_root / "benchmarks/er_bench/schemas/response_inventory/v1/records.schema.json"
    )
    upstream_records = _load_upstream_records(activity, root, schema)
    derived_records = _derived_records(candidate)
    validate_record_bundle([*upstream_records, *derived_records, inventory, completion], schema)
    validate_managed_files(
        inventory,
        candidate,
        excluded_paths={
            "records/managed_file_inventory.json",
            "records/stage_completion.json",
        },
    )
    return {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "status": "valid_terminal_candidate",
        "candidate_root": candidate.as_posix(),
        "working_revision": candidate.relative_to(root).as_posix(),
        "activity_id": activity["activity_id"],
        "completion_id": completion["completion_id"],
        "completion_status": completion["status"],
        "inventory_id": inventory["inventory_id"],
        "semantic_digest": semantic_bundle_digest(derived_records),
        "managed_file_count": len(cast(list[JsonObject], inventory["files"])),
        "quality_gate": quality["status"],
        "source_pdf_accessed": False,
    }


def _validate_review_pass(review_root: Path) -> JsonObject:
    """Verify the exact nonterminal review bytes before candidate publication."""
    receipt = cast(JsonObject, read_json_object(review_root / "records/review_receipt.json"))
    if (
        receipt.get("schema_version") != REVIEW_SCHEMA_VERSION
        or receipt.get("status") != "bounded_review_complete_review_required"
        or receipt.get("completion_written") is not False
        or receipt.get("source_pdf_accessed") is not False
    ):
        raise ValueError("05E review receipt is not a source-free closed review pass")
    receipt_files = receipt.get("files")
    if not isinstance(receipt_files, list):
        raise ValueError("05E review receipt lacks its file list")
    typed_receipt_files = cast(list[JsonObject], receipt_files)
    if [item.get("path") for item in typed_receipt_files] != list(_REVIEW_PAYLOAD_PATHS):
        raise ValueError("05E review receipt file closure differs")
    _validate_receipt_files(review_root, receipt)
    census = cast(JsonObject, read_json_object(review_root / "diagnostics/review_census.json"))
    counts = cast(JsonObject, census.get("counts", {}))
    if (
        census.get("status") != "bounded_review_complete_review_required"
        or census.get("gate2_authorized") is not True
        or census.get("source_pdf_accessed") is not False
        or counts.get("intra_volume_mentions")
        != counts.get("resolved_mentions", 0) + counts.get("terminal_unresolved_mentions", 0)
        or counts.get("membership_claims")
        != counts.get("resolved_memberships", 0) + counts.get("terminal_unresolved_memberships", 0)
    ):
        raise ValueError("05E review census does not close every in-scope outcome")
    if census.get("mention_failure_categories") != {
        "ordinary_prose": 251,
        "response_section_heading": 8,
        "reviewed_source_label_typo_unresolved": 1,
        "running_header": 44,
        "self_mention": 7,
    }:
        raise ValueError("05E review mention outcomes differ from the reviewed closure")
    if census.get("membership_failure_categories") != {"exact_comment_target_absent": 1}:
        raise ValueError("05E review membership outcomes differ from the reviewed closure")
    if census.get("direct_pair_failure_labels") != [
        "Comment SA-CHSRA-29",
        "Comment SA-Caltrans-48",
        "Response SA-Caltrans-48a",
    ]:
        raise ValueError("05E direct-pair outcomes differ from the reviewed closure")
    return receipt


def _validate_receipt_files(root: Path, receipt: Mapping[str, Any]) -> None:
    files = receipt.get("files")
    if not isinstance(files, list):
        raise ValueError("05E review receipt lacks its file list")
    for item in cast(list[JsonObject], files):
        path = root / str(item["path"])
        content = path.read_bytes()
        if len(content) != item.get("byte_size") or hashlib.sha256(content).hexdigest() != item.get(
            "sha256"
        ):
            raise ValueError(f"05E review payload differs: {item.get('path')}")


def _load_quality_report(
    path: Path,
    repository_root: Path,
    receipt: Mapping[str, Any],
) -> JsonObject:
    """Require a passing report bound to the reviewed activity and current files."""
    report_path = path.resolve()
    repo = repository_root.resolve()
    if not report_path.is_relative_to(repo) or not report_path.is_file():
        raise ValueError("05E quality report must be a repository-local input")
    report = cast(JsonObject, read_json_object(report_path))
    if (
        report.get("schema_version") != QUALITY_SCHEMA_VERSION
        or report.get("status") != "pass"
        or report.get("activity_id") != receipt.get("activity_id")
        or report.get("semantic_digest") != receipt.get("semantic_digest")
        or report.get("material_findings") != []
    ):
        raise ValueError("05E quality report does not approve the exact review pass")
    criteria = report.get("criteria")
    if not isinstance(criteria, list):
        raise ValueError("05E quality report lacks its required criteria")
    typed_criteria = cast(list[JsonObject], criteria)
    if {item.get("name") for item in typed_criteria} != {
        "readability",
        "editability",
        "debugging",
        "operations",
        "testing",
    } or any(item.get("status") != "pass" for item in typed_criteria):
        raise ValueError("05E quality report does not pass every required criterion")
    reviewed_files = report.get("reviewed_files")
    if not isinstance(reviewed_files, list) or not reviewed_files:
        raise ValueError("05E quality report lacks reviewed repository files")
    for item in cast(list[JsonObject], reviewed_files):
        relative = Path(str(item["path"]))
        candidate = (repo / relative).resolve()
        if not candidate.is_relative_to(repo) or not candidate.is_file():
            raise ValueError(f"reviewed repository file is missing: {relative}")
        if hashlib.sha256(candidate.read_bytes()).hexdigest() != item.get("sha256"):
            raise ValueError(f"reviewed repository file changed after quality review: {relative}")
    return report


def _load_upstream_records(
    activity: Mapping[str, Any], artifact_root: Path, schema: JsonObject
) -> list[JsonObject]:
    """Load the accepted 05D records named by the reviewed 05E activity."""
    input_refs = cast(list[JsonObject], activity["input_refs"])
    refs = {str(item["role"]): item for item in input_refs}
    completion_path = (artifact_root / str(refs["task05d_completion"]["path"])).resolve()
    candidate_root = completion_path.parent.parent
    validation = validate_task05d_candidate(candidate_root, artifact_root)
    if validation["completion_id"] != refs["task05d_completion"]["identity"]:
        raise ValueError("05E activity names another Task 05D completion")
    source_records_path = candidate_root / "inventory/source_records.jsonl"
    records = [cast(JsonObject, row) for row in read_jsonl(source_records_path)]
    validate_record_bundle(records, schema)
    return records


def _derived_records(root: Path) -> list[JsonObject]:
    """Read authoritative 05E graph records in their semantic digest order."""
    return [
        read_json_object(root / "records/activity.json"),
        *[cast(JsonObject, row) for row in read_jsonl(root / "graph/review_edges.jsonl")],
        *[
            cast(JsonObject, row)
            for row in read_jsonl(root / "diagnostics/individual_diagnostics.jsonl")
        ],
        *[cast(JsonObject, row) for row in read_jsonl(root / "review_views/review_views.jsonl")],
    ]


def _inventory_record(activity: Mapping[str, Any], payloads: Mapping[str, bytes]) -> JsonObject:
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "managed_file_inventory",
        "stage": "05e",
        "activity_id": activity["activity_id"],
        "dependencies": activity["input_refs"],
        "files": [
            {
                "authority": "bundle",
                "path": path,
                "sha256": hashlib.sha256(content).hexdigest(),
                "byte_size": len(content),
            }
            for path, content in sorted(payloads.items())
        ],
    }
    record["inventory_id"] = build_record_id(record)
    return record


def _completion_record(
    activity: Mapping[str, Any],
    inventory: Mapping[str, Any],
    census: Mapping[str, Any],
    quality: Mapping[str, Any],
) -> JsonObject:
    counts = dict(census["counts"])
    counts.update(
        {
            f"{name}_edges": count
            for name, count in cast(Mapping[str, int], census["edge_counts_by_relation"]).items()
        }
    )
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "stage_completion",
        "stage": "05e",
        "status": "complete_with_warnings",
        "activity_id": activity["activity_id"],
        "inventory_id": inventory["inventory_id"],
        "counts": counts,
        "warnings": list(_TERMINAL_WARNINGS),
        "completed_at": quality["reviewed_at"],
    }
    record["completion_id"] = build_record_id(record)
    return record


def _validate_terminal_records(
    completion: Mapping[str, Any],
    inventory: Mapping[str, Any],
    activity: Mapping[str, Any],
    census: Mapping[str, Any],
    quality: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> None:
    """Reconcile terminal identity, review evidence, warnings, and counts."""
    if (
        completion.get("stage") != "05e"
        or completion.get("status") != "complete_with_warnings"
        or completion.get("activity_id") != activity.get("activity_id")
        or completion.get("inventory_id") != inventory.get("inventory_id")
        or inventory.get("stage") != "05e"
        or inventory.get("activity_id") != activity.get("activity_id")
    ):
        raise ValueError("05E terminal records do not describe one candidate")
    if inventory.get("dependencies") != activity.get("input_refs"):
        raise ValueError("05E inventory dependencies differ from its activity")
    expected_completion = _completion_record(activity, inventory, census, quality)
    if completion != expected_completion:
        raise ValueError("05E completion differs from the reviewed census")
    if (
        quality.get("status") != "pass"
        or quality.get("activity_id") != activity.get("activity_id")
        or quality.get("semantic_digest") != receipt.get("semantic_digest")
    ):
        raise ValueError("05E terminal candidate lacks its passing quality gate")


def _publish_atomically(
    candidate_root: Path,
    payloads: Mapping[str, bytes],
    inventory: JsonObject,
    completion: JsonObject,
    *,
    artifact_root: Path,
    repository_root: Path,
) -> None:
    """Expose a candidate only after its complete staged closure validates."""
    candidate_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{candidate_root.name}.staging-", dir=candidate_root.parent)
    )
    published = False
    try:
        for relative_path, content in sorted(payloads.items()):
            publish_bytes_no_clobber(staging / relative_path, content)
        publish_bytes_no_clobber(
            staging / "records/managed_file_inventory.json", json_bytes(inventory)
        )
        validate_managed_files(
            inventory,
            staging,
            excluded_paths={
                "records/managed_file_inventory.json",
                "records/stage_completion.json",
            },
        )
        publish_bytes_no_clobber(staging / "records/stage_completion.json", json_bytes(completion))
        validate_task05e_candidate(staging, artifact_root, repository_root)
        staging.rename(candidate_root)
        published = True
    finally:
        if not published and staging.exists():
            shutil.rmtree(staging)


def _reuse_candidate(
    candidate: Path,
    artifact_root: Path,
    repository_root: Path,
    receipt: Mapping[str, Any],
    quality: Mapping[str, Any],
) -> JsonObject | None:
    if not candidate.exists():
        return None
    result = validate_task05e_candidate(candidate, artifact_root, repository_root)
    if (
        read_json_object(candidate / "records/review_receipt.json") != receipt
        or read_json_object(candidate / "reports/code_quality_review.json") != quality
    ):
        raise ValueError("existing 05E candidate differs from requested closure")
    result["reuse_verified"] = True
    return result


__all__ = [
    "publish_task05e_acceptance",
    "publish_task05e_candidate",
    "validate_task05e_candidate",
]
