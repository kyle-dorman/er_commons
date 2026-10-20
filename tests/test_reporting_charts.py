"""Small chart contracts for future model comparisons, without saved benchmark content."""

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pytest
from test_reporting import observation

from er_commons import reporting_charts as charts
from er_commons.reporting import answer_tables, citation_tables


def model_tables(models: tuple[str, ...]) -> dict[str, list[dict[str, Any]]]:
    """Build independent model rosters using the same invented three-repeat question."""
    observations = []
    for model in models:
        for repeat in (1, 2, 3):
            row = observation(repeat)
            row["model"] = model
            observations.append(row)
    tables = answer_tables(observations)
    tables["citation_results"] = citation_tables(tables["answers"])
    return tables


@pytest.mark.parametrize("models", [("new-model/V2",), ("luna", "haiku", "new-model/V2")])
def test_model_figures_include_every_model(
    models: tuple[str, ...], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A new comparison arm must appear in each plot, even without the original models."""
    figures = {}
    monkeypatch.setattr(
        charts, "_save", lambda figure, output, name: figures.update({name: figure})
    )
    tables = model_tables(models)
    try:
        charts._model_chart(tables["model_results"], tmp_path)
        charts._repeat_chart(tables["repeatability"], tmp_path)
        charts._question_chart(tables["questions"], tmp_path)
        charts._citation_chart(tables["citation_results"], tmp_path)
        labels = figures["model_results"].axes[0].get_legend_handles_labels()[1]
        assert labels == [charts._model_label(model) for model in models]
        for name in ("repeatability", "question_overview", "returned_citations"):
            assert len(figures[name].axes) == len(models)
            for axis, model in zip(figures[name].axes, models, strict=True):
                assert charts._model_label(model) in axis.get_title()
                assert axis.patches or axis.images
    finally:
        for figure in figures.values():
            plt.close(figure)


def test_complexity_chart_selects_primary_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The primary-model label and plotted values must refer to the same selected arm."""
    figures = []
    monkeypatch.setattr(charts, "_save", lambda figure, output, name: figures.append(figure))
    rows = [
        dict(
            model=model,
            covariate=covariate,
            component="joint",
            observed_pass_fraction=value,
            question_rate_min=value,
            question_rate_max=value,
            **{"pass": int(value)},
            observed=1,
            planned=1,
            unique_questions=1,
            bin="1",
        )
        for model, value in (("luna", 0.0), ("new-model/V2", 1.0))
        for covariate in ("citation_occurrences", "response_units", "documents")
    ]
    try:
        charts._complexity_chart(rows, tmp_path, primary_model="new-model/V2")
        assert figures[0].axes[0].get_ylabel().startswith("new-model/V2 ")
        for axis in figures[0].axes:
            assert len(axis.get_xticklabels()) == 1
            assert [text.get_text() for text in axis.texts] == ["1/1"]
    finally:
        for figure in figures:
            plt.close(figure)
    with pytest.raises(ValueError, match="No complexity results for primary model"):
        charts._complexity_chart(rows, tmp_path, primary_model="absent")


def test_render_rejects_missing_model_before_writing(tmp_path: Path) -> None:
    """Incomplete comparison tables cannot silently drop a model from an exported figure."""
    tables = model_tables(("luna", "haiku"))
    tables["questions"] = [row for row in tables["questions"] if row["model"] == "luna"]
    with pytest.raises(ValueError, match="Model roster differs.*questions"):
        charts.render_charts(tables, tmp_path)
    assert not list(tmp_path.iterdir())
