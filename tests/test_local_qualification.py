"""Retained-source exceptions are exact and cannot waive independent evidence."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from er_commons.source_release.local_qualification import (
    RetainedQualificationObservations,
    RetainedQualificationPolicy,
    assess_retained_qualification,
)


def _inputs() -> tuple[RetainedQualificationPolicy, RetainedQualificationObservations]:
    """Supply synthetic records only; no PDF or external evidence is consulted."""
    exceptions = [
        {"object_id": 12649, "generation": 0, "physical_page": 28, "reference_path": "/Thumb"},
        {
            "object_id": 12168,
            "generation": 0,
            "physical_page": 28,
            "reference_path": "/Thumb/ColorSpace/3",
        },
    ]
    policy = RetainedQualificationPolicy.model_validate(
        {
            "schema_version": "retained_qualification_policy_v1",
            "source_sha256": "a" * 64,
            "page_count": 756,
            "exceptions": exceptions,
            "diagnostic_refs": ["diagnostic.json#sha256=" + "b" * 64],
            "cover_page": 3,
            "cover_title": "APPENDIX F.1 TRANSPORTATION IMPACT ASSESSMENT [REVISED]",
            "project_phrase": "City of Brisbane",
            "edition_phrase": "Final EIR",
            "corroboration_page": 5,
            "corroboration_title": "Transportation Impact Assessment",
            "memo_phrase": "Existing Traffic Conditions Memo",
            "memo_heading_page": 136,
            "memo_body_page": 137,
            "memo_body_phrases": [
                "MEMORANDUM",
                "Subject: Baylands Specific Plan: Existing Traffic Conditions",
            ],
            "allowed_pages": [3, 5, 133, 136, 137],
        }
    )
    observations = RetainedQualificationObservations.model_validate(
        {
            "source_sha256": "a" * 64,
            "page_count": 756,
            "diagnostic_refs": policy.diagnostic_refs,
            "structural_failures": exceptions,
            "non_thumbnail_references": [],
            "rendered_body_pages": [28],
            "pages": [
                {"physical_page": 3, "text": policy.cover_title + "\nCity of Brisbane\nFinal EIR"},
                {"physical_page": 5, "text": "Transportation\nImpact Assessment"},
                {"physical_page": 133, "text": "Contents: Existing Traffic Conditions Memo"},
                {"physical_page": 136, "text": "Appendix A: Existing Traffic\nConditions Memo"},
                {
                    "physical_page": 137,
                    "text": (
                        "MEMORANDUM\nSubject: Baylands Specific Plan: Existing Traffic Conditions"
                    ),
                },
            ],
        }
    )
    return policy, observations


def test_retained_observations_qualify_without_filesystem_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The assessment consumes records and never reopens or hashes a PDF."""
    policy, observations = _inputs()

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("unexpected source access")

    monkeypatch.setattr("builtins.open", forbidden)
    result = assess_retained_qualification(policy, observations)
    assert result.qualified
    assert result.dimensions["internal"].physical_pages == (136, 137)
    assert "decoder completeness" in result.limitation
    assert assess_retained_qualification(policy, observations) == result


@pytest.mark.parametrize(
    ("field", "value", "dimension"),
    [
        ("source_sha256", "c" * 64, "identity"),
        ("page_count", 755, "identity"),
        ("diagnostic_refs", ["different-evidence.json"], "structure"),
        ("structural_failures", [], "structure"),
        ("non_thumbnail_references", ["/Contents"], "structure"),
        ("rendered_body_pages", [], "structure"),
    ],
)
def test_mismatched_observations_fail(field: str, value: Any, dimension: str) -> None:
    """A reviewed exception cannot migrate to different bytes or damage."""
    policy, observations = _inputs()
    data = observations.model_dump()
    data[field] = value
    result = assess_retained_qualification(
        policy, RetainedQualificationObservations.model_validate(data)
    )
    assert not result.qualified
    assert result.dimensions[dimension].status == "fail"


@pytest.mark.parametrize(
    ("page", "text", "dimension"),
    [
        (3, "Transportation Impact Assessment\nCity of Brisbane\nFinal EIR", "title"),
        (3, "APPENDIX F.1 TRANSPORTATION IMPACT ASSESSMENT [REVISED]\nFinal EIR", "title"),
        (3, "APPENDIX F.1 TRANSPORTATION IMPACT ASSESSMENT [REVISED]\nCity of Brisbane", "edition"),
        (5, "Bayshore Mobility Study", "title"),
        (136, "Appendix A: Existing Traffic Conditions", "internal"),
        (137, "See Existing Traffic Conditions Memo", "internal"),
    ],
)
def test_independent_text_requirements(page: int, text: str, dimension: str) -> None:
    """The TOC alone cannot substitute for an actual memo heading and body."""
    policy, observations = _inputs()
    data = observations.model_dump()
    for item in data["pages"]:
        if item["physical_page"] == page:
            item["text"] = text
    result = assess_retained_qualification(
        policy, RetainedQualificationObservations.model_validate(data)
    )
    assert not result.qualified
    assert result.dimensions[dimension].status == "fail"


def test_changed_object_path_and_extra_failures_rejected() -> None:
    """Object numbers alone do not prove a thumbnail-only failure."""
    policy, observations = _inputs()
    for change in ({"reference_path": "/Contents"}, {"object_id": 12650}, {"physical_page": 29}):
        data = observations.model_dump()
        data["structural_failures"][0].update(change)
        assert not assess_retained_qualification(
            policy, RetainedQualificationObservations.model_validate(data)
        ).qualified
    data = observations.model_dump()
    data["structural_failures"] += (dict(data["structural_failures"][0], object_id=999),)
    assert not assess_retained_qualification(
        policy, RetainedQualificationObservations.model_validate(data)
    ).qualified


def test_page_scope_and_policy_version_enforced() -> None:
    """A missing, repeated or newly searched page cannot enter the frozen window."""
    policy, observations = _inputs()
    data = observations.model_dump()
    data["pages"] = data["pages"][:-1]
    assert (
        assess_retained_qualification(
            policy, RetainedQualificationObservations.model_validate(data)
        )
        .dimensions["evidence_scope"]
        .status
        == "fail"
    )
    policy_data = policy.model_dump()
    policy_data["schema_version"] = "retained_qualification_policy_v2"
    with pytest.raises(ValidationError):
        RetainedQualificationPolicy.model_validate(policy_data)
    policy_data = policy.model_dump()
    policy_data["allowed_pages"] = (3, 3, 5, 133, 136, 137)
    with pytest.raises(ValidationError):
        RetainedQualificationPolicy.model_validate(policy_data)


def test_changed_policy_has_distinct_disposition_identity() -> None:
    """A revised requirement remains distinguishable from the frozen predecessor."""
    policy, observations = _inputs()
    original = assess_retained_qualification(policy, observations)
    data = policy.model_dump()
    data["memo_phrase"] = "Different Memo"
    revised = assess_retained_qualification(
        RetainedQualificationPolicy.model_validate(data), observations
    )
    assert original.policy_sha256 != revised.policy_sha256
    assert not revised.qualified
