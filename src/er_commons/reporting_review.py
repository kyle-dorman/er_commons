"""Export a verified saved report into a create-only folder of final figures and tables."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import tempfile
from pathlib import Path
from typing import Any

from er_commons.reporting_charts import render_charts
from er_commons.reporting_judges import build_historical_judge_tables
from er_commons.reporting_presentation import gallery_html, prepare_tables, presentation_tables


def read_sealed_tables(source: Path, expected_seal: str) -> dict[str, Any]:
    """Verify the full publication before exposing any saved table to presentation code."""
    source = source.resolve()
    seal_bytes = (source / "completion.json").read_bytes()
    if hashlib.sha256(seal_bytes).hexdigest() != expected_seal:
        raise ValueError("Source completion differs from the accepted result")
    tables = {}
    seen: set[str] = set()
    for entry in json.loads(seal_bytes)["files"]:
        relative = entry["path"]
        path = (source / relative).resolve()
        if not path.is_relative_to(source) or relative in seen:
            raise ValueError("Escaping or duplicate source path")
        seen.add(relative)
        content = path.read_bytes()
        if (
            len(content) != entry["byte_size"]
            or hashlib.sha256(content).hexdigest() != entry["sha256"]
        ):
            raise ValueError(f"Changed sealed source: {relative}")
        if path.suffix == ".json" and path.name != "manifest.json":
            if path.stem in tables:
                raise ValueError(f"Duplicate table name: {path.stem}")
            tables[path.stem] = json.loads(content)
    return tables


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Preserve review column order and encode nested records as lossless JSON cells."""
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value, sort_keys=True, allow_nan=False)
                    if isinstance(value, (dict, list, tuple))
                    else value
                    for key, value in row.items()
                }
            )


def _binding(path: Path) -> dict[str, Any]:
    """Bind bytes once with a filename relative to the publication directory."""
    content = path.read_bytes()
    return {
        "path": path.name,
        "sha256": hashlib.sha256(content).hexdigest(),
        "byte_size": len(content),
    }


def export_review(
    source: Path,
    output: Path,
    expected_seal: str,
    *,
    primary_model: str = "luna",
    judge_repo: Path | None = None,
) -> dict[str, Any]:
    """Publish saved tables and provenance; historical judge enrichment must be explicit.

    A source already containing judge repeatability is self-contained. Only legacy
    Task 12 publications need judge_repo to bind the separately saved 09G records.
    Both the output directory and its sibling provenance file must be fresh.
    """
    source, output = source.resolve(), output.resolve()
    receipt_path = output.with_name(output.name + "_provenance.json")
    if output.exists() or receipt_path.exists():
        raise ValueError("Choose a fresh review folder and provenance path")
    if output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError("Review output must be separate from the sealed source")
    tables = read_sealed_tables(source, expected_seal)
    if judge_repo is not None:
        tables.update(build_historical_judge_tables(judge_repo.resolve()))
    if "judge_repeatability" not in tables or "judge_item_repeatability" not in tables:
        raise ValueError("Legacy report requires explicit --judge-repo for synthetic judge records")
    tables = prepare_tables(tables, primary_model=primary_model)
    selected = presentation_tables(tables)
    gallery = gallery_html(tables, primary_model=primary_model)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".review-") as temporary:
        staging = Path(temporary) / "report"
        staging.mkdir()
        render_charts(tables, staging, primary_model=primary_model)
        for name, rows in selected.items():
            _write_csv(staging / f"{name}.csv", rows)
        (staging / "START_HERE.html").write_text(gallery, encoding="utf-8")
        receipt = {
            "schema_version": "reporting.review.v5",
            "source": str(source),
            "source_completion_sha256": expected_seal,
            "primary_model": primary_model,
            "judge_sources": tables.get("judge_sources", []),
            "judge_repeatability": tables["judge_repeatability"],
            "outputs": [_binding(path) for path in sorted(staging.iterdir())],
            "implementation": [
                _binding(Path(__file__).with_name(name))
                for name in (
                    "reporting_review.py",
                    "reporting_presentation.py",
                    "reporting_counts.py",
                    "reporting_charts.py",
                    "reporting_judges.py",
                    "reporting_inputs.py",
                    "reporting.py",
                )
            ],
        }
        receipt_bytes = json.dumps(receipt, indent=2, allow_nan=False) + "\n"
        # Reserve the receipt before publishing; clean up our reservation on failure.
        with receipt_path.open("x", encoding="utf-8") as handle:
            try:
                handle.write(receipt_bytes)
                handle.flush()
                if output.exists():
                    raise ValueError("Review output appeared during publication")
                staging.rename(output)
            except BaseException:
                receipt_path.unlink(missing_ok=True)
                raise
    logging.getLogger(__name__).info("review_folder_published output=%s", output)
    return receipt


def main() -> None:
    """Render saved results only; no evaluation or model dispatch is exposed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--completion-sha256", required=True)
    parser.add_argument("--primary-model", default="luna")
    parser.add_argument(
        "--judge-repo", type=Path, help="Explicit 09G source checkout for legacy reports"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    export_review(
        args.source,
        args.output,
        args.completion_sha256,
        primary_model=args.primary_model,
        judge_repo=args.judge_repo,
    )


if __name__ == "__main__":
    main()
