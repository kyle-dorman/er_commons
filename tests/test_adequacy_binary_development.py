"""Sealed miniature development fixtures test provenance, boundaries and exact projection."""

import json

import pytest

from er_commons import adequacy_binary_development as loader
from er_commons.artifact_io import json_bytes


def save(path, value):
    """Write one fixture artifact in the published format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def lines(path, rows):
    """Write ordered JSONL without a production artifact dependency."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(json_bytes(row) for row in rows))


def seal(root):
    """Produce a valid local fixture seal with exact closure."""
    inventory = [
        {**loader._binding(p), "path": p.relative_to(root).as_posix()}
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.name != "completion.json"
    ]
    save(root / "completion.json", {"dataset_id": root.name, "inventory": inventory})
    return loader._binding(root / "completion.json")


@pytest.fixture
def published(tmp_path, monkeypatch):
    """Provide two allowlisted cases with generated examples and disclosed excluded slots."""
    monkeypatch.setattr(loader, "DEVELOPMENT_CASE_IDS", frozenset({"C001", "C051"}))
    monkeypatch.setattr(loader, "EXPECTED_COUNTS", {"C": 2, "S": 2})
    monkeypatch.setattr(loader, "CALIBRATION_COUNTS", {"C": 1, "S": 1})
    data = tmp_path / "data"
    repo = tmp_path / "repo"
    base = data / "pipelines/brisbane_baylands/task_09"
    calibration = base / loader.CALIBRATION
    roots = {c: base / loader.DATASETS[c] for c in ("C", "S")}
    payloads = {}
    ids = {}
    for component, root in roots.items():
        provenance = []
        labels = []
        coverage = []
        inputs = []
        for i, case in enumerate(("C001", "C051"), 1):
            sid = f"{case}-BASE" if component == "C" else f"S{i:04}"
            packet = {
                "question": f"Can snapshot {i} restore the file?",
                "candidate_conclusion": "No.",
            }
            if component == "C":
                packet["reference_conclusion"] = "No."
                provenance.append(
                    {
                        "candidate_id": sid,
                        "case_id": case,
                        "payload_line": i,
                        "payload_sha256": __import__("hashlib")
                        .sha256(json_bytes(packet))
                        .hexdigest(),
                        "source_reference": {"path": str(tmp_path / "RESERVED_DO_NOT_READ")},
                    }
                )
                labels.append(
                    {
                        "candidate_id": sid,
                        "case_id": case,
                        "expected_label": "yes",
                        "label_status": "proposal",
                        "types": ["BASE"],
                    }
                )
                coverage.append(
                    {"candidate_id": sid, "case_id": case, "type": "BASE", "status": "generated"}
                )
            else:
                packet.update(
                    candidate_supporting_points=[{"point_id": "P1", "text": "The file is newer."}],
                    candidate_qualifications=[
                        {
                            "point_id": "Q1",
                            "text": "Only this snapshot.",
                            "applies_to": ["conclusion"],
                        }
                    ],
                )
                save(root / f"candidate_inputs/{sid}.json", packet)
                save(root / f"conditions/no_reference/{sid}.json", packet)
                provenance.append(
                    {
                        "example_id": sid,
                        "case_id": case,
                        "candidate_path": f"candidate_inputs/{sid}.json",
                        "candidate_sha256": loader._binding(root / f"candidate_inputs/{sid}.json")[
                            "sha256"
                        ],
                        "no_reference_path": f"conditions/no_reference/{sid}.json",
                        "review_accepted": True,
                        "paired_eligible": case != "C051",
                        "origin_slot": "BASE",
                    }
                )
                labels.append(
                    {
                        "example_id": sid,
                        "expected_label": "yes",
                        "label_status": "proposal",
                        "review_accepted": True,
                        "paired_eligible": case != "C051",
                    }
                )
                coverage.append(
                    {"example_id": sid, "case_id": case, "slot": "BASE", "disposition": "generated"}
                )
            inputs.append(packet)
        coverage.append(
            {
                "case_id": "C051",
                "type" if component == "C" else "slot": "UNRESOLVED",
                "status" if component == "C" else "disposition": "unresolved",
            }
        )
        lines(root / "coverage.jsonl", coverage)
        lines(
            root / ("provenance.jsonl" if component == "C" else "candidate_manifest.jsonl"),
            provenance,
        )
        lines(
            root / ("proposed_labels.jsonl" if component == "C" else "expected_labels.jsonl"),
            labels,
        )
        if component == "C":
            lines(root / "judge_inputs.jsonl", inputs)
        name = "conclusion" if component == "C" else "support"
        save(
            repo / f"docs/specs/task09f_{name}_synthesis_result.json",
            {
                "dataset_id": root.name,
                "artifact_root": str(root),
                "reference_holds": ["C051"] if component == "S" else [],
                "artifacts": {"completion": seal(root)},
            },
        )
        part = calibration / name
        key = "candidate_id" if component == "C" else "example_id"
        projection = dict(inputs[0])
        if component == "S":
            projection["candidate_qualifications"] = ["Only this snapshot."]
        lines(part / "judge_inputs.jsonl", [projection])
        lines(part / "provenance.jsonl", [{key: provenance[0][key]}])
        lines(
            part / "proposed_labels.jsonl",
            [
                {key: provenance[0][key], "expected_label": "yes"}
                if component == "C"
                else {key: provenance[0][key], "expected_support_sufficient": True}
            ],
        )
        payloads[component] = inputs
        ids[component] = [p[key] for p in provenance]
    completion = seal(calibration)
    completion["path"] = str((calibration / "completion.json").relative_to(data))
    save(
        repo / "docs/specs/task09f_binary_calibration_result.json",
        {"artifact_root_relative": str(calibration.relative_to(data)), "completion": completion},
    )
    return data, repo, roots, payloads, ids


