"""Completion-last Task 05D workflow over the exact full-source range."""

from __future__ import annotations

import json
import logging
import resource
import shutil
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
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
    task05d_completion_counts,
    task05d_warning_entries,
    validate_managed_files,
    validate_record_bundle,
)
from er_commons.response_inventory.full_policy import (
    accepted_signature_digests_from_pilot,
    build_structural_accounting,
    select_full_review_population,
)
from er_commons.response_inventory.observations import PageObservation
from er_commons.response_inventory.pdf_access import read_pdfium_range
from er_commons.response_inventory.producer import build_source_records
from er_commons.response_inventory.qualification import (
    apply_full_visual_dispositions,
    poppler_versions,
    qualify_all_pages,
    validate_qualification_report,
)
from er_commons.response_inventory.range_receipts import (
    aggregation_is_ready,
    contiguous_range_key,
)
from er_commons.response_inventory.run_spec import (
    ResponseInventoryRunSpecV2,
    load_response_inventory_run_spec,
    verify_repository_bindings,
)
from er_commons.response_inventory.task05d_policy import (
    TASK05D_PAGE_COUNT,
    TASK05D_RANGE,
)
from er_commons.response_inventory.workflow import (
    _collect_range_evidence,
    _load_observations,
    _load_optional_object,
    _range_cache_is_reusable,
    _receipt_digests,
)

type JsonObject = dict[str, Any]
type PageReader = Callable[[Path, int, int], list[PageObservation]]
type PageQualifier = Callable[[Path, Sequence[PageObservation], Path], JsonObject]

LOGGER = logging.getLogger(__name__)
_GIB = 1024**3
_MIB = 1024**2


@dataclass(frozen=True)
class _RunContext:
    """Identity, paths, and validated bindings for one Task 05D invocation."""

    spec: ResponseInventoryRunSpecV2
    config_sha256: str
    schema: JsonObject
    activity: JsonObject
    source_path: Path
    task_root: Path
    candidate_root: Path
    cache_root: Path


@dataclass(frozen=True)
class _ReviewState:
    """Frozen review evidence and the state transition it permits."""

    qualification: JsonObject
    structural: JsonObject
    unresolved: tuple[int, ...]
    base_preexisted: bool


def build_complete_inventory(
    run_spec_path: Path,
    repository_root: Path,
    artifact_root: Path,
    *,
    page_reader: PageReader = read_pdfium_range,
    page_qualifier: PageQualifier = qualify_all_pages,
    visual_dispositions: Mapping[int, Mapping[str, str]] | None = None,
    tool_versions: Mapping[str, str] | None = None,
    completed_at: str | None = None,
) -> JsonObject:
    """Build or verify one exact 05D working revision without hidden source reads."""
    started = time.monotonic()
    context = _prepare_run_context(
        run_spec_path,
        repository_root,
        artifact_root,
        tool_versions,
    )
    completed = _reuse_completed_full(
        context.candidate_root,
        context.cache_root,
        context.schema,
        context.activity,
        context.spec,
    )
    if completed is not None:
        return completed
    qualification_base_path = context.cache_root / "qualification/qualification_base.json"
    if visual_dispositions is not None and not qualification_base_path.is_file():
        raise ValueError(
            "05D review dispositions require a preexisting frozen qualification base; "
            "run once without dispositions"
        )

    observations, records, source_digest, reused_ranges = _prepare_source_records(
        context,
        page_reader,
    )
    review = _prepare_review_state(
        context,
        artifact_root,
        observations,
        records,
        page_qualifier,
        visual_dispositions,
    )
    source_runtime = _record_or_load_source_runtime(
        context,
        started,
        base_preexisted=review.base_preexisted,
    )
    _write_review_packet(context, review, records, source_digest)
    if review.unresolved or not review.base_preexisted:
        return {
            "status": "review_required",
            "candidate_root": str(context.candidate_root),
            "activity_id": context.activity["activity_id"],
            "review_packet": str(context.cache_root / "review/qualification.json"),
            "unresolved_review_pages": list(review.unresolved),
            "reused_ranges": reused_ranges,
        }

    return _publish_reviewed_candidate(
        context,
        observations,
        records,
        source_digest,
        reused_ranges,
        review,
        source_runtime,
        started,
        completed_at,
    )


