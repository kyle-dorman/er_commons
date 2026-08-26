from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.human_review_support.task04.models import JsonValue
from er_commons.human_review_support.task04.records import RecordValidator

SCHEMA_PARENT = Path(__file__).parents[1] / "benchmarks/er_bench/schemas"
SCHEMA_ROOT = SCHEMA_PARENT / "task04_review/v1"
FAILURE_PAYLOAD: dict[str, JsonValue] = {
    "source_id": "source",
    "current_status": "unresolved_missing_publication",
    "selected_candidate_id": None,
    "attempts": [],
}
WARNING_PAYLOAD: dict[str, JsonValue] = {
    "owners": ["producer"],
    "codes": ["warning"],
    "fingerprint": "normalized warning",
    "occurrence_count": 1,
    "raw_occurrence_count": 1,
    "source_counts": {"source": 1},
    "owner_code_counts": [{"owner": "producer", "code": "warning", "count": 1}],
    "representative_message": "warning",
    "page_anchor_kind": "exact_page",
    "table_parser_evidence": None,
}


def _base_item(queue: str) -> dict[str, JsonValue]:
    return {
        "queue": queue,
        "review_item_id": f"reviewitem-{'c' * 24}",
        "source_id": "source",
        "candidate_id": None,
        "physical_pages": [1] if queue != "failure" else [],
        "reasons": ["test"],
        "population": {},
        "exact_evidence": {"canonical_objects": [], "observations": []},
    }


def test_task04_and_task04a_schemas_have_separate_closure() -> None:
    task04 = sorted(path.stem for path in SCHEMA_ROOT.glob("*.schema.json"))
    task04a = sorted(path.stem for path in (SCHEMA_PARENT / "task04a_review/v1").glob("*.json"))

    assert task04 == [
        "finding_register.schema",
        "input_inventory.schema",
        "review_bundle_manifest.schema",
        "selection_manifest.schema",
        "task03i_handoff.schema",
    ]
    assert task04a == ["release_freeze.schema", "usability_registry.schema"]
    schemas = (
        *SCHEMA_ROOT.glob("*.json"),
        *(SCHEMA_PARENT / "task04a_review/v1").glob("*.json"),
    )
    for path in schemas:
        Draft202012Validator.check_schema(json.loads(path.read_text()))


def test_record_validator_reports_record_and_json_path() -> None:
    record: dict[str, JsonValue] = {
        "schema_version": "er_commons.task04_review.v1.selection_manifest",
        "review_run_id": f"reviewv1-task03h-first-{'a' * 16}",
        "pass": "task03h_first",
        "selection_policy": {"rule": "test"},
        "selection_policy_sha256": "b" * 64,
        "items": [
            {
                "queue": "warning",
                "review_item_id": f"reviewitem-{'c' * 24}",
                "source_id": "source",
                "candidate_id": None,
                "physical_pages": [],
                "reasons": ["test"],
                "population": {},
            }
        ],
        "queue_counts": {"warning": 1},
    }

    with pytest.raises(ValueError, match=r"invalid Task 04 selection_manifest.*\$\.items\[0\]"):
        RecordValidator(SCHEMA_ROOT).validate("selection_manifest", record)


@pytest.mark.parametrize(
    ("queue", "required_payload", "foreign_payload"),
    [
        ("valid_page", {}, {"table_family_id": "family-1"}),
        ("table", {"table_family_id": "family-1"}, {"failure": FAILURE_PAYLOAD}),
        ("failure", {"failure": FAILURE_PAYLOAD}, {"warning": WARNING_PAYLOAD}),
        ("warning", {"warning": WARNING_PAYLOAD}, {"table_family_id": "family-1"}),
    ],
)
def test_selection_queue_variants_reject_cross_queue_payloads(
    queue: str,
    required_payload: dict[str, JsonValue],
    foreign_payload: dict[str, JsonValue],
) -> None:
    item = {**_base_item(queue), **required_payload, **foreign_payload}

    with pytest.raises(ValueError, match=r"invalid Task 04 selection_manifest.*\$\.items\[0\]"):
        RecordValidator(SCHEMA_ROOT).validate("selection_manifest", _selection_record(item))


@pytest.mark.parametrize(
    "item",
    [
        _base_item("valid_page"),
        {**_base_item("table"), "table_family_id": "family-1"},
        {**_base_item("failure"), "failure": FAILURE_PAYLOAD},
        {**_base_item("warning"), "warning": WARNING_PAYLOAD},
    ],
)
def test_selection_queue_variants_accept_only_their_own_payload(
    item: dict[str, JsonValue],
) -> None:
    RecordValidator(SCHEMA_ROOT).validate("selection_manifest", _selection_record(item))


def test_finding_and_handoff_anchor_schema_definitions_stay_identical() -> None:
    register = json.loads((SCHEMA_ROOT / "finding_register.schema.json").read_text())
    handoff = json.loads((SCHEMA_ROOT / "task03i_handoff.schema.json").read_text())
    names = (
        "anchor",
        "source_binding",
        "candidate_binding",
        "page_anchor",
        "table_family_anchor",
        "warning_anchor",
        "failure_anchor",
        "canonical_table_anchor",
        "canonical_block_anchor",
        "observation_anchor",
        "nullable_bbox",
    )
    assert {name: register["$defs"][name] for name in names} == {
        name: handoff["$defs"][name] for name in names
    }


def _selection_record(item: dict[str, JsonValue]) -> dict[str, JsonValue]:
    return {
        "schema_version": "er_commons.task04_review.v1.selection_manifest",
        "review_run_id": f"reviewv1-task03h-first-{'a' * 16}",
        "pass": "task03h_first",
        "selection_policy": {"rule": "test"},
        "selection_policy_sha256": "b" * 64,
        "items": [item],
        "queue_counts": {str(item["queue"]): 1},
    }
