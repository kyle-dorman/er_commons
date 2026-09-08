"""Completion-last Task 05C pilot workflow over bounded range observations."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import (
    json_bytes,
    jsonl_bytes,
    publish_bytes_no_clobber,
    read_json_object,
    read_jsonl,
    sha256_file,
    write_json_atomic,
)
from er_commons.response_inventory.code_inventory import owned_code_digest
from er_commons.response_inventory.contract import (
    SCHEMA_VERSION,
    build_record_id,
    semantic_bundle_digest,
    validate_managed_files,
    validate_record_bundle,
)
from er_commons.response_inventory.observations import (
    PageObservation,
    observation_from_dict,
    observation_to_dict,
)
from er_commons.response_inventory.pdf_access import read_pdfium_range
from er_commons.response_inventory.pilot_policy import TASK05C_RIGHT_CENSORED_RANGE
from er_commons.response_inventory.producer import build_source_records
from er_commons.response_inventory.qualification import (
    apply_visual_dispositions,
    flag_record_review_pages,
    poppler_versions,
    qualify_selected_pages,
    validate_qualification_report,
)
from er_commons.response_inventory.range_receipts import (
    build_range_receipt,
    contiguous_range_key,
    pilot_aggregation_is_ready,
    range_receipt_is_reusable,
)
from er_commons.response_inventory.run_spec import (
    ResponseInventoryRunSpec,
    load_response_inventory_run_spec,
    verify_repository_bindings,
)

type JsonObject = dict[str, Any]
type PageReader = Callable[[Path, int, int], list[PageObservation]]
type PageQualifier = Callable[[Path, Sequence[PageObservation], Path], JsonObject]

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class _RangeResult:
    """Validated evidence returned by one operational restart unit."""

    observations: list[PageObservation]
    receipt: JsonObject
    reused: bool


def build_pilot(
    run_spec_path: Path,
    repository_root: Path,
    artifact_root: Path,
    *,
    page_reader: PageReader = read_pdfium_range,
    page_qualifier: PageQualifier = qualify_selected_pages,
    visual_dispositions: Mapping[int, str] | None = None,
    tool_versions: Mapping[str, str] | None = None,
    completed_at: str | None = None,
) -> JsonObject:
    """Build one exact pilot, reusing only evidence-matched range receipts."""
    spec, config_sha256 = load_response_inventory_run_spec(run_spec_path)
    verify_repository_bindings(spec, repository_root)
    _verify_artifact_bindings(spec, artifact_root)
    schema_path = _repository_binding_path(spec, repository_root, "response_record_schema")
    schema = cast(JsonObject, json.loads(schema_path.read_text(encoding="utf-8")))
    code_sha256 = owned_code_digest(repository_root)
    observed_tool_versions = {
        "pypdfium2": version("pypdfium2"),
        **(dict(tool_versions) if tool_versions is not None else poppler_versions()),
    }
    activity = _activity_record(spec, config_sha256, code_sha256, observed_tool_versions)
    activity_hash = str(activity["activity_id"]).removeprefix("activityv1-")
    task_root = artifact_root / spec.output_policy.artifact_relative_root
    pilot_root = task_root / spec.output_policy.pilot_namespace_template.format(
        activity_hash=activity_hash
    )
    cache_root = task_root / Path(
        str(spec.cache_policy.relative_path_template).format(activity_hash=activity_hash)
    )
    reused = _reuse_completed_pilot(pilot_root, schema, activity)
    if reused is not None:
        return reused

    receipt_digests = _receipt_digests(activity, config_sha256)
    source_path = artifact_root / spec.source.path
    observations, receipts, reused_ranges = _collect_range_evidence(
        spec,
        activity,
        schema,
        source_path,
        cache_root,
        receipt_digests,
        page_reader,
    )

    if not pilot_aggregation_is_ready(receipts):
        raise ValueError("pilot range receipts do not close the exact 14-range selection")
    review_root = cache_root / "review"
    review_path = review_root / "qualification.json"
    cached_qualification = _load_optional_object(review_path)
    if visual_dispositions is not None and _qualification_is_reusable(
        cached_qualification, observations, cache_root / "qualification"
    ):
        if cached_qualification is None:
            raise RuntimeError("qualification reuse succeeded without cached evidence")
        qualification = cached_qualification
    else:
        qualification = page_qualifier(source_path, observations, cache_root / "qualification")
    validate_qualification_report(qualification, observations, cache_root / "qualification")
    source_records = build_source_records(activity, observations)
    source_digest = validate_record_bundle(source_records, schema)
    qualification = flag_record_review_pages(qualification, source_records)
    qualification, unresolved_review_pages = apply_visual_dispositions(
        qualification, dict(visual_dispositions) if visual_dispositions is not None else None
    )
    if unresolved_review_pages:
        LOGGER.info(
            "Task 05C pilot awaits visual review for %d pages",
            len(unresolved_review_pages),
        )
        write_json_atomic(review_path, qualification)
        write_json_atomic(
            review_root / "source_records.json",
            {"records": source_records, "semantic_digest": source_digest},
        )
        return {
            "status": "review_required",
            "pilot_root": str(pilot_root),
            "activity_id": activity["activity_id"],
            "review_packet": str(review_root / "qualification.json"),
            "unresolved_review_pages": list(unresolved_review_pages),
            "reused_ranges": reused_ranges,
        }
    counts = _completion_counts(activity, source_records)
    summary = {
        "schema_version": "er_commons.response_inventory.pilot_summary.v1",
        "activity_id": activity["activity_id"],
        "semantic_digest": source_digest,
        "counts": counts,
    }
    managed_payloads = {
        "inventory/source_records.jsonl": jsonl_bytes(source_records),
        "diagnostics/qualification.json": json_bytes(qualification),
        "diagnostics/build_summary.json": json_bytes(summary),
    }
    inventory = _inventory_record(activity, managed_payloads)
    completion = _completion_record(
        activity,
        inventory,
        counts,
        completed_at or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    )
    validate_record_bundle([*source_records, inventory, completion], schema)
    for relative_path, payload in managed_payloads.items():
        publish_bytes_no_clobber(pilot_root / relative_path, payload)
    inventory_path = pilot_root / "records/managed_file_inventory.json"
    completion_path = pilot_root / "records/stage_completion.json"
    publish_bytes_no_clobber(inventory_path, json_bytes(inventory))
    validate_managed_files(
        inventory,
        pilot_root,
        excluded_paths={
            "records/managed_file_inventory.json",
            "records/stage_completion.json",
        },
    )
    publish_bytes_no_clobber(completion_path, json_bytes(completion))
    LOGGER.info("completed Task 05C pilot activity %s", activity["activity_id"])
    return {
        "pilot_root": str(pilot_root),
        "activity_id": activity["activity_id"],
        "completion_id": completion["completion_id"],
        "semantic_digest": semantic_bundle_digest(source_records),
        "reused_ranges": reused_ranges,
    }


def _collect_range_evidence(
    spec: ResponseInventoryRunSpec,
    activity: JsonObject,
    schema: JsonObject,
    source_path: Path,
    cache_root: Path,
    receipt_digests: JsonObject,
    page_reader: PageReader,
) -> tuple[list[PageObservation], list[JsonObject], int]:
    """Load or build every declared range and preserve their exact order."""
    observations: list[PageObservation] = []
    receipts: list[JsonObject] = []
    reused_ranges = 0
    for page_range in spec.page_ranges:
        bounds = (page_range.first_page, page_range.last_page)
        result = _load_or_build_range(
            bounds,
            activity,
            schema,
            source_path,
            cache_root,
            receipt_digests,
            page_reader,
        )
        observations.extend(result.observations)
        receipts.append(result.receipt)
        reused_ranges += int(result.reused)
    return observations, receipts, reused_ranges


def _load_or_build_range(
    bounds: tuple[int, int],
    activity: JsonObject,
    schema: JsonObject,
    source_path: Path,
    cache_root: Path,
    receipt_digests: JsonObject,
    page_reader: PageReader,
) -> _RangeResult:
    """Reuse exact cache evidence or atomically replace one failed/stale range."""
    key = contiguous_range_key(bounds)
    range_root = cache_root / "ranges" / key
    observations_path = range_root / "observations.json"
    receipt_path = range_root / "receipt.json"
    current = _load_observations(observations_path)
    if current is not None:
        current = _apply_range_boundary_policy(current, bounds)
    receipt = _load_optional_object(receipt_path)
    if current is not None and _range_cache_is_reusable(
        current,
        receipt,
        bounds,
        activity,
        schema,
        observations_path,
        receipt_digests,
    ):
        LOGGER.info("reusing Task 05C pilot range %s", key)
        if receipt is None:  # Defensive: reuse requires a receipt.
            raise RuntimeError(f"range {key} reuse lost its receipt")
        return _RangeResult(current, receipt, True)

    LOGGER.info("building Task 05C pilot range %s", key)
    try:
        current = page_reader(source_path, *bounds)
        _require_exact_range(current, bounds)
        current = _apply_range_boundary_policy(current, bounds)
        semantic_digest = _range_semantic_digest(activity, bounds, current, schema)
        write_json_atomic(
            observations_path,
            {"observations": [observation_to_dict(item) for item in current]},
        )
        receipt = build_range_receipt(
            bounds,
            status="complete",
            bindings=activity["input_refs"],
            digests=receipt_digests,
            files=[_range_observation_file(key, observations_path)],
            semantic_digest=semantic_digest,
        )
        write_json_atomic(receipt_path, receipt)
        return _RangeResult(current, receipt, False)
    except Exception as error:
        _record_range_failure(bounds, key, receipt_path, activity, receipt_digests, error)
        raise


def _range_cache_is_reusable(
    observations: Sequence[PageObservation],
    receipt: JsonObject | None,
    bounds: tuple[int, int],
    activity: JsonObject,
    schema: JsonObject,
    observations_path: Path,
    receipt_digests: JsonObject,
) -> bool:
    """Compare cached range evidence with every current semantic binding."""
    if receipt is None:
        return False
    semantic_digest = _range_semantic_digest(activity, bounds, observations, schema)
    return range_receipt_is_reusable(
        receipt,
        bounds,
        bindings=activity["input_refs"],
        digests=receipt_digests,
        files=[_range_observation_file(contiguous_range_key(bounds), observations_path)],
        semantic_digest=semantic_digest,
    )


def _range_observation_file(key: str, path: Path) -> JsonObject:
    """Describe the one cache payload owned by a range receipt."""
    return {"path": f"ranges/{key}/observations.json", "byte_size": path.stat().st_size}


def _record_range_failure(
    bounds: tuple[int, int],
    key: str,
    receipt_path: Path,
    activity: JsonObject,
    receipt_digests: JsonObject,
    error: Exception,
) -> None:
    """Persist concise range failure evidence while preserving the traceback."""
    failed_receipt = build_range_receipt(
        bounds,
        status="failed",
        bindings=activity["input_refs"],
        digests=receipt_digests,
        files=[],
        semantic_digest=None,
        failure=f"{type(error).__name__}: {error}",
    )
    try:
        write_json_atomic(receipt_path, failed_receipt)
    except Exception:
        LOGGER.exception("could not persist failed range receipt for %s", key)
    LOGGER.exception("Task 05C pilot range %s failed", key)


def _reuse_completed_pilot(
    pilot_root: Path, schema: JsonObject, expected_activity: Mapping[str, Any]
) -> JsonObject | None:
    completion_path = pilot_root / "records/stage_completion.json"
    inventory_path = pilot_root / "records/managed_file_inventory.json"
    records_path = pilot_root / "inventory/source_records.jsonl"
    if not completion_path.is_file():
        return None
    if not inventory_path.is_file() or not records_path.is_file():
        raise ValueError("completed pilot is missing its inventory or source records")
    completion = read_json_object(completion_path)
    inventory = read_json_object(inventory_path)
    source_records = [cast(JsonObject, item) for item in read_jsonl(records_path)]
    activities = [record for record in source_records if record["record_type"] == "activity"]
    if len(activities) != 1 or activities[0] != expected_activity:
        raise ValueError("completed pilot activity differs from the requested run")
    validate_record_bundle([*source_records, inventory, completion], schema)
    validate_managed_files(
        inventory,
        pilot_root,
        excluded_paths={
            "records/managed_file_inventory.json",
            "records/stage_completion.json",
        },
    )
    return {
        "pilot_root": str(pilot_root),
        "activity_id": expected_activity["activity_id"],
        "completion_id": completion["completion_id"],
        "semantic_digest": semantic_bundle_digest(source_records),
        "reused_ranges": len(expected_activity["page_ranges"]),
    }


def _verify_artifact_bindings(spec: ResponseInventoryRunSpec, artifact_root: Path) -> None:
    root = artifact_root.resolve()
    for reference in spec.accepted_inputs:
        path = (root / reference.path).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"accepted input is missing or escapes the artifact root: {path}")
        if path.stat().st_size != reference.byte_size or sha256_file(path) != reference.sha256:
            raise ValueError(f"accepted input binding mismatch: {reference.role}")
    source_path = (root / spec.source.path).resolve()
    if not source_path.is_relative_to(root) or not source_path.is_file():
        raise ValueError("response source is missing or escapes the artifact root")
    if source_path.stat().st_size != spec.source.recorded_byte_size:
        raise ValueError("response source byte size differs from its frozen record")
    _verify_source_manifest(spec, root)
    _verify_source_release_completion(spec, root)
    _verify_task05a_acceptance(spec, root)


def _verify_source_release_completion(spec: ResponseInventoryRunSpec, root: Path) -> None:
    reference = next(
        item for item in spec.accepted_inputs if item.role == "source_release_completion"
    )
    completion = read_json_object(root / reference.path)
    if completion.get("schema_version") != "er_commons.source_release_completion.v1":
        raise ValueError("source release completion has an unexpected schema")
    if completion.get("source_release_version") != spec.source.source_release_version:
        raise ValueError("source release completion names another release")
    manifest = completion.get("manifest")
    source_manifest = next(item for item in spec.accepted_inputs if item.role == "source_manifest")
    if not isinstance(manifest, dict) or (
        manifest.get("local_path") != source_manifest.path.as_posix()
        or manifest.get("byte_size") != source_manifest.byte_size
        or manifest.get("sha256") != source_manifest.sha256
    ):
        raise ValueError("source release completion does not seal the accepted manifest")


def _verify_source_manifest(spec: ResponseInventoryRunSpec, root: Path) -> None:
    reference = next(item for item in spec.accepted_inputs if item.role == "source_manifest")
    manifest = read_json_object(root / reference.path)
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        raise ValueError("source manifest lacks a sources list")
    matches = [
        item
        for item in sources
        if isinstance(item, dict) and item.get("source_id") == spec.source.source_id
    ]
    if len(matches) != 1:
        raise ValueError("source manifest does not contain exactly one response source")
    source = matches[0]
    expected = {
        "source_role": spec.source.source_role,
        "local_path": spec.source.path.as_posix(),
        "sha256": spec.source.recorded_sha256,
        "byte_size": spec.source.recorded_byte_size,
        "pdf_page_count": spec.source.recorded_page_count,
        "retrieval_status": spec.source.retrieval_status,
        "validation_status": spec.source.validation_status,
    }
    if any(source.get(field) != value for field, value in expected.items()):
        raise ValueError("response source metadata differs from its manifest row")


def _verify_task05a_acceptance(spec: ResponseInventoryRunSpec, root: Path) -> None:
    completion = next(item for item in spec.accepted_inputs if item.role == "task05a_completion")
    acceptance_path = (root / completion.path).with_name("task05a_acceptance.json")
    acceptance = read_json_object(acceptance_path)
    accepted = acceptance.get("accepted_completion")
    if acceptance.get("status") != "accepted" or not isinstance(accepted, dict):
        raise ValueError("Task 05A acceptance is absent or not accepted")
    expected_path = completion.path.name
    if (
        accepted.get("path") != f"records/{expected_path}"
        or accepted.get("byte_size") != completion.byte_size
        or accepted.get("sha256") != completion.sha256
    ):
        raise ValueError("Task 05A acceptance names another completion")


def _repository_binding_path(spec: ResponseInventoryRunSpec, root: Path, role: str) -> Path:
    binding = next(item for item in spec.repository_bindings if item.role == role)
    return root / binding.path


def _activity_record(
    spec: ResponseInventoryRunSpec,
    config_sha256: str,
    code_sha256: str,
    tool_versions: Mapping[str, str],
) -> JsonObject:
    source_manifest = next(item for item in spec.accepted_inputs if item.role == "source_manifest")
    task05a = next(item for item in spec.accepted_inputs if item.role == "task05a_completion")
    input_refs = sorted(
        [
            {
                "role": "source_record",
                "identity": f"{spec.source.source_id}@{spec.source.recorded_sha256}",
                "authority": "artifact_root",
                "path": source_manifest.path.as_posix(),
            },
            {
                "role": "task05a_completion",
                "identity": task05a.sha256,
                "authority": "artifact_root",
                "path": task05a.path.as_posix(),
            },
        ],
        key=lambda item: (item["role"], item["identity"], item["path"]),
    )
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "activity",
        "stage": "05c",
        "source_id": spec.source.source_id,
        "page_ranges": [[item.first_page, item.last_page] for item in spec.page_ranges],
        "config_sha256": config_sha256,
        "schema_sha256": next(
            item.sha256
            for item in spec.repository_bindings
            if item.role == "response_record_schema"
        ),
        "code_sha256": code_sha256,
        "tool_versions": dict(sorted(tool_versions.items())),
        "input_refs": input_refs,
    }
    record["activity_id"] = build_record_id(record)
    return record


def _range_activity(activity: Mapping[str, Any], bounds: tuple[int, int]) -> JsonObject:
    record = {key: value for key, value in activity.items() if key != "activity_id"}
    record["page_ranges"] = [list(bounds)]
    record["activity_id"] = build_record_id(record)
    return record


def _range_semantic_digest(
    activity: Mapping[str, Any],
    bounds: tuple[int, int],
    observations: Sequence[PageObservation],
    schema: JsonObject,
) -> str:
    _require_exact_range(observations, bounds)
    records = build_source_records(_range_activity(activity, bounds), observations)
    return validate_record_bundle(records, schema)


def _require_exact_range(observations: Sequence[PageObservation], bounds: tuple[int, int]) -> None:
    expected = list(range(bounds[0], bounds[1] + 1))
    observed = sorted(item.physical_page for item in observations)
    if observed != expected:
        raise ValueError(f"page reader did not close range {bounds[0]}-{bounds[1]}")


def _apply_range_boundary_policy(
    observations: Sequence[PageObservation], bounds: tuple[int, int]
) -> list[PageObservation]:
    """Apply the accepted profile's sole right-censored pilot range policy."""
    _require_exact_range(observations, bounds)
    return [
        replace(
            observation,
            closes_open_unit=(
                observation.closes_open_unit
                or (
                    observation.physical_page == bounds[1]
                    and bounds != TASK05C_RIGHT_CENSORED_RANGE
                )
            ),
        )
        for observation in observations
    ]


