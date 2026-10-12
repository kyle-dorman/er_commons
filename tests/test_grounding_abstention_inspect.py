"""Answer-only classifier and optional gate use invented Inspect fixtures, never inference."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from test_grounding_inspect import completion, sample
from test_grounding_staged_inspect import responses
from test_judge_packet_requests import settings

from er_commons.grounding_abstention_inspect import (
    evaluate_abstention_samples,
    summarize_abstention_records,
)
from er_commons.grounding_staged_inspect import evaluate_staged_samples, summarize_staged_records


def classified(label: str) -> dict:
    """Wrap one invented classification with no synthetic labels in its explanation."""
    return completion({"classification": label, "explanation": "Invented answer text assessment."})


@pytest.mark.parametrize("label", ["clean_abstention", "substantive", "ambiguous"])
def test_answer_only_inspect_classification(tmp_path: Path, label: str) -> None:
    """Only original point texts reach model requests; output has no grounding score."""
    requests = []

    def counter(request: dict) -> int:
        requests.append(copy.deepcopy(request))
        return 100

    logs = evaluate_abstention_samples(
        [sample()],
        settings=settings(),
        artifact_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        count_tokens=counter,
        counter_model_digest="fixture-digest",
        fixture_responses={"fixture": {"abstention": classified(label)}},
    )
    score = logs[0].samples[0].scores["abstention_scorer"]
    record = score.metadata["abstention_record"]
    assert score.value == {"classification": label} and "score" not in record
    assert record["classification"] == label and record["status"] == "classified"
    assert len(requests) == 1 and "SECRET" not in json.dumps(requests)
    assert json.loads(requests[0]["messages"][1]["content"]) == {
        "points": [
            {"point_id": "P1", "text": "Exact claim."},
            {"point_id": "P2", "text": "Exact caveat."},
        ]
    }
    metrics = summarize_abstention_records([record])
    assert (
        metrics[label] == 1 and metrics["stage_calls"] == metrics["exact_input_parity_calls"] == 1
    )
    assert metrics["native_output_tokens"] == 40
    assert metrics["synthetic_comparable"] == (0 if label == "ambiguous" else 1)


@pytest.mark.parametrize(
    "label,status,attempts",
    [
        ("clean_abstention", "not_applicable", 1),
        ("ambiguous", "unresolved_abstention", 1),
        ("substantive", "scored", 3),
        ("bad_label", "schema_error", 1),
    ],
)
def test_optional_gate_routes_before_points(
    tmp_path: Path, label: str, status: str, attempts: int
) -> None:
    """Only substantive classification can dispatch downstream point/conclusion stages."""
    fixtures = responses()
    fixtures["fixture"]["abstention"] = classified(label)
    logs = evaluate_staged_samples(
        [sample()],
        settings=settings(),
        artifact_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        count_tokens=lambda req: 100,
        counter_model_digest="fixture-digest",
        fixture_responses=fixtures,
        check_abstention=True,
    )
    record = logs[0].samples[0].scores["staged_grounding_scorer"].metadata["grounding_record"]
    assert record["status"] == status and record["attempts"] == attempts
    assert record["stages"][0]["kind"] == "abstention"
    assert record["score"] == (2 if label == "substantive" else None)
    if label == "ambiguous":
        metrics = summarize_staged_records([record])
        assert metrics["unresolved_abstention"] == 1 and metrics["evaluation_failed"] == 0


@pytest.mark.parametrize(
    "count,status", [(None, "context_unverified"), (101, "context_counter_mismatch")]
)
def test_classifier_preflight_and_counter_halt(
    tmp_path: Path, count: int | None, status: str
) -> None:
    """Unknown counters block calls; observed mismatch halts the rest of the classification run."""
    fixtures = {sid: {"abstention": classified("substantive")} for sid in ("fixture", "later")}
    logs = evaluate_abstention_samples(
        [sample(), sample("later")],
        settings=settings(),
        artifact_dir=tmp_path / "raw",
        log_dir=tmp_path / "logs",
        count_tokens=None if count is None else lambda req: count,
        counter_model_digest="fixture-digest",
        fixture_responses=fixtures,
    )
    records = [s.scores["abstention_scorer"].metadata["abstention_record"] for s in logs[0].samples]
    assert all(r["status"] == status for r in records)
    assert sum(r["attempts"] for r in records) == (0 if count is None else 1)


def test_classifier_fresh_and_scope_guards(tmp_path: Path) -> None:
    """Existing evidence and development scope cannot silently use fixture transport."""
    (tmp_path / "raw").mkdir()
    kwargs: dict[str, Any] = {
        "settings": settings(),
        "artifact_dir": tmp_path / "raw",
        "log_dir": tmp_path / "logs",
    }
    with pytest.raises(ValueError, match="fresh"):
        evaluate_abstention_samples([sample()], **kwargs)
    kwargs["artifact_dir"] = tmp_path / "fresh"
    with pytest.raises(ValueError, match="invented_fixture"):
        evaluate_abstention_samples(
            [sample().model_copy(update={"scope": "development"})],
            **kwargs,
            fixture_responses={"fixture": {}},
        )
