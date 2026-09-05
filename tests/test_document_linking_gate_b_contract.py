"""Gate B contracts for the reusable document-linking replacement boundary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).parents[1]
SCHEMA_ROOT = REPO_ROOT / "benchmarks/er_bench/schemas/document_linking/v1"
FIXTURE_ROOT = REPO_ROOT / "benchmarks/er_bench/fixtures/document_linking/v1"
POLICY_PATH = REPO_ROOT / "configs/linking_policies/document_linking_v1.json"
FORBIDDEN_PORTABILITY_TEXT = (
    "brisbane",
    "task03",
    "task04",
    "/users/",
    "/volumes/",
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _strings(item)]
    return []


def _artifact_paths(value: object) -> list[str]:
    if isinstance(value, list):
        return [path for item in value for path in _artifact_paths(item)]
    if not isinstance(value, dict):
        return []
    paths = []
    if set(value) == {"authority", "path", "sha256", "byte_size"}:
        paths.append(str(value["path"]))
    return paths + [path for item in value.values() for path in _artifact_paths(item)]


def test_policy_and_run_schemas_are_valid_and_accept_checked_in_contracts() -> None:
    policy_schema = _load(SCHEMA_ROOT / "linking_policy.schema.json")
    run_schema = _load(SCHEMA_ROOT / "document_link_run.schema.json")
    reviewed_schema = _load(SCHEMA_ROOT / "reviewed_navigation_bundle.schema.json")
    Draft202012Validator.check_schema(policy_schema)
    Draft202012Validator.check_schema(run_schema)
    Draft202012Validator.check_schema(reviewed_schema)

    Draft202012Validator(policy_schema).validate(_load(POLICY_PATH))
    for filename in ("machine_only_run.json", "reviewed_navigation_run.json"):
        Draft202012Validator(run_schema).validate(_load(FIXTURE_ROOT / filename))
    Draft202012Validator(reviewed_schema).validate(
        _load(FIXTURE_ROOT / "reviewed_navigation_bundle.json")
    )


def test_policy_contains_exactly_the_accepted_and_deferred_boundaries() -> None:
    policy = _load(POLICY_PATH)
    assert [rule["rule_id"] for rule in policy["section_rules"]] == [
        "R1",
        "R2",
        "R2a",
        "R2b",
        "R3",
        "R4",
        "R5",
    ]
    assert policy["table_alias_rule"]["rule_id"] == "R6"
    assert policy["table_caption_fallback_rule"]["rule_id"] == "R6a"
    assert policy["section_rules"][0]["allowed_callers"] == [
        "machine_reference",
        "effective_navigation",
    ]
    assert all(
        rule["allowed_callers"] == ["effective_navigation"] for rule in policy["section_rules"][1:]
    )
    assert "figure_linking" in policy["deferred_capabilities"]
    assert "footer_derived_printed_page_aliases" in policy["deferred_capabilities"]


def test_run_fixtures_cover_both_review_modes_and_have_closed_source_sets() -> None:
    runs = [
        _load(FIXTURE_ROOT / "machine_only_run.json"),
        _load(FIXTURE_ROOT / "reviewed_navigation_run.json"),
    ]
    assert [run["reviewed_navigation"] is None for run in runs] == [True, False]
    for run in runs:
        source_ids = [document["source_id"] for document in run["documents"]]
        assert source_ids == run["selected_source_ids"]
        assert len(source_ids) == len(set(source_ids))
        assert all(
            document["source_document"]["candidate_id"].startswith("docv1-")
            and document["structured_document"]["candidate_id"].startswith("exv1-")
            for document in run["documents"]
        )


def test_reviewed_run_and_bundle_have_identical_coverage_and_payload_refs() -> None:
    run = _load(FIXTURE_ROOT / "reviewed_navigation_run.json")
    bundle = _load(FIXTURE_ROOT / "reviewed_navigation_bundle.json")
    reviewed = run["reviewed_navigation"]
    assert reviewed["bundle_id"] == bundle["bundle_id"]
    assert reviewed["source_ids"] == bundle["source_ids"]
    assert set(reviewed["source_ids"]).issubset(run["selected_source_ids"])
    assert reviewed["review_decisions_ref"] == bundle["identity_preimage"]["review_decisions_ref"]
    assert reviewed["semantic_view_ref"] == bundle["identity_preimage"]["semantic_view_ref"]
    assert reviewed["text_entries_ref"] == bundle["payloads"]["text_entries_ref"]
    assert reviewed["disposition_ref"] == bundle["payloads"]["dispositions_ref"]
    assert reviewed["parent_relations_ref"] == bundle["payloads"]["parent_relations_ref"]
    assert reviewed["inventory_ref"] == bundle["inventory_ref"]
    assert reviewed["completion_ref"] == bundle["completion_ref"]


def test_all_gate_b_fixtures_are_portable_and_paths_are_contained() -> None:
    fixtures = [_load(path) for path in sorted(FIXTURE_ROOT.glob("*.json"))]
    fixture_text = [text.lower() for fixture in fixtures for text in _strings(fixture)]
    for forbidden in FORBIDDEN_PORTABILITY_TEXT:
        assert all(forbidden not in text for text in fixture_text)

    for fixture in fixtures:
        for path_text in _artifact_paths(fixture):
            path = Path(path_text)
            assert not path.is_absolute()
            assert ".." not in path.parts


def test_resolution_fixture_names_every_required_gate_c_control() -> None:
    cases = _load(FIXTURE_ROOT / "resolution_cases.json")["cases"]
    assert {case["case_id"] for case in cases} == {
        "unique_exact_heading",
        "ambiguous_exact_heading",
        "destination_page_conflict",
        "explicit_parent_conflict",
        "fallback_collision",
        "excluded_navigation_entry",
        "derived_table_alias",
        "unresolved_figure",
        "shuffled_discovery_order",
        "changed_policy_identity",
        "changed_review_identity",
        "corrupt_input_seal",
    }
