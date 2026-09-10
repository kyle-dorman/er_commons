"""Renamed commands require explicit selections and preserve historical identities."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.navigation_overlay.gate_c_validation import (
    AcceptedNavigationControl,
    validate_gate_c_navigation_population,
)
from er_commons.navigation_overlay.validation_spec import RelinkValidationSpec

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "recipe",
    sorted((ROOT / "benchmarks/er_bench/fixtures/document_publication").glob("*/*identity.json")),
)
def test_original_recipe_validates_after_recorded_code_retirement(recipe: Path) -> None:
    """An original recipe is historical evidence even when its old writer is absent."""
    record = json.loads(recipe.read_text())
    if "preimage" not in record:
        pytest.skip("fixture is not a production recipe")
    identity = validate_production_identity(record)
    assert identity.value == record["extraction_id"]


@pytest.mark.parametrize(
    "name",
    ["inspect_conversion_scaling", "audit_document_linking", "validate_document_relink_run"],
)
def test_diagnostic_requires_selection_before_any_execution(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty invocation cannot select accepted roots, write reports, or audit bytes."""
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(sys, "argv", [name])
    with pytest.raises(SystemExit) as failure:
        module.main()
    assert failure.value.code == 2


def test_regression_population_is_explicit_and_not_fixed_to_the_historical_corpus() -> None:
    """One synthetic source/control population exercises the maintained validator."""
    report = validate_gate_c_navigation_population(
        [{"entry_id": "entry", "control_class": "synthetic", "outcome": "unresolved"}],
        baseline_targets={},
        controls={"synthetic": AcceptedNavigationControl(1, 0)},
        primary_rule_counts={},
        expected_baseline_count=0,
    )
    assert report["population_count"] == 1
    assert report["resolved_count"] == 0


def _validation_spec() -> dict[str, Any]:
    """One fully declared synthetic regression request."""
    return {
        "schema_version": "er_commons.document_relink_validation.v1",
        "expected_source_count": 1,
        "reviewed_source_ids": ["synthetic"],
        "context_entries": [],
        "parent_relations": [],
        "navigation_controls": {"synthetic": {"population": 1, "resolved": 0}},
        "primary_rule_counts": {},
        "expected_baseline_count": 0,
    }


def test_validation_spec_rejects_implicit_or_inconsistent_populations() -> None:
    """Current requests fail before opening evidence when selections are incomplete."""
    request = _validation_spec()
    assert RelinkValidationSpec.model_validate(request).expected_source_count == 1
    del request["context_entries"]
    with pytest.raises(ValueError, match="context_entries"):
        RelinkValidationSpec.model_validate(request)
    request = _validation_spec()
    request["primary_rule_counts"] = {"R1": 1}
    with pytest.raises(ValueError, match="primary rule counts"):
        RelinkValidationSpec.model_validate(request)


def test_diagnostic_ledger_uses_only_declared_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An actual renamed metadata invocation does not select a historical namespace."""
    spec = importlib.util.spec_from_file_location(
        "inspect_conversion_scaling", ROOT / "scripts/inspect_conversion_scaling.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = tmp_path / "report"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "inspect_conversion_scaling",
            "--data-root",
            str(tmp_path),
            "--run-relative-root",
            "synthetic/run",
            "--source-id",
            "synthetic",
            "--output-root",
            str(output),
            "--ledger",
        ],
    )
    module.main()
    record = json.loads((output / "task03h_gate1_scaling_ledger.json").read_text())
    assert record["execution_boundary"]["large_payload_bytes_read"] is False
    assert not (tmp_path / "pipelines").exists()
