"""Typed, human-facing updates to Task 04 findings and the Task 03I handoff."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from er_commons.artifact_io import canonical_json_sha256, sha256_file
from er_commons.human_review_support.task04.config import REVIEW_PASS, SCHEMA_VERSION
from er_commons.human_review_support.task04.finding_anchors import (
    FindingSelectors,
    anchor_records,
    derive_evidence_anchors,
    selectors_from_anchor_records,
)
from er_commons.human_review_support.task04.finding_transaction import (
    FindingFiles,
    finding_files,
    publish_finding_update,
    recover_finding_update,
)
from er_commons.human_review_support.task04.json_io import (
    read_json_object,
    require_list,
    require_mapping,
    require_string,
)
from er_commons.human_review_support.task04.models import JsonValue
from er_commons.human_review_support.task04.records import RecordValidator
from er_commons.human_review_support.task04.register_models import (
    FindingRegisterStatus,
    RegisterStatusResult,
)
from er_commons.human_review_support.task04.register_policy import (
    register_is_approved,
    transition_register,
)


class FindingClass(StrEnum):
    """Supported interpretations of a human review observation."""

    EXTRACTION_DEFECT = "extraction_defect"
    REVIEW_TOOL_DEFECT = "review_tool_defect"
    SOURCE_AUTHORED_ISSUE = "source_authored_issue"
    USABILITY_OBSERVATION = "usability_observation"


class FindingStatus(StrEnum):
    """Supported human decisions for one finding."""

    USER_CONFIRMED = "user_confirmed"
    ACCEPTED_FOR_TASK03I = "accepted_for_task03i"
    RETAINED_TASK04 = "retained_task04"
    REJECTED_NOT_MATERIAL = "rejected_not_material"
    REJECTED_NOT_REPRODUCIBLE = "rejected_not_reproducible"


@dataclass(frozen=True)
class FindingDraft:
    """Complete human-authored observation before deterministic identification."""

    review_item_id: str
    finding_class: FindingClass
    status: FindingStatus
    expected_behavior: str
    observed_behavior: str
    downstream_consequence: str
    selectors: FindingSelectors = FindingSelectors()

    def __post_init__(self) -> None:
        required = (
            self.review_item_id,
            self.expected_behavior,
            self.observed_behavior,
            self.downstream_consequence,
        )
        if any(not value.strip() for value in required):
            raise ValueError("finding text fields are required")
        if (
            self.status is FindingStatus.ACCEPTED_FOR_TASK03I
            and self.finding_class is not FindingClass.EXTRACTION_DEFECT
        ):
            raise ValueError("only extraction_defect findings may be accepted_for_task03i")

    def normalized(self) -> FindingDraft:
        """Normalize whitespace and anchor order before hashing and serialization."""
        return FindingDraft(
            review_item_id=self.review_item_id.strip(),
            finding_class=self.finding_class,
            status=self.status,
            expected_behavior=self.expected_behavior.strip(),
            observed_behavior=self.observed_behavior.strip(),
            downstream_consequence=self.downstream_consequence.strip(),
            selectors=self.selectors.normalized(),
        )


@dataclass(frozen=True)
class FindingResult:
    """Paths and deterministic identity produced by one successful update."""

    finding_id: str
    finding_register: Path
    task03i_handoff: Path


def record_finding(
    review_root: Path,
    draft: FindingDraft,
    *,
    schema_root: Path,
) -> FindingResult:
    """Validate, upsert, project, reseal, and recoverably publish one finding."""
    normalized = draft.normalized()
    files = finding_files(review_root)
    recover_finding_update(review_root)
    validator = RecordValidator(schema_root)
    records = _load_validated_records(files, validator)
    review_run_id = _require_consistent_run(records, files)
    _verify_existing_checksums(records, files)
    _validate_registered_findings(records, review_run_id)
    _verify_handoff_projection(records, review_run_id)
    _require_register_open(records["register"])
    item, item_path = _selected_item(
        normalized.review_item_id, records["selection"], files.selection
    )
    source, source_path = _inventory_source(item, records["inventory"], files.inventory)
    anchors = anchor_records(
        derive_evidence_anchors(
            item,
            source,
            item_path=item_path,
            source_path=source_path,
            selectors=normalized.selectors,
        )
    )

    finding = _finding_record(review_run_id, normalized, anchors)
    register = _updated_register(records["register"], finding)
    validator.validate("finding_register", register)
    handoff = _project_handoff(review_run_id, register)
    validator.validate("task03i_handoff", handoff)
    publish_finding_update(files, register, handoff, validator)
    return FindingResult(
        require_string(finding["finding_id"], path="$.finding_id"),
        files.register,
        files.handoff,
    )


def set_finding_register_status(
    review_root: Path,
    status: FindingRegisterStatus,
    *,
    schema_root: Path,
) -> RegisterStatusResult:
    """Approve or close the register through the same recoverable publication path."""
    files = finding_files(review_root)
    recover_finding_update(review_root)
    validator = RecordValidator(schema_root)
    records = _load_validated_records(files, validator)
    review_run_id = _require_consistent_run(records, files)
    _verify_existing_checksums(records, files)
    _validate_registered_findings(records, review_run_id)
    _verify_handoff_projection(records, review_run_id)
    register = transition_register(records["register"], status)
    validator.validate("finding_register", register)
    handoff = _project_handoff(review_run_id, register)
    validator.validate("task03i_handoff", handoff)
    publish_finding_update(files, register, handoff, validator)
    return RegisterStatusResult(status, files.register, files.handoff)


def _load_validated_records(
    files: FindingFiles, validator: RecordValidator
) -> dict[str, dict[str, JsonValue]]:
    records = {
        "selection": read_json_object(files.selection),
        "inventory": read_json_object(files.inventory),
        "register": read_json_object(files.register),
        "handoff": read_json_object(files.handoff),
        "manifest": read_json_object(files.manifest),
    }
    validator.validate("selection_manifest", records["selection"])
    validator.validate("input_inventory", records["inventory"])
    validator.validate("finding_register", records["register"])
    validator.validate("task03i_handoff", records["handoff"])
    validator.validate("review_bundle_manifest", records["manifest"])
    return records


def _require_consistent_run(records: dict[str, dict[str, JsonValue]], files: FindingFiles) -> str:
    values = {
        name: require_string(record.get("review_run_id"), path=f"{name}.review_run_id")
        for name, record in records.items()
    }
    if len(set(values.values())) != 1:
        locations = ", ".join(f"{name}={value}" for name, value in values.items())
        raise ValueError(f"Task 04 records belong to different review runs: {locations}")
    if files.register.parents[1].name != values["register"]:
        raise ValueError(
            "review directory identity does not match its records: "
            f"directory={files.register.parents[1].name}, record={values['register']}"
        )
    return values["register"]


def _verify_existing_checksums(
    records: dict[str, dict[str, JsonValue]], files: FindingFiles
) -> None:
    expected = {
        "handoff.finding_register_sha256": (
            records["handoff"].get("finding_register_sha256"),
            files.register,
        ),
        "handoff.selection_manifest_sha256": (
            records["handoff"].get("selection_manifest_sha256"),
            files.selection,
        ),
        "handoff.input_inventory_sha256": (
            records["handoff"].get("input_inventory_sha256"),
            files.inventory,
        ),
        "handoff.review_bundle_manifest_sha256": (
            records["handoff"].get("review_bundle_manifest_sha256"),
            files.manifest,
        ),
        "manifest.selection_manifest_sha256": (
            records["manifest"].get("selection_manifest_sha256"),
            files.selection,
        ),
    }
    for label, (recorded, path) in expected.items():
        actual = sha256_file(path)
        if recorded != actual:
            raise ValueError(
                f"stale Task 04 checksum at {label}: recorded={recorded}, actual={actual}"
            )


def _selected_item(
    review_item_id: str, selection: dict[str, JsonValue], selection_path: Path
) -> tuple[dict[str, JsonValue], str]:
    items = require_list(selection.get("items"), path="selection.items")
    for index, value in enumerate(items):
        path = f"selection.items[{index}]"
        item = require_mapping(value, path=path)
        if item.get("review_item_id") == review_item_id:
            return item, path
    raise ValueError(
        f"unknown or stale review_item_id {review_item_id!r}; not present in {selection_path}"
    )


def _inventory_source(
    item: dict[str, JsonValue], inventory: dict[str, JsonValue], inventory_path: Path
) -> tuple[dict[str, JsonValue], str]:
    source_id = require_string(item.get("source_id"), path="selection.item.source_id")
    sources = require_list(inventory.get("sources"), path="input_inventory.sources")
    for index, value in enumerate(sources):
        path = f"input_inventory.sources[{index}]"
        source = require_mapping(value, path=path)
        if source.get("source_id") == source_id:
            return source, path
    raise ValueError(f"stale selection source {source_id!r}; not present in {inventory_path}")


def _validate_registered_findings(
    records: dict[str, dict[str, JsonValue]], review_run_id: str
) -> None:
    findings = require_list(records["register"].get("findings"), path="finding_register.findings")
    finding_ids: set[str] = set()
    for index, value in enumerate(findings):
        finding_path = f"finding_register.findings[{index}]"
        finding = require_mapping(value, path=finding_path)
        item_id = require_string(
            finding.get("review_item_id"), path=f"{finding_path}.review_item_id"
        )
        item, item_path = _selected_item(item_id, records["selection"], Path("selection_manifest"))
        source, source_path = _inventory_source(item, records["inventory"], Path("input_inventory"))
        actual = require_list(
            finding.get("evidence_anchors"), path=f"{finding_path}.evidence_anchors"
        )
        selectors = selectors_from_anchor_records(actual, path=f"{finding_path}.evidence_anchors")
        expected = anchor_records(
            derive_evidence_anchors(
                item,
                source,
                item_path=item_path,
                source_path=source_path,
                selectors=selectors,
            )
        )
        if actual != expected:
            raise ValueError(
                f"mismatched or stale evidence anchors at {finding_path}.evidence_anchors"
            )
        expected_id = _finding_id(review_run_id, finding)
        if finding.get("finding_id") != expected_id:
            raise ValueError(
                f"stale finding identity at {finding_path}.finding_id: "
                f"recorded={finding.get('finding_id')}, expected={expected_id}"
            )
        if expected_id in finding_ids:
            raise ValueError(
                f"duplicate finding identity at {finding_path}.finding_id: {expected_id}"
            )
        finding_ids.add(expected_id)
        if (
            finding.get("status") == FindingStatus.ACCEPTED_FOR_TASK03I.value
            and finding.get("class") != FindingClass.EXTRACTION_DEFECT.value
        ):
            raise ValueError(
                f"only extraction_defect findings may be accepted_for_task03i at {finding_path}"
            )


def _finding_record(
    review_run_id: str, draft: FindingDraft, anchors: list[JsonValue]
) -> dict[str, JsonValue]:
    identity_payload: dict[str, JsonValue] = {
        "review_run_id": review_run_id,
        "review_item_id": draft.review_item_id,
        "class": draft.finding_class.value,
        "expected_behavior": draft.expected_behavior,
        "observed_behavior": draft.observed_behavior,
        "downstream_consequence": draft.downstream_consequence,
        "evidence_anchors": anchors,
    }
    finding_id = f"finding-{canonical_json_sha256(identity_payload)[:24]}"
    identity_payload.pop("review_run_id")
    return {"finding_id": finding_id, **identity_payload, "status": draft.status.value}


def _finding_id(review_run_id: str, finding: dict[str, JsonValue]) -> str:
    """Recompute semantic identity while deliberately excluding workflow status."""
    fields = (
        "review_item_id",
        "class",
        "expected_behavior",
        "observed_behavior",
        "downstream_consequence",
        "evidence_anchors",
    )
    payload: dict[str, JsonValue] = {"review_run_id": review_run_id}
    payload.update({field: finding.get(field) for field in fields})
    return f"finding-{canonical_json_sha256(payload)[:24]}"


def _updated_register(
    current: dict[str, JsonValue], finding: dict[str, JsonValue]
) -> dict[str, JsonValue]:
    rows = require_list(current.get("findings"), path="finding_register.findings")
    findings = [
        require_mapping(row, path=f"finding_register.findings[{i}]") for i, row in enumerate(rows)
    ]
    finding_id = finding["finding_id"]
    matching = [row for row in findings if row.get("finding_id") == finding_id]
    if len(matching) > 1:
        raise ValueError(f"finding register contains duplicate identity {finding_id}")
    if matching:
        _require_same_observation(matching[0], finding)
        findings[findings.index(matching[0])] = finding
    else:
        findings.append(finding)
    updated = dict(current)
    updated["status"] = "open"
    sorted_findings = sorted(findings, key=lambda row: str(row.get("finding_id")))
    ordered: list[JsonValue] = []
    ordered.extend(sorted_findings)
    updated["findings"] = ordered
    return updated


def _require_register_open(register: dict[str, JsonValue]) -> None:
    status = require_string(register.get("status"), path="finding_register.status")
    if status not in {"open_empty", "open"}:
        raise ValueError(
            f"finding register is {status!r}; approved or closed registers cannot be edited"
        )


def _require_same_observation(
    existing: dict[str, JsonValue], replacement: dict[str, JsonValue]
) -> None:
    """Guard against an impossible hash collision while allowing status updates."""
    semantic_fields = (
        "finding_id",
        "class",
        "review_item_id",
        "expected_behavior",
        "observed_behavior",
        "downstream_consequence",
        "evidence_anchors",
    )
    if any(existing.get(field) != replacement.get(field) for field in semantic_fields):
        raise ValueError(f"finding identity collision for {replacement.get('finding_id')}")


def _project_handoff(
    review_run_id: str,
    register: dict[str, JsonValue],
) -> dict[str, JsonValue]:
    findings = require_list(register["findings"], path="finding_register.findings")
    accepted_rows: list[JsonValue] = []
    for index, row in enumerate(findings):
        if (
            isinstance(row, dict)
            and row.get("class") == FindingClass.EXTRACTION_DEFECT.value
            and row.get("status") == FindingStatus.ACCEPTED_FOR_TASK03I.value
        ):
            accepted_rows.append(require_mapping(row, path=f"finding_register.findings[{index}]"))
    return {
        "schema_version": f"{SCHEMA_VERSION}.task03i_handoff",
        "review_run_id": review_run_id,
        "pass": REVIEW_PASS,
        "status": (
            "approved"
            if accepted_rows or register_is_approved(register)
            else "empty_pending_review"
        ),
        "finding_register_sha256": "0" * 64,
        "input_inventory_sha256": "0" * 64,
        "selection_manifest_sha256": "0" * 64,
        "review_bundle_manifest_sha256": "0" * 64,
        "extraction_findings": accepted_rows,
    }


def _verify_handoff_projection(
    records: dict[str, dict[str, JsonValue]], review_run_id: str
) -> None:
    """Require the current handoff to equal the accepted extraction-defect subset."""
    expected = _project_handoff(review_run_id, records["register"])
    handoff = records["handoff"]
    for field in ("status", "extraction_findings"):
        if handoff.get(field) != expected[field]:
            raise ValueError(
                f"Task 03I handoff is not an exact finding-register projection at $.{field}"
            )


__all__ = [
    "FindingClass",
    "FindingDraft",
    "FindingResult",
    "FindingRegisterStatus",
    "FindingStatus",
    "RegisterStatusResult",
    "recover_finding_update",
    "record_finding",
    "set_finding_register_status",
]
