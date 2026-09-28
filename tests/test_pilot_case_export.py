"""Publication safeguards and narrowly bound human review dispositions."""

import copy
from pathlib import Path

import pytest
from test_pilot_evidence import annotation, prepared  # noqa: F401

from er_commons import pilot_case_export as exporter
from er_commons import pilot_evidence as evidence


def seal(root: Path) -> str:
    """Pin the exact test directory contents in the same format as real releases."""
    exporter.write_json(
        root / "manifest.json",
        {
            "managed_files": [
                {"path": str(path.relative_to(root)), "sha256": exporter.file_hash(path)}
                for path in sorted(root.rglob("*"))
                if path.is_file()
            ]
        },
    )
    return exporter.file_hash(root / "manifest.json")


def inputs(root: Path, *, warnings=(), recorded_errors=None, claim_count=0):
    """Describe explicit dispositions without inventing accepted claim/source labels."""
    return exporter.ExportInputs(
        data_root=root,
        review_root=root / "reviews",
        disposition_root=root / "dispositions",
        disposition={
            "task164_correction": {"annotation_id": 999},
            "accepted_mvp_consistency_warnings": [{"task_id": task} for task in warnings],
            "claim_count_retained": claim_count,
        },
        accepted_cases={},
        recorded_errors=recorded_errors or {},
        input_bindings={},
    )


