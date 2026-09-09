"""Source-free tests for the Task 05C portable pilot specification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from pydantic import ValidationError

from er_commons.response_inventory.run_spec import (
    ResponseInventoryRunSpec,
    ResponseInventoryRunSpecV2,
    load_response_inventory_run_spec,
    verify_repository_bindings,
)

REPO_ROOT = Path(__file__).parents[1]
CONFIG_PATH = REPO_ROOT / "configs/brisbane_baylands_2025_feir_task05c_pilot_v1.json"
SCHEMA_PATH = REPO_ROOT / "benchmarks/er_bench/schemas/response_inventory/v1/run_spec.schema.json"
COMPLETE_CONFIG_PATH = REPO_ROOT / "configs/brisbane_baylands_2025_feir_task05d_complete_v2.json"
COMPLETE_SCHEMA_PATH = (
    REPO_ROOT / "benchmarks/er_bench/schemas/response_inventory/v2/run_spec.schema.json"
)
EXPECTED_RANGES = (
    (1, 5),
    (23, 25),
    (31, 44),
    (82, 92),
    (154, 158),
    (171, 175),
    (179, 185),
    (368, 372),
    (551, 555),
    (575, 577),
    (668, 671),
    (684, 691),
    (720, 726),
    (738, 744),
)


def _config_payload() -> dict[str, object]:
    return cast(dict[str, object], json.loads(CONFIG_PATH.read_text()))


def _complete_config_payload() -> dict[str, object]:
    return cast(dict[str, object], json.loads(COMPLETE_CONFIG_PATH.read_text()))


def test_checked_in_pilot_config_is_schema_valid_and_exact() -> None:
    payload = _config_payload()
    schema = json.loads(SCHEMA_PATH.read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)

    spec, config_sha256 = load_response_inventory_run_spec(CONFIG_PATH)
    assert len(config_sha256) == 64
    assert tuple((item.first_page, item.last_page) for item in spec.page_ranges) == EXPECTED_RANGES
    assert len(spec.page_ranges) == 14
    assert spec.declared_page_count == 89
    assert spec.source.source_id == "feir_volume_4"
    assert spec.cross_gap_continuations_allowed is False


def test_pilot_config_preserves_accepted_historical_bindings() -> None:
    spec, config_sha256 = load_response_inventory_run_spec(CONFIG_PATH)
    task05a = next(item for item in spec.accepted_inputs if item.role == "task05a_completion")
    assert task05a.sha256 == "649ec0664a6f7aebdfc6b7da011161d696385ed246bc726becaf89c416f652dd"
    assert task05a.byte_size == 2119
    assert config_sha256 == "96c964efd5b18874b12b273aa214f79138331d5da90d6421e13642b3edf21cae"
    assert spec.producer_code_sha256 == (
        "2d4a99ece35fa4efe29ab64cf4f6a18f28ad425d99f5ab78b36528dea168dce1"
    )
    run_spec_binding = next(
        item for item in spec.repository_bindings if item.role == "producer_run_spec_code"
    )
    assert run_spec_binding.sha256 == (
        "d312d0b2fd6b029d5896af87ba1f9e10de48a069d7bb9b2e35d9505404bea25e"
    )


def test_range_accounting_rejects_overlap_and_wrong_count() -> None:
    payload = _config_payload()
    ranges = payload["page_ranges"]
    assert isinstance(ranges, list)
    second = ranges[1]
    assert isinstance(second, dict)
    second.update({"range_id": "p0005-p0025", "first_page": 5})
    payload["declared_page_count"] = 90
    with pytest.raises(ValidationError, match="ordered and non-overlapping"):
        ResponseInventoryRunSpec.model_validate(payload)


def test_same_size_range_substitution_is_not_authorized() -> None:
    payload = _config_payload()
    ranges = payload["page_ranges"]
    assert isinstance(ranges, list)
    first = ranges[0]
    assert isinstance(first, dict)
    first.update({"range_id": "p0006-p0010", "first_page": 6, "last_page": 10})
    with pytest.raises(ValidationError, match="exact authorized pilot ranges"):
        ResponseInventoryRunSpec.model_validate(payload)


def test_run_spec_forbids_scope_expansion_and_in_run_repair() -> None:
    payload = _config_payload()
    stop_behavior = payload["stop_behavior"]
    assert isinstance(stop_behavior, dict)
    stop_behavior["allow_additional_pages"] = True
    with pytest.raises(ValidationError, match="Input should be False"):
        ResponseInventoryRunSpec.model_validate(payload)


def test_repository_digest_mismatch_fails_before_source_access(tmp_path: Path) -> None:
    payload = _config_payload()
    bindings = payload["repository_bindings"]
    assert isinstance(bindings, list)
    binding = bindings[0]
    assert isinstance(binding, dict)
    binding["path"] = "changed.json"
    spec = ResponseInventoryRunSpec.model_validate(payload)
    (tmp_path / "changed.json").write_text("{}\n")
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_repository_bindings(spec, tmp_path)


def test_checked_in_complete_config_is_schema_valid_and_exact() -> None:
    payload = _complete_config_payload()
    schema = json.loads(COMPLETE_SCHEMA_PATH.read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)

    spec, config_sha256 = load_response_inventory_run_spec(COMPLETE_CONFIG_PATH)
    assert isinstance(spec, ResponseInventoryRunSpecV2)
    assert len(config_sha256) == 64
    assert tuple((item.first_page, item.last_page) for item in spec.page_ranges) == ((1, 744),)
    assert spec.declared_page_count == 744
    assert spec.output_policy.working_namespace_template == (
        "working/05d/revisionv1-{activity_hash}"
    )
    assert spec.cache_policy.all_declared_pages is True
    assert spec.stop_behavior.allowed_terminal_warning_codes == ("source_response_heading_absent",)


def test_complete_config_binds_exact_accepted_pilot_and_baseline_evidence() -> None:
    spec, _ = load_response_inventory_run_spec(COMPLETE_CONFIG_PATH)
    assert isinstance(spec, ResponseInventoryRunSpecV2)
    assert spec.accepted_task05c.completion_id == (
        "completionv1-5853fa56753aa6e032687cdd727c72bac1c8cec0abf34cc6d2fac1e9b358e571"
    )
    assert spec.accepted_task05c.semantic_digest == (
        "ac874b8671ea40a07d76602d35c404dc641bb2fd7338178eb838b5ff2af145d3"
    )
    evidence = {item.role: item for item in spec.accepted_inputs}
    assert evidence["task05c_completion"].byte_size == 940
    assert evidence["task05c_completion"].sha256 == (
        "b60e2f3454d8d62f1b9322e3ee3c5479f766c6a408f23cb01e08591f26cc41fb"
    )
    assert evidence["task05c_source_records"].sha256 == (
        "724fa35e0eb99adcee1764905220ffeb14a306823c8bb799adad6447061a43da"
    )
    assert evidence["task05a_structural_profile"].sha256 == (
        "b4cafb2c2964772781c1f284a8e4c919a14b530bb6c424a4e581dd66fc49e9e2"
    )


def test_complete_config_rejects_scope_substitution_and_pilot_policy() -> None:
    payload = _complete_config_payload()
    ranges = payload["page_ranges"]
    assert isinstance(ranges, list)
    only_range = ranges[0]
    assert isinstance(only_range, dict)
    only_range.update({"range_id": "p0001-p0743", "last_page": 743})
    with pytest.raises(ValidationError, match="exact 1-744 range"):
        ResponseInventoryRunSpecV2.model_validate(payload)

    payload = _complete_config_payload()
    stop_behavior = payload["stop_behavior"]
    assert isinstance(stop_behavior, dict)
    stop_behavior["allowed_terminal_warning_codes"] = []
    with pytest.raises(ValidationError, match="source_response_heading_absent"):
        ResponseInventoryRunSpecV2.model_validate(payload)

    payload = _complete_config_payload()
    stop_behavior = payload["stop_behavior"]
    assert isinstance(stop_behavior, dict)
    stop_behavior["allowed_terminal_warning_codes"] = ["unit_boundary_ambiguous"]
    with pytest.raises(ValidationError, match="source_response_heading_absent"):
        ResponseInventoryRunSpecV2.model_validate(payload)


def test_complete_config_requires_every_evidence_role_exactly_once() -> None:
    payload = _complete_config_payload()
    accepted_inputs = payload["accepted_inputs"]
    assert isinstance(accepted_inputs, list)
    accepted_inputs[-1] = accepted_inputs[-2]
    with pytest.raises(ValidationError, match="accepted input roles must be exactly"):
        ResponseInventoryRunSpecV2.model_validate(payload)
