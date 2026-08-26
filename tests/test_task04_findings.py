from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest
from task04_test_support import (
    AcceptingCandidateVerifier,
    FakeRenderer,
    fake_page_evidence,
    make_synthetic_review_tree,
    synthetic_build_request,
)

import er_commons.human_review_support.task04.finding_transaction as transaction_module
from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.human_review_support.task04 import (
    FindingClass,
    FindingDraft,
    FindingStatus,
    build_review_bundle,
    default_schema_root,
    record_finding,
)
from er_commons.human_review_support.task04.json_io import (
    read_json_object,
    require_list,
    require_mapping,
    require_string,
)
from er_commons.human_review_support.task04.models import JsonValue


def test_status_change_updates_stable_finding_and_handoff_projection(tmp_path: Path) -> None:
    review_root, review_item_id = _review_bundle(tmp_path)
    confirmed = _draft(review_item_id, status=FindingStatus.USER_CONFIRMED)

    first = record_finding(review_root, confirmed, schema_root=default_schema_root())
    initial_handoff = _read(review_root / "records/task03i_handoff.json")
    assert initial_handoff["extraction_findings"] == []

    accepted = _draft(review_item_id, status=FindingStatus.ACCEPTED_FOR_TASK03I)
    second = record_finding(review_root, accepted, schema_root=default_schema_root())
    register = _read(review_root / "records/finding_register.json")
    handoff = _read(review_root / "records/task03i_handoff.json")
    finding = _first_object(register, "findings")

    assert first.finding_id == second.finding_id
    assert len(require_list(register["findings"], path="$.findings")) == 1
    assert finding["status"] == "accepted_for_task03i"
    assert handoff["extraction_findings"] == register["findings"]
    assert handoff["finding_register_sha256"] == sha256_file(first.finding_register)
    assert handoff["input_inventory_sha256"] == sha256_file(
        review_root / "records/input_inventory.json"
    )
    assert handoff["selection_manifest_sha256"] == sha256_file(
        review_root / "records/selection_manifest.json"
    )
    assert handoff["review_bundle_manifest_sha256"] == sha256_file(
        review_root / "records/review_bundle_manifest.json"
    )
    anchor = _first_object(finding, "evidence_anchors")
    assert anchor["kind"] == "page"
    assert anchor["physical_page"] == 1
    source = require_mapping(anchor["source"], path="$.evidence_anchors[0].source")
    candidate = require_mapping(anchor["candidate"], path="$.evidence_anchors[0].candidate")
    assert source["source_id"] == "appendix_a"
    assert candidate["completion_sha256"] == "c" * 64
    assert candidate["inventory_sha256"] == "b" * 64


def test_non_extraction_finding_is_preserved_outside_handoff(tmp_path: Path) -> None:
    review_root, review_item_id = _review_bundle(tmp_path)
    record_finding(
        review_root,
        _draft(
            review_item_id,
            finding_class=FindingClass.REVIEW_TOOL_DEFECT,
            status=FindingStatus.RETAINED_TASK04,
        ),
        schema_root=default_schema_root(),
    )

    register = _read(review_root / "records/finding_register.json")
    handoff = _read(review_root / "records/task03i_handoff.json")
    assert len(require_list(register["findings"], path="$.findings")) == 1
    assert handoff["extraction_findings"] == []


def test_unknown_review_item_is_rejected_without_record_changes(tmp_path: Path) -> None:
    review_root, _ = _review_bundle(tmp_path)
    register = review_root / "records/finding_register.json"
    before = register.read_bytes()

    with pytest.raises(ValueError, match="unknown or stale review_item_id"):
        record_finding(
            review_root,
            _draft(f"reviewitem-{'f' * 24}"),
            schema_root=default_schema_root(),
        )

    assert register.read_bytes() == before


def test_mismatched_structured_anchor_is_rejected(tmp_path: Path) -> None:
    review_root, review_item_id = _review_bundle(tmp_path)
    record_finding(review_root, _draft(review_item_id), schema_root=default_schema_root())
    register_path = review_root / "records/finding_register.json"
    handoff_path = review_root / "records/task03i_handoff.json"
    register = _read(register_path)
    finding = _first_object(register, "findings")
    anchor = _first_object(finding, "evidence_anchors")
    anchor["physical_page"] = 99
    write_json_atomic(register_path, register)
    handoff = _read(handoff_path)
    handoff["finding_register_sha256"] = sha256_file(register_path)
    write_json_atomic(handoff_path, handoff)

    with pytest.raises(ValueError, match="mismatched or stale evidence anchors"):
        record_finding(review_root, _draft(review_item_id), schema_root=default_schema_root())


def test_stale_inventory_checksum_is_rejected(tmp_path: Path) -> None:
    review_root, review_item_id = _review_bundle(tmp_path)
    inventory_path = review_root / "records/input_inventory.json"
    inventory = _read(inventory_path)
    source = _first_object(inventory, "sources")
    source["source_pdf_sha256"] = "f" * 64
    write_json_atomic(inventory_path, inventory)

    with pytest.raises(ValueError, match="handoff.input_inventory_sha256"):
        record_finding(review_root, _draft(review_item_id), schema_root=default_schema_root())


