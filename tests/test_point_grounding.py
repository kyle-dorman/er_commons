"""Offline strict-output and citation boundaries for independent G."""

import hashlib
import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from er_commons import point_grounding as core

REPO = Path(__file__).resolve().parents[1]


def evidence(citation: str = "s1") -> dict[str, Any]:
    """Invent a complete source with table headers, units and a footnote."""
    return {
        "occurrence_id": citation,
        "source_id": "invented",
        "canonical_target": {"section_id": "section-1"},
        "title": "Original title",
        "full_source_text": "  Source text\nwith whitespace.  ",
        "tables": [{"headers": ["Speed (mph)"], "rows": [[35]], "footnotes": ["planned"]}],
        "physical_pages": [1],
        "printed_labels": ["i"],
    }


def test_locked_prompt_verbatim() -> None:
    """Keep the selected prompt and semantic schema exactly bound to selection."""
    from er_commons.artifact_io import stable_json_sha256

    selected = json.loads(
        (
            Path(__file__).resolve().parents[1] / "configs/point_grounding_selected_v1.json"
        ).read_text()
    )
    assert core.PROMPT_VERSION == selected["prompt_version"]
    assert stable_json_sha256(core.system_prompt()) == selected["prompt_sha256"]
    assert stable_json_sha256(core.output_json_schema()) == selected["schema_sha256"]
    with pytest.raises(ValueError):
        core.system_prompt("retired.prompt.v1")


@pytest.mark.parametrize("supported", [True, False])
def test_strict_valid_output(supported: bool) -> None:
    """Preserve both semantic labels and original nonblank reasons."""
    result = {"supported": supported, "reason": " Original reason. "}
    assert core.parse_output(json.dumps(result)) == result


@pytest.mark.parametrize(
    "raw",
    [
        '{"supported": 1, "reason": "x"}',
        '{"supported": "false", "reason": "x"}',
        '{"supported": null, "reason": "x"}',
        '{"supported": false, "reason": "  "}',
        '{"supported": false, "reason": 12}',
        '{"supported": false, "reason": "x", "point_id": "p1"}',
        '{"supported": false, "explanation": "x"}',
        '{"supported": true, "supported": false, "reason": "x"}',
        '```json\n{"supported": false, "reason": "x"}\n```',
        'Here: {"supported": false, "reason": "x"}',
        '{"supported": false, "reason": "x"} {}',
        '[{"supported": false, "reason": "x"}]',
        '{"supported": false, "reason": NaN}',
        '{"supported": false, "reason": "x"',
    ],
)
def test_invalid_is_never_semantic_false(raw: str) -> None:
    """No coercion, wrapper stripping, duplicate keys or output repair is allowed."""
    with pytest.raises(ValueError):
        core.parse_output(raw)


def test_projection_preserves_exact_owned_sources() -> None:
    """Deduplicate citations while preserving source order and nested source bytes."""
    originals = {"s1": evidence(), "s2": evidence("s2")}
    result = core.prepare_point(
        " Question ",
        " Point ",
        ["s2", "s1", "s2"],
        allowed_citation_ids=originals,
        load_evidence=originals.__getitem__,
    )
    assert result.status == "not_run" and result.supported is None
    assert result.packet == {
        "question": " Question ",
        "point_text": " Point ",
        "evidence": [originals["s2"], originals["s1"]],
    }
    assert result.packet is not None
    result.packet["evidence"][0]["tables"][0]["rows"][0][0] = 99
    assert originals["s2"]["tables"][0]["rows"] == [[35]]


@pytest.mark.parametrize("field", ["conclusion", "point_id", "qualification", "expected_label"])
def test_no_other_answer_context(field: str) -> None:
    """Refuse extra model-visible context rather than silently forwarding it."""
    with pytest.raises(ValueError):
        core.validate_input(
            {"question": "Q", "point_text": "P", "evidence": [evidence()], field: "x"}
        )


def test_bad_citation_rejects_entire_point_before_loading() -> None:
    """Never salvage the good portion of a mixed valid/unresolved citation list."""
    loader = Mock(return_value=evidence())
    result = core.prepare_point(
        "Q",
        "P",
        ["s1", "bad"],
        allowed_citation_ids={"s1"},
        load_evidence=loader,
    )
    assert result.status == "precheck_failed"
    assert result.error_type == "unresolved_citation"
    assert result.unresolved_citation_ids == ("bad",)
    assert result.packet is None and result.supported is None
    loader.assert_not_called()


@pytest.mark.parametrize("entries", [[evidence(), evidence()], [evidence("other")], []])
def test_duplicate_missing_or_foreign_evidence(entries: list[dict[str, Any]]) -> None:
    """Exact citation ownership is mechanical and separate from source relevance."""
    with pytest.raises(ValueError):
        core.validate_input(
            {"question": "Q", "point_text": "P", "evidence": entries}, citation_ids=["s1"]
        )


def test_wrong_loaded_identity_is_evaluator_input_error() -> None:
    """A source-loader identity mistake cannot become semantic unsupportedness."""
    result = core.prepare_point(
        "Q",
        "P",
        ["s1"],
        allowed_citation_ids={"s1"},
        load_evidence=lambda _: evidence("wrong"),
    )
    assert result.status == "invalid_input"
    assert result.supported is None and result.packet is None


def test_published_precheck_fixtures() -> None:
    """Execute all 57 published cases with mocked artifact failures, no generation."""
    pointer = json.loads(
        (REPO / "docs/specs/task09f1_grounding_candidates_v2_result.json").read_text()
    )
    binding = pointer["artifacts"]["precheck_fixtures"]
    path = Path(binding["path"])
    if not path.exists():
        pytest.skip("Published external development fixtures are not mounted")
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == binding["sha256"]
    fixtures = json.loads(raw)
    assert len(fixtures) == 57
    for fixture in fixtures:
        citations = fixture["citation_ids"]
        allowed = {c for c in citations if "INTENTIONALLY-UNRESOLVED" not in c}
        loader = Mock(side_effect=OSError("simulated valid artifact unavailable"))
        result = core.prepare_point(
            "Known applicable development question",
            fixture["point_text"],
            citations,
            allowed_citation_ids=allowed,
            load_evidence=loader,
        )
        assert result.status == fixture["expected_status"], fixture["fixture_id"]
        assert result.supported is None and result.packet is None
        if fixture["simulated_condition"] != "valid_source_loading_failure":
            loader.assert_not_called()
        else:
            loader.assert_called_once()


def test_published_panel_all_payloads_validate() -> None:
    """Exercise every locked packet through the runtime boundary, including sparse sources."""
    from er_commons.point_grounding_panel import PANEL_POINTER, load_panel

    pointer = json.loads(PANEL_POINTER.read_text())
    if not Path(pointer["panels"]["g"]["artifact_root"]).exists():
        pytest.skip("Published external calibration panel is not mounted")
    samples, _, _ = load_panel()
    for sample in samples:
        assert (
            core.validate_input(
                sample["packet"], citation_ids=sample["metadata"]["owned_citation_ids"]
            )
            == sample["packet"]
        )


def test_source_optional_fields_are_not_invented() -> None:
    """Keep omitted table/printed-label fields absent when the source omits them."""
    source = evidence()
    del source["tables"]
    del source["printed_labels"]
    packet = {"question": "Q", "point_text": "P", "evidence": [source]}
    assert core.validate_input(packet) == packet
