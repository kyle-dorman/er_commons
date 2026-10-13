"""Frozen panel routing, offline audit and explicit cloud CLI authorization boundaries."""

import argparse
import copy
import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_grounding_comparison_inspect import budget, envelopes
from test_grounding_comparison_providers import CONDITIONS
from test_grounding_inspect import sample

from er_commons import grounding_comparison_inspect as execution
from er_commons import grounding_comparison_panel as panel
from er_commons import grounding_comparison_run as cli
from er_commons import grounding_comparison_semantics as semantics
from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_comparison_audit import request_plan
from er_commons.grounding_comparison_providers import render_request


def options(tmp_path: Path, **updates) -> argparse.Namespace:
    """Supply CLI defaults with no implicit execution authorization or spending caps."""
    values = dict(
        config=Path("configs/task09e1_conditions_v2.json"),
        manifest=tmp_path / "panel.json",
        condition="all",
        mode="prepare",
        output=tmp_path / "output",
        execute_paid=False,
        currency_cap=None,
        request_cap=None,
        output_cap=None,
        wall_seconds=None,
    )
    values.update(updates)
    return argparse.Namespace(**values)


@pytest.fixture
def invented_panel(monkeypatch):
    """Provide invented saved inputs without opening any benchmark or restricted labels."""
    samples = [sample()]
    monkeypatch.setattr(cli, "load_dev3", lambda path: (samples, {"invented": True}))
    return samples


def test_selected_packets_never_constructs_unselected_object(tmp_path, monkeypatch):
    """Streaming may read syntax, but only an allowed ID receives an object builder."""
    path = tmp_path / "packets.json"
    path.write_text(
        json.dumps(
            [
                {"id": "unselected", "payload": {"answer": 17, "reserved_secret": [None]}},
                {"id": "allowed", "payload": {"answer": "invented"}},
            ]
        )
    )
    builds = []
    original = panel.ijson.ObjectBuilder

    def builder():
        builds.append(True)
        return original()

    monkeypatch.setattr(panel.ijson, "ObjectBuilder", builder)
    assert panel.selected_packets(path, {"allowed"}) == {
        "allowed": {"id": "allowed", "payload": {"answer": "invented"}}
    }
    assert len(builds) == 1


@pytest.mark.parametrize(
    "rows,match",
    [
        ([{"id": "other"}], "missing"),
        ([{"id": "allowed"}, {"id": "allowed"}], "Duplicate"),
        ([{"payload": {}}], "routing identity"),
    ],
)
def test_selected_packet_routing_rejects_incomplete_identities(tmp_path, rows, match):
    """No missing or duplicate selected identity silently alters the evaluation panel."""
    path = tmp_path / "packets.json"
    path.write_text(json.dumps(rows))
    with pytest.raises(ValueError, match=match):
        panel.selected_packets(path, {"allowed"})


def test_manifest_hash_mismatch_rejects_before_decoding_or_dataset_reads(tmp_path, monkeypatch):
    """The frozen manifest's bytes are checked before any dataset or label route opens."""
    path = tmp_path / "manifest.json"
    path.write_text("not even JSON: reject the hash first")

    def forbidden(*args, **kwargs):
        pytest.fail("Dataset contents must not be read after manifest mismatch")

    for name in ("selected_packets", "selected_rows", "verify_binding"):
        monkeypatch.setattr(panel, name, forbidden)
    with pytest.raises(ValueError, match="exact preserved"):
        panel.load_dev3(path)


def test_prepare_writes_bound_audit_without_credentials_or_transport(
    tmp_path, invented_panel, monkeypatch
):
    """Even present credentials cannot turn the default offline command into paid calls."""
    monkeypatch.setenv("OPENAI_API_KEY", "secret-must-not-be-read-or-persisted")

    def forbidden(*args, **kwargs):
        pytest.fail("Offline prepare cannot evaluate, read credentials or use HTTP")

    monkeypatch.setattr(cli, "evaluate_comparison", forbidden)
    monkeypatch.setattr(execution, "_headers", forbidden)
    monkeypatch.setattr(execution, "_post", forbidden)
    result = cli.launch(options(tmp_path))
    assert result["paid_calls"] == result["inference_calls"] == 0
    assert result["expectations_loaded"] is False
    assert set(result["conditions"]) == set(CONDITIONS)
    assert len(result["code"]) >= 4
    assert set(result["packages"]) == {"inspect-ai", "httpx", "pydantic", "ijson"}
    completion = json.loads((tmp_path / "output" / "completion.json").read_text())
    for binding in completion["files"]:
        assert panel.file_binding(Path(binding["path"])) == binding
        assert "secret-must-not-be-read" not in Path(binding["path"]).read_text()
    for condition in CONDITIONS:
        audit = json.loads((tmp_path / "output" / condition / "audit.json").read_text())
        assert audit["maximum_stage_calls"] == 3
        assert audit["rendered_requests"] == 4
        assert audit["cache_eligibility_verified"] is False
        assert audit["exact_input_tokens"] is None
        assert audit["no_cache_estimate_usd"] is None
        assert audit["plausible_cache_estimate_usd"] is None
    with pytest.raises(FileExistsError):
        cli.launch(options(tmp_path))


