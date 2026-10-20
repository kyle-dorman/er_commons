"""Invented-only fixtures exercise native Inspect/SDK requests without network."""

import asyncio
import copy
import json
import time
from pathlib import Path
from typing import Any

import httpx2
import pytest
from openai import DefaultAsyncHttpxClient

from er_commons import target_generation as target
from er_commons.artifact_io import sha256_file


def packet() -> dict[str, Any]:
    """Return synthetic complete text and table content for native delivery checks."""
    return {
        "schema_version": "task10.evidence_only.v1",
        "case_id": "C041",
        "payload": {
            "question": "What is required?",
            "passages": [
                {
                    "citation_id": "P1",
                    "source_id": "fixture",
                    "title": "Invented report",
                    "heading_path": ["Rules"],
                    "edition": None,
                    "full_source_text": "All gates require inspection.",
                    "tables": [
                        {
                            "id": "fixture-table",
                            "caption": "Inspection schedule",
                            "shape": [1, 1],
                            "cells": [
                                {"text": "Annual inspection", "row_index": 0, "column_index": 0}
                            ],
                        }
                    ],
                    "physical_pages": [1],
                    "printed_labels": ["1"],
                }
            ],
        },
    }


def answer() -> dict[str, Any]:
    """Return a structurally valid cited candidate, with no correctness assertion."""
    return {
        "status": "answered",
        "conclusion": {
            "point_id": "C",
            "text": "Inspection is required.",
            "citation_ids": ["P1"],
            "applies_to": [],
        },
        "supporting_points": [
            {
                "point_id": "S1",
                "text": "All gates require inspection.",
                "citation_ids": ["P1"],
                "applies_to": [],
            }
        ],
        "qualifications": [],
        "optional_context": [],
    }


def mock_provider(
    monkeypatch: pytest.MonkeyPatch,
    *,
    count: int = 100,
    text: str | None = None,
    status: int = 200,
    incomplete: bool = False,
    count_status: int = 200,
    returned_model: str = "gpt-6-luna",
    usage: dict[str, int] | None = None,
    omit_usage: bool = False,
) -> list[dict[str, Any]]:
    """Replace only SDK network transport, retaining real native serialization."""
    calls: list[dict[str, Any]] = []

    async def handle(request: httpx2.Request) -> httpx2.Response:
        body = json.loads(request.content)
        calls.append(body)
        if request.url.path.endswith("/input_tokens"):
            if count_status != 200:
                return httpx2.Response(count_status, json={"error": {"message": "unsupported"}})
            return httpx2.Response(
                200, json={"object": "response.input_tokens", "input_tokens": count}
            )
        if status != 200:
            return httpx2.Response(
                status, json={"error": {"message": "fixture error", "type": "server_error"}}
            )
        return httpx2.Response(
            200,
            json={
                "id": "resp_fixture",
                "object": "response",
                "created_at": 1,
                "model": returned_model,
                "status": "incomplete" if incomplete else "completed",
                "incomplete_details": {"reason": "max_output_tokens"} if incomplete else None,
                "output": [
                    {
                        "id": "msg_fixture",
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {
                                "type": "output_text",
                                "text": text if text is not None else json.dumps(answer()),
                                "annotations": [],
                            }
                        ],
                    }
                ],
                "usage": None
                if omit_usage
                else (
                    usage
                    if usage is not None
                    else {"input_tokens": 100, "output_tokens": 80, "total_tokens": 180}
                ),
            },
        )

    def client(**kwargs: Any) -> DefaultAsyncHttpxClient:
        return DefaultAsyncHttpxClient(transport=httpx2.MockTransport(handle), **kwargs)

    monkeypatch.setenv("OPENAI_API_KEY", "fixture-key-not-real")
    monkeypatch.setattr(target, "DefaultAsyncHttpxClient", client)
    return calls


def invoke(tmp_path: Path) -> dict[str, Any]:
    """Execute one fixture through all production native transport boundaries."""
    return asyncio.run(
        target.generate_one(
            packet(),
            tmp_path,
            json.loads(target.CONFIG.read_text()),
            target.PROMPT.read_text(),
            time.monotonic() + 30,
        )
    )


