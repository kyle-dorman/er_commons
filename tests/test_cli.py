"""Tests for the Typer workspace-inspection CLI and typed project settings."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from er_commons import cli
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


def test_public_groups_expose_responsibility_oriented_workflows() -> None:
    """Completed proof workflows do not remain as public command groups."""
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "sources" in result.output
    assert "documents" in result.output
    assert "collections" in result.output
    assert "extraction" not in result.output
    assert "tables" not in result.output
    assert "canonicalize" not in result.output
    assert "hierarchy" not in result.output


def test_restartable_document_command_requires_explicit_spec_and_source() -> None:
    """Stage one cannot silently select Appendix P or any other document."""
    result = CliRunner().invoke(app, ["documents", "publish", "--help"])

    assert result.exit_code == 0
    assert "--document-spec" in result.output
    assert "--source-id" in result.output
    assert "required" in result.output


def test_collection_handoff_command_requires_explicit_collection_spec() -> None:
    """Stage two has no implicit source scope or production default."""
    result = CliRunner().invoke(app, ["collections", "assemble-handoff", "--help"])

    assert result.exit_code == 0
    assert "--collection-spec" in result.output
    assert "required" in result.output


def test_handoff_validation_is_read_only_and_explicit() -> None:
    """Independent validation requires an exact root, scope, and schema."""
    result = CliRunner().invoke(app, ["collections", "validate-handoff", "--help"])

    assert result.exit_code == 0
    assert "--collection-root" in result.output
    assert "--scope-id" in result.output
    assert "--schema" in result.output


def test_document_publish_command_calls_public_workflow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The CLI forwards the explicit spec/source and reports the completion path."""
    spec = tmp_path / "document.json"
    spec.write_text("{}\n")
    completion = tmp_path / "completion.json"
    calls: list[tuple[Path, Path, str]] = []
    monkeypatch.setenv("ER_COMMONS_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setattr(
        cli,
        "publish_document",
        lambda root, path, source: calls.append((root, path, source)) or completion,
    )

    result = CliRunner().invoke(
        app,
        ["documents", "publish", "--document-spec", str(spec), "--source-id", "alpha"],
    )

    assert result.exit_code == 0
    assert calls == [(tmp_path / "data", spec, "alpha")]
    assert f"document_completion={completion}" in result.output


def test_collection_assembly_command_calls_public_workflow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Collection assembly forwards one explicit specification."""
    spec = tmp_path / "collection.json"
    spec.write_text("{}\n")
    completion = tmp_path / "handoff.json"
    calls: list[tuple[Path, Path]] = []
    monkeypatch.setenv("ER_COMMONS_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setattr(
        cli,
        "assemble_collection_handoff",
        lambda root, path: calls.append((root, path)) or completion,
    )

    result = CliRunner().invoke(
        app,
        ["collections", "assemble-handoff", "--collection-spec", str(spec)],
    )

    assert result.exit_code == 0
    assert calls == [(tmp_path / "data", spec)]
    assert f"handoff_completion={completion}" in result.output


def test_handoff_validation_command_reports_public_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Read-only validation forwards all bounds and labels its result clearly."""
    collection_root = tmp_path / "collection"
    collection_root.mkdir()
    schema = tmp_path / "schema.json"
    schema.write_text("{}\n")
    calls: list[dict[str, Path | str]] = []

    def validate(**kwargs: Path | str) -> SimpleNamespace:
        calls.append(kwargs)
        return SimpleNamespace(
            handoff_id="handoffv1-test",
            verified_document_count=3,
            task04_status="not_evaluated",
        )

    monkeypatch.setattr(cli, "validate_collection_handoff", validate)
    result = CliRunner().invoke(
        app,
        [
            "collections",
            "validate-handoff",
            "--collection-root",
            str(collection_root),
            "--scope-id",
            "scopev1-test",
            "--schema",
            str(schema),
        ],
    )

    assert result.exit_code == 0
    assert calls == [
        {
            "extraction_root": collection_root,
            "scope_id": "scopev1-test",
            "schema_path": schema,
        }
    ]
    assert "handoff_id=handoffv1-test" in result.output
    assert "verified_documents=3" in result.output


def test_contract_validation_command_reports_fixture_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Contract validation forwards explicit paths and reports the checked count."""
    schema = tmp_path / "schema.json"
    schema.write_text("{}\n")
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    calls: list[tuple[Path, Path]] = []
    monkeypatch.setattr(
        cli,
        "validate_collection_contract_fixtures",
        lambda schema_path, fixture_root: calls.append((schema_path, fixture_root)) or 2,
    )

    result = CliRunner().invoke(
        app,
        [
            "collections",
            "validate-contract",
            "--schema",
            str(schema),
            "--fixtures",
            str(fixtures),
        ],
    )

    assert result.exit_code == 0
    assert calls == [(schema.resolve(), fixtures.resolve())]
    assert "collection_contract=valid" in result.output
    assert "fixtures=2" in result.output