def test_full_inputs_separate_labels_and_preserve_blind_reference_hold(published):
    """C stays exact; S drops only qualification metadata, including held-reference cases."""
    data, repo, _, payloads, ids = published
    for component in ("C", "S"):
        samples, labels, metadata = loader.load_full_development(
            component, data_root=data, repo_root=repo
        )
        assert set(labels) == set(ids[component]) and all(labels.values())
        assert all(set(s) == {"sample_id", "case_id", "scope", "packet"} for s in samples)
        assert metadata["counts"]["calibration_seen"] == 1
        assert len(metadata["excluded_slots"]) == 1
        assert metadata["examples"][ids[component][1]]["calibration_seen"] is False
        if component == "C":
            assert [s["packet"] for s in samples] == payloads["C"]
        else:
            assert samples[1]["packet"]["candidate_qualifications"] == ["Only this snapshot."]
            assert metadata["examples"][ids["S"][1]]["paired_eligible"] is False
            assert metadata["reference_holds"] == ["C051"]
            assert "applies_to" not in json.dumps(samples)


def test_corruption_and_extra_files_rejected(published):
    """Neither changed bytes nor unsealed additions can enter the published inventory."""
    data, repo, roots, _, _ = published
    (roots["C"] / "unsealed.json").write_text("{}")
    with pytest.raises(ValueError, match="closure"):
        loader.load_full_development("C", data_root=data, repo_root=repo)
    (roots["C"] / "unsealed.json").unlink()
    (roots["C"] / "judge_inputs.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="checksum"):
        loader.load_full_development("C", data_root=data, repo_root=repo)


def test_path_escape_rejected_before_read(tmp_path):
    """References outside the sealed namespace cannot redirect the loader to test data."""
    with pytest.raises(ValueError, match="escapes"):
        loader._within(tmp_path / "allowed", "../reserved.json")


def test_unresolved_slots_and_duplicate_coverage_rejected():
    """An excluded slot must not carry an eligible example ID."""
    row = {"case_id": "C051", "slot": "BASE", "disposition": "unresolved", "example_id": "S0001"}
    with pytest.raises(ValueError, match="Excluded"):
        loader._coverage([row], "S")
    row = {"case_id": "C051", "slot": "BASE", "disposition": "generated", "example_id": "S0001"}
    with pytest.raises(ValueError, match="repeats"):
        loader._coverage([row, row], "S")


def test_calibration_label_drift_rejected_even_with_valid_reseal(published):
    """A valid artifact seal cannot hide changed calibration labels from overlap checks."""
    data, repo, _, _, ids = published
    root = data / "pipelines/brisbane_baylands/task_09" / loader.CALIBRATION
    lines(
        root / "conclusion/proposed_labels.jsonl",
        [{"candidate_id": ids["C"][0], "expected_label": "no"}],
    )
    completion = seal(root)
    completion["path"] = str((root / "completion.json").relative_to(data))
    save(
        repo / "docs/specs/task09f_binary_calibration_result.json",
        {"artifact_root_relative": str(root.relative_to(data)), "completion": completion},
    )
    with pytest.raises(ValueError, match="accepted calibration"):
        loader.load_full_development("C", data_root=data, repo_root=repo)


def test_provenance_corruption_rejected_after_valid_reseal(published):
    """Payload identity is bound independently of the surrounding inventory seal."""
    data, repo, roots, _, _ = published
    root = roots["C"]
    rows = loader._rows(root / "provenance.jsonl")
    rows[0]["payload_sha256"] = "0" * 64
    lines(root / "provenance.jsonl", rows)
    pointer_path = repo / "docs/specs/task09f_conclusion_synthesis_result.json"
    pointer = loader._json(pointer_path)
    pointer["artifacts"]["completion"] = seal(root)
    save(pointer_path, pointer)
    with pytest.raises(ValueError, match="provenance differs"):
        loader.load_full_development("C", data_root=data, repo_root=repo)


def test_coverage_rejects_nonallowlisted_case():
    """No current test or reserved question can be introduced by a new coverage row."""
    with pytest.raises(ValueError, match="development boundary"):
        loader._coverage(
            [
                {
                    "case_id": "C999",
                    "type": "BASE",
                    "status": "generated",
                    "candidate_id": "C999-BASE",
                }
            ],
            "C",
        )
