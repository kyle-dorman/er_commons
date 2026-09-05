from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from er_commons.artifact_io import file_reference, json_bytes, sha256_bytes, sha256_file
from er_commons.navigation_overlay import preparation

SCHEMA_ROOT = Path(__file__).parents[1] / "benchmarks/er_bench/schemas/navigation_overlay/v1"


def test_gate_a_script_requires_an_explicit_repo_root() -> None:
    """The thin command wrapper exposes the portable checkout-root boundary."""
    script = Path(__file__).parents[1] / "scripts/prepare_task04c_gate_a.py"

    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--repo-root" in result.stdout


def test_review_inputs_reject_stale_release_freeze(tmp_path: Path) -> None:
    request = _review_fixture(tmp_path, stale_freeze=True)

    with pytest.raises(ValueError, match="stale release freeze"):
        preparation._load_and_validate_review_inputs(request)


def test_review_inputs_reject_changed_decision_hash(tmp_path: Path) -> None:
    request = _review_fixture(tmp_path, wrong_decision_hash=True)

    with pytest.raises(ValueError, match="release freeze decision checksum differs"):
        preparation._load_and_validate_review_inputs(request)


@pytest.mark.parametrize(
    ("decision_variant", "message"),
    [("duplicate", "duplicate decision"), ("missing", "accepted decision count differs")],
)
def test_review_inputs_reject_duplicate_or_missing_decision(
    tmp_path: Path, decision_variant: str, message: str
) -> None:
    request = _review_fixture(tmp_path, decision_variant=decision_variant)

    with pytest.raises(ValueError, match=message):
        preparation._load_and_validate_review_inputs(request)


def test_machine_inventory_rejects_candidate_identity_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, gate_a = _machine_fixture(tmp_path, mismatched_completion=True)
    monkeypatch.setattr(preparation, "EXPECTED_SOURCE_COUNT", 1)
    monkeypatch.setattr(preparation, "EXPECTED_CENSUS_PAGE_COUNT", 0)

    with pytest.raises(ValueError, match="candidate completion differs"):
        preparation._machine_inventory(request, gate_a)


def test_output_schema_rejects_invalid_correspondence_row() -> None:
    with pytest.raises(ValueError, match="invalid correspondence row 0"):
        preparation._validate_output_schemas(SCHEMA_ROOT, [{}], {}, {})


def test_publish_is_deterministic_no_clobber_and_detects_corruption(tmp_path: Path) -> None:
    specification = {"identity_preimage": {"policy": "fixed"}, "status": "test"}
    rows = b'{"row":1}\n'
    closure = json_bytes({"closure": 1})

    first = preparation._publish(tmp_path, "plan-test", rows, closure, specification)
    first_inventory = (first / "records/artifact_inventory.json").read_bytes()
    second = preparation._publish(tmp_path, "plan-test", rows, closure, specification)

    assert second == first
    assert (second / "records/artifact_inventory.json").read_bytes() == first_inventory
    (first / "decision_correspondence.jsonl").write_bytes(b'{"changed":true}\n')
    with pytest.raises(FileExistsError, match="changed Task 04C plan artifact"):
        preparation._publish(tmp_path, "plan-test", rows, closure, specification)


def test_explicit_mixed_page_fails_closed_without_entity_mapping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    gate_a, decisions, candidate_roots = _correspondence_fixture(tmp_path, mixed=True)
    monkeypatch.setattr(preparation, "EXPECTED_DECISION_COUNT", 1)

    rows, direct = preparation._decision_correspondence(
        gate_a, decisions, {"items": []}, candidate_roots
    )

    assert rows[0]["mapping_outcome"] == "mixed_page_insufficient_entity_evidence"
    assert rows[0]["entity_ids_by_kind"] == {"blocks": [], "tables": [], "sections": []}
    facts = next(iter(direct.values()))
    assert facts["entity_ids"] == set()
    assert not any(facts["navigation_entity_ids_by_kind"].values())


