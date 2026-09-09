"""Source-free tests for the Task 05 response-inventory MVP contract."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
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
from er_commons.response_inventory.contract import (
    _materialize_fixture_records,
    task05d_completion_counts,
)

REPO_ROOT = Path(__file__).parents[1]
SCHEMA_PATH = REPO_ROOT / "benchmarks/er_bench/schemas/response_inventory/v1/records.schema.json"
FIXTURE_ROOT = REPO_ROOT / "benchmarks/er_bench/fixtures/response_inventory/v1"

SOURCE_COUNT_NAMES = (
    "declared_ranges",
    "completed_ranges",
    "failed_ranges",
    "declared_pages",
    "emitted_pages",
    "page_continuations",
    "marker_candidates",
    "source_spans",
    "commenters",
    "submissions",
    "source_units",
    "comment_units",
    "response_units",
    "general_response_units",
    "membership_claims",
    "reference_mentions",
    "placement_exceptions",
    "diagnostics",
    "open_range_boundary_diagnostics",
    "source_response_heading_absent_diagnostics",
)


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
        "counts": {"general_response_units": 8, "placement_exceptions": 1},
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


def test_complete_05d_bundle_reconciles_full_source_counts() -> None:
    records = _complete_05d_bundle()
    schema = json.loads(SCHEMA_PATH.read_text())

    validate_record_bundle(records, schema)


@pytest.mark.parametrize("count_name", SOURCE_COUNT_NAMES)
def test_05d_completion_reconciles_every_source_count(count_name: str) -> None:
    records = _complete_05d_bundle()
    completion = _record_for_stage(records, "stage_completion", "05d")
    completion["counts"][count_name] += 1
    completion["completion_id"] = build_record_id(completion)
    schema = json.loads(SCHEMA_PATH.read_text())

    with pytest.raises(ValueError, match=f"05D completion count differs for {count_name}"):
        validate_record_bundle(records, schema)


def test_05d_completion_schema_requires_explicit_continuation_count() -> None:
    records = _complete_05d_bundle()
    completion = _record_for_stage(records, "stage_completion", "05d")
    del completion["counts"]["page_continuations"]
    completion["completion_id"] = build_record_id(completion)
    schema = json.loads(SCHEMA_PATH.read_text())

    with pytest.raises(ValueError, match="fails JSON Schema"):
        validate_record_bundle(records, schema)


def test_05d_completion_requires_exact_full_volume_scope() -> None:
    records = _complete_05d_bundle(last_page=743)
    schema = json.loads(SCHEMA_PATH.read_text())

    with pytest.raises(ValueError, match="exact 1-744 range"):
        validate_record_bundle(records, schema)


def test_05d_completion_rejects_range_boundary_diagnostic() -> None:
    records = _complete_05d_bundle(include_boundary_diagnostic=True)
    schema = json.loads(SCHEMA_PATH.read_text())

    with pytest.raises(ValueError, match="cannot retain a range-boundary diagnostic"):
        validate_record_bundle(records, schema)


def test_05d_activity_rejects_extra_dependency_role() -> None:
    records = _complete_05d_bundle(extra_dependency=True)
    schema = json.loads(SCHEMA_PATH.read_text())

    with pytest.raises(ValueError, match="exact stage contract"):
        validate_record_bundle(records, schema)


def test_05d_completion_requires_distinct_general_response_labels_1_through_8() -> None:
    records = _complete_05d_bundle()
    general_responses = [
        record
        for record in records
        if record["record_type"] == "source_unit" and record["unit_kind"] == "general_response"
    ]
    general_responses[-1]["official_label"] = "General Response 7"
    general_responses[-1]["unit_id"] = build_record_id(general_responses[-1])
    schema = json.loads(SCHEMA_PATH.read_text())

    with pytest.raises(ValueError, match="must contain General Responses 1-8"):
        validate_record_bundle(records, schema)


def test_05d_general_response_accounting_is_scoped_to_its_activity() -> None:
    records = _complete_05d_bundle()
    records.extend(_foreign_05c_placement_records())
    schema = json.loads(SCHEMA_PATH.read_text())

    validate_record_bundle(records, schema)


def test_05d_completion_counts_exclude_foreign_activity_records() -> None:
    records = _complete_05d_bundle()
    activity = _record_for_stage(records, "activity", "05d")
    baseline = task05d_completion_counts(activity, records)
    foreign = _foreign_counted_source_records()

    assert task05d_completion_counts(activity, [*records, *foreign]) == baseline


def _complete_05d_bundle(
    *,
    last_page: int = 744,
    include_boundary_diagnostic: bool = False,
    extra_dependency: bool = False,
) -> list[dict[str, object]]:
    """Build a compact semantic 05D bundle while retaining all 744 page rows."""
    dependencies: list[dict[str, object]] = [
        {
            "role": "source_record",
            "identity": "sourcev1-synthetic",
            "authority": "artifact_root",
            "path": "sources/feir_volume_4/source.json",
        },
        {
            "role": "task05c_completion",
            "identity": "completionv1-05c-synthetic",
            "authority": "artifact_root",
            "path": "pilots/05c/records/stage_completion.json",
        },
    ]
    if extra_dependency:
        dependencies.append(
            {
                "role": "task05a_completion",
                "identity": "completionv1-05a-synthetic",
                "authority": "artifact_root",
                "path": "working/05a/records/stage_completion.json",
            }
        )
    dependencies.sort(key=lambda item: (item["role"], item["identity"], item["path"]))
    activity: dict[str, object] = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "activity",
        "stage": "05d",
        "source_id": "feir_volume_4",
        "page_ranges": [[1, last_page]],
        "config_sha256": "0" * 64,
        "schema_sha256": "1" * 64,
        "code_sha256": "2" * 64,
        "tool_versions": {},
        "input_refs": dependencies,
    }
    activity["activity_id"] = build_record_id(activity)
    source_text = "\n".join(
        [
            *(f"General Response {number}" for number in range(1, 9)),
            "General Response 9 is in Volume 5",
        ]
    )
    pages: list[dict[str, object]] = []
    for number in range(1, last_page + 1):
        raw_text = source_text if number == 1 else ""
        page: dict[str, object] = {
            "schema_version": "er_commons.response_inventory.v1",
            "record_type": "page",
            "source_id": "feir_volume_4",
            "physical_page": number,
            "page_state": "section_opener" if number == 1 else "blank",
            "raw_text": raw_text,
            "raw_text_sha256": hashlib.sha256(raw_text.encode()).hexdigest(),
            "page_box": {"width_points": 612, "height_points": 792, "rotation": 0},
            "character_slot_count": len(raw_text),
            "activity_id": activity["activity_id"],
        }
        page["page_id"] = build_record_id(page)
        pages.append(page)
    first_page = pages[0]
    spans: list[dict[str, object]] = []
    units: list[dict[str, object]] = []
    for number in range(1, 9):
        label = f"General Response {number}"
        start = source_text.index(label)
        span = _single_fragment_span(first_page, start, start + len(label))
        unit: dict[str, object] = {
            "schema_version": "er_commons.response_inventory.v1",
            "record_type": "source_unit",
            "source_id": "feir_volume_4",
            "unit_kind": "general_response",
            "official_label": label,
            "start_marker_id": None,
            "span_ids": [span["span_id"]],
            "submission_id": None,
            "activity_id": activity["activity_id"],
        }
        unit["unit_id"] = build_record_id(unit)
        spans.append(span)
        units.append(unit)
    gr9_start = source_text.index("General Response 9")
    gr9_span = _single_fragment_span(first_page, gr9_start, len(source_text))
    exception: dict[str, object] = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "source_placement_exception",
        "source_id": "feir_volume_4",
        "activity_id": activity["activity_id"],
        "exception_code": "general_response_9_not_in_volume_4",
        "advertised_label": "General Response 9",
        "routed_volume": 5,
        "disposition": "cross_volume_scope_exception",
        "evidence_ids": [gr9_span["span_id"]],
    }
    exception["exception_id"] = build_record_id(exception)
    continuation: dict[str, object] = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "page_continuation",
        "from_page_id": pages[0]["page_id"],
        "to_page_id": pages[1]["page_id"],
        "continuation_kind": "general_response",
        "evidence_ids": [units[0]["unit_id"]],
    }
    continuation["continuation_id"] = build_record_id(continuation)
    records: list[dict[str, object]] = [
        activity,
        *pages,
        *spans,
        gr9_span,
        *units,
        continuation,
        exception,
    ]
    if include_boundary_diagnostic:
        diagnostic: dict[str, object] = {
            "schema_version": "er_commons.response_inventory.v1",
            "record_type": "diagnostic",
            "stage": "05d",
            "activity_id": activity["activity_id"],
            "code": "unit_boundary_ambiguous",
            "severity": "warning",
            "terminal": True,
            "subject_ids": [units[0]["unit_id"]],
            "evidence_ids": [spans[0]["span_id"]],
            "message": "Synthetic boundary warning.",
        }
        diagnostic["diagnostic_id"] = build_record_id(diagnostic)
        records.append(diagnostic)
    inventory: dict[str, object] = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "managed_file_inventory",
        "stage": "05d",
        "activity_id": activity["activity_id"],
        "dependencies": deepcopy(dependencies),
        "files": [
            {
                "authority": "bundle",
                "path": "inventory/source_records.jsonl",
                "sha256": None,
                "byte_size": 1,
            }
        ],
    }
    inventory["inventory_id"] = build_record_id(inventory)
    counts = {
        "declared_ranges": 1,
        "completed_ranges": 1,
        "failed_ranges": 0,
        "declared_pages": last_page,
        "emitted_pages": last_page,
        "page_continuations": 1,
        "marker_candidates": 0,
        "source_spans": 9,
        "commenters": 0,
        "submissions": 0,
        "source_units": 8,
        "comment_units": 0,
        "response_units": 0,
        "general_response_units": 8,
        "membership_claims": 0,
        "reference_mentions": 0,
        "placement_exceptions": 1,
        "diagnostics": int(include_boundary_diagnostic),
        "open_range_boundary_diagnostics": int(include_boundary_diagnostic),
        "source_response_heading_absent_diagnostics": 0,
    }
    completion: dict[str, object] = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "stage_completion",
        "stage": "05d",
        "status": "complete_with_warnings" if include_boundary_diagnostic else "complete",
        "activity_id": activity["activity_id"],
        "inventory_id": inventory["inventory_id"],
        "counts": counts,
        "warnings": ["Synthetic boundary warning."] if include_boundary_diagnostic else [],
        "completed_at": "2026-09-08T12:00:00Z",
    }
    completion["completion_id"] = build_record_id(completion)
    return [*records, inventory, completion]


def _single_fragment_span(page: dict[str, object], start: int, end: int) -> dict[str, object]:
    span: dict[str, object] = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "source_span",
        "source_id": page["source_id"],
        "fragments": [
            {
                "page_id": page["page_id"],
                "text_start": start,
                "text_end": end,
                "character_slot_start": None,
                "character_slot_end": None,
                "bbox": None,
                "revision_marks": [],
            }
        ],
    }
    span["span_id"] = build_record_id(span)
    return span


def _record_for_stage(
    records: list[dict[str, object]], record_type: str, stage: str
) -> dict[str, object]:
    return next(
        record
        for record in records
        if record["record_type"] == record_type and record.get("stage") == stage
    )


def _foreign_05c_placement_records() -> list[dict[str, object]]:
    dependencies = [
        {
            "role": "source_record",
            "identity": "sourcev1-foreign",
            "authority": "artifact_root",
            "path": "sources/foreign/source.json",
        },
        {
            "role": "task05a_completion",
            "identity": "completionv1-05a-foreign",
            "authority": "artifact_root",
            "path": "working/05a/foreign-completion.json",
        },
    ]
    activity: dict[str, object] = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "activity",
        "stage": "05c",
        "source_id": "foreign_source",
        "page_ranges": [[1, 1]],
        "config_sha256": "3" * 64,
        "schema_sha256": "4" * 64,
        "code_sha256": "5" * 64,
        "tool_versions": {},
        "input_refs": dependencies,
    }
    activity["activity_id"] = build_record_id(activity)
    raw_text = "General Response 9 is in Volume 5"
    page: dict[str, object] = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "page",
        "source_id": "foreign_source",
        "physical_page": 1,
        "page_state": "section_opener",
        "raw_text": raw_text,
        "raw_text_sha256": hashlib.sha256(raw_text.encode()).hexdigest(),
        "page_box": {"width_points": 612, "height_points": 792, "rotation": 0},
        "character_slot_count": len(raw_text),
        "activity_id": activity["activity_id"],
    }
    page["page_id"] = build_record_id(page)
    span = _single_fragment_span(page, 0, len(raw_text))
    exception: dict[str, object] = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "source_placement_exception",
        "source_id": "foreign_source",
        "activity_id": activity["activity_id"],
        "exception_code": "general_response_9_not_in_volume_4",
        "advertised_label": "General Response 9",
        "routed_volume": 5,
        "disposition": "cross_volume_scope_exception",
        "evidence_ids": [span["span_id"]],
    }
    exception["exception_id"] = build_record_id(exception)
    return [activity, page, span, exception]


def _foreign_counted_source_records() -> list[dict[str, object]]:
    """Return foreign rows covering every activity-scoped count family."""
    records = _foreign_05c_placement_records()
    activity, page, span = records[:3]
    marker_id = "markerv1-" + "6" * 64
    unit_id = "unitv1-" + "7" * 64
    records.extend(
        [
            {
                "record_type": "page_continuation",
                "continuation_id": "continuationv1-" + "6" * 64,
                "from_page_id": page["page_id"],
                "to_page_id": page["page_id"],
            },
            {
                "record_type": "marker_candidate",
                "marker_id": marker_id,
                "page_id": page["page_id"],
            },
            {
                "record_type": "commenter",
                "commenter_id": "commenterv1-" + "6" * 64,
                "source_id": activity["source_id"],
                "opener_span_id": span["span_id"],
            },
            {
                "record_type": "submission",
                "submission_id": "submissionv1-" + "6" * 64,
                "source_id": activity["source_id"],
                "opener_span_id": span["span_id"],
            },
            {
                "record_type": "source_unit",
                "unit_id": unit_id,
                "unit_kind": "comment",
                "activity_id": activity["activity_id"],
            },
            {
                "record_type": "membership_claim",
                "claim_id": "membershipv1-" + "6" * 64,
                "general_response_unit_id": unit_id,
            },
            {
                "record_type": "reference_mention",
                "mention_id": "mentionv1-" + "6" * 64,
                "source_unit_id": unit_id,
            },
            {
                "record_type": "diagnostic",
                "diagnostic_id": "diagnosticv1-" + "6" * 64,
                "activity_id": activity["activity_id"],
                "code": "unit_boundary_ambiguous",
                "terminal": True,
            },
        ]
    )
    return records
