"""Synthetic source-free tests for cross-root imported document selection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from er_commons.collection_processing.authority_refs import (
    CollectionArtifactReference,
    CollectionArtifactResolver,
)
from er_commons.collection_processing.config import CollectionRunSpec
from er_commons.collection_processing.imported_evidence import (
    build_imported_terminal_evidence,
)
from er_commons.collection_processing.imported_selection import (
    ImportedDocumentSelection,
    load_imported_document_selection,
)
from er_commons.collection_processing.preflight import prepare_collection_run
from er_commons.document_publication.identity import build_scope_id


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _write_json(root: Path, relative: str, value: object) -> dict[str, object]:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    content = _json_bytes(value)
    path.write_bytes(content)
    return {
        "authority": "document_input_root",
        "path": relative,
        "sha256": hashlib.sha256(content).hexdigest(),
        "byte_size": len(content),
    }


def _managed_inventory(root: Path, *, total_field: str) -> dict[str, object]:
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in {"records/artifact_inventory.json", "records/completion_record.json"}:
            continue
        content = path.read_bytes()
        files.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(content).hexdigest(),
                "byte_size": len(content),
            }
        )
    return {
        "file_count": len(files),
        total_field: sum(item["byte_size"] for item in files),
        "files": files,
    }


def _fixture(
    tmp_path: Path, *, count: int = 2, valid_linked_inventory_binding: bool = True
) -> dict[str, Any]:
    document_root = tmp_path / "retained-v32"
    collection_root = tmp_path / "fresh-v33"
    document_root.mkdir()
    collection_root.mkdir()
    production_ref = _write_json(
        document_root,
        "resolved_specs_v1/00_initial/production_identity.json",
        {"schema_version": "production", "extraction_id": "exv1-" + "a" * 64},
    )
    spec_ref = _write_json(
        document_root,
        "resolved_specs_v1/00_initial/task06g_document_v1.json",
        {"schema_version": "document", "production_extraction_id": "exv1-" + "a" * 64},
    )
    candidates = []
    order = tuple(f"source_{ordinal}" for ordinal in range(1, count + 1))
    for ordinal, source_id in enumerate(order, start=1):
        candidate_id = f"docv1-{ordinal:064x}"
        linked_id = f"exv1-{ordinal + 100:064x}"
        candidate_root = f"document_publications/documents/{source_id}/{candidate_id}"
        linked_root = f"document_links/linked_candidates/{source_id}/{linked_id}"
        source = {
            "source_id": source_id,
            "sha256": f"{ordinal + 200:064x}",
            "pdf_page_count": ordinal,
        }
        linked_identity_ref = _write_json(
            document_root,
            f"{linked_root}/records/extraction_identity.json",
            {"extraction_id": linked_id},
        )
        linked_inventory_ref = _write_json(
            document_root,
            f"{linked_root}/records/artifact_inventory.json",
            _managed_inventory(document_root / linked_root, total_field="byte_size"),
        )
        linked_completion_ref = _write_json(
            document_root,
            f"{linked_root}/records/completion_record.json",
            {
                "extraction_id": linked_id,
                "status": "complete",
                "completion_last": True,
                "artifact_inventory_sha256": (
                    linked_inventory_ref["sha256"] if valid_linked_inventory_binding else "f" * 64
                ),
            },
        )
        identity_ref = _write_json(
            document_root,
            f"{candidate_root}/records/document_identity.json",
            {
                "candidate_id": candidate_id,
                "source": source,
                "production_extraction_id": "exv1-" + "a" * 64,
                "run_spec_sha256": spec_ref["sha256"],
                "resolved_spec_ref": {
                    "path": f"retained-v32/{spec_ref['path']}",
                    "sha256": spec_ref["sha256"],
                },
                "stage_completions": {
                    "linked_document": {
                        "path": f"retained-v32/{linked_completion_ref['path']}",
                        "sha256": linked_completion_ref["sha256"],
                    }
                },
                "terminal_state": "complete",
            },
        )
        downstream_ref = _write_json(
            document_root,
            f"{candidate_root}/records/downstream_replay.json",
            {
                "candidate_id": candidate_id,
                "source": source,
                "replacement_linked_document_completion_ref": {
                    "path": f"retained-v32/{linked_completion_ref['path']}",
                    "sha256": linked_completion_ref["sha256"],
                },
            },
        )
        for offset, name in enumerate(
            (
                "documents.jsonl",
                "sections.jsonl",
                "tables.jsonl",
                "figures.jsonl",
                "pages.jsonl",
                "cross_references.jsonl",
                "target_aliases.jsonl",
            ),
            start=1,
        ):
            payload = document_root / candidate_root / "content" / "canonical" / name
            payload.parent.mkdir(parents=True, exist_ok=True)
            payload.write_bytes(b"x" * offset)
        inventory_ref = _write_json(
            document_root,
            f"{candidate_root}/records/artifact_inventory.json",
            _managed_inventory(document_root / candidate_root, total_field="byte_count"),
        )
        completion_ref = _write_json(
            document_root,
            f"{candidate_root}/records/completion_record.json",
            {
                "candidate_id": candidate_id,
                "source": source,
                "status": "complete",
                "transaction_id": f"txv1-{ordinal:064x}",
                "candidate_inventory": {
                    "path": str(inventory_ref["path"]).removeprefix("document_publications/"),
                    "sha256": inventory_ref["sha256"],
                },
            },
        )
        candidates.append(
            {
                "source_ordinal": ordinal,
                "logical_source_id": source_id,
                "physical_source_id": source_id,
                "source_identity": source,
                "candidate_id": candidate_id,
                "candidate_root": candidate_root,
                "document_identity_ref": identity_ref,
                "document_completion_ref": completion_ref,
                "candidate_inventory_ref": inventory_ref,
                "downstream_replay_ref": downstream_ref,
                "linked_candidate_id": linked_id,
                "linked_candidate_root": linked_root,
                "linked_identity_ref": linked_identity_ref,
                "linked_completion_ref": linked_completion_ref,
                "linked_inventory_ref": linked_inventory_ref,
            }
        )
    manifest = {
        "schema_version": "er_commons.imported_document_selection.v1",
        "document_input_root_relative_path": "retained-v32",
        "document_production_identity_ref": production_ref,
        "document_run_spec_ref": spec_ref,
        "source_count": count,
        "ordered_source_ids": list(order),
        "candidates": candidates,
    }
    selection_path = tmp_path / "selection.json"
    selection_bytes = _json_bytes(manifest)
    selection_path.write_bytes(selection_bytes)
    return {
        "document_root": document_root,
        "collection_root": collection_root,
        "resolver": CollectionArtifactResolver(
            document_input_root=document_root,
            collection_output_root=collection_root,
        ),
        "manifest": manifest,
        "path": selection_path,
        "order": order,
        "sha256": hashlib.sha256(selection_bytes).hexdigest(),
        "byte_size": len(selection_bytes),
    }


def _load(fixture: dict[str, Any]) -> ImportedDocumentSelection:
    return load_imported_document_selection(
        fixture["path"],
        expected_source_order=fixture["order"],
        expected_sha256=fixture["sha256"],
        expected_byte_size=fixture["byte_size"],
        resolver=fixture["resolver"],
    )


def _artifact_ref(root: Path, path: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "authority": "artifact_root",
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "byte_size": len(content),
    }


def _v4_spec(tmp_path: Path, fixture: dict[str, Any]) -> tuple[Path, str]:
    production_id = "cprodv1-" + "b" * 64
    identity_path = tmp_path / "collection-production.json"
    identity_path.write_bytes(
        _json_bytes(
            {
                "schema_version": "er_commons.collection_production_identity.v1",
                "collection_production_id": production_id,
            }
        )
    )
    sources = []
    for item in fixture["manifest"]["candidates"]:
        source = dict(item["source_identity"])
        source["byte_size"] = 1
        sources.append(
            {
                "source": source,
                "family_root_source_id": fixture["order"][0],
                "document_role": (
                    "root_report" if item["source_ordinal"] == 1 else "top_level_appendix"
                ),
                "parent_source_id": (None if item["source_ordinal"] == 1 else fixture["order"][0]),
                "reference_aliases": [item["physical_source_id"]],
            }
        )
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_bytes(
        _json_bytes(
            {
                "schema_version": "er_commons.source_family_catalog.v1",
                "catalog_version": "fixture-v1",
                "source_family_id": "fixture",
                "sources": sources,
            }
        )
    )
    spec = {
        "schema_version": "er_commons.collection_run_spec.v4",
        "source_membership": [
            {
                "logical_source_id": source_id,
                "physical_source_id": source_id,
            }
            for source_id in fixture["order"]
        ],
        "source_ids": list(fixture["order"]),
        "source_family_catalog_relative_path": "catalog.json",
        "blocking_policy": "all_sources_successful",
        "document_evidence_mode": "imported_downstream_selection",
        "target_policy_sha256": "d" * 64,
        "resolution_policy_sha256": "e" * 64,
        "ordering_policy_version": "record_target_order_v2",
        "collection_output_relative_root": "fresh-v33",
        "collection_production_id": production_id,
        "collection_production_identity_ref": _artifact_ref(tmp_path, identity_path),
        "imported_document_root_relative_path": "retained-v32",
        "imported_selection_ref": _artifact_ref(tmp_path, fixture["path"]),
        "imported_document_run_spec_ref": fixture["manifest"]["document_run_spec_ref"],
        "imported_document_production_identity_ref": fixture["manifest"][
            "document_production_identity_ref"
        ],
    }
    path = tmp_path / "collection-v4.json"
    path.write_bytes(_json_bytes(spec))
    return path, production_id


def test_loads_exact_ordered_selection_and_pins_each_candidate(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)

    selection = _load(fixture)

    assert selection.ordered_source_ids == fixture["order"]
    assert len({item.selection_sha256 for item in selection.candidates}) == 2
    assert all(
        item.document_completion_ref.authority == "document_input_root"
        for item in selection.candidates
    )


@pytest.mark.parametrize("mutation", ["missing", "extra", "changed_size"])
def test_rejects_candidate_file_set_or_size_drift(tmp_path: Path, mutation: str) -> None:
    fixture = _fixture(tmp_path, count=1)
    candidate = fixture["manifest"]["candidates"][0]
    candidate_root = fixture["document_root"] / candidate["candidate_root"]
    payload = candidate_root / "content/canonical/documents.jsonl"
    if mutation == "missing":
        payload.unlink()
    elif mutation == "extra":
        (candidate_root / "undeclared.json").write_text("{}\n")
    else:
        payload.write_bytes(payload.read_bytes() + b"x")

    with pytest.raises(ValueError, match="file set or byte sizes differ"):
        _load(fixture)


def test_rejects_linked_candidate_file_set_drift(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path, count=1)
    candidate = fixture["manifest"]["candidates"][0]
    linked_root = fixture["document_root"] / candidate["linked_candidate_root"]
    (linked_root / "undeclared.json").write_text("{}\n")

    with pytest.raises(ValueError, match="file set or byte sizes differ"):
        _load(fixture)


def test_rejects_linked_completion_inventory_binding(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path, count=1, valid_linked_inventory_binding=False)

    with pytest.raises(ValueError, match="linked completion inventory binding differs"):
        _load(fixture)


def test_inventory_closure_does_not_read_managed_payloads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path, count=1)
    original = Path.read_bytes

    def guarded_read(path: Path) -> bytes:
        if "canonical" in path.parts:
            raise AssertionError(f"managed payload was read: {path}")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read)

    assert len(_load(fixture).candidates) == 1


def test_builds_terminal_evidence_only_from_pinned_selection(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path, count=1)
    selection = _load(fixture)
    selection_ref = {
        "path": "resolved_specs_v1/00_initial/imported_document_selection.json",
        "sha256": fixture["sha256"],
        "byte_size": fixture["byte_size"],
    }

    evidence = build_imported_terminal_evidence(
        selection,
        selection_ref=selection_ref,
        resolver=fixture["resolver"],
    )

    assert len(evidence) == 1
    assert evidence[0].candidate_id == selection.candidates[0].candidate_id
    assert evidence[0].evidence_kind == "downstream_replay"
    assert evidence[0].attempt is None
    assert evidence[0].cross_references_ref["authority"] == "document_input_root"
    assert evidence[0].imported_selection_ref == selection_ref
    assert evidence[0].imported_selection_entry_sha256 == selection.candidates[0].selection_sha256


@pytest.mark.parametrize("mutation", ["order", "duplicate_source", "duplicate_candidate"])
def test_rejects_order_and_identity_mutations(tmp_path: Path, mutation: str) -> None:
    fixture = _fixture(tmp_path)
    manifest = fixture["manifest"]
    if mutation == "order":
        manifest["candidates"].reverse()
    elif mutation == "duplicate_source":
        manifest["candidates"][1]["physical_source_id"] = "source_1"
        manifest["candidates"][1]["source_identity"]["source_id"] = "source_1"
        manifest["ordered_source_ids"][1] = "source_1"
    else:
        manifest["candidates"][1]["candidate_id"] = manifest["candidates"][0]["candidate_id"]
        manifest["candidates"][1]["candidate_root"] = manifest["candidates"][0]["candidate_root"]
    content = _json_bytes(manifest)
    fixture["path"].write_bytes(content)
    fixture.update(sha256=hashlib.sha256(content).hexdigest(), byte_size=len(content))

    with pytest.raises((ValueError, ValidationError)):
        _load(fixture)


def test_rejects_wrong_authority_and_path_escape() -> None:
    base = {
        "path": "record.json",
        "sha256": "a" * 64,
        "byte_size": 1,
    }
    output_ref = CollectionArtifactReference(authority="collection_output_root", **base)
    assert output_ref.authority == "collection_output_root"
    with pytest.raises(ValidationError, match="normalized POSIX"):
        CollectionArtifactReference(authority="document_input_root", **(base | {"path": "../x"}))
    with pytest.raises(ValidationError, match="normalized POSIX"):
        CollectionArtifactReference(authority="document_input_root", **(base | {"path": "a//b"}))


def test_selection_rejects_output_authority_for_an_imported_candidate(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path, count=1)
    fixture["manifest"]["candidates"][0]["document_completion_ref"]["authority"] = (
        "collection_output_root"
    )
    content = _json_bytes(fixture["manifest"])
    fixture["path"].write_bytes(content)
    fixture.update(sha256=hashlib.sha256(content).hexdigest(), byte_size=len(content))

    with pytest.raises(ValidationError, match="pinned root"):
        _load(fixture)


def test_resolver_rejects_wrong_authority_symlink_hash_and_size(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path, count=1)
    resolver = fixture["resolver"]
    path = fixture["document_root"] / "compact.json"
    path.write_text("{}\n")
    good = CollectionArtifactReference(
        authority="document_input_root",
        path="compact.json",
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        byte_size=path.stat().st_size,
    )
    with pytest.raises(ValueError, match="wrong authority"):
        resolver.resolve(good, expected_authority="collection_output_root")
    with pytest.raises(ValueError, match="byte size differs"):
        resolver.resolve(good.model_copy(update={"byte_size": good.byte_size + 1}))
    with pytest.raises(ValueError, match="checksum differs"):
        resolver.resolve(good.model_copy(update={"sha256": "f" * 64}))

    target = fixture["document_root"] / "target.json"
    target.write_text("{}\n")
    symlink = fixture["document_root"] / "alias.json"
    symlink.symlink_to(target)
    linked = good.model_copy(
        update={
            "path": "alias.json",
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "byte_size": target.stat().st_size,
        }
    )
    with pytest.raises(ValueError, match="symlink"):
        resolver.resolve(linked)


def test_loader_rejects_changed_artifact_and_manifest_symlink(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path, count=1)
    completion = fixture["manifest"]["candidates"][0]["document_completion_ref"]
    (fixture["document_root"] / completion["path"]).write_text("changed\n")
    with pytest.raises(ValueError, match="byte size differs|checksum differs"):
        _load(fixture)

    selection_link = tmp_path / "selection-link.json"
    selection_link.symlink_to(fixture["path"])
    fixture["path"] = selection_link
    with pytest.raises(ValueError, match="non-symlink"):
        _load(fixture)


def test_resolver_refuses_prohibited_payload_before_open(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path, count=1)
    reference = CollectionArtifactReference(
        authority="document_input_root",
        path="never-open.pdf",
        sha256="a" * 64,
        byte_size=1,
    )

    with pytest.raises(ValueError, match="prohibited source/model payload access"):
        fixture["resolver"].resolve(reference)


def test_v4_preflight_uses_only_frozen_imported_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    fixture["collection_root"].rmdir()
    spec_path, production_id = _v4_spec(tmp_path, fixture)
    imported_spec = SimpleNamespace(
        production_extraction_id="exv1-" + "a" * 64,
        artifact_relative_root=Path("retained-v32/document_publications"),
    )
    monkeypatch.setattr(
        "er_commons.collection_processing.imported_preflight.load_document_run_spec",
        lambda path: (imported_spec, hashlib.sha256(path.read_bytes()).hexdigest()),
    )
    identity_validation: dict[str, object] = {}

    def validate_identity(_record: object, **kwargs: object) -> SimpleNamespace:
        identity_validation.update(kwargs)
        return SimpleNamespace(collection_production_id=production_id)

    monkeypatch.setattr(
        "er_commons.collection_processing.imported_preflight.validate_collection_production_identity",
        validate_identity,
    )
    monkeypatch.setattr(
        "er_commons.collection_processing.legacy_preflight.load_sealed_manifest_metadata",
        lambda *_args, **_kwargs: pytest.fail("v4 preflight accessed the source manifest"),
    )
    monkeypatch.setattr(
        "er_commons.collection_processing.legacy_preflight.select_collection_sources",
        lambda *_args, **_kwargs: pytest.fail("v4 preflight selected source payloads"),
    )

    run = prepare_collection_run(tmp_path, spec_path)

    spec_digest = hashlib.sha256(spec_path.read_bytes()).hexdigest()
    assert run.scope_id == build_scope_id(
        run_spec_sha256=spec_digest, production_extraction_id=production_id
    )
    assert run.extraction_root == tmp_path / "fresh-v33"
    assert not run.extraction_root.exists()
    assert run.imported_document_root == tmp_path / "retained-v32"
    assert run.collection_production_id == production_id
    assert run.imported_selection is not None
    assert run.imported_selection.ordered_source_ids == fixture["order"]
    assert run.artifact_resolver is not None
    assert identity_validation["expected_output_namespace"] == "fresh-v33"
    assert identity_validation["expected_imported_selection_ref"] == (
        run.collection_spec.imported_selection_ref
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("legacy_document", "requires only its imported-selection controls"),
        ("wrong_mode", "requires imported downstream selection mode"),
        ("overlap", "roots must be distinct"),
        ("wrong_identity_authority", "artifact-root authority"),
    ],
)
def test_v4_config_rejects_ambiguous_roots_modes_and_controls(
    tmp_path: Path, mutation: str, message: str
) -> None:
    fixture = _fixture(tmp_path)
    spec_path, _ = _v4_spec(tmp_path, fixture)
    value = json.loads(spec_path.read_bytes())
    if mutation == "legacy_document":
        value["document_run_spec"] = "run.json"
    elif mutation == "wrong_mode":
        value["document_evidence_mode"] = "downstream_replay_only"
    elif mutation == "overlap":
        value["collection_output_relative_root"] = "retained-v32/new"
    else:
        value["collection_production_identity_ref"]["authority"] = "repository"

    with pytest.raises((ValueError, ValidationError), match=message):
        CollectionRunSpec.model_validate(value)
