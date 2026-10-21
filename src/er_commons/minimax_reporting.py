"""Offline Task 13A replay using the unchanged evaluation and reporting reducers."""

from __future__ import annotations

import copy
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from er_commons.artifact_io import sha256_bytes, sha256_file
from er_commons.locked_reporting import _observation
from er_commons.minimax_provider import MODEL, delivery
from er_commons.reporting import answer_tables, citation_tables, complexity_tables
from er_commons.reporting_inputs import SealedInputs, _json
from er_commons.reporting_judges import build_historical_judge_tables
from er_commons.reporting_review import export_review
from er_commons.reporting_run import _binding, _csv, _implementation
from er_commons.reporting_run import _json as encode_json


def load_run(repo: Path, source: Path, completion_sha256: str) -> dict[str, Any]:
    """Verify all sealed bytes and replay exactly ninety unique MiniMax slots."""
    seal = (source / "completion.json").read_bytes()
    if sha256_bytes(seal) != completion_sha256:
        raise ValueError("MiniMax completion digest mismatch")
    sealed = SealedInputs(source, _json(seal))
    for name in sealed.files:
        sealed.read(name)
    frozen_bytes = (repo / "docs/specs/task11e_frozen_generation_v1.json").read_bytes()
    if sealed.read("frozen_configuration.json") != frozen_bytes:
        raise ValueError("Base frozen configuration changed")
    frozen = copy.deepcopy(_json(frozen_bytes))
    frozen["targets"]["minimax"] = {"model": MODEL}
    data, preflight = sealed.json("inputs.json"), sealed.json("preflight.json")
    slots = preflight["slots"]
    expected = {("minimax", repeat, case) for repeat in (1, 2, 3) for case in data}
    keys = [(s["model"], s["repeat"], s["case_id"]) for s in slots]
    if len(data) != 30 or len(keys) != 90 or set(keys) != expected:
        raise ValueError("MiniMax roster differs from thirty questions by three repeats")
    if any(s["condition"] != "minimax_cloud" for s in slots):
        raise ValueError("MiniMax condition mismatch")
    outcomes = sealed.json("slot_results.json")
    outcome_keys = [(s["model"], s["repeat"], s["case_id"]) for s in outcomes]
    if len(outcome_keys) != 90 or set(outcome_keys) != expected:
        raise ValueError("Missing or duplicate MiniMax outcomes")
    by_key = dict(zip(outcome_keys, outcomes, strict=True))
    rows = [
        _observation(
            sealed,
            s,
            data[s["case_id"]],
            frozen,
            preflight,
            by_key[(s["model"], s["repeat"], s["case_id"])],
            delivery_fn=delivery,
        )
        for s in slots
    ]
    return {
        "rows": rows,
        "configuration": preflight["minimax_condition"],
        "source_files": list(sealed.consumed.values()),
        "stop_reason": sealed.json("accounting.json")["stop_reason"],
    }


def publish(
    repo: Path,
    data_root: Path,
    source: Path,
    output: Path,
    review_output: Path,
    completion_sha256: str,
) -> dict[str, Any]:
    """Publish a separate MiniMax test gallery, preserving original Task 13 results."""
    root = (data_root / "pipelines/brisbane_baylands/task_13a").resolve()
    paths = [p.resolve() for p in (source, output, review_output)]
    if any(not p.is_relative_to(root) or p == root for p in paths):
        raise ValueError("Task 13A publications must use its external namespace")
    if any(a.is_relative_to(b) for i, a in enumerate(paths) for j, b in enumerate(paths) if i != j):
        raise ValueError("Run, report and gallery must be separate")
    if output.exists() or review_output.exists():
        raise ValueError("Choose fresh publication destinations")
    loaded = load_run(repo, source, completion_sha256)
    tables = answer_tables(loaded["rows"])
    tables["execution_status"] = [
        {
            "model": "minimax",
            "planned": 90,
            "stop_reason": loaded["stop_reason"],
            **dict(Counter(r["status"] for r in loaded["rows"])),
        }
    ]
    tables["citation_results"] = citation_tables(tables["answers"])
    tables["complexity"] = complexity_tables(tables["answers"], primary_model="minimax")
    tables.update(build_historical_judge_tables(repo))
    manifest = {
        "schema_version": "task13a.reporting.v1",
        "scope": "test_only",
        "planned_answers": 90,
        "questions": 30,
        "new_calls": 0,
        "source": str(source),
        "source_completion_sha256": completion_sha256,
        "source_files": loaded["source_files"],
        "configuration": loaded["configuration"],
        "implementation": _implementation(repo),
        "historical_judge_sources": tables["judge_sources"],
        "recomputed_answers": sum(r["report"] is not None for r in loaded["rows"]),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".task13a-report-", dir=output.parent) as tmp:
        staging = Path(tmp) / "report"
        staging.mkdir()
        for name, rows in tables.items():
            (staging / f"{name}.json").write_bytes(encode_json(rows))
            (staging / f"{name}.csv").write_bytes(_csv(rows))
        (staging / "manifest.json").write_bytes(encode_json(manifest))
        seal = {
            "schema_version": "task13a.reporting.completion.v1",
            "files": [_binding(p, p.name) for p in sorted(staging.iterdir())],
        }
        (staging / "completion.json").write_bytes(encode_json(seal))
        if output.exists():
            raise ValueError("Report destination appeared")
        staging.rename(output)
    export_review(
        output, review_output, sha256_file(output / "completion.json"), primary_model="minimax"
    )
    return manifest
