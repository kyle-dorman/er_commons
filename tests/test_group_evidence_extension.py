"""Research reopening cannot rewrite the historical claim review or silently add cases."""

from pathlib import Path

import pytest

from er_commons.group_evidence_extension import REOPENED, _combined_rows, validate_authorization


def authorization_fixture() -> tuple[dict, dict]:
    """Return a scoped synthetic instruction and exact upstream bindings."""
    upstream = {
        "upstream_result": {"path": "result", "sha256": "x"},
        "upstream_handoff": {"path": "handoff", "sha256": "y"},
        "held_case_ids": REOPENED,
    }
    authorization = {
        "schema_version": "task08e.research_reopening.v1",
        "actor": "Kyle",
        "verbatim_user_instruction": "Research these three; preserve old decisions.",
        "reopened_case_ids": REOPENED,
        "scope": "research_preparation_only",
        "historical_decisions_unchanged": True,
        "human_evidence_review_authorized": False,
        "08f_authorized": False,
        "research_directions": {cid: "Test question gaps" for cid in REOPENED},
        **{key: upstream[key] for key in ("upstream_result", "upstream_handoff")},
    }
    return authorization, upstream


@pytest.mark.parametrize(
    "field,value",
    [
        ("reopened_case_ids", ["C013"]),
        ("human_evidence_review_authorized", True),
        ("historical_decisions_unchanged", False),
        ("verbatim_user_instruction", ""),
        ("08f_authorized", True),
        ("upstream_handoff", {}),
    ],
)
def test_reopening_rejects_scope_or_binding_drift(field: str, value: object) -> None:
    """Explicit research scope cannot become an approval or deferred-case backfill."""
    authorization, upstream = authorization_fixture()
    validate_authorization(authorization, upstream)
    authorization[field] = value
    with pytest.raises(ValueError, match="authorization"):
        validate_authorization(authorization, upstream)


def test_combination_keeps_upstream_order_and_zero_new_claims() -> None:
    """Component concatenation must not displace the three reopened questions."""
    order = [f"C{i:03}" for i in range(1, 58) if i not in (13, 23, 38, 57)]
    common = {
        "upstream_handoff": {"sha256": "sealed"},
        "deferred_case_ids": ["C013", "C023", "C038", "C057"],
    }
    base = {
        **common,
        "cases": [{"case_id": cid} for cid in order if cid not in REOPENED],
        "held_case_ids": REOPENED,
    }
    supplement = {
        **common,
        "cases": [{"case_id": cid} for cid in REOPENED],
        "held_case_ids": [],
        "approved_claims": 0,
    }
    review = {"source_context": {"cases": [{"case_id": cid} for cid in order]}}
    assert [row["case_id"] for row in _combined_rows(base, supplement, review)] == order
    supplement["approved_claims"] = 1
    with pytest.raises(ValueError, match="membership"):
        _combined_rows(base, supplement, review)


