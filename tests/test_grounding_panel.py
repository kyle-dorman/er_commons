"""Selection safety and deterministic nested panel invariants without inference."""

import json
from pathlib import Path

import pytest

from er_commons.grounding_panel import DEV3, DEV6, choose_samples, selection_metadata


def metadata() -> list[dict]:
    """Create enough eligible metadata for every slot, including fallback cases."""
    return [
        {
            "case_id": case,
            "variant_id": f"{case}-{category}-01",
            "perturbation_id": category,
            "grounding.score": score,
            "comparison_eligible": True,
        }
        for case in DEV6
        for category, score in (("F03", 0), ("F01", 1), ("P08", 2), ("R01", None))
    ]


def test_deterministic_nested_distinct_selection() -> None:
    """Input order cannot rotate frozen samples; dev3 is an exact dev6 subset."""
    chosen = choose_samples(metadata())
    assert chosen == choose_samples(list(reversed(metadata())))
    assert len(chosen) == len({r["sample_id"] for r in chosen}) == 24
    assert len([r for r in chosen if r["case_id"] in DEV3]) == 12
    for case in DEV6:
        rows = [r for r in chosen if r["case_id"] == case]
        assert len(rows) == 4
        assert rows[1]["expected_grounding"] == 0
        assert rows[2]["expected_grounding"] == 1
    assert any(r["coverage_gap"] for r in chosen)


def test_missing_score_slot_fails_closed() -> None:
    """No borrowing another score or case when a required slot is absent."""
    with pytest.raises(ValueError, match="No eligible distinct sample"):
        choose_samples([r for r in metadata() if r["grounding.score"] != 1])


def test_reserved_and_other_case_payloads_never_decoded(tmp_path: Path) -> None:
    """Malformed nonselected records prove routing precedes any JSON parser."""
    row = {
        "variant_id": "C041-F01-01",
        "case_id": "C041",
        "perturbation_id": "F01",
        "grounding": {"score": 1, "rationale": "not retained"},
        "comparison_eligible": True,
    }
    path = tmp_path / "expectations.jsonl"
    path.write_text(
        json.dumps(row)
        + '\n{"variant_id":"C041-reserved", THIS IS NOT JSON\n'
        + '{"variant_id":"C002-test", INVALID\n'
    )
    result = selection_metadata(path, {"C041-F01-01", "C002-test"})
    assert result == [
        {
            "variant_id": "C041-F01-01",
            "case_id": "C041",
            "perturbation_id": "F01",
            "grounding.score": 1,
            "comparison_eligible": True,
        }
    ]


@pytest.mark.parametrize(
    "change", ["duplicate", "missing", "excluded", "case_mismatch", "ambiguous"]
)
def test_metadata_identity_failures(tmp_path: Path, change: str) -> None:
    """Reject incomplete, excluded or ambiguous metadata before answer access."""
    row = {
        "variant_id": "C041-F01-01",
        "case_id": "C041",
        "perturbation_id": "F01",
        "grounding": {"score": 1},
        "comparison_eligible": True,
    }
    if change == "excluded":
        row["comparison_eligible"] = False
    if change == "case_mismatch":
        row["case_id"] = "C014"
    content = json.dumps(row) + "\n"
    if change == "duplicate":
        content *= 2
    if change == "missing":
        content = ""
    if change == "ambiguous":
        content = '{"variant_id":"C041-F01-01","variant_id":"C041-F02-01"}\n'
    path = tmp_path / "expectations.jsonl"
    path.write_text(content)
    with pytest.raises(ValueError):
        selection_metadata(path, {"C041-F01-01"})