def _prepare_run_context(
    run_spec_path: Path,
    repository_root: Path,
    artifact_root: Path,
    tool_versions: Mapping[str, str] | None,
) -> _RunContext:
    """Validate preflight and derive one readable set of identity-bound paths."""
    spec_value, config_sha256 = load_response_inventory_run_spec(run_spec_path)
    if not isinstance(spec_value, ResponseInventoryRunSpecV2):
        raise ValueError("complete inventory requires a Task 05D v2 run specification")
    verify_repository_bindings(spec_value, repository_root)
    _verify_full_artifact_bindings(spec_value, artifact_root)
    _require_free_space(artifact_root, _GIB, "05D preflight")
    schema_path = _repository_binding_path(spec_value, repository_root, "response_record_schema")
    schema = cast(JsonObject, json.loads(schema_path.read_text(encoding="utf-8")))
    observed_versions = {
        "pypdfium2": version("pypdfium2"),
        **(dict(tool_versions) if tool_versions is not None else poppler_versions()),
    }
    activity = _activity_record(spec_value, config_sha256, observed_versions, repository_root)
    activity_hash = str(activity["activity_id"]).removeprefix("activityv1-")
    task_root = artifact_root / spec_value.output_policy.artifact_relative_root
    return _RunContext(
        spec=spec_value,
        config_sha256=config_sha256,
        schema=schema,
        activity=activity,
        source_path=artifact_root / spec_value.source.path,
        task_root=task_root,
        candidate_root=task_root
        / spec_value.output_policy.working_namespace_template.format(activity_hash=activity_hash),
        cache_root=task_root
        / Path(
            str(spec_value.cache_policy.relative_path_template).format(activity_hash=activity_hash)
        ),
    )


def _prepare_source_records(
    context: _RunContext,
    page_reader: PageReader,
) -> tuple[list[PageObservation], list[JsonObject], str, int]:
    """Load the exact range and prove deterministic source-record construction."""
    observations, receipts, reused_ranges = _collect_range_evidence(
        context.spec,
        context.activity,
        context.schema,
        context.source_path,
        context.cache_root,
        _receipt_digests(context.activity, context.config_sha256),
        page_reader,
    )
    if not aggregation_is_ready(receipts, (TASK05D_RANGE,)):
        raise ValueError("05D range receipt does not close the exact 1-744 selection")
    records = build_source_records(context.activity, observations)
    source_digest = validate_record_bundle(records, context.schema)
    _validate_shuffled_determinism(context.activity, observations, context.schema, source_digest)
    return observations, records, source_digest, reused_ranges


def _prepare_review_state(
    context: _RunContext,
    artifact_root: Path,
    observations: Sequence[PageObservation],
    records: Sequence[JsonObject],
    page_qualifier: PageQualifier,
    visual_dispositions: Mapping[int, Mapping[str, str]] | None,
) -> _ReviewState:
    """Freeze deterministic review evidence and apply only later-pass decisions."""
    qualification_root = context.cache_root / "qualification"
    base_path = qualification_root / "qualification_base.json"
    base = _load_optional_object(base_path)
    base_preexisted = base is not None
    if base is None:
        if visual_dispositions is not None:
            raise ValueError("05D cannot apply review dispositions before freezing review evidence")
        base = page_qualifier(context.source_path, observations, qualification_root)
        validate_qualification_report(base, observations, qualification_root)
        write_json_atomic(base_path, base)
    else:
        validate_qualification_report(base, observations, qualification_root)
    qualification = select_full_review_population(
        cast(JsonObject, json.loads(json.dumps(base))),
        records,
        observations,
        accepted_signature_digests=_accepted_signature_baseline(context.spec, artifact_root),
    )
    qualification, unresolved = apply_full_visual_dispositions(
        qualification,
        visual_dispositions if base_preexisted else None,
    )
    return _ReviewState(
        qualification=qualification,
        structural=build_structural_accounting(records),
        unresolved=unresolved,
        base_preexisted=base_preexisted,
    )


