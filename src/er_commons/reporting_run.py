"""Offline Task 12 publication: verified saved observations to sealed tables and charts."""

from __future__ import annotations

import argparse
import csv
import importlib.metadata
import io
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from er_commons.artifact_io import sha256_bytes
from er_commons.reporting import answer_tables, citation_tables, complexity_tables
from er_commons.reporting_charts import render_charts
from er_commons.reporting_inputs import load_development
from er_commons.reporting_judges import build_historical_judge_tables

LOGGER = logging.getLogger(__name__)


def _json(value: Any) -> bytes:
    """Serialize stable JSON with unavailable values represented by null."""
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def _csv(rows: list[dict[str, Any]]) -> bytes:
    """Export lossless JSON cells for nested provenance and blank nullable scalars."""
    fields = sorted({key for row in rows for key in row})
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
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
    return stream.getvalue().encode()


def _binding(path: Path, name: str) -> dict[str, Any]:
    """Bind one implementation or publication file by exact bytes."""
    content = path.read_bytes()
    return {"path": name, "sha256": sha256_bytes(content), "byte_size": len(content)}


def _implementation(repo: Path) -> list[dict[str, Any]]:
    """Freeze direct reporting sources and the locked runtime without volatile Git state."""
    paths = sorted((repo / "src/er_commons").rglob("*.py"))
    paths += [
        repo / "docs/specs/task12_reporting_v1.md",
        repo / "docs/specs/task12_presentation_v2.md",
        repo / "docs/specs/task12_judge_repeatability_v3.md",
        repo / "docs/specs/task12_response_units_v4.md",
        repo / "uv.lock",
        repo / "pyproject.toml",
    ]
    return [_binding(path, str(path.relative_to(repo))) for path in paths]


