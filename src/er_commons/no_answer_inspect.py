"""Native Inspect execution for the conclusion-only no-answer classifier A.

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
from er_commons import no_answer as core
from er_commons.artifact_io import stable_json_sha256

REPO = Path(__file__).resolve().parents[2]
PROVIDERS = shared.PROVIDERS


def generation_config(
    condition_id: str, prompt_version: str = core.PROMPT_VERSION
) -> GenerateConfig:
    """Apply shared native settings while preserving the selected schema ordering."""
    prompt = core.system_prompt(prompt_version)
    schema = core.output_json_schema()
    return shared.generation_config(condition_id, "A", prompt, schema, "no_answer_A")


def native_model(
    condition_id: str, *, prompt_version: str = core.PROMPT_VERSION, **model_args: Any
) -> Model:
    """Construct the shared native provider without changing component semantics."""
    return shared.native_model(
        condition_id,
        "A",
        core.system_prompt(prompt_version),
        generation_config(condition_id, prompt_version),
        **model_args,
    )


def selected_condition() -> str:
    """Validate the selected model and semantic identities before dispatch."""
    return shared.selected_condition(
        "A", core.PROMPT_VERSION, core.system_prompt(), core.output_json_schema()
    )


@scorer(metrics={"correct": [mean()], "valid": [mean()]})
def no_answer_score(prompt_version: str = core.PROMPT_VERSION) -> Scorer:
    """Separate output failures and three-way semantic errors in native sample logs."""

    core.system_prompt(prompt_version)  # Validate before any evaluation begins.

    async def score(state: TaskState, target: Target) -> Score:
        """Score once; malformed judgments never request a replacement generation."""
        if target.text not in {"clean_abstention", "substantive", "ambiguous"}:
            raise ValueError("Unknown no-answer calibration label")
        raw = state.output.completion
        metadata: dict[str, Any] = {
            "raw_output": raw,
            "prompt_version": prompt_version,
            "expected_classification": target.text,
            "guard_status": "not_run",
        }
        try:
            if state.output.stop_reason == "max_tokens":
                raise ValueError("truncated_output")
            result = core.parse_output(raw)
        except (ValueError, TypeError) as error:
            metadata.update(
                status="invalid_output",
                error_type=type(error).__name__,
                error=str(error),
                error_family="output_failure",
            )
            return Score(value={"correct": 0, "valid": 0}, answer=raw, metadata=metadata)
        decision = result["classification"]
        correct = decision == target.text
        # Flags can overlap: ambiguous -> abstention is both ambiguous-class error
        # and false abstention. Invalid outputs never acquire semantic labels.
        metadata.update(
            status="evaluated",
            classification=decision,
            result=result,
            false_abstention=decision == "clean_abstention" and not correct,
            substantive_false_abstention=(
                decision == "clean_abstention" and target.text == "substantive"
            ),
            missed_abstention=target.text == "clean_abstention" and not correct,
            ambiguous_class_error=not correct and "ambiguous" in (decision, target.text),
            error_family="none" if correct else "classification_error",
        )
        return Score(
            value={"correct": int(correct), "valid": 1},
            answer=decision,
            explanation=result["reason"],
            metadata=metadata,
        )

    return score


def build_task(
    condition_id: str,
    samples: list[dict[str, Any]],
    labels: dict[str, str],
    *,
    epochs: int = 1,
    provenance: dict[str, Any] | None = None,
    prompt_version: str = core.PROMPT_VERSION,
    cost_limit: float | None = None,
) -> Task:
    """Build one native generation per conclusion; targets never enter messages."""
    shared.validate_samples(samples, labels, epochs)
    selected_condition()
    config = generation_config(condition_id, prompt_version)
    prompt = core.system_prompt(prompt_version)
    dataset = []
    for sample in samples:
        sample_id = sample["sample_id"]
        packet = core.validate_input(sample["packet"])
        label = labels[sample_id]
        if label not in {"clean_abstention", "substantive", "ambiguous"}:
            raise ValueError("Unknown no-answer calibration label")
        dataset.append(
            Sample(
                id=sample_id,
                input=[
                    ChatMessageSystem(
                        content=[ContentText(text=prompt, cache_breakpoint=True)]
                        if condition_id == "anthropic_generation"
                        else prompt
                    ),
                    ChatMessageUser(
                        content=json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
                    ),
                ],
                target=label,
                metadata={
                    **{key: value for key, value in sample.items() if key != "packet"},
                    "payload_sha256": stable_json_sha256(packet),
                    "guard_status": "not_run",
                },
            )
        )
    return Task(
        name=f"no_answer_A_{condition_id}",
        dataset=dataset,
        model=native_model(condition_id, prompt_version=prompt_version),
        config=config,
        solver=generate(cache=False),
        scorer=no_answer_score(prompt_version),
        epochs=epochs,
        cost_limit=cost_limit,
        time_limit=150,
        metadata={
            **shared.task_metadata("A", prompt_version, prompt, core.output_json_schema()),
            "policy_version": core.POLICY_VERSION,
            "contract_version": core.CONTRACT_VERSION,
            "panel": provenance or {},
            "guard_status": "not_run",
        },
    )


@task
def no_answer(condition_id: str | None = None, prompt_version: str = core.PROMPT_VERSION) -> Task:
    """Load only the locked A24 calibration panel through the standard Inspect CLI."""
    samples, labels, provenance = core.load_panel()
    return build_task(
        condition_id or selected_condition(),
        samples,
        labels,
        provenance=provenance,
        prompt_version=prompt_version,
    )


@task
def no_answer_full(condition_id: str | None = None) -> Task:
    """Evaluate all sealed A310 development proposals using the existing v2 prompt."""
    from er_commons.no_answer_development import load_full_development

    samples, labels, provenance = load_full_development()
    return build_task(
        condition_id or selected_condition(),
        samples,
        labels,
        provenance=provenance,
        prompt_version=core.PROMPT_VERSION,
    )
