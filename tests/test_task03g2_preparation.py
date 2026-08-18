"""No-PDF preparation checks for the fresh three-source pilot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from er_commons.document_publication.task03g2_preparation import CATALOG, prepare_task03g2


def test_prepare_task03g2_stages_exact_catalog_and_reports_freshness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from er_commons.document_publication import (
        fresh_preflight,
        preflight,
    )
    from er_commons.document_publication import (
        task03g2_preparation as preparation,
    )

    manifest = tmp_path / (
        "datasets/ceqa/raw/brisbane_baylands/"
        "brisbane_baylands_2025_deir_sources_v1/records/source_manifest.json"
    )
    manifest.parent.mkdir(parents=True)
    catalog = json.loads(CATALOG.read_text())
    manifest.write_text(
        json.dumps(
            {
                "source_release_version": "brisbane_baylands_2025_deir_sources_v1",
                "sources": [
                    {**document["source"], "source_role": "model_corpus"}
                    for document in catalog["sources"]
                ],
            }
        )
    )
    completion = manifest.parent / "completion_record.json"
    completion.write_text("{}")

    def fake_sha256(path: Path) -> str:
        if path == manifest:
            return "fede3e4af815378b77a7f7f54c863ef095328da789859d4f4b25a524f3408f38"
        if path == completion:
            return "d1175d6bf54d2c557293cb7bb0e1191250a9b5db2aef5c9e563ebe01e58767a6"
        return hashlib.sha256(path.read_bytes()).hexdigest()

    monkeypatch.setattr(preparation, "sha256_file", fake_sha256)
    monkeypatch.setattr(fresh_preflight, "sha256_file", fake_sha256)
    monkeypatch.setattr(preflight, "sha256_file", fake_sha256)
    report_path = prepare_task03g2(tmp_path)
    report = json.loads(report_path.read_text())

    assert report["status"] == "ready_for_source_verification"
    assert report["source_pdf_bytes_read"] is False
    assert len(report["owner_configs"]) == 18
    assert report["freshness"]["completed_candidate_markers"] == []
    staged = report_path.parent / CATALOG.name
    assert staged.read_bytes() == CATALOG.read_bytes()
