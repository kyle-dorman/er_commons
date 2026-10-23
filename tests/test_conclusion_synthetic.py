"""Offline publication fixtures test isolation and identity, not semantic judging."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.adequacy_binary import (
    CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION,
    output_json_schema,
    system_prompt,
)
from er_commons.adequacy_binary_development import DEVELOPMENT_CASE_IDS
from er_commons.artifact_io import file_reference, json_bytes, jsonl_bytes, stable_json_sha256
from er_commons.conclusion_synthetic import load_publication


def seal(root: Path, pointer: Path) -> None:
    """Rebind fixture bytes so semantic-invalid artifacts reach structural checks."""
    inventory = [
        file_reference(path, root=root)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "completion.json"
    ]
    dataset = "task15-c-test-fixture"
    (root / "completion.json").write_bytes(
        json_bytes({"dataset_id": dataset, "inventory": inventory})
    )
    pointer.write_bytes(
        json_bytes(
            {
                "schema_version": "task15.c_synthetic_result.v1",
                "dataset_id": dataset,
                "artifact_root_relative": "pipelines/brisbane_baylands/task_15/fixture",
                "completion": file_reference(root / "completion.json", root=root),
            }
        )
    )


@pytest.fixture
def publication(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Build structural placeholders, never an authored semantic evaluation suite."""
    root = tmp_path / "pipelines/brisbane_baylands/task_15/fixture"
    root.mkdir(parents=True)
    pointer = tmp_path / "result.json"
    catalog = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs/specs/task15b_conclusion_synthetic_catalog_v1.json"
        ).read_text()
    )
    (root / "catalog.json").write_bytes(json_bytes(catalog))
    artifacts: dict[str, list[dict[str, Any]]] = {
        name: []
        for name in [
            "authoring_inputs",
            "judge_inputs",
            "provenance",
            "proposed_labels",
            "coverage",
            "reviews",
        ]
    }
    for number, case in enumerate(sorted(DEVELOPMENT_CASE_IDS), start=1):
        sid = f"fixture-{case}"
        reference = f"Structural placeholder {case}."
        partition = "audit" if case in catalog["partitions"]["audit"] else "tuning"
        packet = {
            "question": f"Fixture {case}?",
            "candidate_conclusion": reference,
            "reference_conclusion": reference,
        }
        artifacts["authoring_inputs"].append(
            {
                "case_id": case,
                "question": packet["question"],
                "reference_conclusion": reference,
                "partition": partition,
            }
        )
        artifacts["judge_inputs"].append(packet)
        artifacts["provenance"].append(
            {
                "candidate_id": sid,
                "case_id": case,
                "partition": partition,
                "line_number": number,
                "input_sha256": stable_json_sha256(packet),
                "slots": ["BASE"],
            }
        )
        artifacts["proposed_labels"].append(
            {
                "candidate_id": sid,
                "expected_label": True,
                "review_disposition": "accepted",
                "author": "author",
                "reviewer": "reviewer",
                "rationale": "Fixture only.",
            }
        )
        for slot in catalog["slots"]:
            base = slot["slot"] == "BASE"
            artifacts["coverage"].append(
                {
                    "case_id": case,
                    "slot": slot["slot"],
                    "status": "generated" if base else "inapplicable",
                    "candidate_id": sid if base else None,
                    "rationale": "Fixture only.",
                }
            )
            artifacts["reviews"].append(
                {
                    "case_id": case,
                    "slot": slot["slot"],
                    "disposition": "accepted",
                    "author": "author",
                    "reviewer": "reviewer",
                    "rationale": "Fixture only.",
                    "expected_label": True if base else None,
                    "candidate_sha256": hashlib.sha256(reference.encode()).hexdigest()
                    if base
                    else None,
                }
            )
    for name, rows in artifacts.items():
        (root / f"{name}.jsonl").write_bytes(jsonl_bytes(rows))
    (root / "input_bindings.json").write_bytes(
        json_bytes(
            {
                "development_only_files_read": [
                    {
                        "case_id": row["case_id"],
                        "question_sha256": hashlib.sha256(row["question"].encode()).hexdigest(),
                        "reference_sha256": hashlib.sha256(
                            row["reference_conclusion"].encode()
                        ).hexdigest(),
                    }
                    for row in artifacts["authoring_inputs"]
                ]
            }
        )
    )
    (root / "policy.md").write_text("Structural fixture policy.\n")
    (root / "prompt").mkdir()
    version = CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION
    prompt = system_prompt("C", prompt_version=version)
    schema = output_json_schema("C", prompt_version=version)
    (root / "prompt/prompt.txt").write_text(prompt)
    (root / "prompt/schema.json").write_bytes(json_bytes(schema))
    (root / "prompt/manifest.json").write_bytes(
        json_bytes(
            {
                "prompt_version": version,
                "prompt_sha256": stable_json_sha256(prompt),
                "schema_sha256": stable_json_sha256(schema),
            }
        )
    )
    (root / "manifest.json").write_bytes(
        json_bytes(
            {
                "dataset_id": "task15-c-test-fixture",
                "sample_count": 19,
                "prompt_version": CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION,
                "label_status": "agent_proposed_independently_reviewed_not_human_gold",
                "policy_sha256": hashlib.sha256((root / "policy.md").read_bytes()).hexdigest(),
                "catalog_sha256": hashlib.sha256((root / "catalog.json").read_bytes()).hexdigest(),
            }
        )
    )
    seal(root, pointer)
    return tmp_path, root, pointer


