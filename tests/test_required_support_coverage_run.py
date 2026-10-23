"""Offline budget and actual native wire tests for the bounded coverage pilot."""

import asyncio
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx2
import pytest
from inspect_ai.model import ChatMessage, ChatMessageSystem, ChatMessageUser
from inspect_ai.util._json import json_schema_dump
from judge_native_fixtures import envelope

from er_commons import required_support_coverage as core
from er_commons import required_support_coverage_inspect as native
from er_commons.artifact_io import stable_json_sha256
from er_commons.required_support_coverage_run import WireGate, budget_bound, save


def packet() -> dict[str, Any]:
    """Make a tiny isolated required-point request without external references."""
    return {
        "question": "What is required?",
        "required_reference_point": {"point_id": "R1", "text": "A replacement is required."},
        "candidate_supporting_points": [{"point_id": "S1", "text": "A replacement is required."}],
    }


def test_budget_reserves_nine_attempts_and_durable_no_clobber(tmp_path: Path) -> None:
    """All retries and repetitions reserve maximum input/output before dispatch."""
    samples = [{"sample_id": "one", "packet": packet()}]
    price = {"input_per_million": ".25", "output_per_million": ".5"}
    fixed = (
        len(core.system_prompt().encode())
        + len(json.dumps(core.output_json_schema(), ensure_ascii=False).encode())
        + 4096
    )
    inputs = fixed + len(json.dumps(packet(), ensure_ascii=False).encode())
    assert (
        budget_bound(samples, price)
        == (Decimal(inputs) * Decimal(".25") + 4096 * Decimal(".5")) * 9 / 1_000_000
    )
    save(tmp_path / "claim.json", {"reserved": "1"})
    with pytest.raises(FileExistsError):
        save(tmp_path / "claim.json", {"reserved": "0"})


@pytest.mark.parametrize("prior", [0, 2])
def test_native_wire_gate_and_attempt_cap(tmp_path: Path, prior: int) -> None:
    """Actual installed Inspect serialization passes isolation checks without paid calls."""
    config = native.generation_config()
    config.extra_body = {
        **(config.extra_body or {}),
        "service_tier": "default",
        "prompt_cache_retention": "24h",
    }
    assert config.response_schema is not None
    gate = WireGate(
        tmp_path,
        [{"packet": packet()}],
        json_schema_dump(config.response_schema.json_schema),
        {stable_json_sha256(packet()): prior},
    )
    sent = []

    def handler(request: Any) -> Any:
        sent.append(json.loads(request.content))
        return httpx2.Response(
            200,
            json=envelope(
                "openai_generation",
                '{"covered":true,"supporting_point_ids":["S1"],"reason":"Present."}',
            ),
        )

    client = httpx2.AsyncClient(
        transport=httpx2.MockTransport(handler),
        event_hooks={"request": [gate.request], "response": [gate.response]},
    )
    model = native.native_model(http_client=client, streaming=False, api_key="offline")
    model.config = config
    messages: list[ChatMessage] = [
        ChatMessageSystem(content=core.system_prompt()),
        ChatMessageUser(content=json.dumps(packet())),
    ]
    asyncio.run(model.generate(messages, cache=False))
    assert len(sent) == gate.total == 1
    body = sent[0]
    for _ in range(8 - prior):
        asyncio.run(
            gate.request(httpx2.Request("POST", "https://api.openai.com/v1/responses", json=body))
        )
    with pytest.raises(ValueError, match="allowance"):
        asyncio.run(
            gate.request(httpx2.Request("POST", "https://api.openai.com/v1/responses", json=body))
        )


def test_gate_blocks_counter_and_then_all_calls(tmp_path: Path) -> None:
    """Unapproved counting and fatal drift stop subsequent requests before dispatch."""
    gate = WireGate(tmp_path, [{"packet": packet()}], {})
    with pytest.raises(ValueError, match="endpoint"):
        asyncio.run(
            gate.request(
                httpx2.Request("POST", "https://api.openai.com/v1/responses/input_tokens", json={})
            )
        )
    assert gate.total == 0 and gate.stopped


