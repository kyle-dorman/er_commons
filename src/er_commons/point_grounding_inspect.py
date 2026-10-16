"""Native Inspect execution for the independent supporting-point grounding judge.

Inspect owns provider transport, bounded retries, concurrency and evaluation logs.
The strict benchmark parser owns validity; invalid judgments never trigger retries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser, ContentText, GenerateConfig, Model
from inspect_ai.scorer import Score, Scorer, Target, mean, scorer
from inspect_ai.solver import TaskState, generate

from er_commons import judge_inspect as shared
from er_commons import point_grounding as core

REPO = Path(__file__).resolve().parents[2]
PROMPT_VERSION = core.PROMPT_VERSION
CONFIG_PATH = shared.CONFIG_PATH
PROVIDERS = shared.PROVIDERS


def generation_config(
    condition_id: str, prompt_version: str = core.PROMPT_VERSION
) -> GenerateConfig:
    """Apply shared native settings while preserving the selected schema ordering."""
    prompt = core.system_prompt(prompt_version)
    schema = core.output_json_schema()
    schema["properties"] = {key: schema["properties"][key] for key in ("reason", "supported")}
    schema["required"] = ["reason", "supported"]
    return shared.generation_config(condition_id, "G", prompt, schema, "point_grounding_v1")


def native_model(
    condition_id: str, *, prompt_version: str = core.PROMPT_VERSION, **model_args: Any
) -> Model:
    """Construct the shared native provider without changing component semantics."""
    return shared.native_model(
        condition_id,
        "G",
        core.system_prompt(prompt_version),
        generation_config(condition_id, prompt_version),
        **model_args,
    )


def selected_condition() -> str:
    """Validate the selected model and semantic identities before dispatch."""
    return shared.selected_condition(
        "G", core.PROMPT_VERSION, core.system_prompt(), core.output_json_schema()
    )


@scorer(
    metrics={
        "correct": [mean()],
        "valid": [mean()],
        "false_accept": [mean()],
        "false_reject": [mean()],
    }
)
def point_grounding_score(prompt_version: str = PROMPT_VERSION) -> Scorer:
    """Separate semantic disagreements from invalid output without repairing judgments."""

    core.system_prompt(prompt_version)

    async def score(state: TaskState, target: Target) -> Score:
        """Retain raw responses and null decisions for every invalid model judgment."""
        if target.text not in {"yes", "no"}:
            raise ValueError("Expected target must be yes or no")
        raw = state.output.completion
        metadata: dict[str, Any] = {
            "raw_output": raw,
            "prompt_version": prompt_version,
            "decision": None,
            "expected_supported": target.text == "yes",
        }
        values = {"correct": 0, "valid": 0, "false_accept": 0, "false_reject": 0}
        if state.output.stop_reason == "max_tokens":
            metadata.update(status="invalid_output", error_type="truncated_output")
            return Score(value=values, answer=raw, metadata=metadata)
        try:
            result = core.parse_output(raw)
        except (ValueError, TypeError) as error:
            metadata.update(status="invalid_output", error_type=type(error).__name__)
            return Score(value=values, answer=raw, metadata=metadata)
        decision = result["supported"]
        expected = target.text == "yes"
        error_kind = (
            "false_accept"
            if decision and not expected
            else "false_reject"
            if expected and not decision
            else None
        )
        metadata.update(
            status="evaluated", decision=decision, result=result, semantic_error=error_kind
        )
        return Score(
            value={
                "correct": int(decision == expected),
                "valid": 1,
                "false_accept": int(error_kind == "false_accept"),
                "false_reject": int(error_kind == "false_reject"),
            },
            answer="yes" if decision else "no",
            explanation=result["reason"],
            metadata=metadata,
        )

    return score


def build_task(
    condition_id: str,
    samples: list[dict[str, Any]],
    labels: dict[str, bool],
    *,
    epochs: int = 1,
    prompt_version: str = PROMPT_VERSION,
    cost_limit: float | None = None,
    provenance: dict[str, Any] | None = None,
) -> Task:
    """Build one-generation G samples; provenance stays outside model-visible messages."""
    if condition_id not in PROVIDERS:
        raise ValueError("Unknown point-grounding provider")
    shared.validate_samples(samples, labels, epochs)
    selected_condition()
    prompt = core.system_prompt(prompt_version)
    dataset = []
    for sample in samples:
        metadata = sample.get("metadata", {})
        if metadata.get("status") in {"precheck_failed", "execution_error", "invalid_input"}:
            raise ValueError("Failed prechecks or evaluator errors cannot reach a model")
        packet = core.validate_input(
            sample["packet"], citation_ids=metadata.get("owned_citation_ids")
        )
        if type(labels[sample["sample_id"]]) is not bool:
            raise ValueError("Expected label must be a Boolean")
        dataset.append(
            Sample(
                id=sample["sample_id"],
                input=[
                    ChatMessageSystem(
                        content=[ContentText(text=prompt, cache_breakpoint=True)]
                        if condition_id == "anthropic_generation"
                        else prompt
                    ),
                    ChatMessageUser(
                        content=json.dumps(
                            packet, ensure_ascii=False, separators=(",", ":"), allow_nan=False
                        )
                    ),
                ],
                target="yes" if labels[sample["sample_id"]] else "no",
                metadata={
                    **sample.get("metadata", {}),
                    "packet": packet,
                    "case_id": sample["case_id"],
                    "sample_id": sample["sample_id"],
                },
            )
        )
    return Task(
        name=f"point_grounding_G_{condition_id}",
        dataset=dataset,
        model=native_model(condition_id, prompt_version=prompt_version),
        config=generation_config(condition_id, prompt_version),
        solver=generate(cache=False),
        scorer=point_grounding_score(prompt_version),
        epochs=epochs,
        cost_limit=cost_limit,
        time_limit=150,
        metadata={
            **shared.task_metadata("G", prompt_version, prompt, core.output_json_schema()),
            "policy_version": core.POLICY_VERSION,
            "contract_version": core.CONTRACT_VERSION,
            "schema_version": core.SCHEMA_VERSION,
            "panel_provenance": provenance or {},
        },
    )


@task
def point_grounding(
    condition_id: str | None = None,
    panel: str = "calibration",
    epochs: int = 1,
    prompt_version: str = PROMPT_VERSION,
) -> Task:
    """Expose only the locked calibration panel; Inspect owns repetition and execution."""
    if panel != "calibration":
        raise ValueError("Only the locked calibration panel is supported")
    from er_commons.point_grounding_panel import load_panel

    core.system_prompt(prompt_version)
    samples, labels, provenance = load_panel()
    return build_task(
        condition_id or selected_condition(),
        samples,
        labels,
        epochs=epochs,
        prompt_version=prompt_version,
        provenance=provenance,
    )


@task
def point_grounding_full(
    condition_id: str | None = None,
    epochs: int = 3,
    prompt_version: str = core.PROMPT_VERSION,
) -> Task:
    """Evaluate eligible frozen development points with the selected production prompt."""
    from er_commons.point_grounding_development import load_development

    core.system_prompt(prompt_version)
    samples, labels, provenance = load_development()
    return build_task(
        condition_id or selected_condition(),
        samples,
        labels,
        epochs=epochs,
        prompt_version=prompt_version,
        provenance=provenance,
    )
