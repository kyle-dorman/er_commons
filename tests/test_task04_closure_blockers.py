from __future__ import annotations

import json
import os
from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path
from typing import cast

import pytest
from task04_test_support import (
    AcceptingCandidateVerifier,
    FakeRenderer,
    SyntheticReviewTree,
    fake_page_evidence,
    make_synthetic_review_tree,
)

import er_commons.human_review_support.task04.finding_transaction as transaction_module
import er_commons.human_review_support.task04.records as records_module
from er_commons.artifact_io import sha256_file
from er_commons.human_review_support.task04 import (
    BuildRequest,
    FindingClass,
    FindingDraft,
    FindingRegisterStatus,
    FindingSelectors,
    FindingStatus,
    InputScopePolicy,
    build_review_bundle,
    default_schema_root,
    record_finding,
    set_finding_register_status,
)
from er_commons.human_review_support.task04.discovery import discover_inputs
from er_commons.human_review_support.task04.finding_anchors import (
    FindingSelectors as AnchorSelectors,
)
from er_commons.human_review_support.task04.finding_anchors import (
    anchor_records,
    derive_evidence_anchors,
)
from er_commons.human_review_support.task04.json_io import read_json_object
from er_commons.human_review_support.task04.models import (
    BlockEvidence,
    JsonValue,
    PageEvidence,
    TableEvidence,
)


def test_production_scope_rejects_a_valid_one_source_fixture(tmp_path: Path) -> None:
    tree = _ready_fixture(tmp_path)
    readiness_path = tree.retained_root / "inputs/task03h_preparation_readiness.json"
    readiness = _read(readiness_path)
    readiness["status"] = "ready_for_user_authorized_clean_run"
    _write(readiness_path, readiness)

    with pytest.raises(ValueError, match=r"source_scope\.source_count.*required=35"):
        discover_inputs(
            tree.retained_root,
            tree.data_root,
            candidate_verifier=AcceptingCandidateVerifier(),
        )


@pytest.mark.parametrize("field", ("staged_path", "sha256", "byte_size"))
def test_readiness_must_bind_exact_staged_catalog(tmp_path: Path, field: str) -> None:
    tree = _ready_fixture(tmp_path)
    readiness_path = tree.retained_root / "inputs/task03h_preparation_readiness.json"
    readiness = _read(readiness_path)
    catalog = _object(readiness, "catalog")
    invalid_values: dict[str, JsonValue] = {
        "staged_path": "inputs/wrong.json",
        "sha256": "f" * 64,
        "byte_size": 1,
    }
    catalog[field] = invalid_values[field]
    _write(readiness_path, readiness)

    with pytest.raises(ValueError, match=rf"\$\.catalog\.{field}"):
        _discover_fixture(tree)


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("status", r"\$\.status.*unaccepted|unaccepted.*\$\.status"),
        ("source_order", r"\$\.source_scope\.ordered_source_ids"),
    ),
)
def test_fixture_override_still_requires_accepted_declared_scope(
    tmp_path: Path, mutation: str, message: str
) -> None:
    tree = _ready_fixture(tmp_path)
    readiness_path = tree.retained_root / "inputs/task03h_preparation_readiness.json"
    readiness = _read(readiness_path)
    if mutation == "status":
        readiness["status"] = "ready_for_user_authorized_clean_run"
    else:
        _object(readiness, "source_scope")["ordered_source_ids"] = ["wrong_source"]
    _write(readiness_path, readiness)

    with pytest.raises(ValueError, match=message):
        _discover_fixture(tree)


