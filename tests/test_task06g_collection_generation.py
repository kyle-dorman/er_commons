"""Regression checks for the v38 full-replay control replacement."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.task06g.collection_generation import (
    check_collection_generation,
    generate_collection_configs,
)

ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "configs/task06/v4"
RECIPE = CONFIG / "task06g_generation_v1.json"


def test_collection_generator_preserves_historical_v38_owner_packet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Require the executed packet to report post-execution finalizer drift."""
    original = Path.open

    def guarded(path: Path, *args: object, **kwargs: object):
        assert path.suffix.lower() not in {".pdf", ".png", ".pt", ".bin", ".safetensors"}
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    with pytest.raises(ValueError, match=r"generator differs: .*finaliz"):
        check_collection_generation(RECIPE)


def test_v38_packet_has_full_descendant_graph_and_no_imported_selection() -> None:
    """Reject the superseded four-command collection-only v38 recipe."""
    execution = json.loads((CONFIG / "task06g_execution_v1.json").read_bytes())
    recipe = json.loads(RECIPE.read_bytes())
    assert execution["command_order"] == [
        "document_feir_appendix_f1",
        "document_deir_appendix_a",
        "document_deir_main",
        "resolve_relink_specs",
        "relink_and_assemble",
        "resolve_comparison_specs",
        "publish_comparison",
        "validate_handoff",
    ]
    assert list(recipe["phases"]) == ["initial", "relink", "comparison"]
    assert not (CONFIG / "task06g_collection_only_v1.json").exists()
    assert not (CONFIG / "task06g_imported_document_selection_v1.json").exists()


def test_v38_packet_pins_namespace_resource_and_preserved_ledger() -> None:
    """Bind the authorized namespace, 52-GiB ceiling, and prior attempts."""
    execution = json.loads((CONFIG / "task06g_execution_v1.json").read_bytes())
    recipe = json.loads(RECIPE.read_bytes())
    assert recipe["tmux_session"] == "er-commons-06g-replay-v38"
    assert execution["resource_limits"]["max_output_bytes"] == 52 * 1024**3
    rendered = json.dumps({"recipe": recipe, "execution": execution})
    assert "replay_v38" in rendered
    for value in (
        "replay_v32",
        "execution_attempt_v16",
        "replay_v35",
        "execution_attempt_v17",
        "replay_v36",
        "replay_v37",
        "execution_attempt_v19",
    ):
        assert value in rendered


def test_v38_full_controls_are_check_only() -> None:
    """Prevent the retired collection-only generator from rewriting v38."""
    with pytest.raises(ValueError, match="check-only"):
        generate_collection_configs(ROOT, check=False)
