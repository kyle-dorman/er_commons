"""Executable-boundary tests for generic relink and downstream replay."""

from __future__ import annotations

import json
import weakref
from pathlib import Path
from types import SimpleNamespace

import pytest

from er_commons.collection_processing import document_evidence
from er_commons.document_publication import candidates, outcomes
from er_commons.document_records.document_references import relink_replay


class _Ref:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.sha256 = "0" * 64

    def resolve(self, **_: object) -> Path:
        return self.path


class _Spec:
    def __init__(self, *, collection: Path, document: Path) -> None:
        self.selected_source_ids = ("source_a", "source_b")
        self.figure_alias_source_ids: tuple[str, ...] = ()
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
    released_builds: list[weakref.ReferenceType[object]] = []
    observed: dict[str, object] = {}
    prepared = _prepared(tmp_path, spec, document)
    monkeypatch.setattr(relink_replay, "prepare_document_relink_run", lambda **_: prepared)
    monkeypatch.setattr(relink_replay, "verify_prepared_link_spec", lambda _: None)

    class HeavyBuild:
        pass

    def execute(*_args: object, **_kwargs: object) -> SimpleNamespace:
        build = HeavyBuild()
        released_builds.append(weakref.ref(build))
        return SimpleNamespace(completion_path=linked_completion, build=build)

    monkeypatch.setattr(relink_replay, "execute_prepared_document_relink", execute)

    def publish(**kwargs: object) -> Path:
        assert released_builds[0]() is None
        observed.update(kwargs)
        return tmp_path / "published/records/completion_record.json"

    monkeypatch.setattr(relink_replay, "publish_downstream_replay", publish)
    prepared.budget = None
    prepared.document_spec = None
    prepared.publication_inputs = None
    spec.document_publication_spec_ref.sha256 = "a" * 64
    monkeypatch.setattr(relink_replay, "prepare_accepted_document_run", lambda *_a, **_k: None)

    result = relink_replay.relink_and_replay_document(
        data_root=tmp_path,
        link_spec=tmp_path / "link.json",
        source_id="source_a",
        repository_root=tmp_path,
    )

    assert observed["cross_reference_completion"] == linked_completion
    assert observed["source_candidate_root"] == Path("/sealed/source_a")
    assert observed["document_run_spec"] == document
    assert result.linked_completion_path == linked_completion
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

    def replay(*_: object, **kwargs: object) -> relink_replay.RelinkReplayResult:
        source_id = str(kwargs["source_id"])
        events.append(f"replay:{source_id}")
        return relink_replay.RelinkReplayResult(
            linked_completion_path=tmp_path / f"{source_id}.linked.json",
            document_completion_path=tmp_path / f"{source_id}.json",
        )

    monkeypatch.setattr(relink_replay, "_relink_and_replay_prepared", replay)
    monkeypatch.setattr(
        relink_replay, "verify_relinked_figure_source_policy", lambda *_args, **_kwargs: 0
    )
    monkeypatch.setattr(relink_replay, "verify_inherited_navigation_links", lambda *_: 28)

    def assemble(*_args: object, **_kwargs: object) -> Path:
        events.append("assemble")
        return tmp_path / "handoff.json"

    monkeypatch.setattr(relink_replay, "assemble_collection_handoff", assemble)

    result = relink_replay.relink_replay_and_assemble_collection(
        data_root=tmp_path,
        link_spec=tmp_path / "link.json",
        repository_root=tmp_path,
    )

    assert events == ["replay:source_a", "replay:source_b", "assemble"]
    assert [item.linked_completion_path.name for item in result.documents] == [
        "source_a.linked.json",
        "source_b.linked.json",
    ]
    assert all(not hasattr(item, "linked") for item in result.documents)
    assert result.handoff_completion_path == tmp_path / "handoff.json"


