"""Small sealed publications exercise export failure boundaries without historical data."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from er_commons import reporting_review
from er_commons.reporting import COMPONENTS
from er_commons.reporting_presentation import TABLES, prepare_tables


def saved_tables() -> dict[str, Any]:
    """Invent one candidate with repeated references to a separately citable table."""
    tables: dict[str, Any] = {name: [] for name in TABLES}
    unit = ["invented-document", "extraction", "table", "table-1"]
    tables["answers"] = [
        {
            "model": "next-model",
            "model_id": "model-version",
            "case_id": "invented-case",
            "repeat": 1,
            "split": "development",
            "candidate_id": "candidate-1",
            "canonical_units": [unit],
            "input_canonical_units": [unit],
            "automatic_details": {
                "citation_attempts": [
                    {"status": "resolved", "token": "P1"},
                    {"status": "resolved", "token": "P1"},
                ]
            },
            **dict.fromkeys(COMPONENTS, "pass"),
        }
    ]
    tables["model_results"] = [
        {"model": "next-model", "exposure_group": group, "pass": 1}
        for group in ("fixed_six", "all")
    ]
    return tables


def seal_tables(path: Path, tables: dict[str, Any]) -> str:
    """Seal invented table bytes using the production publication inventory contract."""
    path.mkdir()
    files = []
    for name, rows in tables.items():
        content = json.dumps(rows).encode()
        filename = f"{name}.json"
        (path / filename).write_bytes(content)
        files.append(
            {
                "path": filename,
                "sha256": hashlib.sha256(content).hexdigest(),
                "byte_size": len(content),
            }
        )
    completion = json.dumps({"files": files}).encode()
    (path / "completion.json").write_bytes(completion)
    return hashlib.sha256(completion).hexdigest()


def test_self_contained_export_publishes_bound_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A new model's saved report exports without any checkout or historical-source access."""
    source, output = tmp_path / "source", tmp_path / "review"
    seal = seal_tables(source, saved_tables())

    def forbidden_history(repo: Path) -> dict[str, Any]:
        raise AssertionError("Self-contained export must not reload historical data")

    def render(tables: dict[str, Any], path: Path, *, primary_model: str) -> None:
        assert primary_model == "next-model"
        assert tables["answers"][0]["response_units"] == 1
        (path / "model_results.png").write_bytes(b"invented chart")

    monkeypatch.setattr(reporting_review, "build_historical_judge_tables", forbidden_history)
    monkeypatch.setattr(reporting_review, "render_charts", render)
    receipt = reporting_review.export_review(source, output, seal, primary_model="next-model")
    assert json.loads((tmp_path / "review_provenance.json").read_text()) == receipt
    for entry in receipt["outputs"]:
        content = (output / entry["path"]).read_bytes()
        assert len(content) == entry["byte_size"]
        assert hashlib.sha256(content).hexdigest() == entry["sha256"]
    assert "next-model performance" in (output / "START_HERE.html").read_text()
    assert "fixed_six" not in (output / "model_results.csv").read_text()
    assert reporting_review.read_sealed_tables(source, seal) == saved_tables()
    with pytest.raises(ValueError, match="fresh"):
        reporting_review.export_review(source, output, seal, primary_model="next-model")


def test_existing_receipt_blocks_publication(tmp_path: Path) -> None:
    """A prior receipt cannot be replaced or leave a new mismatched report alongside it."""
    output = tmp_path / "review"
    receipt = tmp_path / "review_provenance.json"
    receipt.write_text("existing receipt")
    with pytest.raises(ValueError, match="fresh"):
        reporting_review.export_review(tmp_path / "absent-source", output, "unused")
    assert receipt.read_text() == "existing receipt"
    assert not output.exists()


@pytest.mark.parametrize("target", ["completion.json", "answers.json"])
def test_changed_sealed_bytes_rejected(tmp_path: Path, target: str) -> None:
    """Both the root seal and its bound tables must match before a report can be rendered."""
    source = tmp_path / "source"
    seal = seal_tables(source, saved_tables())
    with (source / target).open("a") as handle:
        handle.write(" ")
    with pytest.raises(ValueError, match="differs|Changed sealed source"):
        reporting_review.read_sealed_tables(source, seal)


def test_failed_renderer_leaves_no_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A partial chart failure cleans staging and never advertises a completed report."""
    source, output = tmp_path / "source", tmp_path / "review"
    seal = seal_tables(source, saved_tables())

    def fail(tables: dict[str, Any], path: Path, *, primary_model: str) -> None:
        (path / "partial.png").write_bytes(b"partial")
        raise RuntimeError("chart failed")

    monkeypatch.setattr(reporting_review, "render_charts", fail)
    with pytest.raises(RuntimeError, match="chart failed"):
        reporting_review.export_review(source, output, seal, primary_model="next-model")
    assert list(tmp_path.iterdir()) == [source]


def test_legacy_report_requires_explicit_judge_source(tmp_path: Path) -> None:
    """Missing old judge tables produce an actionable error without implicit source reads."""
    tables = saved_tables()
    del tables["judge_repeatability"]
    source, output = tmp_path / "source", tmp_path / "review"
    seal = seal_tables(source, tables)
    with pytest.raises(ValueError, match="explicit --judge-repo"):
        reporting_review.export_review(source, output, seal, primary_model="next-model")
    assert not output.exists()


def test_preparation_preserves_saved_input_and_judgments() -> None:
    """Presentation recounting cannot mutate sealed input objects or saved pass decisions."""
    source = saved_tables()
    before = deepcopy(source)
    prepared = prepare_tables(source, primary_model="next-model")
    assert source == before
    answer = prepared["answer_complexity"][0]
    assert answer["citation_occurrences"] == 2
    assert answer["response_units"] == answer["tables"] == 1
    assert answer["joint"] == source["answers"][0]["joint"]


def test_normalized_counts_survive_without_raw_citation_attempts() -> None:
    """A compact saved report retains its per-answer counts and aggregate denominators."""
    normalized = prepare_tables(saved_tables(), primary_model="next-model")
    normalized["answers"][0].pop("automatic_details")
    before = deepcopy(normalized)
    prepared = prepare_tables(normalized, primary_model="next-model")
    assert prepared["answer_complexity"] == before["answer_complexity"]
    assert prepared["complexity"] == before["complexity"]
    assert normalized == before


def test_failed_publication_removes_reserved_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A directory publication failure rolls back its newly reserved provenance file."""
    source, output = tmp_path / "source", tmp_path / "review"
    seal = seal_tables(source, saved_tables())

    def render(tables: dict[str, Any], path: Path, *, primary_model: str) -> None:
        (path / "model_results.png").write_bytes(b"invented chart")

    def fail_rename(path: Path, target: str | Path) -> Path:
        assert (tmp_path / "review_provenance.json").exists()
        raise OSError("publication failed")

    monkeypatch.setattr(reporting_review, "render_charts", render)
    monkeypatch.setattr(Path, "rename", fail_rename)
    with pytest.raises(OSError, match="publication failed"):
        reporting_review.export_review(source, output, seal, primary_model="next-model")
    assert list(tmp_path.iterdir()) == [source]
