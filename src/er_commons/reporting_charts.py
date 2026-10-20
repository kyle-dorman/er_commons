"""Static Matplotlib views of the exported reporting tables, with explicit denominators."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402

from er_commons.reporting import COMPONENTS  # noqa: E402


def _save(fig: Any, output: Path, name: str) -> None:
    """Write deterministic shareable vector and raster copies of the same figure."""
    fig.savefig(
        output / f"{name}.png", dpi=160, bbox_inches="tight", metadata={"Software": "er_commons"}
    )
    fig.savefig(output / f"{name}.svg", bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)


def _models(rows: list[dict[str, Any]]) -> list[str]:
    """Keep established display order, then include every other model label unchanged."""
    models = {row["model"] for row in rows}
    if not models:
        raise ValueError("Chart requires at least one model")
    return sorted(models, key=lambda model: ({"luna": 0, "haiku": 1}.get(model, 2), model))


def _model_label(model: str) -> str:
    """Capitalize familiar short names without rewriting model/version identifiers."""
    return {"luna": "Luna", "haiku": "Haiku"}.get(model, model)


def render_charts(
    tables: dict[str, list[dict[str, Any]]], output: Path, *, primary_model: str = "luna"
) -> None:
    """Render measured development summaries; no estimates, fitted trends or causal claims."""
    if len({r["split"] for r in tables["answers"]}) != 1:
        raise ValueError("Render each benchmark split separately")
    expected_models = {row["model"] for row in tables["answers"]}
    for name in ("model_results", "repeatability", "questions", "citation_results"):
        if {row["model"] for row in tables[name]} != expected_models:
            raise ValueError(f"Model roster differs between answers and {name}")
    if primary_model not in {row["model"] for row in tables["complexity"]}:
        raise ValueError(f"No complexity results for primary model {primary_model!r}")
    with matplotlib.rc_context({"svg.hashsalt": "task12.reporting.v1", "font.size": 10}):
        _model_chart(tables["model_results"], output)
        _repeat_chart(tables["repeatability"], output)
        _question_chart(tables["questions"], output)
        _citation_chart(tables["citation_results"], output)
        _complexity_chart(tables["complexity"], output, primary_model=primary_model)
        _judge_chart(tables["judge_agreement"], output)
        _judge_repeat_chart(tables["judge_repeatability"], output)


def _model_chart(rows: list[dict[str, Any]], output: Path) -> None:
    """Show component passes with planned counts and unresolved observations."""
    models = _models(rows)
    width = 0.8 / len(models)
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    for index, model in enumerate(models):
        offset = (index - (len(models) - 1) / 2) * width
        color = {"luna": "#247b96", "haiku": "#bb6548"}.get(model, f"C{index % 10}")
        selected = [
            next(
                r
                for r in rows
                if r["model"] == model
                and r["exposure_group"] == "all"
                and r["repeat"] == 0
                and r["component"] == component
            )
            for component in COMPONENTS
        ]
        bars = ax.bar(
            np.arange(len(COMPONENTS)) + offset,
            [r["planned_pass_fraction"] for r in selected],
            width * 0.95,
            label=_model_label(model),
            color=color,
        )
        ax.bar_label(bars, labels=[f"{r['pass']}/{r['planned']}" for r in selected], fontsize=7)
    ax.set(
        xticks=range(len(COMPONENTS)),
        xticklabels=COMPONENTS,
        ylim=(0, 1.17),
        title=f"All {rows[0]['split']} questions",
    )
    ax.grid(axis="y", alpha=0.2)
    ax.set_ylabel("Model pass fraction / planned answers")
    fig.suptitle(f"Frozen {rows[0]['split']} results • three repeats per question")
    fig.legend(
        *ax.get_legend_handles_labels(),
        loc="upper center",
        bbox_to_anchor=(0.5, 0.94),
        ncols=len(models),
    )
    fig.subplots_adjust(top=0.79)
    fig.text(
        0.5,
        -0.02,
        "G requires every required point. Joint uses the same answer. "
        "Counts include all planned slots; availability is in model_results.csv.",
        ha="center",
    )
    _save(fig, output, "model_results")


def _repeat_chart(rows: list[dict[str, Any]], output: Path) -> None:
    """Display the full repeat distribution at unique-question level."""
    models = _models(rows)
    fig, panels = plt.subplots(
        1, len(models), figsize=(6.5 * len(models), 5), sharey=True, squeeze=False
    )
    axes = panels[0]
    for ax, model in zip(axes, models, strict=True):
        selected = [
            next(
                r
                for r in rows
                if r["model"] == model and r["exposure_group"] == "all" and r["component"] == c
            )
            for c in COMPONENTS
        ]
        bottoms = np.zeros(len(selected))
        for field, label, color in (
            ("passes_0", "0 / 3", "#d8a2a2"),
            ("passes_1", "1 / 3", "#e6cc8a"),
            ("passes_2", "2 / 3", "#87bdc0"),
            ("passes_3", "3 / 3", "#267f88"),
            ("unresolved_triples", "Unresolved", "#777777"),
            ("not_applicable_triples", "N/A", "#cccccc"),
            ("mixed_applicability_triples", "Mixed N/A", "#aaaaaa"),
        ):
            values = [r[field] for r in selected]
            bars = ax.bar(range(len(selected)), values, bottom=bottoms, label=label, color=color)
            ax.bar_label(
                bars, labels=[str(v) if v else "" for v in values], label_type="center", fontsize=9
            )
            bottoms += values
        ax.set(
            title=f"{_model_label(model)} • {selected[0]['planned_questions']} unique "
            f"{selected[0]['split']} questions",
            xticks=range(len(COMPONENTS)),
            xticklabels=COMPONENTS,
            ylim=(0, selected[0]["planned_questions"] + 2),
        )
    axes[0].set_ylabel("Unique questions")
    axes[-1].legend(bbox_to_anchor=(1.02, 1), title="Passing repeats")
    fig.suptitle("Observed three-run repeatability • no best-answer selection")
    _save(fig, output, "repeatability")


def _question_chart(rows: list[dict[str, Any]], output: Path) -> None:
    """Show every component/repeat for the entire benchmark split together."""
    cases = sorted({r["case_id"] for r in rows})
    models = _models(rows)
    fig, panels = plt.subplots(
        1, len(models), figsize=(7.5 * len(models), 9), sharey=True, squeeze=False
    )
    axes = panels[0]
    for ax, model in zip(axes, models, strict=True):
        grid = []
        for case in cases:
            grid.append(
                [
                    {"pass": 1, "fail": 0, "unavailable": 0.5, "not_applicable": 0.25}[
                        next(
                            r
                            for r in rows
                            if r["model"] == model and r["case_id"] == case and r["component"] == c
                        )[f"repeat{repeat}"]
                    ]
                    for c in COMPONENTS
                    for repeat in (1, 2, 3)
                ]
            )
        ax.imshow(
            grid,
            vmin=0,
            vmax=1,
            cmap=ListedColormap(["#e5a299", "#e2e2e2", "#d1bd7f", "#84b8ad"]),
            aspect="auto",
        )
        for i, line in enumerate(grid):
            for j, value in enumerate(line):
                ax.text(
                    j,
                    i,
                    {1: "P", 0: "F", 0.5: "?", 0.25: "–"}[value],
                    ha="center",
                    va="center",
                    fontsize=7,
                )
        ax.set(
            xticks=range(len(COMPONENTS) * 3),
            xticklabels=[
                f"{dict(automatic='Auto', joint='Joint').get(c, c)}\n{r}"
                for c in COMPONENTS
                for r in (1, 2, 3)
            ],
            yticks=range(len(cases)),
            yticklabels=cases,
            title=_model_label(model),
        )
        ax.tick_params(axis="x", labelsize=7)
    fig.suptitle("Per-question outcomes • P pass, F fail, ? unavailable, – not applicable")
    fig.text(
        0.5,
        0.03,
        "Columns show component and repeat. "
        "All questions in this benchmark split are shown together.",
        ha="center",
    )
    _save(fig, output, "question_overview")


def _citation_chart(rows: list[dict[str, Any]], output: Path) -> None:
    """Keep reference citation matching separate from semantic judge results."""
    models = _models(rows)
    fig, panels = plt.subplots(
        1, len(models), figsize=(5.5 * len(models), 4), sharey=True, squeeze=False
    )
    axes = panels[0]
    for ax, model in zip(axes, models, strict=True):
        row = next(
            r
            for r in rows
            if r["model"] == model and r["exposure_group"] == "all" and r["repeat"] == 0
        )
        for offset, aggregation in ((-0.2, "macro"), (0.2, "micro")):
            values = [row[f"{aggregation}_{metric}"] for metric in ("precision", "recall", "f1")]
            bars = ax.bar(
                np.arange(3) + offset,
                [v if v is not None else np.nan for v in values],
                0.38,
                label=aggregation,
            )
            ax.bar_label(
                bars, labels=[f"{v:.3f}" if v is not None else "" for v in values], fontsize=9
            )
        if not row["eligible"]:
            ax.text(
                0.5,
                0.5,
                "Unavailable / no eligible observations",
                transform=ax.transAxes,
                ha="center",
                fontsize=9,
            )
        ax.set(
            title=f"{_model_label(model)} • {row['eligible']}/{row['planned']} eligible answers",
            xticks=range(3),
            xticklabels=("Precision", "Recall", "F1"),
            ylim=(0, 1.15),
        )
        ax.legend()
    axes[0].set_ylabel("Reference citation matching")
    fig.suptitle("Returned citations • neutral context excluded from precision denominator")
    fig.text(
        0.5, -0.03, "Verified delivery is an input audit; retrieval metrics are N/A.", ha="center"
    )
    _save(fig, output, "returned_citations")


def _complexity_chart(
    rows: list[dict[str, Any]], output: Path, *, primary_model: str = "luna"
) -> None:
    """Plot fixed-bin pass fractions and question-level range, never fitted trends."""
    rows = [row for row in rows if row["model"] == primary_model]
    if not rows:
        raise ValueError(f"No complexity results for primary model {primary_model!r}")
    fig, axes = plt.subplots(1, 3, figsize=(17, 5), sharey=True)
    covariates = ("citation_occurrences", "response_units", "documents")
    for ax, covariate in zip(axes, covariates, strict=True):
        selected = [r for r in rows if r["covariate"] == covariate and r["component"] == "joint"]
        for index, row in enumerate(selected):
            value = row["observed_pass_fraction"]
            if value is not None:
                ax.vlines(
                    index,
                    row["question_rate_min"],
                    row["question_rate_max"],
                    color="#9aa6ac",
                    linewidth=4,
                )
                ax.scatter(index, value, color="#247b96", zorder=3)
                ax.annotate(
                    f"{row['pass']}/{row['observed']}",
                    (index, value),
                    xytext=(0, 9),
                    textcoords="offset points",
                    ha="center",
                    fontsize=9,
                )
        ax.set(
            xticks=range(len(selected)),
            xticklabels=[
                f"{r['bin']}\nN={r['planned']}\nQ={r['unique_questions']}" for r in selected
            ],
            title={
                "citation_occurrences": "Citation occurrences",
                "response_units": "Distinct response units cited",
                "documents": "Distinct documents cited",
            }[covariate],
            ylim=(-0.05, 1.15),
        )
        ax.grid(axis="y", alpha=0.2)
    axes[0].set_ylabel(f"{_model_label(primary_model)} joint pass fraction / observed answers")
    fig.suptitle("Descriptive associations • output behavior is not intrinsic question difficulty")
    fig.subplots_adjust(bottom=0.3, top=0.82)
    fig.text(
        0.5,
        0.01,
        "N = answers; Q = unique questions. Grey ranges: within-bin question pass fractions, "
        "not confidence intervals.\nA response unit is a section, table or figure caption; "
        "repeated references count as separate citation occurrences. "
        "Input counts and all component results are exported separately.",
        ha="center",
    )
    # Preserve the published filename; the axis and provenance identify the selected model.
    _save(fig, output, "luna_complexity")


def _judge_chart(rows: list[dict[str, Any]], output: Path) -> None:
    """Show each historical panel separately, with its own counts and metric units."""
    fig, axes = plt.subplots(1, 4, figsize=(16, 5), sharey=True)
    for ax, component in zip(axes, ("A", "G", "S", "C"), strict=True):
        row = next(r for r in rows if r["component"] == component and r["partition"] == "all")
        metric = "macro_f1_valid_only" if component == "A" else "f1"
        values = [row["accuracy_valid_only"], row[metric]]
        bars = ax.bar((0, 1), values, color=("#64778d", "#247b96"))
        ax.bar_label(bars, labels=[f"{v:.3f}" for v in values], fontsize=10)
        ax.set(
            xticks=(0, 1),
            xticklabels=("Accuracy", "Macro F1" if component == "A" else "Positive F1"),
            ylim=(0, 1.16),
            title=f"{component} • {row['correct']}/{row['valid']} correct\n"
            f"{row['valid']}/{row['planned']} valid\n{row['evaluation_unit']}",
        )
    axes[0].set_ylabel("Agreement with synthetic reference labels (valid-only)")
    fig.suptitle("Judge accuracy on synthetic datasets")
    fig.subplots_adjust(top=0.73)
    fig.text(
        0.5,
        -0.04,
        "A: three-class routing; G/S/C positive classes: supported / sufficient / adequate.\n"
        "All development populations include calibration exposure. Tables retain partitions, "
        "failure-inclusive accuracy and confusion counts.\n"
        "These are not target-model pass rates; component accuracies cannot be multiplied.",
        ha="center",
    )
    _save(fig, output, "judge_agreement")


def _judge_repeat_chart(rows: list[dict[str, Any]], output: Path) -> None:
    """Show same-item correctness across three judge evaluations against synthetic labels."""
    selected = [
        next(row for row in rows if row["component"] == component and row["partition"] == "all")
        for component in ("A", "G", "S", "C")
    ]
    fig, ax = plt.subplots(figsize=(10, 6))
    for offset, key, label, color in (
        (-0.2, "correct_at_least_once", "Correct at least once", "#84b8ad"),
        (0.2, "correct_all_three", "Correct all three times", "#247b96"),
    ):
        values = [
            row[key] / row["planned_items"]
            if row[key] is not None and row["planned_items"]
            else np.nan
            for row in selected
        ]
        bars = ax.bar(np.arange(4) + offset, values, 0.38, color=color, label=label)
        ax.bar_label(
            bars,
            labels=[
                f"{row[key]}/{row['planned_items']}" if row[key] is not None else "Unavailable"
                for row in selected
            ],
            fontsize=10,
        )
    ax.set(
        xticks=range(4),
        xticklabels=[
            f"{row['component']}\n{row['planned_items']} synthetic "
            f"{'points' if row['component'] == 'G' else 'examples'}"
            for row in selected
        ],
        ylabel="Fraction of planned synthetic items",
        ylim=(0, 1.12),
    )
    fig.suptitle("Judge correctness across three evaluations of each synthetic item")
    fig.legend(
        *ax.get_legend_handles_labels(), loc="upper center", bbox_to_anchor=(0.5, 0.94), ncols=2
    )
    fig.subplots_adjust(top=0.80, bottom=0.22)
    fig.text(
        0.5,
        0.02,
        "Correct means matching the recorded reference label, including negative labels.\n"
        "Each item keeps its three original evaluations; "
        "no new judgments or best-answer selection.\n"
        "Complete triples: "
        + "; ".join(
            f"{r['component']} {r['complete_triples']}/{r['planned_items']}" for r in selected
        )
        + ". Missing/invalid triples remain explicit in the tables.",
        ha="center",
        fontsize=9,
    )
    _save(fig, output, "judge_repeatability")
