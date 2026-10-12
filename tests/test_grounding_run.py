"""CLI binding tests use invented records and mocks, never a model or service."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from er_commons import grounding_run
from er_commons.ollama_token_counter import (
    BINARY_SHA256,
    MODEL_BLOB_SHA256,
    MODEL_DIGEST,
    MODEL_NAME,
    RUNNER_SHA256,
    RUNTIME_VERSION,
)


def inputs(tmp_path: Path) -> tuple[Path, Path]:
    """Write pinned identity metadata using nonexistent assets that are never read."""
    settings = {
        "base_url": "http://127.0.0.1:11434/v1",
        "model": f"ollama/{MODEL_NAME}",
        "identity": {"digest": MODEL_DIGEST, "runtime_version": RUNTIME_VERSION},
        "context": 49152,
        "max_tokens": 1500,
        "timeout": 300,
    }
    config = {
        "base_url": "http://127.0.0.1:11434",
        "model": MODEL_NAME,
        "model_digest": MODEL_DIGEST,
        "runtime_version": RUNTIME_VERSION,
        "server_pid": 123,
        "binary_path": "/invented/ollama",
        "binary_sha256": BINARY_SHA256,
        "runner_path": "/invented/runner",
        "runner_sha256": RUNNER_SHA256,
        "model_blob_path": "/invented/model",
        "model_blob_sha256": MODEL_BLOB_SHA256,
    }
    settings_path, config_path = tmp_path / "settings.json", tmp_path / "counter.json"
    settings_path.write_text(json.dumps(settings))
    config_path.write_text(json.dumps(config))
    return settings_path, config_path


@pytest.mark.parametrize(
    "pipeline", ["single", "staged", "abstention", "staged_with_abstention", "points"]
)
def test_exact_counter_wiring_to_inspect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pipeline: str
) -> None:
    """Forward the same validated counter instance and digest to Inspect."""
    settings, config = inputs(tmp_path)
    manifest, output = tmp_path / "manifest.json", tmp_path / "output"
    rows = [
        {
            "sample_id": "fixture",
            "case_id": "invented",
            "scope": "invented_fixture",
            "packet": {},
            "expected_score": 2,
            "category": "control",
            "control": True,
        }
    ]
    loader = Mock(return_value=rows)
    counter = Mock(model_digest=MODEL_DIGEST)
    constructor = Mock(return_value=counter)
    logs = [SimpleNamespace(status="success")]
    evaluator = Mock(return_value=logs)
    monkeypatch.setattr(grounding_run, "load_panel_samples", loader)
    monkeypatch.setattr(grounding_run, "OllamaTokenCounter", constructor)
    target = {
        "single": "evaluate_grounding_samples",
        "staged": "evaluate_staged_samples",
        "abstention": "evaluate_abstention_samples",
        "staged_with_abstention": "evaluate_staged_samples",
        "points": "evaluate_staged_samples",
    }[pipeline]
    monkeypatch.setattr(grounding_run, target, evaluator)
    assert (
        grounding_run.evaluate_panel(manifest, "dev3", settings, config, output, pipeline=pipeline)
        == logs
    )
    loader.assert_called_once_with(manifest, "dev3")
    args = evaluator.call_args.kwargs
    assert args.get("check_abstention", False) == (pipeline == "staged_with_abstention")
    assert args.get("points_only", False) == (pipeline == "points")
    assert args["count_tokens"] is counter
    assert args["counter_model_digest"] == MODEL_DIGEST
    assert args["artifact_dir"] == output / "requests"
    assert args["log_dir"] == output / "inspect"
    assert constructor.call_args.kwargs["artifact_dir"] == output / "token_preflight"
    assert isinstance(constructor.call_args.args[0].binary_path, Path)
    counter.assert_not_called()
    assert not output.exists()


@pytest.mark.parametrize("field", ["model", "digest", "runtime_version", "base_url"])
def test_identity_mismatch_stops_before_inspect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    """An otherwise valid local configuration cannot count a different request identity."""
    settings_path, config = inputs(tmp_path)
    settings = json.loads(settings_path.read_text())
    if field in {"digest", "runtime_version"}:
        settings["identity"][field] = "different"
    elif field == "model":
        settings[field] = "ollama/different"
    else:
        settings[field] = "http://127.0.0.1:11435/v1"
    settings_path.write_text(json.dumps(settings))
    loader, evaluator, constructor = Mock(), Mock(), Mock()
    monkeypatch.setattr(grounding_run, "load_panel_samples", loader)
    monkeypatch.setattr(grounding_run, "evaluate_grounding_samples", evaluator)
    monkeypatch.setattr(grounding_run, "OllamaTokenCounter", constructor)
    with pytest.raises(ValueError, match="differ"):
        grounding_run.evaluate_panel(
            tmp_path / "unused", "dev3", settings_path, config, tmp_path / "out"
        )
    loader.assert_not_called()
    evaluator.assert_not_called()
    constructor.assert_not_called()


@pytest.mark.parametrize("change", ["extra", "missing_path", "nonobject", "relative_path"])
def test_invalid_counter_config(tmp_path: Path, change: str) -> None:
    """Fail malformed identity configuration without probing files or a network."""
    _, path = inputs(tmp_path)
    config = json.loads(path.read_text())
    if change == "extra":
        config["unknown"] = True
    elif change == "missing_path":
        del config["runner_path"]
    elif change == "relative_path":
        config["runner_path"] = "relative"
    else:
        config = []
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError):
        grounding_run.load_counter_config(path)


def test_cli_rejects_broad_panel_before_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    """No full19 or implicit all-development selection is exposed by the CLI."""
    runner = Mock()
    monkeypatch.setattr(grounding_run, "evaluate_panel", runner)
    monkeypatch.setattr(
        "sys.argv",
        [
            "grounding_run",
            "--manifest",
            "unused",
            "--settings",
            "unused",
            "--counter-config",
            "unused",
            "--output",
            "unused",
            "--panel",
            "full19",
        ],
    )
    with pytest.raises(SystemExit) as error:
        grounding_run.main()
    assert error.value.code == 2
    runner.assert_not_called()


def test_combined_dataset_routes_to_new_loader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Explicit new dataset binding selects the new loader, including incremental Dev6."""
    settings, config = inputs(tmp_path)
    loader, old_loader = Mock(return_value=[]), Mock()
    evaluator = Mock(return_value=[])
    monkeypatch.setattr(grounding_run, "load_dataset_panel_samples", loader)
    monkeypatch.setattr(grounding_run, "load_panel_samples", old_loader)
    monkeypatch.setattr(
        grounding_run, "OllamaTokenCounter", Mock(return_value=Mock(model_digest=MODEL_DIGEST))
    )
    monkeypatch.setattr(grounding_run, "evaluate_staged_samples", evaluator)
    grounding_run.evaluate_panel(
        tmp_path / "manifest",
        "dev6_additions",
        settings,
        config,
        tmp_path / "out",
        pipeline="staged_with_abstention",
        dataset_version="09a3",
    )
    loader.assert_called_once_with(tmp_path / "manifest", "dev6_additions")
    old_loader.assert_not_called()
    assert evaluator.call_args.kwargs["check_abstention"] is True