def _write_review_packet(
    context: _RunContext,
    review: _ReviewState,
    records: Sequence[JsonObject],
    source_digest: str,
) -> None:
    """Publish the replaceable evidence a reviewer needs, with explicit paths."""
    review_root = context.cache_root / "review"
    write_json_atomic(review_root / "qualification.json", review.qualification)
    write_json_atomic(
        review_root / "source_records.json",
        {"records": records, "semantic_digest": source_digest},
    )
    write_json_atomic(review_root / "structural_accounting.json", review.structural)


def _publish_reviewed_candidate(
    context: _RunContext,
    observations: Sequence[PageObservation],
    records: Sequence[JsonObject],
    source_digest: str,
    reused_ranges: int,
    review: _ReviewState,
    source_runtime: JsonObject,
    started: float,
    completed_at: str | None,
) -> JsonObject:
    """Validate the review/reuse gate, then publish one completion-last candidate."""
    validate_qualification_report(
        review.qualification,
        observations,
        context.cache_root / "qualification",
    )
    _require_free_space(context.task_root, 512 * _MIB, "05D publication")
    counts = task05d_completion_counts(context.activity, records)
    if counts["open_range_boundary_diagnostics"] != 0:
        raise ValueError("05D cannot publish an open range-boundary diagnostic")
    warnings = task05d_warning_entries(
        records,
        str(context.activity["activity_id"]),
        allowed_codes=context.spec.stop_behavior.allowed_terminal_warning_codes,
    )
    repeatability = {
        "schema_version": "er_commons.response_inventory.repeatability.v1",
        "activity_id": context.activity["activity_id"],
        "range_receipts_reused": reused_ranges,
        "range_receipts_expected": 1,
        "source_reader_calls_required": 0,
        "qualification_source_calls_required": 0,
        "semantic_digest": source_digest,
        "status": "passed" if reused_ranges == 1 and review.base_preexisted else "failed",
    }
    if repeatability["status"] != "passed":
        raise ValueError("05D terminal publication requires receipt-reuse reconstruction")
    runtime = _terminal_runtime(context, source_runtime, started)
    summary = {
        "schema_version": "er_commons.response_inventory.build_summary.v1",
        "activity_id": context.activity["activity_id"],
        "semantic_digest": source_digest,
        "counts": counts,
        "allowed_terminal_warning_codes": list(
            context.spec.stop_behavior.allowed_terminal_warning_codes
        ),
        "diagnostic_counts": dict(
            sorted(
                Counter(
                    str(record["code"])
                    for record in records
                    if record.get("record_type") == "diagnostic"
                ).items()
            )
        ),
        "structural_accounting_digest": review.structural["report_digest"],
        "review_population_digest": review.qualification["review_population_digest"],
    }
    payloads, inventory, completion = _close_candidate_payloads(
        context.activity,
        records,
        review.qualification,
        review.structural,
        repeatability,
        runtime,
        summary,
        counts,
        warnings,
        completed_at or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    )
    validate_record_bundle([*records, inventory, completion], context.schema)
    _publish_candidate_atomically(context.candidate_root, payloads, inventory, completion)
    return {
        "candidate_root": str(context.candidate_root),
        "activity_id": context.activity["activity_id"],
        "completion_id": completion["completion_id"],
        "semantic_digest": source_digest,
        "reused_ranges": reused_ranges,
    }


