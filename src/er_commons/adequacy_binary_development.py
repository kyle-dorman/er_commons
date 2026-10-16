"""Read sealed development-only C/S synthesis with labels isolated from judge payloads."""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from er_commons.adequacy_binary import Component, validate_input
from er_commons.artifact_io import json_bytes, stable_json_sha256

REPO = Path(__file__).resolve().parents[2]
DEVELOPMENT_CASE_IDS = frozenset(
    {
        "C001",
        "C006",
        "C007",
        "C008",
        "C014",
        "C017",
        "C019",
        "C027",
        "C028",
        "C029",
        "C036",
        "C037",
        "C041",
        "C042",
        "C045",
        "C050",
        "C051",
        "C054",
        "C056",
    }
)
DATASETS = {"C": "09f_20261014_conclusion_synthesis_v1", "S": "09f_support_synthesis_20261014_v1"}
EXPECTED_COUNTS = {"C": 246, "S": 490}
CALIBRATION_COUNTS = {"C": 24, "S": 12}
CALIBRATION = "09f_20261014_binary_contract_calibration_v3"
PROJECTION_VERSION = "task09f.support_qualification_text_projection.v1"


def _json(path: Path) -> Any:
    """Decode a trusted-path artifact after its seal was checked."""
    return json.loads(path.read_text())


def _rows(path: Path) -> list[dict[str, Any]]:
    """Read JSONL in its published order without dropping empty or malformed rows."""
    return [json.loads(line) for line in path.read_text().splitlines()]


def _binding(path: Path) -> dict[str, Any]:
    """Record exact bytes, independent of parsed JSON object ordering."""
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "byte_size": len(data)}


def _within(root: Path, path: str) -> Path:
    """Reject escaping paths and symlinks before reading any referenced artifact."""
    selected = Path(path)
    if not selected.is_absolute():
        selected = root / selected
    if not selected.resolve().is_relative_to(root.resolve()):
        raise ValueError("Artifact path escapes its sealed development dataset")
    return selected


def _verify(path: Path, expected: dict[str, Any]) -> None:
    """Check byte length and SHA-256 without relying on mutable filesystem metadata."""
    actual = _binding(path)
    if any(actual[key] != expected[key] for key in ("sha256", "byte_size")):
        raise ValueError(f"Artifact checksum differs: {path.name}")


def _seal(root: Path, completion: dict[str, Any]) -> dict[str, Any]:
    """Verify every sealed file and exact inventory closure; never follow source pointers."""
    path = _within(root, completion["path"])
    if path != root / "completion.json":
        raise ValueError("Unexpected completion path")
    _verify(path, completion)
    manifest: dict[str, Any] = _json(path)
    expected = {"completion.json"}
    for item in manifest["inventory"]:
        file = _within(root, item["path"])
        relative = file.relative_to(root).as_posix()
        if relative in expected:
            raise ValueError("Duplicate sealed inventory entry")
        expected.add(relative)
        _verify(file, item)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError("Sealed inventory closure differs")
    return manifest


