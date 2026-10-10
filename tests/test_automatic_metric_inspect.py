"""Actual offline Inspect execution preserves counts, nulls, and saved logs."""

import json
from pathlib import Path
from typing import Any

import pytest
from inspect_ai.log import EvalLog, read_eval_log
from inspect_ai.model import Model

from er_commons.automatic_metric_inspect import (
    SavedMetricSample,
    automatic_metric_task,
    evaluate_saved_samples,
)

FIXTURE = Path(__file__).parent / "fixtures/automatic_metrics/saved_samples.json"


def samples() -> list[SavedMetricSample]:
    """Load only checked-in invented cases, never a benchmark release."""
    return [SavedMetricSample.model_validate(row) for row in json.loads(FIXTURE.read_text())]


def metrics(log: EvalLog, scorer_name: str) -> dict[str, float]:
    """Get named Inspect aggregates from the persisted evaluation result."""
    assert log.results is not None
    result = next(score for score in log.results.scores if score.name == scorer_name)
    return {key: metric.value for key, metric in result.metrics.items()}


def test_offline_inspect_saved_logs_and_denominators(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise both scorers and Inspect aggregation with zero generation calls."""
    calls = 0

    async def forbidden_generation(*args: Any, **kwargs: Any) -> Any:
        """Fail if any solver or scorer accidentally requests inference."""
        nonlocal calls
        calls += 1
        raise AssertionError("Offline automatic metrics must not invoke a model")

    monkeypatch.setattr(Model, "generate", forbidden_generation)
    logs = evaluate_saved_samples(samples(), tmp_path)
    assert calls == 0
    assert len(logs) == 1 and logs[0].status == "success"
    saved = list(tmp_path.glob("*.eval"))
    assert len(saved) == 1
    log = read_eval_log(saved[0])
    assert log.status == "success"
    assert not log.stats.model_usage
    assert log.samples is not None
    by_id = {sample.id: sample for sample in log.samples}
    missing = by_id["perfect-missing-retrieval"]
    assert missing.scores is not None
    assert missing.scores["automatic_retrieval"].value == {"recall": None}
    assert missing.scores["automatic_retrieval"].explanation == "unavailable"
    empty = by_id["partial-empty-retrieval"]
    assert empty.scores is not None
    assert empty.scores["automatic_retrieval"].value == {"recall": 0.0}
    citation = empty.scores["automatic_citations"]
    assert citation.value == pytest.approx({"precision": 1 / 3, "recall": 1 / 3, "f1": 1 / 3})
    assert citation.metadata is not None
    record = citation.metadata["metric_record"]
    assert record["citation"]["precision_denominator"] == 3
    assert record["citation"]["neutral_count"] == 1
    assert record["invalid_tokens"] == ["str:unknown"]
    na = by_id["empty-support-not-applicable"]
    assert na.scores is not None
    assert na.scores["automatic_citations"].value == {"precision": None, "recall": None, "f1": None}
    citation_metrics = metrics(log, "automatic_citations")
    assert citation_metrics["eligible_cases"] == 3
    assert citation_metrics["not_applicable_cases"] == 1
    assert citation_metrics["support_count"] == 6
    assert citation_metrics["precision_denominator"] == 6
    assert citation_metrics["macro_precision"] == pytest.approx(7 / 9)
    assert citation_metrics["micro_precision"] == pytest.approx(2 / 3)
    assert citation_metrics["micro_recall"] == pytest.approx(2 / 3)
    assert citation_metrics["micro_f1"] == pytest.approx(2 / 3)
    retrieval_metrics = metrics(log, "automatic_retrieval")
    assert retrieval_metrics["eligible_cases"] == 2
    assert retrieval_metrics["unavailable_cases"] == 1
    assert retrieval_metrics["not_applicable_cases"] == 1
    assert retrieval_metrics["support_count"] == 5
    assert retrieval_metrics["complete_case_recall"] == 0.5
    assert retrieval_metrics["macro_recall"] == pytest.approx(0.5)
    assert retrieval_metrics["micro_recall"] == pytest.approx(0.4)
    for sample in log.samples:
        assert "approved_roles" not in json.dumps(sample.input)


def test_all_missing_retrieval_keeps_null_aggregate(tmp_path: Path) -> None:
    """Undefined means are omitted by Inspect, with status counts retained."""
    log = evaluate_saved_samples(samples()[:1], tmp_path)[0]
    aggregate = metrics(log, "automatic_retrieval")
    assert "macro_recall" not in aggregate
    assert "micro_recall" not in aggregate
    assert aggregate["eligible_cases"] == 0
    assert aggregate["unavailable_cases"] == 1
    assert aggregate["support_count"] == 0


def test_saved_task_rejects_duplicate_or_empty_cases() -> None:
    """A saved evaluation must not silently double-weight case identities."""
    with pytest.raises(ValueError, match="distinct"):
        automatic_metric_task([samples()[0], samples()[0]])
    with pytest.raises(ValueError, match="nonempty"):
        automatic_metric_task([])


def test_distinct_saved_variants_retain_benchmark_case_identity(tmp_path: Path) -> None:
    """Two answers to one case remain separate Inspect samples and observations."""
    variants = [
        sample.model_copy(update={"case_id": "shared-case", "sample_id": f"variant-{index}"})
        for index, sample in enumerate(samples()[:2])
    ]
    log = evaluate_saved_samples(variants, tmp_path)[0]
    assert log.status == "success"
    assert not log.stats.model_usage
    assert log.samples is not None
    assert {sample.id for sample in log.samples} == {"variant-0", "variant-1"}
    for sample in log.samples:
        assert sample.scores is not None
        metadata = sample.scores["automatic_citations"].metadata
        assert metadata is not None
        assert metadata["metric_record"]["case_id"] == "shared-case"
    assert metrics(log, "automatic_citations")["eligible_cases"] == 2
    assert metrics(log, "automatic_citations")["macro_recall"] == pytest.approx(2 / 3)
    with pytest.raises(ValueError, match="distinct sample IDs"):
        automatic_metric_task(
            [variants[0], variants[1].model_copy(update={"sample_id": "variant-0"})]
        )


@pytest.mark.parametrize("patch", [{"case_id": " "}, {"sample_id": ""}, {"packet_local": "false"}])
def test_prepared_envelope_rejects_blank_identity_and_coercion(patch: dict[str, Any]) -> None:
    """A malformed envelope must not change identity or packet namespace implicitly."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        SavedMetricSample.model_validate(samples()[0].model_dump() | patch)


@pytest.mark.parametrize("contents", ["not json", "{}", "[]", '[{"case_id":"x"}]'])
def test_cli_reports_bad_input_without_starting_inspect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    contents: str,
) -> None:
    """Expected file/schema problems get concise CLI errors before a log is created."""
    from er_commons.automatic_metric_inspect import main

    path = tmp_path / "samples.json"
    path.write_text(contents)
    output = tmp_path / "inspect"
    monkeypatch.setattr("sys.argv", ["automatic-metrics", str(path), "--log-dir", str(output)])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert "error:" in capsys.readouterr().err
    assert not output.exists()
