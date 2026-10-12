"""Exercise fresh development authoring through publication using invented evidence only."""

import json
from pathlib import Path

import pytest
from test_synthetic_stage_expectations import fixture

from er_commons import synthetic_batch as batch
from er_commons import synthetic_publication as publication
from er_commons.artifact_io import artifact_inventory, file_reference
from er_commons.synthetic_records import SPEC_ROOT
from er_commons.synthetic_stage_expectations import ANNOTATION_VERSION


@pytest.fixture
def staged_run(tmp_path: Path) -> tuple[Path, Path]:
    """Prepare and author one fresh slot without reading any predecessor answer."""
    proposal, packet = fixture()
    proposal["case_id"] = packet["case_id"] = "C001"
    packet["reference_answer"]["conclusion"]["text"] = "Available water is limited."
    root = tmp_path / "fresh"
    batch.prepare(
        root,
        {
            "annotation_version": ANNOTATION_VERSION,
            "cases": [packet],
            "dev_case_ids": ["C001"],
            "source_bindings": {},
            "restricted_controls": [],
            "limitations": [],
            "regeneration": {
                "development_slot_ids": ["metadata-only-slot"],
                "preserved_final_check_variant_ids": ["untouched-reserved-id"],
                "preserved_excluded_variant_ids": ["untouched-excluded-id"],
                "predecessor_reservation": {"path": "metadata-only", "sha256": "fixture"},
            },
        },
        SPEC_ROOT,
        smoke=True,
    )

    def execute(arguments: list[str], prompt: str, attempt: Path) -> int:
        """Save a complete source-linked proposal in place of a real invocation."""
        assert "untouched-reserved-id" not in prompt
        assert "untouched-excluded-id" not in prompt
        assert "point_expectations" in prompt
        (attempt / "stdout.jsonl").write_text('{"type":"thread.started"}\n')
        (attempt / "stderr.txt").write_text("")
        batch.save(attempt / "raw_output.json", proposal)
        return 0

    result = batch.run(root, executor=execute)
    assert result[0]["status"] == "validated", result
    raw = root / result[0]["attempt"] / "raw_output.json"
    review = tmp_path / "review.json"
    batch.save(
        review,
        {
            "status": "passed",
            "configuration_id": batch.read(root / "prepared.json")["configuration_id"],
            "reviewed_outputs": [file_reference(raw, root=root)],
            "exclusions": [],
        },
    )
    return root, review


def test_fresh_stage_annotations_publish_without_new_reservations(
    staged_run: tuple[Path, Path],
) -> None:
    """Check inherited boundaries, exact slot binding, label separation and immutable closure."""
    root, review = staged_run
    before = artifact_inventory(root, set())

    def forbidden(arguments: list[str], prompt: str, attempt: Path) -> int:
        """Completed units must resume without a new model call."""
        raise AssertionError("Unexpected invocation during completed-unit replay")

    assert batch.run(root, executor=forbidden)[0]["status"] == "validated"
    assert artifact_inventory(root, set()) == before
    summary = publication.publish(root, review)
    assert summary["variant_count"] == 1
    assert summary["point_expectation_count"] == 1
    assert summary["reserved_final_checks"] == 0
    assert summary["preserved_external_final_checks"] == 1
    assert summary["annotation_version"] == ANNOTATION_VERSION
    answer = json.loads((root / "published/answers.jsonl").read_text())
    expectation = json.loads((root / "published/expectations.jsonl").read_text())
    slots = json.loads((root / "published/development_slots.jsonl").read_text())
    reservation = batch.read(root / "published/reservation.json")
    assert answer["variant_id"] == expectation["variant_id"] == slots["variant_id"]
    assert answer["variant_id"].startswith("task09a2-")
    assert slots["predecessor_development_variant_id"] == "metadata-only-slot"
    assert expectation["predecessor_development_variant_id"] == "metadata-only-slot"
    assert expectation["grounding"]["point_expectations"][0]["supported"] is True
    assert "grounding" not in answer and "point_expectations" not in answer["answer"]
    assert reservation["final_check_variant_ids"] == []
    assert reservation["development_variant_ids"] == [answer["variant_id"]]
    assert reservation["preserved_external_final_check_variant_ids"] == ["untouched-reserved-id"]
    assert reservation["preserved_external_excluded_variant_ids"] == ["untouched-excluded-id"]
    assert publication.verify(root)["valid"]
    with pytest.raises(ValueError, match="immutable"):
        publication.publish(root, review)
    assert publication.verify(root)["valid"]


@pytest.mark.parametrize("relative", ["output_schema.json", "config.json"])
def test_fresh_schema_and_configuration_drift_blocks_replay(
    staged_run: tuple[Path, Path], relative: str
) -> None:
    """Changed prepared bytes cannot be reused or published despite a prior successful unit."""
    root, review = staged_run
    path = root / relative
    path.write_text(path.read_text() + " ")
    with pytest.raises(ValueError, match="changed|checksum"):
        batch.run(root)
    with pytest.raises(ValueError, match="changed|checksum"):
        publication.publish(root, review)
    assert not (root / "published").exists()