def _receipt_digests(activity: Mapping[str, Any], run_spec_sha256: str) -> JsonObject:
    return {
        "code_sha256": activity["code_sha256"],
        "config_sha256": activity["config_sha256"],
        "run_spec_sha256": run_spec_sha256,
        "schema_sha256": activity["schema_sha256"],
    }


def _load_observations(path: Path) -> list[PageObservation] | None:
    if not path.is_file():
        return None
    try:
        value = read_json_object(path).get("observations")
    except ValueError as error:
        LOGGER.warning("ignoring unreadable observation cache %s: %s", path, error)
        return None
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        LOGGER.warning("ignoring malformed observation cache %s", path)
        return None
    try:
        return [observation_from_dict(cast(dict[str, Any], item)) for item in value]
    except (KeyError, TypeError, ValueError) as error:
        LOGGER.warning("ignoring invalid observation cache %s: %s", path, error)
        return None


def _load_optional_object(path: Path) -> JsonObject | None:
    if not path.is_file():
        return None
    try:
        return cast(JsonObject, read_json_object(path))
    except ValueError as error:
        LOGGER.warning("ignoring unreadable JSON cache %s: %s", path, error)
        return None


def _qualification_is_reusable(
    report: JsonObject | None,
    observations: Sequence[PageObservation],
    cache_root: Path,
) -> bool:
    """Reuse only complete evidence bound to the current page observations."""
    if report is None:
        return False
    try:
        validate_qualification_report(report, observations, cache_root)
    except ValueError as error:
        LOGGER.info("cached qualification is not reusable: %s", error)
        return False
    return True


