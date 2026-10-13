"""Maintained cloud configurations reject silent settings drift before dispatch."""

import copy
import json
from pathlib import Path

import pytest

from er_commons.grounding_provider_config import Condition, load_conditions

CONFIG = Path("configs/grounding_judges_v1.json")


def test_selected_cloud_settings_are_explicit():
    """The reusable profile carries the tested medium/cache settings for all three models."""
    conditions = load_conditions(CONFIG)
    assert list(conditions) == ["fireworks_glm", "openai_generation", "anthropic_generation"]
    assert all(c.settings["reasoning_effort"] == "medium" for c in conditions.values())
    assert conditions["fireworks_glm"].settings["fireworks_evidence_cache_prefix"] is True


@pytest.mark.parametrize(
    "mutation", ["empty", "duplicate", "typo", "endpoint", "api", "effort", "credential", "retired"]
)
def test_configuration_rejects_ambiguous_or_ignored_settings(tmp_path, mutation):
    """Bad configuration fails before provider requests or artifact creation."""
    data = json.loads(CONFIG.read_text())
    first = data["conditions"][0]
    if mutation == "empty":
        data["conditions"] = []
    elif mutation == "duplicate":
        data["conditions"].append(copy.deepcopy(first))
    elif mutation == "typo":
        first["settings"]["reasoning_efort"] = "medium"
    elif mutation == "endpoint":
        first["endpoint"] += "/wrong"
    elif mutation == "api":
        first["api"] = "openai_responses"
    elif mutation == "effort":
        data["conditions"][1]["settings"]["reasoning_effort"] = "typo"
    elif mutation == "credential":
        first["credential_env"] = "not an environment name"
    elif mutation == "retired":
        first["id"] = "local_clef"
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        load_conditions(path)


def test_single_provider_configuration_is_supported(tmp_path):
    """A repeated benchmark run need not configure unused models."""
    data = json.loads(CONFIG.read_text())
    data["conditions"] = data["conditions"][:1]
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data))
    assert list(load_conditions(path)) == ["fireworks_glm"]


@pytest.mark.parametrize(
    "options",
    [None, {"mode": "typo", "ttl": "30m"}, {"mode": "implicit", "ttl": "30m", "typo": True}],
)
def test_invalid_cache_options_rejected_without_breakpoint(options):
    """Cache options are checked even when evidence splitting is disabled."""
    data = load_conditions(CONFIG)["openai_generation"].model_dump()
    data["settings"].pop("evidence_cache_breakpoint")
    data["settings"]["prompt_cache_options"] = options
    with pytest.raises(ValueError):
        Condition.model_validate(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("reasoning_effort", []),
        ("reasoning_effort", {}),
        ("prompt_cache_options", {"mode": [], "ttl": "30m"}),
    ],
)
def test_malformed_setting_types_raise_validation_error(field, value):
    """Invalid container values never escape validation as an unhandled TypeError."""
    data = load_conditions(CONFIG)["openai_generation"].model_dump()
    data["settings"].pop("evidence_cache_breakpoint")
    data["settings"][field] = value
    with pytest.raises(ValueError):
        Condition.model_validate(data)