def test_render_identity_binds_pillow_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_tree = _ready_fixture(tmp_path / "first")
    first_root = _build(first_tree)
    first_manifest = _read(first_root / "records/review_bundle_manifest.json")
    assert _object(first_manifest, "package_versions")["Pillow"] == version("Pillow")

    original_version = cast(
        Callable[[str], str],
        records_module.version,  # type: ignore[attr-defined]
    )

    def changed_version(distribution: str) -> str:
        return "999.0-test" if distribution == "Pillow" else original_version(distribution)

    monkeypatch.setattr(records_module, "version", changed_version)
    second_tree = _ready_fixture(tmp_path / "second")
    second_root = _build(second_tree)
    second_manifest = _read(second_root / "records/review_bundle_manifest.json")
    dependencies = _array(_object(second_manifest, "identity"), "dependencies")

    assert first_root.name != second_root.name
    assert _object(second_manifest, "package_versions")["Pillow"] == "999.0-test"
    assert any(
        isinstance(row, dict) and row.get("name") == "Pillow" and row.get("version") == "999.0-test"
        for row in dependencies
    )


def test_task03i_finding_carries_exact_table_and_block_objects(tmp_path: Path) -> None:
    tree = _ready_fixture(tmp_path)
    review_root = _build(tree, evidence_loader=_table_and_block_evidence)
    item = _first(_read(review_root / "records/selection_manifest.json"), "items")
    result = record_finding(
        review_root,
        _draft(
            str(item["review_item_id"]),
            FindingStatus.ACCEPTED_FOR_TASK03I,
            selectors=FindingSelectors(
                table_ids=("tbl/appendix_a/p1/table-1",),
                block_ids=("block/appendix_a/p1/paragraph-1",),
            ),
        ),
        schema_root=default_schema_root(),
    )
    register = _read(result.finding_register)
    handoff = _read(result.task03i_handoff)
    finding = _first(register, "findings")
    anchors = _array(finding, "evidence_anchors")
    exact = {
        row["kind"]: row
        for row in anchors
        if isinstance(row, dict) and row.get("kind") in {"canonical_table", "canonical_block"}
    }

    assert exact["canonical_table"]["bbox"] == [40.0, 50.0, 500.0, 700.0]
    assert exact["canonical_block"]["bbox"] == [50.0, 60.0, 200.0, 80.0]
    assert handoff["extraction_findings"] == register["findings"]


def test_tampered_canonical_bbox_is_rejected_as_stale_anchor(tmp_path: Path) -> None:
    tree = _ready_fixture(tmp_path)
    review_root = _build(tree, evidence_loader=_table_and_block_evidence)
    item = _first(_read(review_root / "records/selection_manifest.json"), "items")
    draft = _draft(
        str(item["review_item_id"]),
        selectors=FindingSelectors(block_ids=("block/appendix_a/p1/paragraph-1",)),
    )
    result = record_finding(review_root, draft, schema_root=default_schema_root())
    register = _read(result.finding_register)
    finding = _first(register, "findings")
    anchor = next(
        row
        for row in _array(finding, "evidence_anchors")
        if isinstance(row, dict) and row.get("kind") == "canonical_block"
    )
    anchor["bbox"] = [0.0, 0.0, 1.0, 1.0]
    _write(result.finding_register, register)
    handoff = _read(result.task03i_handoff)
    handoff["finding_register_sha256"] = sha256_file(result.finding_register)
    _write(result.task03i_handoff, handoff)

    with pytest.raises(ValueError, match="mismatched or stale evidence anchors"):
        record_finding(review_root, draft, schema_root=default_schema_root())


@pytest.mark.parametrize(
    "selectors",
    (
        FindingSelectors(table_ids=("tbl/not-retained",)),
        FindingSelectors(block_ids=("block/not-retained",)),
        FindingSelectors(observation_ids=("observation/not-retained",)),
    ),
)
def test_finding_rejects_unknown_exact_selectors(
    tmp_path: Path, selectors: FindingSelectors
) -> None:
    tree = _ready_fixture(tmp_path)
    review_root = _build(tree, evidence_loader=_table_and_block_evidence)
    item = _first(_read(review_root / "records/selection_manifest.json"), "items")

    with pytest.raises(ValueError, match="unknown or stale"):
        record_finding(
            review_root,
            _draft(str(item["review_item_id"]), selectors=selectors),
            schema_root=default_schema_root(),
        )


