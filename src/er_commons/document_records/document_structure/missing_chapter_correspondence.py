"""Closed shape and cross-record checks for Task 06E correspondence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from jsonschema.exceptions import ValidationError  # type: ignore[import-untyped]

from er_commons.document_records.document_structure.constants import (
    MISSING_CHAPTER_CORRESPONDENCE_SCHEMA_RELATIVE_PATH,
)
from er_commons.document_records.document_structure.errors import StructureContractError

JsonObject = dict[str, Any]
CORRESPONDENCE_SCHEMA_RELATIVE_PATH = MISSING_CHAPTER_CORRESPONDENCE_SCHEMA_RELATIVE_PATH
DEFAULT_CORRESPONDENCE_SCHEMA_PATH = (
    Path(__file__).resolve().parents[4] / CORRESPONDENCE_SCHEMA_RELATIVE_PATH
)


def validate_missing_chapter_correspondence(
    payload: JsonObject,
    *,
    schema_path: Path = DEFAULT_CORRESPONDENCE_SCHEMA_PATH,
    sections: list[JsonObject] | None = None,
    content: list[JsonObject] | None = None,
    content_record_count: int | None = None,
    candidate_id: str | None = None,
    expected_decision_ref: JsonObject | None = None,
) -> None:
    """Validate the closed payload and, during construction, its section inverse."""
    schema = json.loads(schema_path.read_bytes())
    try:
        Draft202012Validator(schema).validate(payload)
    except ValidationError as error:
        raise StructureContractError(
            f"missing-chapter correspondence schema violation: {error.message}"
        ) from error
    _validate_record_semantics(payload["records"], candidate_id, expected_decision_ref)
    if sections is not None:
        _validate_section_inverse(payload["records"], sections, content, content_record_count)


def _validate_record_semantics(
    records: list[JsonObject],
    candidate_id: str | None,
    expected_decision_ref: JsonObject | None,
) -> None:
    """Reject internally inconsistent or cross-candidate reusable correspondence."""
    seen_markers: set[tuple[str, str]] = set()
    seen_targets: set[str] = set()
    for record in records:
        marker = (record["source_id"], record["chapter_marker"])
        target = record["new_target"]["section_id"]
        if marker in seen_markers:
            raise _correspondence_mismatch(
                "missing-chapter correspondence repeats chapter identity",
                record,
                target,
                "source_id+chapter_marker uniqueness",
                "unique",
                marker,
            )
        if target in seen_targets:
            raise _correspondence_mismatch(
                "missing-chapter correspondence repeats chapter identity",
                record,
                target,
                "new_target.section_id uniqueness",
                "unique",
                target,
            )
        seen_markers.add(marker)
        seen_targets.add(target)
    decision_refs = {json.dumps(item["decision_ref"], sort_keys=True) for item in records}
    if len(decision_refs) != 1:
        expected_ref = records[0]["decision_ref"]
        mixed_record = next(item for item in records if item["decision_ref"] != expected_ref)
        raise _correspondence_mismatch(
            "missing-chapter correspondence mixes decision artifacts",
            mixed_record,
            mixed_record["new_target"]["section_id"],
            "decision_ref",
            expected_ref,
            mixed_record["decision_ref"],
        )
    if expected_decision_ref is not None and any(
        item["decision_ref"] != expected_decision_ref for item in records
    ):
        record = next(item for item in records if item["decision_ref"] != expected_decision_ref)
        raise _correspondence_mismatch(
            "missing-chapter correspondence uses an unexpected decision artifact",
            record,
            record["new_target"]["section_id"],
            "decision_ref",
            expected_decision_ref,
            record["decision_ref"],
        )
    prior_end = 0
    for record in records:
        start, end = record["logical_content_page_extent"]
        target = record["new_target"]["section_id"]
        inferred_candidate = target.split("/section/", maxsplit=1)[0]
        block_prefix = f"{inferred_candidate}/block/{record['source_id']}/"
        scope_prefixes = {
            "block": f"{inferred_candidate}/block/{record['source_id']}/",
            "table": f"{inferred_candidate}/table/{record['source_id']}/",
            "figure": f"{inferred_candidate}/figure/{record['source_id']}/",
        }
        ownership_ids = [item["content_record_id"] for item in record["direct_content_ownership"]]
        ownership_keys = [
            item["source_stable_item_key"]
            for item in record["direct_content_ownership"]
            if item["source_stable_item_key"] is not None
        ]
        checks: list[tuple[str, object, object]] = [
            ("logical_content_page_extent", True, start <= end),
            ("logical_content_page_extent.order", True, start > prior_end),
            ("new_target.source_id", record["source_id"], _record_source_id(target)),
        ]
        if candidate_id is not None:
            checks.append(("new_target.candidate_id", candidate_id, inferred_candidate))
        for item in record["retained_heading_block_ids"]:
            checks.append(("retained_heading_block_ids.namespace", block_prefix, item))
        for item in record["chapter_scope_content_ids"]:
            checks.append(
                (
                    "chapter_scope_content_ids.namespace",
                    tuple(scope_prefixes.values()),
                    item,
                )
            )
        owner_prefix = f"{inferred_candidate}/section/{record['source_id']}/"
        for item in record["direct_content_ownership"]:
            checks.extend(
                (
                    (
                        "direct_content_ownership.content_record_id",
                        "member of chapter_scope_content_ids",
                        item["content_record_id"],
                    ),
                    (
                        "direct_content_ownership.chapter_scope_section_id",
                        target,
                        item["chapter_scope_section_id"],
                    ),
                    (
                        "direct_content_ownership.current_owner_section_id",
                        item["original_owner_section_id"],
                        item["current_owner_section_id"],
                    ),
                    (
                        "direct_content_ownership.original_owner_section_id.namespace",
                        owner_prefix,
                        item["original_owner_section_id"],
                    ),
                )
            )
        checks.extend(
            (
                (
                    "direct_content_ownership.content_record_id uniqueness",
                    len(ownership_ids),
                    len(set(ownership_ids)),
                ),
                (
                    "direct_content_ownership.source_stable_item_key uniqueness",
                    len(ownership_keys),
                    len(set(ownership_keys)),
                ),
            )
        )
        if record["following_boundary_kind"] == "following_heading":
            checks.extend(
                (
                    (
                        "following_boundary_record_id.namespace",
                        block_prefix,
                        record["following_boundary_record_id"],
                    ),
                    (
                        "scope_boundary_record_id.namespace",
                        tuple(scope_prefixes.values()),
                        record["scope_boundary_record_id"],
                    ),
                )
            )
        else:
            document_id = f"{inferred_candidate}/document/{record['source_id']}"
            checks.extend(
                (
                    (
                        "following_boundary_record_id",
                        document_id,
                        record["following_boundary_record_id"],
                    ),
                    ("scope_boundary_record_id", document_id, record["scope_boundary_record_id"]),
                )
            )
        for field, expected, observed in checks:
            valid = observed == expected
            if field.endswith(".namespace"):
                valid = _matches_namespace(observed, expected)
            elif expected == "member of chapter_scope_content_ids":
                valid = observed in record["chapter_scope_content_ids"]
            if not valid:
                raise _correspondence_mismatch(
                    "missing-chapter correspondence semantic binding failed",
                    record,
                    target,
                    field,
                    expected,
                    observed,
                )
        prior_end = end


def _validate_section_inverse(
    records: list[JsonObject],
    sections: list[JsonObject],
    content: list[JsonObject] | None,
    content_record_count: int | None,
) -> None:
    chapter_sections = {
        (_record_source_id(item["id"]), item["chapter_marker"]): item
        for item in sections
        if item["section_kind"] in {"composite_semantic", "derived_chapter"}
    }
    by_marker = {(item["source_id"], item["chapter_marker"]): item for item in records}
    if len(by_marker) != len(records) or set(by_marker) != set(chapter_sections):
        raise StructureContractError(
            "missing-chapter correspondence is not one-to-one with projected chapters"
        )
    for marker, record in by_marker.items():
        section = chapter_sections[marker]
        derivation = section["derivation_ref"]
        expected = {
            "source_id": _record_source_id(section["id"]),
            "chapter_title": section["structural_title"],
            "representation": section["chapter_representation"],
            "decision_ref": section["evidence_ref"],
            "new_target": {
                "section_id": section["id"],
                "state": "projected_candidate_local",
            },
            "retained_heading_block_ids": section["heading_component_block_ids"],
            "ordered_child_refs": derivation["ordered_child_refs"],
            "chapter_scope_content_ids": section["chapter_scope_content_ids"],
            "logical_content_page_extent": [
                derivation["extent_start_page"],
                derivation["extent_end_page"],
            ],
            "following_boundary_record_id": section["following_boundary_record_id"],
            "scope_boundary_record_id": section["scope_boundary_record_id"],
            "following_boundary_kind": (
                "document_end"
                if "/document/" in section["following_boundary_record_id"]
                else "following_heading"
            ),
            "content_record_count": content_record_count,
        }
        for field, value in expected.items():
            if record[field] != value:
                raise _correspondence_mismatch(
                    f"missing-chapter correspondence differs from section field {field}",
                    record,
                    section["id"],
                    field,
                    value,
                    record[field],
                )
        ownership = record["direct_content_ownership"]
        if [_entity_tail(item["content_record_id"]) for item in ownership] != [
            _entity_tail(item) for item in derivation["direct_content_record_refs"]
        ]:
            raise _correspondence_mismatch(
                "missing-chapter correspondence differs from direct content derivation",
                record,
                section["id"],
                "direct_content_ownership.content_record_id",
                derivation["direct_content_record_refs"],
                [item["content_record_id"] for item in ownership],
            )
        if content is not None:
            by_id = {item["id"]: item for item in content}
            for item in ownership:
                current = by_id.get(item["content_record_id"])
                if current is None:
                    raise _correspondence_mismatch(
                        "missing-chapter direct content ownership differs from current content",
                        record,
                        item["content_record_id"],
                        "content_record_id",
                        item["content_record_id"],
                        None,
                    )
                for field, expected_value, observed_value in (
                    (
                        "source_stable_item_key",
                        item["source_stable_item_key"],
                        current.get("stable_item_key"),
                    ),
                    (
                        "current_owner_section_id",
                        item["current_owner_section_id"],
                        current.get("section_id"),
                    ),
                    (
                        "original_owner_section_id",
                        item["current_owner_section_id"],
                        item["original_owner_section_id"],
                    ),
                ):
                    if observed_value != expected_value:
                        raise _correspondence_mismatch(
                            "missing-chapter direct content ownership differs from current content",
                            record,
                            item["content_record_id"],
                            field,
                            expected_value,
                            observed_value,
                        )


def _correspondence_mismatch(
    context: str,
    record: JsonObject,
    record_id: object,
    field: str,
    expected: object,
    observed: object,
) -> StructureContractError:
    """Build an actionable correspondence error with stable evidence coordinates."""
    return StructureContractError(
        f"{context}: chapter={record.get('chapter_marker')!r}, record={record_id!r}, "
        f"field={field!r}, expected={expected!r}, observed={observed!r}"
    )


def _matches_namespace(observed: object, expected: object) -> bool:
    """Match one record ID against a required prefix or tuple of prefixes."""
    if not isinstance(observed, str):
        return False
    if isinstance(expected, str):
        return observed.startswith(expected)
    if isinstance(expected, tuple):
        return all(isinstance(prefix, str) for prefix in expected) and any(
            observed.startswith(prefix) for prefix in expected
        )
    return False


def _record_source_id(record_id: str) -> str:
    marker = "/section/"
    if marker not in record_id:
        raise StructureContractError("missing-chapter section has invalid ID")
    return record_id.split(marker, maxsplit=1)[1].split("/", maxsplit=1)[0]


def _entity_tail(record_id: str) -> str:
    """Compare old and candidate-local record IDs by stable family/source suffix."""
    return record_id.split("/", maxsplit=1)[1] if record_id.startswith("exv1-") else record_id