def _completion_counts(activity: Mapping[str, Any], records: Sequence[JsonObject]) -> JsonObject:
    units = [record for record in records if record["record_type"] == "source_unit"]
    diagnostics = [record for record in records if record["record_type"] == "diagnostic"]
    ranges = activity["page_ranges"]
    return {
        "declared_ranges": len(ranges),
        "completed_ranges": len(ranges),
        "failed_ranges": 0,
        "declared_pages": sum(end - start + 1 for start, end in ranges),
        "emitted_pages": _count(records, "page"),
        "marker_candidates": _count(records, "marker_candidate"),
        "source_spans": _count(records, "source_span"),
        "commenters": _count(records, "commenter"),
        "submissions": _count(records, "submission"),
        "source_units": len(units),
        "comment_units": sum(unit["unit_kind"] == "comment" for unit in units),
        "response_units": sum(unit["unit_kind"] == "response" for unit in units),
        "general_response_units": sum(unit["unit_kind"] == "general_response" for unit in units),
        "membership_claims": _count(records, "membership_claim"),
        "reference_mentions": _count(records, "reference_mention"),
        "placement_exceptions": _count(records, "source_placement_exception"),
        "diagnostics": len(diagnostics),
        "open_range_boundary_diagnostics": sum(
            item["code"] == "unit_boundary_ambiguous" and item["terminal"] is True
            for item in diagnostics
        ),
    }


