"""Derive immutable numbering levels and local level-transfer evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

JsonRecord = dict[str, Any]


@dataclass(frozen=True)
class LevelEvidence:
    """Precomputed absolute levels and R07 transfer proposals."""

    numbering_levels: dict[str, int]
    supported_levels: dict[str, int]
    transfers: dict[str, tuple[int | None, str]]


def derive_level_evidence(
    *,
    features: Sequence[Mapping[str, Any]],
    toc_targets: dict[str, tuple[str, int]],
    regimes: Mapping[str, Mapping[str, Any]],
) -> LevelEvidence:
    """Build all level evidence once from immutable feature records."""
    article_regimes = {
        item["regime_id"] for item in features if item["numbering_kind"] == "article"
    }
    numbering_levels = calibrated_numbering_levels(features, toc_targets, regimes, article_regimes)
    supported: dict[str, int] = {}
    for feature in features:
        key = feature["stable_item_key"]
        if feature["outline_state"] == "unique_exact":
            if feature["outline_level"] is None:
                raise ValueError(f"unique outline anchor lacks effective level: {key}")
            supported[key] = int(feature["outline_level"])
        elif key in toc_targets:
            supported[key] = toc_targets[key][1]
        elif key in numbering_levels:
            supported[key] = numbering_levels[key]
    return LevelEvidence(
        numbering_levels=numbering_levels,
        supported_levels=supported,
        transfers=_local_level_transfers(features, supported),
    )


def calibrated_numbering_levels(
    features: Sequence[Mapping[str, Any]],
    toc_targets: dict[str, tuple[str, int]],
    regimes: Mapping[str, Mapping[str, Any]],
    article_regimes: set[str],
) -> dict[str, int]:
    """Calibrate R05 levels from the nearest earlier immutable anchor."""
    levels: dict[str, int] = {}
    immutable_anchors: dict[str, list[tuple[int, int]]] = {}
    for feature in features:
        key = feature["stable_item_key"]
        fallback = _numbering_level(feature, regimes, article_regimes)
        if fallback is None:
            continue
        regime_id = feature["regime_id"]
        depth = int(feature["numbering_depth"])
        anchors = immutable_anchors.setdefault(regime_id, [])
        levels[key] = anchors[-1][0] - anchors[-1][1] + depth if anchors else fallback

        absolute_level: int | None = None
        if feature["outline_state"] == "unique_exact":
            outline_level = feature["outline_level"]
            if not isinstance(outline_level, int):
                raise ValueError(f"unique outline anchor lacks effective level: {key}")
            absolute_level = outline_level
        elif key in toc_targets:
            absolute_level = toc_targets[key][1]
        if absolute_level is not None:
            levels[key] = absolute_level
            anchors.append((absolute_level, depth))
    return levels


def _numbering_level(
    feature: Mapping[str, Any],
    regimes: Mapping[str, Mapping[str, Any]],
    article_regimes: set[str],
) -> int | None:
    if feature["raw_role"] != "section_header":
        return None
    kind = feature["numbering_kind"]
    depth = feature["numbering_depth"]
    if kind in {"none", "bullet"} or depth is None:
        return None
    if kind in {"upper_alpha", "upper_roman"} and feature["regime_id"] not in article_regimes:
        return None
    return int(regimes[feature["regime_id"]]["root_level"]) + int(depth) - 1


def _local_level_transfers(
    features: Sequence[Mapping[str, Any]], supported: dict[str, int]
) -> dict[str, tuple[int | None, str]]:
    transfers: dict[str, tuple[int | None, str]] = {}
    for index, feature in enumerate(features):
        if feature["raw_role"] != "section_header" or feature["numbering_kind"] != "none":
            continue
        earlier_index = next(
            (
                cursor
                for cursor in range(index - 1, -1, -1)
                if features[cursor]["stable_item_key"] in supported
            ),
            None,
        )
        if earlier_index is None:
            continue
        earlier = features[earlier_index]
        earlier_level = supported[earlier["stable_item_key"]]
        raw_level = feature["raw_level"]
        unsupported = not isinstance(raw_level, int) or not 1 <= raw_level <= 6
        unsupported = unsupported or raw_level > earlier_level + 1
        if not unsupported:
            continue
        later_index = next(
            (
                cursor
                for cursor in range(index + 1, len(features))
                if features[cursor]["stable_item_key"] in supported
            ),
            len(features),
        )
        cluster = [
            item
            for item in features[earlier_index + 1 : later_index]
            if item["raw_role"] == "section_header" and item["numbering_kind"] == "none"
        ]
        if (
            len(cluster) < 2
            or max(item["left_pt"] for item in cluster) - min(item["left_pt"] for item in cluster)
            > 1
        ):
            continue
        later = features[later_index] if later_index < len(features) else None
        transferred = None
        detail = "unsupported local heading cluster lacks compatible later support"
        if later is not None:
            later_level = supported[later["stable_item_key"]]
            aligned = all(abs(item["left_pt"] - later["left_pt"]) <= 1 for item in cluster)
            if earlier_level == later_level - 1 and aligned:
                transferred = later_level
                detail = "local heading level transferred from bounding supported headings"
        for item in cluster:
            transfers[item["stable_item_key"]] = (transferred, detail)
    return transfers
