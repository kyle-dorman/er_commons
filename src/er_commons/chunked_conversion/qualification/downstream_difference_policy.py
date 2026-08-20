"""Derive exact-pointer policy for reviewed downstream identity and observation drift."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import sha256_file
from er_commons.chunked_conversion.qualification.semantic_comparison import (
    STABLE_ID,
    ArtifactPathRule,
    DifferencePolicy,
    DigestReferenceRule,
    FileDifferencePolicy,
    PointerPattern,
)

OBSERVATION_FIELDS = frozenset(
    {
        "wall_seconds",
        "cpu_seconds",
        "inference_seconds",
        "pipeline_wall_seconds",
        "page_wall_seconds_sum",
        "started_at_utc",
        "finished_at_utc",
        "completed_at_utc",
        "generated_at_utc",
    }
)
OBSERVATION_RECORD_WORDS = (
    "observation",
    "timing",
    "resource",
    "completion",
    "summary",
    "report",
)
PATH_FIELDS = frozenset({"path", "relative_path", "artifact_root", "artifact_relative_root"})


@dataclass(frozen=True)
class PolicySummary:
    """Count each explicitly located difference kind for the sealed report."""

    ignored_observations: int
    stable_identities: int
    artifact_paths: int
    digest_references: int


@dataclass
class _Rules:
    ignored: list[PointerPattern]
    identities: list[PointerPattern]
    paths: list[ArtifactPathRule]
    digests: list[DigestReferenceRule]


def build_difference_policy(
    expected_root: Path,
    actual_root: Path,
    *,
    artifact_marker: str,
    exclude: frozenset[str] = frozenset(),
) -> tuple[DifferencePolicy, PolicySummary]:
    """Locate only typed, context-authorized differences at exact file pointers."""
    expected_files = _json_files(expected_root, exclude)
    actual_files = _json_files(actual_root, exclude)
    if set(expected_files) != set(actual_files):
        return DifferencePolicy(), PolicySummary(0, 0, 0, 0)
    expected_digests = _digest_targets(expected_root, exclude)
    actual_digests = _digest_targets(actual_root, exclude)
    policies: dict[str, FileDifferencePolicy] = {}
    totals = [0, 0, 0, 0]
    for relative in sorted(expected_files):
        rules = _Rules([], [], [], [])
        _locate(
            _load(expected_files[relative]),
            _load(actual_files[relative]),
            "/",
            relative,
            artifact_marker,
            expected_digests,
            actual_digests,
            rules,
        )
        if any((rules.ignored, rules.identities, rules.paths, rules.digests)):
            policies[relative] = FileDifferencePolicy(
                ignored=tuple(rules.ignored),
                stable_identities=tuple(rules.identities),
                artifact_paths=tuple(rules.paths),
                digest_references=tuple(rules.digests),
            )
        for index, count in enumerate(
            (len(rules.ignored), len(rules.identities), len(rules.paths), len(rules.digests))
        ):
            totals[index] += count
    return DifferencePolicy(policies), PolicySummary(*totals)


def _locate(
    expected: Any,
    actual: Any,
    pointer: str,
    relative: str,
    marker: str,
    expected_digests: dict[str, str],
    actual_digests: dict[str, str],
    rules: _Rules,
) -> None:
    if type(expected) is not type(actual) or expected == actual:
        return
    if isinstance(expected, dict) and isinstance(actual, dict) and set(expected) == set(actual):
        for key in sorted(expected):
            _locate(
                expected[key],
                actual[key],
                _child(pointer, key),
                relative,
                marker,
                expected_digests,
                actual_digests,
                rules,
            )
        return
    if isinstance(expected, list) and isinstance(actual, list) and len(expected) == len(actual):
        for index, (left, right) in enumerate(zip(expected, actual, strict=True)):
            _locate(
                left,
                right,
                _child(pointer, str(index)),
                relative,
                marker,
                expected_digests,
                actual_digests,
                rules,
            )
        return
    pattern = PointerPattern(pointer)
    if isinstance(expected, str) and isinstance(actual, str):
        target = _shared_digest_target(expected, actual, expected_digests, actual_digests)
        if target is not None:
            rules.digests.append(DigestReferenceRule(pattern, target))
        elif _stable_shape(expected, actual):
            rules.identities.append(pattern)
        elif _is_artifact_path(pointer, expected, actual, marker):
            rules.paths.append(ArtifactPathRule(pattern, marker))
        elif _is_observation(relative, pointer):
            rules.ignored.append(pattern)
    elif _is_observation(relative, pointer):
        rules.ignored.append(pattern)


def _is_observation(relative: str, pointer: str) -> bool:
    leaf = pointer.rsplit("/", 1)[-1]
    filename = Path(relative).name.lower()
    context = "/".join(pointer.lower().split("/")[:-1])
    return leaf in OBSERVATION_FIELDS and (
        any(word in filename for word in OBSERVATION_RECORD_WORDS)
        or any(word in context for word in OBSERVATION_RECORD_WORDS)
    )


def _is_artifact_path(pointer: str, left: str, right: str, marker: str) -> bool:
    leaf = pointer.rsplit("/", 1)[-1]
    return (
        leaf in PATH_FIELDS
        and marker in left
        and marker in right
        and left.split(marker, 1)[1] == right.split(marker, 1)[1]
    )


def _stable_shape(left: str, right: str) -> bool:
    left_ids = STABLE_ID.findall(left)
    right_ids = STABLE_ID.findall(right)
    return (
        bool(left_ids)
        and len(left_ids) == len(right_ids)
        and (STABLE_ID.sub("<id>", left) == STABLE_ID.sub("<id>", right))
    )


def _shared_digest_target(
    left: str, right: str, left_targets: dict[str, str], right_targets: dict[str, str]
) -> str | None:
    left_target = left_targets.get(left)
    return (
        left_target if left_target is not None and right_targets.get(right) == left_target else None
    )


def _json_files(root: Path, excluded: frozenset[str]) -> dict[str, Path]:
    return {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in {".json", ".jsonl"}
        and path.relative_to(root).as_posix() not in excluded
    }


def _digest_targets(root: Path, excluded: frozenset[str]) -> dict[str, str]:
    return {
        sha256_file(path): path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.relative_to(root).as_posix() not in excluded
    }


def _load(path: Path) -> Any:
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text().splitlines()]
    return json.loads(path.read_bytes())


def _child(pointer: str, segment: str) -> str:
    escaped = segment.replace("~", "~0").replace("/", "~1")
    return f"/{escaped}" if pointer == "/" else f"{pointer}/{escaped}"


__all__ = ["PolicySummary", "build_difference_policy"]
