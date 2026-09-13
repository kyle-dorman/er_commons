"""Versioned collection identities preserve v2 and separate imported v3 evidence."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from er_commons.collection_processing.accounting import AccountingBuilder, AccountingInputs
from er_commons.collection_processing.artifact_reader import CollectionArtifactReader
from er_commons.collection_processing.bundle import ContractBundleWriter
from er_commons.collection_processing.contract import (
    HANDOFF_PREIMAGE_FIELDS,
    INDEX_PREIMAGE_FIELDS,
    LINK_PREIMAGE_FIELDS,
    build_collection_handoff_id,
    build_cross_document_link_id,
    build_record_target_index_id,
    canonical_sha256,
    collection_identity_fields,
)
from er_commons.collection_processing.cross_document_linking import (
    CrossDocumentLinkBuilder,
    CrossDocumentLinkInputs,
)
from er_commons.collection_processing.domain import PublishedStage, StageBuild
from er_commons.collection_processing.handoff_assembly import (
    HandoffAssembler,
    HandoffAssemblyInputs,
)
from er_commons.collection_processing.mentions import MentionManifest
from er_commons.collection_processing.record_target_indexing import (
    RecordTargetIndexBuilder,
    RecordTargetIndexInputs,
)
from er_commons.collection_processing.semantic_validation import validate_collection_bundle
from er_commons.collection_processing.storage import bytes_ref, json_bytes, managed_inventory
from er_commons.document_publication.published_document import DocumentTerminalEvidence

PRODUCTION = "exv1-" + "1" * 64
COLLECTION = "cprodv1-" + "2" * 64
SCOPE = "scopev1-" + "3" * 64
CONTROLS = {"collection_production_id": COLLECTION, "imported_selection_sha256": "4" * 64}


def _ref(path: str, authority: str = "document_input_root") -> dict:
    return {"authority": authority, "path": path, "sha256": "4" * 64, "byte_size": 1}


def _selections() -> tuple[dict, tuple[DocumentTerminalEvidence, ...]]:
    selections, evidence = [], []
    for ordinal in range(1, 36):
        source = {"source_id": f"source_{ordinal}", "sha256": "5" * 64, "pdf_page_count": 1}
        candidate = f"docv1-{ordinal:064x}"
        linked = f"exv1-{ordinal:064x}"
        root, link_root = f"documents/{source['source_id']}/{candidate}", f"linked/{linked}"
        row = {
            "source_ordinal": ordinal,
            "logical_source_id": source["source_id"],
            "physical_source_id": source["source_id"],
            "source_identity": source,
            "candidate_id": candidate,
            "candidate_root": root,
            "linked_candidate_id": linked,
            "linked_candidate_root": link_root,
        }
        for field, filename in {
            "document_identity_ref": "document_identity.json",
            "document_completion_ref": "completion_record.json",
            "candidate_inventory_ref": "artifact_inventory.json",
            "downstream_replay_ref": "downstream_replay.json",
        }.items():
            row[field] = _ref(f"{root}/records/{filename}")
        for field, filename in {
            "linked_identity_ref": "extraction_identity.json",
            "linked_completion_ref": "completion_record.json",
            "linked_inventory_ref": "artifact_inventory.json",
        }.items():
            row[field] = _ref(f"{link_root}/records/{filename}")
        selections.append(row)
        evidence.append(
            DocumentTerminalEvidence(
                source=source,
                source_ordinal=ordinal,
                evidence_kind="downstream_replay",
                transaction_id="txv1-" + "6" * 64,
                attempt=None,
                disposition="complete",
                terminal_event_ref=None,
                attempt_record_ref=None,
                downstream_replay_ref=row["downstream_replay_ref"],
                failure_class=None,
                retained_evidence_refs=(),
                candidate_id=candidate,
                document_completion_ref=row["document_completion_ref"],
                candidate_inventory_ref=row["candidate_inventory_ref"],
                target_aliases_ref=_ref(f"{root}/content/canonical/target_aliases.jsonl"),
            )
        )
    imported = {
        "selection_ref": _ref("resolved_specs/selection.json", "artifact_root"),
        "selection_sha256": CONTROLS["imported_selection_sha256"],
        "document_production_identity_ref": _ref("inputs/production_identity.json"),
        "document_run_spec_ref": _ref("inputs/document.json"),
        "document_input_root_relative_path": "pipelines/preserved/document_publications",
        "selections": selections,
    }
    return imported, tuple(evidence)


def _publish(root: Path, build: StageBuild) -> PublishedStage:
    directory = root / "scopes" / SCOPE / build.name.directory / build.identity
    for relative, value in {
        **build.payloads,
        "records/artifact_inventory.json": json_bytes(managed_inventory(build.payloads)),
        "records/completion_record.json": json_bytes(build.completion),
    }.items():
        path = directory / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    path = directory / "records/completion_record.json"
    return PublishedStage(path, bytes_ref(path.relative_to(root).as_posix(), path.read_bytes()), ())


def _build_stages(root: Path, monkeypatch: pytest.MonkeyPatch, controls: dict):
    imported, evidence = _selections()
    monkeypatch.setattr(RecordTargetIndexBuilder, "_entries", lambda *_: [])
    monkeypatch.setattr(
        "er_commons.collection_processing.record_target_indexing.build_document_targets",
        lambda *_: [],
    )
    accounting = AccountingBuilder().build(
        AccountingInputs(SCOPE, "production_full", PRODUCTION, evidence, **controls)
    )
    accounting_stage = _publish(root, accounting)
    index = RecordTargetIndexBuilder().build(
        RecordTargetIndexInputs(
            root,
            PRODUCTION,
            SCOPE,
            accounting.completion,
            accounting_stage,
            evidence,
            "record_target_order_v2",
            "7" * 64,
            **controls,
        )
    )
    index_stage = _publish(root, index)
    manifest = MentionManifest(
        [
            {"source_id": item.source["source_id"], "candidate_id": item.candidate_id}
            for item in evidence
        ],
        (),
    ).as_record(
        index_id=index.identity, source_family_catalog_ref=bytes_ref("catalog.json", b"{}\n")
    )
    (root / "manifest.json").write_bytes(json_bytes(manifest))
    resolution = CrossDocumentLinkBuilder()._stage_build(
        CrossDocumentLinkInputs(
            root,
            root,
            Path("catalog.json"),
            PRODUCTION,
            SCOPE,
            index.completion,
            index_stage,
            evidence,
            "8" * 64,
            **controls,
        ),
        manifest,
        bytes_ref("manifest.json", json_bytes(manifest)),
        [],
    )
    resolution_stage = _publish(root, resolution)
    handoff = HandoffAssembler().build(
        HandoffAssemblyInputs(
            PRODUCTION,
            SCOPE,
            accounting.completion,
            accounting_stage,
            index.completion,
            index_stage,
            resolution.completion,
            resolution_stage,
            "all_sources_successful",
            **controls,
        )
    )
    _publish(root, handoff)
    return imported, evidence, (accounting, index, resolution, handoff)


def test_v2_controls_default_is_byte_identical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Explicitly absent recovery controls preserve every old identity and serialized byte."""
    first = _build_stages(tmp_path, monkeypatch, {})[2]
    second = _build_stages(
        tmp_path,
        monkeypatch,
        {
            "collection_production_id": None,
            "imported_selection_sha256": None,
        },
    )[2]
    assert [asdict(stage) for stage in first] == [asdict(stage) for stage in second]
    # Independently reproduced from accepted HEAD builders, not a v3 projection.
    assert [
        sha256(
            json_bytes(
                {
                    "payloads": {key: value.decode() for key, value in stage.payloads.items()},
                    "completion": stage.completion,
                }
            )
        ).hexdigest()
        for stage in first
    ] == [
        "679ef8809ff1a49e047a10decb41ae83e0dbb9ea8d70a0b01b27ba0b22e9f7da",
        "38ff7b06188cca30ed9f3273d420e74c0c1f3e61ae9dd7f04d6b7b25a349b97d",
        "00694bb65ee28f7632fe2e918825ec65e7d51e05005719bc8e46067a3edcd531",
        "64e037d7f7960d06e767e3a3dd1ac2db581b4a06a7dba94b2c9755584e4401e9",
    ]
    for stage in first:
        assert stage.completion["schema_version"].endswith(".v2")


