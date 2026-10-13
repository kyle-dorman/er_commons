"""Post-run proposed-label diagnostics; this module never constructs model requests."""

from __future__ import annotations

import copy
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any

import ijson  # type: ignore[import-untyped]

from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_comparison_panel import load_dev3, load_development_panel
from er_commons.grounding_comparison_semantics import point_inputs
from er_commons.grounding_metrics import Label, classification_metrics
from er_commons.grounding_records import SavedGroundingSample
from er_commons.synthetic_intake import verify_binding


def _selected_labels(path: Path, ids: set[str]) -> dict[str, dict[str, Any]]:
    """Build only selected expectation objects from the mixed development container."""
    result = {}
    buffered: list[tuple[str, Any]] = []
    builder: Any = None
    selected: bool | None = None
    with path.open("rb") as stream:
        for prefix, event, value in ijson.parse(stream):
            if prefix == "item" and event == "start_map":
                buffered, builder, selected = [], None, None
            if not prefix.startswith("item"):
                continue
            if selected is None:
                buffered.append((event, value))
                if prefix == "item.sample_id" and event == "string":
                    selected = value in ids
                    if selected:
                        builder = ijson.ObjectBuilder()
                        for old_event, old_value in buffered:
                            builder.event(old_event, old_value)
                    buffered = []
            elif selected:
                builder.event(event, value)
            if prefix == "item" and event == "end_map":
                if selected is None:
                    raise ValueError("Expectation lacks routing identity")
                if selected:
                    row = builder.value
                    if row["sample_id"] in result:
                        raise ValueError("Duplicate selected expectation")
                    result[row["sample_id"]] = row["expectation"]
    if set(result) != ids:
        raise ValueError("Missing selected expectations")
    return result


def _records(directory: Path, ids: set[str]) -> dict[str, dict[str, Any]]:
    """Read the latest completed observation per sample; probes never enter denominators."""
    records = {}
    for sample_id in sorted(ids):
        sample_dir = directory / "requests" / stable_json_sha256({"sample_id": sample_id})
        candidates = sorted(sample_dir.glob("result_*.json"))
        for path in reversed(candidates):
            value = json.loads(path.read_text())
            if value.get("sample_id") != sample_id:
                raise ValueError("Saved result sample identity differs")
            if value.get("evaluation_denominator") is False:
                continue
            records[sample_id] = value
            break
    return records


def _confusion() -> dict[str, int]:
    """Create complete binary diagnostic cells, including zero-count cells."""
    return {
        "true_positive": 0,
        "false_positive": 0,
        "true_negative": 0,
        "false_negative": 0,
        "compared": 0,
    }


def _observe(matrix: dict[str, int], predicted: bool, proposed: bool) -> None:
    """Count strict boolean predictions against proposals without interpreting truth."""
    if type(predicted) is not bool or type(proposed) is not bool:
        raise ValueError("Comparison requires strict boolean predictions and proposals")
    key = ("true_" if predicted == proposed else "false_") + (
        "positive" if predicted else "negative"
    )
    matrix[key] += 1
    matrix["compared"] += 1


def _source_links(sample: SavedGroundingSample, point_id: str | None) -> list[dict[str, Any]]:
    """Link disagreements to original citation/source identities without copying source text."""
    evidence = sample.packet["payload"]["evidence"]
    if point_id is not None:
        matches = [p for p in point_inputs(sample.packet) if p["point"]["point_id"] == point_id]
        if len(matches) != 1:
            raise ValueError("Compared point absent from original packet")
        evidence = matches[0]["evidence"]
    return [
        {
            key: item[key]
            for key in ("citation_id", "resolution", "source_id", "canonical_target")
            if key in item
        }
        for item in evidence
    ]


