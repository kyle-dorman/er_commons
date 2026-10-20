"""Pure presentation selection and legacy-table normalization, with no source I/O."""

from __future__ import annotations

import html
from copy import deepcopy
from typing import Any

from er_commons.reporting import complexity_tables
from er_commons.reporting_counts import COUNT_FIELDS, response_unit_counts

FIGURES = {
    "model_results": "Model results — all questions",
    "repeatability": "Three-repeat consistency",
    "question_overview": "Every question and repeat",
    "returned_citations": "Returned-citation precision, recall and F1",
    "luna_complexity": "Luna performance versus citation occurrences, response units and documents",
    "judge_agreement": "Judge accuracy on synthetic datasets",
    "judge_repeatability": "Judge correctness at least once and all three times",
}
TABLES = (
    "model_results",
    "point_results",
    "repeatability",
    "questions",
    "citation_results",
    "complexity",
    "answer_complexity",
    "judge_agreement",
    "judge_confusion",
    "judge_repeatability",
    "judge_item_repeatability",
)


def presentation_tables(tables: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Select pooled model summaries while preserving historical judge partitions."""
    result = {}
    for name in TABLES:
        rows = tables[name]
        if name in {"model_results", "point_results", "repeatability", "citation_results"}:
            rows = [row for row in rows if row["exposure_group"] == "all"]
        result[name] = [{k: v for k, v in row.items() if k != "exposure_group"} for row in rows]
    return result


def figures_for(primary_model: str) -> dict[str, str]:
    """Keep stable figure filenames while labeling the explicitly selected model."""
    return {
        **FIGURES,
        "luna_complexity": (
            f"{primary_model} performance versus citation occurrences, response units and documents"
        ),
    }


def prepare_tables(source: dict[str, Any], *, primary_model: str = "luna") -> dict[str, Any]:
    """Copy saved tables and refresh output-count views without changing judgments."""
    tables = deepcopy(source)
    tables["answer_complexity"] = []
    for answer in tables["answers"]:
        attempts = answer.get("automatic_details", {}).get("citation_attempts")
        counts = (
            response_unit_counts(
                answer["canonical_units"], answer["input_canonical_units"], attempts
            )
            if attempts is not None and "canonical_units" in answer
            else {key: answer[key] for key in COUNT_FIELDS if key in answer}
        )
        for obsolete in ("citations", "section_status", "input_section_status"):
            answer.pop(obsolete, None)
        answer.update(counts)
        tables["answer_complexity"].append(
            {
                **{
                    key: answer.get(key)
                    for key in (
                        "model",
                        "model_id",
                        "case_id",
                        "repeat",
                        "run_id",
                        "candidate_id",
                        "candidate_sha256",
                        "request_sha256",
                        "attempt",
                        "split",
                        "joint",
                    )
                },
                **counts,
            }
        )
    tables["complexity"] = complexity_tables(tables["answers"], primary_model=primary_model)
    return tables


def gallery_html(tables: dict[str, Any], *, primary_model: str = "luna") -> str:
    """Describe exactly one split; figures retain their machine-readable source tables."""
    split_names = {a["split"] for a in tables["answers"]}
    if len(split_names) != 1:
        raise ValueError("Presentation must contain exactly one benchmark split")
    split = next(iter(split_names))
    questions = len({a["case_id"] for a in tables["answers"]})
    title = f"{questions} {split} questions"
    explanation = (
        "Development results are a reporting preview. Task 13 will produce the main "
        "target-model results on the 30 locked test questions. Judge accuracy is measured "
        "against the reference labels in each judge's synthetic dataset."
        if split == "development"
        else "These test questions are the main target-model results. "
        "Judge accuracy is measured against reference labels in synthetic datasets."
    )
    figures = "\n".join(
        f"<section><h2>{html.escape(label)}</h2>"
        f'<a href="{name}.png"><img src="{name}.png" alt="{html.escape(label)}"></a>'
        f'<p><a href="{name}.svg">Vector figure (SVG)</a></p></section>'
        for name, label in figures_for(primary_model).items()
    )
    links = "\n".join(
        f'<li><a href="{name}.csv">{name.replace("_", " ").title()}</a></li>' for name in TABLES
    )
    return (
        '<!doctype html><meta charset="utf-8">'
        f"<title>{html.escape(title)}</title>"
        "<style>body{font:17px system-ui;max-width:1400px;margin:40px auto;padding:0 25px;"
        "color:#243340}img{width:100%}section{margin:50px 0}p{max-width:1000px;line-height:1.6}"
        "a{color:#12657a}</style>"
        f"<h1>{html.escape(title)}</h1><p>{explanation}</p>"
        "<p>All questions are reported together. "
        "Each model has three planned repeats per question. "
        "PNG figures are ready to view; SVG files are ready to share or edit. "
        "The folder contains only final figures and relevant tables.</p>"
        f"<h2>Tables (CSV)</h2><ul>{links}</ul>"
        "<p>Repeat 0 in summary tables means pooled repeats. Blank cells mean unavailable, "
        "not zero. A = routing; G = required-point grounding; S = support sufficiency; "
        "C = conclusion adequacy. Joint success requires the same answer to pass all checks. "
        "Citation matching is not semantic grounding; retrieval is N/A. "
        "Context citations are optional and neutral in precision, recall and F1. "
        "Each section, table or figure caption is a distinct response unit. "
        "Each reference to a unit counts as a citation occurrence, including reuse in "
        "different points. Citation precision/recall/F1 still use distinct canonical units.</p>"
        "<p>Judge repeat consistency compares each synthetic item with its reference label "
        "on three evaluations: correct at least once means 1, 2 or 3 correct; correct all "
        "three means 3/3. A/S/C count synthetic examples, G counts synthetic points. "
        "This is correctness, not merely repeating the same prediction. Missing or invalid "
        "predictions remain unresolved in the tables.</p>" + figures
    )