def test_frozen_population_and_code_validation(tmp_path: Path) -> None:
    """A complete frozen suite validates; changed labels cannot slip into dispatch."""
    from er_commons.artifact_io import sha256_file, stable_json_sha256
    from er_commons.required_support_coverage_run import CASES, CODE, REPO, prepare

    samples = []
    cases = sorted(CASES)
    for index in range(20):
        value = packet()
        point_index = index % 10
        value["required_reference_point"]["point_id"] = f"R{point_index + 1}"
        samples.append(
            {"sample_id": f"case-{index}", "case_id": cases[point_index % 6], "packet": value}
        )
    (tmp_path / "samples.jsonl").write_text("\n".join(json.dumps(s) for s in samples))
    save(
        tmp_path / "expected_labels.json",
        {s["sample_id"]: index % 2 == 0 for index, s in enumerate(samples)},
    )
    save(tmp_path / "checkpoint_ids.json", [s["sample_id"] for s in samples])
    manifest = {
        "execution_root": str(tmp_path.resolve()),
        "files": {
            name: sha256_file(tmp_path / name)
            for name in ("samples.jsonl", "expected_labels.json", "checkpoint_ids.json")
        },
        "code_sha256": {name: sha256_file(REPO / name) for name in CODE},
        "prompt_sha256": stable_json_sha256(core.system_prompt()),
        "output_schema_sha256": stable_json_sha256(core.output_json_schema()),
        "reference_completion_sha256": "a" * 64,
        "review_approved": True,
        "pricing": {
            "verified_on": "2026-10-23",
            "source": "https://developers.openai.com/api/docs/models/gpt-6-luna",
            "input_per_million": ".25",
            "output_per_million": ".5",
        },
    }
    save(tmp_path / "manifest.json", manifest)
    assert prepare(tmp_path)[3]["slots"] == 60
    (tmp_path / "expected_labels.json").write_text("{}")
    with pytest.raises(ValueError, match="artifact differs"):
        prepare(tmp_path)


@pytest.mark.parametrize("failure", ["server", "malformed", "accounting"])
def test_run_level_response_failures_stop_dispatch(tmp_path: Path, failure: str) -> None:
    """Repeated server errors and uncertain accounting stop untouched requests."""
    gate = WireGate(tmp_path, [{"packet": packet()}], {})
    if failure == "server":
        asyncio.run(gate.response(httpx2.Response(503)))
        assert gate.stopped is None
        asyncio.run(gate.response(httpx2.Response(503)))
    elif failure == "malformed":
        asyncio.run(gate.response(httpx2.Response(200, content=b"not json")))
    else:
        asyncio.run(gate.response(httpx2.Response(200, json={"model": "another-model"})))
    assert gate.stopped


def test_continuation_preserves_prior_liability_and_rejects_drift(tmp_path: Path) -> None:
    """Only sealed unsent commitments can transfer; sent uncertain bounds remain reserved."""
    from er_commons.artifact_io import sha256_file, stable_json_sha256
    from er_commons.required_support_coverage_run import continuation_accounting

    ancestor = tmp_path / "round1"
    successor = tmp_path / "round1_continue_v1"
    ancestor.mkdir()
    successor.mkdir()
    samples = [{"sample_id": "one", "packet": packet()}]
    pricing = {"input_per_million": ".25", "output_per_million": ".5"}
    bound = budget_bound(samples, pricing)
    manifest: dict[str, Any] = {
        "files": {},
        "code_sha256": {},
        "pricing": pricing,
        "prompt_sha256": "prompt",
        "output_schema_sha256": "schema",
        "reference_completion_sha256": "reference",
    }
    for name in (
        "samples.jsonl",
        "expected_labels.json",
        "checkpoint_ids.json",
        "system_prompt.txt",
        "input_schema.json",
        "output_schema.json",
        "reference_bindings.json",
        "authored_variants.jsonl",
        "independent_review.json",
    ):
        (ancestor / name).write_text("frozen")
        manifest["files"][name] = sha256_file(ancestor / name)
    save(ancestor / "manifest.json", manifest | {"execution_root": str(ancestor)})
    save(ancestor / "paid_run_claim.json", {"reserved_usd": str(bound), "cap_usd": "10"})
    (ancestor / "checkpoint/wire").mkdir(parents=True)
    save(ancestor / "checkpoint/results.json", [{"valid": False, "covered": None}])
    save(ancestor / "checkpoint/status.json", {"wire_attempts": 1})
    save(
        ancestor / "checkpoint/wire/request_0001.json",
        {
            "prompt_cache_retention": "in_memory",
            "input": [{}, {"content": [{"text": json.dumps(packet())}]}],
        },
    )
    save(
        ancestor / "completion.json",
        {
            "status": "sealed_stopped_operational_failure_not_qualification",
            "files": [
                {
                    "path": str(p.relative_to(ancestor)),
                    "sha256": sha256_file(p),
                    "byte_size": p.stat().st_size,
                }
                for p in ancestor.rglob("*")
                if p.is_file()
            ],
        },
    )
    manifest["continuation_of"] = {
        "execution_root": str(ancestor),
        "completion_sha256": sha256_file(ancestor / "completion.json"),
    }
    result = continuation_accounting(successor, manifest, samples, bound)
    assert result["prior_attempt_counts"] == {stable_json_sha256(packet()): 1}
    assert result["remaining_wire_attempts"] == 8
    assert Decimal(result["prior_reserved_usd"]) == bound / 9
    assert (
        Decimal(result["released_unsent_reservation_usd"]) + Decimal(result["prior_reserved_usd"])
        == bound
    )
    manifest["files"]["expected_labels.json"] = "changed"
    with pytest.raises(ValueError, match="semantic input"):
        continuation_accounting(successor, manifest, samples, bound)
    manifest["files"]["expected_labels.json"] = sha256_file(ancestor / "expected_labels.json")
    (ancestor / "unsealed.json").write_text("{}")
    with pytest.raises(ValueError, match="unsealed"):
        continuation_accounting(successor, manifest, samples, bound)