@pytest.mark.parametrize(
    "collection,selection",
    [(COLLECTION, None), (None, "4" * 64), (PRODUCTION, "4" * 64), (COLLECTION, "bad")],
)
def test_recovery_controls_are_closed_and_typed(collection, selection) -> None:
    with pytest.raises(ValueError, match="collection recovery requires"):
        collection_identity_fields(PRODUCTION, collection, selection)


@pytest.mark.parametrize(
    "builder,fields,schema",
    [
        (build_record_target_index_id, INDEX_PREIMAGE_FIELDS, "record_target_index"),
        (build_cross_document_link_id, LINK_PREIMAGE_FIELDS, "cross_document_link"),
        (build_collection_handoff_id, HANDOFF_PREIMAGE_FIELDS, "collection_handoff"),
    ],
)
def test_v3_ids_bind_both_controls_and_preserve_v2_identity(builder, fields, schema) -> None:
    old = {field: "fixed" for field in fields}
    old["schema_version"] = f"er_commons.{schema}_identity.v2"
    assert builder(old).endswith(canonical_sha256(old))
    new = {key: value for key, value in old.items() if key != "production_extraction_id"}
    new.update(CONTROLS, schema_version=f"er_commons.{schema}_identity.v3")
    initial = builder(new)
    assert initial != builder(old)
    for field, value in [
        ("collection_production_id", "cprodv1-" + "9" * 64),
        ("imported_selection_sha256", "a" * 64),
    ]:
        assert builder({**new, field: value}) != initial
    with pytest.raises(ValueError, match="identity fields differ"):
        builder({**new, "production_extraction_id": PRODUCTION})


