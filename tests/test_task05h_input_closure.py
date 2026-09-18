"""Synthetic file-boundary regressions for accepted input closure and associations."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from er_commons.artifact_io import json_bytes, jsonl_bytes
from er_commons.response_inventory import release_inputs
from er_commons.response_inventory.contract import (
    _materialize_fixture_records,
    semantic_bundle_digest,
    validate_record_bundle,
)


def _write(path: Path, value: Any, *, rows: bool = False) -> dict[str, Any]:
    """Write only temporary synthetic fixtures and return their exact seal."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = jsonl_bytes(value) if rows else json_bytes(value)
    path.write_bytes(payload)
    return {
        "path": path.name,
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def test_checkpoint_rejects_unexpected_owned_file(tmp_path: Path) -> None:
    """A valid completion digest cannot bless an extra unlisted payload."""
    seal = _write(tmp_path / "payload.json", {"value": 1})
    completion = _write(tmp_path / "completion.json", {"status": "complete", "inventory": [seal]})
    release_inputs._checkpoint(tmp_path, completion)
    _write(tmp_path / "extra.json", {})
    with pytest.raises(ValueError, match="managed closure"):
        release_inputs._checkpoint(tmp_path, completion)


def _associations() -> tuple[dict[str, Any], dict[str, Any]]:
    """Provide distinct frozen candidate/comparison/finalization checkpoint bindings."""
    acceptance = {"finalization_checkpoint_id": "final", "finalization_root": "final"}
    handoff = {
        "candidate_id": "candidate",
        "semantic_digest": "semantic",
        "dependencies": [],
        "candidate_checkpoint_id": "candidate-check",
        "candidate_root": "candidate",
        "comparison_checkpoint_id": "comparison-check",
        "comparison_root": "comparison",
    }
    controls = {
        "acceptance_pointer": acceptance,
        "task05h_handoff": handoff,
        "candidate_root_completion": {"checkpoint_id": "candidate-check"},
        "comparison_root_completion": {"checkpoint_id": "comparison-check"},
        "finalization_completion": {"checkpoint_id": "final"},
    }
    binding = {
        "task05g_acceptance": deepcopy(acceptance),
        "task05g_candidate_id": "candidate",
        "task05g_semantic_digest": "semantic",
        "dependencies": [],
        "seals": {
            "candidate_root_completion": {"path": "candidate/completion.json"},
            "comparison_root_completion": {"path": "comparison/completion.json"},
            "finalization_completion": {"path": "final/completion.json"},
        },
    }
    return binding, controls


@pytest.mark.parametrize("kind", ["candidate", "comparison", "finalization"])
def test_mixed_checkpoint_association_rejected(kind: str) -> None:
    """Individually valid-shaped controls cannot select another checkpoint."""
    binding, controls = _associations()
    release_inputs._associations(binding, controls)
    key = "finalization_completion" if kind == "finalization" else f"{kind}_root_completion"
    controls[key]["checkpoint_id"] = "another-checkpoint"
    with pytest.raises(ValueError, match="association"):
        release_inputs._associations(binding, controls)


def _source_graph_fixture(
    tmp_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """Create small null-digest accepted payloads around the maintained source fixture."""
    repo = Path(__file__).parents[1]
    raw = json.loads(
        (
            repo / "benchmarks/er_bench/fixtures/response_inventory/v1/valid_graph_cardinality.json"
        ).read_text()
    )
    source = _materialize_fixture_records(raw["records"])
    activity = {"record_type": "activity", "activity_id": "graph", "schema_version": "fixture"}
    binding: dict[str, Any] = {
        "accepted_component_semantic_digests": {
            "task05d": semantic_bundle_digest(source),
            "task05e": semantic_bundle_digest([activity]),
        }
    }
    dependencies = {}
    for stage in ("05d", "05e"):
        owner = tmp_path / stage
        rows = (
            {"inventory/source_records.jsonl": source}
            if stage == "05d"
            else {
                "graph/review_edges.jsonl": [],
                "diagnostics/individual_diagnostics.jsonl": [],
                "review_views/review_views.jsonl": [],
            }
        )
        files = []
        for name, values in rows.items():
            seal = _write(owner / name, values, rows=True)
            files.append({**seal, "path": name, "sha256": None})
        if stage == "05e":
            seal = _write(owner / "records/activity.json", activity)
            files.append({**seal, "path": "records/activity.json", "sha256": None})
        _write(
            owner / "records/managed_file_inventory.json", {"inventory_id": stage, "files": files}
        )
        _write(
            owner / "records/stage_completion.json",
            {"completion_id": stage, "inventory_id": stage, "stage": stage},
        )
        _write(
            owner.with_suffix(".acceptance.json"),
            {
                "completion_id": stage,
                "semantic_digest": binding["accepted_component_semantic_digests"][f"task{stage}"],
            },
        )
        dependencies[f"task{stage}_completion"] = {
            "identity": stage,
            "path": f"{stage}/records/stage_completion.json",
        }
    return binding, dependencies, source


def test_null_digest_source_tamper_fails_raw_text_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Same-length text changes must reach the real raw-text/anchor validator."""
    binding, dependencies, source = _source_graph_fixture(tmp_path)

    def validate_source(rows: list[dict[str, Any]], schema: dict[str, Any]) -> str:
        """Validate the real fixture source; synthetic wrapper controls are test scaffolding."""
        return validate_record_bundle(rows[: len(source)], schema)

    monkeypatch.setattr(release_inputs, "validate_record_bundle", validate_source)
    release_inputs._source_graph(binding, tmp_path, dependencies)
    page = next(row for row in source if row["record_type"] == "page")
    page["raw_text"] = "X" + page["raw_text"][1:]
    path = tmp_path / "05d/inventory/source_records.jsonl"
    old_size = path.stat().st_size
    _write(path, source, rows=True)
    assert path.stat().st_size == old_size
    with pytest.raises(ValueError, match="raw.text|raw text|digest"):
        release_inputs._source_graph(binding, tmp_path, dependencies)


def test_null_digest_source_semantic_drift_stops_before_new_sealing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Independently exercise the fixed accepted semantic digest after schema validation."""
    binding, dependencies, source = _source_graph_fixture(tmp_path)
    monkeypatch.setattr(release_inputs, "validate_record_bundle", lambda rows, schema: "valid")
    release_inputs._source_graph(binding, tmp_path, dependencies)
    page = next(row for row in source if row["record_type"] == "page")
    page["raw_text"] = "X" + page["raw_text"][1:]
    page["raw_text_sha256"] = hashlib.sha256(page["raw_text"].encode()).hexdigest()
    path = tmp_path / "05d/inventory/source_records.jsonl"
    old_size = path.stat().st_size
    _write(path, source, rows=True)
    assert path.stat().st_size == old_size
    with pytest.raises(ValueError, match="05d accepted semantic digest"):
        release_inputs._source_graph(binding, tmp_path, dependencies)
