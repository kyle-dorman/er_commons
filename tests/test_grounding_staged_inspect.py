"""Invented staged Inspect calls exercise exact preflight without any model execution."""

import copy
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from test_grounding_inspect import completion, sample
from test_judge_packet_requests import settings

from er_commons import grounding_stage_runtime as runtime
from er_commons import grounding_staged_inspect as adapter


def evaluate(tmp_path: Path, fixtures: dict | None, **kwargs: Any) -> dict:
    """Return the durable Inspect score record from one invented saved answer."""
    options = {"count_tokens": lambda request: 100, "counter_model_digest": "fixture-digest"}
    options.update(kwargs)
    logs = adapter.evaluate_staged_samples(
        [sample()],
        settings=settings(),
        artifact_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        fixture_responses=fixtures,
        **options,
    )
    assert logs[0].status == "success"
    return logs[0].samples[0].scores["staged_grounding_scorer"].metadata["grounding_record"]


@pytest.mark.parametrize(
    "count,status", [(None, "context_unverified"), (50000, "context_overflow")]
)
def test_unknown_or_overflow_count_blocks_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, count: int | None, status: str
) -> None:
    """Even the read-only runtime check cannot precede an exact valid count."""

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("No transport allowed")

    monkeypatch.setattr(runtime, "check_live_model", forbidden)
    record = evaluate(tmp_path, None, count_tokens=None if count is None else lambda req: count)
    assert record["status"] == status and record["attempts"] == 0
    assert record["score"] is None and record["conclusion_skipped"]
    assert not list((tmp_path / "raw").rglob("attempt_*"))


def test_semantic_failure_skips_conclusion(tmp_path: Path) -> None:
    """Malformed point evidence remains diagnostic and cannot become false in stage two."""
    record = evaluate(tmp_path, {"fixture": {"P2": completion({"bad": "schema"})}})
    assert record["status"] == "schema_error" and record["attempts"] == 1
    assert record["score"] is None and record["conclusion_skipped"]
    assert [s["key"] for s in record["stages"]] == ["P2"]


def test_fresh_only_and_fixture_scope(tmp_path: Path) -> None:
    """Prior run directories cannot be overwritten or silently reused."""
    (tmp_path / "raw").mkdir()
    with pytest.raises(ValueError, match="fresh"):
        evaluate(tmp_path, None)
    s = sample().model_copy(update={"scope": "development"})
    with pytest.raises(ValueError, match="invented_fixture"):
        adapter.evaluate_staged_samples(
            [s],
            settings=settings(),
            artifact_dir=tmp_path / "fresh",
            log_dir=tmp_path / "logs",
            fixture_responses={"fixture": {}},
        )


def test_stage_input_token_mismatch_blocks_result(tmp_path: Path) -> None:
    """A completed native envelope must agree with the exact stage request count."""
    output = completion({})
    output["prompt_eval_count"] = 101
    record = evaluate(tmp_path, {"fixture": {"P2": output}})
    assert record["status"] == "context_counter_mismatch" and record["score"] is None
    assert record["attempts"] == 1 and record["conclusion_skipped"]


def test_missing_fixture_never_falls_back_to_native(tmp_path: Path) -> None:
    """A missing per-stage fixture produces a saved failure, never a live call."""
    record = evaluate(tmp_path, {"fixture": {}})
    assert record["status"] == "input_error" and record["conclusion_skipped"]


def responses(*, disagree: bool = False) -> dict:
    """Invent judgments over literal fixture evidence, without any benchmark labels."""
    return {
        "fixture": {
            "P2": completion(
                {
                    "point_id": "P2",
                    "supported": True,
                    "unsupported_assertions": [],
                    "locators": [{"citation_id": "S1", "excerpt": "Exact source."}],
                    "explanation": "Source supports this invented point.",
                }
            ),
            "conclusion": completion(
                {
                    "conclusion_supported": not disagree,
                    "clean_abstention": False,
                    "point_reviews": [
                        {
                            "point_id": "P2",
                            "supported": not disagree,
                            "explanation": "Review the actual source.",
                        }
                    ],
                    "locators": [{"citation_id": "S1", "excerpt": "Exact source."}],
                    "explanation": "Conclusion reviewed.",
                }
            ),
        }
    }