def test_native_complete_payload_and_schema(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls = mock_provider(monkeypatch)
    result = invoke(tmp_path)
    assert result["status"] == "valid", result
    assert len(calls) == 2
    count, generation = calls
    assert count == {key: value for key, value in generation.items() if key in target.COUNT_FIELDS}
    assert count["text"]["format"]["schema"] == target.output_schema()
    assert json.loads(generation["input"][1]["content"][0]["text"]) == packet()["payload"]
    assert (tmp_path / "generation_response.body").exists()
    assert (tmp_path / "dispatch.json").exists()
    assert result["candidate_sha256"] == sha256_file(tmp_path / "candidate.json")


@pytest.mark.parametrize("field", ["reference", "judge_feedback", "selection_reason"])
def test_reference_isolation(field: str) -> None:
    record = packet()
    record["payload"][field] = "SECRET"
    with pytest.raises(ValueError):
        target.validate_record(record)


def test_invalid_citation_and_abstention() -> None:
    value = answer()
    value["conclusion"]["citation_ids"] = ["P999"]
    with pytest.raises(ValueError, match="unresolved"):
        target.validate_answer(json.dumps(value), packet()["payload"])
    value = answer()
    value.update(status="abstained", supporting_points=[])
    value["conclusion"]["citation_ids"] = []
    target.validate_answer(json.dumps(value), packet()["payload"])
    value["qualifications"] = [copy.deepcopy(answer()["supporting_points"][0])]
    with pytest.raises(ValueError, match="other prose"):
        target.validate_answer(json.dumps(value), packet()["payload"])


@pytest.mark.parametrize("kwargs", [{"count": 40000}, {"count": 0}])
def test_context_blocks_generation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, kwargs: dict[str, Any]
) -> None:
    calls = mock_provider(monkeypatch, **kwargs)
    result = invoke(tmp_path)
    assert result["status"] == "failed"
    assert len(calls) == 1
    assert not (tmp_path / "dispatch.json").exists()


@pytest.mark.parametrize("kwargs", [{"text": "broken json"}, {"incomplete": True}, {"status": 500}])
def test_output_failures_preserved_no_retry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, kwargs: dict[str, Any]
) -> None:
    calls = mock_provider(monkeypatch, **kwargs)
    result = invoke(tmp_path)
    assert result["status"] == "failed"
    assert len(calls) == 2
    assert result["generation_calls"] == 1
    assert (tmp_path / "generation_response.body").exists()
    assert not (tmp_path / "candidate.json").exists()