def test_non_exact_handoff_projection_is_rejected(tmp_path: Path) -> None:
    review_root, review_item_id = _review_bundle(tmp_path)
    record_finding(
        review_root,
        _draft(review_item_id, status=FindingStatus.ACCEPTED_FOR_TASK03I),
        schema_root=default_schema_root(),
    )
    handoff_path = review_root / "records/task03i_handoff.json"
    handoff = _read(handoff_path)
    handoff["status"] = "empty_pending_review"
    handoff["extraction_findings"] = []
    write_json_atomic(handoff_path, handoff)

    with pytest.raises(ValueError, match="not an exact finding-register projection"):
        record_finding(review_root, _draft(review_item_id), schema_root=default_schema_root())


def test_interrupted_publication_is_completed_before_next_edit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_root, review_item_id = _review_bundle(tmp_path)
    real_replace = os.replace
    replacement_count = 0

    def interrupt_second_replace(source: Path, target: Path) -> None:
        nonlocal replacement_count
        replacement_count += 1
        if replacement_count == 2:
            raise OSError("simulated process interruption")
        real_replace(source, target)

    monkeypatch.setattr(transaction_module, "_replace_authoritative", interrupt_second_replace)
    with pytest.raises(RuntimeError, match="rerun to recover"):
        record_finding(
            review_root,
            _draft(review_item_id, status=FindingStatus.ACCEPTED_FOR_TASK03I),
            schema_root=default_schema_root(),
        )
    assert len(list((review_root / "records").glob(".finding-update-*"))) == 1

    monkeypatch.setattr(transaction_module, "_replace_authoritative", real_replace)
    result = record_finding(
        review_root,
        _draft(review_item_id, status=FindingStatus.ACCEPTED_FOR_TASK03I),
        schema_root=default_schema_root(),
    )
    register = _read(result.finding_register)
    handoff = _read(result.task03i_handoff)
    assert len(require_list(register["findings"], path="$.findings")) == 1
    assert handoff["extraction_findings"] == register["findings"]
    assert not list((review_root / "records").glob(".finding-update-*"))


def test_recovery_rejects_modified_target_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_root, review_item_id = _review_bundle(tmp_path)
    real_replace = os.replace

    def interrupt_first_replace(source: Path, target: Path) -> None:
        raise OSError("simulated process interruption")

    monkeypatch.setattr(transaction_module, "_replace_authoritative", interrupt_first_replace)
    with pytest.raises(RuntimeError):
        record_finding(review_root, _draft(review_item_id), schema_root=default_schema_root())
    monkeypatch.setattr(transaction_module, "_replace_authoritative", real_replace)
    (review_root / "records/finding_register.json").write_text("corrupt\n")

    with pytest.raises(ValueError, match="unrecognized bytes"):
        record_finding(review_root, _draft(review_item_id), schema_root=default_schema_root())


def test_recovery_rejects_ambiguous_journals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_root, review_item_id = _review_bundle(tmp_path)

    monkeypatch.setattr(
        transaction_module,
        "_replace_authoritative",
        lambda source, target: (_ for _ in ()).throw(OSError("interrupted")),
    )
    with pytest.raises(RuntimeError):
        record_finding(review_root, _draft(review_item_id), schema_root=default_schema_root())
    journal = next((review_root / "records").glob(".finding-update-*"))
    shutil.copytree(journal, journal.with_name(f"{journal.name}-duplicate"))

    with pytest.raises(ValueError, match="multiple journals"):
        record_finding(review_root, _draft(review_item_id), schema_root=default_schema_root())


def _review_bundle(tmp_path: Path) -> tuple[Path, str]:
    tree = make_synthetic_review_tree(tmp_path)
    review_root = build_review_bundle(
        synthetic_build_request(tree),
        renderer=FakeRenderer(),
        page_evidence_loader=fake_page_evidence,
        candidate_verifier=AcceptingCandidateVerifier(),
    )
    selection = _read(review_root / "records/selection_manifest.json")
    item = _first_object(selection, "items")
    review_item_id = require_string(item["review_item_id"], path="$.items[0].review_item_id")
    return review_root, review_item_id


def _draft(
    review_item_id: str,
    *,
    finding_class: FindingClass = FindingClass.EXTRACTION_DEFECT,
    status: FindingStatus = FindingStatus.USER_CONFIRMED,
) -> FindingDraft:
    return FindingDraft(
        review_item_id=review_item_id,
        finding_class=finding_class,
        status=status,
        expected_behavior="Expected table ownership behavior.",
        observed_behavior="Observed duplicate canonical text.",
        downstream_consequence="Search can return duplicate content.",
    )


def _read(path: Path) -> dict[str, JsonValue]:
    return read_json_object(path)


def _first_object(record: dict[str, JsonValue], field: str) -> dict[str, JsonValue]:
    rows = require_list(record[field], path=f"$.{field}")
    assert rows, f"expected at least one row at $.{field}"
    return require_mapping(rows[0], path=f"$.{field}[0]")
