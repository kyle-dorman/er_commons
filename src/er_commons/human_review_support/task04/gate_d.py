"""Publish the compact Task 04A Gate D release decision."""

from __future__ import annotations

import shutil
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import json_bytes, sha256_bytes, sha256_file
from er_commons.human_review_support.task04.json_io import (
    read_json_object,
    require_list,
    require_mapping,
    require_string,
)
from er_commons.human_review_support.task04.models import JsonObject, JsonValue
from er_commons.human_review_support.task04.records import RecordValidator
from er_commons.human_review_support.task04.toc_decisions import load_toc_decisions
from er_commons.human_review_support.task04.toc_models import (
    TocDisposition,
    TocSourceCensus,
    parse_toc_censuses,
)

REVIEW_RUN_ID = "reviewv1-task03j-final-c17"
EXPECTED_SOURCE_COUNT = 35
EXPECTED_DECISION_COUNT = 757
EXPECTED_VISIBLE_TOC_CARD_COUNT = 341
EXPECTED_AMBIGUOUS_LINK_COUNT = 725
MAX_HASHED_INPUT_BYTES = 1_000_000


@dataclass(frozen=True)
class GateDRequest:
    """Exact compact inputs and destination for the Gate D publication."""

    gate_a_path: Path
    gate_c_root: Path
    schema_root: Path

    @property
    def output_root(self) -> Path:
        """Return the additive closure directory beneath the accepted c17 run."""
        return self.gate_c_root / "gate_d"


@dataclass(frozen=True)
class _GateDInputs:
    """Validated compact records used to derive all Gate D outputs."""

    gate_a: JsonObject
    gate_c: JsonObject
    selection: JsonObject
    finding_recheck: JsonObject
    gate_a_path: Path
    decisions_path: Path
    decisions: dict[str, TocDisposition]


