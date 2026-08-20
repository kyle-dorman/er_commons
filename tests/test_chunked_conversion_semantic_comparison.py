"""Focused tests for the human-owned offline semantic comparator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.artifact_io import sha256_file
from er_commons.chunked_conversion.qualification.semantic_comparison import (
    ArtifactPathRule,
    DifferencePolicy,
    DigestReferenceRule,
    FileDifferencePolicy,
    PointerPattern,
    QualificationDiagnosticError,
    compare_trees,
)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")


def _stable(prefix: str, token: str) -> str:
    return f"{prefix}-{token * 64}"


def test_ignored_difference_is_authorized_only_at_its_pointer(tmp_path: Path) -> None:
    expected, actual = tmp_path / "expected", tmp_path / "actual"
    _write(expected / "record.json", {"observation": {"wall": 1}, "semantic": {"wall": 1}})
    _write(actual / "record.json", {"observation": {"wall": 9}, "semantic": {"wall": 1}})
    policy = DifferencePolicy(
        {"record.json": FileDifferencePolicy(ignored=(PointerPattern("/observation/wall"),))}
    )

    assert compare_trees(expected, actual, policy).byte_exact_count == 0

    _write(actual / "record.json", {"observation": {"wall": 9}, "semantic": {"wall": 9}})
    with pytest.raises(QualificationDiagnosticError) as caught:
        compare_trees(expected, actual, policy)
    assert caught.value.path == "record.json#/semantic/wall"
    assert caught.value.code == "exact_json_value"


def test_identity_bijection_is_shared_across_files(tmp_path: Path) -> None:
    expected, actual = tmp_path / "expected", tmp_path / "actual"
    accepted = _stable("exv1", "a")
    replacement = _stable("exv1", "b")
    for root, identity in ((expected, accepted), (actual, replacement)):
        _write(root / "owner.json", {"id": identity})
        _write(root / "reference.json", {"owner": identity})
    rules = FileDifferencePolicy(stable_identities=(PointerPattern("/*"),))
    policy = DifferencePolicy({"owner.json": rules, "reference.json": rules})

    compare_trees(expected, actual, policy)

    _write(actual / "reference.json", {"owner": _stable("exv1", "c")})
    with pytest.raises(QualificationDiagnosticError, match="stable_identity_forward"):
        compare_trees(expected, actual, policy)


def test_artifact_root_normalization_requires_declared_path_field(tmp_path: Path) -> None:
    expected, actual = tmp_path / "expected", tmp_path / "actual"
    marker = "/documents/source/"
    _write(expected / "record.json", {"path": f"pipelines/accepted{marker}x.json", "note": "same"})
    _write(actual / "record.json", {"path": f"pipelines/new{marker}x.json", "note": "same"})
    policy = DifferencePolicy(
        {
            "record.json": FileDifferencePolicy(
                artifact_paths=(ArtifactPathRule(PointerPattern("/path"), marker),)
            )
        }
    )
    compare_trees(expected, actual, policy)

    _write(
        actual / "record.json", {"path": f"pipelines/new{marker}x.json", "note": f"new{marker}x"}
    )
    with pytest.raises(QualificationDiagnosticError) as caught:
        compare_trees(expected, actual, policy)
    assert caught.value.path == "record.json#/note"


def test_digest_difference_must_close_over_declared_target(tmp_path: Path) -> None:
    expected, actual = tmp_path / "expected", tmp_path / "actual"
    _write(expected / "target.json", {"id": _stable("docv1", "a")})
    _write(actual / "target.json", {"id": _stable("docv1", "b")})
    _write(expected / "reference.json", {"sha256": sha256_file(expected / "target.json")})
    _write(actual / "reference.json", {"sha256": sha256_file(actual / "target.json")})
    policy = DifferencePolicy(
        {
            "target.json": FileDifferencePolicy(stable_identities=(PointerPattern("/id"),)),
            "reference.json": FileDifferencePolicy(
                digest_references=(DigestReferenceRule(PointerPattern("/sha256"), "target.json"),)
            ),
        }
    )
    compare_trees(expected, actual, policy)

    _write(actual / "reference.json", {"sha256": "f" * 64})
    with pytest.raises(QualificationDiagnosticError) as caught:
        compare_trees(expected, actual, policy)
    assert caught.value.code == "digest_reference_closure"


def test_unknown_policy_file_fails_closed(tmp_path: Path) -> None:
    expected, actual = tmp_path / "expected", tmp_path / "actual"
    _write(expected / "record.json", {"value": 1})
    _write(actual / "record.json", {"value": 1})
    policy = DifferencePolicy({"missing.json": FileDifferencePolicy()})

    with pytest.raises(QualificationDiagnosticError, match="policy_file_exists"):
        compare_trees(expected, actual, policy)