def frozen_fixture(tmp_path: Path) -> Path:
    """Write synthetic sealed panel records to test consumer integrity checks."""
    from er_commons.artifact_io import file_reference, json_bytes, stable_json_sha256

    rows = choose_samples(metadata())
    packets, expectations = [], []
    for row in rows:
        packet = {"id": row["sample_id"], "payload": {"question": "Fixture"}}
        expectation = {"case_id": row["case_id"], "grounding": {"score": row["expected_grounding"]}}
        row.update(
            answer_sha256=stable_json_sha256(row["sample_id"]),
            packet_sha256=stable_json_sha256(packet),
            payload_sha256=stable_json_sha256(packet["payload"]),
            expectation_sha256=stable_json_sha256(expectation),
        )
        packets.append(packet)
        expectations.append({"sample_id": row["sample_id"], "expectation": expectation})
    artifacts = {}
    for name, content in (
        ("packets.json", packets),
        ("restricted_expectations.json", expectations),
    ):
        path = tmp_path / name
        path.write_bytes(json_bytes(content))
        artifacts[name] = file_reference(path, root=tmp_path)
    path = tmp_path / "manifest.json"
    path.write_bytes(
        json_bytes(
            {
                "schema_version": "task09e.grounding_panel.v1",
                "status": "frozen",
                "samples": rows,
                "artifacts": artifacts,
                "panels": {
                    name: [r["sample_id"] for r in rows if r["case_id"] in cases]
                    for name, cases in (("dev3", DEV3), ("dev6", DEV6))
                },
            }
        )
    )
    return path


def test_loader_verifies_nested_identity_and_separates_expectations(tmp_path: Path) -> None:
    """Consumer rows preserve IDs and keep synthetic scores outside packet payloads."""
    from er_commons.grounding_panel import load_panel_samples

    path = frozen_fixture(tmp_path)
    dev3, dev6 = load_panel_samples(path, "dev3"), load_panel_samples(path, "dev6")
    assert dev3 == dev6[:12]
    assert all("expected_score" not in row["packet"] for row in dev6)
    assert all(row["scope"] == "development" for row in dev6)
    with pytest.raises(ValueError, match="bounded"):
        load_panel_samples(path, "full19")
    packet_path = tmp_path / "packets.json"
    packet_path.write_text(packet_path.read_text() + " ")
    with pytest.raises(ValueError):
        load_panel_samples(path, "dev3")


def test_loader_rejects_altered_expectations_and_membership(tmp_path: Path) -> None:
    """A manifest cannot quietly rotate samples or change synthetic expectations."""
    from er_commons.grounding_panel import load_panel_samples

    path = frozen_fixture(tmp_path)
    manifest = json.loads(path.read_text())
    manifest["samples"][0]["expected_grounding"] = 0
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="identity differs"):
        load_panel_samples(path, "dev3")
    manifest["panels"]["dev3"].reverse()
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="membership"):
        load_panel_samples(path, "dev3")


@pytest.mark.parametrize("change", ["imbalance", "duplicate_answer", "missing_slot", "wrong_case"])
def test_loader_rejects_per_question_contract_changes(tmp_path: Path, change: str) -> None:
    """Total population size cannot hide invalid per-question membership."""
    from er_commons.grounding_panel import load_panel_samples

    path = frozen_fixture(tmp_path)
    manifest = json.loads(path.read_text())
    rows = manifest["samples"]
    if change == "imbalance":
        rows[0]["case_id"] = rows[4]["case_id"]
    elif change == "duplicate_answer":
        rows[0]["answer_sha256"] = rows[1]["answer_sha256"]
    elif change == "missing_slot":
        rows[0]["slot"] = "edge"
    else:
        rows[0]["sample_id"] = "C099-CONTROL"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        load_panel_samples(path, "dev6")


@pytest.mark.parametrize("change", ["duplicate", "extra", "missing"])
def test_loader_rejects_artifact_population_changes(tmp_path: Path, change: str) -> None:
    """Even correctly rehashed artifact lists must have exact unique row identities."""
    from er_commons.artifact_io import file_reference
    from er_commons.grounding_panel import load_panel_samples

    path = frozen_fixture(tmp_path)
    manifest = json.loads(path.read_text())
    artifact = tmp_path / "packets.json"
    packets = json.loads(artifact.read_text())
    if change == "missing":
        packets.pop()
    else:
        packets.append({**packets[0], "id": "extra"} if change == "extra" else packets[0])
    artifact.write_text(json.dumps(packets))
    manifest["artifacts"]["packets.json"] = file_reference(artifact, root=tmp_path)
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        load_panel_samples(path, "dev6")
