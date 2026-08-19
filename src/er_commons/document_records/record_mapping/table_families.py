"""Load and cross-check producer table-family definitions and assignments."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.table_records import (
    FamilyEvidence,
    JsonObject,
    ProducerTableFamily,
    read_json_object,
    read_jsonl_objects,
)


def _validate_continuation_evidence(
    family_payload: JsonObject,
    *,
    family_by_id: dict[str, ProducerTableFamily],
    assignment_by_table: dict[str, str],
) -> None:
    expected_family_ids = {
        family.family_id
        for family in family_by_id.values()
        if "cross_page_continuation" in family.evidence
    }
    raw_decisions = family_payload.get("continuation_decisions", [])
    if not isinstance(raw_decisions, list) or not all(
        isinstance(decision, dict) for decision in raw_decisions
    ):
        raise MappingContractError("table_families.json has invalid continuation decisions")
    accepted_family_ids: set[str] = set()
    for decision in raw_decisions:
        if decision.get("status") != "accepted":
            continue
        left_table = decision.get("left_table_id")
        right_table = decision.get("right_table_id")
        inherited = decision.get("inherited_header")
        valid = (
            isinstance(left_table, str)
            and isinstance(right_table, str)
            and assignment_by_table.get(left_table) is not None
            and assignment_by_table.get(left_table) == assignment_by_table.get(right_table)
            and isinstance(inherited, dict)
            and inherited.get("origin") == "inherited"
            and inherited.get("content_status") == "unresolved_no_printed_header_projection"
            and inherited.get("source_table_id") == left_table
        )
        if not valid:
            raise MappingContractError("invalid accepted continuation evidence")
        assert isinstance(left_table, str)
        accepted_family_ids.add(assignment_by_table[left_table])
    if accepted_family_ids != expected_family_ids:
        raise MappingContractError("continuation family evidence lacks accepted decisions")


def load_table_families(
    table_root: Path,
) -> tuple[tuple[ProducerTableFamily, ...], dict[str, str]]:
    """Load exact family records and return their table-to-family index."""
    assignments = read_jsonl_objects(table_root / "family_assignments.jsonl")
    family_payload = read_json_object(table_root / "table_families.json")
    raw_families = family_payload.get("families")
    if not isinstance(raw_families, list) or not all(
        isinstance(record, dict) for record in raw_families
    ):
        raise MappingContractError("table_families.json has invalid families")
    family_by_id: dict[str, ProducerTableFamily] = {}
    for record in raw_families:
        family_id = record.get("family_id")
        table_ids = record.get("table_ids")
        evidence = record.get("evidence")
        if (
            not isinstance(family_id, str)
            or not isinstance(table_ids, list)
            or not all(isinstance(table_id, str) for table_id in table_ids)
            or not isinstance(evidence, list)
            or not all(
                item
                in {
                    "footer_run",
                    "exact_cleaned_header",
                    "cross_page_continuation",
                    "singleton",
                }
                for item in evidence
            )
        ):
            raise MappingContractError("invalid table family record")
        if family_id in family_by_id or len(table_ids) != len(set(table_ids)):
            raise MappingContractError(f"duplicate table family content: {family_id}")
        family_by_id[family_id] = ProducerTableFamily(
            family_id=family_id,
            table_ids=tuple(table_ids),
            evidence=tuple(cast(FamilyEvidence, item) for item in evidence),
        )
    assignment_by_table: dict[str, str] = {}
    assignment_pairs: set[tuple[str, str]] = set()
    for assignment in assignments:
        table_id = assignment.get("table_id")
        family_id = assignment.get("family_id")
        if not isinstance(table_id, str) or not isinstance(family_id, str):
            raise MappingContractError("invalid table family assignment")
        if table_id in assignment_by_table:
            raise MappingContractError(f"duplicate table family assignment: {table_id}")
        assignment_by_table[table_id] = family_id
        assignment_pairs.add((table_id, family_id))
    family_pairs = {
        (table_id, family.family_id)
        for family in family_by_id.values()
        for table_id in family.table_ids
    }
    if assignment_pairs != family_pairs:
        raise MappingContractError("family assignments differ from family definitions")
    _validate_continuation_evidence(
        family_payload,
        family_by_id=family_by_id,
        assignment_by_table=assignment_by_table,
    )
    return tuple(family_by_id.values()), assignment_by_table
