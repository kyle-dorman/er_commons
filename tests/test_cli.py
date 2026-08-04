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


def test_public_groups_expose_only_sources_and_maintained_extraction() -> None:
    """Completed proof workflows do not remain as public command groups."""
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "sources" in result.output
    assert "extraction" in result.output
    assert "documents" not in result.output
    assert "tables" not in result.output
    assert "canonicalize" not in result.output
    assert "hierarchy" not in result.output


def test_restartable_document_command_requires_explicit_spec_and_source() -> None:
    """Stage one cannot silently select Appendix P or any other document."""
    result = CliRunner().invoke(app, ["extraction", "run-document", "--help"])

    assert result.exit_code == 0
    assert "--run-spec" in result.output
    assert "--source-id" in result.output
    assert "required" in result.output


def test_corpus_scope_command_requires_explicit_scope_spec() -> None:
    """Stage two has no implicit source scope or production default."""
    result = CliRunner().invoke(app, ["extraction", "run-scope", "--help"])

    assert result.exit_code == 0
    assert "--run-spec" in result.output
    assert "required" in result.output


def test_handoff_validation_is_read_only_and_explicit() -> None:
    """Independent validation requires an exact root, scope, and schema."""
    result = CliRunner().invoke(app, ["extraction", "validate-handoff", "--help"])

    assert result.exit_code == 0
    assert "--extraction-root" in result.output
    assert "--scope-id" in result.output
    assert "--schema" in result.output