def test_failure_observation_selector_resolves_only_retained_typed_id() -> None:
    item: dict[str, JsonValue] = {
        "queue": "failure",
        "source_id": "appendix_a",
        "candidate_id": None,
        "physical_pages": [],
        "failure": {
            "attempts": [
                {
                    "attempt_id": "attempt-1",
                    "disposition": "failed",
                    "failure_class": "parse",
                    "stage": "producer",
                    "detail": "failed",
                    "relative_path": "attempt.json",
                }
            ]
        },
        "exact_evidence": {
            "canonical_objects": [],
            "observations": [{"kind": "failure_observation", "observation_id": "attempt-1"}],
        },
    }
    source: dict[str, JsonValue] = {
        "source_id": "appendix_a",
        "sha256": "a" * 64,
        "source_pdf_sha256": "a" * 64,
        "selected_candidate_id": None,
        "selected_completion_sha256": None,
        "selected_inventory_sha256": None,
    }
    anchors = derive_evidence_anchors(
        item,
        source,
        item_path="selection.items[0]",
        source_path="input_inventory.sources[0]",
        selectors=AnchorSelectors(observation_ids=("attempt-1",)),
    )

    observation = anchor_records(anchors)[1]
    assert isinstance(observation, dict)
    assert observation["observation_kind"] == "failure_observation"


def test_register_approval_and_closure_are_one_way_and_checksum_linked(tmp_path: Path) -> None:
    tree = _ready_fixture(tmp_path)
    review_root = _build(tree)
    item = _first(_read(review_root / "records/selection_manifest.json"), "items")
    review_item_id = str(item["review_item_id"])
    confirmed = record_finding(
        review_root,
        _draft(review_item_id),
        schema_root=default_schema_root(),
    )
    with pytest.raises(ValueError, match="user_confirmed"):
        set_finding_register_status(
            review_root,
            FindingRegisterStatus.APPROVED,
            schema_root=default_schema_root(),
        )

    retained = record_finding(
        review_root,
        _draft(review_item_id, FindingStatus.RETAINED_TASK04),
        schema_root=default_schema_root(),
    )
    assert retained.finding_id == confirmed.finding_id
    approved = set_finding_register_status(
        review_root,
        FindingRegisterStatus.APPROVED,
        schema_root=default_schema_root(),
    )
    register = _read(approved.finding_register)
    handoff = _read(approved.task03i_handoff)
    assert register["status"] == "approved"
    assert handoff["status"] == "approved"
    assert handoff["extraction_findings"] == []
    assert handoff["finding_register_sha256"] == sha256_file(approved.finding_register)

    with pytest.raises(ValueError, match="cannot be edited"):
        record_finding(
            review_root,
            _draft(review_item_id, FindingStatus.REJECTED_NOT_MATERIAL),
            schema_root=default_schema_root(),
        )
    closed = set_finding_register_status(
        review_root,
        FindingRegisterStatus.CLOSED,
        schema_root=default_schema_root(),
    )
    assert _read(closed.finding_register)["status"] == "closed"
    assert _read(closed.task03i_handoff)["status"] == "approved"


def test_register_status_transition_recovers_interrupted_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tree = _ready_fixture(tmp_path)
    review_root = _build(tree)
    real_replace = os.replace
    replacements = 0

    def interrupt_handoff(source: Path, target: Path) -> None:
        nonlocal replacements
        replacements += 1
        if replacements == 2:
            raise OSError("simulated status interruption")
        real_replace(source, target)

    monkeypatch.setattr(transaction_module, "_replace_authoritative", interrupt_handoff)
    with pytest.raises(RuntimeError, match="rerun to recover"):
        set_finding_register_status(
            review_root,
            FindingRegisterStatus.APPROVED,
            schema_root=default_schema_root(),
        )
    monkeypatch.setattr(transaction_module, "_replace_authoritative", real_replace)
    result = set_finding_register_status(
        review_root,
        FindingRegisterStatus.APPROVED,
        schema_root=default_schema_root(),
    )

    register = _read(result.finding_register)
    handoff = _read(result.task03i_handoff)
    assert register["status"] == "approved"
    assert handoff["finding_register_sha256"] == sha256_file(result.finding_register)
    assert not list((review_root / "records").glob(".finding-update-*"))