def _calibration(
    data_root: Path, repo: Path, component: Component
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bind accepted calibration overlap and its exact projected payloads, not new gold labels."""
    pointer_path = repo / "docs/specs/task09f_binary_calibration_result.json"
    pointer = _json(pointer_path)
    root = data_root / "pipelines/brisbane_baylands/task_09" / CALIBRATION
    if data_root / pointer["artifact_root_relative"] != root:
        raise ValueError("Unexpected calibration dataset")
    completion = dict(pointer["completion"], path=str(data_root / pointer["completion"]["path"]))
    _seal(root, completion)
    part = root / ("conclusion" if component == "C" else "support")
    provenance, inputs = _rows(part / "provenance.jsonl"), _rows(part / "judge_inputs.jsonl")
    key = "candidate_id" if component == "C" else "example_id"
    label_rows = _rows(part / "proposed_labels.jsonl")
    mapped = {}
    for source, value, label in zip(provenance, inputs, label_rows, strict=True):
        if source[key] != label[key]:
            raise ValueError("Calibration label alignment differs")
        expected = (
            label["expected_label"] == "yes"
            if component == "C"
            else label["expected_support_sufficient"]
        )
        if type(expected) is not bool:
            raise ValueError("Calibration labels must be Boolean")
        mapped[source[key]] = {"packet": value, "expected": expected}
    if len(mapped) != len(inputs) or len(mapped) != CALIBRATION_COUNTS[component]:
        raise ValueError("Calibration IDs or counts differ")
    return mapped, {
        "pointer": _binding(pointer_path),
        "completion": _binding(root / "completion.json"),
    }


def _coverage(
    rows: list[dict[str, Any]], component: Component
) -> tuple[dict[str, list[str]], list[dict[str, Any]]]:
    """Map only generated/shared slots; unresolved and inapplicable slots never become samples."""
    types: dict[str, list[str]] = defaultdict(list)
    excluded = []
    seen_slots: set[tuple[str, str]] = set()
    for row in rows:
        case = row["case_id"]
        slot = row["type" if component == "C" else "slot"]
        if case not in DEVELOPMENT_CASE_IDS or (case, slot) in seen_slots:
            raise ValueError("Coverage crosses development boundary or repeats a slot")
        seen_slots.add((case, slot))
        status = row["status" if component == "C" else "disposition"]
        sid = row.get("candidate_id" if component == "C" else "example_id")
        if status in ("generated", "shared"):
            if not isinstance(sid, str) or not sid:
                raise ValueError("Generated/shared coverage requires an example ID")
            types[sid].append(slot)
        elif status in ("unresolved", "inapplicable"):
            if sid is not None:
                raise ValueError("Excluded coverage unexpectedly identifies a generated example")
            excluded.append({"case_id": case, "type": slot, "status": status})
        else:
            raise ValueError("Unknown synthesis coverage disposition")
    return dict(types), excluded


def load_full_development(
    component: Component,
    *,
    data_root: Path | None = None,
    repo_root: Path = REPO,
) -> tuple[list[dict[str, Any]], dict[str, bool], dict[str, Any]]:
    """Load all published blind development examples with sidecar evaluation metadata.

    C conclusions are unchanged. S uses the already accepted calibration projection:
    qualification objects become their exact text strings; nothing else is rewritten.
    C051's reference-comparison hold does not exclude its reviewed no-reference S rows.
    No release, reserved/test payload, or source-document pointer is opened.
    """
    if component not in ("C", "S"):
        raise ValueError("Unknown binary component")
    base = data_root if data_root is not None else Path(os.environ["ER_COMMONS_DATA_ROOT"])
    root = base / "pipelines/brisbane_baylands/task_09" / DATASETS[component]
    dimension = "conclusion" if component == "C" else "support"
    pointer_path = repo_root / f"docs/specs/task09f_{dimension}_synthesis_result.json"
    pointer = _json(pointer_path)
    if pointer["dataset_id"] != DATASETS[component] or Path(pointer["artifact_root"]) != root:
        raise ValueError("Unexpected full-development dataset")
    manifest = _seal(root, pointer["artifacts"]["completion"])
    if manifest["dataset_id"] != DATASETS[component]:
        raise ValueError("Completion dataset identity differs")
    for item in pointer["artifacts"].values():
        _verify(_within(root, item["path"]), item)
    calibration, calibration_binding = _calibration(base, repo_root, component)
    coverage = _rows(root / "coverage.jsonl")
    types, excluded = _coverage(coverage, component)
    coverage_cases: dict[str, str] = {}
    for row in coverage:
        sid = row.get("candidate_id" if component == "C" else "example_id")
        if sid is not None:
            if sid in coverage_cases and coverage_cases[sid] != row["case_id"]:
                raise ValueError("Shared coverage crosses question identities")
            coverage_cases[sid] = row["case_id"]
    samples: list[dict[str, Any]] = []
    labels: dict[str, bool] = {}
    details: dict[str, Any] = {}
    if component == "C":
        inputs = _rows(root / "judge_inputs.jsonl")
        provenance = _rows(root / "provenance.jsonl")
        label_rows = _rows(root / "proposed_labels.jsonl")
        source_rows = list(zip(provenance, inputs, label_rows, strict=True))
    else:
        candidates = _rows(root / "candidate_manifest.jsonl")
        label_rows = _rows(root / "expected_labels.jsonl")
        label_map = {r["example_id"]: r for r in label_rows}
        if len(label_map) != len(label_rows):
            raise ValueError("Duplicate support label ID")
        source_rows = []
        for source in candidates:
            candidate_path = _within(root, source["candidate_path"])
            if _binding(candidate_path)["sha256"] != source["candidate_sha256"]:
                raise ValueError("Support candidate provenance hash differs")
            candidate = _json(candidate_path)
            if candidate != _json(_within(root, source["no_reference_path"])):
                raise ValueError("Common candidate/no-reference condition differs")
            source_rows.append((source, candidate, label_map[source["example_id"]]))
        if {s["example_id"] for s in candidates} != set(label_map):
            raise ValueError("Candidate and label inventories differ")
    for index, (source, original, label) in enumerate(source_rows, start=1):
        sid = source["candidate_id" if component == "C" else "example_id"]
        case = source["case_id"]
        if (
            case not in DEVELOPMENT_CASE_IDS
            or sid in labels
            or sid not in types
            or coverage_cases[sid] != case
        ):
            raise ValueError("Unexpected case, duplicate example or absent generated coverage")
        if label["candidate_id" if component == "C" else "example_id"] != sid:
            raise ValueError("Label/provenance row alignment differs")
        expected = label["expected_label"]
        if expected not in ("yes", "no"):
            raise ValueError("Expected labels must be exact yes/no proposals")
        packet = dict(original)
        if component == "C":
            if (
                source["payload_line"] != index
                or source["payload_sha256"] != hashlib.sha256(json_bytes(packet)).hexdigest()
            ):
                raise ValueError("Conclusion projection provenance differs")
            if label["case_id"] != case or set(label["types"]) != set(types[sid]):
                raise ValueError("Conclusion label metadata differs from coverage")
        else:
            if source["review_accepted"] is not True or label["review_accepted"] is not True:
                raise ValueError("Support example lacks independent acceptance")
            if source["paired_eligible"] != label["paired_eligible"]:
                raise ValueError("Support eligibility provenance differs")
            qualifications = packet["candidate_qualifications"]
            if not isinstance(qualifications, list) or any(
                not isinstance(q, dict) or set(q) != {"point_id", "text", "applies_to"}
                for q in qualifications
            ):
                raise ValueError("Unexpected published qualification shape")
            packet["candidate_qualifications"] = [q["text"] for q in qualifications]
        validate_input(component, packet)
        if sid in calibration and (
            packet != calibration[sid]["packet"]
            or (expected == "yes") != calibration[sid]["expected"]
        ):
            raise ValueError("Full dataset projection differs from accepted calibration")
        samples.append(
            {"sample_id": sid, "case_id": case, "scope": "development", "packet": packet}
        )
        labels[sid] = expected == "yes"
        details[sid] = {
            "case_id": case,
            "types": types[sid],
            "calibration_seen": sid in calibration,
            "label_status": label["label_status"],
            "source_payload_sha256": stable_json_sha256(original),
            "projected_payload_sha256": stable_json_sha256(packet),
            "paired_eligible": source.get("paired_eligible"),
        }
    if len(samples) != EXPECTED_COUNTS[component] or set(types) != set(labels):
        raise ValueError("Published example counts or coverage ID set differ")
    if {s["case_id"] for s in samples} != DEVELOPMENT_CASE_IDS or not set(calibration) <= set(
        labels
    ):
        raise ValueError("Development question coverage or calibration overlap differs")
    payload_hashes = [stable_json_sha256(sample["packet"]) for sample in samples]
    if len(set(payload_hashes)) != len(payload_hashes):
        raise ValueError("Duplicate projected judge payload")
    metadata = {
        "component": component,
        "dataset_id": DATASETS[component],
        "pointer": _binding(pointer_path),
        "completion": _binding(root / "completion.json"),
        "calibration": calibration_binding,
        "projection_version": "unchanged_published_conclusion"
        if component == "C"
        else PROJECTION_VERSION,
        "label_basis": "published_independently_reviewed_agent_proposals_not_human_gold",
        "counts": {
            "examples": len(samples),
            "questions": len(DEVELOPMENT_CASE_IDS),
            "labels": dict(Counter(labels.values())),
            "calibration_seen": len(calibration),
        },
        "examples": details,
        "excluded_slots": excluded,
        "reference_holds": pointer.get("reference_holds", []),
        "reference_hold_policy": (
            "paired-reference eligibility only; reviewed blind support rows remain eligible"
        ),
        "inventory_verified": True,
    }
    return samples, labels, metadata