def test_ordinary_toc_page_preserves_expected_entity_correspondence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    gate_a, decisions, candidate_roots = _correspondence_fixture(tmp_path, mixed=False)
    monkeypatch.setattr(preparation, "EXPECTED_DECISION_COUNT", 1)

    rows, direct = preparation._decision_correspondence(
        gate_a, decisions, {"items": []}, candidate_roots
    )

    assert rows[0]["mapping_outcome"] == "mapped"
    assert rows[0]["entity_ids_by_kind"]["blocks"] == ["block-body", "block-toc"]
    facts = next(iter(direct.values()))
    assert facts["navigation_entity_ids_by_kind"]["blocks"] == ["block-toc"]


def _review_fixture(
    root: Path,
    *,
    stale_freeze: bool = False,
    wrong_decision_hash: bool = False,
    decision_variant: str = "valid",
) -> preparation.GateAPreparationRequest:
    data_root = root / "data"
    task03j_root = data_root / "task03j"
    review_root = data_root / "review"
    gate_a_path = data_root / "gate_a.json"
    output_parent = data_root / "output"
    task03j_root.mkdir(parents=True)
    (review_root / "records").mkdir(parents=True)
    (review_root / "gate_d").mkdir()
    gate_a = {
        "review_run_id": preparation.TASK04A_GATE_A_ID,
        "pass": "task03j_final",
        "status": "source_free_prepared",
        "source_free_boundary": {
            "source_pdf_bytes_read": False,
            "renders_generated": False,
            "model_files_read": False,
        },
    }
    entries = [
        {
            "entry_id": f"tocpagev1-{index:024x}",
            "disposition": "toc" if index < 60 else "not_toc",
        }
        for index in range(757)
    ]
    if decision_variant == "duplicate":
        entries[-1]["entry_id"] = entries[-2]["entry_id"]
    elif decision_variant == "missing":
        entries.pop()
    decisions = {"entries": entries}
    selection = {
        "review_run_id": preparation.TASK04A_REVIEW_ID,
        "items": [
            {
                "queue": "toc_review",
                "population": {"candidate_page_id": f"tocpagev1-{index:024x}"},
            }
            for index in range(341)
        ],
    }
    registry: dict[str, Any] = {"entries": []}
    ambiguous = {
        "entries": [
            {"reference_id": f"xref-{index:04d}"}
            for index in range(preparation.EXPECTED_AMBIGUOUS_LINK_COUNT)
        ]
    }
    paths = {
        "gate_a_preparation": gate_a_path,
        "toc_review_decisions": review_root / "records/toc_review_decisions.json",
        "selection_manifest": review_root / "records/selection_manifest.json",
        "release_freeze": review_root / "gate_d/release_freeze.json",
        "gate_d_completion": review_root / "gate_d/gate_d_completion.json",
        "usability_registry": review_root / "gate_d/usability_registry.json",
        "ambiguous_link_dispositions": review_root / "gate_d/ambiguous_link_dispositions.json",
    }
    _write(paths["gate_a_preparation"], gate_a)
    _write(paths["toc_review_decisions"], decisions)
    _write(paths["selection_manifest"], selection)
    _write(paths["usability_registry"], registry)
    _write(paths["ambiguous_link_dispositions"], ambiguous)
    decision_sha = "0" * 64 if wrong_decision_hash else sha256_file(paths["toc_review_decisions"])
    freeze = {
        "review_run_id": "stale-review" if stale_freeze else preparation.TASK04A_REVIEW_ID,
        "status": "frozen",
        "machine_candidate": {
            "production_extraction_id": preparation.PRODUCTION_EXTRACTION_ID,
            "scope_id": preparation.SCOPE_ID,
            "handoff_id": preparation.HANDOFF_ID,
        },
        "human_toc_decisions": {"sha256": decision_sha},
    }
    _write(paths["release_freeze"], freeze)
    refs = {
        name: file_reference(path, root=data_root)
        for name, path in paths.items()
        if name != "gate_d_completion"
    }
    completion = {
        "review_run_id": preparation.TASK04A_REVIEW_ID,
        "status": "complete",
        "source_count": preparation.EXPECTED_SOURCE_COUNT,
        "toc_decision_count": preparation.EXPECTED_DECISION_COUNT,
        "managed_records": {
            name: {"sha256": refs[name]["sha256"], "byte_size": refs[name]["byte_size"]}
            for name in ("release_freeze", "usability_registry", "ambiguous_link_dispositions")
        },
    }
    _write(paths["gate_d_completion"], completion)
    return preparation.GateAPreparationRequest(
        data_root=data_root,
        repo_root=Path(__file__).parents[1],
        task03j_root=task03j_root,
        gate_a_path=gate_a_path,
        review_root=review_root,
        output_parent=output_parent,
    )


