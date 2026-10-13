"""Frozen pre-cleanup native requests and persisted results, using invented inputs."""

import json
from pathlib import Path
from typing import Any

import pytest
from test_grounding_abstention_inspect import classified
from test_grounding_inspect import completion, sample
from test_grounding_staged_inspect import responses
from test_judge_packet_requests import settings

from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_abstention_inspect import evaluate_abstention_samples
from er_commons.grounding_staged_inspect import evaluate_staged_samples

GOLDEN = Path(__file__).parent / "fixtures" / "task09e_phase0"
SCENARIOS = ("gated_success", "disagreement", "malformed", "unverified", "abstention")


def _without_elapsed(value: Any) -> Any:
    """Normalize only wall-clock measurements; preserve every other persisted field."""
    if isinstance(value, dict):
        return {
            key: _without_elapsed(item) for key, item in value.items() if key != "elapsed_seconds"
        }
    if isinstance(value, list):
        return [_without_elapsed(item) for item in value]
    return value


def capture(tmp_path: Path, scenario: str) -> dict[str, Any]:
    """Run the legacy Inspect entrypoint and collect its full deterministic artifacts."""
    fixtures = responses(disagree=scenario == "disagreement")
    fixtures["fixture"]["abstention"] = classified("substantive")
    if scenario == "malformed":
        fixtures["fixture"]["P2"] = completion({"bad": "schema"})
    options = dict(
        settings=settings(),
        artifact_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        count_tokens=None if scenario == "unverified" else lambda request: 100,
        counter_model_digest="fixture-digest",
        fixture_responses=fixtures,
    )
    if scenario == "abstention":
        logs = evaluate_abstention_samples([sample()], **options)
    else:
        logs = evaluate_staged_samples(
            [sample()], check_abstention=scenario == "gated_success", **options
        )
    assert logs[0].status == "success"
    artifacts = {}
    for path in sorted((tmp_path / "raw").rglob("*.json")):
        value = json.loads(path.read_text())
        if path.name == "completion.json":
            record_name = (
                "abstention_record.json" if scenario == "abstention" else "grounding_record.json"
            )
            record = json.loads(path.with_name(record_name).read_text())
            assert value == {"record_sha256": stable_json_sha256(record)}
        else:
            artifacts[str(path.relative_to(tmp_path / "raw"))] = _without_elapsed(value)
    return artifacts


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_legacy_request_and_result_parity(tmp_path: Path, scenario: str) -> None:
    """Preserve frozen prompts, schemas, request bytes, errors and final result structure."""
    assert capture(tmp_path, scenario) == json.loads((GOLDEN / f"{scenario}.json").read_text())
