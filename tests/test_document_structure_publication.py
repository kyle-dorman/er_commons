"""Publication-boundary tests for Task 03E.4 semantic candidates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.document_records.document_structure.errors import (
    DocumentStructureInvariantError,
)
from er_commons.document_records.document_structure.publication import (
    deep_audit_completed_document_structure,
    preserve_failed_attempt,
    verify_completed_document_structure,
)
from er_commons.document_records.document_structure.support import (
    MISSING_CHAPTER_CORRESPONDENCE_PATH,
    REPEATED_HEADING_CORRESPONDENCE_PATH,
    SUPPORT_PATHS,
)
from er_commons.document_records.record_mapping.identity import extraction_identity_sha256
from er_commons.document_records.record_mapping.publication import (
    sha256_file,
    write_inventory,
    write_json,
)


def _v3_identity() -> dict[str, object]:
    """Return a self-consistent compact identity for publication-boundary tests."""
    identity: dict[str, object] = {
        "semantic_contract": {
            "missing_chapter_repair": {
                "decisions": {
                    "path": "06e/eligible_decisions.jsonl",
                    "sha256": "1" * 64,
                }
            }
        }
    }
    digest = extraction_identity_sha256(identity)
    identity["extraction_id"] = f"exv1-{digest}"
    identity["identity_sha256"] = digest
    return identity


def _repeated_identity() -> dict[str, object]:
    """Return a self-consistent v2 identity with the new compact support binding."""
    identity: dict[str, object] = {
        "semantic_contract": {
            "repeated_heading_repair": {
                "decisions": {"path": "06d/eligible_decisions.jsonl", "sha256": "2" * 64},
                "correspondence_schema": {
                    "path": (
                        "benchmarks/er_bench/schemas/task06_recovery/v1/"
                        "repeated_heading_correspondence.schema.json"
                    ),
                    "sha256": sha256_file(
                        Path(__file__).parents[1]
                        / "benchmarks/er_bench/schemas/task06_recovery/v1/"
                        "repeated_heading_correspondence.schema.json"
                    ),
                },
            }
        }
    }
    digest = extraction_identity_sha256(identity)
    identity["extraction_id"] = f"exv1-{digest}"
    identity["identity_sha256"] = digest
    return identity


def _write_completed_candidate(
    root: Path,
    candidate_id: str,
    *,
    disposition: str = "accepted_with_known_limitations",
    status: str = "complete_with_warnings",
    semantic_payload: bytes | None = None,
    v3: bool = False,
    correspondence_payload: dict[str, object] | None = None,
    repeated: bool = False,
) -> None:
    """Write the smallest checksum-valid semantic candidate fixture."""
    support_files = []
    for role, relative in SUPPORT_PATHS.items():
        write_json(root / relative, {"role": role})
        support_files.append(
            {
                "role": role,
                "path": relative,
                "sha256": sha256_file(root / relative),
                "schema_version": "2.0.0",
            }
        )
    if v3:
        identity = _v3_identity()
        assert candidate_id == identity["extraction_id"]
        write_json(
            root / "records" / "extraction_identity.json",
            identity,
        )
        write_json(
            root / MISSING_CHAPTER_CORRESPONDENCE_PATH,
            correspondence_payload or _valid_missing_chapter_correspondence(candidate_id),
        )
        support_files.append(
            {
                "role": "missing_chapter_correspondence",
                "path": MISSING_CHAPTER_CORRESPONDENCE_PATH,
                "sha256": sha256_file(root / MISSING_CHAPTER_CORRESPONDENCE_PATH),
                "schema_version": "1.0.0",
            }
        )
    if repeated:
        identity = _repeated_identity()
        assert candidate_id == identity["extraction_id"]
        write_json(root / "records" / "extraction_identity.json", identity)
        write_json(
            root / REPEATED_HEADING_CORRESPONDENCE_PATH,
            correspondence_payload or _valid_repeated_correspondence(candidate_id),
        )
        support_files.append(
            {
                "role": "repeated_heading_correspondence",
                "path": REPEATED_HEADING_CORRESPONDENCE_PATH,
                "sha256": sha256_file(root / REPEATED_HEADING_CORRESPONDENCE_PATH),
                "schema_version": "1.0.0",
            }
        )
    write_json(
        root / "records" / "manifest.json",
        {
            "schema_version": (
                "er_commons.canonical_extraction_manifest.v3"
                if v3
                else "er_commons.canonical_extraction_manifest.v2"
            ),
            "extraction_id": candidate_id,
            **(
                {"identity_sha256": _v3_identity()["identity_sha256"]}
                if v3
                else (
                    {"identity_sha256": _repeated_identity()["identity_sha256"]} if repeated else {}
                )
            ),
            "source_semantic_disposition": disposition,
            "support_files": support_files,
        },
    )
    if semantic_payload is not None:
        payload_path = root / "canonical" / "blocks.jsonl"
        payload_path.parent.mkdir(parents=True, exist_ok=True)
        payload_path.write_bytes(semantic_payload)
    inventory_path = write_inventory(root)
    write_json(
        root / "records" / "completion_record.json",
        {
            "schema_version": (
                "er_commons.canonical_extraction_completion.v3"
                if v3
                else "er_commons.canonical_extraction_completion.v2"
            ),
            "extraction_id": candidate_id,
            "status": status,
            "source_semantic_disposition": disposition,
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "support_files_verified": True,
            **({"repeated_heading_correspondence_count": 1} if repeated else {}),
            "undeclared_difference_count": 0,
        },
    )


def _valid_repeated_correspondence(candidate_id: str) -> dict[str, object]:
    """Return one closed two-to-one repeated-heading mapping fixture."""
    return {
        "schema_version": "er_commons.recovery.repeated_heading_correspondence.v1",
        "candidate_id": candidate_id,
        "decision_ref": {"path": "06d/eligible_decisions.jsonl", "sha256": "2" * 64},
        "records": [
            {
                "schema_version": "er_commons.recovery.stage_correspondence.v1",
                "stage_role": "semantic_sections_and_target_aliases",
                "change_class": "many_to_one_repeated_heading_repair",
                "policy_version": "repeated_chapter_divider_opening_v1",
                "old_targets": [
                    {"section_id": "old/section/a", "role": "retained_anchor"},
                    {"section_id": "old/section/b", "role": "absorbed_duplicate"},
                ],
                "new_target": {
                    "section_id": f"{candidate_id}/section/deir_appendix_a/sec000001",
                    "state": "projected_candidate_local",
                },
                "source_heading_block_ids": ["old/block/a", "old/block/b"],
                "retained_heading_block_ids": [
                    f"{candidate_id}/block/deir_appendix_a/blk000001",
                    f"{candidate_id}/block/deir_appendix_a/blk000002",
                ],
                "retained_heading_stable_keys": ["a" * 64, "b" * 64],
                "logical_content_page_extent": [311, 449],
                "following_boundary_section_id": "old/section/c",
                "following_boundary_stable_key": "c" * 64,
                "following_boundary_raw_text": "07 | INFRASTRUCTURE",
                "following_boundary_page": 452,
                "content_record_count": 10,
                "content_record_ids_unique": True,
                "affected_descendants": [
                    "semantic_sections_and_membership",
                    "target_aliases",
                    "document_links_and_publication",
                    "collection_target_index_resolution_and_handoff",
                ],
            }
        ],
    }


def _valid_missing_chapter_correspondence(candidate_id: str) -> dict[str, object]:
    """Return one closed v3 correspondence fixture."""
    return {
        "schema_version": "er_commons.recovery.missing_chapter_correspondence.v1",
        "records": [
            {
                "schema_version": "er_commons.recovery.stage_correspondence.v1",
                "stage_role": "semantic_sections_and_target_aliases",
                "change_class": "distinct_missing_whole_chapter_target",
                "policy_version": "missing_whole_chapter_v1",
                "source_id": "main",
                "chapter_marker": "8",
                "chapter_title": "Chapter 8 Alternatives",
                "representation": "recovered_composite",
                "decision_ref": {"path": "06e/eligible_decisions.jsonl", "sha256": "1" * 64},
                "old_targets": [],
                "new_target": {
                    "section_id": f"{candidate_id}/section/main/sec000008",
                    "state": "projected_candidate_local",
                },
                "retained_heading_block_ids": [f"{candidate_id}/block/main/blk000008"],
                "ordered_child_refs": ["child-key"],
                "chapter_scope_content_ids": [f"{candidate_id}/block/main/blk000008"],
                "direct_content_ownership": [],
                "logical_content_page_extent": [10, 19],
                "following_boundary_record_id": f"{candidate_id}/block/main/blk000009",
                "scope_boundary_record_id": f"{candidate_id}/block/main/blk000009",
                "following_boundary_kind": "following_heading",
                "content_record_count": 3,
                "content_record_ids_unique": True,
            }
        ],
    }


def test_completed_candidate_verifier_fails_closed_on_tamper(tmp_path: Path) -> None:
    """Reuse is allowed only while every inventory and support checksum is exact."""
    candidate_id = "exv1-" + "a" * 64
    _write_completed_candidate(tmp_path, candidate_id)

    assert verify_completed_document_structure(tmp_path, candidate_id).is_file()

    support_path = tmp_path / SUPPORT_PATHS["cross_producer_bridge"]
    support_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(DocumentStructureInvariantError) as error:
        verify_completed_document_structure(tmp_path, candidate_id)
    assert error.value.stage == "candidate reuse verification"
    assert (
        error.value.invariant
        == "semantic candidate inventory metadata matches the managed file set"
    )
    assert error.value.subject.endswith("records/artifact_inventory.json")


def test_v3_adds_correspondence_without_changing_v2_support_roles(tmp_path: Path) -> None:
    candidate_id = str(_v3_identity()["extraction_id"])
    _write_completed_candidate(tmp_path, candidate_id, v3=True)
    assert verify_completed_document_structure(tmp_path, candidate_id).is_file()
    assert (tmp_path / MISSING_CHAPTER_CORRESPONDENCE_PATH).is_file()


def test_v2_repeated_heading_support_is_sealed_and_reusable(tmp_path: Path) -> None:
    """A new v2 candidate exposes compact 06D correspondence under its terminal seal."""
    candidate_id = str(_repeated_identity()["extraction_id"])
    _write_completed_candidate(tmp_path, candidate_id, repeated=True)

    assert verify_completed_document_structure(tmp_path, candidate_id).is_file()
    assert (tmp_path / REPEATED_HEADING_CORRESPONDENCE_PATH).is_file()


def test_v2_repeated_heading_reuse_rejects_wrong_candidate_binding(tmp_path: Path) -> None:
    """Inventory-consistent tampering still fails the compact semantic binding."""
    candidate_id = str(_repeated_identity()["extraction_id"])
    payload = _valid_repeated_correspondence(candidate_id)
    payload["candidate_id"] = "exv1-" + "f" * 64
    _write_completed_candidate(
        tmp_path,
        candidate_id,
        repeated=True,
        correspondence_payload=payload,
    )

    with pytest.raises(DocumentStructureInvariantError) as error:
        verify_completed_document_structure(tmp_path, candidate_id)
    assert error.value.invariant == "repeated-heading correspondence matches its closed schema"


def test_v2_repeated_heading_identity_rejects_omitted_support(tmp_path: Path) -> None:
    """A new identity cannot silently omit its declared correspondence support role."""
    candidate_id = str(_repeated_identity()["extraction_id"])
    _write_completed_candidate(tmp_path, candidate_id, repeated=True)
    (tmp_path / REPEATED_HEADING_CORRESPONDENCE_PATH).unlink()
    manifest_path = tmp_path / "records" / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["support_files"] = [
        item
        for item in manifest["support_files"]
        if item["role"] != "repeated_heading_correspondence"
    ]
    write_json(manifest_path, manifest)
    inventory_path = write_inventory(tmp_path)
    completion_path = tmp_path / "records" / "completion_record.json"
    completion = json.loads(completion_path.read_bytes())
    completion["artifact_inventory_sha256"] = sha256_file(inventory_path)
    write_json(completion_path, completion)

    with pytest.raises(DocumentStructureInvariantError) as error:
        verify_completed_document_structure(tmp_path, candidate_id)
    assert error.value.invariant == "semantic candidate support roles are exact and unique"


def test_v3_reuse_rejects_rehashed_identity_with_old_candidate_id(tmp_path: Path) -> None:
    """A substituted decision stream cannot be blessed under an old content address."""
    candidate_id = str(_v3_identity()["extraction_id"])
    _write_completed_candidate(tmp_path, candidate_id, v3=True)
    identity_path = tmp_path / "records" / "extraction_identity.json"
    identity = json.loads(identity_path.read_text())
    identity["semantic_contract"]["missing_chapter_repair"]["decisions"]["sha256"] = "0" * 64
    digest = extraction_identity_sha256(identity)
    identity["identity_sha256"] = digest
    write_json(identity_path, identity)
    manifest_path = tmp_path / "records" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["identity_sha256"] = digest
    write_json(manifest_path, manifest)
    inventory_path = write_inventory(tmp_path)
    completion_path = tmp_path / "records" / "completion_record.json"
    completion = json.loads(completion_path.read_text())
    completion["artifact_inventory_sha256"] = sha256_file(inventory_path)
    write_json(completion_path, completion)
    with pytest.raises(DocumentStructureInvariantError) as error:
        verify_completed_document_structure(tmp_path, candidate_id)
    assert error.value.invariant == "missing-chapter correspondence matches its closed schema"
    assert "identity digest or candidate binding" in str(error.value.observed)


@pytest.mark.parametrize(
    "payload",
    [
        {"schema_version": "er_commons.recovery.missing_chapter_correspondence.v1"},
        {
            "schema_version": "er_commons.recovery.missing_chapter_correspondence.v1",
            "records": [],
        },
    ],
)
def test_v3_reuse_rejects_missing_correspondence_records(
    tmp_path: Path, payload: dict[str, object]
) -> None:
    """A checksum-valid support file still fails when required records are absent."""
    candidate_id = str(_v3_identity()["extraction_id"])
    _write_completed_candidate(
        tmp_path,
        candidate_id,
        v3=True,
        correspondence_payload=payload,
    )
    with pytest.raises(DocumentStructureInvariantError) as error:
        verify_completed_document_structure(tmp_path, candidate_id)
    assert error.value.invariant == "missing-chapter correspondence matches its closed schema"


def test_fast_reuse_skips_semantic_hash_and_deep_audit_detects_same_size_tamper(
    tmp_path: Path,
) -> None:
    """Normal restart trusts immutable large bytes; explicit audit reauthenticates them."""
    candidate_id = "exv1-" + "e" * 64
    original = b'{"block":"one"}\n'
    changed = b'{"block":"two"}\n'
    assert len(original) == len(changed)
    _write_completed_candidate(tmp_path, candidate_id, semantic_payload=original)
    payload_path = tmp_path / "canonical" / "blocks.jsonl"
    payload_path.write_bytes(changed)

    assert verify_completed_document_structure(tmp_path, candidate_id).is_file()
    with pytest.raises(DocumentStructureInvariantError) as error:
        deep_audit_completed_document_structure(tmp_path, candidate_id)
    assert error.value.stage == "candidate deep audit"
    assert error.value.subject == payload_path.as_posix()


@pytest.mark.parametrize("status", ["complete", "complete_with_warnings"])
def test_completed_candidate_verifier_supports_strict_control(tmp_path: Path, status: str) -> None:
    """Strict hierarchy inputs may complete with or without inherited warnings."""
    candidate_id = "exv1-" + "c" * 64
    _write_completed_candidate(
        tmp_path,
        candidate_id,
        disposition="strict_quality_gate",
        status=status,
    )

    assert verify_completed_document_structure(tmp_path, candidate_id).is_file()


def test_failed_attempt_is_retained_without_completion(tmp_path: Path) -> None:
    """A simulated failed build remains inspectable but cannot look complete."""
    task_root = tmp_path / "task"
    staging_root = task_root / ".tmp" / "simulated-failure"
    write_json(staging_root / "records" / "partial.json", {"stage": "application"})
    write_json(staging_root / "records" / "completion_record.json", {"status": "complete"})

    failed = preserve_failed_attempt(task_root, staging_root)

    assert failed == task_root / "attempts" / "simulated-failure"
    assert (failed / "records" / "partial.json").is_file()
    assert not (failed / "records" / "completion_record.json").exists()
    assert not staging_root.exists()


def test_completion_inventory_digest_is_rechecked(tmp_path: Path) -> None:
    """A completion record cannot point at a substituted inventory."""
    candidate_id = "exv1-" + "b" * 64
    _write_completed_candidate(tmp_path, candidate_id)
    completion_path = tmp_path / "records" / "completion_record.json"
    completion = json.loads(completion_path.read_bytes())
    completion["artifact_inventory_sha256"] = "0" * 64
    write_json(completion_path, completion)

    with pytest.raises(DocumentStructureInvariantError) as error:
        verify_completed_document_structure(tmp_path, candidate_id)
    assert error.value.invariant == "semantic completion seals its inventory"
    assert error.value.expected == sha256_file(tmp_path / "records" / "artifact_inventory.json")
    assert error.value.observed == "0" * 64


def test_malformed_terminal_record_has_structured_evidence(tmp_path: Path) -> None:
    """A malformed reuse record names the failed invariant and exact subject."""
    candidate_id = "exv1-" + "d" * 64
    _write_completed_candidate(tmp_path, candidate_id)
    manifest_path = tmp_path / "records" / "manifest.json"
    manifest_path.write_text("{", encoding="utf-8")

    with pytest.raises(DocumentStructureInvariantError) as error:
        verify_completed_document_structure(tmp_path, candidate_id)

    assert error.value.invariant == "candidate record contains valid JSON"
    assert error.value.expected == "valid JSON"
    assert error.value.subject == manifest_path.as_posix()
