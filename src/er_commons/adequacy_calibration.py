"""Load the sealed C24/S12 development calibration panel without any inference."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Literal

REPO = Path(__file__).resolve().parents[2]


def file_binding(path: Path) -> dict[str, Any]:
    """Bind immutable panel bytes without exposing payloads to the model."""
    data = path.read_bytes()
    return {
        "path": str(path.resolve()),
        "sha256": hashlib.sha256(data).hexdigest(),
        "byte_size": len(data),
    }


def _rows(path: Path) -> list[dict[str, Any]]:
    """Read ordered JSONL records without exposing their contents in logs."""
    return [json.loads(line) for line in path.read_text().splitlines()]


def load_panel(
    component: Literal["C", "S"],
) -> tuple[list[dict[str, Any]], dict[str, bool], dict[str, Any]]:
    """Verify the published v3 seal and separate labels from the selected payloads."""
    pointer_path = REPO / "docs/specs/task09f_binary_calibration_result.json"
    pointer = json.loads(pointer_path.read_text())
    root = Path(os.environ["ER_COMMONS_DATA_ROOT"])
    directory = root / pointer["artifact_root_relative"]
    if directory.name != "09f_20261014_binary_contract_calibration_v3":
        raise ValueError("Only the reviewed v3 calibration panel is authorized")
    completion_path = root / pointer["completion"]["path"]
    if file_binding(completion_path)["sha256"] != pointer["completion"]["sha256"]:
        raise ValueError("Panel completion hash differs")
    completion = json.loads(completion_path.read_text())
    for item in completion["inventory"]:
        path = directory / item["path"]
        actual = file_binding(path)
        if actual["sha256"] != item["sha256"] or path.stat().st_size != item["byte_size"]:
            raise ValueError("Panel inventory differs")
    part = directory / ("conclusion" if component == "C" else "support")
    payloads = _rows(part / "judge_inputs.jsonl")
    provenance = _rows(part / "provenance.jsonl")
    label_rows = _rows(part / "proposed_labels.jsonl")
    samples, labels = [], {}
    for payload, source, label in zip(payloads, provenance, label_rows, strict=True):
        sample_id = source["candidate_id" if component == "C" else "example_id"]
        if label["candidate_id" if component == "C" else "example_id"] != sample_id:
            raise ValueError("Label alignment differs")
        labels[sample_id] = (
            label["expected_label"] == "yes"
            if component == "C"
            else label["expected_support_sufficient"]
        )
        samples.append(
            {
                "sample_id": sample_id,
                "case_id": source["case_id"],
                "scope": "development",
                "packet": payload,
            }
        )
    if len(samples) != (24 if component == "C" else 12) or len(labels) != len(samples):
        raise ValueError("Fixed panel counts differ")
    return (
        samples,
        labels,
        {"pointer": file_binding(pointer_path), "completion": file_binding(completion_path)},
    )