@pytest.mark.parametrize(
    "disagree,status,score", [(False, "scored", 2), (True, "unresolved_disagreement", None)]
)
def test_serial_calls_prediction_binding_and_unresolved(
    tmp_path: Path, disagree: bool, status: str, score: int | None
) -> None:
    """Conclusion contains actual validated stage predictions; disagreement excludes score zero."""
    requests = []

    def counter(request: dict) -> int:
        requests.append(copy.deepcopy(request))
        return 100

    record = evaluate(tmp_path, responses(disagree=disagree), count_tokens=counter)
    assert record["status"] == status and record["score"] == score
    assert len(requests) == 2 and "SECRET" not in json.dumps(requests)
    payload = json.loads(requests[-1]["messages"][1]["content"])
    assert payload["point_assessments"] == [record["stages"][0]["result"]]
    metrics = adapter.summarize_staged_records([record])
    assert metrics["retries"] == 0 and metrics["stage_calls"] == 2
    assert metrics["point_calls"] == metrics["conclusion_calls"] == 1
    assert metrics["native_input_tokens"] == 200 and metrics["native_output_tokens"] == 80
    assert metrics["failed"] == 0
    if disagree:
        assert metrics["synthetic_numeric_comparable"] == 0
        assert metrics["unresolved_disagreement"] == 1
    assert all(s["elapsed_seconds"] >= 0 for s in record["stages"])


@pytest.mark.parametrize("failures,attempts,status", [(1, 3, "scored"), (2, 2, "runtime_error")])
def test_single_transient_retry_per_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failures: int, attempts: int, status: str
) -> None:
    """Recount before every retry and preserve all attempted calls in Inspect records."""
    calls = 0
    counts = 0
    monkeypatch.setattr(runtime, "check_live_model", lambda *args: None)

    async def transport(request: dict, directory: Path, captured: dict, **kwargs: Any) -> None:
        nonlocal calls
        calls += 1
        if calls <= failures:
            raise httpx.ReadTimeout("Invented transient failure")
        key = "P2" if calls == failures + 1 else "conclusion"
        output = responses()["fixture"][key]
        captured.update(output=output, **runtime.validate_completion(output, settings()))

    def counter(request: dict) -> int:
        nonlocal counts
        counts += 1
        return 100

    monkeypatch.setattr(runtime, "call_native_judge", transport)
    record = evaluate(tmp_path, None, count_tokens=counter)
    assert record["status"] == status and record["attempts"] == attempts
    assert calls == counts == attempts
    assert adapter.summarize_staged_records([record])["retries"] == 1


def test_disproven_counter_halts_remaining_samples(tmp_path: Path) -> None:
    """One observed counter mismatch prevents further calls across the whole Inspect run."""
    fixtures = responses()
    fixtures["fixture"]["P2"]["prompt_eval_count"] = 101
    fixtures["later"] = responses()["fixture"]
    logs = adapter.evaluate_staged_samples(
        [sample(), sample("later")],
        settings=settings(),
        artifact_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        count_tokens=lambda req: 100,
        counter_model_digest="fixture-digest",
        fixture_responses=fixtures,
    )
    records = [
        s.scores["staged_grounding_scorer"].metadata["grounding_record"] for s in logs[0].samples
    ]
    assert sum(r["attempts"] for r in records) == 1
    assert all(r["status"] == "context_counter_mismatch" for r in records)


def test_zero_point_clean_abstention_still_calls_conclusion(tmp_path: Path) -> None:
    """No point predictions is a real empty list, never an implicit supported conclusion."""
    from er_commons.artifact_io import stable_json_sha256

    s = sample()
    payload = s.packet["payload"]
    payload["answer"]["qualifications"] = []
    payload["answer"]["status"] = "abstained"
    payload["answer"]["conclusion"]["text"] = "I cannot determine this from the evidence."
    payload["answer"]["conclusion"]["citation_ids"] = []
    payload["evidence"] = []
    s.packet["diagnostics"]["payload_sha256"] = stable_json_sha256(payload)
    output = completion(
        {
            "conclusion_supported": None,
            "clean_abstention": True,
            "point_reviews": [],
            "locators": [],
            "explanation": "No assertion to assess.",
        }
    )
    logs = adapter.evaluate_staged_samples(
        [s],
        settings=settings(),
        artifact_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        count_tokens=lambda req: 100,
        counter_model_digest="fixture-digest",
        fixture_responses={"fixture": {"conclusion": output}},
    )
    record = logs[0].samples[0].scores["staged_grounding_scorer"].metadata["grounding_record"]
    assert record["status"] == "not_applicable" and record["score"] is None
    assert record["attempts"] == 1 and record["stage_expected"] == 1
    assert record["stages"][0]["kind"] == "conclusion"


