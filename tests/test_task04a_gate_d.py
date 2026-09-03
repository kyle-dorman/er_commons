from __future__ import annotations

import json
from pathlib import Path

from er_commons.artifact_io import sha256_file
from er_commons.human_review_support.task04.gate_d import GateDRequest, publish_gate_d

SCHEMA_ROOT = Path(__file__).parents[1] / "benchmarks/er_bench/schemas/task04a_review/v1"


def test_gate_d_publishes_compact_records_without_hashing_gate_a(tmp_path: Path) -> None:
    gate_a_path, gate_c_root = _gate_d_fixture(tmp_path)

    output = publish_gate_d(GateDRequest(gate_a_path, gate_c_root, SCHEMA_ROOT))

    assert output == gate_c_root / "gate_d"
    completion = _read(output / "gate_d_completion.json")
    release = _read(output / "release_freeze.json")
    dispositions = _read(output / "ambiguous_link_dispositions.json")
    assert completion["large_file_hashing_performed"] is False
    assert completion["largest_hashed_input_bytes"] < 1_000_000
    assert len(completion["managed_records"]) == 5
    assert release["decision_counts"] == {"total": 757, "toc": 60, "not_toc": 697}
    assert len(dispositions["entries"]) == 725
    assert all(entry["disposition"] == "unresolved" for entry in dispositions["entries"])
    decision_reference = release["human_toc_decisions"]
    assert decision_reference["sha256"] == sha256_file(gate_c_root / decision_reference["path"])
    assert not (gate_c_root / ".gate_d.staging").exists()


def _gate_d_fixture(root: Path) -> tuple[Path, Path]:
    review_parent = root / "task_04_review"
    gate_a_root = review_parent / "reviewv1-task03j-final-b19a7a36b04bda89"
    gate_c_root = review_parent / "reviewv1-task03j-final-c17"
    gate_a_path = gate_a_root / "records/gate_a_preparation.json"
    records = gate_c_root / "records"
    gate_a_path.parent.mkdir(parents=True)
    records.mkdir(parents=True)

    page_ids = [f"tocpagev1-{index:04d}" for index in range(757)]
    censuses = []
    for source_index in range(35):
        pages = (
            [
                {
                    "candidate_page_id": entry_id,
                    "physical_page": index + 1,
                    "signals": ["canonical_toc_block"],
                }
                for index, entry_id in enumerate(page_ids)
            ]
            if source_index == 0
            else []
        )
        links = (
            [
                {
                    "reference_id": f"xref-{index:04d}",
                    "raw_text": f"page {index}",
                    "lookup_key": str(index),
                    "mention_class": "printed_page",
                    "unresolved_reason": None,
                    "candidate_target_ids": [f"target-{index:04d}"],
                }
                for index in range(725)
            ]
            if source_index == 0
            else []
        )
        censuses.append(
            {
                "source_id": f"source-{source_index:02d}",
                "source_ordinal": source_index + 1,
                "candidate_id": f"docv1-{source_index:02d}",
                "candidate_pages": pages,
                "ambiguous_reference_links": links,
            }
        )
    gate_a = {
        "pass": "task03j_final",
        "status": "source_free_prepared",
        "review_run_id": "reviewv1-task03j-final-b19a7a36b04bda89",
        "inputs": {
            "task03j": {
                "production_extraction_id": "exv1-test",
                "scope_id": "scopev1-test",
                "handoff_id": "handoffv1-test",
            }
        },
        "toc_candidate_census": censuses,
    }
    gate_c = {
        "review_run_id": "reviewv1-task03j-final-c17",
        "source_count": 35,
        "ambiguous_reference_link_count": 725,
    }
    selection = {
        "items": [
            {
                "queue": "positive_toc",
                "population": {"candidate_page_id": entry_id},
            }
            for entry_id in page_ids[:341]
        ]
    }
    finding = {
        "status": "machine_evidence_bound_pending_human_confirmation",
        "finding_id": "finding-test",
        "source_id": "deir_appendix_k2_part_5_of_5",
        "physical_pages": list(range(974, 984)),
    }
    decisions = {
        "entries": [
            {
                "entry_id": entry_id,
                "disposition": "toc" if index < 60 else "not_toc",
            }
            for index, entry_id in enumerate(page_ids)
        ]
    }
    _write(gate_a_path, gate_a)
    _write(records / "gate_c_execution.json", gate_c)
    _write(records / "selection_manifest.json", selection)
    _write(records / "task03i_finding_recheck.json", finding)
    _write(records / "toc_review_decisions.json", decisions)
    return gate_a_path, gate_c_root


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value))


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    assert isinstance(value, dict)
    return value