def test_relinked_output_gate_rejects_nonmain_figure_policy_leak(tmp_path: Path) -> None:
    candidate = tmp_path / "linked"
    completion = candidate / "records/completion_record.json"
    completion.parent.mkdir(parents=True)
    completion.write_text("{}")
    canonical = candidate / "canonical"
    canonical.mkdir()
    (canonical / "cross_references.jsonl").write_text(
        json.dumps(
            {
                "mention_class": "figure",
                "resolution_status": "unresolved",
                "unresolved_reason": "no_local_alias",
                "candidates": [],
                "cross_document_evidence": None,
            }
        )
        + "\n"
    )
    support = candidate / "support"
    support.mkdir()
    (support / "document_link_preservation.json").write_text(
        json.dumps({"schema_version": "er_commons.document_link_preservation.v1"})
    )

    with pytest.raises(ValueError, match="disabled source emitted a figure-resolution"):
        relink_replay.verify_relinked_figure_source_policy(
            completion, source_id="deir_appendix_d", figure_aliases_enabled=False
        )

    row_path = canonical / "cross_references.jsonl"
    row = json.loads(row_path.read_text())
    row["unresolved_reason"] = "accepted_target_type_unavailable"
    row_path.write_text(json.dumps(row) + "\n")
    assert (
        relink_replay.verify_relinked_figure_source_policy(
            completion, source_id="deir_appendix_d", figure_aliases_enabled=False
        )
        == 1
    )


def _write_inherited_navigation_fixture(tmp_path: Path) -> tuple[Path, list[dict[str, str]]]:
    overlay_root = tmp_path / relink_replay.TASK04C_LINK_ROOT
    overlay_root.mkdir(parents=True)
    overlay_rows = [
        {
            "source_id": "source_a",
            "source_toc_entry_id": f"navtocentryv1-{ordinal:064x}",
            "target_id": f"old/section/source_a/sec{ordinal:06d}",
        }
        for ordinal in range(28)
    ]
    (overlay_root / "link_overlay.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in overlay_rows)
    )
    linked = tmp_path / "linked"
    completion = linked / "records/completion_record.json"
    completion.parent.mkdir(parents=True)
    (linked / "navigation").mkdir()
    return completion, overlay_rows


def test_inherited_navigation_gate_accepts_namespace_rebinding(tmp_path: Path) -> None:
    completion, overlay_rows = _write_inherited_navigation_fixture(tmp_path)
    decisions = [
        {
            "navigation_entry_id": row["source_toc_entry_id"],
            "outcome": "resolved_unique",
            "candidate_target_ids": [row["target_id"].replace("old/", "current/", 1)],
        }
        for row in overlay_rows
    ]
    (completion.parent.parent / "navigation/decisions.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in decisions)
    )

    assert relink_replay.verify_inherited_navigation_links(tmp_path, {"source_a": completion}) == 28


def test_inherited_navigation_gate_rejects_duplicate_decisions(tmp_path: Path) -> None:
    completion, overlay_rows = _write_inherited_navigation_fixture(tmp_path)
    duplicate = {
        "navigation_entry_id": overlay_rows[0]["source_toc_entry_id"],
        "outcome": "resolved_unique",
        "candidate_target_ids": ["current/section/source_a/sec000000"],
    }
    (completion.parent.parent / "navigation/decisions.jsonl").write_text(
        json.dumps(duplicate) + "\n" + json.dumps(duplicate) + "\n"
    )

    with pytest.raises(ValueError, match="navigation decision is duplicated"):
        relink_replay.verify_inherited_navigation_links(tmp_path, {"source_a": completion})


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

    def replay(*_: object, **kwargs: object) -> relink_replay.RelinkReplayResult:
        source_id = str(kwargs["source_id"])
        events.append(source_id)
        if source_id == "source_b":
            raise RuntimeError("document replay failed")
        return relink_replay.RelinkReplayResult(
            linked_completion_path=tmp_path / f"{source_id}.linked.json",
            document_completion_path=tmp_path / f"{source_id}.json",
        )

    monkeypatch.setattr(relink_replay, "_relink_and_replay_prepared", replay)
    monkeypatch.setattr(
        relink_replay, "verify_relinked_figure_source_policy", lambda *_args, **_kwargs: 0
    )
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