def test_verified_projection_preserves_original_snapshots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Synthetic held input retains rejected claims and exact historical hold feedback."""
    import er_commons.group_evidence_extension as extension
    from er_commons.group_claims_batch import reference, write_new

    authorization, upstream = authorization_fixture()
    required = {"required_reading": []}
    review = {
        "source_context": {
            "cases": [{"case_id": cid, "question": {"text": cid}} for cid in REOPENED],
            "limitations": ["old"],
        },
        "cases": {
            cid: {
                "case_decision": {"decision": "hold", "feedback": "saved"},
                "claims": [{"decision": "rejected"}],
            }
            for cid in REOPENED
        },
        "advancing": [],
        "context_notes": {"all_57_decisions": {}, "holds": ["historical"]},
    }
    write_new(tmp_path / "review.json", review)
    write_new(tmp_path / "required.json", required)
    handoff = {
        "review": reference(tmp_path / "review.json"),
        "required_context": reference(tmp_path / "required.json"),
        "supplemental_inventory": {"retained": True},
    }
    write_new(tmp_path / "handoff.json", handoff)
    write_new(tmp_path / "result.json", {"handoff": reference(tmp_path / "handoff.json")})
    upstream.update(
        upstream_handoff=reference(tmp_path / "handoff.json"),
        upstream_result=reference(tmp_path / "result.json"),
        deferred_case_ids=["C013", "C023", "C038", "C057"],
    )
    authorization.update(
        upstream_handoff=upstream["upstream_handoff"], upstream_result=upstream["upstream_result"]
    )
    write_new(tmp_path / "authorization.json", authorization)
    monkeypatch.setattr(extension, "load_inputs", lambda _: upstream)
    result = extension.load_supplement_inputs(
        tmp_path / "result.json", tmp_path / "authorization.json"
    )
    for case in result["cases"]:
        assert case["approved_claims"] == case["support_chains"] == []
        assert case["reviewed_case"] == review["cases"][case["case_id"]]
        assert case["source_context"] in review["source_context"]["cases"]
        assert case["historical_reconciliation"] == {"holds": ["historical"]}
    register = extension.prepare_supplement_inputs(
        tmp_path / "result.json", tmp_path / "authorization.json", tmp_path / "out"
    )
    assert register == extension.prepare_supplement_inputs(
        tmp_path / "result.json", tmp_path / "authorization.json", tmp_path / "out"
    )


def test_composite_seal_roundtrip_and_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Composition preserves exact child bytes and rejects summary or closure drift."""
    import json

    import er_commons.group_evidence_extension as extension
    import er_commons.group_evidence_publication as publication
    from er_commons.group_claims_batch import reference, write_new

    authorization, upstream = authorization_fixture()
    order = [f"C{i:03}" for i in range(1, 58) if i not in (13, 23, 38, 57)]
    review_path = tmp_path / "review.json"
    write_new(review_path, {"source_context": {"cases": [{"case_id": cid} for cid in order]}})
    write_new(tmp_path / "handoff.json", {"review": reference(review_path)})
    write_new(tmp_path / "upstream.json", {"handoff": reference(tmp_path / "handoff.json")})
    upstream.update(
        upstream_handoff=reference(tmp_path / "handoff.json"),
        upstream_result=reference(tmp_path / "upstream.json"),
        deferred_case_ids=["C013", "C023", "C038", "C057"],
    )
    authorization.update(
        upstream_handoff=upstream["upstream_handoff"], upstream_result=upstream["upstream_result"]
    )
    write_new(tmp_path / "authorization.json", authorization)
    common = {
        "upstream_handoff": upstream["upstream_handoff"],
        "deferred_case_ids": upstream["deferred_case_ids"],
        "source_occurrences": 0,
        "beyond_claim_findings": 0,
        "query_receipts": 0,
    }
    base = {
        **common,
        "cases": [{"case_id": cid} for cid in order if cid not in REOPENED],
        "held_case_ids": REOPENED,
        "approved_claims": 385,
    }
    supplement = {
        **common,
        "cases": [{"case_id": cid} for cid in REOPENED],
        "held_case_ids": [],
        "approved_claims": 0,
        "research_reopening_authorization": reference(tmp_path / "authorization.json"),
    }
    base_result = tmp_path / "base_result.json"
    supplement_result = tmp_path / "supplement_result.json"
    write_new(base_result, {"completion": {"path": str(tmp_path / "base" / "completion.json")}})
    write_new(
        supplement_result,
        {"completion": {"path": str(tmp_path / "supplement" / "completion.json")}},
    )
    monkeypatch.setattr(
        publication,
        "verify_prepared_result",
        lambda path: base if path == base_result else supplement,
    )
    monkeypatch.setattr(extension, "load_inputs", lambda _: upstream)
    out = tmp_path / "combined"
    out.mkdir()
    (out / "REVIEW_INSTRUCTIONS.md").write_text("Blank review; saved order.")
    write_new(tmp_path / "qualification.json", {"status": "pass"})
    original_children = [path.read_bytes() for path in (base_result, supplement_result)]
    result = extension.publish_combined_result(
        base_result, supplement_result, out, qualification_path=tmp_path / "qualification.json"
    )
    assert (
        extension.publish_combined_result(
            base_result, supplement_result, out, qualification_path=tmp_path / "qualification.json"
        )
        == result
    )
    result_path = tmp_path / "result53.json"
    write_new(result_path, result)
    verified = extension.verify_combined_result(result_path)
    assert [row["case_id"] for row in verified["cases"]] == order
    assert verified["approved_claims"] == 385
    assert [path.read_bytes() for path in (base_result, supplement_result)] == original_children
    result_path.write_text(json.dumps({**result, "human_decisions": 1}))
    with pytest.raises(ValueError, match="summary differs"):
        extension.verify_combined_result(result_path)
    result_path.write_text(json.dumps(result))
    (out / "unexpected.txt").write_text("undeclared")
    with pytest.raises(ValueError, match="closure changed"):
        extension.verify_combined_result(result_path)
    with pytest.raises(ValueError, match="separate"):
        extension.publish_combined_result(
            base_result,
            supplement_result,
            tmp_path / "base",
            qualification_path=tmp_path / "qualification.json",
        )