def test_run_resume_no_calls_and_tamper(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = mock_provider(monkeypatch)
    records = [{**packet(), "case_id": key} for key in target.INITIAL]
    monkeypatch.setattr(target, "load_smoke", lambda root, **kwargs: (records, {}))
    output = tmp_path / "run"
    first = asyncio.run(target.run(tmp_path, output))
    assert first["valid_candidates"] == 3
    assert asyncio.run(target.run(tmp_path, output)) == first
    assert len(calls) == 6
    (output / "C041" / "raw_answer.txt").write_text("tampered")
    with pytest.raises(ValueError, match="inventory changed"):
        asyncio.run(target.run(tmp_path, output))


def test_interrupted_attempt_never_redispatched(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls = mock_provider(monkeypatch)
    records = [{**packet(), "case_id": key} for key in target.INITIAL]
    monkeypatch.setattr(target, "load_smoke", lambda root, **kwargs: (records, {}))
    output = tmp_path / "run"
    asyncio.run(target.run(tmp_path, output))
    (output / "completion.json").unlink()
    (output / "C041" / "completion.json").unlink()
    with pytest.raises(ValueError, match="Interrupted"):
        asyncio.run(target.run(tmp_path, output))
    assert len(calls) == 6
    assert json.loads((output / "interrupted.json").read_text())["redispatch_permitted"] is False


def test_count_unsupported_no_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = mock_provider(monkeypatch, count_status=404)
    result = invoke(tmp_path)
    assert result["status"] == "failed"
    assert result["generation_calls"] == 0
    assert len(calls) == 1


def test_required_point_field_not_defaulted() -> None:
    value = answer()
    del value["conclusion"]["applies_to"]
    with pytest.raises(Exception, match="applies_to"):
        target.validate_answer(json.dumps(value), packet()["payload"])


def test_expired_run_no_count(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = mock_provider(monkeypatch)
    result = asyncio.run(
        target.generate_one(
            packet(),
            tmp_path,
            json.loads(target.CONFIG.read_text()),
            target.PROMPT.read_text(),
            time.monotonic() - 1,
        )
    )
    assert result["status"] == "failed"
    assert not calls


@pytest.mark.parametrize(
    "panel,repeat",
    [("other", 1), ("initial_three", 3), ("initial_three", True), ("initial_three", 1.0)],
)
def test_scope_rejected_before_loading(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, panel: str, repeat: int
) -> None:
    """Unsupported panels or extra sampling cannot reach source loading or providers."""

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Source loaded")

    monkeypatch.setattr(target, "load_smoke", forbidden)
    with pytest.raises(ValueError):
        asyncio.run(target.run(tmp_path, tmp_path / "run", panel=panel, repeat=repeat))


def test_complete_six_repeat_identity_and_no_reroll(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Six-case repetition preserves full coverage and replay makes no new calls."""
    calls = mock_provider(monkeypatch)
    records = [{**packet(), "case_id": key} for key in target.EXPANDED]
    monkeypatch.setattr(target, "load_smoke", lambda root, **kwargs: (records, {}))
    config = json.loads(target.CONFIG.read_text())
    config.update(max_generation_calls=6, max_count_calls=6, max_spend_usd=3)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    output = tmp_path / "repeat"
    result = asyncio.run(
        target.run(tmp_path, output, config_path=path, panel="expanded_six", repeat=2)
    )
    assert result["case_ids"] == target.EXPANDED
    assert result["valid_candidates"] == 6
    assert all(row["repeat"] == 2 for row in result["results"])
    assert len({row["candidate_id"] for row in result["results"]}) == 6
    assert len(calls) == 12
    assert (
        asyncio.run(target.run(tmp_path, output, config_path=path, panel="expanded_six", repeat=2))
        == result
    )
    assert len(calls) == 12
    with pytest.raises(FileExistsError):
        asyncio.run(target.run(tmp_path, output, config_path=path, panel="expanded_six", repeat=1))
    assert len(calls) == 12


@pytest.mark.parametrize(
    "override", [{"max_generation_calls": 2}, {"max_count_calls": 2}, {"max_retries": 1}]
)
def test_call_capacity_and_retry_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, override: dict[str, int]
) -> None:
    """Underbudget panel coverage and hidden retries fail before native requests."""
    calls = mock_provider(monkeypatch)
    records = [{**packet(), "case_id": key} for key in target.INITIAL]
    monkeypatch.setattr(target, "load_smoke", lambda root, **kwargs: (records, {}))
    config = json.loads(target.CONFIG.read_text())
    config.update(override)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError):
        asyncio.run(target.run(tmp_path, tmp_path / "run", config_path=path))
    assert not calls


def test_frozen_panel_manifest_names() -> None:
    """CLI panel names must resolve to the accepted fixed-six manifest membership."""
    manifest = json.loads(target.PANEL.read_text())
    assert target.panel_case_ids("initial_three") == manifest["initial_three"]
    assert target.panel_case_ids("expanded_six") == manifest["fixed_six"]


@pytest.mark.parametrize(
    "override",
    [
        {"max_spend_usd": float("nan")},
        {"count_cost_allowance_usd": float("inf")},
        {"reserve_input_per_million": -1},
        {"max_output_tokens": True},
        {"max_input_tokens": 1.5},
        {"timeout_seconds": 0},
        {"max_retries": False},
        {"provider": "anthropic"},
        {"base_url": "https://example.com/v1"},
        {"service_tier": "priority"},
        {"reasoning_summary": "auto"},
        {"model": ""},
        {"context_tokens": 4096},
    ],
)
def test_invalid_config_fails_before_namespace_or_network(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, override: dict[str, Any]
) -> None:
    """Malformed budgets and misleading controls cannot reach provider dispatch."""
    calls = mock_provider(monkeypatch)
    records = [{**packet(), "case_id": key} for key in target.INITIAL]
    monkeypatch.setattr(target, "load_smoke", lambda root, **kwargs: (records, {}))
    config = json.loads(target.CONFIG.read_text())
    config.update(override)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    output = tmp_path / "run"
    with pytest.raises(ValueError):
        asyncio.run(target.run(tmp_path, output, config_path=path))
    assert not output.exists()
    assert not calls


def test_stopped_panel_retains_repeat_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A preflight failure preserves identities for every undispatched panel slot."""
    calls = mock_provider(monkeypatch, count_status=404)
    records = [{**packet(), "case_id": key} for key in target.INITIAL]
    monkeypatch.setattr(target, "load_smoke", lambda root, **kwargs: (records, {}))
    output = tmp_path / "run"
    result = asyncio.run(target.run(tmp_path, output, repeat=2))
    assert len(calls) == 1
    assert [row["status"] for row in result["results"]] == [
        "failed",
        "not_dispatched",
        "not_dispatched",
    ]
    assert all(row["attempt"] == 1 and row["repeat"] == 2 for row in result["results"])
    assert asyncio.run(target.run(tmp_path, output, repeat=2)) == result
    assert len(calls) == 1


@pytest.mark.parametrize(
    "overrides",
    [
        {"returned_model": "different-model"},
        {"omit_usage": True},
        {"usage": {"input_tokens": 100, "output_tokens": 5000, "total_tokens": 5100}},
        {"usage": {"input_tokens": 40000, "output_tokens": 80, "total_tokens": 40080}},
        {"usage": {"input_tokens": -1, "output_tokens": 80, "total_tokens": 79}},
    ],
)
def test_unverified_output_preserves_receipt_without_candidate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, overrides: dict[str, Any]
) -> None:
    """Provider identity/accounting violations retain diagnostics without valid output."""
    calls = mock_provider(monkeypatch, **overrides)
    result = invoke(tmp_path)
    assert result["status"] == "failed"
    assert "accounting uncertain" in result["failure"]
    assert len(calls) == 2
    assert "returned_model" in result and "usage" in result
    assert (tmp_path / "raw_answer.txt").exists()
    assert (tmp_path / "generation_response.body").exists()
    assert not (tmp_path / "candidate.json").exists()


@pytest.mark.parametrize("text", [None, "broken json"])
def test_client_close_failure_preserves_final_receipts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, text: str | None
) -> None:
    """Cleanup errors cannot suppress the final seal or an earlier failure reason."""
    calls = mock_provider(monkeypatch, text=text)
    client_factory = target.DefaultAsyncHttpxClient  # type: ignore[attr-defined]

    def client(**kwargs: Any) -> DefaultAsyncHttpxClient:
        """Close the fixture transport, then simulate a cleanup exception."""
        instance = client_factory(**kwargs)
        close = instance.aclose

        async def failing_close() -> None:
            """Simulate failure after releasing transport resources."""
            await close()
            raise RuntimeError("fixture close failure")

        instance.aclose = failing_close  # type: ignore[method-assign]
        return instance

    monkeypatch.setattr(target, "DefaultAsyncHttpxClient", client)
    result = invoke(tmp_path)
    assert result["status"] == "failed"
    assert result["cleanup_error"] == "RuntimeError: fixture close failure"
    assert len(calls) == 2
    assert (tmp_path / "result.json").exists()
    assert (tmp_path / "completion.json").exists()
    if text is not None:
        assert result["failure_type"] == "JSONDecodeError"