def _record_or_load_source_runtime(
    context: _RunContext,
    started: float,
    *,
    base_preexisted: bool,
) -> JsonObject:
    """Persist expensive first-pass resource evidence for terminal reporting."""
    path = context.cache_root / "review/source_pass_runtime.json"
    existing = _load_optional_object(path)
    if existing is not None:
        if existing.get("activity_id") != context.activity["activity_id"]:
            raise ValueError("05D source-pass runtime evidence names another activity")
        return existing
    if base_preexisted:
        raise ValueError("05D frozen review evidence lacks source-pass runtime evidence")
    report: JsonObject = {
        "schema_version": "er_commons.response_inventory.source_pass_runtime.v1",
        "activity_id": context.activity["activity_id"],
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "maximum_resident_memory_bytes": _peak_rss_bytes(),
        "cache_size_bytes": _tree_size(context.cache_root),
    }
    write_json_atomic(path, report)
    return report


def _terminal_runtime(
    context: _RunContext,
    source_runtime: Mapping[str, Any],
    closure_started: float,
) -> JsonObject:
    """Combine first-pass and source-free closure resource measurements."""
    source_elapsed = float(source_runtime["elapsed_seconds"])
    closure_elapsed = round(time.monotonic() - closure_started, 6)
    source_rss = int(source_runtime["maximum_resident_memory_bytes"])
    closure_rss = _peak_rss_bytes()
    return {
        "schema_version": "er_commons.response_inventory.runtime_resources.v2",
        "activity_id": context.activity["activity_id"],
        "elapsed_seconds": round(source_elapsed + closure_elapsed, 6),
        "source_pass_elapsed_seconds": source_elapsed,
        "closure_elapsed_seconds": closure_elapsed,
        "maximum_resident_memory_bytes": max(source_rss, closure_rss),
        "source_pass_maximum_resident_memory_bytes": source_rss,
        "closure_maximum_resident_memory_bytes": closure_rss,
        "cache_size_bytes": _tree_size(context.cache_root),
    }


def _verify_full_artifact_bindings(spec: ResponseInventoryRunSpecV2, artifact_root: Path) -> None:
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
    _verify_task05c_evidence(spec, root)


def _verify_task05c_evidence(spec: ResponseInventoryRunSpecV2, root: Path) -> None:
    completion = read_json_object(root / _input(spec, "task05c_completion").path)
    inventory = read_json_object(root / _input(spec, "task05c_managed_inventory").path)
    summary = read_json_object(root / _input(spec, "task05c_build_summary").path)
    records = [
        cast(JsonObject, row)
        for row in read_jsonl(root / _input(spec, "task05c_source_records").path)
    ]
    accepted = spec.accepted_task05c
    if completion.get("completion_id") != accepted.completion_id:
        raise ValueError("accepted Task 05C completion identity differs")
    if completion.get("inventory_id") != accepted.inventory_id:
        raise ValueError("accepted Task 05C completion names another inventory")
    if inventory.get("inventory_id") != accepted.inventory_id:
        raise ValueError("accepted Task 05C inventory identity differs")
    if summary.get("activity_id") != accepted.activity_id:
        raise ValueError("accepted Task 05C summary names another activity")
    if summary.get("semantic_digest") != accepted.semantic_digest:
        raise ValueError("accepted Task 05C summary semantic digest differs")
    if semantic_bundle_digest(records) != accepted.semantic_digest:
        raise ValueError("accepted Task 05C records semantic digest differs")


def _verify_source_manifest(spec: ResponseInventoryRunSpecV2, root: Path) -> None:
    reference = _input(spec, "source_manifest")
    manifest = read_json_object(root / reference.path)
    rows = manifest.get("sources")
    if not isinstance(rows, list):
        raise ValueError("source manifest lacks a sources list")
    matches = [
        row for row in rows if isinstance(row, dict) and row.get("source_id") == "feir_volume_4"
    ]
    if len(matches) != 1:
        raise ValueError("source manifest does not contain exactly one response source")
    row = matches[0]
    expected = {
        "source_role": spec.source.source_role,
        "local_path": spec.source.path.as_posix(),
        "sha256": spec.source.recorded_sha256,
        "byte_size": spec.source.recorded_byte_size,
        "pdf_page_count": TASK05D_PAGE_COUNT,
        "retrieval_status": spec.source.retrieval_status,
        "validation_status": spec.source.validation_status,
    }
    if any(row.get(key) != value for key, value in expected.items()):
        raise ValueError("response source metadata differs from its manifest row")


