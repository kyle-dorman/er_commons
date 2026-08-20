"""Typed, context-specific comparison of immutable qualification trees."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from er_commons.artifact_io import sha256_file
from er_commons.chunked_conversion.qualification.diagnostics import QualificationError

STABLE_ID = re.compile(r"(?:dconv1|prv1|exv1|hcorv1|docv1)-[0-9a-f]{64}")


QualificationDiagnosticError = QualificationError


@dataclass(frozen=True)
class PointerPattern:
    """One JSON pointer; ``*`` matches exactly one list or object segment."""

    value: str

    def matches(self, pointer: str) -> bool:
        """Return whether this pattern names the supplied concrete pointer."""
        expected = self.value.strip("/").split("/") if self.value != "/" else []
        actual = pointer.strip("/").split("/") if pointer != "/" else []
        return len(expected) == len(actual) and all(
            wanted == "*" or wanted == observed
            for wanted, observed in zip(expected, actual, strict=True)
        )


@dataclass(frozen=True)
class ArtifactPathRule:
    """Authorize root-prefix normalization at one declared JSON pointer."""

    pointer: PointerPattern
    marker: str


@dataclass(frozen=True)
class DigestReferenceRule:
    """Bind one digest field to one managed file in the same tree."""

    pointer: PointerPattern
    target: str


@dataclass(frozen=True)
class FileDifferencePolicy:
    """Explicitly authorize differences at semantic locations in one file."""

    ignored: tuple[PointerPattern, ...] = ()
    stable_identities: tuple[PointerPattern, ...] = ()
    artifact_paths: tuple[ArtifactPathRule, ...] = ()
    digest_references: tuple[DigestReferenceRule, ...] = ()


@dataclass(frozen=True)
class DifferencePolicy:
    """Map managed relative paths to their narrowly scoped difference rules."""

    files: dict[str, FileDifferencePolicy] = field(default_factory=dict)


@dataclass(frozen=True)
class TreeComparison:
    """Successful closed comparison of two trees."""

    file_count: int
    byte_exact_count: int


class _IdentityBijection:
    """Maintain one expected-to-actual ID relation across the complete tree."""

    def __init__(self) -> None:
        self.forward: dict[str, str] = {}
        self.reverse: dict[str, str] = {}

    def compare(self, expected: str, actual: str, path: str) -> None:
        """Compare string structure and extend the shared identity bijection."""
        left = list(STABLE_ID.finditer(expected))
        right = list(STABLE_ID.finditer(actual))
        if len(left) != len(right) or _without_ids(expected) != _without_ids(actual):
            _fail("stable_identity_shape", path, expected, actual)
        for expected_match, actual_match in zip(left, right, strict=True):
            expected_id = expected_match.group(0)
            actual_id = actual_match.group(0)
            if expected_id.split("-", 1)[0] != actual_id.split("-", 1)[0]:
                _fail("stable_identity_prefix", path, expected_id, actual_id)
            if self.forward.get(expected_id, actual_id) != actual_id:
                _fail("stable_identity_forward", path, self.forward[expected_id], actual_id)
            if self.reverse.get(actual_id, expected_id) != expected_id:
                _fail("stable_identity_reverse", path, self.reverse[actual_id], expected_id)
            self.forward[expected_id] = actual_id
            self.reverse[actual_id] = expected_id


def compare_trees(
    expected_root: Path,
    actual_root: Path,
    policy: DifferencePolicy,
    *,
    exclude: frozenset[str] = frozenset(),
) -> TreeComparison:
    """Compare exact file sets and declared JSON differences without writing artifacts."""
    expected_paths = _managed_paths(expected_root) - exclude
    actual_paths = _managed_paths(actual_root) - exclude
    if expected_paths != actual_paths:
        _fail("managed_file_set", "$", sorted(expected_paths), sorted(actual_paths))
    identities = _IdentityBijection()
    byte_exact_count = 0
    for relative in sorted(expected_paths):
        expected = expected_root / relative
        actual = actual_root / relative
        file_policy = policy.files.get(relative, FileDifferencePolicy())
        if expected.suffix in {".json", ".jsonl"}:
            _compare_value(
                _load_json(expected),
                _load_json(actual),
                f"{relative}#",
                file_policy,
                identities,
                expected_root,
                actual_root,
            )
        elif sha256_file(expected) != sha256_file(actual):
            _fail("exact_binary", relative, sha256_file(expected), sha256_file(actual))
        byte_exact_count += sha256_file(expected) == sha256_file(actual)
    unknown = sorted(set(policy.files) - expected_paths)
    if unknown:
        _fail("policy_file_exists", "$", [], unknown)
    return TreeComparison(len(expected_paths), byte_exact_count)


def _compare_value(
    expected: Any,
    actual: Any,
    path: str,
    policy: FileDifferencePolicy,
    identities: _IdentityBijection,
    expected_root: Path,
    actual_root: Path,
) -> None:
    pointer = path.split("#", 1)[1] or "/"
    if _matches(policy.ignored, pointer):
        return
    digest_rule = next(
        (rule for rule in policy.digest_references if rule.pointer.matches(pointer)), None
    )
    if digest_rule is not None:
        _verify_digest_reference(expected, expected_root, digest_rule.target, path)
        _verify_digest_reference(actual, actual_root, digest_rule.target, path)
        return
    if isinstance(expected, dict) and isinstance(actual, dict):
        if set(expected) != set(actual):
            _fail("json_object_keys", path, sorted(expected), sorted(actual))
        for key in sorted(expected):
            _compare_value(
                expected[key],
                actual[key],
                _child(path, key),
                policy,
                identities,
                expected_root,
                actual_root,
            )
        return
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            _fail("json_array_length", path, len(expected), len(actual))
        for index, (left, right) in enumerate(zip(expected, actual, strict=True)):
            _compare_value(
                left,
                right,
                _child(path, str(index)),
                policy,
                identities,
                expected_root,
                actual_root,
            )
        return
    if isinstance(expected, str) and isinstance(actual, str):
        path_rule = next(
            (rule for rule in policy.artifact_paths if rule.pointer.matches(pointer)), None
        )
        if path_rule is not None:
            expected = _normalize_artifact_path(expected, path_rule.marker, path)
            actual = _normalize_artifact_path(actual, path_rule.marker, path)
        if _matches(policy.stable_identities, pointer):
            identities.compare(expected, actual, path)
            return
    if type(expected) is not type(actual) or expected != actual:
        _fail("exact_json_value", path, expected, actual)


def _verify_digest_reference(value: Any, root: Path, target: str, path: str) -> None:
    if not isinstance(value, str):
        _fail("digest_reference_type", path, "sha256 string", value)
    target_path = root / target
    if not target_path.is_file() or sha256_file(target_path) != value:
        expected = sha256_file(target_path) if target_path.is_file() else target
        _fail("digest_reference_closure", path, expected, value)


def _load_json(path: Path) -> Any:
    try:
        if path.suffix == ".jsonl":
            return [json.loads(line) for line in path.read_text().splitlines()]
        return json.loads(path.read_bytes())
    except (OSError, ValueError, TypeError) as error:
        raise QualificationError(
            "valid_json",
            stage="semantic_comparison",
            path=path.as_posix(),
            expected="valid JSON",
            actual=str(error),
        ) from error


def _managed_paths(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def _normalize_artifact_path(value: str, marker: str, path: str) -> str:
    if marker not in value:
        _fail("artifact_path_marker", path, marker, value)
    return f"<artifact-root>{marker}{value.split(marker, 1)[1]}"


def _without_ids(value: str) -> str:
    return STABLE_ID.sub("<stable-id>", value)


def _matches(patterns: tuple[PointerPattern, ...], pointer: str) -> bool:
    return any(pattern.matches(pointer) for pattern in patterns)


def _child(path: str, segment: str) -> str:
    escaped = segment.replace("~", "~0").replace("/", "~1")
    return f"{path}/{escaped}"


def _fail(invariant: str, path: str, expected: object, actual: object) -> None:
    raise QualificationError(
        invariant,
        stage="semantic_comparison",
        path=path,
        expected=expected,
        actual=actual,
    )


__all__ = [
    "ArtifactPathRule",
    "DifferencePolicy",
    "DigestReferenceRule",
    "FileDifferencePolicy",
    "PointerPattern",
    "QualificationDiagnosticError",
    "TreeComparison",
    "compare_trees",
]
