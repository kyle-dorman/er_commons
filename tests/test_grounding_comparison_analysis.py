"""Post-run report denominators, proposal comparisons and restricted-label isolation."""

import copy
import json
from pathlib import Path

import pytest
from test_grounding_inspect import sample

from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_comparison_analysis import _records, _selected_labels, report_records


def label() -> dict:
    """Return an invented proposal with no calibrated-correctness claim."""
    return {
        "clean_abstention": False,
        "conclusion_supported": True,
        "score": 2,
        "point_expectations": [{"point_id": "P2", "supported": True}],
    }


def stage(kind: str, decision: dict, key: str | None = None, **extra: object) -> dict:
    """Represent a completed invented stage in the runtime's persisted result shape."""
    return {
        "kind": kind,
        "key": key or kind,
        "status": "validated",
        "reused": False,
        "result": {"decision": decision, "quotation_diagnostics": {"status": "not_applicable"}},
        **extra,
    }


def record(key: str = "fixture") -> dict:
    """Provide a matched valid score with all three original stages."""
    return {
        "sample_id": key,
        "case_id": "invented",
        "status": "scored",
        "score": 2,
        "elapsed_seconds": 0.1,
        "stages": [
            stage("abstention", {"classification": "substantive"}),
            stage("point", {"point_id": "P2", "supported": True}, "P2"),
            stage(
                "conclusion",
                {
                    "clean_abstention": False,
                    "conclusion_supported": True,
                    "point_reviews": [{"point_id": "P2", "supported": True}],
                },
            ),
        ],
    }


def test_all_69_denominator_remains_with_missing_results() -> None:
    """A blocked condition reports 0/69 instead of dropping unobserved answers."""
    samples = [sample(str(i)) for i in range(69)]
    report = report_records(samples, {s.sample_id: label() for s in samples}, {"blocked": {}})
    result = report["conditions"]["blocked"]
    assert report["population"] == 69
    assert result["observed_answers"] == result["valid_answers"] == 0
    assert result["statuses"] == {"missing": 69}
    assert result["estimated_cost_usd"] is None
    assert result["native_usage"]["cache_read_tokens"] is None


def test_matched_valid_denominator_is_separate_from_all_answers() -> None:
    """Invalid survivors never enlarge score agreement or erase full-panel coverage."""
    samples = [sample("a"), sample("b")]
    failed = {"sample_id": "b", "status": "stage_error", "score": None, "stages": []}
    report = report_records(
        samples,
        {s.sample_id: label() for s in samples},
        {"left": {"a": record("a"), "b": record("b")}, "right": {"a": record("a"), "b": failed}},
    )
    comparison = report["matched_valid"][0]
    assert comparison["population"] == 2
    assert comparison["matched_valid"] == comparison["matched_numeric"] == 1
    assert comparison["numeric_score_agreement"] == 1
    assert report["conditions"]["right"]["stage_statuses"] == {"validated": 3}


def test_source_linked_proposal_and_review_disagreements() -> None:
    """Disagreement records point to actual cited identities without asserting label truth."""
    observed = record()
    observed["status"], observed["score"] = "unresolved_disagreement", None
    observed["stages"][1]["result"]["decision"]["supported"] = False
    observed["stages"][2]["result"]["decision"]["conclusion_supported"] = False
    result = report_records([sample()], {"fixture": label()}, {"x": {"fixture": observed}})[
        "conditions"
    ]["x"]
    assert result["point_support"]["false_negative"] == 1
    assert result["conclusion_support"]["false_negative"] == 1
    assert {d["stage"] for d in result["source_linked_disagreements"]} == {
        "point",
        "conclusion",
        "review_disagreement",
    }
    point = next(d for d in result["source_linked_disagreements"] if d["stage"] == "point")
    assert point["sources"][0]["citation_id"] == "S1"
    assert "full_source_text" not in json.dumps(point)
    assert result["numeric_answers"] == 0