def _bundle(root: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    imported, evidence, stages = _build_stages(root, monkeypatch, CONTROLS)
    policy = SimpleNamespace(
        document_concurrency=1,
        page_batch_size=16,
        cpu_threads_per_document=4,
        device="cpu",
        docling_timeout_seconds=60,
        outer_process_deadline_seconds=90,
        retry_limit=0,
    )
    run = SimpleNamespace(
        extraction_root=root,
        scope_id=SCOPE,
        document_spec=SimpleNamespace(production_extraction_id=PRODUCTION, resource_policy=policy),
    )
    writer = ContractBundleWriter(
        run,
        **CONTROLS,
        collection_production_identity_ref=_ref(
            "resolved_specs/collection_identity.json", "artifact_root"
        ),
        imported_selection_ref=imported["selection_ref"],
        imported_document_evidence=imported,
    )
    monkeypatch.setattr(
        writer,
        "_stage_one_records",
        lambda *_: pytest.fail("must not reconstruct imported attempts"),
    )
    path = writer.publish(
        evidence=evidence,
        accounting=stages[0].completion,
        index=stages[1].completion,
        resolution=stages[2].completion,
        handoff=stages[3].completion,
        stage_attempts=[],
    )
    import json

    return json.loads(path.read_bytes())


def test_v3_bundle_preserves_imported_rows_and_new_stage_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _bundle(tmp_path, monkeypatch)
    assert bundle["imported_document_evidence"] == _selections()[0]
    assert "document_attempts" not in bundle and "production_extraction_id" not in bundle
    assert bundle["collection_stage_attempts"] == []
    for key in ("accounting", "target_index", "resolution_completion", "handoff"):
        assert bundle[key]["schema_version"].endswith(".v3")


@pytest.mark.parametrize(
    "mutation",
    [
        "selection_digest",
        "stage_identity",
        "duplicate",
        "order",
        "reference",
        "control_authority",
        "root_traversal",
        "attempt_fallback",
    ],
)
def test_v3_bundle_rejects_cross_authority_and_selection_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    bundle = deepcopy(_bundle(tmp_path, monkeypatch))
    rows = bundle["imported_document_evidence"]["selections"]
    if mutation == "selection_digest":
        bundle["imported_selection_sha256"] = "9" * 64
    elif mutation == "stage_identity":
        bundle["target_index"]["identity_preimage"]["collection_production_id"] = (
            "cprodv1-" + "9" * 64
        )
    elif mutation == "duplicate":
        rows[-1] = rows[0]
    elif mutation == "order":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "reference":
        rows[0]["document_completion_ref"]["authority"] = "collection_output_root"
    elif mutation == "control_authority":
        bundle["collection_production_identity_ref"]["authority"] = "collection_output_root"
    elif mutation == "root_traversal":
        bundle["imported_document_evidence"]["document_input_root_relative_path"] = "../old"
    else:
        bundle["accounting"]["rows"][0]["evidence_kind"] = "document_attempt"
    with pytest.raises(ValueError):
        validate_collection_bundle(bundle, CollectionArtifactReader(tmp_path))


def test_bundle_write_is_restartable_and_refuses_conflicting_bytes(tmp_path: Path) -> None:
    """Bundle completion may repeat exact bytes but never replace existing evidence."""
    path = tmp_path / "contract_bundle.json"
    ContractBundleWriter._write_exact(path, b"accepted\n")
    ContractBundleWriter._write_exact(path, b"accepted\n")
    with pytest.raises(ValueError, match="conflicting contract bundle"):
        ContractBundleWriter._write_exact(path, b"different\n")
    assert path.read_bytes() == b"accepted\n"