def test_audit_conclusion_observations_are_synthetic_shapes_not_labels():
    """Offline rendering names both hypothetical verdicts and does not consume expectations."""
    s = sample().model_copy(update={"expected_score": 0, "stage_expectations": {"SECRET": True}})
    plan = request_plan(s)
    assert [key for _, key, _ in plan] == [
        "abstention",
        "P2",
        "conclusion_audit_all_false",
        "conclusion_audit_all_true",
    ]
    for expected, (_, _, payload) in zip((False, True), plan[-2:], strict=True):
        assert payload["point_assessments"] == [{"point_id": "P2", "supported": expected}]
        assert "SECRET" not in json.dumps(payload)


@pytest.mark.parametrize("mode", ["smoke", "cache", "run"])
def test_live_requires_explicit_execute_paid(tmp_path, invented_panel, monkeypatch, mode):
    """Credentials and explicit dollar caps are not themselves execution authorization."""
    monkeypatch.setenv("OPENAI_API_KEY", "present-but-not-authorized")
    with pytest.raises(ValueError, match="execute-paid"):
        cli.launch(
            options(
                tmp_path,
                mode=mode,
                condition="openai_generation",
                currency_cap="1",
                request_cap=3,
                output_cap=20000,
                wall_seconds=60,
            )
        )
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("missing", ["currency_cap", "request_cap", "output_cap", "wall_seconds"])
def test_live_requires_every_explicit_cap(tmp_path, invented_panel, missing):
    """An omitted cap cannot be replaced with an implicit potentially unbounded default."""
    values = dict(
        mode="run",
        condition="openai_generation",
        execute_paid=True,
        currency_cap="1",
        request_cap=3,
        output_cap=20000,
        wall_seconds=60,
    )
    values[missing] = None
    with pytest.raises(ValueError, match="caps"):
        cli.launch(options(tmp_path, **values))
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "bad",
    [
        {"currency_cap": "0"},
        {"request_cap": 0},
        {"output_cap": 0},
        {"wall_seconds": 0},
    ],
)
def test_live_rejects_nonpositive_caps(tmp_path, invented_panel, bad):
    """Paid execution is blocked before artifacts or dispatch for invalid cap values."""
    values = dict(
        mode="run",
        condition="openai_generation",
        execute_paid=True,
        currency_cap="1",
        request_cap=3,
        output_cap=20000,
        wall_seconds=60,
    )
    values.update(bad)
    with pytest.raises(ValueError):
        cli.launch(options(tmp_path, **values))
    assert not (tmp_path / "output").exists()


def test_live_requires_fresh_namespace(tmp_path, invented_panel, monkeypatch):
    """A new process must not reset prior caps in an existing namespace."""

    def forbidden(*args, **kwargs):
        pytest.fail("Guard must precede evaluation")

    monkeypatch.setattr(cli, "evaluate_comparison", forbidden)
    args = options(
        tmp_path,
        mode="run",
        condition="openai_generation",
        execute_paid=True,
        currency_cap="1",
        request_cap=3,
        output_cap=20000,
        wall_seconds=60,
    )
    args.output.mkdir()
    with pytest.raises(FileExistsError):
        cli.launch(args)


def test_all_cloud_selection_shares_one_budget_and_binds_run(tmp_path, invented_panel, monkeypatch):
    """A six-condition selection cannot multiply the user's global cap into six budgets."""
    calls = []

    def evaluate(samples, condition, output, run_budget, **kwargs):
        calls.append((condition.id, run_budget, kwargs))
        return [SimpleNamespace(status="success", location="invented.eval")]

    monkeypatch.setattr(cli, "evaluate_comparison", evaluate)
    result = cli.launch(
        options(
            tmp_path,
            mode="smoke",
            condition="all-cloud",
            execute_paid=True,
            currency_cap="1",
            request_cap=3,
            output_cap=20000,
            wall_seconds=60,
        )
    )
    assert {key for key, _, _ in calls} == set(CONDITIONS)
    assert len({id(run_budget) for _, run_budget, _ in calls}) == 1
    assert all(kwargs["protocol"] == "smoke" for _, _, kwargs in calls)
    assert all(row["protocol_only"] for row in result["conditions"].values())
    manifest = json.loads((tmp_path / "output" / "manifest.json").read_text())
    assert manifest["inputs"] == {"invented": True}
    assert manifest["caps"]["currency"] == "1"


