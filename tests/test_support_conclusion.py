"""Exercise the explicit S v8 boundary without provider calls."""

import asyncio
import hashlib
import json
from copy import deepcopy

import httpx2
import pytest
from inspect_ai.model import ChatMessageSystem, ChatMessageUser
from judge_native_fixtures import envelope
from test_context_projection import fixture as context_fixture
from test_context_projection import item as context_item
from test_development_evaluation import a_result, fixture, judgment

from er_commons import adequacy_binary as core
from er_commons import adequacy_inspect as native
from er_commons import context_comparison, context_projection, support_claims, support_conclusion
from er_commons.artifact_io import stable_json_sha256
from er_commons.development_evaluation import pending_items, prepare_candidate
from er_commons.judge_context import baylands_overview

V8 = support_conclusion.VERSION
PACKET = {
    "question": "Why?",
    "candidate_conclusion": "The benefit applies only if the measure operates.",
    "candidate_supporting_points": [{"point_id": "P1", "text": "Operating it reduces demand."}],
}


def test_version_is_strict_and_legacy_unchanged():
    """V8 rejects excluded fields and preserves both historical prompt selections."""
    assert core.validate_input("S", PACKET, prompt_version=V8) == PACKET
    for field in ("candidate_qualifications", "optional_context", "reference_conclusion"):
        with pytest.raises(ValueError):
            core.validate_input("S", {**PACKET, field: []}, prompt_version=V8)
    with pytest.raises(ValueError):
        core.validate_input("S", PACKET, with_reference=True, prompt_version=V8)
    with pytest.raises(ValueError):
        core.validate_input("S", PACKET, prompt_version=support_claims.VERSION)
    for component in ("C",):
        with pytest.raises(ValueError):
            native._prompt_version(component, V8)
    assert native._prompt_version("S", None) == core.SUPPORT_BASIS_PROMPT_VERSION
    assert hashlib.sha256(core.system_prompt("S").encode()).hexdigest() == (
        "4d1d2b59cfc38dacc509500e4cbfdc68be20de21377ed7e133fbc4535c7c6266"
    )
    assert core.system_prompt("S", prompt_version=support_claims.VERSION) == support_claims.PROMPT
    assert core.output_json_schema("S", prompt_version=V8) == core.output_json_schema("S")


def test_real_projection_keeps_conclusion_verbatim_and_grounding():
    """Separate caveats cannot alter S input, and G keeps its qualification units."""
    answer = json.loads(fixture()[0])
    answer["conclusion"]["text"] = PACKET["candidate_conclusion"]
    answer["qualifications"] = [
        {**answer["supporting_points"][0], "point_id": "Q1", "text": "QUALIFICATION_SENTINEL"}
    ]
    answer["optional_context"] = [
        {**answer["supporting_points"][0], "point_id": "O1", "text": "CONTEXT_SENTINEL"}
    ]
    args = fixture(answer)
    legacy = prepare_candidate(*args)
    plan = prepare_candidate(*args, support_prompt_version=V8)
    s = next(i for i in plan["items"] if i["component"] == "S")
    old_s = next(i for i in legacy["items"] if i["component"] == "S")
    assert s["sample_id"] != old_s["sample_id"]
    assert s["packet"]["candidate_conclusion"] == answer["conclusion"]["text"]
    assert set(s["packet"]) == set(PACKET)
    assert "SENTINEL" not in json.dumps(s["packet"])
    assert [i for i in plan["items"] if i["component"] != "S"] == [
        i for i in legacy["items"] if i["component"] != "S"
    ]
    raw = {"support_sufficient": True, "reason_codes": [], "reason": "Supported."}
    saved = judgment(s, raw)
    with pytest.raises(ValueError, match="version mismatch"):
        pending_items(plan, [a_result(plan), saved])
    saved.update(prompt_version=V8, input_version=support_conclusion.INPUT_VERSION)
    pending_items(plan, [a_result(plan), saved])
    with pytest.raises(ValueError, match="explicit"):
        prepare_candidate(*args, support_prompt_version=support_claims.VERSION)


def test_context_envelope_requires_matching_version_identity():
    """Context envelopes retain v8 isolation and cannot reinterpret a legacy item."""
    record, mapping = context_fixture()
    item = context_item("S", record)
    item["packet"].pop("candidate_qualifications")
    item.update(prompt_version=V8, input_version=support_conclusion.INPUT_VERSION)
    item["payload_sha256"] = stable_json_sha256(item["packet"])
    item["sample_id"] = stable_json_sha256(
        {
            k: item[k]
            for k in ("identity", "component", "point_id", "prompt_version", "input_version")
        }
    )
    result = context_projection.project_judge(
        item,
        record,
        mapping,
        summary=baylands_overview(),
        prompt=support_conclusion.PROMPT,
        prompt_version=V8,
    )
    assert "candidate_qualifications" not in json.dumps(result)
    with pytest.raises(ValueError, match="versions differ"):
        context_projection.project_judge(
            item, record, mapping, summary=baylands_overview(), prompt=support_claims.PROMPT
        )
    changed = deepcopy(item)
    changed["input_version"] = "wrong"
    with pytest.raises(ValueError):
        context_projection.project_judge(
            changed,
            record,
            mapping,
            summary=baylands_overview(),
            prompt=support_conclusion.PROMPT,
            prompt_version=V8,
        )
    config = context_comparison._execution_config(
        "anthropic_generation",
        "S",
        result["messages"][0]["content"],
        4096,
        prompt_version=V8,
        max_connections=16,
    )
    assert config.max_tokens == 4096


def test_native_s_payload_is_conclusion_only(monkeypatch):
    """Exercise real SDK serialization through an offline HTTP transport."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "offline-fixture-key")
    bodies = []
    raw = json.dumps({"support_sufficient": True, "reason_codes": [], "reason": "Supported."})

    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx2.Response(200, json=envelope("anthropic_generation", raw))

    model = native.native_model(
        "anthropic_generation",
        "S",
        prompt_version=V8,
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
        streaming=False,
    )
    messages = [
        ChatMessageSystem(content=support_conclusion.PROMPT),
        ChatMessageUser(content=json.dumps(core.validate_input("S", PACKET, prompt_version=V8))),
    ]
    output = asyncio.run(model.generate(messages))
    assert output.completion == raw
    assert len(bodies) == 1
    content = bodies[0]["messages"][0]["content"]
    delivered = json.loads(content[0]["text"] if isinstance(content, list) else content)
    assert delivered == PACKET


def test_context_execute_rejects_extra_fields_before_provider(tmp_path, monkeypatch):
    """An explicit v8 dispatch validates isolation before constructing any provider."""
    from er_commons.judge_context import compose_project_context

    def forbidden(*args, **kwargs):
        raise AssertionError("Provider must not be constructed")

    monkeypatch.setattr(context_comparison.judge_inspect, "native_model", forbidden)
    with pytest.raises(ValueError):
        asyncio.run(
            context_comparison.execute(
                directory=tmp_path,
                condition="anthropic_generation",
                component="S",
                prompt=compose_project_context(support_conclusion.PROMPT, baylands_overview()),
                payload={**PACKET, "candidate_qualifications": []},
                deadline=1e20,
                max_output_tokens=4096,
                prompt_version=V8,
            )
        )
