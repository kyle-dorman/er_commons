"""Read only the two historical document-product roles needed by v1 reports."""

from __future__ import annotations

from typing import Any, Literal

LegacyProduct = Literal["stable_content_evidence", "hierarchy_decisions"]

_V1_ROLE = {
    "stable_content_evidence": "baseline_producer",
    "hierarchy_decisions": "hierarchy_correction",
}


def legacy_product_completion(identity: dict[str, Any], product: LegacyProduct) -> dict[str, Any]:
    """Read one allowlisted v1 stage role without adapting it into v2 evidence."""
    stages = identity.get("stage_completions")
    if not isinstance(stages, dict):
        raise ValueError("legacy document identity has no stage completions")
    value = stages.get(_V1_ROLE[product])
    if not isinstance(value, dict):
        raise ValueError(f"legacy document identity lacks {_V1_ROLE[product]}")
    return value


__all__ = ["legacy_product_completion"]
