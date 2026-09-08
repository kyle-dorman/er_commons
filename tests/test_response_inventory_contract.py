"""Source-free tests for the Task 05 response-inventory MVP contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.response_inventory import (
    build_publication_id,
    build_record_id,
    semantic_bundle_digest,
    validate_contract_fixtures,
    validate_managed_files,
    validate_record_bundle,
)
from er_commons.response_inventory.__main__ import main
from er_commons.response_inventory.contract import _materialize_fixture_records

REPO_ROOT = Path(__file__).parents[1]
SCHEMA_PATH = REPO_ROOT / "benchmarks/er_bench/schemas/response_inventory/v1/records.schema.json"
FIXTURE_ROOT = REPO_ROOT / "benchmarks/er_bench/fixtures/response_inventory/v1"


def test_checked_in_source_free_contract_fixtures() -> None:
    assert validate_contract_fixtures(SCHEMA_PATH, FIXTURE_ROOT) == 8


def test_record_identity_ignores_runtime_and_display_fields() -> None:
    record = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "source_unit",
        "source_id": "source-a",
        "unit_kind": "response",
        "official_label": "Response A-1",
        "start_marker_id": "markerv1-" + "9" * 64,
        "span_ids": ["spanv1-" + "0" * 64],
        "submission_id": None,
        "activity_id": "activityv1-" + "1" * 64,
    }
    identity = build_record_id(record)
    changed_runtime = {**record, "activity_id": "activityv1-" + "2" * 64}
    assert build_record_id(changed_runtime) == identity

    changed_anchor = {**record, "span_ids": ["spanv1-" + "3" * 64]}
    assert build_record_id(changed_anchor) != identity


def test_span_identity_excludes_visual_and_character_slot_evidence() -> None:
    span = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "source_span",
        "source_id": "source-a",
        "fragments": [
            {
                "page_id": "pagev1-" + "0" * 64,
                "text_start": 4,
                "text_end": 9,
                "character_slot_start": 5,
                "character_slot_end": 10,
                "bbox": [1, 2, 3, 4],
                "revision_marks": ["underline"],
            }
        ],
    }
    identity = build_record_id(span)
    changed_visual = json.loads(json.dumps(span))
    changed_visual["fragments"][0].update(
        {"character_slot_start": None, "character_slot_end": None, "bbox": None}
    )
    changed_visual["fragments"][0].pop("revision_marks")
    assert build_record_id(changed_visual) == identity

    changed_text_anchor = json.loads(json.dumps(span))
    changed_text_anchor["fragments"][0]["text_end"] = 10
    assert build_record_id(changed_text_anchor) != identity


def test_semantic_digest_is_independent_of_discovery_order() -> None:
    first = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "page",
        "source_id": "source-a",
        "physical_page": 1,
    }
    first["page_id"] = build_record_id(first)
    second = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "page",
        "source_id": "source-a",
        "physical_page": 2,
    }
    second["page_id"] = build_record_id(second)
    assert semantic_bundle_digest([first, second]) == semantic_bundle_digest([second, first])


def test_publication_identity_excludes_working_path_and_timestamp() -> None:
    activity_id = "activityv1-" + "a" * 64
    inventory = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "managed_file_inventory",
        "stage": "05g",
        "activity_id": activity_id,
        "dependencies": [],
        "files": [
            {
                "authority": "bundle",
                "path": "inventory/records.jsonl",
                "sha256": "b" * 64,
                "byte_size": 1,
            }
        ],
    }
    inventory["inventory_id"] = build_record_id(inventory)
    completion = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "stage_completion",
        "stage": "05g",
        "status": "complete",
        "activity_id": activity_id,
        "inventory_id": inventory["inventory_id"],
        "counts": {"general_responses": 8, "placement_exceptions": 1},
        "completed_at": "2026-09-08T12:00:00Z",
    }
    completion["completion_id"] = build_record_id(completion)
    publication_id = build_publication_id(completion, inventory)
    assert publication_id.startswith("inventoryv1-")
    assert len(publication_id) == len("inventoryv1-") + 64


def test_managed_file_validation_allows_working_size_closure(tmp_path: Path) -> None:
    output = tmp_path / "records.jsonl"
    output.write_text("{}\n")
    inventory = {
        "stage": "05c",
        "files": [
            {
                "authority": "bundle",
                "path": "records.jsonl",
                "sha256": None,
                "byte_size": 3,
            }
        ],
    }
    assert validate_managed_files(inventory, tmp_path) == 1


def test_source_free_module_entrypoint(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--schema", str(SCHEMA_PATH), "--fixtures", str(FIXTURE_ROOT)]) == 0
    output = capsys.readouterr().out
    assert "response_inventory_contract=valid" in output


def test_schema_is_one_small_record_union() -> None:
    schema = json.loads(SCHEMA_PATH.read_text())
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert len(schema["oneOf"]) == 18
    assert "normalized_text" not in schema["$defs"]["page"]["properties"]


def test_source_unit_cannot_claim_a_review_activity() -> None:
    fixture = json.loads((FIXTURE_ROOT / "valid_mvp_bundle.json").read_text())
    records = _materialize_fixture_records(fixture["records"])
    review_activity_id = next(
        record["activity_id"]
        for record in records
        if record["record_type"] == "activity" and record["stage"] == "05g"
    )
    unit = next(record for record in records if record["record_type"] == "source_unit")
    unit["activity_id"] = review_activity_id
    schema = json.loads(SCHEMA_PATH.read_text())
    with pytest.raises(ValueError, match="source_unit has an activity from the wrong stage"):
        validate_record_bundle(records, schema)


def test_source_unit_requires_at_least_one_span() -> None:
    fixture = json.loads((FIXTURE_ROOT / "valid_mvp_bundle.json").read_text())
    records = _materialize_fixture_records(fixture["records"])
    unit = next(record for record in records if record["record_type"] == "source_unit")
    unit["span_ids"] = []
    unit["unit_id"] = build_record_id(unit)
    schema = json.loads(SCHEMA_PATH.read_text())
    with pytest.raises(ValueError, match="fails JSON Schema"):
        validate_record_bundle(records, schema)


def test_directed_edge_rejects_reverse_mention_evidence() -> None:
    fixture = json.loads((FIXTURE_ROOT / "valid_graph_cardinality.json").read_text())
    records = _materialize_fixture_records(fixture["records"])
    reverse_mention_id = next(
        record["mention_id"]
        for record in records
        if record["record_type"] == "reference_mention" and len(record["target_labels"]) == 2
    )
    edge = next(record for record in records if record["record_type"] == "semantic_edge")
    edge["evidence_ids"] = [reverse_mention_id]
    schema = json.loads(SCHEMA_PATH.read_text())
    with pytest.raises(ValueError, match="mention evidence does not name an endpoint"):
        validate_record_bundle(records, schema)


def test_activity_inputs_must_equal_managed_inventory_dependencies() -> None:
    fixture = json.loads((FIXTURE_ROOT / "valid_page_states.json").read_text())
    inventory = next(
        record for record in fixture["records"] if record["record_type"] == "managed_file_inventory"
    )
    inventory["dependencies"][0]["identity"] = "sourcev1-different"
    records = _materialize_fixture_records(fixture["records"])
    schema = json.loads(SCHEMA_PATH.read_text())
    with pytest.raises(
        ValueError, match="activity input_refs differ from managed inventory dependencies"
    ):
        validate_record_bundle(records, schema)


def test_gr9_placement_exception_requires_nonempty_same_activity_evidence() -> None:
    fixture = json.loads((FIXTURE_ROOT / "valid_page_states.json").read_text())
    exception = next(
        record
        for record in fixture["records"]
        if record["record_type"] == "source_placement_exception"
    )
    exception["evidence_ids"] = []
    records = _materialize_fixture_records(fixture["records"])
    schema = json.loads(SCHEMA_PATH.read_text())
    with pytest.raises(ValueError, match="fails JSON Schema"):
        validate_record_bundle(records, schema)

    fixture = json.loads((FIXTURE_ROOT / "valid_page_states.json").read_text())
    exception = next(
        record
        for record in fixture["records"]
        if record["record_type"] == "source_placement_exception"
    )
    foreign_activity = {
        **next(record for record in fixture["records"] if record["record_type"] == "activity"),
        "fixture_key": "foreign-activity",
        "source_id": "another_source",
        "page_ranges": [[1, 1]],
    }
    foreign_page = {
        **next(record for record in fixture["records"] if record.get("fixture_key") == "section"),
        "fixture_key": "foreign-page",
        "source_id": "another_source",
        "physical_page": 1,
        "activity_id": "@foreign-activity",
    }
    fixture["records"].extend([foreign_activity, foreign_page])
    exception["evidence_ids"] = ["@foreign-page"]
    records = _materialize_fixture_records(fixture["records"])
    with pytest.raises(
        ValueError, match="source-placement exception evidence must use its source activity"
    ):
        validate_record_bundle(records, schema)


@pytest.mark.parametrize(
    ("count_name", "wrong_value"),
    [
        ("completed_ranges", 0),
        ("emitted_pages", 6),
        ("marker_candidates", 1),
        ("general_response_units", 8),
        ("placement_exceptions", 0),
    ],
)
def test_05c_completion_counts_reconcile_with_records(count_name: str, wrong_value: int) -> None:
    fixture = json.loads((FIXTURE_ROOT / "valid_page_states.json").read_text())
    completion = next(
        record for record in fixture["records"] if record["record_type"] == "stage_completion"
    )
    completion["counts"][count_name] = wrong_value
    records = _materialize_fixture_records(fixture["records"])
    schema = json.loads(SCHEMA_PATH.read_text())
    with pytest.raises(ValueError, match=f"05C completion count differs for {count_name}"):
        validate_record_bundle(records, schema)


def test_05c_completion_does_not_require_all_general_responses() -> None:
    fixture = json.loads((FIXTURE_ROOT / "valid_page_states.json").read_text())
    records = _materialize_fixture_records(fixture["records"])
    assert not any(record["record_type"] == "source_unit" for record in records)
    schema = json.loads(SCHEMA_PATH.read_text())
    validate_record_bundle(records, schema)
