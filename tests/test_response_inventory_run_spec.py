"""Source-free tests for the Task 05C portable pilot specification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from pydantic import ValidationError

from er_commons.response_inventory.code_inventory import owned_code_digest
from er_commons.response_inventory.run_spec import (
    ResponseInventoryRunSpec,
    load_response_inventory_run_spec,
    verify_repository_bindings,
)

REPO_ROOT = Path(__file__).parents[1]
CONFIG_PATH = REPO_ROOT / "configs/brisbane_baylands_2025_feir_task05c_pilot_v1.json"
SCHEMA_PATH = REPO_ROOT / "benchmarks/er_bench/schemas/response_inventory/v1/run_spec.schema.json"
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


def test_pilot_config_binds_accepted_completion_and_small_repository_inputs() -> None:
    spec, _ = load_response_inventory_run_spec(CONFIG_PATH)
    task05a = next(item for item in spec.accepted_inputs if item.role == "task05a_completion")
    assert task05a.sha256 == "649ec0664a6f7aebdfc6b7da011161d696385ed246bc726becaf89c416f652dd"
    assert task05a.byte_size == 2119
    verify_repository_bindings(spec, REPO_ROOT)
    assert spec.producer_code_sha256 == owned_code_digest(REPO_ROOT)


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