def test_gate_false_exemptions_and_misses_include_na() -> None:
    """Clean-abstention mistakes are reported separately from available numeric scores."""
    false_exemption = record("a")
    false_exemption.update(status="not_applicable", score=None)
    false_exemption["stages"] = [stage("abstention", {"classification": "clean_abstention"})]
    abstention = {**label(), "clean_abstention": True}
    result = report_records(
        [sample("a"), sample("b")],
        {"a": label(), "b": abstention},
        {"x": {"a": false_exemption, "b": record("b")}},
    )["conditions"]["x"]
    assert result["abstention"]["false_exemptions"] == result["abstention"]["misses"] == 1
    assert result["valid_answers"] == 2 and result["numeric_answers"] == 1


def test_quote_diagnostics_and_native_cache_evidence_are_separate() -> None:
    """Nonliteral quotes still count valid semantic stages; cache unknown stays null."""
    observed = record()
    point = observed["stages"][1]
    point["usage"] = {
        "input_tokens": 100,
        "output_tokens": 2,
        "cache_read_tokens": 30,
        "cache_write_tokens": 0,
    }
    point["result"]["quotation_diagnostics"] = {
        "status": "applicable",
        "missing_quotation": True,
        "locators": [{"literal_match": False}],
        "unsupported_assertions": [{"literal_match": False}],
    }
    result = report_records([sample()], {"fixture": label()}, {"x": {"fixture": observed}})[
        "conditions"
    ]["x"]
    assert result["valid_answers"] == 1
    assert result["quotation_diagnostics"]["nonliteral_excerpt"] == 1
    assert result["native_usage"]["cache_read_tokens"] == 30
    assert result["saved_stages_reused"] == 0


def test_selected_expectations_skip_unselected_objects_and_reject_duplicates(
    tmp_path: Path,
) -> None:
    """Only selected IDs become loaded label objects; no global-label return path exists."""
    path = tmp_path / "labels.json"
    path.write_text(
        json.dumps(
            [
                {"sample_id": "other", "expectation": {"SECRET": "unselected"}},
                {"expectation": label(), "sample_id": "selected"},
            ]
        )
    )
    assert _selected_labels(path, {"selected"}) == {"selected": label()}
    path.write_text(json.dumps([{"sample_id": "selected", "expectation": label()}] * 2))
    with pytest.raises(ValueError, match="Duplicate"):
        _selected_labels(path, {"selected"})


def test_latest_observation_excludes_protocol_probe(tmp_path: Path) -> None:
    """Repeated cache/smoke probes never replace a completed evaluation observation."""
    directory = tmp_path / "requests" / stable_json_sha256({"sample_id": "fixture"})
    directory.mkdir(parents=True)
    original = record()
    (directory / "result_0001.json").write_text(json.dumps(original))
    probe = copy.deepcopy(original)
    probe.update(evaluation_denominator=False, status="protocol_complete")
    (directory / "result_0002.json").write_text(json.dumps(probe))
    assert _records(tmp_path, {"fixture"}) == {"fixture": original}


def test_unknown_sample_and_duplicate_stage_are_not_silently_counted() -> None:
    """Malformed result membership cannot turn into an apparent comparison."""
    with pytest.raises(ValueError, match="populations"):
        report_records([sample()], {"fixture": label()}, {"x": {"unknown": record()}})
    observed = record()
    observed["stages"].append(observed["stages"][0])
    with pytest.raises(ValueError, match="Duplicate"):
        report_records([sample()], {"fixture": label()}, {"x": {"fixture": observed}})