def paired_samples():
    """Preserve one source while changing only an original invented target point."""
    first = sample()
    second = sample("shared")
    second.packet = copy.deepcopy(second.packet)
    second.packet["payload"]["answer"]["qualifications"][0]["text"] = "Another invented caveat."
    second.packet["diagnostics"]["payload_sha256"] = stable_json_sha256(second.packet["payload"])
    return [first, second]


def test_cache_probe_preserves_identical_warm_request_and_shared_evidence():
    """Probe sample identities stay outside model input; third request varies the real point."""
    probes = cli._protocol_samples(paired_samples(), "cache")
    assert len({s.sample_id for s in probes}) == 3
    requests = []
    for s in probes:
        payload = semantics.point_inputs(s.packet)[0]
        requests.append(
            render_request(
                CONDITIONS["openai_generation"],
                "point",
                payload,
                semantics.stage_prompt("point"),
                semantics.stage_schema("point", payload),
            )
        )
    assert requests[0] == requests[1]
    assert requests[0]["request_sha256"] != requests[2]["request_sha256"]
    payloads = [semantics.point_inputs(s.packet)[0] for s in probes]
    assert payloads[0]["evidence"] == payloads[2]["evidence"]


def test_probe_actual_inspect_results_exclude_evaluation_denominator(tmp_path, monkeypatch):
    """Three measured protocol calls create no answer scores or evaluation denominator."""
    condition = CONDITIONS["openai_generation"]
    probes = cli._protocol_samples(paired_samples(), "cache")
    fixtures = {s.sample_id: envelopes(condition)["fixture"] for s in probes}

    async def forbidden(*args, **kwargs):
        pytest.fail("Invented protocol test cannot use HTTP")

    monkeypatch.setattr(execution, "_post", forbidden)
    logs = execution.evaluate_comparison(
        probes, condition, tmp_path, budget(), fixtures=fixtures, protocol="cache"
    )
    assert logs[0].status == "success"
    records = [s.scores["comparison_scorer"].metadata["comparison_record"] for s in logs[0].samples]
    assert len(records) == 3
    assert all(r["status"] == "protocol_complete" and r["score"] is None for r in records)
    assert all(r["evaluation_denominator"] is False for r in records)
    assert all(len(r["stages"]) == 1 and r["stages"][0]["kind"] == "point" for r in records)
    assert len(list((tmp_path / "requests").rglob("completion.json"))) == 3


def test_receipt_summary_preserves_usage_unknown_cache_and_reuse(tmp_path):
    """Measured tokens yield a ceiling, absent cache counts stay unknown, reuse is not rebilled."""
    condition = CONDITIONS["openai_generation"]
    usage = {
        "input_tokens": 100,
        "output_tokens": 20,
        "cache_read_tokens": None,
        "cache_write_tokens": None,
        "native_usage": {"input_tokens": 100, "output_tokens": 20},
    }
    directory = tmp_path / "requests" / "sample"
    directory.mkdir(parents=True)
    record = {
        "sample_id": "invented",
        "stages": [
            {"key": "point", "status": "validated", "usage": usage, "elapsed_seconds": 1.2},
            {"key": "point", "status": "validated", "usage": usage, "reused": True},
            {"key": "blocked", "status": "context_unverified"},
        ],
    }
    (directory / "result_0001.json").write_text(json.dumps(record))
    result = cli._receipt_summary(tmp_path, condition.pricing.model_dump(mode="json"))
    assert result["billed_cost_usd"] is None
    first, reused, blocked = result["observations"]
    assert first["native_usage"] == usage
    assert Decimal(first["conservative_measured_token_cost_usd"]) == Decimal("0.000044")
    assert first["elapsed_seconds"] == 1.2
    assert reused["conservative_measured_token_cost_usd"] is None
    assert reused["reused_saved_receipt"] is True
    assert blocked["native_usage"] == {}
    assert blocked["conservative_measured_token_cost_usd"] is None
    assert "not assumed" in result["first_request_cold"]
    assert "unverified" in result["cache_savings"]


