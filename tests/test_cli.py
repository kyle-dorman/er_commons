"""Tests for the Typer workspace-inspection CLI and typed project settings."""

import pytest
from typer.testing import CliRunner

from er_commons.cli import app
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


def test_documents_group_exposes_clean_review_pipeline() -> None:
    """The document CLI has one explicit maintained review command."""
    result = CliRunner().invoke(app, ["documents", "--help"])

    assert result.exit_code == 0
    assert "run-review" in result.output