def _count(records: Sequence[JsonObject], record_type: str) -> int:
    return sum(record["record_type"] == record_type for record in records)


def _inventory_record(activity: Mapping[str, Any], payloads: Mapping[str, bytes]) -> JsonObject:
    files = [
        {
            "authority": "bundle",
            "path": relative_path,
            "sha256": None,
            "byte_size": len(payload),
        }
        for relative_path, payload in sorted(payloads.items())
    ]
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "managed_file_inventory",
        "stage": "05c",
        "activity_id": activity["activity_id"],
        "dependencies": activity["input_refs"],
        "files": files,
    }
    record["inventory_id"] = build_record_id(record)
    return record


def _completion_record(
    activity: Mapping[str, Any],
    inventory: Mapping[str, Any],
    counts: JsonObject,
    completed_at: str,
) -> JsonObject:
    warning_count = counts["diagnostics"]
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "stage_completion",
        "stage": "05c",
        "status": "complete_with_warnings" if warning_count else "complete",
        "activity_id": activity["activity_id"],
        "inventory_id": inventory["inventory_id"],
        "counts": counts,
        "warnings": (
            ["See diagnostic records for explicitly bounded pilot warnings."]
            if warning_count
            else []
        ),
        "completed_at": completed_at,
    }
    record["completion_id"] = build_record_id(record)
    return record


__all__ = ["build_pilot"]