def test_cache_probe_empty_or_no_claims_fails_clearly(monkeypatch):
    """Unusable probe populations fail before output or dispatch."""
    with pytest.raises(ValueError, match="nonempty"):
        cli._protocol_samples([], "cache")
    monkeypatch.setattr(cli, "point_inputs", lambda packet: [])
    with pytest.raises(ValueError, match="at least one claim"):
        cli._protocol_samples([sample()], "cache")


def test_explicit_panel_and_allowance_are_forwarded(tmp_path, monkeypatch):
    """Selected development identity and counting exception reach the maintained runner."""
    loaded, called = [], []
    monkeypatch.setattr(
        cli, "load_development_panel", lambda *args: (loaded.append(args) or [sample()], {})
    )
    monkeypatch.setattr(
        cli,
        "evaluate_comparison",
        lambda *args, **kwargs: (
            called.append(kwargs) or [SimpleNamespace(status="success", location="fixture.eval")]
        ),
    )
    cli.launch(
        options(
            tmp_path,
            config=cli.DEFAULT_CONFIG,
            mode="smoke",
            condition="fireworks_glm",
            panel="dev6",
            manifest_sha256="a" * 64,
            counting_mode="provider-allowance",
            execute_paid=True,
            currency_cap="1",
            request_cap=3,
            output_cap=10000,
            wall_seconds=60,
        )
    )
    assert loaded == [(tmp_path / "panel.json", "dev6", "a" * 64)]
    assert called[0]["exploratory_provider_allowance"] is True


def test_inspect_failure_keeps_summary_and_fails(tmp_path, invented_panel, monkeypatch):
    """Command failures remain observable without discarding immutable run evidence."""
    monkeypatch.setattr(
        cli,
        "evaluate_comparison",
        lambda *args, **kwargs: [SimpleNamespace(status="error", location="fixture.eval")],
    )
    with pytest.raises(ValueError, match="Inspect comparison failed"):
        cli.launch(
            options(
                tmp_path,
                mode="smoke",
                condition="openai_generation",
                execute_paid=True,
                currency_cap="1",
                request_cap=3,
                output_cap=10000,
                wall_seconds=60,
            )
        )
    assert json.loads((tmp_path / "output" / "summary.json").read_text())["conditions"][
        "openai_generation"
    ]["inspect_statuses"] == ["error"]


def test_prepare_from_other_cwd_renders_and_binds_override(tmp_path, invented_panel, monkeypatch):
    """Offline rendering uses the selected prompt and repository-anchored contract."""
    config = Path("configs/task09e1_conditions_v2.json").resolve()
    prompt = tmp_path / "prompts.json"
    prompt.write_text(json.dumps({"point": "Invented explicit point prompt"}))
    monkeypatch.chdir(tmp_path)
    result = cli.launch(
        options(tmp_path, config=config, condition="openai_generation", stage_prompts=prompt)
    )
    assert result["stage_prompts"] == panel.file_binding(prompt)
    requests = list((tmp_path / "output" / "openai_generation").glob("*.json"))
    point = next(
        json.loads(path.read_text())
        for path in requests
        if json.loads(path.read_text()).get("kind") == "point"
    )
    assert "Invented explicit point prompt" in json.dumps(point["request"])


def test_operational_halt_fails_command_even_when_inspect_records_it(
    tmp_path, invented_panel, monkeypatch
):
    """A successfully written Inspect log does not imply the native run succeeded."""

    def stopped(samples, condition, output, budget, **kwargs):
        budget.halt_reason = "transport_error"
        return [SimpleNamespace(status="success", location="fixture.eval")]

    monkeypatch.setattr(cli, "evaluate_comparison", stopped)
    with pytest.raises(ValueError, match="Comparison halted"):
        cli.launch(
            options(
                tmp_path,
                mode="smoke",
                condition="openai_generation",
                execute_paid=True,
                currency_cap="1",
                request_cap=3,
                output_cap=10000,
                wall_seconds=60,
            )
        )
    summary = json.loads((tmp_path / "output" / "summary.json").read_text())
    assert summary["halt_reason"] == "transport_error"


def test_mixed_allowance_modes_rejected_before_any_dispatch(tmp_path, invented_panel, monkeypatch):
    """An invalid later condition cannot follow an already-paid earlier condition."""
    calls = []
    monkeypatch.setattr(cli, "evaluate_comparison", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(ValueError, match="authorized medium"):
        cli.launch(
            options(
                tmp_path,
                config=cli.DEFAULT_CONFIG,
                mode="smoke",
                condition="all",
                counting_mode="provider-allowance",
                execute_paid=True,
                currency_cap="1",
                request_cap=3,
                output_cap=10000,
                wall_seconds=60,
            )
        )
    assert calls == []
    assert not (tmp_path / "output").exists()
