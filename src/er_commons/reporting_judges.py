"""Offline historical judge-label agreement, separate from target answer pass rates."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

from inspect_ai.log import read_eval_log

from er_commons.artifact_io import sha256_file

_CLASSES = ("clean_abstention", "substantive", "ambiguous")


def _read(path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    """Read a bound JSON object; changed sealed bytes fail closed."""
    if expected_sha256 is not None and sha256_file(path) != expected_sha256:
        raise ValueError(f"historical judge source checksum mismatch: {path}")
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected historical object: {path}")
    return cast(dict[str, Any], value)


def _ratio(numerator: int, denominator: int) -> float | None:
    """Keep zero-denominator metrics unavailable, never silently perfect."""
    return numerator / denominator if denominator else None


def agreement_from_confusion(
    matrix: dict[str, dict[str, int]], *, planned: int
) -> list[dict[str, Any]]:
    """Compute valid-only one-vs-rest metrics, keeping invalid slots outside labels."""
    classes = list(matrix)
    if not classes or any(set(row) != set(classes) for row in matrix.values()):
        raise ValueError("confusion matrix must be square with exact class coverage")
    if any(type(n) is not int or n < 0 for row in matrix.values() for n in row.values()):
        raise ValueError("confusion counts must be nonnegative integers")
    valid = sum(sum(row.values()) for row in matrix.values())
    if type(planned) is not int or planned < valid:
        raise ValueError("planned denominator cannot be smaller than valid confusion counts")
    correct = sum(matrix[c][c] for c in classes)
    shared = {
        "planned": planned,
        "valid": valid,
        "invalid_or_missing": planned - valid,
        "correct": correct,
        "coverage": _ratio(valid, planned),
        "accuracy_valid_only": _ratio(correct, valid),
        "accuracy_failure_inclusive": _ratio(correct, planned),
        "metric_basis": "historical_judge_label_agreement",
        "zero_denominator": "unavailable",
    }
    rows: list[dict[str, Any]] = []
    for label in classes:
        tp = matrix[label][label]
        fp = sum(matrix[other][label] for other in classes if other != label)
        fn = sum(matrix[label][other] for other in classes if other != label)
        rows.append(
            {
                **shared,
                "positive_class": label,
                "support_valid": tp + fn,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": valid - tp - fp - fn,
                "precision": _ratio(tp, tp + fp),
                "recall": _ratio(tp, tp + fn),
                "f1": _ratio(2 * tp, 2 * tp + fp + fn),
            }
        )
    f1s = [row["f1"] for row in rows]
    macro = sum(f1s) / len(f1s) if all(v is not None for v in f1s) else None
    for row in rows:
        row["macro_f1_valid_only"] = macro
    return rows


def _append_matrix(
    tables: dict[str, list[dict[str, Any]]],
    metadata: dict[str, Any],
    matrix: dict[str, dict[str, int]],
    planned: int,
) -> None:
    """Emit long confusion and metric tables with identical provenance keys."""
    rows = agreement_from_confusion(matrix, planned=planned)
    tables["judge_agreement"].extend(
        {**metadata, **row}
        for row in rows
        if metadata["component"] == "A" or row["positive_class"] == "true"
    )
    tables["judge_confusion"].extend(
        {**metadata, "expected": expected, "predicted": predicted, "count": count}
        for expected, cells in matrix.items()
        for predicted, count in cells.items()
    )


def build_historical_judge_tables(repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    """Replay only the exact Task 09G-selected development summaries, without calls."""
    tables: dict[str, list[dict[str, Any]]] = {
        name: []
        for name in (
            "judge_agreement",
            "judge_confusion",
            "judge_observations",
            "judge_sources",
            "judge_repeatability",
            "judge_item_repeatability",
        )
    }
    freeze_path = repo_root / "docs/specs/task09g_judge_freeze_v1.json"
    freeze = _read(freeze_path)
    bindings = {item["path"]: item["sha256"] for item in freeze["evidence"]}
    tables["judge_sources"].append({"path": str(freeze_path), "sha256": sha256_file(freeze_path)})

    def source(name: str) -> dict[str, Any]:
        """Verify a tracked result against the accepted freeze."""
        relative = f"docs/specs/{name}"
        path = repo_root / relative
        value = _read(path, bindings[relative])
        tables["judge_sources"].append({"path": str(path), "sha256": bindings[relative]})
        return value

    def summary(pointer: dict[str, Any]) -> dict[str, Any]:
        """Verify only the explicitly referenced historical development report."""
        ref = pointer["summary"]
        value = _read(Path(ref["path"]), ref["sha256"])
        tables["judge_sources"].append({"path": ref["path"], "sha256": ref["sha256"]})
        return value

    def meta(component: str, run: str, dataset: str, labels: str) -> dict[str, Any]:
        """Bind selected judge version and distinguish historical label provenance."""
        return {
            "component": component,
            **freeze["components"][component],
            "run_id": run,
            "dataset_panel": dataset,
            "label_provenance": labels,
            "evaluation_unit": "point_repeat" if component == "G" else "candidate_repeat",
            "exposure": "historical_development_not_held_out",
            "partition": "all",
            "epochs": 3,
        }

    a_pointer = source("task09f1_a_full_development_v2_result.json")
    a = summary(a_pointer)["models"]["luna"]
    metadata = meta(
        "A",
        a_pointer["run_id"],
        a_pointer["panel"]["dataset_id"],
        a_pointer["panel"]["label_status"],
    )
    metadata["calibration_partition_availability"] = "not_reconstructable_from_saved_summary"
    matrix = a["confusion_expected_rows_predicted_columns"]
    if set(matrix) != set(_CLASSES):
        raise ValueError("historical A class vocabulary changed")
    _append_matrix(tables, metadata, matrix, a["partitions"]["all"]["planned_judgments"])
    for name in ("flagged", "unflagged"):
        partition = a["partitions"][name]
        tables["judge_agreement"].append(
            {
                **metadata,
                "partition": name,
                "positive_class": "unavailable",
                "planned": partition["planned_judgments"],
                "valid": partition["valid"],
                "correct": partition["correct"],
                "invalid_or_missing": partition["planned_judgments"] - partition["valid"],
                "coverage": _ratio(partition["valid"], partition["planned_judgments"]),
                "accuracy_valid_only": partition["accuracy_valid_only"],
                "accuracy_failure_inclusive": partition["accuracy_failure_inclusive"],
                "precision": None,
                "recall": None,
                "f1": None,
                "confusion_unavailable_reason": "saved_partition_summary_has_no_confusion",
                "metric_basis": "historical_judge_label_agreement",
            }
        )

    completion_ref = a_pointer["completion"]
    completion = _read(Path(completion_ref["path"]), completion_ref["sha256"])
    tables["judge_sources"].append(completion_ref)
    log_path = a["log_path"]
    log_ref = next(ref for ref in completion["artifacts"] if ref["path"] == log_path)
    if sha256_file(Path(log_path)) != log_ref["sha256"]:
        raise ValueError("historical A log checksum mismatch")
    tables["judge_sources"].append(log_ref)
    a_observations = _a_observations(read_eval_log(log_path), metadata)
    _append_repeatability(
        tables, a_observations, metadata, a["partitions"]["all"]["planned_judgments"]
    )

    g = source("task09f1_g_full_development_v3_result.json")
    condition = g["conditions"][freeze["components"]["G"]["condition_id"]]
    metadata = meta("G", Path(g["run_root"]).name, g["panel"]["scope"], g["panel"]["label_status"])
    metadata["positive_class_definition"] = "point_supported_by_owned_evidence"
    metadata["calibration_label_provenance"] = g["panel"]["calibration_provenance"]["label_status"]
    metadata["excluded_unresolved_candidates"] = len(g["panel"]["excluded_unresolved"])
    combined = {label: {pred: 0 for pred in ("false", "true")} for label in ("false", "true")}
    for name in ("calibration_overlap", "outside_calibration"):
        partition = condition[name]
        matrix = partition["confusion_expected_rows_predicted_columns"]
        _append_matrix(tables, {**metadata, "partition": name}, matrix, partition["planned"])
        for label, cells in matrix.items():
            for predicted, count in cells.items():
                combined[label][predicted] += count
    _append_matrix(tables, metadata, combined, condition["planned"])

    g_ref = g["artifacts"]["report"]
    g_report = _read(Path(g_ref["path"]), g_ref["sha256"])
    tables["judge_sources"].append(g_ref)
    g_observations = []
    overlap = set(g["panel"]["calibration_overlap_ids"])
    for row in g_report["conditions"][freeze["components"]["G"]["condition_id"]]["observations"]:
        g_observations.append(
            {
                **metadata,
                "sample_id": row["sample_id"],
                "case_id": row["case_id"],
                "repeat": row["epoch"],
                "repeat_identity_basis": "saved_observation_epoch",
                "partition": "calibration_overlap"
                if row["sample_id"] in overlap
                else "outside_calibration",
                "expected": row["expected"],
                "decision": row["decision"],
                "status": row["status"],
                "valid": row["status"] == "evaluated" and type(row["decision"]) is bool,
            }
        )
    _append_repeatability(tables, g_observations, metadata, condition["planned"])

    sc_pointer = source("task09f_inspect_full_dev3_result.json")
    sc = summary(sc_pointer)
    for component in ("S", "C"):
        condition_id = freeze["components"][component]["condition_id"]
        cell = sc["cells"][f"{condition_id}:{component}"]
        metadata = meta(
            component,
            Path(sc_pointer["artifact_root_relative"]).name,
            "published_support_synthesis" if component == "S" else "published_conclusion_synthesis",
            sc["label_basis"],
        )
        metadata["positive_class_definition"] = (
            "support_sufficient" if component == "S" else "conclusion_adequate"
        )
        observations = _binary_observations(cell["per_example"], metadata)
        if len(observations) != cell["planned_observations"]:
            raise ValueError("historical binary summary planned coverage mismatch")
        partitions = ["all", *sorted({row["partition"] for row in observations})]
        for partition in partitions:
            selected = [
                row for row in observations if partition == "all" or row["partition"] == partition
            ]
            matrix = {label: {pred: 0 for pred in ("false", "true")} for label in ("false", "true")}
            for row in selected:
                if row["valid"]:
                    matrix[str(row["expected"]).lower()][str(row["decision"]).lower()] += 1
            _append_matrix(tables, {**metadata, "partition": partition}, matrix, len(selected))
        _append_repeatability(tables, observations, metadata, cell["planned_observations"])
    return tables


def _binary_observations(
    examples: list[dict[str, Any]], metadata: dict[str, Any]
) -> list[dict[str, Any]]:
    """Preserve recorded repeat order; reject duplicate or incomplete example records."""
    seen: set[str] = set()
    observations = []
    for example in examples:
        sample_id = example["sample_id"]
        if sample_id in seen:
            raise ValueError("duplicate historical sample identity")
        seen.add(sample_id)
        if type(example["expected"]) is not bool:
            raise ValueError("historical binary label must be boolean")
        if len(example["decisions"]) != 3 or len(example["statuses"]) != 3:
            raise ValueError("historical summary must retain three planned repeat slots")
        for epoch, (decision, status) in enumerate(
            zip(example["decisions"], example["statuses"], strict=True), start=1
        ):
            observations.append(
                {
                    **metadata,
                    "sample_id": sample_id,
                    "case_id": example["case_id"],
                    "repeat": epoch,
                    "repeat_identity_basis": "saved_per_example_epoch_order",
                    "partition": example["exposure_stratum"],
                    "expected": example["expected"],
                    "decision": decision,
                    "status": status,
                    "valid": status == "evaluated" and type(decision) is bool,
                }
            )
    return observations


def _a_observations(log: Any, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    """Read exact saved A labels and epochs; invalid predictions remain unavailable."""
    observations = []
    for sample in log.samples or []:
        source_metadata = sample.metadata or {}
        score = (sample.scores or {}).get("no_answer_score")
        details = score.metadata or {} if score is not None else {}
        expected = sample.target
        if expected not in _CLASSES:
            raise ValueError("historical A expected class is invalid")
        decision = details.get("classification")
        status = details.get("status", "missing")
        observations.append(
            {
                **metadata,
                "sample_id": str(sample.id),
                "case_id": source_metadata["case_id"],
                "candidate_id": source_metadata["candidate_record"]["candidate_id"],
                "payload_sha256": source_metadata["payload_sha256"],
                "repeat": sample.epoch,
                "repeat_identity_basis": "saved_native_log_epoch",
                "partition": "flagged" if source_metadata["label_uncertain"] else "unflagged",
                "expected": expected,
                "decision": decision,
                "status": status,
                "valid": status == "evaluated" and decision in _CLASSES and sample.error is None,
            }
        )
    return observations


def judge_repeatability(
    observations: list[dict[str, Any]], metadata: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Align each synthetic item across three epochs, never pooling correctness across items."""
    groups: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in observations:
        sample_id, epoch = row["sample_id"], row["repeat"]
        if metadata.get("component") == "A":
            if row["expected"] not in _CLASSES or (
                row["valid"] and row["decision"] not in _CLASSES
            ):
                raise ValueError("historical A class vocabulary changed")
        elif type(row["expected"]) is not bool or (
            row["valid"] and type(row["decision"]) is not bool
        ):
            raise ValueError("historical binary label must be boolean")
        if type(epoch) is not int or epoch not in (1, 2, 3):
            raise ValueError("historical repeat must be 1, 2 or 3")
        if epoch in groups[sample_id]:
            raise ValueError("duplicate historical sample/repeat identity")
        groups[sample_id][epoch] = row
    items = []
    for sample_id, epochs in sorted(groups.items()):
        first = next(iter(epochs.values()))
        for row in epochs.values():
            if any(
                row.get(key) != first.get(key)
                for key in (
                    "case_id",
                    "partition",
                    "expected",
                    "component",
                    "run_id",
                    "candidate_id",
                    "payload_sha256",
                )
            ):
                raise ValueError(
                    "historical item identity or expected label changes across repeats"
                )
        outcomes = [
            bool(epochs[epoch]["decision"] == first["expected"])
            if epoch in epochs and epochs[epoch]["valid"]
            else None
            for epoch in (1, 2, 3)
        ]
        complete = all(value is not None for value in outcomes)
        correct = sum(value is True for value in outcomes)
        items.append(
            {
                **metadata,
                "sample_id": sample_id,
                "case_id": first["case_id"],
                "partition": first["partition"],
                "expected": first["expected"],
                "evaluation_unit": "point" if metadata.get("component") == "G" else "candidate",
                "correct_by_repeat": outcomes,
                "observed_correct": correct,
                "valid_repeats": sum(value is not None for value in outcomes),
                "complete_triple": complete,
                "correct_count": correct if complete else None,
                "correct_at_least_once": correct > 0 if complete else None,
                "correct_all_three": correct == 3 if complete else None,
                "repeat_identity_basis": first["repeat_identity_basis"],
            }
        )
    summaries = []
    for partition in ["all", *sorted({item["partition"] for item in items})]:
        selected = [item for item in items if partition == "all" or item["partition"] == partition]
        complete_items = [item for item in selected if item["complete_triple"]]
        distribution = {
            f"correct_{count}": sum(item["correct_count"] == count for item in complete_items)
            for count in range(4)
        }
        at_least = sum(item["correct_count"] > 0 for item in complete_items)
        all_three = distribution["correct_3"]
        summaries.append(
            {
                **metadata,
                "partition": partition,
                "evaluation_unit": "point" if metadata.get("component") == "G" else "candidate",
                "metric_basis": "synthetic_judge_label_agreement_same_item_three_repeats",
                "planned_items": len(selected),
                "complete_triples": len(complete_items),
                "unresolved_triples": len(selected) - len(complete_items),
                **distribution,
                "correct_at_least_once": at_least,
                "correct_all_three": all_three,
                "correct_at_least_once_fraction": _ratio(at_least, len(selected)),
                "correct_all_three_fraction": _ratio(all_three, len(selected)),
                "correct_at_least_once_complete_fraction": _ratio(at_least, len(complete_items)),
                "correct_all_three_complete_fraction": _ratio(all_three, len(complete_items)),
                "observed_correct": sum(item["observed_correct"] for item in selected),
                "valid_repeats": sum(item["valid_repeats"] for item in selected),
                "planned_repeats": 3 * len(selected),
                "at_least_once_observed_lower_bound": sum(
                    item["observed_correct"] > 0 for item in selected
                ),
                "basis": "exact_saved_item_repeat_records",
            }
        )
    return items, summaries


def _append_repeatability(
    tables: dict[str, list[dict[str, Any]]],
    observations: list[dict[str, Any]],
    metadata: dict[str, Any],
    planned: int,
) -> None:
    """Require the bound roster and saved confusion to agree with aligned observations."""
    items, summaries = judge_repeatability(observations, metadata)
    if len(observations) != planned or len(items) * 3 != planned:
        raise ValueError("historical repeatability planned coverage mismatch")
    matching = [
        row
        for row in tables["judge_agreement"]
        if row["component"] == metadata["component"] and row["partition"] == "all"
    ]
    if matching and (
        summaries[0]["observed_correct"] != matching[0]["correct"]
        or summaries[0]["valid_repeats"] != matching[0]["valid"]
    ):
        raise ValueError("historical repeatability and confusion disagree")
    tables["judge_observations"].extend(observations)
    tables["judge_item_repeatability"].extend(items)
    tables["judge_repeatability"].extend(summaries)