def _verify_source_release_completion(spec: ResponseInventoryRunSpecV2, root: Path) -> None:
    completion = read_json_object(root / _input(spec, "source_release_completion").path)
    manifest_ref = _input(spec, "source_manifest")
    manifest = completion.get("manifest")
    if completion.get("schema_version") != "er_commons.source_release_completion.v1":
        raise ValueError("source release completion has an unexpected schema")
    if completion.get("source_release_version") != spec.source.source_release_version:
        raise ValueError("source release completion names another release")
    if not isinstance(manifest, dict) or manifest != {
        "local_path": manifest_ref.path.as_posix(),
        "byte_size": manifest_ref.byte_size,
        "sha256": manifest_ref.sha256,
    }:
        raise ValueError("source release completion does not seal the accepted manifest")


def _activity_record(
    spec: ResponseInventoryRunSpecV2,
    config_sha256: str,
    tool_versions: Mapping[str, str],
    repository_root: Path,
) -> JsonObject:
    source_manifest = _input(spec, "source_manifest")
    task05c = _input(spec, "task05c_completion")
    input_refs = sorted(
        [
            {
                "role": "source_record",
                "identity": f"{spec.source.source_id}@{spec.source.recorded_sha256}",
                "authority": "artifact_root",
                "path": source_manifest.path.as_posix(),
            },
            {
                "role": "task05c_completion",
                "identity": spec.accepted_task05c.completion_id,
                "authority": "artifact_root",
                "path": task05c.path.as_posix(),
            },
        ],
        key=lambda row: (row["role"], row["identity"], row["path"]),
    )
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "activity",
        "stage": "05d",
        "source_id": spec.source.source_id,
        "page_ranges": [list(TASK05D_RANGE)],
        "config_sha256": config_sha256,
        "schema_sha256": next(
            binding.sha256
            for binding in spec.repository_bindings
            if binding.role == "response_record_schema"
        ),
        "code_sha256": owned_code_digest(repository_root),
        "tool_versions": dict(sorted(tool_versions.items())),
        "input_refs": input_refs,
    }
    record["activity_id"] = build_record_id(record)
    return record


def _accepted_signature_baseline(
    spec: ResponseInventoryRunSpecV2, artifact_root: Path
) -> frozenset[str]:
    profile = read_json_object(artifact_root / _input(spec, "task05a_structural_profile").path)
    _validate_task05a_profile(profile)
    records = [
        cast(JsonObject, row)
        for row in read_jsonl(artifact_root / _input(spec, "task05c_source_records").path)
    ]
    qualification = read_json_object(artifact_root / _input(spec, "task05c_qualification").path)
    return accepted_signature_digests_from_pilot(records, qualification)


def _validate_shuffled_determinism(
    activity: JsonObject,
    observations: Sequence[PageObservation],
    schema: JsonObject,
    source_digest: str,
) -> None:
    """Require semantic identity when page observations arrive in reverse order."""
    shuffled = build_source_records(activity, tuple(reversed(observations)))
    if validate_record_bundle(shuffled, schema) != source_digest:
        raise ValueError("05D source records are not deterministic under shuffled input")