def test_failed_point_does_not_hide_later_diagnostics(tmp_path: Path) -> None:
    """A semantic point failure allows remaining point diagnostics but blocks conclusion."""
    from er_commons.artifact_io import stable_json_sha256

    s = sample()
    payload = s.packet["payload"]
    additional = copy.deepcopy(payload["answer"]["qualifications"][0])
    additional["point_id"] = "P3"
    payload["answer"]["qualifications"].append(additional)
    s.packet["diagnostics"]["payload_sha256"] = stable_json_sha256(payload)
    second = copy.deepcopy(responses()["fixture"]["P2"])
    value = json.loads(second["message"]["content"])
    value["point_id"] = "P3"
    second["message"]["content"] = json.dumps(value)
    logs = adapter.evaluate_staged_samples(
        [s],
        settings=settings(),
        artifact_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        count_tokens=lambda req: 100,
        counter_model_digest="fixture-digest",
        fixture_responses={"fixture": {"P2": completion({}), "P3": second}},
    )
    record = logs[0].samples[0].scores["staged_grounding_scorer"].metadata["grounding_record"]
    assert record["attempts"] == 2 and record["score"] is None
    assert [s["status"] for s in record["stages"]] == ["schema_error", "validated"]
    assert record["stage_expected"] == 3 and record["conclusion_skipped"]


@pytest.mark.parametrize("valid", [True, False])
def test_points_only_never_runs_other_stages(tmp_path: Path, valid: bool) -> None:
    """Point diagnostics have no final score or synthetic whole-answer accuracy metrics."""
    output = responses()["fixture"]["P2"] if valid else completion({})
    logs = adapter.evaluate_staged_samples(
        [sample()],
        settings=settings(),
        artifact_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        count_tokens=lambda req: 100,
        counter_model_digest="fixture-digest",
        fixture_responses={"fixture": {"P2": output}},
        points_only=True,
    )
    record = logs[0].samples[0].scores["staged_grounding_scorer"].metadata["grounding_record"]
    assert record["status"] == ("points_complete" if valid else "schema_error")
    assert record["score"] is None and record["attempts"] == record["stage_expected"] == 1
    assert [s["kind"] for s in record["stages"]] == ["point"]
    metrics = adapter.summarize_staged_records([record])
    assert metrics["point_supported"] == int(valid)
    assert metrics["point_unsupported"] == 0
    assert metrics["evaluation_failed"] == int(not valid)
    assert "grounding_mean" not in metrics and "synthetic_exact_agreement" not in metrics


def test_points_only_zero_points_and_incompatible_gate(tmp_path: Path) -> None:
    """An answer without non-conclusion points receives an explicit zero-call result."""
    from er_commons.artifact_io import stable_json_sha256

    s = sample()
    s.packet["payload"]["answer"]["qualifications"] = []
    s.packet["diagnostics"]["payload_sha256"] = stable_json_sha256(s.packet["payload"])
    logs = adapter.evaluate_staged_samples(
        [s],
        settings=settings(),
        artifact_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        fixture_responses={"fixture": {}},
        points_only=True,
    )
    record = logs[0].samples[0].scores["staged_grounding_scorer"].metadata["grounding_record"]
    assert record["status"] == "points_complete" and record["no_points"] is True
    assert record["attempts"] == record["stage_expected"] == 0 and record["score"] is None
    assert adapter.summarize_staged_records([record])["no_points"] == 1
    with pytest.raises(ValueError, match="cannot run an abstention"):
        adapter.evaluate_staged_samples(
            [s],
            settings=settings(),
            artifact_dir=tmp_path / "other",
            log_dir=tmp_path / "otherlogs",
            points_only=True,
            check_abstention=True,
        )


