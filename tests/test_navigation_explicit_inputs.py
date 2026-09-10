"""Future navigation invocations never discover an implicit accepted corpus."""

from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

import pytest
from navigation_input_fixtures import MATERIALIZATION, PREPARATION, RECONCILIATION

from er_commons.navigation_overlay import cli


@pytest.mark.parametrize(
    ("stage", "request_type", "bindings", "publisher"),
    [
        ("prepare", cli.GateAPreparationRequest, PREPARATION, "prepare_and_publish_gate_a"),
        (
            "materialize",
            cli.GateBMaterializationRequest,
            MATERIALIZATION,
            "prepare_and_publish_gate_b",
        ),
        ("reconcile", cli.GateCReconciliationRequest, RECONCILIATION, "prepare_and_publish_gate_c"),
    ],
)
def test_explicit_spec_isolated_per_invocation(
    tmp_path, monkeypatch, stage, request_type, bindings, publisher
):
    """Two unrelated input specs retain separate roots and accepted bindings."""
    requests = []

    def publish(request):
        requests.append(request)
        return request.output_parent

    monkeypatch.setattr(cli, publisher, publish)
    for name in ("first", "second"):
        directory = tmp_path / name
        directory.mkdir()
        raw = {
            field.name: field.name
            for field in fields(request_type)
            if field.name not in {"bindings", "output_parent"}
        }
        raw["bindings"] = bindings.model_dump()
        spec = directory / "input.json"
        spec.write_text(json.dumps(raw))
        assert (
            cli.main(stage, ["--input-spec", str(spec), "--output-root", str(directory / "output")])
            == 0
        )
    assert requests[0].extraction_root == tmp_path / "first/extraction_root"
    assert requests[1].extraction_root == tmp_path / "second/extraction_root"
    assert requests[0].bindings == requests[1].bindings == bindings


def test_input_spec_has_no_default_paths(tmp_path: Path) -> None:
    spec = tmp_path / "empty.json"
    spec.write_text("{}")
    with pytest.raises(ValueError, match="input spec fields differ"):
        cli.main("prepare", ["--input-spec", str(spec), "--output-root", str(tmp_path / "out")])


def test_new_reproduction_schema_preserves_the_historical_command() -> None:
    """New writer provenance gets a new schema; old sealed provenance stays valid."""
    from jsonschema import Draft202012Validator

    root = Path(__file__).parents[1] / "benchmarks/er_bench/schemas/navigation_overlay"
    old = json.loads((root / "v1/gate_a_specification.schema.json").read_text())
    new = json.loads((root / "v2/gate_a_specification.schema.json").read_text())
    old_command = old["properties"]["reproduction"]["properties"]["command"]
    new_command = new["properties"]["reproduction"]["properties"]["command"]
    Draft202012Validator(old_command).validate(
        "uv run python scripts/prepare_task04c_gate_a.py --repo-root ."
    )
    Draft202012Validator(new_command).validate(
        "uv run python scripts/prepare_reviewed_navigation.py "
        "--input-spec INPUT_SPEC --output-root OUTPUT_ROOT"
    )
    assert list(Draft202012Validator(old_command).iter_errors(new_command["const"]))