def _validate_task05a_profile(profile: Mapping[str, Any]) -> None:
    """Verify the accepted profile that supplies the structural-regime vocabulary."""
    expected = {
        "schema_version": "er_commons.task05a.structural_regime_profile.v1",
        "task_id": "05A",
        "source_id": "feir_volume_4",
        "selected_page_count": 195,
        "selected_pages_accounted_for": True,
        "status": "complete",
    }
    if any(profile.get(key) != value for key, value in expected.items()):
        raise ValueError("accepted Task 05A structural-regime profile differs")
    assignments = profile.get("primary_page_assignments")
    cross_cutting = profile.get("cross_cutting_regimes")
    if not isinstance(assignments, list) or not assignments:
        raise ValueError("accepted Task 05A profile lacks primary regime assignments")
    if not isinstance(cross_cutting, list) or not all(
        isinstance(value, str) and value for value in cross_cutting
    ):
        raise ValueError("accepted Task 05A profile lacks cross-cutting regimes")


def _inventory_record(activity: Mapping[str, Any], payloads: Mapping[str, bytes]) -> JsonObject:
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "managed_file_inventory",
        "stage": "05d",
        "activity_id": activity["activity_id"],
        "dependencies": activity["input_refs"],
        "files": [
            {"authority": "bundle", "path": path, "sha256": None, "byte_size": len(payload)}
            for path, payload in sorted(payloads.items())
        ],
    }
    record["inventory_id"] = build_record_id(record)
    return record


def _close_candidate_payloads(
    activity: Mapping[str, Any],
    records: Sequence[JsonObject],
    qualification: JsonObject,
    structural: JsonObject,
    repeatability: JsonObject,
    runtime: JsonObject,
    summary: JsonObject,
    counts: JsonObject,
    warnings: Sequence[str],
    completed_at: str,
) -> tuple[dict[str, bytes], JsonObject, JsonObject]:
    """Close the exact candidate byte size without mutating files after publication."""
    runtime["candidate_size_bytes"] = 0
    for _attempt in range(10):
        payloads = {
            "inventory/source_records.jsonl": jsonl_bytes(records),
            "diagnostics/qualification.json": json_bytes(qualification),
            "diagnostics/structural_accounting.json": json_bytes(structural),
            "diagnostics/build_summary.json": json_bytes(summary),
            "diagnostics/repeatability.json": json_bytes(repeatability),
            "diagnostics/runtime_resources.json": json_bytes(runtime),
        }
        inventory = _inventory_record(activity, payloads)
        completion = _completion_record(activity, inventory, counts, warnings, completed_at)
        candidate_size = sum(len(payload) for payload in payloads.values())
        candidate_size += len(json_bytes(inventory)) + len(json_bytes(completion))
        if runtime["candidate_size_bytes"] == candidate_size:
            return payloads, inventory, completion
        runtime["candidate_size_bytes"] = candidate_size
    raise ValueError("05D candidate byte-size accounting did not converge")


def _publish_candidate_atomically(
    candidate_root: Path,
    payloads: Mapping[str, bytes],
    inventory: JsonObject,
    completion: JsonObject,
) -> None:
    """Stage a complete candidate beside its target, then expose it in one rename."""
    candidate_root.parent.mkdir(parents=True, exist_ok=True)
    if candidate_root.exists():
        raise ValueError("05D candidate path exists without a reusable completion")
    staging_root = Path(
        tempfile.mkdtemp(prefix=f".{candidate_root.name}.staging-", dir=candidate_root.parent)
    )
    published = False
    try:
        LOGGER.info("staging Task 05D candidate at %s", staging_root)
        for relative_path, payload in payloads.items():
            publish_bytes_no_clobber(staging_root / relative_path, payload)
        publish_bytes_no_clobber(
            staging_root / "records/managed_file_inventory.json", json_bytes(inventory)
        )
        validate_managed_files(
            inventory,
            staging_root,
            excluded_paths={
                "records/managed_file_inventory.json",
                "records/stage_completion.json",
            },
        )
        publish_bytes_no_clobber(
            staging_root / "records/stage_completion.json", json_bytes(completion)
        )
        runtime_report = json.loads(payloads["diagnostics/runtime_resources.json"])
        if _tree_size(staging_root) != runtime_report["candidate_size_bytes"]:
            raise ValueError("05D staged candidate byte size differs from its runtime report")
        staging_root.rename(candidate_root)
        published = True
    finally:
        if not published and staging_root.exists():
            LOGGER.warning("removing incomplete Task 05D staging directory: %s", staging_root)
            shutil.rmtree(staging_root)