def test_coverage_metrics_separate_claims_reviews_and_failed_scores() -> None:
    """A valid reviewed conclusion cannot hide wrong claims or a blocked numeric score."""
    observed = record("a")
    observed.update(status="unresolved_disagreement", score=None)
    observed["stages"][1]["result"]["decision"]["supported"] = False
    metrics = report_records(
        [sample("a"), sample("b")],
        {"a": label(), "b": label()},
        {"x": {"a": observed}},
    )["conditions"]["x"]["metrics_v2"]
    assert metrics["original_claim_support"]["eligible"] == 2
    assert metrics["original_claim_support"]["returned"] == 1
    assert metrics["original_claim_support"]["accuracy"] == 0
    assert metrics["claim_review_support"]["accuracy"] == 0.5
    assert metrics["conclusion_support"]["accuracy"] == 0.5
    assert metrics["numeric_score"]["returned"] == 0
    assert metrics["numeric_score"]["accuracy"] == 0
    assert metrics["numeric_score"]["macro_f1"] == 0


def test_invalid_conclusion_does_not_contribute_review_predictions() -> None:
    """Even plausible fields from a validation-failed stage remain failures."""
    observed = record()
    observed.update(status="stage_error", score=None)
    observed["stages"][2]["status"] = "schema_error"
    metrics = report_records([sample()], {"fixture": label()}, {"x": {"fixture": observed}})[
        "conditions"
    ]["x"]["metrics_v2"]
    assert metrics["original_claim_support"]["accuracy"] == 1
    assert metrics["claim_review_support"]["failed"] == 1
    assert metrics["conclusion_support"]["failed"] == 1
    assert metrics["numeric_score"]["failed"] == 1


def test_clean_abstention_proposal_is_excluded_from_numeric_eligibility() -> None:
    """N/A is a separate outcome and never an extra numeric class or missing numeric error."""
    proposed = {
        "clean_abstention": True,
        "conclusion_supported": None,
        "score": None,
        "point_expectations": [],
    }
    metrics = report_records([sample()], {"fixture": proposed}, {"x": {}})["conditions"]["x"][
        "metrics_v2"
    ]
    assert all(
        metrics[name]["eligible"] == 0
        for name in (
            "original_claim_support",
            "claim_review_support",
            "conclusion_support",
            "numeric_score",
        )
    )
    assert metrics["numeric_score"]["accuracy"] is None


@pytest.mark.parametrize("panel", ["dev3", "dev6", "full-dev"])
def test_analysis_forwards_manifest_binding_before_reading_labels(tmp_path, monkeypatch, panel):
    """Explicit hashes use the pinned loader before analysis opens restricted proposals."""
    from er_commons import grounding_comparison_analysis as analysis

    def loader(path, selected_panel, expected_hash):
        assert path == tmp_path / "manifest.json"
        assert selected_panel == panel
        assert expected_hash == "a" * 64
        raise ValueError("binding rejected before labels")

    monkeypatch.setattr(analysis, "load_development_panel", loader)
    with pytest.raises(ValueError, match="binding rejected before labels"):
        analysis.analyze_runs(tmp_path / "manifest.json", {}, panel=panel, expected_sha256="a" * 64)


def test_analysis_expansion_requires_explicit_manifest_binding(tmp_path):
    """Legacy unpinned Dev3 remains the only no-hash compatibility route."""
    from er_commons.grounding_comparison_analysis import analyze_runs

    with pytest.raises(ValueError, match="requires an expected manifest hash"):
        analyze_runs(tmp_path / "nonexistent.json", {}, panel="dev6")


@pytest.mark.parametrize("kind", ["claim", "review"])
def test_coverage_metrics_reject_duplicate_predictions_even_with_distinct_stage_keys(kind):
    """Repeated predictions cannot collapse into one metric item or inflate older counts."""
    observed = record()
    if kind == "claim":
        duplicate = copy.deepcopy(observed["stages"][1])
        duplicate["key"] = "other-stage-key"
        observed["stages"].append(duplicate)
    else:
        reviews = observed["stages"][2]["result"]["decision"]["point_reviews"]
        reviews.append(copy.deepcopy(reviews[0]))
    with pytest.raises(ValueError, match="Duplicate .*prediction"):
        report_records([sample()], {"fixture": label()}, {"x": {"fixture": observed}})
