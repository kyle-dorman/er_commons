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
                "model": "gpt-6-luna",
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
                "usage": {"input_tokens": 100, "output_tokens": 80, "total_tokens": 180},
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
    assert result["candidate_sha256"] == target.sha256_file(tmp_path / "candidate.json")


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
    monkeypatch.setattr(target, "load_smoke", lambda root: (records, {}))
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
    monkeypatch.setattr(target, "load_smoke", lambda root: (records, {}))
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
