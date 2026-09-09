"""Focused tests for readable response-inventory CLI input failures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from er_commons.response_inventory.cli import _load_review_dispositions


def test_review_dispositions_load_stage_specific_shapes(tmp_path: Path) -> None:
    parser = argparse.ArgumentParser()
    full_path = tmp_path / "full.json"
    full_path.write_text(
        json.dumps(
            {
                "6": {
                    "status": "accepted",
                    "reviewer": "reviewer",
                    "reason": "visible evidence agrees",
                    "evidence_id": "renderv1-test",
                }
            }
        )
    )
    assert _load_review_dispositions(full_path, parser, decision_objects=True) == {
        6: {
            "status": "accepted",
            "reviewer": "reviewer",
            "reason": "visible evidence agrees",
            "evidence_id": "renderv1-test",
        }
    }

    pilot_path = tmp_path / "pilot.json"
    pilot_path.write_text('{"6": "accepted"}')
    assert _load_review_dispositions(pilot_path, parser, decision_objects=False) == {6: "accepted"}


@pytest.mark.parametrize(
    ("payload", "decision_objects", "message"),
    [
        ("[]", True, "must contain one JSON object"),
        ('{"page-six": {}}', True, "page keys must be integers"),
        ('{"6": "accepted"}', True, "string-valued decision objects"),
        ('{"6": {"status": 7}}', True, "string-valued decision objects"),
        ('{"6": {}}', False, "map pages to status strings"),
        ("not-json", True, "cannot read --review-dispositions"),
    ],
    ids=["not-object", "bad-page", "05d-string", "05d-nonstring", "05c-object", "json"],
)
def test_review_dispositions_reject_malformed_input(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    payload: str,
    decision_objects: bool,
    message: str,
) -> None:
    path = tmp_path / "decisions.json"
    path.write_text(payload)
    with pytest.raises(SystemExit):
        _load_review_dispositions(
            path,
            argparse.ArgumentParser(),
            decision_objects=decision_objects,
        )
    assert message in capsys.readouterr().err