@pytest.mark.parametrize("mutation", ["extra", "missing", "changed", "manifest"])
def test_sealed_manifest_detects_tampering(tmp_path, mutation):
    payload = tmp_path / "payload.json"
    payload.write_text('{"review": "original"}')
    expected_hash = seal(tmp_path)
    exporter.verify_manifest(tmp_path, expected_hash)
    if mutation == "extra":
        (tmp_path / "extra.json").write_text("{}")
    elif mutation == "missing":
        payload.unlink()
    elif mutation == "changed":
        payload.write_text('{"review": "altered"}')
    else:
        (tmp_path / "manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="mismatch"):
        exporter.verify_manifest(tmp_path, expected_hash)


def test_manifest_rejects_symlink_escape_even_with_matching_hash(tmp_path):
    root = tmp_path / "release"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    (root / "linked.json").symlink_to(outside)
    expected_hash = seal(root)
    with pytest.raises(ValueError, match="escapes"):
        exporter.verify_manifest(root, expected_hash)


@pytest.mark.parametrize("relative", ["../outside", "/absolute/path"])
def test_bound_paths_cannot_escape(tmp_path, relative):
    with pytest.raises(ValueError, match="escapes"):
        exporter.bound_path(tmp_path, relative)


def correction_task():
    """Two candidates distinguish source identity from an arbitrary field number."""
    task = {
        "data": {"claim_id": "claim", "slots": [{"slot": "c001", "candidate_ids": ["a", "b"]}]},
        "annotations": [annotation(c001_p01_label="partial", c001_p02_label="supports")],
    }
    correction = {
        "annotation_id": 1,
        "claim_id": "claim",
        "candidate_id": "a",
        "field": "c001_p01_label",
        "original": "partial",
        "effective": "context",
    }
    return task, correction


def test_clarification_changes_only_a_copy_of_bound_source_label():
    task, correction = correction_task()
    original = copy.deepcopy(task)
    effective = exporter.clarified_annotation(task, correction)
    assert task == original
    assert effective["result"][0]["value"]["choices"] == ["context"]
    assert effective["result"][1] == original["annotations"][0]["result"][1]


@pytest.mark.parametrize(
    "field,value",
    [
        ("annotation_id", 2),
        ("claim_id", "wrong"),
        ("candidate_id", "absent"),
        ("candidate_id", "b"),
        ("field", "c001_p02_label"),
        ("original", "context"),
    ],
)
def test_clarification_rejects_wrong_binding(field, value):
    task, correction = correction_task()
    correction[field] = value
    with pytest.raises(ValueError):
        exporter.clarified_annotation(task, correction)


def test_warning_acceptance_requires_exact_task_and_recorded_error(prepared):  # noqa: F811
    packet, accepted, root = prepared
    expected = evidence.prepare_claim_tasks(packet, data_root=root, approved_review=accepted)[0]
    native = annotation(c001_p01_label="context", c001_outcome="supported")
    task = {**expected, "id": 2, "annotations": [native]}
    with pytest.raises(evidence.ReviewValidationError) as caught:
        evidence.normalize_claim_review(task, native, expected_task=expected, export_lineage="test")
    original = copy.deepcopy(task)
    accepted_inputs = inputs(root, warnings=[2], recorded_errors={2: str(caught.value)})
    result = exporter.normalize_export_review(task, expected, accepted_inputs, "test")
    assert task == original
    assert result["strict_validation_passed"] is False
    assert result["claim_review"]["pairs"][0]["relationship"] == "context"
    assert result["claim_review"]["outcome"] == "supported"
    for bad_inputs in [
        inputs(root, warnings=[3], recorded_errors={2: str(caught.value)}),
        inputs(root, warnings=[2], recorded_errors={2: "different error"}),
    ]:
        with pytest.raises(evidence.ReviewValidationError):
            exporter.normalize_export_review(task, expected, bad_inputs, "test")
    task["annotations"][0]["result"].append(annotation(foreign="context")["result"][0])
    with pytest.raises(ValueError, match="foreign"):
        exporter.normalize_export_review(task, expected, accepted_inputs, "test")


def test_export_never_overwrites_existing_directory_or_file(tmp_path):
    output = tmp_path / "export"
    output.mkdir()
    marker = output / "keep.json"
    marker.write_text("original")
    with pytest.raises(FileExistsError):
        exporter.export_cases(inputs(tmp_path), output)
    with pytest.raises(FileExistsError):
        exporter.write_json(marker, {"replace": True})
    assert marker.read_text() == "original"
    assert not (output / "manifest.json").exists()


@pytest.mark.parametrize("options", [{"warnings": [2]}, {"claim_count": 1}])
def test_incomplete_publication_never_gets_completion_manifest(tmp_path, options):
    output = tmp_path / "export"
    with pytest.raises(ValueError):
        exporter.export_cases(inputs(tmp_path, **options), output)
    assert output.exists()
    assert not (output / "manifest.json").exists()
    with pytest.raises(FileExistsError):
        exporter.export_cases(inputs(tmp_path, **options), output)


@pytest.mark.parametrize("case", ["../escaped", "/absolute", "nested/case", ".."])
def test_unsafe_case_names_fail_before_creating_output(tmp_path, case):
    bound = inputs(tmp_path)
    bound.accepted_cases[case] = {}
    output = tmp_path / "export"
    with pytest.raises(ValueError, match="case"):
        exporter.export_cases(bound, output)
    assert not output.exists()


@pytest.mark.parametrize("key", ["case_label", "claim_id", "task", "task_id"])
def test_duplicate_identity_cannot_silently_replace_a_record(key):
    with pytest.raises(ValueError, match="Duplicate"):
        exporter.unique_records(
            [{key: "same", "value": "first"}, {key: "same", "value": "last"}], key
        )


def test_missing_clarification_prevents_sealing(tmp_path):
    output = tmp_path / "export"
    with pytest.raises(ValueError, match="exactly one applied user clarification"):
        exporter.export_cases(inputs(tmp_path), output)
    assert not (output / "manifest.json").exists()


@pytest.mark.parametrize("root_name", ["reviews", "dispositions"])
def test_output_cannot_mutate_a_sealed_input_release(tmp_path, root_name):
    output = tmp_path / root_name / "new_export"
    with pytest.raises(ValueError, match="inside a sealed"):
        exporter.export_cases(inputs(tmp_path), output)
    assert not output.exists()


def test_clarification_cannot_change_bound_claim_outcome(prepared):  # noqa: F811
    packet, accepted, root = prepared
    expected = evidence.prepare_claim_tasks(packet, data_root=root, approved_review=accepted)[0]
    native = annotation(c001_p01_label="partial", c001_outcome="no_support_found")
    task = {**expected, "id": 2, "annotations": [native]}
    bound = inputs(root)
    bound.disposition["task164_correction"] = {
        "annotation_id": 1,
        "claim_id": packet["claims"][0]["claim_id"],
        "candidate_id": packet["candidates"][0]["candidate_id"],
        "field": "c001_p01_label",
        "original": "partial",
        "effective": "context",
        "claim_outcome": "supported",
    }
    with pytest.raises(ValueError, match="Clarified claim outcome differs"):
        exporter.normalize_export_review(task, expected, bound, "test")


def test_late_validation_failure_keeps_partial_files_unsealed(tmp_path, monkeypatch):
    """A completed case is retained for debugging if final disposition coverage fails."""
    bound = inputs(tmp_path)
    bound.accepted_cases["case"] = {}

    def validated_case(*args):
        """Stand in for source validation; exercise only the publisher's final gate."""
        return (
            {"claims": [], "citations": [], "limitations": {"accepted_mvp_warning_tasks": []}},
            {"original_reviews": "preserved"},
            [],
        )

    monkeypatch.setattr(exporter, "build_case", validated_case)
    output = tmp_path / "export"
    with pytest.raises(ValueError, match="exactly one applied user clarification"):
        exporter.export_cases(bound, output)
    assert (output / "cases" / "case.json").is_file()
    assert (output / "audit" / "case.json").is_file()
    assert not (output / "manifest.json").exists()


def test_output_cannot_mutate_accepted_claim_handoff(tmp_path):
    """Publishing inside any accepted upstream release would break its sealed closure."""
    bound = inputs(tmp_path)
    claim_root = tmp_path / "claims" / "accepted"
    claim_root.mkdir(parents=True)
    (claim_root / "reviews.json").write_text("[]")
    manifest_hash = seal(claim_root)
    bound.input_bindings["claim_manifest"] = {
        "path": "claims/accepted/manifest.json",
        "sha256": manifest_hash,
    }
    output = claim_root / "nested" / "new_export"
    with pytest.raises(ValueError, match="inside a sealed input release"):
        exporter.export_cases(bound, output)
    assert not output.exists()
    assert not output.parent.exists()
    exporter.verify_manifest(claim_root, manifest_hash)