def _machine_fixture(
    root: Path, *, mismatched_completion: bool
) -> tuple[preparation.GateAPreparationRequest, dict[str, Any]]:
    data_root = root / "data"
    task03j_root = data_root / "task03j"
    candidate_id = "docv1-" + "a" * 64
    candidate = task03j_root / "document_publications/documents/source-a" / candidate_id
    records = candidate / "records"
    records.mkdir(parents=True)
    completion_id = "docv1-" + "b" * 64 if mismatched_completion else candidate_id
    _write(
        records / "completion_record.json",
        {"candidate_id": completion_id, "candidate_inventory": {"sha256": "c" * 64}},
    )
    _write(
        records / "document_identity.json",
        {
            "candidate_id": candidate_id,
            "production_extraction_id": preparation.PRODUCTION_EXTRACTION_ID,
            "source": {"source_id": "source-a"},
            "stage_completions": {"structured_document": {}, "hierarchy_decisions": {}},
        },
    )
    _write(
        records / "artifact_inventory.json",
        {
            "files": [
                {"path": path, "sha256": "d" * 64, "byte_size": 1}
                for path in preparation._CANONICAL_FILES
            ]
        },
    )
    gate_a = {
        "toc_candidate_census": [
            {
                "source_id": "source-a",
                "source_ordinal": 1,
                "candidate_id": candidate_id,
                "candidate_pages": [],
            }
        ]
    }
    request = preparation.GateAPreparationRequest(
        data_root=data_root,
        repo_root=Path(__file__).parents[1],
        task03j_root=task03j_root,
        gate_a_path=data_root / "unused.json",
        review_root=data_root / "unused-review",
        output_parent=data_root / "output",
    )
    return request, gate_a


def _correspondence_fixture(
    root: Path, *, mixed: bool
) -> tuple[
    dict[str, Any],
    dict[str, str],
    dict[tuple[str, str], Path],
]:
    candidate_id = "docv1-" + "a" * 64
    candidate = root / "candidate"
    canonical = candidate / "content/canonical"
    canonical.mkdir(parents=True)
    page_id = "page-1"
    _jsonl(canonical / "pages.jsonl", [{"id": page_id}])
    _jsonl(
        canonical / "blocks.jsonl",
        [
            {
                "id": "block-toc",
                "section_id": "section-toc",
                "semantic_placement": "toc_content",
                "is_toc_row": True,
                "regions": [{"page_id": page_id}],
            },
            {
                "id": "block-body",
                "section_id": "section-body",
                "semantic_placement": "body",
                "is_toc_row": False,
                "regions": [{"page_id": page_id}],
            },
        ],
    )
    _jsonl(canonical / "tables.jsonl", [])
    entry_id = (
        "tocpagev1-"
        + sha256_bytes(
            json.dumps(
                {"candidate_id": candidate_id, "physical_page": 1},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        )[:24]
    )
    page = {
        "candidate_page_id": entry_id,
        "page_id": page_id,
        "physical_page": 1,
        "signals": ["canonical_toc_block", "canonical_toc_placement"],
    }
    if mixed:
        page["page_role"] = "mixed"
    gate_a = {
        "toc_candidate_census": [
            {
                "source_id": "source-a",
                "candidate_id": candidate_id,
                "candidate_pages": [page],
            }
        ]
    }
    return gate_a, {entry_id: "not_toc"}, {("source-a", candidate_id): candidate}


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def _jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
