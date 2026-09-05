"""Portable contract tests for the generic reviewed-navigation bundle."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from er_commons.artifact_io import json_bytes, jsonl_bytes, sha256_file
from er_commons.document_records.document_references import reviewed_navigation
from er_commons.document_records.document_references.reviewed_navigation import (
    ArtifactRoots,
    ReviewedNavigationMaterializationRequest,
    load_reviewed_navigation_bundle,
    materialize_reviewed_navigation,
    materialize_reviewed_navigation_from_spec,
)

PROJECT_ROOT = Path(__file__).parents[1]
SCHEMA_PATH = (
    PROJECT_ROOT
    / "benchmarks/er_bench/schemas/document_linking/v1/reviewed_navigation_bundle.schema.json"
)


def _reference(path: Path, root: Path) -> dict[str, Any]:
    return {
        "authority": "artifact_root",
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
        "byte_size": path.stat().st_size,
    }


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _request(tmp_path: Path) -> ReviewedNavigationMaterializationRequest:
    inputs = tmp_path / "inputs"
    decisions = inputs / "review_decisions.jsonl"
    semantic = inputs / "semantic_view.json"
    text = inputs / "text_entries.jsonl"
    dispositions = inputs / "dispositions.jsonl"
    parents = inputs / "parent_relations.jsonl"
    _write(decisions, jsonl_bytes([{"decision_id": "decision-1"}]))
    _write(semantic, json_bytes({"semantic_view_id": "semantic-1"}))
    _write(
        text,
        jsonl_bytes(
            [
                {
                    "source_id": "report_alpha",
                    "navigation_entry_id": "entry-parent",
                    "table_disposition_id": "disposition-parent",
                    "text": "Parent",
                },
                {
                    "source_id": "report_alpha",
                    "navigation_entry_id": "entry-child",
                    "table_disposition_id": "disposition-child",
                    "text": "a. Child",
                },
            ]
        ),
    )
    _write(
        dispositions,
        jsonl_bytes(
            [
                {
                    "source_id": "report_alpha",
                    "disposition_id": "disposition-parent",
                    "effective_navigation": True,
                },
                {
                    "source_id": "report_alpha",
                    "disposition_id": "disposition-child",
                    "effective_navigation": True,
                },
            ]
        ),
    )
    _write(
        parents,
        jsonl_bytes(
            [
                {
                    "source_id": "report_alpha",
                    "relation_id": "relation-1",
                    "child_entry_id": "entry-child",
                    "parent_entry_id": "entry-parent",
                }
            ]
        ),
    )
    roots = ArtifactRoots(repository=PROJECT_ROOT, artifact_root=tmp_path)
    return ReviewedNavigationMaterializationRequest(
        roots=roots,
        output_parent=tmp_path / "bundles",
        schema_path=SCHEMA_PATH,
        source_ids=("report_alpha",),
        review_decisions_ref=_reference(decisions, tmp_path),
        semantic_view_ref=_reference(semantic, tmp_path),
        text_entries_ref=_reference(text, tmp_path),
        dispositions_ref=_reference(dispositions, tmp_path),
        parent_relations_ref=_reference(parents, tmp_path),
    )


def test_materializer_publishes_completion_last_and_exactly_reuses(tmp_path: Path) -> None:
    request = _request(tmp_path)

    first = materialize_reviewed_navigation(request)
    second = materialize_reviewed_navigation(request)

    assert second == first
    assert first.root.name.startswith("navreviewv1-")
    assert first.descriptor["identity_preimage"]["text_entries_ref"]["authority"] == "bundle"
    completion = json.loads((first.root / "records/completion_record.json").read_text())
    assert completion["completion_last"] is True
    assert completion["status"] == "complete"
    assert first.descriptor_path.parent == request.output_parent


def test_materializer_identity_binds_its_small_code_closure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[Path] = []

    def digest(path: Path) -> str:
        observed.append(path)
        return "0" * 64

    monkeypatch.setattr(reviewed_navigation, "sha256_file", digest)
    reviewed_navigation._materializer_code_sha256()

    assert {path.name for path in observed} >= {
        "artifact_io.py",
        "relinking_config.py",
        "reviewed_navigation.py",
        "publication.py",
    }


def test_loader_rejects_changed_managed_bytes_and_identity(tmp_path: Path) -> None:
    request = _request(tmp_path)
    published = materialize_reviewed_navigation(request)
    text_path = published.root / "navigation/text_entries.jsonl"
    text_path.write_bytes(text_path.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="artifact byte size differs|inventory closure differs"):
        load_reviewed_navigation_bundle(
            published.descriptor_path,
            roots=request.roots,
            schema_path=request.schema_path,
        )

    descriptor = json.loads(published.descriptor_path.read_text())
    descriptor["bundle_id"] = "navreviewv1-" + "0" * 64
    changed = tmp_path / "changed_descriptor.json"
    changed.write_bytes(json_bytes(descriptor))
    with pytest.raises(ValueError, match="bundle identity differs"):
        load_reviewed_navigation_bundle(
            changed,
            roots=request.roots,
            schema_path=request.schema_path,
        )


def test_materializer_rejects_undeclared_sources_and_dangling_parents(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    parent_path = tmp_path / request.parent_relations_ref["path"]
    _write(
        parent_path,
        jsonl_bytes(
            [
                {
                    "source_id": "report_alpha",
                    "relation_id": "relation-1",
                    "child_entry_id": "entry-missing",
                    "parent_entry_id": "entry-parent",
                }
            ]
        ),
    )
    bad_parent_ref = _reference(parent_path, tmp_path)
    with pytest.raises(ValueError, match="parent relation child differs"):
        materialize_reviewed_navigation(replace(request, parent_relations_ref=bad_parent_ref))

    text_path = tmp_path / request.text_entries_ref["path"]
    rows = [
        {
            "source_id": "report_beta",
            "navigation_entry_id": "entry-beta",
            "text": "Other",
        }
    ]
    _write(text_path, jsonl_bytes(rows))
    with pytest.raises(ValueError, match="undeclared source"):
        materialize_reviewed_navigation(
            replace(
                request,
                text_entries_ref=_reference(text_path, tmp_path),
                parent_relations_ref=bad_parent_ref,
            )
        )


def test_loader_enforces_reviewed_coverage_subset(tmp_path: Path) -> None:
    request = _request(tmp_path)
    published = materialize_reviewed_navigation(request)

    with pytest.raises(ValueError, match="coverage exceeds selected"):
        load_reviewed_navigation_bundle(
            published.descriptor_path,
            roots=request.roots,
            schema_path=request.schema_path,
            selected_source_ids=("report_beta",),
        )


def test_materializer_rejects_parent_relation_cycles(tmp_path: Path) -> None:
    request = _request(tmp_path)
    parent_path = tmp_path / request.parent_relations_ref["path"]
    _write(
        parent_path,
        jsonl_bytes(
            [
                {
                    "source_id": "report_alpha",
                    "relation_id": "relation-1",
                    "child_entry_id": "entry-child",
                    "parent_entry_id": "entry-parent",
                },
                {
                    "source_id": "report_alpha",
                    "relation_id": "relation-2",
                    "child_entry_id": "entry-parent",
                    "parent_entry_id": "entry-child",
                },
            ]
        ),
    )

    with pytest.raises(ValueError, match="parent relation cycle"):
        materialize_reviewed_navigation(
            replace(request, parent_relations_ref=_reference(parent_path, tmp_path))
        )


def test_existing_changed_namespace_is_never_overwritten(tmp_path: Path) -> None:
    request = _request(tmp_path)
    published = materialize_reviewed_navigation(request)
    identity_path = published.root / "records/identity_preimage.json"
    identity_path.write_text("{}\n")

    with pytest.raises(ValueError, match="changed file"):
        materialize_reviewed_navigation(request)


def test_portable_request_spec_drives_the_same_materializer(tmp_path: Path) -> None:
    request = _request(tmp_path)
    spec = {
        "schema_version": "er_commons.reviewed_navigation_request.v1",
        "artifact_relative_root": "portable_bundles",
        "source_ids": list(request.source_ids),
        "bundle_schema_ref": {
            "authority": "repository",
            "path": SCHEMA_PATH.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": sha256_file(SCHEMA_PATH),
            "byte_size": SCHEMA_PATH.stat().st_size,
        },
        "review_decisions_ref": request.review_decisions_ref,
        "semantic_view_ref": request.semantic_view_ref,
        "text_entries_ref": request.text_entries_ref,
        "dispositions_ref": request.dispositions_ref,
        "parent_relations_ref": request.parent_relations_ref,
    }
    spec_path = tmp_path / "review_spec.json"
    spec_path.write_bytes(json_bytes(spec))

    published = materialize_reviewed_navigation_from_spec(
        data_root=tmp_path,
        review_spec=spec_path,
        repository_root=PROJECT_ROOT,
    )

    assert published.root.parent == tmp_path / "portable_bundles"
    assert published.descriptor["source_ids"] == ["report_alpha"]