def test_points_only_unsupported_is_valid_diagnostic(tmp_path: Path) -> None:
    """A validated false support flag is counted without manufacturing a grounding score."""
    output = completion(
        {
            "point_id": "P2",
            "supported": False,
            "unsupported_assertions": [
                {"assertion": "Exact caveat.", "explanation": "Not supported."}
            ],
            "locators": [],
            "explanation": "Invented unsupported point.",
        }
    )
    logs = adapter.evaluate_staged_samples(
        [sample()],
        settings=settings(),
        artifact_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        count_tokens=lambda req: 100,
        counter_model_digest="fixture-digest",
        fixture_responses={"fixture": {"P2": output}},
        points_only=True,
    )
    record = logs[0].samples[0].scores["staged_grounding_scorer"].metadata["grounding_record"]
    assert record["status"] == "points_complete" and record["score"] is None
    metrics = adapter.summarize_staged_records([record])
    assert metrics["point_unsupported"] == 1 and metrics["point_supported"] == 0
    assert metrics["evaluation_failed"] == 0


def test_stage_expectations_never_change_requests(tmp_path: Path) -> None:
    """Restricted stage labels change analysis metadata, never any native judge input."""
    requests: list[list[dict]] = [[], []]
    for index, expectation in enumerate(
        (
            None,
            {
                "clean_abstention": False,
                "point_expectations": [{"point_id": "P2", "supported": False}],
                "conclusion_supported": False,
            },
        )
    ):
        s = sample().model_copy(update={"stage_expectations": expectation})

        def counter(request: dict, captured: list[dict] = requests[index]) -> int:
            captured.append(copy.deepcopy(request))
            return 100

        logs = adapter.evaluate_staged_samples(
            [s],
            settings=settings(),
            artifact_dir=tmp_path / str(index) / "raw",
            log_dir=tmp_path / str(index) / "logs",
            count_tokens=counter,
            counter_model_digest="fixture-digest",
            fixture_responses=responses(),
        )
        record = logs[0].samples[0].scores["staged_grounding_scorer"].metadata["grounding_record"]
        assert record["stage_expectations"] == expectation
    assert requests[0] == requests[1]


def test_stage_diagnostics_exclude_invalid_missing_and_null() -> None:
    """Missing, malformed and abstention-null judgments never become negative predictions."""
    expectations = {
        "clean_abstention": False,
        "point_expectations": [
            {"point_id": "P2", "supported": True},
            {"point_id": "P3", "supported": False},
            {"point_id": "P4", "supported": None},
        ],
        "conclusion_supported": True,
    }
    record = {
        "stage_expectations": expectations,
        "stages": [
            {"key": "abstention", "status": "validated", "result": {"classification": "ambiguous"}},
            {"key": "P2", "status": "validated", "result": {"supported": False}},
            {"key": "P3", "status": "schema_error", "result": {"supported": False}},
            {"key": "P4", "status": "validated", "result": {"supported": True}},
        ],
    }
    metrics = adapter._stage_diagnostics([record])
    assert metrics["stage_diagnostic_point_eligible"] == 2
    assert metrics["stage_diagnostic_point_predictions"] == 1
    assert metrics["stage_diagnostic_point_coverage"] == 0.5
    assert metrics["stage_diagnostic_point_agreement"] == 0
    assert metrics["stage_diagnostic_point_expected_true_predicted_false"] == 1
    assert metrics["stage_diagnostic_point_expected_false_predicted_false"] == 0
    assert metrics["stage_diagnostic_abstention_ambiguous"] == 1
    assert metrics["stage_diagnostic_abstention_agreement"] is None
    assert metrics["stage_diagnostic_conclusion_eligible"] == 1
    assert metrics["stage_diagnostic_conclusion_coverage"] == 0
    assert metrics["stage_diagnostic_conclusion_agreement"] is None
    assert adapter._stage_diagnostics([{"stages": []}]) == {}


def test_stage_diagnostics_validated_confusion_and_no_eligible() -> None:
    """Boolean agreement has explicit denominators; null expectations are ineligible."""
    records = [
        {
            "stage_expectations": {
                "clean_abstention": True,
                "conclusion_supported": None,
                "point_expectations": [],
            },
            "stages": [
                {
                    "key": "abstention",
                    "status": "validated",
                    "result": {
                        "classification": "clean_abstention",
                    },
                }
            ],
        }
    ]
    metrics = adapter._stage_diagnostics(records)
    assert metrics["stage_diagnostic_abstention_eligible"] == 1
    assert metrics["stage_diagnostic_abstention_predictions"] == 1
    assert metrics["stage_diagnostic_abstention_agreement"] == 1
    assert metrics["stage_diagnostic_abstention_expected_true_predicted_true"] == 1
    assert metrics["stage_diagnostic_point_coverage"] is None
    assert metrics["stage_diagnostic_conclusion_eligible"] == 0
