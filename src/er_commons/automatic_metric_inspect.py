"""Offline saved-answer scoring; Inspect owns execution, logs, and aggregation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal, Self

from inspect_ai import Task, eval
from inspect_ai.dataset import Sample
from inspect_ai.log import EvalLog
from inspect_ai.model import ModelOutput
from inspect_ai.scorer import Metric, SampleScore, Score, Scorer, Target, metric, scorer
from inspect_ai.solver import Generate, Solver, TaskState, solver
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from er_commons.automatic_metric_inputs import (
    build_catalog,
    resolve_citations,
    resolve_receipt,
    resolve_references,
)
from er_commons.automatic_metrics import MetricRecord, aggregate_metrics, calculate_metrics


class SavedMetricSample(BaseModel):
    """Explicit prepared input, with reviewed evidence confined to score metadata.

    Production callers must supply verified development projections through the
    existing release loader. This format does not authorize loading a release or
    traversing a challenge partition.
    """

    model_config = ConfigDict(extra="forbid", strict=True)
    case_id: str
    sample_id: str | None = None
    scope: Literal["invented_fixture", "development"]
    saved_answer: Any
    sources: list[dict[str, Any]]
    verified_aliases: dict[str, str] = Field(default_factory=dict)
    packet_mapping: dict[str, str] | None = None
    packet_local: bool = False
    retrieval_receipt: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        """Keep benchmark identity and optional observation identity nonblank."""
        if not self.case_id.strip() or (self.sample_id is not None and not self.sample_id.strip()):
            raise ValueError("case_id and supplied sample_id must be nonblank")
        return self

    @property
    def inspect_id(self) -> str:
        """Preserve existing one-answer IDs while supporting explicit variant IDs."""
        return self.sample_id if self.sample_id is not None else self.case_id


def _validate_sample_ids(samples: list[SavedMetricSample]) -> None:
    """Reject accidental duplicate observations without merging variants of one case."""
    if not samples or len({sample.inspect_id for sample in samples}) != len(samples):
        raise ValueError("Provide nonempty samples with distinct sample IDs")


def load_saved_samples(path: Path) -> list[SavedMetricSample]:
    """Read only the explicit prepared array and validate it before Inspect starts."""
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("samples must be a JSON array")
    samples = [SavedMetricSample.model_validate(row) for row in rows]
    _validate_sample_ids(samples)
    return samples


def _record(state: TaskState) -> MetricRecord:
    """Resolve the actual saved output against explicit canonical source mappings."""
    sample = SavedMetricSample.model_validate(state.metadata["automatic_metric_input"])
    catalog = build_catalog(sample.sources, verified_aliases=sample.verified_aliases)
    try:
        answer = json.loads(state.output.completion)
    except json.JSONDecodeError:
        answer = state.output.completion
    return calculate_metrics(
        sample.case_id,
        resolve_references(sample.sources, catalog),
        resolve_citations(
            answer, catalog, packet_mapping=sample.packet_mapping, packet_local=sample.packet_local
        ),
        resolve_receipt(sample.retrieval_receipt, catalog),
    )


@metric
def automatic_summary(family: Literal["citation", "retrieval"]) -> Metric:
    """Pool original counts, preserving null aggregates and explicit eligibility."""

    def compute(scores: list[SampleScore]) -> dict[str, float | int | None]:
        """Read auditable records from scores rather than averaging scalar defaults."""
        records = [
            MetricRecord.model_validate((item.score.metadata or {})["metric_record"])
            for item in scores
        ]
        summary = aggregate_metrics(records)
        return summary.citation if family == "citation" else summary.retrieval

    return compute


@solver
def saved_answer() -> Solver:
    """Load the supplied answer without invoking any target or judge model."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        """Set output only; automatic source/reference metadata never enters input."""
        sample = SavedMetricSample.model_validate(state.metadata["automatic_metric_input"])
        state.output = ModelOutput.from_content(
            "saved-answer", json.dumps(sample.saved_answer, ensure_ascii=False)
        )
        return state

    return solve


@scorer(metrics=[automatic_summary("citation")])
def automatic_citations() -> Scorer:
    """Expose final-citation matching as its own Inspect result."""

    async def score(state: TaskState, target: Target) -> Score:
        """Retain null scores and reconstruction evidence for every saved answer."""
        record = _record(state)
        return Score(
            value={
                "precision": record.citation.precision,
                "recall": record.citation.recall,
                "f1": record.citation.f1,
            },
            explanation=record.citation.status,
            metadata={"metric_record": record.model_dump(mode="json")},
        )

    return score


@scorer(metrics=[automatic_summary("retrieval")])
def automatic_retrieval() -> Scorer:
    """Expose actual-delivery recall independently of final answer citations."""

    async def score(state: TaskState, target: Target) -> Score:
        """Missing receipts remain unavailable in both logs and aggregates."""
        record = _record(state)
        return Score(
            value={"recall": record.retrieval.recall},
            explanation=record.retrieval.status,
            metadata={"metric_record": record.model_dump(mode="json")},
        )

    return score


def automatic_metric_task(samples: list[SavedMetricSample]) -> Task:
    """Construct one offline Inspect task with two independent automatic results."""
    _validate_sample_ids(samples)
    return Task(
        name="task09d_automatic_metrics",
        dataset=[
            Sample(
                id=sample.inspect_id,
                input="Evaluate the supplied saved answer offline.",
                metadata={"automatic_metric_input": sample.model_dump(mode="json")},
            )
            for sample in samples
        ],
        solver=saved_answer(),
        scorer=[automatic_citations(), automatic_retrieval()],
    )


def evaluate_saved_samples(samples: list[SavedMetricSample], log_dir: Path) -> list[EvalLog]:
    """Delegate all evaluation execution and persisted reporting to Inspect."""
    return list(
        eval(
            automatic_metric_task(samples),
            model="mockllm/model",
            log_dir=str(log_dir),
            display="none",
            retry_on_error=0,
            fail_on_error=True,
        )
    )


def main() -> None:
    """Run explicitly prepared saved inputs; never discover or generate samples."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("samples", type=Path, help="Prepared saved metric samples JSON array")
    parser.add_argument("--log-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        samples = load_saved_samples(args.samples)
    except ValidationError as error:
        issue = error.errors(include_input=False, include_url=False)[0]
        location = ".".join(map(str, issue["loc"]))
        parser.error(f"Invalid saved sample at {location}: {issue['msg']}")
    except (OSError, ValueError) as error:
        parser.error(f"Cannot load saved samples: {error}")
    logs = evaluate_saved_samples(samples, args.log_dir)
    if any(log.status != "success" for log in logs):
        raise SystemExit("Inspect evaluation failed; inspect the saved log")


if __name__ == "__main__":
    main()
