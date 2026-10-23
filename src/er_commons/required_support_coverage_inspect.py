"""Native Inspect adapter for diagnostic required-support coverage judgments."""

from __future__ import annotations

import json
from typing import Any

from inspect_ai import Task
from inspect_ai.dataset import Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser, GenerateConfig, Model
from inspect_ai.scorer import Score, Scorer, Target, mean, scorer
from inspect_ai.solver import TaskState, generate

from er_commons import judge_inspect as shared
from er_commons import required_support_coverage as core
from er_commons.artifact_io import stable_json_sha256


def generation_config(condition_id: str = "openai_generation") -> GenerateConfig:
    """Reuse native settings with the explicitly approved pilot concurrency."""
    if condition_id != "openai_generation":
        raise ValueError("Task15Y pilot authorizes only the native OpenAI profile")
    wire_schema = core.output_json_schema()
    # OpenAI strict schema omits uniqueItems; local parsing still enforces it.
    wire_schema["properties"]["supporting_point_ids"].pop("uniqueItems")
    config = shared.generation_config(
        condition_id,
        "required_support_coverage",
        core.system_prompt(),
        wire_schema,
        "required_support_coverage",
    )
    config.max_connections = 16
    return config


def native_model(condition_id: str = "openai_generation", **model_args: Any) -> Model:
    """Construct only the approved provider, retaining native transport and costs."""
    return shared.native_model(
        condition_id,
        "required_support_coverage",
        core.system_prompt(),
        generation_config(condition_id),
        **model_args,
    )


@scorer(metrics={"correct": [mean()], "valid": [mean()]})
def coverage_score() -> Scorer:
    """Record validity separately; invalid results have no coverage decision."""

    async def score(state: TaskState, target: Target) -> Score:
        """Parse once without correction, label replacement or semantic retries."""
        if target.text not in {"true", "false"}:
            raise ValueError("Expected coverage label must be true or false")
        expected = target.text == "true"
        metadata: dict[str, Any] = {
            "raw_output": state.output.completion,
            "expected_covered": expected,
            "prompt_version": core.PROMPT_VERSION,
        }
        try:
            if state.output.stop_reason != "stop":
                raise ValueError(f"incomplete_output:{state.output.stop_reason}")
            user_messages = [message for message in state.messages if message.role == "user"]
            if len(user_messages) != 1 or not isinstance(user_messages[0].content, str):
                raise ValueError("Expected exactly one JSON user input")
            packet = json.loads(user_messages[0].content)
            result = core.parse_output(state.output.completion, payload=packet)
        except (ValueError, TypeError) as error:
            metadata.update(
                status="invalid_output", error=str(error), error_family="output_failure"
            )
            return Score(value={"correct": 0, "valid": 0}, metadata=metadata)
        decision = result["covered"]
        metadata.update(
            status="evaluated",
            covered=decision,
            result=result,
            false_positive=decision and not expected,
            false_negative=expected and not decision,
        )
        return Score(
            value={"correct": int(decision == expected), "valid": 1},
            answer=str(decision).lower(),
            explanation=result["reason"],
            metadata=metadata,
        )

    return score


def build_task(
    condition_id: str,
    samples: list[dict[str, Any]],
    labels: dict[str, bool],
    *,
    epochs: int = 3,
    provenance: dict[str, Any] | None = None,
    cost_limit: float | None = None,
    model_args: dict[str, Any] | None = None,
) -> Task:
    """Build isolated requests; callers own frozen inputs and hard budget preflight."""
    shared.validate_samples(samples, labels, epochs)
    config = generation_config(condition_id)
    prompt = core.system_prompt()
    dataset = []
    for sample in samples:
        sample_id = sample["sample_id"]
        packet = core.validate_input(sample["packet"])
        label = labels[sample_id]
        if type(label) is not bool:
            raise ValueError("Coverage labels must be Booleans")
        dataset.append(
            Sample(
                id=sample_id,
                input=[
                    ChatMessageSystem(content=prompt),
                    ChatMessageUser(
                        content=json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
                    ),
                ],
                target=str(label).lower(),
                metadata={
                    **{key: value for key, value in sample.items() if key != "packet"},
                    "payload_sha256": stable_json_sha256(packet),
                },
            )
        )
    return Task(
        name=f"required_support_coverage_{condition_id}",
        dataset=dataset,
        model=native_model(condition_id, **(model_args or {})),
        config=config,
        solver=generate(cache=False),
        scorer=coverage_score(),
        epochs=epochs,
        cost_limit=cost_limit,
        time_limit=150,
        metadata={
            **shared.task_metadata(
                "required_support_coverage", core.PROMPT_VERSION, prompt, core.output_json_schema()
            ),
            "input_schema_sha256": stable_json_sha256(core.input_json_schema()),
            "panel": provenance or {},
            "diagnostic_only": True,
        },
    )
