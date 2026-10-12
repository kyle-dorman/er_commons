"""Verify untouched reservations and publication against real record materialization."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from test_synthetic_records import fixture

from er_commons import synthetic_batch as batch
from er_commons import synthetic_publication as publication
from er_commons import synthetic_records
from er_commons.artifact_io import file_reference


def test_reservation_is_deterministic_and_excludes_unusable() -> None:
    """Input ordering cannot change reservations or promote ambiguous/duplicate variants."""
    rows: list[dict[str, Any]] = [
        {
            "variant_id": f"v{i}",
            "perturbation_id": "F01",
            "verification_status": "model_verified",
            "grounding": {"score": i % 3},
            "adequacy": {"score": 1},
        }
        for i in range(12)
    ]
    rows[0]["verification_status"] = "unresolved"
    rows[1]["duplicate"] = True
    rows[2]["judge_exposed"] = True
    first = publication.reserve(rows, seed="fixed")
    assert first == publication.reserve(list(reversed(rows)), seed="fixed")
    assert set(first["excluded_variant_ids"]) == {"v0", "v1"}
    assert "v2" not in first["final_check_variant_ids"]
    assert "v2" in first["development_variant_ids"]
    assert len(first["final_check_variant_ids"]) == 2
    assert first["judge_exposures_before_reservation"] == 1
    assert set(first["final_check_variant_ids"]).isdisjoint(first["development_variant_ids"])
    assert set(
        first["final_check_variant_ids"]
        + first["development_variant_ids"]
        + first["excluded_variant_ids"]
    ) == {f"v{i}" for i in range(12)}
    with pytest.raises(ValueError, match="Duplicate"):
        publication.reserve(rows + [rows[0]], seed="fixed")


@pytest.fixture
def authored(tmp_path: Path, request: pytest.FixtureRequest) -> tuple[Path, Path]:
    """Run a source-free smoke fixture through the real validator and recording path."""
    proposal, packet = fixture()
    proposal["case_id"] = packet["case_id"] = "C001"
    if not getattr(request, "param", False):
        packet["reference_answer"]["conclusion"]["text"] = "The available water is limited."
    # Smoke preparation requests these four categories; unsupported fixture categories are explicit.
    proposal["coverage"].extend(
        {
            "perturbation_id": category,
            "disposition": "inapplicable",
            "reason": "Fixture does not model this category.",
        }
        for category in ["O01", "F03", "C05"]
    )
    root = tmp_path / "run"
    batch.prepare(
        root,
        {
            "cases": [packet],
            "dev_case_ids": ["C001"],
            "source_bindings": {},
            "restricted_controls": [],
            "limitations": [],
        },
        synthetic_records.SPEC_ROOT,
        smoke=True,
    )

    def execute(arguments: list[str], prompt: str, attempt: Path) -> int:
        """Write a complete deterministic response without invoking a model."""
        (attempt / "stdout.jsonl").write_text('{"type":"thread.started"}\n')
        (attempt / "stderr.txt").write_text("")
        batch.save(attempt / "raw_output.json", proposal)
        return 0

    result = batch.run(root, executor=execute)
    assert result[0]["status"] == "validated"
    raw = root / result[0]["attempt"] / "raw_output.json"
    review = tmp_path / "review.json"
    batch.save(
        review,
        {
            "status": "passed",
            "configuration_id": batch.read(root / "prepared.json")["configuration_id"],
            "reviewed_outputs": [file_reference(raw, root=root)],
        },
    )
    return root, review


def test_publish_seal_roundtrip_and_tamper(authored: tuple[Path, Path]) -> None:
    """Publication uses full validation, preserves records, and rejects post-seal mutation."""
    root, review = authored
    summary = publication.publish(root, review)
    assert summary["case_count"] == 1 and summary["variant_count"] == 1
    assert summary["coverage_rows"] == 4 and summary["reserved_final_checks"] == 1
    assert publication.verify(root)["valid"]
    assert (root / "published/publication_source.py").is_file()
    answer = root / "published/answers.jsonl"
    answer.write_text(answer.read_text() + " ")
    with pytest.raises(ValueError, match="inventory"):
        publication.verify(root)


@pytest.mark.parametrize("field", ["configuration_id", "reviewed_outputs"])
def test_review_must_bind_actual_outputs(authored: tuple[Path, Path], field: str) -> None:
    """A passed review for a different configuration or output cannot authorize publication."""
    root, review = authored
    record = copy.deepcopy(batch.read(review))
    record[field] = "wrong" if field == "configuration_id" else []
    review.write_text(__import__("json").dumps(record))
    with pytest.raises(ValueError, match="review"):
        publication.publish(root, review)
    assert not (root / "completion.json").exists()
    assert not (root / "published").exists()


@pytest.mark.parametrize("authored", [True], indirect=True)
def test_control_duplicate_excluded_from_comparison_and_reservation(
    authored: tuple[Path, Path],
) -> None:
    """Exact copies of the unchanged control are retained but never count as new challenges."""
    root, review = authored
    summary = publication.publish(root, review)
    assert summary["variant_count"] == 1
    assert summary["duplicate_variants"] == 1
    assert summary["comparison_eligible_variants"] == 0
    assert summary["reserved_final_checks"] == 0
    reservation = batch.read(root / "published/reservation.json")
    assert len(reservation["excluded_variant_ids"]) == 1
    assert reservation["development_variant_ids"] == []


def test_failed_case_keeps_unchanged_control(tmp_path: Path) -> None:
    """A failed model job loses generated coverage, never its unchanged reference control."""
    _, packet = fixture()
    packet["case_id"] = "C001"
    root = tmp_path / "failed"
    batch.prepare(
        root,
        {
            "cases": [packet],
            "dev_case_ids": ["C001"],
            "source_bindings": {},
            "restricted_controls": [],
            "limitations": [],
        },
        synthetic_records.SPEC_ROOT,
        smoke=True,
    )

    def fail(arguments: list[str], prompt: str, attempt: Path) -> int:
        """Simulate exhausted transport failures without model execution."""
        return 1

    result = batch.run(root, executor=fail, sleeper=lambda _: None)
    assert result[0]["status"] == "failed"
    review = tmp_path / "failed_review.json"
    batch.save(
        review,
        {
            "status": "passed",
            "configuration_id": batch.read(root / "prepared.json")["configuration_id"],
            "reviewed_outputs": [],
        },
    )
    summary = publication.publish(root, review)
    assert summary["failed_cases"] == ["C001"]
    assert summary["variant_count"] == 0 and summary["control_count"] == 1
    control = json.loads((root / "published/controls.jsonl").read_text())
    assert control["answer"] == packet["reference_answer"]
    assert control["provenance"]["model"] is None
    assert control["provenance"]["invocation"] is None
    assert publication.verify(root)["valid"]


def test_review_exclusion_preserves_scores_and_raw(authored: tuple[Path, Path]) -> None:
    """Independent uncertainty excludes a proposal without rewriting author judgments."""
    root, review = authored
    record = batch.read(review)
    raw_path = root / record["reviewed_outputs"][0]["path"]
    raw_before = raw_path.read_bytes()
    original = batch.read(raw_path)["variants"][0]["expectation"]
    record["exclusions"] = [
        {
            "case_id": "C001",
            "variant_index": 0,
            "reason": "Alternative premise needs more evidence.",
        }
    ]
    review.write_text(json.dumps(record))
    summary = publication.publish(root, review)
    assert summary["reviewed_uncertain_variants"] == 1
    coverage = json.loads((root / "published" / "coverage.jsonl").read_text().splitlines()[0])
    assert coverage["model_disposition"] == "generated"
    assert coverage["disposition"] == "ambiguous"
    assert coverage["comparison_eligible_variant_count"] == 0
    assert summary["comparison_eligible_variants"] == summary["reserved_final_checks"] == 0
    saved = json.loads((root / "published/expectations.jsonl").read_text())
    assert saved["grounding"] == original["grounding"]
    assert saved["adequacy"] == original["adequacy"]
    assert saved["verification_status"] == original["verification_status"]
    assert saved["review_exclusion_reason"] == record["exclusions"][0]["reason"]
    assert raw_path.read_bytes() == raw_before
    reservation = batch.read(root / "published/reservation.json")
    assert reservation["excluded_variant_ids"] == [saved["variant_id"]]
    assert reservation["development_variant_ids"] == []


@pytest.mark.parametrize(
    "exclusion",
    [
        {"case_id": "C001", "variant_index": 99, "reason": "Not present."},
        {"case_id": "C001", "variant_index": 0, "reason": " "},
        {"case_id": "C001", "variant_index": True, "reason": "Bad type."},
        {"case_id": "C999", "variant_index": 0, "reason": "Wrong case."},
    ],
)
def test_invalid_exclusions_fail_before_publication(
    authored: tuple[Path, Path],
    exclusion: dict[str, Any],
) -> None:
    """Every exclusion must name a real variant and explain uncertainty."""
    root, review = authored
    record = batch.read(review)
    record["exclusions"] = [exclusion]
    review.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="exclusion"):
        publication.publish(root, review)
    assert not (root / "published").exists()


def test_inherited_partition_preserves_external_reservation(tmp_path: Path) -> None:
    """Fresh IDs stay development-only; skipped slots and external reservations remain explicit."""
    batch.save(tmp_path / "config.json", {"smoke": False})
    batch.save(
        tmp_path / "cases/C001/input.json",
        {"regeneration_slots": {"P01": "old-dev-1", "P02": "old-dev-2"}},
    )
    inherited = {
        "development_slot_ids": ["old-dev-1", "old-dev-2"],
        "preserved_final_check_variant_ids": ["old-reserved"],
        "preserved_excluded_variant_ids": ["old-excluded"],
        "predecessor_reservation": {"path": "metadata-only", "sha256": "fixed"},
    }
    records = [
        {
            "variant_id": "new-id",
            "case_id": "C001",
            "perturbation_id": "P01",
            "predecessor_development_variant_id": "old-dev-1",
            "comparison_eligible": True,
        }
    ]
    coverage = [
        {
            "case_id": "C001",
            "perturbation_id": c,
            "disposition": d,
            "reason": "Explicit disposition",
        }
        for c, d in [("P01", "generated"), ("P02", "inapplicable")]
    ]
    reservation, slots = publication.inherited_partition(tmp_path, records, coverage, inherited)
    assert reservation["final_check_variant_ids"] == []
    assert reservation["preserved_external_final_check_variant_ids"] == ["old-reserved"]
    assert reservation["development_variant_ids"] == ["new-id"]
    assert slots[1]["variant_id"] is None
    with pytest.raises(ValueError, match="Incomplete"):
        publication.inherited_partition(tmp_path, records, coverage[:1], inherited)
    records[0]["predecessor_development_variant_id"] = "old-reserved"
    with pytest.raises(ValueError, match="Absent"):
        publication.inherited_partition(tmp_path, records, coverage, inherited)