def _ready_fixture(tmp_path: Path) -> SyntheticReviewTree:
    tree = make_synthetic_review_tree(tmp_path)
    catalog_path = next((tree.retained_root / "inputs").glob("*source_family_catalog*.json"))
    readiness_path = tree.retained_root / "inputs/task03h_preparation_readiness.json"
    readiness = _read(readiness_path)
    readiness["status"] = "synthetic_fixture_ready"
    _object(readiness, "source_scope")["ordered_source_ids"] = ["appendix_a"]
    readiness["catalog"] = {
        "staged_path": catalog_path.relative_to(tree.data_root).as_posix(),
        "sha256": sha256_file(catalog_path),
        "byte_size": catalog_path.stat().st_size,
    }
    _write(readiness_path, readiness)
    return tree


def _discover_fixture(tree: SyntheticReviewTree) -> object:
    return discover_inputs(
        tree.retained_root,
        tree.data_root,
        candidate_verifier=AcceptingCandidateVerifier(),
        input_scope=InputScopePolicy.synthetic_fixture(source_count=1),
    )


def _build(tree: SyntheticReviewTree, *, evidence_loader: object | None = None) -> Path:
    kwargs: dict[str, object] = {
        "renderer": FakeRenderer(),
        "candidate_verifier": AcceptingCandidateVerifier(),
        "page_evidence_loader": evidence_loader or fake_page_evidence,
    }
    return build_review_bundle(
        BuildRequest(
            tree.retained_root,
            tree.data_root,
            tree.output_root,
            InputScopePolicy.synthetic_fixture(source_count=1),
        ),
        **kwargs,  # type: ignore[arg-type]
    )


def _table_and_block_evidence(
    candidate: Path, selected_pages: set[int], source_pdf: Path
) -> dict[int, PageEvidence]:
    del candidate, source_pdf
    return {
        page: PageEvidence(
            page,
            612.0,
            792.0,
            None,
            (
                BlockEvidence(
                    "block/appendix_a/p1/paragraph-1",
                    "paragraph",
                    "overlapping table text",
                    (50.0, 60.0, 200.0, 80.0),
                    1,
                ),
            ),
            (
                TableEvidence(
                    "tbl/appendix_a/p1/table-1",
                    None,
                    "tableformer",
                    (2, 2),
                    (),
                    (40.0, 50.0, 500.0, 700.0),
                    0,
                ),
            ),
        )
        for page in selected_pages
    }


def _draft(
    review_item_id: str,
    status: FindingStatus = FindingStatus.USER_CONFIRMED,
    *,
    selectors: FindingSelectors | None = None,
) -> FindingDraft:
    return FindingDraft(
        review_item_id=review_item_id,
        finding_class=FindingClass.EXTRACTION_DEFECT,
        status=status,
        expected_behavior="Canonical table and text ownership should be unambiguous.",
        observed_behavior="The retained exact objects show duplicate ownership.",
        downstream_consequence="Search can return duplicate table text.",
        selectors=selectors or FindingSelectors(),
    )


def _read(path: Path) -> dict[str, JsonValue]:
    return read_json_object(path)


def _write(path: Path, value: dict[str, JsonValue]) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n")


def _object(record: dict[str, JsonValue], field: str) -> dict[str, JsonValue]:
    value = record[field]
    assert isinstance(value, dict)
    return value


def _array(record: dict[str, JsonValue], field: str) -> list[JsonValue]:
    value = record[field]
    assert isinstance(value, list)
    return value


def _first(record: dict[str, JsonValue], field: str) -> dict[str, JsonValue]:
    values = _array(record, field)
    assert values and isinstance(values[0], dict)
    return values[0]


def test_new_register_status_cli_remains_thin() -> None:
    script = Path(__file__).parents[1] / "scripts/set_task04_finding_register_status.py"
    assert len(script.read_text().splitlines()) <= 60