def _coverage_metrics(
    samples: list[SavedGroundingSample],
    labels: dict[str, dict[str, Any]],
    records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Score every eligible proposal, retaining invalid or absent predictions as failures."""
    names = (
        "original_claim_support",
        "claim_review_support",
        "conclusion_support",
        "numeric_score",
    )
    targets: dict[str, list[Label]] = {name: [] for name in names}
    predictions: dict[str, list[Label | None]] = {name: [] for name in names}
    for sample in samples:
        proposed = labels[sample.sample_id]
        record = records.get(sample.sample_id, {})
        valid = [stage for stage in record.get("stages", []) if stage["status"] == "validated"]
        claims = {
            stage["result"]["decision"]["point_id"]: stage["result"]["decision"]["supported"]
            for stage in valid
            if stage["kind"] == "point"
        }
        if len(claims) != sum(stage["kind"] == "point" for stage in valid):
            raise ValueError("Duplicate original claim prediction")
        conclusions = [
            stage["result"]["decision"] for stage in valid if stage["kind"] == "conclusion"
        ]
        if len(conclusions) > 1:
            raise ValueError("Multiple conclusion observations for one sample")
        conclusion = conclusions[0] if conclusions else {}
        reviews = {row["point_id"]: row["supported"] for row in conclusion.get("point_reviews", [])}
        if len(reviews) != len(conclusion.get("point_reviews", [])):
            raise ValueError("Duplicate claim-review prediction")
        expected_points = {
            row["point_id"]: row["supported"] for row in proposed["point_expectations"]
        }
        if len(expected_points) != len(proposed["point_expectations"]):
            raise ValueError("Duplicate claim expectation")
        if not set(claims) <= set(expected_points) or not set(reviews) <= set(expected_points):
            raise ValueError("Prediction references an unexpected claim")
        for point_id, expected in expected_points.items():
            if type(expected) is not bool:
                raise ValueError("Claim expectations must be strict booleans")
            for name, observed in (
                ("original_claim_support", claims),
                ("claim_review_support", reviews),
            ):
                targets[name].append(expected)
                predictions[name].append(observed.get(point_id))
        expected = proposed["conclusion_supported"]
        if expected is not None:
            if type(expected) is not bool:
                raise ValueError("Conclusion expectation must be a strict boolean or null")
            targets["conclusion_support"].append(expected)
            predictions["conclusion_support"].append(conclusion.get("conclusion_supported"))
        expected_score = proposed["score"]
        if expected_score is not None:
            targets["numeric_score"].append(expected_score)
            predictions["numeric_score"].append(
                record.get("score") if record.get("status") == "scored" else None
            )
    return {
        "schema_version": "task09e2.coverage_metrics.v2",
        "failure_policy": (
            "Missing and invalid outputs are incorrect and add a false negative "
            "for their expected class."
        ),
        "macro_policy": (
            "Average all declared classes; zero-division class F1 is zero. "
            "No eligible items yields null."
        ),
        **{
            name: classification_metrics(
                targets[name],
                predictions[name],
                classes=(0, 1, 2) if name == "numeric_score" else (False, True),
            )
            for name in names
        },
    }


def _condition_report(
    samples: list[SavedGroundingSample],
    labels: dict[str, dict[str, Any]],
    records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Include missing/error samples while comparing every available valid stage prediction."""
    gates, points, conclusions = _confusion(), _confusion(), _confusion()
    statuses: Counter[str] = Counter()
    stages: Counter[str] = Counter()
    scores: Counter[str] = Counter()
    quotes: Counter[str] = Counter()
    strict: Counter[str] = Counter()
    links = []
    valid_ids, numeric_ids = [], []
    usage_totals: Counter[str] = Counter()
    usage_known: Counter[str] = Counter()
    latency = 0.0
    reused = 0
    for sample in samples:
        key = sample.sample_id
        proposed = labels[key]
        record = records.get(key)
        if record is None:
            statuses["missing"] += 1
            continue
        status = record["status"]
        statuses[status] += 1
        latency += record.get("elapsed_seconds", 0.0)
        if status in {"scored", "not_applicable"}:
            valid_ids.append(key)
            scores[str(record["score"])] += 1
            if status == "scored":
                numeric_ids.append(key)
        expected_points = {p["point_id"]: p["supported"] for p in proposed["point_expectations"]}
        seen: set[tuple[str, str]] = set()
        for stage in record.get("stages", []):
            kind, stage_key = stage["kind"], stage.get("key", stage["kind"])
            if (kind, stage_key) in seen:
                raise ValueError("Duplicate saved stage observation")
            seen.add((kind, stage_key))
            stages[stage["status"]] += 1
            reused += bool(stage.get("reused", False))
            # Latest observations count each original receipt once, including saved reuse.
            for name in (
                "input_tokens",
                "output_tokens",
                "cache_read_tokens",
                "cache_write_tokens",
            ):
                value = stage.get("usage", {}).get(name)
                if value is not None:
                    if type(value) is not int or value < 0:
                        raise ValueError("Invalid saved native usage")
                    usage_totals[name] += value
                    usage_known[name] += 1
            if stage["status"] != "validated":
                continue
            result = stage["result"]
            strict[result.get("strict_legacy", {}).get("status", "unavailable")] += 1
            decision = result["decision"]
            diagnostic = result.get("quotation_diagnostics", {"status": "not_applicable"})
            quotes[diagnostic["status"]] += 1
            if diagnostic.get("missing_quotation"):
                quotes["missing_quotation"] += 1
            for locator in diagnostic.get("locators", []):
                quotes["literal_match" if locator["literal_match"] else "nonliteral_excerpt"] += 1
            for issue in diagnostic.get("unsupported_assertions", []):
                quotes[
                    "literal_assertion" if issue["literal_match"] else "nonliteral_assertion"
                ] += 1
            if kind == "abstention":
                classification = decision["classification"]
                if classification != "ambiguous":
                    _observe(
                        gates, classification == "clean_abstention", proposed["clean_abstention"]
                    )
            elif kind == "point":
                point_id = decision["point_id"]
                _observe(points, decision["supported"], expected_points[point_id])
                if decision["supported"] != expected_points[point_id]:
                    links.append(
                        {
                            "sample_id": key,
                            "case_id": sample.case_id,
                            "stage": "point",
                            "point_id": point_id,
                            "predicted": decision["supported"],
                            "proposed": expected_points[point_id],
                            "sources": _source_links(sample, point_id),
                        }
                    )
            elif kind == "conclusion":
                predicted, expected = (
                    decision["conclusion_supported"],
                    proposed["conclusion_supported"],
                )
                if predicted is not None and expected is not None:
                    _observe(conclusions, predicted, expected)
                    if predicted != expected:
                        links.append(
                            {
                                "sample_id": key,
                                "case_id": sample.case_id,
                                "stage": "conclusion",
                                "predicted": predicted,
                                "proposed": expected,
                                "sources": _source_links(sample, None),
                            }
                        )
                for review in decision["point_reviews"]:
                    prior = next(
                        (
                            s["result"]["decision"]["supported"]
                            for s in record["stages"]
                            if s["kind"] == "point"
                            and s["status"] == "validated"
                            and s["result"]["decision"]["point_id"] == review["point_id"]
                        ),
                        None,
                    )
                    if prior is not None and prior != review["supported"]:
                        links.append(
                            {
                                "sample_id": key,
                                "case_id": sample.case_id,
                                "stage": "review_disagreement",
                                "point_id": review["point_id"],
                                "point_prediction": prior,
                                "review_prediction": review["supported"],
                                "sources": _source_links(sample, review["point_id"]),
                            }
                        )
    return {
        "metrics_v2": _coverage_metrics(samples, labels, records),
        "population": len(samples),
        "observed_answers": len(records),
        "valid_answers": len(valid_ids),
        "numeric_answers": len(numeric_ids),
        "valid_sample_ids": valid_ids,
        "numeric_sample_ids": numeric_ids,
        "statuses": dict(statuses),
        "stage_statuses": dict(stages),
        "score_distribution": dict(scores),
        "abstention": {
            **gates,
            "population": len(samples),
            "false_exemptions": gates["false_positive"],
            "misses": gates["false_negative"],
        },
        "point_support": {
            **points,
            "population": sum(len(x["point_expectations"]) for x in labels.values()),
        },
        "conclusion_support": {
            **conclusions,
            "population": sum(x["conclusion_supported"] is not None for x in labels.values()),
        },
        "quotation_diagnostics": dict(quotes),
        "strict_legacy_statuses": dict(strict),
        "source_linked_disagreements": links,
        "elapsed_seconds": latency,
        "native_usage": {
            name: usage_totals[name] if usage_known[name] else None
            for name in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens")
        },
        "usage_receipt_counts": dict(usage_known),
        "usage_note": (
            "One original receipt per latest stage; saved reuse is not an additional billed call."
        ),
        "saved_stages_reused": reused,
        "estimated_cost_usd": None,
        "billed_cost_usd": None,
        "cost_note": (
            "Use sealed dispatch reservation ledger for conservative bounds; "
            "no billed figures supplied."
        ),
    }


def report_records(
    samples: list[SavedGroundingSample],
    labels: dict[str, dict[str, Any]],
    runs: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    """Compare completed observations after execution, with all-panel and matched-valid views."""
    ids = {s.sample_id for s in samples}
    if (
        len(ids) != len(samples)
        or set(labels) != ids
        or any(not set(r) <= ids for r in runs.values())
    ):
        raise ValueError("Report populations differ from selected panel")
    reports = {name: _condition_report(samples, labels, rows) for name, rows in runs.items()}
    matched = []
    for left, right in itertools.combinations(reports, 2):
        common = sorted(
            set(reports[left]["valid_sample_ids"]) & set(reports[right]["valid_sample_ids"])
        )
        numeric = [
            key
            for key in common
            if runs[left][key]["status"] == runs[right][key]["status"] == "scored"
        ]
        matched.append(
            {
                "left": left,
                "right": right,
                "population": len(samples),
                "matched_valid": len(common),
                "matched_numeric": len(numeric),
                "numeric_score_agreement": sum(
                    runs[left][key]["score"] == runs[right][key]["score"] for key in numeric
                ),
                "matched_sample_ids": common,
            }
        )
    return {
        "schema_version": "task09e1.postrun_analysis.v1",
        "population": len(samples),
        "conditions": reports,
        "matched_valid": matched,
        "limitations": [
            "Expectations are uncalibrated synthetic proposals, not ground truth.",
            "Missing and invalid answers remain in the full-panel denominator.",
            "Source links support review; no new semantic truth is inferred.",
        ],
    }


def analyze_runs(
    manifest_path: Path,
    run_dirs: dict[str, Path],
    *,
    panel: str = "dev3",
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    """Load restricted proposals only in this explicit post-Inspect analysis operation."""
    if expected_sha256 is None:
        if panel != "dev3":
            raise ValueError("Non-Dev3 analysis requires an expected manifest hash")
        samples, bindings = load_dev3(manifest_path)
    else:
        samples, bindings = load_development_panel(manifest_path, panel, expected_sha256)
    manifest = json.loads(manifest_path.read_text())
    path = verify_binding(
        manifest["artifacts"]["restricted_expectations.json"], manifest_path.parent
    )
    ids = {s.sample_id for s in samples}
    expected = _selected_labels(path, ids)
    rows = {r["sample_id"]: r for r in manifest["samples"] if r["sample_id"] in ids}
    labels = {}
    for sample in samples:
        value = expected[sample.sample_id]
        if stable_json_sha256(value) != rows[sample.sample_id]["expectation_sha256"]:
            raise ValueError("Selected expectation binding differs")
        if value["case_id"] != sample.case_id or value["comparison_eligible"] is not True:
            raise ValueError("Selected expectation eligibility differs")
        label = copy.deepcopy(value["grounding"])
        mapping = sample.packet["mappings"]["candidate_points"]
        for point in label["point_expectations"]:
            point["point_id"] = mapping[point["point_id"]]
        if [p["point_id"] for p in label["point_expectations"]] != [
            p["point"]["point_id"] for p in point_inputs(sample.packet)
        ]:
            raise ValueError("Proposal point coverage differs")
        labels[sample.sample_id] = label
    report = report_records(
        samples, labels, {name: _records(root, ids) for name, root in run_dirs.items()}
    )
    report["panel_binding"] = bindings["manifest"]
    report["expectations_binding"] = manifest["artifacts"]["restricted_expectations.json"]
    return report