def publish_gate_d(request: GateDRequest) -> Path:
    """Build, validate, and atomically publish the compact Gate D package."""
    if request.output_root.exists():
        raise FileExistsError(f"Gate D output already exists: {request.output_root}")
    staging = request.gate_c_root / ".gate_d.staging"
    if staging.exists():
        raise FileExistsError(f"Gate D staging output already exists: {staging}")
    staging.mkdir()
    try:
        inputs = _load_inputs(request)
        records = _build_records(inputs, request.gate_c_root)
        validator = RecordValidator(request.schema_root)
        references: dict[str, dict[str, JsonValue]] = {}
        for name, record in records.items():
            validator.validate(name, record)
            references[name] = _write_record(staging, name, record)
        completion = _completion_record(inputs, references, request.gate_c_root)
        validator.validate("gate_d_completion", completion)
        _write_record(staging, "gate_d_completion", completion)
        staging.rename(request.output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return request.output_root


def _load_inputs(request: GateDRequest) -> _GateDInputs:
    """Load only review JSON records and reject stale or incomplete review state."""
    if request.gate_c_root.name != REVIEW_RUN_ID:
        raise ValueError(f"Gate D requires {REVIEW_RUN_ID}, found {request.gate_c_root.name}")
    records_root = request.gate_c_root / "records"
    gate_a = read_json_object(request.gate_a_path)
    gate_c = read_json_object(records_root / "gate_c_execution.json")
    selection = read_json_object(records_root / "selection_manifest.json")
    finding_recheck = read_json_object(records_root / "task03i_finding_recheck.json")
    decisions_path = records_root / "toc_review_decisions.json"
    _require_small_input(decisions_path)
    decisions = dict(load_toc_decisions(decisions_path))
    _validate_input_identity(gate_a, gate_c, finding_recheck)
    _validate_decision_coverage(selection, decisions)
    if len(decisions) != EXPECTED_DECISION_COUNT:
        raise ValueError(
            f"expected {EXPECTED_DECISION_COUNT} accepted TOC decisions; found {len(decisions)}"
        )
    return _GateDInputs(
        gate_a,
        gate_c,
        selection,
        finding_recheck,
        request.gate_a_path,
        decisions_path,
        decisions,
    )


def _validate_input_identity(
    gate_a: JsonObject, gate_c: JsonObject, finding_recheck: JsonObject
) -> None:
    """Require the exact accepted review pass and its pending recheck record."""
    if gate_a.get("pass") != "task03j_final" or gate_a.get("status") != "source_free_prepared":
        raise ValueError("Gate D requires the completed Task 03J Gate A preparation")
    if gate_c.get("review_run_id") != REVIEW_RUN_ID:
        raise ValueError("Gate C execution record does not belong to the accepted c17 review")
    if gate_c.get("source_count") != EXPECTED_SOURCE_COUNT:
        raise ValueError("Gate C execution record does not account for all 35 sources")
    if gate_c.get("ambiguous_reference_link_count") != EXPECTED_AMBIGUOUS_LINK_COUNT:
        raise ValueError("Gate C ambiguous-link count differs from the approved disposition")
    if finding_recheck.get("status") != "machine_evidence_bound_pending_human_confirmation":
        raise ValueError("Task 03I recheck record is not awaiting the approved human disposition")


def _validate_decision_coverage(
    selection: JsonObject, decisions: Mapping[str, TocDisposition]
) -> None:
    """Require a terminal decision for every TOC card shown in c17."""
    visible_ids: set[str] = set()
    items = require_list(selection.get("items"), path="selection_manifest.items")
    for index, value in enumerate(items):
        item = require_mapping(value, path=f"selection_manifest.items[{index}]")
        if item.get("queue") not in {"toc_review", "positive_toc"}:
            continue
        population = require_mapping(
            item.get("population"), path=f"selection_manifest.items[{index}].population"
        )
        visible_ids.add(
            require_string(
                population.get("candidate_page_id"),
                path=f"selection_manifest.items[{index}].population.candidate_page_id",
            )
        )
    if len(visible_ids) != EXPECTED_VISIBLE_TOC_CARD_COUNT:
        raise ValueError(
            f"expected {EXPECTED_VISIBLE_TOC_CARD_COUNT} visible TOC cards; "
            f"found {len(visible_ids)}"
        )
    missing = sorted(visible_ids - decisions.keys())
    if missing:
        raise ValueError(f"visible TOC cards lack accepted decisions: {missing}")


def _build_records(inputs: _GateDInputs, gate_c_root: Path) -> dict[str, dict[str, Any]]:
    """Create every Gate D record from one validated in-memory input set."""
    census = parse_toc_censuses(inputs.gate_a.get("toc_candidate_census"))
    if len(census) != EXPECTED_SOURCE_COUNT:
        raise ValueError(f"expected 35 source censuses; found {len(census)}")
    decision_mapping = {
        page.entry_id: (source.source_id, source.candidate_id, page.physical_page)
        for source in census
        for page in source.pages
    }
    unknown = sorted(inputs.decisions.keys() - decision_mapping.keys())
    if unknown:
        raise ValueError(f"accepted decisions are absent from the Gate A census: {unknown}")
    ambiguous_links = _ambiguous_link_dispositions(inputs.gate_a)
    if len(ambiguous_links["entries"]) != EXPECTED_AMBIGUOUS_LINK_COUNT:
        raise ValueError("Gate A does not contain the approved 725 ambiguous links")
    decision_counts = Counter(inputs.decisions.values())
    expected_counts = {"toc": 60, "not_toc": 697}
    actual_counts = {
        "toc": decision_counts["toc"],
        "not_toc": decision_counts["not_toc"],
    }
    if actual_counts != expected_counts:
        raise ValueError(
            f"expected accepted TOC decision counts {expected_counts}; found {actual_counts}"
        )
    decision_reference = _small_file_reference(inputs.decisions_path, gate_c_root)
    usability = _usability_registry(census)
    task03i = _task03i_disposition(inputs.finding_recheck)
    risk = _unresolved_risk_report(decision_counts)
    provisional = {
        "usability_registry": usability,
        "ambiguous_link_dispositions": ambiguous_links,
        "unresolved_risk_report": risk,
        "task03i_recheck_disposition": task03i,
    }
    references = {name: _record_reference(name, record) for name, record in provisional.items()}
    release = _release_freeze(
        inputs.gate_a,
        decision_reference,
        decision_counts,
        references,
    )
    return {**provisional, "release_freeze": release}


def _usability_registry(censuses: tuple[TocSourceCensus, ...]) -> dict[str, Any]:
    """Record the approved source-level usability decision for all 35 sources."""
    entries: list[dict[str, Any]] = []
    for census in censuses:
        _, candidate_id = census.selection_identity()
        entries.append(
            {
                "entry_id": f"usabilityv1-{census.source_id}",
                "source_id": census.source_id,
                "candidate_id": candidate_id,
                "status": "eligible",
                "condition": "eligible_with_task04a_human_toc_overlay",
                "unresolved_links": "excluded_from_trusted_resolved_link_use",
            }
        )
    return {
        "schema_version": "er_commons.task04_review.v1.usability_registry",
        "review_run_id": REVIEW_RUN_ID,
        "pass": "task03j_final",
        "status": "approved",
        "source_count": len(entries),
        "entries": entries,
    }


def _ambiguous_link_dispositions(gate_a: JsonObject) -> dict[str, Any]:
    """Carry every unreviewed ambiguous machine link forward as unresolved."""
    entries: list[dict[str, Any]] = []
    raw_censuses = require_list(
        gate_a.get("toc_candidate_census"), path="gate_a.toc_candidate_census"
    )
    for index, value in enumerate(raw_censuses):
        census = require_mapping(value, path=f"gate_a.toc_candidate_census[{index}]")
        source_id = require_string(census.get("source_id"), path=f"census[{index}].source_id")
        candidate_id = require_string(
            census.get("candidate_id"), path=f"census[{index}].candidate_id"
        )
        links = require_list(
            census.get("ambiguous_reference_links"),
            path=f"census[{index}].ambiguous_reference_links",
        )
        for link_index, value in enumerate(links):
            machine = require_mapping(value, path=f"census[{index}].links[{link_index}]")
            entries.append(
                {
                    "reference_id": require_string(
                        machine.get("reference_id"),
                        path=f"census[{index}].links[{link_index}].reference_id",
                    ),
                    "source_id": source_id,
                    "candidate_id": candidate_id,
                    "disposition": "unresolved",
                    "reason": "not_human_reviewed_in_task04a",
                    "downstream_status": "excluded_from_trusted_resolved_link_use",
                    "machine_evidence": machine,
                }
            )
    entries.sort(key=lambda item: item["reference_id"])
    if len({entry["reference_id"] for entry in entries}) != len(entries):
        raise ValueError("Gate A contains duplicate ambiguous reference identities")
    return {
        "schema_version": "er_commons.task04a_review.v1.ambiguous_link_dispositions",
        "review_run_id": REVIEW_RUN_ID,
        "status": "complete_unresolved",
        "entry_count": len(entries),
        "entries": entries,
    }


def _task03i_disposition(recheck: JsonObject) -> dict[str, Any]:
    """Record the user's terminal confirmation without rewriting Gate C evidence."""
    return {
        "schema_version": "er_commons.task04a_review.v1.task03i_recheck_disposition",
        "review_run_id": REVIEW_RUN_ID,
        "status": "fixed_confirmed",
        "reviewer": "user",
        "review_date": "2026-09-03",
        "finding_id": recheck.get("finding_id"),
        "source_id": recheck.get("source_id"),
        "physical_pages": recheck.get("physical_pages"),
        "gate_c_evidence_status": recheck.get("status"),
    }


def _unresolved_risk_report(decision_counts: Counter[TocDisposition]) -> dict[str, Any]:
    """Separate accepted limitations from release-blocking material findings."""
    return {
        "schema_version": "er_commons.task04a_review.v1.unresolved_risk_report",
        "review_run_id": REVIEW_RUN_ID,
        "status": "accepted_with_limitations",
        "material_blocker_count": 0,
        "accepted_limitation_count": 3,
        "limitations": [
            {
                "code": "ambiguous_links_unreviewed",
                "count": EXPECTED_AMBIGUOUS_LINK_COUNT,
                "disposition": "unresolved_and_excluded_from_trusted_resolved_link_use",
            },
            {
                "code": "binary_toc_review_scope",
                "count": sum(decision_counts.values()),
                "disposition": "accepted_mvp_variance_from_detailed_role_form",
            },
            {
                "code": "human_overlay_not_materialized",
                "count": 1,
                "disposition": "deferred_to_task04c_before_downstream_link_use",
            },
        ],
    }


def _release_freeze(
    gate_a: JsonObject,
    decisions: dict[str, JsonValue],
    decision_counts: Counter[TocDisposition],
    records: dict[str, dict[str, JsonValue]],
) -> dict[str, Any]:
    """Pin the accepted machine candidate and compact human decision layer."""
    inputs = require_mapping(gate_a.get("inputs"), path="gate_a.inputs")
    task03j = require_mapping(inputs.get("task03j"), path="gate_a.inputs.task03j")
    return {
        "schema_version": "er_commons.task04_review.v1.release_freeze",
        "review_run_id": REVIEW_RUN_ID,
        "pass": "task03j_final",
        "status": "frozen",
        "review_register_sha256": decisions["sha256"],
        "unresolved_material_finding_count": 0,
        "machine_candidate": {
            "production_extraction_id": task03j.get("production_extraction_id"),
            "scope_id": task03j.get("scope_id"),
            "handoff_id": task03j.get("handoff_id"),
        },
        "human_toc_decisions": decisions,
        "decision_counts": {
            "total": sum(decision_counts.values()),
            "toc": decision_counts["toc"],
            "not_toc": decision_counts["not_toc"],
        },
        "gate_d_records": records,
        "ambiguous_link_count": EXPECTED_AMBIGUOUS_LINK_COUNT,
        "task03i_recheck_status": "fixed_confirmed",
        "task04b_status": "closed_no_op",
        "next_task": "task04c_materialize_human_review_navigation_overlay",
        "large_file_hashing": "not_recomputed;sealed_upstream_digests_referenced",
    }


def _completion_record(
    inputs: _GateDInputs,
    references: dict[str, dict[str, JsonValue]],
    gate_c_root: Path,
) -> dict[str, Any]:
    """Seal the additive Gate D directory after every owned record is written."""
    hashed_size = inputs.decisions_path.stat().st_size
    return {
        "schema_version": "er_commons.task04a_review.v1.gate_d_completion",
        "review_run_id": REVIEW_RUN_ID,
        "status": "complete",
        "source_count": EXPECTED_SOURCE_COUNT,
        "toc_decision_count": len(inputs.decisions),
        "ambiguous_link_disposition_count": EXPECTED_AMBIGUOUS_LINK_COUNT,
        "managed_records": references,
        "input_records": {
            "toc_review_decisions": _small_file_reference(inputs.decisions_path, gate_c_root),
            "gate_a_preparation": {
                "path": inputs.gate_a_path.relative_to(gate_c_root.parent).as_posix(),
                "verification": "identity_and_declared_digests_reused_without_file_rehash",
            },
        },
        "large_file_hashing_performed": False,
        "largest_hashed_input_bytes": hashed_size,
    }


def _record_reference(name: str, record: dict[str, Any]) -> dict[str, JsonValue]:
    """Predict the exact reference for a deterministically serialized new record."""
    content = json_bytes(record)
    return {
        "path": f"{name}.json",
        "sha256": sha256_bytes(content),
        "byte_size": len(content),
    }


def _write_record(staging: Path, name: str, record: dict[str, Any]) -> dict[str, JsonValue]:
    """Write one deterministic record and return its exact managed reference."""
    content = json_bytes(record)
    path = staging / f"{name}.json"
    path.write_bytes(content)
    return {"path": path.name, "sha256": sha256_bytes(content), "byte_size": len(content)}


def _small_file_reference(path: Path, root: Path) -> dict[str, JsonValue]:
    """Hash one explicitly bounded compact input and reject accidental large reads."""
    _require_small_input(path)
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
        "byte_size": path.stat().st_size,
    }


def _require_small_input(path: Path) -> None:
    """Protect Gate D from silently hashing a large upstream artifact."""
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size > MAX_HASHED_INPUT_BYTES:
        raise ValueError(f"Gate D refuses to hash input larger than 1 MB: {path}")


__all__ = ["GateDRequest", "publish_gate_d"]
