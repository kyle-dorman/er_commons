"""Run an explicitly authorized frozen panel through Inspect and exact preflight.

Usage: ``python -m er_commons.grounding_run --manifest MANIFEST --panel dev3
--settings SETTINGS --counter-config COUNTER_CONFIG --output EXTERNAL_DIRECTORY``.
The pinned Ollama service must already be running; this command manages no service.
Use ``grounding_preflight`` for offline gate recording without inference.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from inspect_ai.log import EvalLog

from er_commons.grounding_abstention_inspect import evaluate_abstention_samples
from er_commons.grounding_dataset_panel import load_dataset_panel_samples
from er_commons.grounding_inspect import evaluate_grounding_samples
from er_commons.grounding_panel import load_panel_samples
from er_commons.grounding_records import SavedGroundingSample
from er_commons.grounding_staged_inspect import evaluate_staged_samples
from er_commons.judge_qualification import validate_settings
from er_commons.ollama_token_counter import OllamaCounterConfig, OllamaTokenCounter


def load_counter_config(path: Path) -> OllamaCounterConfig:
    """Decode explicit counter identity and convert only its three local asset paths."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Counter configuration must be an object")
    for field in ("binary_path", "runner_path", "model_blob_path"):
        if not isinstance(value.get(field), str):
            raise ValueError(f"Counter configuration requires string {field}")
        value[field] = Path(value[field])
    try:
        config = OllamaCounterConfig(**value)
    except TypeError as error:
        raise ValueError(f"Invalid counter configuration fields: {error}") from error
    config.validate()
    return config


def validate_counter_settings(settings: dict[str, Any], config: OllamaCounterConfig) -> None:
    """Require counting and generation to address the same pinned model and runtime."""
    validate_settings(settings)
    config.validate()
    base_url = settings["base_url"].rstrip("/").removesuffix("/v1")
    if (
        settings["model"] != f"ollama/{config.model}"
        or settings["identity"]["digest"] != config.model_digest
        or settings["identity"]["runtime_version"] != config.runtime_version
        or base_url != config.base_url.rstrip("/").removesuffix("/v1")
    ):
        raise ValueError("Counter and generation model, digest, runtime or endpoint differ")


def evaluate_panel(
    manifest: Path,
    panel: str,
    settings_path: Path,
    counter_config_path: Path,
    output: Path,
    *,
    pipeline: str = "single",
    dataset_version: str = "original",
) -> list[EvalLog]:
    """Validate identity before loading the fixed panel or starting Inspect execution."""
    if pipeline not in {"single", "staged", "abstention", "staged_with_abstention", "points"}:
        raise ValueError("Unknown grounding pipeline")
    if dataset_version not in {"original", "09a3"}:
        raise ValueError("Unknown grounding dataset version")
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    if not isinstance(settings, dict):
        raise ValueError("Generation settings must be an object")
    config = load_counter_config(counter_config_path)
    validate_counter_settings(settings, config)
    loader = load_dataset_panel_samples if dataset_version == "09a3" else load_panel_samples
    samples = [SavedGroundingSample.model_validate(row) for row in loader(manifest, panel)]
    counter = OllamaTokenCounter(config, artifact_dir=output / "token_preflight")
    evaluator = {
        "single": evaluate_grounding_samples,
        "staged": evaluate_staged_samples,
        "abstention": evaluate_abstention_samples,
        "staged_with_abstention": evaluate_staged_samples,
        "points": evaluate_staged_samples,
    }[pipeline]
    options: dict[str, Any] = (
        {"check_abstention": True} if pipeline == "staged_with_abstention" else {}
    )
    if pipeline == "points":
        options["points_only"] = True
    return evaluator(
        samples,
        settings=settings,
        artifact_dir=output / "requests",
        log_dir=output / "inspect",
        count_tokens=counter,
        counter_model_digest=counter.model_digest,
        **options,
    )


def main() -> None:
    """Require explicit panel, counter and output paths without a fallback counter."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "settings", "counter-config", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--panel", choices=("dev3", "dev6", "dev6_additions"), required=True)
    parser.add_argument(
        "--pipeline",
        choices=("single", "staged", "abstention", "staged_with_abstention", "points"),
        default="single",
    )
    parser.add_argument("--dataset-version", choices=("original", "09a3"), default="original")
    args = parser.parse_args()
    try:
        logs = evaluate_panel(
            args.manifest,
            args.panel,
            args.settings,
            args.counter_config,
            args.output,
            pipeline=args.pipeline,
            dataset_version=args.dataset_version,
        )
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    if not logs or any(log.status != "success" for log in logs):
        raise SystemExit("Inspect grounding evaluation failed; inspect the saved log")


if __name__ == "__main__":
    main()
