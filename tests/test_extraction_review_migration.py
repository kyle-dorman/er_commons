"""Gate 2 request/command checks for the renamed historical review owner."""

from __future__ import annotations

import json
import runpy
import sys
from importlib.resources import files
from pathlib import Path

import pytest

from er_commons.human_review_support.extraction_review import request
from er_commons.human_review_support.extraction_review.final_pass import HANDOFF_ID, SCOPE_ID

ROOT = Path(__file__).parents[1]


def _spec(operation="prepare"):
    """Select historical profile and every input path as explicit request data."""
    return {
        "schema_version": "er_commons.extraction_review_request.v1",
        "operation": operation,
        "review_pass": "task03j_final",
        "data_root": "data",
        "retained_root": "data/accepted",
        "source_pdf_root": "data/sources",
        "prior_review_root": "data/prior",
        "schema_root": str(ROOT / "benchmarks/er_bench/schemas/task04a_review/v1"),
        "expected_source_count": 35,
        "scope_id": SCOPE_ID,
        "handoff_id": HANDOFF_ID,
    }


def test_request_requires_explicit_inputs_and_validates_profile(tmp_path):
    value = _spec()
    path = tmp_path / "review.json"
    path.write_text(json.dumps(value))
    parsed = request.load_review_request(path, "prepare")
    assert parsed.data_root == tmp_path / "data"
    assert parsed.retained_root == tmp_path / "data/accepted"
    assert parsed.render_pages is False
    value.pop("retained_root")
    with pytest.raises(ValueError, match="requires: retained_root"):
        request.ReviewRequestSpec.model_validate(value)
    value = _spec()
    value["handoff_id"] = "handoffv1-" + "0" * 64
    with pytest.raises(ValueError, match="historical final-pass profile"):
        request.ReviewRequestSpec.model_validate(value)


def test_rendering_requires_a_separate_explicit_request():
    value = _spec("build_final")
    value.update(gate_a_path="data/gate_a.json", review_run_id="reviewv1-task03j-final-c17")
    with pytest.raises(ValueError, match="render_pages=true"):
        request.ReviewRequestSpec.model_validate(value)
    value["render_pages"] = True
    assert request.ReviewRequestSpec.model_validate(value).render_pages


@pytest.mark.parametrize(
    "script",
    [
        "prepare_extraction_review",
        "build_extraction_review_bundle",
        "build_final_extraction_review",
        "publish_extraction_review",
        "record_review_finding",
        "set_review_register_status",
    ],
)
def test_renamed_help_has_no_settings_or_execution(script, monkeypatch, capsys):
    import er_commons.settings as settings

    def forbidden(*args, **kwargs):
        pytest.fail("help must not read settings or execute review work")

    monkeypatch.setattr(settings, "load_settings", forbidden)
    monkeypatch.setattr(request, "execute_review_request", forbidden)
    monkeypatch.setattr(sys, "argv", [script, "--help"])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(ROOT / "scripts" / f"{script}.py"), run_name="__main__")
    assert raised.value.code == 0
    help_text = capsys.readouterr().out
    if script in {"record_review_finding", "set_review_register_status"}:
        assert "--review-root" in help_text
    else:
        assert "--review-spec" in help_text and "--output-root" in help_text
    assert "--task-root-relative" not in help_text


def test_new_package_assets_preserve_historical_schema_contract():
    assets = files("er_commons.human_review_support.extraction_review.assets")
    assert all(
        assets.joinpath(name).is_file() for name in ("review.html", "review.js", "review.css")
    )
    from er_commons.human_review_support.extraction_review.config import REVIEW_PASS, SCHEMA_VERSION

    assert SCHEMA_VERSION == "er_commons.task04_review.v1"
    assert REVIEW_PASS == "task03h_first"
