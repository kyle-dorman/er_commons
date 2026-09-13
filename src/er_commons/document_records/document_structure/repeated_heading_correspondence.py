"""Closed validation for compact repeated-heading correspondence evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from jsonschema.exceptions import ValidationError  # type: ignore[import-untyped]

from er_commons.document_records.document_structure.constants import (
    REPEATED_HEADING_CORRESPONDENCE_SCHEMA_RELATIVE_PATH,
)
from er_commons.document_records.document_structure.errors import StructureContractError

JsonObject = dict[str, Any]
DEFAULT_CORRESPONDENCE_SCHEMA_PATH = (
    Path(__file__).resolve().parents[4] / REPEATED_HEADING_CORRESPONDENCE_SCHEMA_RELATIVE_PATH
)


def validate_repeated_heading_correspondence(
    payload: JsonObject,
    *,
    schema_path: Path = DEFAULT_CORRESPONDENCE_SCHEMA_PATH,
    candidate_id: str,
    expected_decision_ref: JsonObject,
    sections: list[JsonObject] | None = None,
    content: list[JsonObject] | None = None,
) -> None:
    """Validate schema, identity binding, and optional candidate-local closure."""
    schema = json.loads(schema_path.read_bytes())
    try:
        Draft202012Validator(schema).validate(payload)
    except ValidationError as error:
        raise StructureContractError(
            f"repeated-heading correspondence schema violation: {error.message}"
        ) from error
    if payload.get("candidate_id") != candidate_id:
        raise StructureContractError("repeated-heading correspondence candidate binding differs")
    if payload.get("decision_ref") != expected_decision_ref:
        raise StructureContractError("repeated-heading correspondence decision binding differs")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise StructureContractError("repeated-heading correspondence requires records")
    new_targets: set[str] = set()
    old_targets: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise StructureContractError("repeated-heading correspondence record must be an object")
        old = record.get("old_targets")
        new = record.get("new_target")
        retained = record.get("retained_heading_block_ids")
        if (
            not isinstance(old, list)
            or len(old) != 2
            or not isinstance(new, dict)
            or not isinstance(new.get("section_id"), str)
            or not isinstance(retained, list)
            or len(retained) != 2
        ):
            raise StructureContractError("repeated-heading correspondence is not two-to-one")
        old_ids = [item.get("section_id") for item in old if isinstance(item, dict)]
        if (
            len(old_ids) != 2
            or not all(isinstance(section_id, str) for section_id in old_ids)
            or len(set(old_ids)) != 2
        ):
            raise StructureContractError("repeated-heading correspondence old targets differ")
        typed_old_ids = [str(section_id) for section_id in old_ids]
        if old_targets.intersection(typed_old_ids):
            raise StructureContractError("repeated-heading correspondence reuses an old target")
        old_targets.update(typed_old_ids)
        target_id = new["section_id"]
        if not target_id.startswith(f"{candidate_id}/section/"):
            raise StructureContractError(
                "repeated-heading new target is outside candidate namespace"
            )
        if target_id in new_targets:
            raise StructureContractError("repeated-heading correspondences share a new target")
        new_targets.add(target_id)
        if any(
            not isinstance(block_id, str) or not block_id.startswith(f"{candidate_id}/block/")
            for block_id in retained
        ):
            raise StructureContractError(
                "repeated-heading retained blocks are outside candidate namespace"
            )
        if record.get("content_record_ids_unique") is not True:
            raise StructureContractError("repeated-heading content identities are not unique")
    if sections is None and content is None:
        return
    if sections is None or content is None:
        raise StructureContractError("repeated-heading candidate records must be supplied together")
    section_ids = {item.get("id") for item in sections}
    content_ids = {item.get("id") for item in content}
    if not new_targets.issubset(section_ids):
        raise StructureContractError(
            "repeated-heading new target is absent from candidate sections"
        )
    retained_ids = {
        block_id for record in records for block_id in record["retained_heading_block_ids"]
    }
    if not retained_ids.issubset(content_ids):
        raise StructureContractError(
            "repeated-heading retained block is absent from candidate content"
        )
    if any(record.get("content_record_count") != len(content) for record in records):
        raise StructureContractError("repeated-heading content count differs from candidate")
