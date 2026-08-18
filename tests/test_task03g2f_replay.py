"""Offline behavior and human-ownership checks for the Task 03G.2f replay."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from er_commons.task03g2f_replay.audit import (
    validate_local_ownership,
    validate_main_deferrals,
)
from er_commons.task03g2f_replay.config import ReplayPaths
from er_commons.task03g2f_replay.errors import ReplayValidationError
from er_commons.task03g2f_replay.inventory import (
    DirectoryInventory,
    require_unchanged,
)
from er_commons.task03g2f_replay.table_audit import TableDelta

RUNTIME_ROOT = Path("src/er_commons/task03g2f_replay")


def test_replay_modules_fit_one_named_responsibility() -> None:
    """The replay stays navigable without opening a monolithic run script."""
    for path in RUNTIME_ROOT.glob("*.py"):
        source = path.read_text()
        assert len(source.splitlines()) <= 220, f"split the responsibilities in {path.name}"
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 60, f"split {path.name}:{node.name} ({length} lines)"

    for path in (
        Path("src/er_commons/corpus_extraction/downstream_replay.py"),
        Path("src/er_commons/corpus_extraction/downstream_replay_validation.py"),
    ):
        source = path.read_text()
        assert len(source.splitlines()) <= 220, f"split the responsibilities in {path.name}"
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 60, f"split {path.name}:{node.name} ({length} lines)"


def test_cli_is_a_portable_application_shell() -> None:
    """The operator-facing script contains no artifact policy or machine path."""
    source = Path("scripts/run_task03g2f_downstream_replay.py").read_text()
    assert len(source.splitlines()) <= 60
    assert "/Volumes/" not in source
    assert "Task03G2FReplay(paths).execute()" in source


def test_paths_derive_from_explicit_project_and_data_roots(tmp_path: Path) -> None:
    """A checkout or artifact root can move without editing replay code."""
    paths = ReplayPaths(tmp_path / "project", tmp_path / "artifacts", "scopev1-test")
    assert paths.document_spec.is_relative_to(paths.project_root)
    assert paths.retained_bundle.is_relative_to(paths.data_root)
    assert paths.retained_bundle.parts[-2:] == ("scopev1-test", "contract_bundle.json")


def test_main_deferrals_preserve_catalog_selected_source_identity() -> None:
    """Deferred mentions remain immutable while carrying intended source IDs."""
    rows = [_deferred("appendix d", "deir_appendix_d", number) for number in range(8)] + [
        _deferred("appendix p", "deir_appendix_p", number) for number in range(10)
    ]
    assert validate_main_deferrals(rows) == {"appendix d": 8, "appendix p": 10}

    rows[0]["cross_document_evidence"] = {"intended_target_source_ids": ["wrong"]}
    with pytest.raises(ReplayValidationError) as failure:
        validate_main_deferrals(rows)
    assert failure.value.detail.code == "MAIN_INTENDED_SOURCE"
    assert failure.value.detail.context["mention_id"] == "appendix d-0"


def test_local_and_external_dispositions_are_independently_audited() -> None:
    """Local Appendix D mentions are not relabeled as cross-document mentions."""
    rows = {
        "deir_appendix_p": [
            {
                "mention_class": "appendix",
                "lookup_key": "appendix d",
                "resolution_status": "resolved",
            },
            {
                "mention_class": "appendix",
                "lookup_key": "appendix d",
                "resolution_status": "resolved",
            },
            {"unresolved_reason": "external_document_outside_corpus"},
        ],
        "deir_appendix_d": [
            {
                "mention_class": "appendix",
                "lookup_key": "appendix a",
                "unresolved_reason": "no_local_alias",
            },
            {
                "mention_class": "appendix",
                "lookup_key": "appendix a",
                "unresolved_reason": "no_local_alias",
            },
        ],
    }
    assert validate_local_ownership(rows) == (2, 2, 1)


def test_attempt_inventory_failure_is_structured_for_debugging() -> None:
    """Attempt isolation failures expose a stable code and before/after values."""
    before = {"documents": DirectoryInventory(True, 1, "a")}
    after = {"documents": DirectoryInventory(True, 2, "b")}
    with pytest.raises(ReplayValidationError) as failure:
        require_unchanged(before, after, operation="test")
    assert failure.value.detail.code == "ATTEMPT_INVENTORY_CHANGED"
    assert failure.value.detail.context["operation"] == "test"


def test_reviewed_table_delta_is_named_data_not_an_inline_literal() -> None:
    """The candidate-neutral expectation is directly inspectable and testable."""
    expected = TableDelta.expected()
    assert expected.newly_resolved_distances == (6, 6, 6, 7, 7, 8)
    assert expected.previously_resolved_changed == 0


def _deferred(alias: str, source_id: str, number: int) -> dict[str, object]:
    return {
        "id": f"{alias}-{number}",
        "lookup_key": alias,
        "unresolved_reason": "deferred_cross_document",
        "cross_document_evidence": {"intended_target_source_ids": [source_id]},
    }
