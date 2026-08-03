"""Tests for the Typer workspace-inspection CLI and typed project settings."""

import pytest
from typer.testing import CliRunner

from er_commons.cli import (
    DEFAULT_CANONICALIZATION_SPEC,
    DEFAULT_COMPLETE_DOCUMENT_SPEC,
    DEFAULT_SEMANTIC_MATERIALIZATION_SPEC,
    app,
)
from er_commons.settings import ProjectSettings


def test_data_root_honors_environment_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment settings take precedence over the local checkout's .env file."""
    monkeypatch.setenv("ER_COMMONS_DATA_ROOT", "/tmp/er-commons-test")

    assert ProjectSettings().data_root.as_posix() == "/tmp/er-commons-test"


def test_paths_reports_expected_subdirectories(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI exposes the three external roots documented for users and agents."""
    monkeypatch.setenv("ER_COMMONS_DATA_ROOT", "/tmp/er-commons-test")

    result = CliRunner().invoke(app, ["paths"])

    assert result.exit_code == 0
    assert "ceqa_dataset=/tmp/er-commons-test/datasets/ceqa" in result.output
    assert "pipeline_artifacts=/tmp/er-commons-test/pipelines" in result.output
    assert "benchmark_artifacts=/tmp/er-commons-test/benchmarks/er_bench" in result.output


def test_tables_group_exposes_only_retained_pipeline_runs() -> None:
    """The CLI omits superseded exploratory table-pilot commands."""
    result = CliRunner().invoke(app, ["tables", "--help"])

    assert result.exit_code == 0
    assert "run-review" in result.output
    assert "run-first-600" in result.output
    assert "task03a1" not in result.output


def test_documents_group_exposes_review_and_complete_producer_commands() -> None:
    """Review and production policy remain distinct package-backed commands."""
    result = CliRunner().invoke(app, ["documents", "--help"])

    assert result.exit_code == 0
    assert "run-review" in result.output
    assert "run-complete" in result.output
    assert DEFAULT_COMPLETE_DOCUMENT_SPEC.name.endswith("appendix_p_v2.json")


def test_restartable_document_command_requires_explicit_spec_and_source() -> None:
    """Stage one cannot silently select Appendix P or any other document."""
    result = CliRunner().invoke(app, ["extraction", "run-document", "--help"])

    assert result.exit_code == 0
    assert "--run-spec" in result.output
    assert "--source-id" in result.output
    assert "required" in result.output


def test_canonicalize_group_exposes_document_scoped_materialization() -> None:
    """Canonical records have a distinct package-backed command boundary."""
    result = CliRunner().invoke(app, ["canonicalize", "--help"])

    assert result.exit_code == 0
    assert "run-document" in result.output
    assert "run-semantic-document" in result.output
    assert DEFAULT_CANONICALIZATION_SPEC.name.endswith("task03d_appendix_p_v1.json")
    assert DEFAULT_SEMANTIC_MATERIALIZATION_SPEC.name.endswith("task03e4_semantic_v1.json")
