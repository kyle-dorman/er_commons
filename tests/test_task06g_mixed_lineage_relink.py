"""Focused source-free checks for the Task 06G mixed-lineage relink gate."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from er_commons.document_records.document_references.relink_preflight import (
    _validate_mixed_lineage_mapping,
)
from er_commons.document_records.document_references.relink_publication import (
    _relink_verification_budget,
)
from er_commons.document_records.document_references.relinking_config import (
    DocumentLinkRunSpec,
)

ROOT = Path(__file__).parents[1]
BASE = ROOT / "configs/brisbane_baylands_2025_deir_task04d_link_v1.json"


def test_relink_budget_covers_accepted_large_files_and_full_manifest() -> None:
    """The collection relink envelope covers G2, G3, and all 35 canonical inputs."""
    budget = _relink_verification_budget()
    assert budget.read_file_limit >= 1_174_032_051
    assert budget.read_file_limit >= 649_451_594
    assert budget.read_file_limit >= 554_127_874
    assert budget.read_total_limit > 5_001_823_926


def _changed_candidate(source_id: str, marker: str) -> dict[str, object]:
    root = f"replacement/{source_id}"
    return {
        "source_document": {
            "candidate_id": "docv1-" + marker * 64,
            "completion_ref": _ref(f"{root}/doc/records/completion_record.json", marker),
            "inventory_ref": _ref(f"{root}/doc/records/artifact_inventory.json", marker),
        },
        "structured_document": {
            "candidate_id": "exv1-" + marker * 64,
            "completion_ref": _ref(f"{root}/structure/records/completion_record.json", marker),
            "inventory_ref": _ref(f"{root}/structure/records/artifact_inventory.json", marker),
        },
    }


def _ref(path: str, marker: str = "a") -> dict[str, object]:
    return {
        "authority": "artifact_root",
        "path": path,
        "sha256": marker * 64,
        "byte_size": 1,
    }


def _specs() -> tuple[DocumentLinkRunSpec, DocumentLinkRunSpec]:
    base_value = json.loads(BASE.read_bytes())
    base = DocumentLinkRunSpec.model_validate(base_value)
    documents: list[dict[str, object]] = []
    changes = {
        "deir_appendix_f1": (
            "feir_appendix_f1",
            "1",
            "new_source_addition_no_old_entity_equivalence",
            "qualified_substitute_new_source_no_entity_equivalence",
            [
                _ref(
                    "pipelines/brisbane_baylands/task_06_recovery_v1/06c/"
                    "gate3_inputs_v1/source/records/source_manifest.json"
                )
            ],
            [],
        ),
        "deir_appendix_a": (
            "deir_appendix_a",
            "2",
            "repeated_heading_many_to_one",
            "accepted_repeated_heading_repair",
            [
                _ref(
                    "pipelines/brisbane_baylands/task_06_recovery_v1/06d/"
                    "qualification_v8/completion.json"
                )
            ],
            ["support/repeated_heading_correspondence.json"],
        ),
        "deir_main": (
            "deir_main",
            "3",
            "missing_chapter_additions_and_fc1_aliases",
            "accepted_missing_chapter_and_fc1_repair",
            [
                _ref(
                    "pipelines/brisbane_baylands/task_06_recovery_v1/06e/"
                    "qualification_v17/completion.json"
                ),
                _ref(
                    "pipelines/brisbane_baylands/task_06_recovery_v1/06f/"
                    "qualification_v10/completion.json"
                ),
            ],
            ["support/missing_chapter_correspondence.json"],
        ),
    }
    for original in base.documents:
        change = changes.get(original.source_id)
        if change is None:
            row = original.model_dump(mode="json")
            row.update(
                logical_source_id=original.source_id,
                base_source_id=original.source_id,
                base_source_document=original.source_document.model_dump(mode="json"),
                base_structured_document=original.structured_document.model_dump(mode="json"),
                change_class="preserved_semantic",
                reuse_basis="sealed_base_candidate_downstream_replay",
                evidence_refs=[original.source_document.completion_ref.model_dump(mode="json")],
                correspondence_refs=[],
            )
        else:
            selected_source, marker, change_class, reuse_basis, evidence, correspondence = change
            row = {"source_id": selected_source, **_changed_candidate(selected_source, marker)}
            structured_path = Path(row["structured_document"]["completion_ref"]["path"])
            row.update(
                logical_source_id=original.source_id,
                base_source_id=original.source_id,
                base_source_document=original.source_document.model_dump(mode="json"),
                base_structured_document=original.structured_document.model_dump(mode="json"),
                change_class=change_class,
                reuse_basis=reuse_basis,
                evidence_refs=evidence,
                correspondence_refs=[
                    _ref((structured_path.parent.parent / suffix).as_posix(), marker)
                    for suffix in correspondence
                ],
            )
        documents.append(row)
    value = deepcopy(base_value)
    value.update(
        schema_version="er_commons.document_link_run_spec.v2",
        resolution_status="resolved",
        figure_alias_source_ids=["deir_main"],
        accepted_fc1_evidence=_accepted_fc1_evidence(),
        base_membership_ref={"authority": "repository", **_ref("base.json")},
        documents=documents,
        selected_source_ids=[row["source_id"] for row in documents],
    )
    value["base_membership_ref"]["authority"] = "repository"
    return DocumentLinkRunSpec.model_validate(value), base


def _accepted_fc1_evidence() -> dict[str, object]:
    reference = _ref("06f/value.json")
    return {
        "qualification_id": "figqualv1-" + "b" * 64,
        "source_id": "deir_main",
        "completion_ref": reference,
        "inventory_ref": reference,
        "identity_ref": reference,
        "qualification_ref": reference,
        "figure_aliases_ref": reference,
        "target_index_entries_ref": reference,
    }


def test_mixed_lineage_accepts_only_three_owned_changes() -> None:
    selected, base = _specs()
    _validate_mixed_lineage_mapping(spec=selected, base=base)


@pytest.mark.parametrize(
    "mutation", ["wrong_source", "unowned_change", "missing_evidence", "shuffle"]
)
def test_mixed_lineage_rejects_incomplete_or_unowned_mapping(mutation: str) -> None:
    selected, base = _specs()
    value = selected.model_dump(mode="json")
    if mutation == "wrong_source":
        value["documents"][9]["source_id"] = "deir_appendix_f1"
        value["selected_source_ids"][9] = "deir_appendix_f1"
    elif mutation == "unowned_change":
        value["documents"][0]["source_document"]["candidate_id"] = "docv1-" + "9" * 64
    elif mutation == "missing_evidence":
        value["documents"][17]["evidence_refs"] = []
    else:
        value["documents"][0], value["documents"][1] = (
            value["documents"][1],
            value["documents"][0],
        )
        value["selected_source_ids"][0], value["selected_source_ids"][1] = (
            value["selected_source_ids"][1],
            value["selected_source_ids"][0],
        )
    with pytest.raises((ValueError, ValidationError)):
        _validate_mixed_lineage_mapping(spec=DocumentLinkRunSpec.model_validate(value), base=base)