def test_explicit_partition_and_label_isolation(publication: tuple[Path, Path, Path]) -> None:
    """Partition selection keeps related variants together and labels outside packets."""
    data_root, _, pointer = publication
    tuning, labels, meta = load_publication(pointer, data_root=data_root, partition="tuning")
    audit, _, _ = load_publication(pointer, data_root=data_root, partition="audit")
    assert len(tuning) == 15 and len(audit) == 4
    assert set(labels) == {row["sample_id"] for row in tuning}
    assert not {r["case_id"] for r in tuning} & {r["case_id"] for r in audit}
    assert all(
        set(r["packet"]) == {"question", "candidate_conclusion", "reference_conclusion"}
        for r in tuning + audit
    )
    assert meta["publication_sample_count"] == 19
    assert load_publication(pointer, data_root=data_root, partition="tuning")[0] == tuning


def test_tamper_rejected_before_parse(publication: tuple[Path, Path, Path]) -> None:
    """Unsealed payload changes cannot silently acquire existing expectations."""
    data_root, root, pointer = publication
    (root / "judge_inputs.jsonl").write_text("tampered")
    with pytest.raises(ValueError, match="binding differs"):
        load_publication(pointer, data_root=data_root, partition="all")


@pytest.mark.parametrize(
    "defect", ["reviewer", "review_hash", "label", "leakage", "coverage", "partition"]
)
def test_invalid_publication_rejected(publication: tuple[Path, Path, Path], defect: str) -> None:
    """A valid seal alone cannot approve leakage, broken joins or unreviewed labels."""
    data_root, root, pointer = publication
    file = {
        "reviewer": "proposed_labels",
        "review_hash": "reviews",
        "label": "proposed_labels",
        "leakage": "judge_inputs",
        "coverage": "coverage",
        "partition": "provenance",
    }[defect]
    path = root / f"{file}.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if defect == "reviewer":
        rows[0]["reviewer"] = rows[0]["author"]
    if defect == "review_hash":
        rows[0]["candidate_sha256"] = "wrong"
    if defect == "label":
        rows[0]["expected_label"] = "true"
    if defect == "leakage":
        rows[0]["expected_label"] = True
    if defect == "coverage":
        rows.pop()
    if defect == "partition":
        rows[0]["partition"] = "audit"
    path.write_bytes(jsonl_bytes(rows))
    seal(root, pointer)
    with pytest.raises(ValueError):
        load_publication(pointer, data_root=data_root, partition="all")


def test_external_path_rejected(publication: tuple[Path, Path, Path]) -> None:
    """A pointer cannot redirect the loader into historical or reserved directories."""
    data_root, _, pointer = publication
    content = json.loads(pointer.read_text())
    content["artifact_root_relative"] = "pipelines/brisbane_baylands/task_15/../../restricted"
    pointer.write_bytes(json_bytes(content))
    with pytest.raises(ValueError, match="escapes root"):
        load_publication(pointer, data_root=data_root, partition="all")


@pytest.mark.parametrize(
    "defect", ["excluded_review", "false_baseline", "source_hash", "audit", "prompt"]
)
def test_review_and_predeclared_bindings(publication: tuple[Path, Path, Path], defect: str) -> None:
    """Resealing cannot excuse invalid review, baseline or predeclared input identities."""
    data_root, root, pointer = publication
    if defect in {"excluded_review", "false_baseline"}:
        path = root / "reviews.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if defect == "excluded_review":
            rows[1].update(reviewer="author", rationale="", disposition="revise")
        else:
            rows[0]["expected_label"] = False
            labels_path = root / "proposed_labels.jsonl"
            labels = [json.loads(line) for line in labels_path.read_text().splitlines()]
            labels[0]["expected_label"] = False
            labels_path.write_bytes(jsonl_bytes(labels))
        path.write_bytes(jsonl_bytes(rows))
    elif defect == "source_hash":
        path = root / "input_bindings.json"
        bindings = json.loads(path.read_text())
        bindings["development_only_files_read"][0]["reference_sha256"] = "wrong"
        path.write_bytes(json_bytes(bindings))
    elif defect == "audit":
        path = root / "catalog.json"
        catalog = json.loads(path.read_text())
        catalog["partitions"]["audit"] = ["C001", "C006", "C007", "C008"]
        path.write_bytes(json_bytes(catalog))
        manifest_path = root / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["catalog_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_bytes(json_bytes(manifest))
    else:
        (root / "prompt/prompt.txt").write_text("Wrong rubric.")
    seal(root, pointer)
    with pytest.raises(ValueError):
        load_publication(pointer, data_root=data_root, partition="all")