def _completion_record(
    activity: Mapping[str, Any],
    inventory: Mapping[str, Any],
    counts: JsonObject,
    warnings: Sequence[str],
    completed_at: str,
) -> JsonObject:
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "stage_completion",
        "stage": "05d",
        "status": "complete_with_warnings" if warnings else "complete",
        "activity_id": activity["activity_id"],
        "inventory_id": inventory["inventory_id"],
        "counts": counts,
        "warnings": list(warnings),
        "completed_at": completed_at,
    }
    record["completion_id"] = build_record_id(record)
    return record


def _reuse_completed_full(
    candidate_root: Path,
    cache_root: Path,
    schema: JsonObject,
    activity: JsonObject,
    spec: ResponseInventoryRunSpecV2,
) -> JsonObject | None:
    completion_path = candidate_root / "records/stage_completion.json"
    if not completion_path.is_file():
        return None
    inventory_path = candidate_root / "records/managed_file_inventory.json"
    records_path = candidate_root / "inventory/source_records.jsonl"
    if not inventory_path.is_file() or not records_path.is_file():
        raise ValueError("completed 05D candidate is missing managed records")
    records = [cast(JsonObject, row) for row in read_jsonl(records_path)]
    completion = read_json_object(completion_path)
    inventory = read_json_object(inventory_path)
    activities = [row for row in records if row.get("record_type") == "activity"]
    if activities != [activity]:
        raise ValueError("completed 05D activity differs from the requested run")
    validate_record_bundle([*records, inventory, completion], schema)
    validate_managed_files(
        inventory,
        candidate_root,
        excluded_paths={
            "records/managed_file_inventory.json",
            "records/stage_completion.json",
        },
    )
    range_key = contiguous_range_key(TASK05D_RANGE)
    receipt = _load_optional_object(cache_root / f"ranges/{range_key}/receipt.json")
    observations_path = cache_root / f"ranges/{range_key}/observations.json"
    observations = _load_observations(observations_path)
    if receipt is None or observations is None or receipt.get("status") != "complete":
        raise ValueError("completed 05D candidate lacks its reusable full-range receipt")
    receipt_digests = _receipt_digests(activity, activity["config_sha256"])
    if not _range_cache_is_reusable(
        observations,
        receipt,
        TASK05D_RANGE,
        activity,
        schema,
        observations_path,
        receipt_digests,
    ):
        raise ValueError("completed 05D candidate range receipt is stale or mismatched")
    if receipt.get("page_range") != list(TASK05D_RANGE) or len(observations) != TASK05D_PAGE_COUNT:
        raise ValueError("completed 05D receipt does not close pages 1-744")
    return {
        "candidate_root": str(candidate_root),
        "activity_id": activity["activity_id"],
        "completion_id": completion["completion_id"],
        "semantic_digest": semantic_bundle_digest(records),
        "reused_ranges": 1,
        "reuse_verified": True,
    }


def _input(spec: ResponseInventoryRunSpecV2, role: str) -> Any:
    return next(reference for reference in spec.accepted_inputs if reference.role == role)


def _repository_binding_path(spec: ResponseInventoryRunSpecV2, root: Path, role: str) -> Path:
    return root / next(binding.path for binding in spec.repository_bindings if binding.role == role)


def _require_free_space(path: Path, minimum: int, label: str) -> None:
    probe = path
    while not probe.exists():
        probe = probe.parent
    if shutil.disk_usage(probe).free < minimum:
        raise ValueError(f"{label} requires at least {minimum} free bytes")


def _tree_size(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


__all__ = ["build_complete_inventory"]