def publish(repo: Path, data_root: Path, output: Path) -> dict[str, Any]:
    """Replay inputs and publish create-only results; identical reruns verify byte equality."""
    repo, data_root, output = repo.resolve(), data_root.resolve(), output.resolve()
    if not output.is_relative_to(data_root) or output.is_relative_to(repo):
        raise ValueError("Reports must be outside the repository under ER_COMMONS_DATA_ROOT")
    if not output.is_relative_to(data_root / "pipelines/brisbane_baylands/task_12"):
        raise ValueError("Task 12 reports require a fresh task_12 namespace")
    loaded = load_development(repo, data_root)
    tables = answer_tables(loaded["rows"])
    tables["citation_results"] = citation_tables(tables["answers"])
    tables["complexity"] = complexity_tables(tables["answers"])
    tables.update(build_historical_judge_tables(repo))
    tables["bounded_audit"] = [
        {
            "model": row["model"],
            "case_id": row["case_id"],
            "repeat": row["repeat"],
            "identity": row["identity"],
            "exposure_group": row["exposure_group"],
            "plan_exact_replay": True,
            "report_exact_replay": True,
            "required_point_ids": [
                p["point_id"]
                for group in ("supporting_points", "qualifications")
                for p in row["candidate"][group]
            ],
            "route": row["report"]["route"],
            "coverage_complete": row["report"]["coverage_complete"],
            "audit_scope": "fixed repeat1 C041/C014/C001/C008 per model; "
            "identity/projection/coverage audit, no new semantic labels",
        }
        for row in loaded["rows"]
        if row["repeat"] == 1 and row["case_id"] in {"C041", "C014", "C001", "C008"}
    ]
    aggregate = [
        r
        for r in tables["model_results"]
        if r["component"] == "joint" and r["repeat"] == 0 and r["exposure_group"] == "all"
    ]
    # Historical agreement confirms compatible definitions on this accepted complete population.
    for row in aggregate:
        expected = loaded["source_result"]["aggregate"][row["model"]]["strict"]["passed"]
        if row["pass"] != expected:
            raise ValueError(
                "Recomputed joint results differ from accepted 11E complete population"
            )
    manifest = {
        "schema_version": "task12.reporting.v1",
        "scope": "development_only",
        "replay": loaded["replay"],
        "sources": loaded["provenance"],
        "historical_judge_sources": tables["judge_sources"],
        "accepted_reviews": loaded["accepted_reviews"],
        "implementation": _implementation(repo),
        "runtime": {
            name: importlib.metadata.version(name)
            for name in ("er-commons", "inspect-ai", "matplotlib", "numpy")
        },
        "configuration": loaded["frozen_configuration"],
        "joint_results": aggregate,
        "readiness": {
            "reporting_contract_ready": True,
            "locked_test_execution_authorized": False,
            "tasks_13_15": "provisional",
            "next": "Task 13 must separately authorize and bind its locked-only input adapter "
            "and planned 2 × 30 × 3 slots; reuse these frozen reducers and definitions.",
            "limitations": [
                "Development exposure includes both original six and additional thirteen.",
                "Historical judge agreement is not human-gold or fresh held-out validation.",
                "No quality threshold is invented after development inspection.",
                "Frozen scores retain previously reviewed evaluator disagreements.",
            ],
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".task12-", dir=output.parent) as temporary:
        staging = Path(temporary)
        for name, rows in tables.items():
            (staging / f"{name}.json").write_bytes(_json(rows))
            (staging / f"{name}.csv").write_bytes(_csv(rows))
        (staging / "manifest.json").write_bytes(_json(manifest))
        (staging / "README.md").write_text(
            "# Frozen development reporting\n\n"
            "114 answers: Luna and Haiku, 19 questions, three repeats. "
            "Original six and additional thirteen are separate development exposure groups.\n\n"
            "Start with model_results.png, question_overview.png and repeatability.png. "
            "Every chart has a shareable SVG. JSON is lossless; nested CSV cells are JSON. "
            "Blank CSV scalars mean unavailable/null, never zero. Repeat 0 "
            "means pooled repeats.\n\n"
            "answers preserves complete candidate identities and automatic diagnostics; points "
            "preserves each required G point. questions retains each component/repeat; "
            "repeatability counts complete, unresolved and N/A triples. "
            "model_results distinguishes planned, observed, applicable and "
            "complete-evaluation counts.\n\n"
            "returned_citations shows reference matching, not semantic "
            "grounding. Delivery coverage "
            "is an input audit; retrieval/read/ranked metrics remain N/A. "
            "luna_complexity is descriptive; ranges are question-level "
            "spread, not confidence intervals. "
            "Sections, tables and figure captions count as separate response units; "
            "each reference counts as a citation occurrence.\n\n"
            "judge_agreement and judge_confusion contain historical label "
            "agreement, not target-model "
            "success. Populations differ and include model-proposed reference labels. "
            "judge_observations retains exact A/G/S/C repeat identities. "
            "Existing reviews remain provenance and do not "
            "override frozen judgments.\n\n"
            "manifest binds all consumed files, reporting implementation, runtime and readiness. "
            "completion seals outputs. Identical replay verifies byte "
            "equality; changed code or inputs "
            "requires a new output directory. No calls were made. Tasks 13–15 remain provisional.\n"
        )
        render_charts(tables, staging)
        completion = {
            "schema_version": "task12.completion.v1",
            "files": [_binding(path, path.name) for path in sorted(staging.iterdir())],
        }
        (staging / "completion.json").write_bytes(_json(completion))
        if output.exists():
            expected_files = {path.name for path in staging.iterdir()}
            if {path.name for path in output.iterdir()} != expected_files:
                raise ValueError(
                    "Existing report inventory differs; select a fresh output directory"
                )
            for path in staging.iterdir():
                if (output / path.name).read_bytes() != path.read_bytes():
                    raise ValueError(f"Existing report differs: {path.name}; use a fresh namespace")
            LOGGER.info("report_replay_verified output=%s answers=%s", output, len(loaded["rows"]))
        else:
            staging.rename(output)
            LOGGER.info("report_published output=%s answers=%s", output, len(loaded["rows"]))
    return manifest


def main() -> None:
    """Require an explicit output and configured external root; expose no dispatch mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = os.environ.get("ER_COMMONS_DATA_ROOT")
    if not root:
        parser.error("ER_COMMONS_DATA_ROOT is required")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    publish(Path.cwd(), Path(root), args.output)


if __name__ == "__main__":
    main()