def test_reusable_candidate_selection_respects_downstream_evidence_kind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep both valid lineage levels while selecting the collection-required one."""
    parent = tmp_path / "documents/source_a"
    ordinary = parent / ("docv1-" + "1" * 64)
    downstream = parent / ("docv1-" + "2" * 64)
    for root in (ordinary, downstream):
        records = root / "records"
        records.mkdir(parents=True)
        (records / "document_identity.json").write_text("{}")
        (records / "completion_record.json").write_text("{}")
    (downstream / "records/downstream_replay.json").write_text("{}")
    identity = SimpleNamespace(
        source=SimpleNamespace(),
        model_dump=lambda **_: {},
    )
    monkeypatch.setattr(candidates, "read_retained_record", lambda *_a, **_k: identity)
    monkeypatch.setattr(candidates, "verify_candidate", lambda *_a, **_k: None)
    monkeypatch.setattr(candidates, "_matches_run", lambda *_a, **_k: True)
    monkeypatch.setattr(candidates, "verify_identity_and_upstreams", lambda *_a, **_k: None)
    monkeypatch.setattr(candidates, "verify_downstream_replay", lambda *_a, **_k: None)
    monkeypatch.setattr(candidates, "reconcile_published_attempt", lambda *_a, **_k: None)
    run = SimpleNamespace(final_parent=parent, data_root=tmp_path)

    with pytest.raises(ValueError, match="multiple reusable"):
        candidates.find_reusable_candidate(run)
    assert candidates.find_reusable_candidate(run, evidence_kind="document_attempt") == (
        ordinary / "records/completion_record.json"
    )
    assert candidates.find_reusable_candidate(run, evidence_kind="downstream_replay") == (
        downstream / "records/completion_record.json"
    )
    second_downstream = parent / ("docv1-" + "3" * 64)
    second_records = second_downstream / "records"
    second_records.mkdir(parents=True)
    (second_records / "document_identity.json").write_text("{}")
    (second_records / "completion_record.json").write_text("{}")
    (second_records / "downstream_replay.json").write_text("{}")
    with pytest.raises(ValueError, match="multiple reusable"):
        candidates.find_reusable_candidate(run, evidence_kind="downstream_replay")


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("document_attempt", "ordinary"),
        ("downstream_replay_only", "downstream"),
    ],
)
def test_terminal_collector_routes_declared_evidence_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    expected: str,
) -> None:
    """The collection mode controls observation as well as execution."""
    calls: list[str] = []

    def observe(kind: str):
        def inner(*_args: object, **_kwargs: object) -> SimpleNamespace:
            calls.append(kind)
            return SimpleNamespace(disposition="complete")

        return inner

    monkeypatch.setattr(document_evidence, "observe_document_outcome", observe("ordinary"))
    monkeypatch.setattr(
        document_evidence,
        "observe_downstream_replay_outcome",
        observe("downstream"),
    )
    run = SimpleNamespace(
        data_root=tmp_path,
        document_spec_path=tmp_path / "document.json",
        collection_spec=SimpleNamespace(
            document_evidence_mode=mode,
            source_ids=("source_a",),
        ),
    )
    runner_calls: list[str] = []
    collector = document_evidence.TerminalEvidenceCollector(
        document_runner=lambda *_args: runner_calls.append("run")
    )

    assert len(collector.collect(run)) == 1
    assert calls == [expected]
    assert runner_calls == (["run"] if mode == "document_attempt" else [])


def test_downstream_observation_never_falls_back_to_attempt_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing replay is a hard collection error even if attempt evidence exists."""
    monkeypatch.setattr(outcomes, "prepare_document_run", lambda *_a, **_k: SimpleNamespace())
    monkeypatch.setattr(outcomes, "find_reusable_candidate", lambda *_a, **_k: None)
    monkeypatch.setattr(
        outcomes,
        "_matching_attempt",
        lambda *_a, **_k: pytest.fail("downstream mode must not inspect attempt fallback"),
    )

    with pytest.raises(ValueError, match="no reusable downstream replay"):
        outcomes.observe_downstream_replay_outcome(
            tmp_path,
            tmp_path / "document.json",
            "source_a",
            source_ordinal=1,
        )
