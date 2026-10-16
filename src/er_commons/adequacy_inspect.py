"""Native Inspect execution for the retained independent adequacy judges.

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

from er_commons import adequacy_binary as core
from er_commons import judge_inspect as shared

REPO = Path(__file__).resolve().parents[2]
VERSIONS = {
    "C": core.CONCLUSION_COMPARISON_REASON_PROMPT_VERSION,
    "S": core.SUPPORT_BASIS_PROMPT_VERSION,
}
PROVIDERS = shared.PROVIDERS


def generation_config(condition_id: str, component: core.Component) -> GenerateConfig:
    """Apply shared native settings to the selected component schema."""
    return shared.generation_config(
        condition_id,
        component,
        core.system_prompt(component, prompt_version=VERSIONS[component]),
        core.output_json_schema(component, prompt_version=VERSIONS[component]),
        f"adequacy_binary_{component}",
    )


def native_model(condition_id: str, component: core.Component, **model_args: Any) -> Model:
    """Construct the shared native provider without changing component semantics."""
    return shared.native_model(
        condition_id,
        component,
        core.system_prompt(component, prompt_version=VERSIONS[component]),
        generation_config(condition_id, component),
        **model_args,
    )


@scorer(metrics={"correct": [mean()], "valid": [mean()]})
def adequacy_score(component: core.Component) -> Scorer:
    """Retain raw text and quotation diagnostics independently of binary agreement."""

    async def score(state: TaskState, target: Target) -> Score:
        if target.text not in {"yes", "no"}:
            raise ValueError("Expected target must be yes or no")
        raw = state.output.completion
        metadata: dict[str, Any] = {"raw_output": raw, "prompt_version": VERSIONS[component]}
        if component == "C":
            metadata["quotation_fidelity"] = core.quote_fidelity_diagnostics(
                raw, state.metadata["packet"]
            )
        if state.output.stop_reason == "max_tokens":
            metadata.update(status="invalid_output", error_type="truncated_output")
            return Score(value={"correct": 0, "valid": 0}, answer=raw, metadata=metadata)
        try:
            result = core.parse_output(component, raw, prompt_version=VERSIONS[component])
        except (ValueError, TypeError) as error:
            metadata.update(status="invalid_output", error_type=type(error).__name__)
            return Score(value={"correct": 0, "valid": 0}, answer=raw, metadata=metadata)
        decision = result["conclusion_adequate" if component == "C" else "support_sufficient"]
        metadata.update(status="evaluated", decision=decision, result=result)
        return Score(
            value={"correct": int(decision == (target.text == "yes")), "valid": 1},
            answer="yes" if decision else "no",
            explanation=result["explanation"],
            metadata=metadata,
        )

    return score


def build_task(
    condition_id: str,
    component: core.Component,
    samples: list[dict[str, Any]],
    labels: dict[str, bool],
    *,
    epochs: int = 1,
    cost_limit: float | None = None,
) -> Task:
    """Create a one-generation task; cost_limit is Inspect's per-sample soft limit."""
    if component not in VERSIONS:
        raise ValueError("Unknown component")
    shared.validate_samples(samples, labels, epochs)
    selected_condition(component)
    prompt = core.system_prompt(component, prompt_version=VERSIONS[component])
    dataset = []
    for sample in samples:
        packet = core.validate_input(component, sample["packet"])
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
                        content=json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
                    ),
                ],
                target="yes" if labels[sample["sample_id"]] else "no",
                metadata={"packet": packet, "case_id": sample["case_id"]},
            )
        )
    return Task(
        name=f"adequacy_{component}_{condition_id}",
        dataset=dataset,
        model=native_model(condition_id, component),
        config=generation_config(condition_id, component),
        solver=generate(cache=False),
        scorer=adequacy_score(component),
        epochs=epochs,
        cost_limit=cost_limit,
        time_limit=150,
        metadata=shared.task_metadata(
            component,
            VERSIONS[component],
            prompt,
            core.output_json_schema(component, prompt_version=VERSIONS[component]),
        ),
    )


@task
def adequacy(
    condition_id: str | None = None,
    component: core.Component = "C",
    panel: str = "calibration",
) -> Task:
    """Use the locked C/S selection by default; explicit profiles support historical work."""
    if condition_id is None:
        condition_id = selected_condition(component)
    if panel == "calibration":
        from er_commons.adequacy_calibration import load_panel

        samples, labels, _ = load_panel(component)
    elif panel == "full_development":
        from er_commons.adequacy_binary_development import load_full_development

        samples, labels, _ = load_full_development(component)
    else:
        raise ValueError("panel must be calibration or full_development")
    return build_task(condition_id, component, samples, labels)


def selected_condition(component: core.Component) -> str:
    """Validate the selected component identity before default dispatch."""
    if component not in VERSIONS:
        raise ValueError("Unknown component")
    return shared.selected_condition(
        component,
        VERSIONS[component],
        core.system_prompt(component, prompt_version=VERSIONS[component]),
        core.output_json_schema(component, prompt_version=VERSIONS[component]),
    )