def test_continuation_checkpoint_limits_total_slot_attempts() -> None:
    """One previous attempt plus at most two fresh attempts never exceeds three."""
    from er_commons.required_support_coverage_run import effective_transport_retries

    assert effective_transport_retries({"continuation_of": {}}, "checkpoint") == 1
    assert effective_transport_retries({"continuation_of": {}}, "remainder") == 2
    assert effective_transport_retries({}, "checkpoint") == 2


def test_all19_binding_rejects_changed_inputs_and_budget_forks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Expansion binds a sealed approved suite and cannot acquire a second paid namespace."""
    from er_commons import required_support_coverage_run as run
    from er_commons.artifact_io import sha256_file

    repo = tmp_path / "repo"
    (repo / "docs/specs").mkdir(parents=True)
    prepared = tmp_path / "data/preparation"
    (prepared / "suite").mkdir(parents=True)
    root = prepared.with_name(prepared.name + "_round1")
    root.mkdir()
    seal_digest = "bc1765e7881c4cab97253ec10aa2d4fa2efb0129929e9fc1c764c3635af9fc74"
    pointer = repo / "docs/specs/task15y_all19_preparation_result.json"
    save(pointer, {"artifact_root_relative": "preparation", "completion": {"sha256": seal_digest}})
    manifest: dict[str, Any] = {
        "preparation_pointer_sha256": sha256_file(pointer),
        "prepared_inputs_root": str(prepared),
        "files": {},
        "reference_completion_sha256": "reference",
        "prompt_sha256": stable_json_sha256(core.system_prompt()),
    }
    for name in (
        "samples.jsonl",
        "expected_labels.json",
        "checkpoint_ids.json",
        "system_prompt.txt",
        "input_schema.json",
        "output_schema.json",
    ):
        value = core.system_prompt() if name == "system_prompt.txt" else "{}"
        if name == "output_schema.json":
            value = json.dumps(core.output_json_schema())
        (prepared / "suite" / name).write_text(value)
        (root / name).write_text(value)
        manifest["files"][name] = sha256_file(root / name)
    (repo / "docs/prompts").mkdir()
    prompt = repo / "docs/prompts/task15y_required_support_coverage_v1.txt"
    prompt.write_text("approved instruction")
    save(prepared / "manifest.json", manifest | {"prompt_sha256": sha256_file(prompt)})
    save(
        prepared / "completion.json",
        {
            "files": [
                {
                    "path": str(p.relative_to(prepared)),
                    "byte_size": p.stat().st_size,
                    "sha256": sha256_file(p),
                }
                for p in prepared.rglob("*")
                if p.is_file()
            ]
        },
    )
    monkeypatch.setattr(run, "REPO", repo)
    monkeypatch.setenv("ER_COMMONS_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setattr(
        run,
        "sha256_file",
        lambda p: seal_digest if p == prepared / "completion.json" else sha256_file(p),
    )
    result = run.all19_binding(root, manifest)
    reservation = result | {
        "manifest_sha256": "manifest",
        "reserved_usd": "24.97518",
        "cap_usd": "30",
    }
    run.shared_all19_claim(root, reservation, create=True)
    run.shared_all19_claim(root, reservation, create=False)
    with pytest.raises(FileExistsError):
        run.shared_all19_claim(root, reservation, create=True)
    with pytest.raises(ValueError, match="claim differs"):
        run.shared_all19_claim(root, reservation | {"cap_usd": "60"}, create=False)
    with pytest.raises(ValueError, match="sole execution root"):
        run.all19_binding(tmp_path / "another-run", manifest)
    manifest["files"]["expected_labels.json"] = "changed"
    with pytest.raises(ValueError, match="changed approved input"):
        run.all19_binding(root, manifest)
    manifest["files"]["expected_labels.json"] = sha256_file(root / "expected_labels.json")
    (prepared / "suite/samples.jsonl").write_text("tampered")
    with pytest.raises(ValueError, match="inventory differs"):
        run.all19_binding(root, manifest)


@pytest.mark.parametrize("failure", ["status_hash", "stop", "invalid", "systematic"])
def test_all19_remainder_rejects_checkpoint_stop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    """Approval cannot override stopped or systematically failing expansion checkpoints."""
    from er_commons import required_support_coverage_run as run
    from er_commons.artifact_io import sha256_file

    (tmp_path / "checkpoint").mkdir()
    rows = [{"valid": True} for _ in range(252)]
    if failure == "invalid":
        rows[0]["valid"] = rows[1]["valid"] = False
    save(tmp_path / "checkpoint/results.json", rows)
    save(
        tmp_path / "checkpoint/status.json", {"stop_reason": "fatal" if failure == "stop" else None}
    )
    save(
        tmp_path / "checkpoint_review.json",
        {
            "approved": True,
            "checkpoint_results_sha256": sha256_file(tmp_path / "checkpoint/results.json"),
            "checkpoint_status_sha256": "wrong"
            if failure == "status_hash"
            else sha256_file(tmp_path / "checkpoint/status.json"),
            "no_systematic_rule_failure": failure != "systematic",
        },
    )
    reservation = {"execution_mode": "all19"}
    save(tmp_path / "paid_run_claim.json", reservation)
    monkeypatch.setattr(run, "prepare", lambda root: ([], {}, [], reservation))
    monkeypatch.setattr(run, "shared_all19_claim", lambda *args, **kwargs: None)
    with pytest.raises(ValueError, match="checkpoint stop"):
        asyncio.run(run.execute(tmp_path, "remainder"))
    assert not (tmp_path / "remainder").exists()


def test_judgment_rows_preserve_missing_and_failed_slots() -> None:
    """Partial native logs retain the full plan without turning failures into false labels."""
    from types import SimpleNamespace

    from er_commons.required_support_coverage_run import judgment_rows

    class Score:
        metadata = {
            "status": "evaluated",
            "covered": True,
            "result": {"covered": True, "supporting_point_ids": ["S1"], "reason": "Present."},
        }

        def model_dump(self, *, mode: str) -> dict[str, Any]:
            return {"value": 1, "metadata": self.metadata}

    class Failure:
        def model_dump(self, *, mode: str) -> dict[str, str]:
            return {"message": "Provider failure"}

    samples = [{"sample_id": "one"}, {"sample_id": "two"}]
    labels = {"one": True, "two": False}
    logs = [
        SimpleNamespace(
            samples=[
                SimpleNamespace(
                    id="one", epoch=1, scores={"coverage": Score()}, error=None, model_usage={}
                ),
                SimpleNamespace(
                    id="two", epoch=2, scores={"coverage": Score()}, error=Failure(), model_usage={}
                ),
            ]
        )
    ]
    rows = judgment_rows(logs, samples, labels)
    assert [(row["sample_id"], row["epoch"]) for row in rows] == [
        ("one", 1),
        ("one", 2),
        ("one", 3),
        ("two", 1),
        ("two", 2),
        ("two", 3),
    ]
    assert rows[0]["valid"] is True and rows[0]["covered"] is True
    assert all(row["valid"] is False and row["covered"] is None for row in rows[1:])
    assert rows[4]["status"] == "unavailable"
    assert rows[4]["result"] is None
    assert rows[4]["error"] == {"message": "Provider failure"}
    assert rows[1]["status"] == "unavailable" and rows[1]["native_log"] is None
    with pytest.raises(ValueError, match="Duplicate sample repetition"):
        judgment_rows(logs * 2, samples, labels)
