"""Executable-boundary tests for generic relink and downstream replay."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from er_commons.document_records.document_references import relink_replay


class _Ref:
    def __init__(self, path: Path) -> None:
        self.path = path

    def resolve(self, **_: object) -> Path:
        return self.path


class _Spec:
    def __init__(self, *, collection: Path, document: Path) -> None:
        self.selected_source_ids = ("source_a", "source_b")
        self.collection_run_spec_ref = _Ref(collection)
        self.document_publication_spec_ref = _Ref(document)

    def document(self, source_id: str) -> SimpleNamespace:
        return SimpleNamespace(
            source_document=SimpleNamespace(
                completion_ref=_Ref(Path(f"/sealed/{source_id}/records/completion_record.json"))
            )
        )


def _prepared(tmp_path: Path, spec: _Spec, document: Path) -> SimpleNamespace:
    return SimpleNamespace(
        spec=spec,
        repository_root=tmp_path,
        artifact_root=tmp_path,
        document_spec_path=document,
        collection_spec_path=spec.collection_run_spec_ref.path,
    )


def _write_collection(path: Path, *, document_name: str, mode: str) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "er_commons.collection_run_spec.v2",
                "document_run_spec": document_name,
                "source_ids": ["source_a", "source_b"],
                "source_family_catalog_relative_path": "inputs/catalog.json",
                "blocking_policy": "all_sources_successful",
                "document_evidence_mode": mode,
                "target_policy_sha256": "1" * 64,
                "resolution_policy_sha256": "2" * 64,
                "ordering_policy_version": "record_target_order_v2",
            }
        )
    )


def test_document_bridge_passes_fresh_link_completion_to_downstream_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = tmp_path / "document.json"
    document.write_text("{}")
    spec = _Spec(collection=tmp_path / "collection.json", document=document)
    linked_completion = tmp_path / "linked/records/completion_record.json"
    linked = SimpleNamespace(completion_path=linked_completion)
    observed: dict[str, object] = {}
    prepared = _prepared(tmp_path, spec, document)
    monkeypatch.setattr(relink_replay, "prepare_document_relink_run", lambda **_: prepared)
    monkeypatch.setattr(relink_replay, "verify_prepared_link_spec", lambda _: None)
    monkeypatch.setattr(relink_replay, "execute_prepared_document_relink", lambda *_a, **_k: linked)

    def publish(**kwargs: object) -> Path:
        observed.update(kwargs)
        return tmp_path / "published/records/completion_record.json"

    monkeypatch.setattr(relink_replay, "publish_downstream_replay", publish)

    result = relink_replay.relink_and_replay_document(
        data_root=tmp_path,
        link_spec=tmp_path / "link.json",
        source_id="source_a",
        repository_root=tmp_path,
    )

    assert observed["cross_reference_completion"] == linked_completion
    assert observed["source_candidate_root"] == Path("/sealed/source_a")
    assert observed["document_run_spec"] == document
    assert result.document_completion_path == tmp_path / "published/records/completion_record.json"


def test_collection_bridge_replays_every_source_before_assembly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = tmp_path / "document.json"
    document.write_text("{}")
    collection = tmp_path / "collection.json"
    _write_collection(
        collection,
        document_name=document.name,
        mode="downstream_replay_only",
    )
    spec = _Spec(collection=collection, document=document)
    events: list[str] = []

    prepared = _prepared(tmp_path, spec, document)
    monkeypatch.setattr(relink_replay, "prepare_document_relink_run", lambda **_: prepared)
    monkeypatch.setattr(relink_replay, "verify_prepared_link_spec", lambda _: None)

    def replay(*_: object, **kwargs: object) -> SimpleNamespace:
        source_id = str(kwargs["source_id"])
        events.append(f"replay:{source_id}")
        return SimpleNamespace(document_completion_path=tmp_path / f"{source_id}.json")

    monkeypatch.setattr(relink_replay, "_relink_and_replay_prepared", replay)
    monkeypatch.setattr(
        relink_replay,
        "assemble_collection_handoff",
        lambda data_root, run_spec: events.append("assemble") or tmp_path / "handoff.json",
    )

    result = relink_replay.relink_replay_and_assemble_collection(
        data_root=tmp_path,
        link_spec=tmp_path / "link.json",
        repository_root=tmp_path,
    )

    assert events == ["replay:source_a", "replay:source_b", "assemble"]
    assert result.handoff_completion_path == tmp_path / "handoff.json"


def test_collection_bridge_fails_before_writes_on_mismatched_spec(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = tmp_path / "document.json"
    document.write_text("{}")
    collection = tmp_path / "collection.json"
    _write_collection(collection, document_name=document.name, mode="document_attempt")
    spec = _Spec(collection=collection, document=document)
    called = False
    prepared = _prepared(tmp_path, spec, document)
    monkeypatch.setattr(relink_replay, "prepare_document_relink_run", lambda **_: prepared)

    def replay(*_args: object, **_kwargs: object) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(relink_replay, "_relink_and_replay_prepared", replay)

    with pytest.raises(ValueError, match="must forbid document attempts"):
        relink_replay.relink_replay_and_assemble_collection(
            data_root=tmp_path,
            link_spec=tmp_path / "link.json",
            repository_root=tmp_path,
        )

    assert called is False


def test_collection_bridge_stops_before_handoff_on_document_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = tmp_path / "document.json"
    document.write_text("{}")
    collection = tmp_path / "collection.json"
    _write_collection(
        collection,
        document_name=document.name,
        mode="downstream_replay_only",
    )
    spec = _Spec(collection=collection, document=document)
    events: list[str] = []
    prepared = _prepared(tmp_path, spec, document)
    monkeypatch.setattr(relink_replay, "prepare_document_relink_run", lambda **_: prepared)
    monkeypatch.setattr(relink_replay, "verify_prepared_link_spec", lambda _: None)

    def replay(*_: object, **kwargs: object) -> None:
        source_id = str(kwargs["source_id"])
        events.append(source_id)
        if source_id == "source_b":
            raise RuntimeError("document replay failed")

    monkeypatch.setattr(relink_replay, "_relink_and_replay_prepared", replay)
    monkeypatch.setattr(
        relink_replay,
        "assemble_collection_handoff",
        lambda *_: pytest.fail("handoff must not run after a document failure"),
    )

    with pytest.raises(RuntimeError, match="document replay failed"):
        relink_replay.relink_replay_and_assemble_collection(
            data_root=tmp_path,
            link_spec=tmp_path / "link.json",
            repository_root=tmp_path,
        )

    assert events == ["source_a", "source_b"]
